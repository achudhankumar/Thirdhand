"""Verify Meta raw bytes and persist bounded, validated messages/status events."""

import hashlib
import hmac
import json
import logging
import math
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from database.inbox import InboxFull

logger = logging.getLogger(__name__)
router = APIRouter()


def numeric(value, minimum=1, maximum=256):
    return (
        isinstance(value, str)
        and value.isascii()
        and value.isdigit()
        and minimum <= len(value) <= maximum
    )


def timestamp(value):
    if (
        not isinstance(value, str)
        or not value.isascii()
        or not value.isdigit()
        or len(value) > 16
    ):
        raise ValueError("Invalid timestamp")
    if not 0 < float(value) <= time.time() + 300:
        raise ValueError("Invalid timestamp")


def validate_message(message):
    if (
        not isinstance(message, dict)
        or not isinstance(message.get("id"), str)
        or not 1 <= len(message["id"]) <= 256
    ):
        raise ValueError("Invalid message ID")
    if not numeric(message.get("from"), 7, 15):
        raise ValueError("Invalid sender")
    timestamp(message.get("timestamp"))
    kind = message.get("type")
    if kind == "reminder":
        raise ValueError("Reserved internal message type")
    if not isinstance(kind, str) or not 1 <= len(kind) <= 64:
        raise ValueError("Invalid type")
    if kind == "text":
        text = message.get("text")
        if (
            not isinstance(text, dict)
            or not isinstance(text.get("body"), str)
            or not 1 <= len(text["body"]) <= 8000
        ):
            raise ValueError("Invalid text")
    elif kind == "interactive":
        interactive = message.get("interactive")
        if not isinstance(interactive, dict):
            raise ValueError("Invalid interactive message")
        reply = interactive.get("button_reply") or interactive.get("list_reply")
        if (
            not isinstance(reply, dict)
            or not isinstance(reply.get("id"), str)
            or not 1 <= len(reply["id"]) <= 256
        ):
            raise ValueError("Invalid interactive reply")
    elif kind == "location":
        location = message.get("location")
        if not isinstance(location, dict):
            raise ValueError("Invalid location")
        for key, limit in [("latitude", 90), ("longitude", 180)]:
            number = location.get(key)
            if (
                type(number) not in (int, float)
                or not math.isfinite(number)
                or not -limit <= number <= limit
            ):
                raise ValueError("Invalid location")
    elif kind in {"audio", "image", "document"}:
        media = message.get(kind)
        if not isinstance(media, dict) or not numeric(media.get("id"), 1, 64):
            raise ValueError("Invalid media")
        if (
            not isinstance(media.get("caption", ""), str)
            or len(media.get("caption", "")) > 1000
        ):
            raise ValueError("Invalid caption")


def entries(value):
    if not isinstance(value, list) or len(value) > 100:
        raise ValueError("Invalid event list")
    return value


@router.get("/webhook", response_class=PlainTextResponse)
async def verify(request: Request):
    query = request.query_params
    expected = request.app.state.settings.meta_verify_token.get_secret_value()
    if (
        not expected
        or query.get("hub.mode") != "subscribe"
        or not hmac.compare_digest(
            query.get("hub.verify_token", "").encode(), expected.encode()
        )
    ):
        raise HTTPException(403, "Invalid verification token")
    challenge = query.get("hub.challenge", "")
    if not numeric(challenge, 1, 128):
        raise HTTPException(400, "Invalid challenge")
    return challenge


@router.post("/webhook")
async def receive(request: Request):
    settings = request.app.state.settings
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > settings.webhook_max_bytes:
            raise HTTPException(413, "Webhook body too large")
        body.extend(chunk)
    secret = settings.meta_app_secret.get_secret_value()
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not secret or not hmac.compare_digest(
        expected.encode(), request.headers.get("x-hub-signature-256", "").encode()
    ):
        raise HTTPException(403, "Invalid signature")
    try:
        data = json.loads(body)
        if (
            not isinstance(data, dict)
            or data.get("object") != "whatsapp_business_account"
        ):
            raise ValueError("Invalid webhook object")
        messages, statuses = [], []
        for entry in entries(data.get("entry", [])):
            if not isinstance(entry, dict):
                raise ValueError("Invalid entry")
            for change in entries(entry.get("changes", [])):
                if not isinstance(change, dict):
                    raise ValueError("Invalid change")
                if change.get("field") != "messages":
                    continue  # Coexistence and new onboarding are outside Phase 1.
                value = change.get("value")
                if not isinstance(value, dict) or not isinstance(
                    value.get("metadata"), dict
                ):
                    raise ValueError("Invalid value")
                if (
                    value["metadata"].get("phone_number_id")
                    != settings.meta_phone_number_id
                ):
                    continue
                display_phone = "".join(
                    ch
                    for ch in str(value["metadata"].get("display_phone_number", ""))
                    if ch.isdigit()
                )
                for message in entries(value.get("messages", [])):
                    validate_message(message)
                    if display_phone and message.get("from") == display_phone:
                        continue
                    messages.append(message)
                for status in entries(value.get("statuses", [])):
                    if (
                        not isinstance(status, dict)
                        or not isinstance(status.get("id"), str)
                        or not 1 <= len(status["id"]) <= 256
                        or status.get("status")
                        not in {"sent", "delivered", "read", "failed"}
                    ):
                        raise ValueError("Invalid status")
                    timestamp(status.get("timestamp"))
                    statuses.append(
                        {k: status[k] for k in ("id", "status", "timestamp")}
                    )
        await request.app.state.inbox.enqueue(messages, statuses)
    except (ValueError, TypeError, AttributeError, KeyError):
        raise HTTPException(400, "Malformed webhook payload") from None
    except InboxFull:
        raise HTTPException(503, "Please retry later") from None
    except Exception as exc:
        logger.error("Durable webhook acceptance failed (%s)", type(exc).__name__)
        raise HTTPException(503, "Inbox unavailable") from None
    return {"status": "accepted"}
