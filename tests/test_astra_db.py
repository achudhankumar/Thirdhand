"""Durable-state semantics and concurrent-write behavior."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from database.astra_db import AstraMemory, MemoryUnavailable, RevisionConflict


async def test_history_window(memory):
    for i in range(16):
        await memory.append_message("user", "user", str(i))
    history = await memory.get_history("user")
    assert len(history) == 10
    assert history[0]["content"] == "6"
    assert history[-1]["content"] == "15"


async def test_concurrent_first_insert_and_updates(memory):
    await asyncio.gather(
        *(memory.append_message("user", "user", str(i)) for i in range(6))
    )
    session = await memory.get_session("user")
    assert session.revision == 6
    assert {m.content for m in session.history} == {str(i) for i in range(6)}
    assert "user" not in memory._collection.documents


async def test_slot_state_and_conflict(memory):
    session = await memory.start_booking("user", "movie", 0)
    assert session.booking.status == "collecting"
    session = await memory.update_slots(
        "user",
        {
            "movie": "Movie",
            "theatre": "Cinema",
            "date": "2099-01-01",
            "showtime": "18:00",
            "seat_count": 2,
        },
        session.revision,
    )
    assert session.booking.status == "ready"
    before = session.revision
    session = await memory.transition_booking("user", "checkout_pending", before)
    with pytest.raises(RevisionConflict):
        await memory.transition_booking("user", "checkout_pending", before)
    with pytest.raises(ValueError):
        await memory.update_slots("user", {"seat_count": 3}, session.revision)
    session = await memory.transition_booking(
        "user",
        "checkout_ready",
        session.revision,
        "https://merchant.example/checkout/session",
    )
    assert session.booking.checkout_url.endswith("/session")
    with pytest.raises(ValueError):
        await memory.transition_booking("user", "completed", session.revision)


async def test_expiry_and_delete(memory):
    session = await memory.append_message("user", "user", "old")
    memory._collection.documents[memory._key("user")]["expires_at"] = 0
    assert (await memory.get_session("user")).history == []
    fresh = await memory.append_message("user", "user", "new")
    assert fresh.revision == session.revision + 1
    await memory.delete_session("user")
    assert (await memory.get_session("user")).revision == 0


async def test_initialize_and_fail_closed(settings):
    service = AstraMemory(settings)
    with pytest.raises(MemoryUnavailable):
        await service.get_session("user")
    service._database.create_collection = AsyncMock(return_value=object())
    await service.initialize()
    await service.initialize()
    service._database.create_collection.assert_awaited_once()


async def test_storage_timeout_not_retried(memory):
    memory._collection.find_one = AsyncMock(side_effect=TimeoutError("timeout"))
    with pytest.raises(MemoryUnavailable):
        await memory.get_session("user")
    memory._collection.find_one.assert_awaited_once()


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_hash_key", "short"),
        ("astra_db_application_token", ""),
        ("astra_db_api_endpoint", "http://localhost:8000"),
        ("chat_history_messages", 11),
    ],
)
def test_invalid_configuration(settings, field, value):
    with pytest.raises(ValidationError):
        type(settings)(**{**settings.model_dump(), field: value}, _env_file=None)


async def test_bad_roles_and_content(memory):
    for role, text in [("system", "secret"), ("user", ""), ("assistant", "x" * 8001)]:
        with pytest.raises(ValidationError):
            await memory.append_message("user", role, text)
