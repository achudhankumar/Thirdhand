"""Single-host inbox: fenced claims, conservative recovery, explicit connections."""

import asyncio
import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


class InboxFull(RuntimeError):
    """The entire batch was rejected; sender should retry."""


class LostLease(RuntimeError):
    """This worker no longer owns the operation."""


class Inbox:
    def __init__(self, path, max_pending=1000, lease_seconds=300):
        self.path, self.max_pending, self.lease_seconds = (
            path,
            max_pending,
            lease_seconds,
        )

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    async def initialize(self):
        def operation():
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with self._connection() as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("BEGIN IMMEDIATE")
                if db.execute("PRAGMA user_version").fetchone()[0] > 2:
                    raise RuntimeError("Inbox schema is newer than this application")
                db.execute(
                    "CREATE TABLE IF NOT EXISTS inbox (id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0)"
                )
                columns = {r["name"] for r in db.execute("PRAGMA table_info(inbox)")}
                for name, definition in {
                    "sender": "TEXT NOT NULL DEFAULT ''",
                    "lease_token": "TEXT",
                    "lease_until": "REAL",
                    "last_error": "TEXT",
                }.items():
                    if name not in columns:
                        db.execute(f"ALTER TABLE inbox ADD COLUMN {name} {definition}")
                for row in db.execute(
                    "SELECT id,payload FROM inbox WHERE sender=''"
                ).fetchall():
                    payload = json.loads(row["payload"])
                    db.execute(
                        "UPDATE inbox SET sender=? WHERE id=?",
                        (payload.get("from") or "internal:" + row["id"], row["id"]),
                    )
                db.execute(
                    "UPDATE inbox SET status='review',last_error='legacy_processing_unknown' WHERE status='processing' AND lease_token IS NULL"
                )
                db.execute(
                    "CREATE INDEX IF NOT EXISTS inbox_status ON inbox(status,created)"
                )
                db.execute(
                    "CREATE INDEX IF NOT EXISTS inbox_sender ON inbox(sender,status)"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS outbound (id TEXT PRIMARY KEY, job_id TEXT NOT NULL, sequence INTEGER NOT NULL, recipient TEXT NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL, provider_id TEXT, response TEXT, error_code TEXT, created REAL NOT NULL, updated REAL NOT NULL, UNIQUE(job_id,sequence))"
                )
                db.execute(
                    "CREATE INDEX IF NOT EXISTS outbound_provider ON outbound(provider_id)"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS delivery_events (id TEXT PRIMARY KEY, provider_id TEXT NOT NULL, status TEXT NOT NULL, provider_time REAL NOT NULL, received REAL NOT NULL)"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS reminders (id TEXT PRIMARY KEY, sender TEXT NOT NULL, due REAL NOT NULL, title TEXT NOT NULL, customer_time REAL NOT NULL, state TEXT NOT NULL DEFAULT 'pending')"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS job_reviews (id INTEGER PRIMARY KEY,job_id TEXT NOT NULL,outcome TEXT NOT NULL,reason TEXT NOT NULL,created REAL NOT NULL)"
                )
                db.execute("PRAGMA user_version=2")

        await asyncio.to_thread(operation)

    @staticmethod
    def assert_lease(db, job_id, token):
        if not db.execute(
            "SELECT 1 FROM inbox WHERE id=? AND status='processing' AND lease_token=? AND lease_until>?",
            (job_id, token, time.time()),
        ).fetchone():
            raise LostLease("Job ownership expired")

    @staticmethod
    def reconcile(db, provider_id):
        events = {
            r[0]
            for r in db.execute(
                "SELECT status FROM delivery_events WHERE provider_id=?", (provider_id,)
            )
        }
        state = next(
            (v for v in ("read", "delivered", "failed", "sent") if v in events), None
        )
        if state:
            db.execute(
                "UPDATE outbound SET state=?,updated=? WHERE provider_id=?",
                (state, time.time(), provider_id),
            )

    async def enqueue(self, messages, statuses=None):
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                pending = db.execute(
                    "SELECT count(*) FROM inbox WHERE status!='done'"
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
                        "INSERT INTO inbox(id,payload,status,created,updated,sender) VALUES(?,?,'pending',?,?,?)",
                        (
                            message["id"],
                            json.dumps(message),
                            now,
                            now,
                            message.get("from") or "internal:" + message["id"],
                        ),
                    )
                    inserted += 1
                for event in statuses or []:
                    identity = hashlib.sha256(
                        json.dumps(event, sort_keys=True).encode()
                    ).hexdigest()
                    db.execute(
                        "INSERT OR IGNORE INTO delivery_events VALUES(?,?,?,?,?)",
                        (
                            identity,
                            event["id"],
                            event["status"],
                            float(event["timestamp"]),
                            time.time(),
                        ),
                    )
                    self.reconcile(db, event["id"])
                return inserted

        return await asyncio.to_thread(operation)

    async def claim(self):
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                now = time.time()
                db.execute(
                    "UPDATE outbound SET state='uncertain',error_code='expired_worker',updated=? WHERE state='sending' AND job_id IN (SELECT id FROM inbox WHERE status='processing' AND lease_until<=?)",
                    (now, now),
                )
                db.execute(
                    "UPDATE inbox SET status='review',last_error='lease_expired',updated=? WHERE status='processing' AND lease_until<=?",
                    (now, now),
                )
                row = db.execute(
                    "SELECT i.* FROM inbox i WHERE i.status='pending' AND NOT EXISTS (SELECT 1 FROM inbox other WHERE other.sender=i.sender AND other.status IN ('processing','review')) ORDER BY i.created,i.rowid LIMIT 1"
                ).fetchone()
                if row is None:
                    return None
                token = uuid.uuid4().hex
                db.execute(
                    "UPDATE inbox SET status='processing',attempts=attempts+1,lease_token=?,lease_until=?,updated=? WHERE id=?",
                    (token, now + self.lease_seconds, now, row["id"]),
                )
                return {
                    **dict(row),
                    "lease_token": token,
                    "message": json.loads(row["payload"]),
                }

        return await asyncio.to_thread(operation)

    async def renew(self, job_id, token):
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                self.assert_lease(db, job_id, token)
                db.execute(
                    "UPDATE inbox SET lease_until=?,updated=? WHERE id=?",
                    (time.time() + self.lease_seconds, time.time(), job_id),
                )

        await asyncio.to_thread(operation)

    async def check_lease(self, job_id, token):
        def operation():
            with self._connection() as db:
                self.assert_lease(db, job_id, token)

        await asyncio.to_thread(operation)

    async def finish(self, message_id, success, token, *, review=False, error=None):
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                self.assert_lease(db, message_id, token)
                db.execute(
                    "UPDATE inbox SET status=?,updated=?,last_error=?,lease_token=NULL,lease_until=NULL WHERE id=?",
                    (
                        "done" if success else "review" if review else "failed",
                        time.time(),
                        error,
                        message_id,
                    ),
                )
                if not success:
                    db.execute(
                        "UPDATE outbound SET state='uncertain',error_code='worker_failed',updated=? WHERE job_id=? AND state='sending'",
                        (time.time(), message_id),
                    )
                if message_id.startswith("reminder:"):
                    db.execute(
                        "UPDATE reminders SET state=? WHERE id=?",
                        (
                            "done" if success else "review" if review else "expired",
                            message_id.removeprefix("reminder:"),
                        ),
                    )

        await asyncio.to_thread(operation)

    async def counts(self):
        def operation():
            with self._connection() as db:
                return dict(
                    db.execute(
                        "SELECT status,count(*) FROM inbox GROUP BY status"
                    ).fetchall()
                )

        return await asyncio.to_thread(operation)

    async def add_reminder(self, sender, due, title, customer_time, identity):
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                if (
                    db.execute(
                        "SELECT count(*) FROM reminders WHERE sender=? AND state IN ('pending','enqueued')",
                        (sender,),
                    ).fetchone()[0]
                    >= 20
                ):
                    raise ValueError("Reminder list is full")
                db.execute(
                    "INSERT OR IGNORE INTO reminders(id,sender,due,title,customer_time) VALUES(?,?,?,?,?)",
                    (identity, sender, due, title[:200], customer_time),
                )

        await asyncio.to_thread(operation)

    async def reminders(self, sender):
        def operation():
            with self._connection() as db:
                return [
                    dict(r)
                    for r in db.execute(
                        "SELECT * FROM reminders WHERE sender=? AND state='pending' ORDER BY due",
                        (sender,),
                    )
                ]

        return await asyncio.to_thread(operation)

    async def cancel_reminders(self, sender):
        def operation():
            with self._connection() as db:
                db.execute(
                    "UPDATE reminders SET state='cancelled' WHERE sender=? AND state='pending'",
                    (sender,),
                )
                db.execute(
                    "UPDATE inbox SET status='done',last_error='cancelled_reminder' WHERE sender=? AND status='pending' AND id LIKE 'reminder:%'",
                    (sender,),
                )

        await asyncio.to_thread(operation)

    async def dispatch_due(self):
        def operation():
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                now = time.time()
                pending = db.execute(
                    "SELECT count(*) FROM inbox WHERE status!='done'"
                ).fetchone()[0]
                for row in db.execute(
                    "SELECT * FROM reminders WHERE state='pending' AND due<=? ORDER BY due",
                    (now,),
                ).fetchall():
                    if now - row["customer_time"] >= 86400 or now - row["due"] >= 3600:
                        db.execute(
                            "UPDATE reminders SET state='expired' WHERE id=?",
                            (row["id"],),
                        )
                        continue
                    if pending >= self.max_pending:
                        break
                    message = {
                        "id": "reminder:" + row["id"],
                        "from": row["sender"],
                        "timestamp": str(row["customer_time"]),
                        "type": "reminder",
                        "text": {"body": "Reminder: " + row["title"]},
                    }
                    db.execute(
                        "INSERT OR IGNORE INTO inbox(id,payload,status,created,updated,sender) VALUES(?,?,'pending',?,?,?)",
                        (message["id"], json.dumps(message), now, now, row["sender"]),
                    )
                    db.execute(
                        "UPDATE reminders SET state='enqueued' WHERE id=?", (row["id"],)
                    )
                    pending += 1

        await asyncio.to_thread(operation)

    async def cleanup(self, now=None):
        """Retain dedup tombstones, remove old successful payloads after seven days.

        Uncertain/failed records require review rather than silent deletion.
        Full account/data-retention policy remains a later production gate.
        """

        def operation():
            with self._connection() as db:
                instant = time.time() if now is None else now
                db.execute(
                    "UPDATE inbox SET payload='{}' WHERE status='done' AND updated<?",
                    (instant - 7 * 86400,),
                )
                db.execute(
                    "UPDATE outbound SET payload='{}',response=NULL WHERE state IN ('accepted','sent','delivered','read') AND updated<?",
                    (instant - 7 * 86400,),
                )

        await asyncio.to_thread(operation)
