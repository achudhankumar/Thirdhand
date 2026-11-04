"""Async Astra memory with bounded history and optimistic concurrency control."""

import asyncio
import hashlib
import hmac
import logging
import random
import time
from collections.abc import Callable
from typing import Any, Literal

from astrapy import DataAPIClient
from astrapy.exceptions import DataAPIErrorDescriptor, DataAPIResponseException
from astrapy.info import CollectionDefinition

from config import BaseModel, ConfigDict, Field, JsonValue, model_validator
from config.settings import Settings
from services.jobs import assert_active

logger = logging.getLogger(__name__)

REQUIRED_SLOTS = {
    "movie": ("theatre", "movie", "date", "showtime", "seat_count"),
    "food": ("restaurant", "items", "quantity", "date", "showtime", "delivery_address"),
}
TRANSITIONS = {
    "collecting": {"ready", "cancelled"},
    "ready": {"collecting", "checkout_pending", "cancelled"},
    "checkout_pending": {"checkout_ready", "cancelled"},
    "checkout_ready": {"cancelled"},
    "completed": set(),
    "cancelled": set(),
}


class MemoryErrorBase(RuntimeError):
    """Base error for the memory service."""


class MemoryUnavailable(MemoryErrorBase):
    """Storage failed; callers must not continue a booking blindly."""


class RevisionConflict(MemoryErrorBase):
    """Another worker changed the session; reload before proceeding."""


class ChatMessage(BaseModel):
    """Persist only user-visible conversation, never hidden reasoning."""

    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)
    created_at: float = Field(default_factory=time.time)


class BookingState(BaseModel):
    """Durable conversational slots; checkout orchestration belongs to tools."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal["movie", "food"]
    status: Literal[
        "collecting",
        "ready",
        "checkout_pending",
        "checkout_ready",
        "completed",
        "cancelled",
    ] = "collecting"
    slots: dict[str, JsonValue] = Field(default_factory=dict)
    checkout_url: str | None = None

    @property
    def missing_slots(self) -> list[str]:
        return [
            key
            for key in REQUIRED_SLOTS[self.kind]
            if self.slots.get(key) in (None, "", [], {})
        ]

    @model_validator(mode="after")
    def validate_state(self) -> "BookingState":
        if (
            self.status in {"ready", "checkout_pending", "checkout_ready", "completed"}
            and self.missing_slots
        ):
            raise ValueError("Required slots are missing")
        if self.checkout_url is not None:
            from urllib.parse import urlsplit

            url = urlsplit(self.checkout_url)
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
            ):
                raise ValueError(
                    "Checkout URL must be an HTTPS URL without credentials"
                )
        if len(self.model_dump_json().encode("utf-8")) > 32768:
            raise ValueError("Booking state exceeds 32 KiB")
        return self


class Session(BaseModel):
    """One bounded document keeps history and booking updates atomic."""

    model_config = ConfigDict(extra="forbid")
    revision: int = Field(default=0, ge=0)
    history: list[ChatMessage] = Field(default_factory=list, max_length=40)
    booking: BookingState | None = None
    location: dict[str, float] | None = None
    profile: dict[str, Any] = Field(default_factory=dict)
    updated_at: float = Field(default_factory=time.time)
    expires_at: float = 0


class AstraMemory:
    """Call initialize once before accepting requests on each worker."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None
        self._database = None
        if not settings.use_local_memory_fallback:
            self._client = DataAPIClient(
                settings.astra_db_application_token.get_secret_value()
            )
            self._database = self._client.get_async_database(
                str(settings.astra_db_api_endpoint).rstrip("/"),
                keyspace=settings.astra_db_keyspace,
            )
        self._collection: Any = None
        self._initialize_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Create or validate the collection, failing startup on schema mismatch."""
        async with self._initialize_lock:
            if self._collection is not None:
                return
            if getattr(self.settings, "use_local_memory_fallback", False):
                self._collection = LocalFileCollection(self.settings.local_memory_path)
                logger.info("Using local file session storage fallback")
                return
            try:
                async with asyncio.timeout(self.settings.database_timeout_seconds):
                    self._collection = await self._database.create_collection(
                        self.settings.astra_db_collection,
                        definition=CollectionDefinition(
                            indexing={"allow": ["_id", "revision"]}
                        ),
                    )
                logger.info("Astra session collection initialized")
            except Exception as exc:
                self._collection = None
                logger.error("Astra initialization failed (%s)", type(exc).__name__)
                raise MemoryUnavailable(
                    "Unable to initialize Astra session storage"
                ) from exc

    def _key(self, user_id: str) -> str:
        if not user_id.strip() or len(user_id) > 256:
            raise ValueError(
                "A non-empty user identifier of at most 256 characters is required"
            )
        return hmac.new(
            self.settings.session_hash_key.get_secret_value().encode("utf-8"),
            user_id.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def _call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        await assert_active()
        if self._collection is None:
            raise MemoryUnavailable("Call initialize before accessing memory")
        try:
            async with asyncio.timeout(self.settings.database_timeout_seconds):
                return await getattr(self._collection, method)(*args, **kwargs)
        except DataAPIResponseException:
            # Preserve structured error codes internally, never log raw requests.
            raise
        except Exception as exc:
            logger.error("Astra %s failed (%s)", method, type(exc).__name__)
            raise MemoryUnavailable("Session storage request failed") from exc

    async def _read(self, key: str) -> tuple[Session, bool]:
        try:
            document = await self._call("find_one", {"_id": key})
            if document is None:
                return Session(), False
            document.pop("_id", None)
            session = Session.model_validate(document)
            if session.expires_at <= time.time():
                return Session(revision=session.revision), True
            return session, True
        except DataAPIResponseException as exc:
            logger.error("Astra read rejected")
            raise MemoryUnavailable("Unable to read session") from exc

    async def get_session(self, user_id: str) -> Session:
        """Expired documents are treated as empty while preserving CAS revision."""
        session, _ = await self._read(self._key(user_id))
        return session

    async def get_history(self, user_id: str) -> list[dict[str, str]]:
        session = await self.get_session(user_id)
        return [
            {"role": message.role, "content": message.content}
            for message in session.history
        ]

    async def _save(self, key: str, session: Session, exists: bool) -> bool:
        previous_revision = session.revision
        now = time.time()
        updated = session.model_copy(
            update={
                "revision": previous_revision + 1,
                "updated_at": now,
                "expires_at": now + self.settings.session_ttl_seconds,
            }
        )
        document = {"_id": key, **updated.model_dump(mode="json")}
        try:
            if exists:
                result = await self._call(
                    "replace_one", {"_id": key, "revision": previous_revision}, document
                )
                return result.matched_count == 1
            await self._call("insert_one", document)
            return True
        except DataAPIResponseException as exc:
            codes = {error.error_code for error in exc.error_descriptors}
            if not exists and codes == {"DOCUMENT_ALREADY_EXISTS"}:
                return False
            logger.error("Astra write rejected")
            raise MemoryUnavailable("Unable to save session") from exc

    async def _mutate(
        self,
        user_id: str,
        change: Callable[[Session], None],
        expected_revision: int | None = None,
    ) -> Session:
        key = self._key(user_id)
        for attempt in range(self.settings.database_conflict_retries):
            session, exists = await self._read(key)
            if expected_revision is not None and session.revision != expected_revision:
                raise RevisionConflict("Session changed; reload before updating")
            change(session)
            session = Session.model_validate(session.model_dump())
            if await self._save(key, session, exists):
                session.revision += 1
                session.updated_at = time.time()
                session.expires_at = (
                    session.updated_at + self.settings.session_ttl_seconds
                )
                return session
            if expected_revision is not None:
                raise RevisionConflict("Concurrent update; reload before updating")
            await asyncio.sleep(random.uniform(0.005, 0.025) * (2**attempt))
        raise RevisionConflict("Session busy; retry the operation")

    async def append_message(self, user_id: str, role: str, content: str) -> Session:
        """Atomically append with a message-count sliding window."""
        message = ChatMessage(role=role, content=content)

        def change(session: Session) -> None:
            session.history = (session.history + [message])[
                -self.settings.chat_history_messages :
            ]

        return await self._mutate(user_id, change)

    async def start_booking(
        self,
        user_id: str,
        kind: Literal["movie", "food"],
        expected_revision: int,
    ) -> Session:
        def change(session: Session) -> None:
            if session.booking and session.booking.status not in {
                "completed",
                "cancelled",
            }:
                raise ValueError("Finish or cancel the active booking first")
            session.booking = BookingState(kind=kind)

        return await self._mutate(user_id, change, expected_revision)

    async def update_slots(
        self,
        user_id: str,
        slots: dict[str, JsonValue],
        expected_revision: int,
    ) -> Session:
        def change(session: Session) -> None:
            booking = session.booking
            if booking is None or booking.status not in {"collecting", "ready"}:
                raise ValueError("No editable booking")
            data = booking.model_dump()
            data["slots"] = {**booking.slots, **slots}
            data["status"] = "collecting"
            data["checkout_url"] = None
            updated = BookingState.model_validate(data)
            if not updated.missing_slots:
                updated.status = "ready"
            session.booking = updated

        return await self._mutate(user_id, change, expected_revision)

    async def transition_booking(
        self,
        user_id: str,
        status: str,
        expected_revision: int,
        checkout_url: str | None = None,
    ) -> Session:
        """CAS transitions let only one worker claim checkout_pending."""

        def change(session: Session) -> None:
            booking = session.booking
            if booking is None or status not in TRANSITIONS[booking.status]:
                raise ValueError("Invalid booking transition")
            data = booking.model_dump()
            data.update(status=status, checkout_url=checkout_url)
            session.booking = BookingState.model_validate(data)

        return await self._mutate(user_id, change, expected_revision)

    async def delete_session(self, user_id: str) -> None:
        """Physically erase a user's stored session on request."""
        try:
            await self._call("delete_one", {"_id": self._key(user_id)})
        except DataAPIResponseException as exc:
            logger.error("Astra deletion rejected")
            raise MemoryUnavailable("Unable to delete session") from exc

    async def update_profile(self, user_id: str, profile: dict[str, Any]) -> Session:
        def change(session: Session) -> None:
            session.profile = dict(profile)

        return await self._mutate(user_id, change)

    async def set_location(
        self, user_id: str, latitude: float, longitude: float
    ) -> Session:
        import math

        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise ValueError("Invalid location")

        def change(session: Session) -> None:
            session.location = {"latitude": latitude, "longitude": longitude}

        return await self._mutate(user_id, change)

    async def clear_location(self, user_id: str) -> Session:
        def change(session: Session):
            session.location = None

        return await self._mutate(user_id, change)

    async def change_profile(self, user_id: str, change_profile) -> Session:
        def change(session: Session):
            change_profile(session.profile)

        return await self._mutate(user_id, change)


class LocalFileCollection:
    """Compatible local API backed by SQLite; import legacy JSON exactly once.

    The legacy JSON is preserved for recovery. SQLite supplies atomic writes,
    cross-instance CAS and explicit handle closure; corrupt legacy data fails closed.
    This storage is allowed only in explicitly selected development mode.
    """

    def __init__(self, path: str = "data/local_sessions.json") -> None:
        import json
        from pathlib import Path

        from database.inbox import Inbox

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.storage = Inbox(str(self.path) + ".sqlite3")
        with self.storage._connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY,payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS metadata (name TEXT PRIMARY KEY,value TEXT NOT NULL)"
            )
            if not db.execute(
                "SELECT 1 FROM metadata WHERE name='legacy_import'"
            ).fetchone():
                documents = {}
                if self.path.exists():
                    try:
                        if self.path.stat().st_size > 10485760:
                            raise ValueError("Legacy file exceeds import limit")
                        documents = json.loads(self.path.read_text(encoding="utf-8"))
                        if not isinstance(documents, dict) or any(
                            not isinstance(k, str) or not isinstance(v, dict)
                            for k, v in documents.items()
                        ):
                            raise ValueError("Invalid legacy collection")
                    except (ValueError, OSError) as exc:
                        raise MemoryUnavailable(
                            "Legacy session file needs repair; original retained"
                        ) from exc
                db.executemany(
                    "INSERT INTO documents(id,payload) VALUES(?,?)",
                    [(k, json.dumps(v)) for k, v in documents.items()],
                )
                db.execute("INSERT INTO metadata VALUES('legacy_import','complete')")

    async def find_one(self, query: dict) -> dict | None:
        import json

        def operation():
            with self.storage._connection() as db:
                row = db.execute(
                    "SELECT payload FROM documents WHERE id=?",
                    (query.get("_id") or query.get("phone_number"),),
                ).fetchone()
                return json.loads(row[0]) if row else None

        return await asyncio.to_thread(operation)

    async def insert_one(self, document: dict) -> None:
        import json
        import sqlite3

        def operation():
            with self.storage._connection() as db:
                try:
                    db.execute(
                        "INSERT INTO documents VALUES(?,?)",
                        (
                            document.get("_id") or document.get("phone_number"),
                            json.dumps(document),
                        ),
                    )
                except sqlite3.IntegrityError:
                    raise DataAPIResponseException(
                        "duplicate",
                        command={},
                        raw_response={},
                        error_descriptors=[
                            DataAPIErrorDescriptor(
                                {
                                    "errorCode": "DOCUMENT_ALREADY_EXISTS",
                                    "message": "duplicate",
                                }
                            )
                        ],
                        warning_descriptors=[],
                    ) from None

        await asyncio.to_thread(operation)

    async def replace_one(self, query: dict, document: dict):
        import json
        from types import SimpleNamespace

        def operation():
            with self.storage._connection() as db:
                result = db.execute(
                    "UPDATE documents SET payload=? WHERE id=? AND json_extract(payload,'$.revision')=?",
                    (json.dumps(document), query.get("_id"), query.get("revision")),
                )
                return SimpleNamespace(matched_count=result.rowcount)

        return await asyncio.to_thread(operation)

    async def delete_one(self, query: dict) -> None:
        def operation():
            with self.storage._connection() as db:
                db.execute(
                    "DELETE FROM documents WHERE id=?",
                    (query.get("_id") or query.get("phone_number"),),
                )

        await asyncio.to_thread(operation)

    async def mutate_document(self, key, change):
        import json

        def operation():
            with self.storage._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT payload FROM documents WHERE id=?", (key,)
                ).fetchone()
                doc = (
                    json.loads(row[0])
                    if row
                    else {
                        "_id": key,
                        "phone_number": key,
                        "history": [],
                        "active_flow": None,
                        "slots": {},
                    }
                )
                change(doc)
                db.execute(
                    "INSERT INTO documents VALUES(?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                    (key, json.dumps(doc)),
                )
                return doc

        return await asyncio.to_thread(operation)


_default_local_collection: LocalFileCollection | None = None


def _get_playbook_collection() -> LocalFileCollection:
    global _default_local_collection
    if _default_local_collection is None:
        _default_local_collection = LocalFileCollection("data/playbook_sessions.json")
    return _default_local_collection


async def get_session(phone_number: str) -> dict[str, Any]:
    """Legacy functional API, now transactionally persisted without lost turns."""
    from datetime import datetime, timezone

    def change(doc):
        doc.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

    return await _get_playbook_collection().mutate_document(phone_number, change)


async def save_turn(
    phone_number: str,
    user_msg: str,
    bot_msg: str,
    active_flow: str | None = None,
    slots: dict | None = None,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    def change(doc):
        doc["history"] = (
            doc.get("history", [])
            + [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": bot_msg},
            ]
        )[-10:]
        doc.update(
            active_flow=active_flow,
            slots=slots or {},
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    return await _get_playbook_collection().mutate_document(phone_number, change)
