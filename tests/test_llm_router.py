"""Exercise the real OpenAI SDK against offline HTTP responses."""

import io
import json
import wave
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import AsyncOpenAI

from services.llm_orchestrator import LLMOrchestrator, normalize_audio, tool_schemas
from services.tools.booking_tool import BookingTool
from services.tools.local_tool import LocalTool
from services.tools.shopping_tool import ShoppingTool
from services.tools.transit_tool import TransitTool


def completion(message):
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1,
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
            }
        ],
    }


@pytest.fixture
async def brain(settings, memory):
    seen = []

    def handle(request):
        data = json.loads(request.content)
        seen.append(data)
        if len(seen) == 1:
            return httpx.Response(
                200,
                json=completion(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call1",
                                "type": "function",
                                "function": {
                                    "name": "get_train_live_status",
                                    "arguments": '{"train_no":"12606"}',
                                },
                            }
                        ],
                    }
                ),
            )
        return httpx.Response(
            200,
            json=completion(
                {
                    "role": "assistant",
                    "content": "Train status: provider reports on time.",
                }
            ),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        api = AsyncOpenAI(api_key="test", http_client=http, max_retries=0)
        whatsapp = AsyncMock()
        transit = TransitTool(settings, http)
        transit.get_train_live_status = AsyncMock(
            return_value={"current_station": "TPJ", "delay_minutes": 0}
        )
        service = LLMOrchestrator(
            settings,
            memory,
            whatsapp,
            transit,
            BookingTool(settings, memory),
            ShoppingTool(http),
            LocalTool(settings, http),
            api,
        )
        yield service, seen


async def test_tanglish_function_round_trip(brain, memory):
    service, seen = brain
    answer = await service.respond("919876543210", "12606 train enga iruku")
    service.transit.get_train_live_status.assert_awaited_once_with(train_no="12606")
    assert "on time" in answer
    assert seen[1]["messages"][-1]["role"] == "tool"
    assert json.loads(seen[1]["messages"][-1]["content"])["current_station"] == "TPJ"
    assert len(await memory.get_history("919876543210")) == 2


async def test_untrusted_args_rejected(brain):
    service, _ = brain
    with pytest.raises(ValueError):
        await service.execute_tool(
            "get_train_live_status",
            '{"train_no":"12606","user_id":"victim"}',
            "user",
            False,
        )
    with pytest.raises(ValueError):
        await service.execute_tool("made_up_tool", "{}", "user", False)


async def test_local_requires_location(brain):
    service, _ = brain
    result = await service.execute_tool(
        "search_nearby_places", '{"category":"pharmacy"}', "user", False
    )
    assert "location" in result["error"]


async def test_global_cancel_and_reset(brain, memory):
    service, seen = brain
    await memory.start_booking("user", "movie", 0)
    assert "cancelled" in await service.respond("user", "cancel")
    assert (await memory.get_session("user")).booking.status == "cancelled"
    await service.respond("user", "reset")
    assert (await memory.get_session("user")).revision == 0
    assert seen == []


async def test_location_and_greeting(brain, memory):
    service, _ = brain
    await service.handle_message(
        {
            "from": "919876543210",
            "type": "location",
            "location": {"latitude": 13.08, "longitude": 80.27},
        }
    )
    assert (await memory.get_session("919876543210")).location["latitude"] == 13.08
    await service.handle_message(
        {"from": "919876543210", "type": "text", "text": {"body": "hi"}}
    )
    service.whatsapp.send_buttons.assert_awaited_once()


async def test_real_audio_normalization():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b"\x00\x00" * 800)
    result = await normalize_audio(buffer.getvalue())
    assert result.startswith(b"RIFF")


async def test_whisper_and_vision_real_sdk(settings, memory):
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path.endswith("/transcriptions"):
            assert b"whisper-1" in request.content
            return httpx.Response(
                200, json={"text": "Vanakkam, summarize this voice note."}
            )
        content = json.loads(request.content)
        assert content["messages"][1]["content"][1]["image_url"]["url"].startswith(
            "data:image/png;base64,"
        )
        return httpx.Response(
            200,
            json=completion(
                {"role": "assistant", "content": "Bill total: INR 120. Uncertain date."}
            ),
        )

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b"\x00\x00" * 800)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        api = AsyncOpenAI(api_key="test", http_client=http, max_retries=0)
        service = LLMOrchestrator(
            settings,
            memory,
            AsyncMock(),
            AsyncMock(),
            BookingTool(settings, memory),
            AsyncMock(),
            AsyncMock(),
            api,
        )
        assert (await service.transcribe(buffer.getvalue())).startswith("Vanakkam")
        assert "120" in await service.extract_image(b"fixture-image", "image/png")
    assert len(requests) == 2


def test_tool_schema_contract():
    tools = tool_schemas()
    assert len(tools) == 8
    assert all(
        t["function"]["parameters"]["additionalProperties"] is False for t in tools
    )
