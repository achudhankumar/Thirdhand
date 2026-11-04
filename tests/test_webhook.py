"""Real ASGI webhook requests with signed bodies and durable SQLite storage."""

import asyncio
import hashlib
import hmac
import json

import httpx
import pytest
from fastapi import FastAPI

from database.inbox import Inbox, InboxFull
from routers.webhook import router


@pytest.fixture
async def gateway(settings):
    app = FastAPI()
    app.state.settings = settings
    inbox = Inbox(settings.inbox_path, 10)
    await inbox.initialize()
    app.state.inbox = inbox
    app.include_router(router)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:
        yield client, inbox


def payload(message_id="wamid.test"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "123456"},
                            "messages": [
                                {
                                    "id": message_id,
                                    "from": "919876543210",
                                    "type": "text",
                                    "text": {"body": "12606 train enga iruku"},
                                }
                            ],
                        }
                    }
                ]
            }
        ],
    }


def signed(settings, data):
    body = json.dumps(data).encode()
    signature = (
        "sha256="
        + hmac.new(
            settings.meta_app_secret.get_secret_value().encode(), body, hashlib.sha256
        ).hexdigest()
    )
    return body, {"x-hub-signature-256": signature, "content-type": "application/json"}


async def test_verification(gateway):
    client, _ = gateway
    response = await client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200 and response.text == "12345"
    assert response.headers["content-type"].startswith("text/plain")
    assert (
        await client.get("/webhook", params={"hub.verify_token": "bad"})
    ).status_code == 403


async def test_signed_dedup_and_persistence(gateway, settings):
    client, inbox = gateway
    body, headers = signed(settings, payload())
    responses = await asyncio.gather(
        *(client.post("/webhook", content=body, headers=headers) for i in range(4))
    )
    assert all(r.status_code == 200 for r in responses)
    assert await inbox.counts() == {"pending": 1}
    item = await inbox.claim()
    assert item["message"]["text"]["body"].endswith("enga iruku")
    restarted = Inbox(settings.inbox_path)
    await restarted.initialize()
    assert await restarted.counts() == {"pending": 1}
    await restarted.claim()
    await restarted.finish(item["id"], True)
    assert (
        await client.post("/webhook", content=body, headers=headers)
    ).status_code == 200
    assert await restarted.counts() == {"done": 1}


async def test_invalid_signature_and_json(gateway, settings):
    client, _ = gateway
    assert (await client.post("/webhook", json=payload())).status_code == 403
    body, headers = signed(settings, [])
    assert (
        await client.post("/webhook", content=body, headers=headers)
    ).status_code == 400
    body, headers = signed(settings, payload())
    assert (
        await client.post("/webhook", content=body + b" ", headers=headers)
    ).status_code == 403


async def test_other_phone_and_status_events(gateway, settings):
    client, inbox = gateway
    data = payload()
    data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"] = "other"
    body, headers = signed(settings, data)
    assert (
        await client.post("/webhook", content=body, headers=headers)
    ).status_code == 200
    assert await inbox.counts() == {}


async def test_backpressure_is_atomic(settings):
    inbox = Inbox(settings.inbox_path, 1)
    await inbox.initialize()
    with pytest.raises(InboxFull):
        await inbox.enqueue([{"id": "a"}, {"id": "b"}])
    assert await inbox.counts() == {}


async def test_body_limit(gateway, settings):
    client, _ = gateway
    settings.webhook_max_bytes = 1024
    assert (await client.post("/webhook", content=b"x" * 1025)).status_code == 413


async def test_queue_failed_retained(gateway):
    _, inbox = gateway
    await inbox.enqueue([{"id": "x"}])
    await inbox.claim()
    await inbox.finish("x", False)
    assert await inbox.counts() == {"failed": 1}
    assert await inbox.claim() is None


async def test_application_lifespan_worker(settings, memory, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    import main

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    memory.initialize = AsyncMock()
    monkeypatch.setattr(main, "AstraMemory", lambda config: memory)
    processor = SimpleNamespace(handle_message=AsyncMock(), client=AsyncMock())
    monkeypatch.setattr(main, "LLMOrchestrator", lambda *args: processor)
    app = main.FastAPI(lifespan=main.lifespan)
    app.include_router(router)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client:
            body, headers = signed(settings, payload())
            assert (
                await client.post("/webhook", content=body, headers=headers)
            ).status_code == 200
            for attempt in range(30):
                if (await app.state.inbox.counts()).get("done") == 1:
                    break
                await asyncio.sleep(0.05)
            assert await app.state.inbox.counts() == {"done": 1}
            processor.handle_message.assert_awaited_once()
    processor.client.close.assert_awaited_once()


async def test_application_rejects_missing_credentials(settings, monkeypatch):
    from pydantic import SecretStr

    import main

    settings.meta_app_secret = SecretStr("")
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    app = main.FastAPI(lifespan=main.lifespan)
    with pytest.raises(ValueError, match="meta_app_secret"):
        async with app.router.lifespan_context(app):
            raise AssertionError("Startup must fail before serving")
