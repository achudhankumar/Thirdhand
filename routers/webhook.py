"""Verified Meta webhook ingress; acknowledge only after durable enqueue."""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from database.inbox import InboxFull

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/webhook", response_class=PlainTextResponse)
async def verify(request: Request):
    settings = request.app.state.settings
    query = request.query_params
    expected = settings.meta_verify_token.get_secret_value()
    token = query.get("hub.verify_token", "")
    if (
        not expected
        or query.get("hub.mode") != "subscribe"
        or not hmac.compare_digest(token.encode(), expected.encode())
    ):
        raise HTTPException(403, "Invalid verification token")
    challenge = query.get("hub.challenge", "")
    if not challenge.isascii() or not challenge.isdigit() or len(challenge) > 128:
        raise HTTPException(400, "Invalid challenge")
    return challenge


@router.post("/webhook")
async def receive(request: Request):
    settings = request.app.state.settings
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > settings.webhook_max_bytes:
            raise HTTPException(413, "Webhook body too large")
    secret = settings.meta_app_secret.get_secret_value()
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    signature = request.headers.get("x-hub-signature-256", "")
    if not secret or not hmac.compare_digest(expected.encode(), signature.encode()):
        raise HTTPException(403, "Invalid signature")
    try:
        data = json.loads(body)
        if (
            not isinstance(data, dict)
            or data.get("object") != "whatsapp_business_account"
        ):
            raise ValueError("Invalid webhook object")
        messages = []
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if (
                    value.get("metadata", {}).get("phone_number_id")
                    != settings.meta_phone_number_id
                ):
                    continue
                for message in value.get("messages", []):
                    if (
                        not isinstance(message, dict)
                        or not isinstance(message.get("id"), str)
                        or not 1 <= len(message["id"]) <= 256
                    ):
                        raise ValueError("Invalid message ID")
                    sender = message.get("from", "")
                    if (
                        not isinstance(sender, str)
                        or not sender.isascii()
                        or not sender.isdigit()
                        or not 7 <= len(sender) <= 15
                    ):
                        raise ValueError("Invalid sender")
                    messages.append(message)
        await request.app.state.inbox.enqueue(messages)
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise HTTPException(400, "Malformed webhook payload") from exc
    except InboxFull as exc:
        raise HTTPException(503, "Please retry later") from exc
    except Exception as exc:
        logger.error("Durable webhook acceptance failed (%s)", type(exc).__name__)
        raise HTTPException(503, "Inbox unavailable") from exc
    return {"status": "accepted"}
