"""Operator recovery, stale work and authenticated intake integration tests."""

import asyncio
import copy
import json
import sqlite3
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from database.inbox import Inbox
from manage_inbox import main as manage
from routers.webhook import router
from services.outbound import SendPolicyError
from tests.test_webhook import payload, signed


async def drive_worker(app, expected):
    from main import run_worker

    stop = asyncio.Event()
    task = asyncio.create_task(run_worker(app, stop))
    try:
        for _ in range(100):
            if (await app.state.inbox.counts()).get(expected) == 1:
                break
            await asyncio.sleep(0.02)
        assert (await app.state.inbox.counts()).get(expected) == 1
    finally:
        stop.set()
        await asyncio.wait_for(task, 2)


async def test_worker_real_transport_persists_provider_acceptance(settings, memory):
    from services.llm_orchestrator import LLMOrchestrator
    from services.tools.booking_tool import BookingTool
    from services.whatsapp_client import WhatsAppClient

    queue = Inbox(settings.inbox_path)
    await queue.initialize()
    message = payload()["entry"][0]["changes"][0]["value"]["messages"][0]
    message["text"]["body"] = "hi"
    await queue.enqueue([message])
    requests = []

    def send(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"messages": [{"id": "accepted-message"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(send)) as http:
        service = LLMOrchestrator(
            settings,
            memory,
            WhatsAppClient(settings, http, queue),
            AsyncMock(),
            BookingTool(settings, memory),
            AsyncMock(),
            AsyncMock(),
            client=AsyncMock(),
        )
        service.global_features.inbox = queue
        app = SimpleNamespace(
            state=SimpleNamespace(inbox=queue, settings=settings, orchestrator=service)
        )
        await drive_worker(app, "done")
    assert len(requests) == 1 and requests[0]["type"] == "interactive"
    with queue._connection() as db:
        row = db.execute("SELECT state,provider_id FROM outbound").fetchone()
        assert tuple(row) == ("accepted", "accepted-message")


async def test_ambiguous_checkout_is_quarantined_not_hidden_by_ai_fallback(
    settings, memory
):
    from pathlib import Path

    from openai.types.chat import ChatCompletion

    from services.llm_orchestrator import LLMOrchestrator
    from services.tools.booking_tool import BookingTool
    from tests.test_llm_router import completion

    sender = "919876543210"
    Path(settings.booking_profiles_path).write_text(
        json.dumps(
            [
                {
                    "merchant": "Cinema",
                    "kind": "movie",
                    "hosts": ["merchant.example"],
                    "start_url": "https://merchant.example/",
                    "steps": [{"action": "click", "selector": "button"}],
                    "checkout_selector": "#checkout",
                    "checkout_path_prefix": "/checkout",
                }
            ]
        )
    )
    browser = AsyncMock()
    browser.checkout.side_effect = TimeoutError()
    booking = BookingTool(settings, memory, browser)
    await booking.handle(
        sender,
        "update",
        "movie",
        {
            "theatre": "Cinema",
            "movie": "Movie",
            "date": "2099-01-01",
            "showtime": "18:00",
            "seat_count": 2,
        },
    )
    await memory.update_profile(
        sender, {"language": "english", "onboarding_step": "completed"}
    )
    api = AsyncMock()
    api.chat.completions.create.return_value = ChatCompletion.model_validate(
        completion(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "checkout",
                        "type": "function",
                        "function": {
                            "name": "booking",
                            "arguments": json.dumps(
                                {"action": "checkout", "kind": "movie", "slots": {}}
                            ),
                        },
                    }
                ],
            }
        )
    )
    whatsapp = AsyncMock()
    service = LLMOrchestrator(
        settings,
        memory,
        whatsapp,
        AsyncMock(),
        booking,
        AsyncMock(),
        AsyncMock(),
        client=api,
    )
    queue = Inbox(settings.inbox_path)
    await queue.initialize()
    service.global_features.inbox = queue
    await queue.enqueue(
        [
            {
                "id": "checkout",
                "from": sender,
                "timestamp": str(int(time.time())),
                "type": "text",
                "text": {"body": "confirm checkout"},
            }
        ]
    )
    app = SimpleNamespace(
        state=SimpleNamespace(inbox=queue, settings=settings, orchestrator=service)
    )
    await drive_worker(app, "review")
    assert (await memory.get_session(sender)).booking.status == "checkout_pending"
    browser.checkout.assert_awaited_once()
    api.chat.completions.create.assert_awaited_once()
    assert "operator review" in whatsapp.send_text.call_args.args[1]
    await queue.enqueue(
        [
            {
                "id": "reset",
                "from": sender,
                "timestamp": str(int(time.time())),
                "type": "text",
                "text": {"body": "reset"},
            }
        ]
    )
    assert await queue.claim() is None


async def test_signed_batch_31_messages_not_silently_dropped(settings):
    queue = Inbox(settings.inbox_path, 100)
    await queue.initialize()
    app = FastAPI()
    app.state.settings = settings
    app.state.inbox = queue
    app.include_router(router)
    data = payload()
    messages = data["entry"][0]["changes"][0]["value"]["messages"]
    messages[:] = [copy.deepcopy(messages[0]) for _ in range(31)]
    for i, message in enumerate(messages):
        message["id"] = f"wamid.{i}"
    raw, headers = signed(settings, data)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:
        assert (
            await client.post("/webhook", content=raw, headers=headers)
        ).status_code == 200
        assert await queue.counts() == {"pending": 31}
        queue.max_pending = 31
        raw, headers = signed(settings, payload("overload"))
        assert (
            await client.post("/webhook", content=raw, headers=headers)
        ).status_code == 503
        assert await queue.counts() == {"pending": 31}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update(entry=None),
        lambda d: d["entry"].__setitem__(0, True),
        lambda d: d["entry"][0].update(changes={}),
        lambda d: d["entry"][0]["changes"][0].update(value=[]),
        lambda d: d["entry"][0]["changes"][0]["value"]["messages"][0].update(
            timestamp=None
        ),
        lambda d: d["entry"][0]["changes"][0]["value"]["messages"][0].update(
            timestamp="999999999999"
        ),
        lambda d: d["entry"][0]["changes"][0]["value"]["messages"][0].update(
            text={"body": True}
        ),
        lambda d: d["entry"][0]["changes"][0]["value"]["messages"][0].update(
            type="reminder"
        ),
    ],
)
async def test_signed_malformed_batches_rejected_without_partial_acceptance(
    settings, mutation
):
    queue = Inbox(settings.inbox_path)
    await queue.initialize()
    app = FastAPI()
    app.state.settings = settings
    app.state.inbox = queue
    app.include_router(router)
    data = payload()
    mutation(data)
    raw, headers = signed(settings, data)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:
        assert (
            await client.post("/webhook", content=raw, headers=headers)
        ).status_code == 400
    assert await queue.counts() == {}


async def test_old_job_runs_no_model_or_merchant_action():
    from main import _process_message

    service = AsyncMock()
    app = SimpleNamespace(state=SimpleNamespace(orchestrator=service))
    with pytest.raises(SendPolicyError):
        await _process_message(app, {"timestamp": str(time.time() - 86401)})
    service.handle_message.assert_not_awaited()


async def test_operator_backup_and_resolution_are_audited_without_replay(
    tmp_path, capsys
):
    path = tmp_path / "inbox.sqlite"
    queue = Inbox(str(path))
    await queue.initialize()
    await queue.enqueue(
        [
            {"id": "failed", "from": "919876543210"},
            {"id": "next", "from": "919876543210"},
        ]
    )
    item = await queue.claim()
    await queue.finish(item["id"], False, item["lease_token"], review=True)
    assert await queue.claim() is None
    backup = tmp_path / "snapshot.sqlite"
    manage(["--database", str(path), "backup", "--output", str(backup)])
    db = sqlite3.connect(backup)
    try:
        assert db.execute("SELECT count(*) FROM inbox").fetchone()[0] == 2
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        db.close()
    manage(
        [
            "--database",
            str(path),
            "resolve",
            "--id",
            "failed",
            "--outcome",
            "abandoned",
            "--reason",
            "Checked external state; no repeat authorized",
        ]
    )
    assert (await queue.claim())["id"] == "next"
    with queue._connection() as db:
        assert (
            db.execute("SELECT outcome FROM job_reviews").fetchone()[0] == "abandoned"
        )
        assert db.execute("SELECT count(*) FROM outbound").fetchone()[0] == 0
    assert "no message sent" in capsys.readouterr().out


async def test_successful_payload_retention_keeps_dedup_tombstone(tmp_path):
    queue = Inbox(str(tmp_path / "retention.sqlite"))
    await queue.initialize()
    await queue.enqueue(
        [{"id": "old", "from": "919876543210", "text": {"body": "private"}}]
    )
    item = await queue.claim()
    await queue.finish("old", True, item["lease_token"])
    await queue.cleanup(now=time.time() + 8 * 86400)
    with queue._connection() as db:
        assert (
            db.execute("SELECT payload FROM inbox WHERE id='old'").fetchone()[0] == "{}"
        )
    assert await queue.enqueue([{"id": "old", "from": "919876543210"}]) == 0
