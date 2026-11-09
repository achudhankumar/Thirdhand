"""Real modular/global behavior preservation and audited integrity regressions."""

import asyncio
import io
import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import SecretStr
from pypdf import PdfWriter

from database.astra_db import AstraMemory, LocalFileCollection, MemoryUnavailable
from database.inbox import Inbox
from services import generate_pincode_scoped_reply, resolve_pincode_details
from services.global_features import GlobalFeatures
from services.global_support.providers import rank_offers
from services.global_support.regional import lookup
from services.global_support.schedule import add_reminder
from services.jobs import JobContext, current_job
from services.llm_orchestrator import LLMOrchestrator
from services.pdf_processor import extract_pdf
from services.tools.booking_tool import BookingTool
from services.tools.local_scout_tool import LocalScoutTool


async def test_no_fabricated_results_or_unknown_geography(memory):
    assert await resolve_pincode_details("902100", "Los Angeles") is None
    assert await resolve_pincode_details("621999", "Trichy") is None
    known = await resolve_pincode_details("620018")
    assert known["verified"] is False
    reply = await generate_pincode_scoped_reply(
        await memory.get_session("u"), "u", "train status", memory
    )
    assert "unavailable" in reply["text"].lower()
    assert all(
        v not in reply["text"] for v in ["Virudhachalam", "On Time", "4.6", "₹965"]
    )


async def test_local_scout_never_defaults_unknown_places(settings):
    scout = LocalScoutTool(settings, AsyncMock())
    with pytest.raises(ValueError, match="unverified"):
        await scout.search_nearby_by_text_or_coords("pharmacy", "unknown place")


async def test_local_legacy_import_once_atomic_cross_instance_cas(settings, tmp_path):
    legacy = tmp_path / "sessions.json"
    legacy.write_text(json.dumps({"legacy": {"_id": "legacy", "revision": 0}}))
    first = LocalFileCollection(str(legacy))
    second = LocalFileCollection(str(legacy))
    assert (await first.find_one({"_id": "legacy"}))["revision"] == 0
    outcomes = await asyncio.gather(
        *(
            c.replace_one(
                {"_id": "legacy", "revision": 0}, {"_id": "legacy", "revision": 1}
            )
            for c in [first, second]
        )
    )
    assert sorted(r.matched_count for r in outcomes) == [0, 1]
    await first.delete_one({"_id": "legacy"})
    reopened = LocalFileCollection(str(legacy))
    assert await reopened.find_one({"_id": "legacy"}) is None
    assert "legacy" in json.loads(legacy.read_text())
    config = settings.model_copy(
        update={
            "environment": "development",
            "use_local_memory_fallback": True,
            "local_memory_path": str(tmp_path / "real.json"),
        }
    )
    memories = [AstraMemory(config), AstraMemory(config)]
    await asyncio.gather(*(m.initialize() for m in memories))
    await asyncio.gather(
        *(memories[i % 2].append_message("user", "user", str(i)) for i in range(6))
    )
    assert (await memories[0].get_session("user")).revision == 6


def test_corrupt_local_legacy_fails_without_erasure(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{broken")
    with pytest.raises(MemoryUnavailable):
        LocalFileCollection(str(path))
    assert path.read_text() == "{broken"


@pytest.mark.parametrize(
    "city,iso,zone,currency",
    [
        ("London", "GB", "Europe/London", "GBP"),
        ("Toronto", "CA", "America/Toronto", "CAD"),
        ("trichy", "IN", "Asia/Kolkata", "INR"),
        ("திருச்சி", "IN", "Asia/Kolkata", "INR"),
        ("Madurai", "IN", "Asia/Kolkata", "INR"),
    ],
)
async def test_global_city_context_preserved_without_guessed_coordinates(
    memory, settings, city, iso, zone, currency
):
    features = GlobalFeatures(memory, settings)
    reply = await features.handle("user", city)
    assert "Location set" in reply
    session = await memory.get_session("user")
    assert session.location is None
    assert session.profile["global_location"]["country_iso"] == iso
    assert session.profile["global_location"]["timezone"] == zone
    assert session.profile["global_location"]["currency"] == currency
    assert await features.handle("user", "time")


async def test_global_pin_confirmation_pending_city_discovery_and_clear(
    memory, settings, monkeypatch
):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    settings.google_places_api_key = SecretStr("")
    features = GlobalFeatures(memory, settings)
    assert "Which city" in await features.handle("u", "cinema")
    assert "postal PIN" in await features.handle("u", "621211")
    assert "another city" in await features.handle("u", "unlisted town")
    assert "Tiruchirappalli" in await features.handle("u", "trichy")
    assert "pending_request" not in (await memory.get_session("u")).profile
    assert "London" in await features.location_pin("u", 51.5, -0.1)
    assert "pending_city" in (await memory.get_session("u")).profile
    assert "London" in await features.handle("u", "yes")
    assert "Chennai" in await features.handle("u", "Chennai cinema")
    assert "Chennai" in await features.handle("u", "yes")
    await memory.set_location("u", 13.08, 80.27)
    await features.handle("u", "clear location")
    session = await memory.get_session("u")
    assert session.location is None and "global_location" not in session.profile


async def test_global_tasks_and_name_memory_preserved(memory, settings):
    features = GlobalFeatures(memory, settings)
    assert await features.handle("u", "task call home") == "Task added."
    assert "call home" in await features.handle("u", "tasks")
    assert await features.handle("u", "done 1") == "Task completed."
    assert await features.handle("u", "tasks") == "No tasks."
    await features.handle("u", "En peru Karthik")
    assert await features.handle("u", "En peru enna?") == "Karthik"


def test_global_ranking_and_dst_preserved():
    offer = {
        "name": "A",
        "currency": "CAD",
        "deliverable": True,
        "price": 15,
        "tax": 1,
        "duty": 0,
        "shipping": 2,
        "rating": 4,
        "url": "https://example.org",
    }
    assert (
        len(
            rank_offers(
                [
                    offer,
                    offer | {"currency": "INR"},
                    offer | {"shipping": None},
                    offer | {"price": float("nan")},
                ],
                "CAD",
                20,
            )
        )
        == 1
    )
    state = {"location": {"timezone": "America/Toronto"}}
    result = add_reminder(
        state,
        "2026-11-01 01:30 Check clock",
        datetime(2026, 10, 31, 22, tzinfo=timezone.utc),
    )
    assert "repeated" in result


def test_global_regional_freshness_preserved(tmp_path, monkeypatch):
    path = tmp_path / "providers.json"
    path.write_text(
        json.dumps(
            [
                {
                    "name": "Fixture",
                    "country": "CA",
                    "cities": ["Toronto"],
                    "operations": ["transit"],
                    "endpoint": "https://fixture.invalid",
                    "token_env": "TEST_TOKEN",
                    "max_age_seconds": 60,
                }
            ]
        )
    )
    monkeypatch.setenv("PROVIDER_REGISTRY", str(path))
    monkeypatch.setenv("TEST_TOKEN", "fixture")
    loc = {"country_iso": "CA", "city": "Toronto", "currency": "CAD"}
    data = {
        "operation": "transit",
        "city": "Toronto",
        "observed_at": time.time(),
        "summary": "Test train",
    }
    with patch("httpx.Client.post", return_value=Mock(json=lambda: data)):
        assert "Test train" in lookup("transit", "train", loc)
        data["observed_at"] = 0
        assert "unverified" in lookup("transit", "train", loc)


async def test_reminders_durable_once_and_window_expiry(settings, memory, tmp_path):
    queue = Inbox(str(tmp_path / "reminders.sqlite"))
    await queue.initialize()
    features = GlobalFeatures(memory, settings, queue)
    await features.handle("u", "London")
    now = time.time()
    await queue.add_reminder("u", now - 10, "Meeting", now - 100, "one")
    await queue.dispatch_due()
    await queue.dispatch_due()
    assert await queue.counts() == {"pending": 1}
    item = await queue.claim()
    assert item["message"]["text"]["body"] == "Reminder: Meeting"
    await queue.finish(item["id"], True, item["lease_token"])
    with queue._connection() as db:
        assert db.execute("SELECT state FROM reminders").fetchone()[0] == "done"
    await queue.add_reminder("u", now - 10, "Too late", now - 90000, "two")
    await queue.dispatch_due()
    assert await queue.counts() == {"done": 1}
    with queue._connection() as db:
        assert (
            db.execute("SELECT state FROM reminders WHERE id='two'").fetchone()[0]
            == "expired"
        )


async def test_global_commands_before_onboarding_and_stop_cancels_reminders(
    settings, memory, tmp_path
):
    whatsapp = AsyncMock()
    booking = BookingTool(settings, memory)
    service = LLMOrchestrator(
        settings,
        memory,
        whatsapp,
        AsyncMock(),
        booking,
        AsyncMock(),
        AsyncMock(),
        client=AsyncMock(),
    )
    queue = Inbox(str(tmp_path / "queue.sqlite"))
    await queue.initialize()
    service.global_features.inbox = queue
    await queue.add_reminder("u", time.time() + 600, "call", time.time(), "one")
    await memory.start_booking("u", "movie", 0)
    reply = await service.handle_interactive_turn("u", "stop")
    assert "cancelled" in reply["reply"]
    session = await memory.get_session("u")
    assert session.booking.status == "cancelled" and session.profile["opt_out"] is True
    assert await queue.reminders("u") == []
    await service.handle_interactive_turn("u", "start")
    assert not (await memory.get_session("u")).profile["opt_out"]
    assert (
        "Task added"
        in (await service.handle_interactive_turn("u", "task call home"))["reply"]
    )
    await service.handle_interactive_turn("u", "delete my data")
    assert (await memory.get_session("u")).profile == {}


async def test_no_key_or_upstream_failure_returns_unavailability(settings, memory):
    settings.openai_api_key = SecretStr("")
    service = LLMOrchestrator(
        settings,
        memory,
        None,
        AsyncMock(),
        BookingTool(settings, memory),
        AsyncMock(),
        AsyncMock(),
    )
    await memory.update_profile(
        "u", {"language": "english", "onboarding_step": "completed"}
    )
    result = await service.handle_interactive_turn("u", "tell me something")
    assert "unavailable" in result["reply"].lower()
    settings.gemini_api_key = SecretStr("test-gemini")
    service = LLMOrchestrator(
        settings,
        memory,
        None,
        AsyncMock(),
        BookingTool(settings, memory),
        AsyncMock(),
        AsyncMock(),
        client=AsyncMock(),
    )
    with pytest.raises(Exception, match="OpenAI transcription"):
        await service.transcribe(b"audio")
    service.client.audio.transcriptions.create.assert_not_awaited()


async def test_real_pdf_extraction_and_rejection():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    stream = io.BytesIO()
    writer.write(stream)
    assert await extract_pdf(stream.getvalue()) == "This PDF has no extractable text."
    with pytest.raises(ValueError):
        await extract_pdf(b"not a pdf")
    writer = PdfWriter()
    for _ in range(31):
        writer.add_blank_page(width=100, height=100)
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ValueError, match="30 pages"):
        await extract_pdf(stream.getvalue())


async def test_real_reminder_command_uses_trusted_window_and_is_idempotent(
    settings, memory, tmp_path
):
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    queue = Inbox(str(tmp_path / "command.sqlite"))
    await queue.initialize()
    features = GlobalFeatures(memory, settings, queue)
    sender = "447700900123"
    await features.handle(sender, "London")
    now = time.time()
    await queue.enqueue([{"id": "command", "from": sender, "timestamp": str(int(now))}])
    item = await queue.claim()
    local = datetime.now(ZoneInfo("Europe/London")) + timedelta(minutes=5)
    text = f"remind {local:%Y-%m-%d %H:%M} Meeting"
    assert "verified incoming" in await features.handle(sender, text)
    token = current_job.set(
        JobContext(queue, item["id"], item["lease_token"], sender, now)
    )
    try:
        assert "saved" in await features.handle(sender, text)
        assert "saved" in await features.handle(sender, text)
    finally:
        current_job.reset(token)
    reminders = await queue.reminders(sender)
    assert len(reminders) == 1
    assert now < reminders[0]["due"] < now + 600


async def test_shared_location_outside_catalog_still_reaches_existing_places_flow(
    settings, memory
):
    await memory.set_location("user", 55.6761, 12.5683)
    await memory.update_profile(
        "user", {"language": "english", "onboarding_step": "awaiting_place"}
    )
    service = LLMOrchestrator(
        settings,
        memory,
        None,
        AsyncMock(),
        BookingTool(settings, memory),
        AsyncMock(),
        AsyncMock(),
        client=AsyncMock(),
    )
    service.respond = AsyncMock(return_value="Provider places result")
    result = await service.handle_interactive_turn("user", "Nearby pharmacies")
    assert result["reply"] == "Provider places result"
    service.respond.assert_awaited_once_with("user", "Nearby pharmacies")
    session = await memory.get_session("user")
    assert session.location == {"latitude": 55.6761, "longitude": 12.5683}
    assert "global_location" not in session.profile and "place" not in session.profile


async def test_language_change_persists_and_keeps_confirmed_city(settings, memory):
    features = GlobalFeatures(memory, settings)
    await features.handle("user", "Toronto")
    await memory.change_profile("user", lambda p: p.update(language="english"))
    service = LLMOrchestrator(
        settings,
        memory,
        None,
        AsyncMock(),
        BookingTool(settings, memory),
        AsyncMock(),
        AsyncMock(),
        client=AsyncMock(),
    )
    await service.handle_interactive_turn("user", "change language")
    assert "language" not in (await memory.get_session("user")).profile
    result = await service.handle_interactive_turn("user", "lang_tamil")
    assert "Language saved" in result["reply"]
    session = await memory.get_session("user")
    assert session.profile["language"] == "tamil"
    assert session.profile["global_location"]["city"] == "Toronto"
    assert session.profile["onboarding_step"] == "completed"


async def test_opt_out_blocks_media_and_location_and_accepts_unsubscribe(
    settings, memory
):
    whatsapp = AsyncMock()
    service = LLMOrchestrator(
        settings,
        memory,
        whatsapp,
        AsyncMock(),
        BookingTool(settings, memory),
        AsyncMock(),
        AsyncMock(),
        client=AsyncMock(),
    )
    reply = await service.handle_interactive_turn("u", "unsubscribe")
    assert "stopped" in reply["reply"].lower()
    assert (await memory.get_session("u")).profile["opt_out"] is True
    for incoming in [
        {
            "from": "u",
            "type": "location",
            "location": {"latitude": 13.08, "longitude": 80.27},
        },
        {"from": "u", "type": "audio", "audio": {"id": "123"}},
        {"from": "u", "type": "document", "document": {"id": "456"}},
    ]:
        await service.handle_message(incoming)
    whatsapp.download_media.assert_not_awaited()
    assert (await memory.get_session("u")).location is None
    assert whatsapp.send_text.await_count == 3
