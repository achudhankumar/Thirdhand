"""Crash, overload, ownership and ambiguous-delivery regressions."""

import asyncio
import json
import sqlite3
import time
from unittest.mock import AsyncMock

import pytest

from database.inbox import Inbox, InboxFull, LostLease
from services.http import UpstreamError
from services.jobs import JobContext, current_job
from services.outbound import DeliveryUncertain, Outbound, SendPolicyError


@pytest.fixture
async def queue(tmp_path):
    service = Inbox(str(tmp_path / "inbox.sqlite"), 100)
    await service.initialize()
    return service


def message(identity="one", sender="919876543210"):
    return {
        "id": identity,
        "from": sender,
        "timestamp": str(int(time.time())),
        "type": "text",
        "text": {"body": "hello"},
    }


async def claim_context(queue, identity="one"):
    await queue.enqueue([message(identity)])
    item = await queue.claim()
    job = JobContext(
        queue,
        item["id"],
        item["lease_token"],
        item["message"]["from"],
        float(item["message"]["timestamp"]),
    )
    return item, job


async def test_concurrent_claim_and_conversation_order(queue):
    await queue.enqueue([message("a"), message("b"), message("c", "447700900123")])
    claims = await asyncio.gather(*(queue.claim() for _ in range(6)))
    assert {r["id"] for r in claims if r} == {"a", "c"}
    assert await queue.counts() == {"processing": 2, "pending": 1}
    item = next(r for r in claims if r and r["id"] == "a")
    with pytest.raises(LostLease):
        await queue.finish("a", True, "wrong-token")
    await queue.finish("a", True, item["lease_token"])
    assert (await queue.claim())["id"] == "b"


async def test_initializer_never_steals_live_job_and_expiry_quarantines(queue):
    item, _ = await claim_context(queue)
    second = Inbox(queue.path)
    await second.initialize()
    assert await second.claim() is None
    await second.renew(item["id"], item["lease_token"])
    with queue._connection() as db:
        db.execute("UPDATE inbox SET lease_until=0")
    assert await second.claim() is None
    assert await queue.counts() == {"review": 1}
    with pytest.raises(LostLease):
        await queue.finish(item["id"], True, item["lease_token"])


async def test_v1_migration_preserves_data_and_quarantines_unknown_processing(tmp_path):
    path = str(tmp_path / "legacy.sqlite")
    db = sqlite3.connect(path)
    db.execute(
        "CREATE TABLE inbox (id TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL,attempts INTEGER NOT NULL DEFAULT 0)"
    )
    db.execute(
        "INSERT INTO inbox VALUES(?,?,?,1,1,1)",
        ("old", json.dumps(message("old")), "processing"),
    )
    db.commit()
    db.close()
    service = Inbox(path)
    await service.initialize()
    await service.initialize()
    assert await service.counts() == {"review": 1}
    with service._connection() as db:
        assert (
            json.loads(db.execute("SELECT payload FROM inbox").fetchone()[0])["id"]
            == "old"
        )
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2


async def test_overload_atomic_not_silent_and_duplicate_still_acknowledged(queue):
    queue.max_pending = 1
    with pytest.raises(InboxFull):
        await queue.enqueue([message("a"), message("b")])
    assert await queue.counts() == {}
    assert await queue.enqueue([message("a")]) == 1
    assert await queue.enqueue([message("a")]) == 0


async def test_outbound_acceptance_and_early_out_of_order_statuses(queue):
    _, job = await claim_context(queue)
    await queue.enqueue(
        [], [{"id": "out-1", "status": "read", "timestamp": str(int(time.time()))}]
    )
    token = current_job.set(job)
    operation = AsyncMock(return_value={"messages": [{"id": "out-1"}]})
    try:
        outbound = Outbound(queue)
        result = await outbound.send(job.sender, {"type": "text"}, operation)
        assert result["messages"][0]["id"] == "out-1"
        job.sequence = 0
        assert await outbound.send(job.sender, {"type": "text"}, operation) == result
        operation.assert_awaited_once()
    finally:
        current_job.reset(token)
    await queue.enqueue(
        [], [{"id": "out-1", "status": "sent", "timestamp": str(int(time.time()))}]
    )
    with queue._connection() as db:
        row = db.execute("SELECT * FROM outbound").fetchone()
        assert row["state"] == "read" and row["provider_id"] == "out-1"


@pytest.mark.parametrize(
    "failure,expected",
    [
        (TimeoutError(), "uncertain"),
        (UpstreamError("upstream", http_status=500), "uncertain"),
        (UpstreamError("rejected", http_status=400), "rejected"),
        (UpstreamError("rate limited", http_status=429), "rejected"),
    ],
)
async def test_uncertain_or_rejected_delivery_never_repeats(queue, failure, expected):
    _, job = await claim_context(queue)
    token = current_job.set(job)
    operation = AsyncMock(side_effect=failure)
    try:
        outbound = Outbound(queue)
        with pytest.raises(UpstreamError):
            await outbound.send(job.sender, {"type": "text"}, operation)
        job.sequence = 0
        with pytest.raises(DeliveryUncertain):
            await outbound.send(job.sender, {"type": "text"}, operation)
        operation.assert_awaited_once()
    finally:
        current_job.reset(token)
    with queue._connection() as db:
        assert db.execute("SELECT state FROM outbound").fetchone()[0] == expected


async def test_cancelled_send_is_uncertain_and_retains_intent(queue):
    _, job = await claim_context(queue)
    token = current_job.set(job)
    entered = asyncio.Event()

    async def operation():
        entered.set()
        await asyncio.Event().wait()

    try:
        task = asyncio.create_task(
            Outbound(queue).send(job.sender, {"type": "text"}, operation)
        )
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        current_job.reset(token)
    with queue._connection() as db:
        assert db.execute("SELECT state,payload FROM outbound").fetchone()[:] == (
            "uncertain",
            '{"type": "text"}',
        )


async def test_expired_window_and_stale_lease_prevent_send(queue):
    _, job = await claim_context(queue)
    operation = AsyncMock()
    token = current_job.set(job)
    try:
        job.customer_time = time.time() - 86401
        with pytest.raises(SendPolicyError):
            await Outbound(queue).send(job.sender, {}, operation)
        job.customer_time = time.time()
        with queue._connection() as db:
            db.execute("UPDATE inbox SET lease_until=0")
        with pytest.raises(LostLease):
            await Outbound(queue).send(job.sender, {}, operation)
        operation.assert_not_awaited()
    finally:
        current_job.reset(token)


async def test_sqlite_connections_are_explicitly_closed(tmp_path, monkeypatch):
    opened, closed = [], []
    original = sqlite3.connect

    class Tracked(sqlite3.Connection):
        def close(self):
            closed.append(id(self))
            super().close()

    def connect(*args, **kwargs):
        db = original(*args, **kwargs, factory=Tracked)
        opened.append(id(db))
        return db

    monkeypatch.setattr(sqlite3, "connect", connect)
    service = Inbox(str(tmp_path / "closed.sqlite"))
    await service.initialize()
    for _ in range(10):
        await service.counts()
    assert len(opened) == 11 and opened == closed


async def test_stale_worker_cannot_mutate_session_memory(queue, memory):
    _, job = await claim_context(queue)
    with queue._connection() as db:
        db.execute("UPDATE inbox SET lease_until=0")
    token = current_job.set(job)
    try:
        with pytest.raises(LostLease):
            await memory.append_message(job.sender, "assistant", "stale reply")
    finally:
        current_job.reset(token)
    assert (await memory.get_session(job.sender)).history == []
