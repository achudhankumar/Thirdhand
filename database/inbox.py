"""Durable single-replica inbox with atomic deduplication and bounded backlog."""

import asyncio
import json
import sqlite3
import time
from pathlib import Path


class InboxFull(RuntimeError):
    """Provider should retry later because the durable queue is full."""


class Inbox:
    def __init__(self, path: str, max_pending: int = 1000) -> None:
        self.path = path
        self.max_pending = max_pending

    def _connection(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    async def initialize(self) -> None:
        def operation():
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with self._connection() as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute(
                    "CREATE TABLE IF NOT EXISTS inbox (id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0)"
                )
                db.execute(
                    "CREATE INDEX IF NOT EXISTS inbox_status ON inbox(status, created)"
                )
                db.execute(
                    "UPDATE inbox SET status='pending' WHERE status='processing'"
                )

        await asyncio.to_thread(operation)

    async def enqueue(self, messages: list[dict]) -> int:
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                pending = db.execute(
                    "SELECT count(*) FROM inbox WHERE status IN ('pending','processing')"
                ).fetchone()[0]
                inserted = 0
                for message in messages:
                    if db.execute(
                        "SELECT 1 FROM inbox WHERE id=?", (message["id"],)
                    ).fetchone():
                        continue
                    if pending + inserted >= self.max_pending:
                        raise InboxFull("Queue full")
                    now = time.time()
                    db.execute(
                        "INSERT INTO inbox VALUES (?, ?, 'pending', ?, ?, 0)",
                        (message["id"], json.dumps(message), now, now),
                    )
                    inserted += 1
                db.execute(
                    "DELETE FROM inbox WHERE status='done' AND updated < ?",
                    (time.time() - 7 * 86400,),
                )
                return inserted

        return await asyncio.to_thread(operation)

    async def claim(self) -> dict | None:
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT * FROM inbox WHERE status='pending' ORDER BY created LIMIT 1"
                ).fetchone()
                if not row:
                    return None
                db.execute(
                    "UPDATE inbox SET status='processing', attempts=attempts+1, updated=? WHERE id=?",
                    (time.time(), row["id"]),
                )
                return {**dict(row), "message": json.loads(row["payload"])}

        return await asyncio.to_thread(operation)

    async def finish(self, message_id: str, success: bool) -> None:
        def operation():
            with self._connection() as db:
                db.execute(
                    "UPDATE inbox SET status=?, updated=? WHERE id=?",
                    ("done" if success else "failed", time.time(), message_id),
                )

        await asyncio.to_thread(operation)

    async def counts(self) -> dict:
        def operation():
            with self._connection() as db:
                return dict(
                    db.execute(
                        "SELECT status,count(*) FROM inbox GROUP BY status"
                    ).fetchall()
                )

        return await asyncio.to_thread(operation)
