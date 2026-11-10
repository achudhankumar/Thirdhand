"""Meta WhatsApp Cloud API client with strict payload and download limits."""

import hashlib
import hmac
from urllib.parse import urlsplit

import httpx

from config.settings import Settings
from services.http import UpstreamError, request_json
from services.outbound import Outbound


class WhatsAppClient:
    def __init__(
        self, settings: Settings, client: httpx.AsyncClient, inbox=None
    ) -> None:
        self.settings = settings
        self.client = client
        self.outbound = Outbound(inbox) if inbox is not None else None
        self.base = f"https://graph.facebook.com/{settings.meta_api_version}"
        self.headers = {
            "Authorization": f"Bearer {settings.meta_access_token.get_secret_value()}"
        }

    async def _send(self, recipient: str, payload: dict) -> dict:
        if (
            not recipient.isascii()
            or not recipient.isdigit()
            or not 7 <= len(recipient) <= 15
        ):
            raise ValueError("Recipient must be an international numeric WhatsApp ID")

        async def send():
            return await request_json(
                self.client,
                "POST",
                f"{self.base}/{self.settings.meta_phone_number_id}/messages",
                headers=self.headers,
                json={"messaging_product": "whatsapp", "to": recipient, **payload},
            )

        if self.outbound is not None:
            return await self.outbound.send(recipient, payload, send)
        return await send()

    async def send_typing_indicator(self, message_id: str) -> None:
        """Mark incoming message as read (blue ticks) and trigger WhatsApp 3-dot typing indicator."""
        token = self.settings.meta_access_token.get_secret_value().strip()
        if not message_id or not token or token == "test-meta":
            return
        try:
            resp = await self.client.post(
                f"{self.base}/{self.settings.meta_phone_number_id}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                    "typing_indicator": {"type": "text"},
                },
                timeout=3.0,
            )
            if resp.status_code >= 400:
                await self.client.post(
                    f"{self.base}/{self.settings.meta_phone_number_id}/messages",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "messaging_product": "whatsapp",
                        "status": "read",
                        "message_id": message_id,
                    },
                    timeout=3.0,
                )
        except Exception:
            pass

    async def send_text(self, recipient: str, text: str) -> dict:
        if not text or len(text) > 4096:
            raise ValueError("WhatsApp text must contain 1 to 4096 characters")
        return await self._send(
            recipient, {"type": "text", "text": {"body": text, "preview_url": False}}
        )

    async def send_image(
        self, recipient: str, image_url: str, caption: str = ""
    ) -> dict:
        if not image_url or not image_url.startswith(("http://", "https://")):
            raise ValueError("image_url must be a valid HTTP/HTTPS URL")
        image_payload: dict[str, str] = {"link": image_url}
        if caption:
            image_payload["caption"] = caption[:1024]
        return await self._send(
            recipient,
            {
                "type": "image",
                "image": image_payload,
            },
        )

    async def send_buttons(
        self, recipient: str, body: str, buttons: list[dict]
    ) -> dict:
        if not 1 <= len(buttons) <= 3 or not 1 <= len(body) <= 1024:
            raise ValueError("Use 1 to 3 buttons and a body of at most 1024 characters")
        ids = set()
        for button in buttons:
            if (
                set(button) != {"id", "title"}
                or not 1 <= len(button["title"]) <= 20
                or not 1 <= len(button["id"]) <= 256
                or button["id"] in ids
            ):
                raise ValueError("Button titles, unique IDs, or fields are invalid")
            ids.add(button["id"])
        return await self._send(
            recipient,
            {
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body},
                    "action": {
                        "buttons": [{"type": "reply", "reply": b} for b in buttons]
                    },
                },
            },
        )

    async def send_list(
        self, recipient: str, body: str, label: str, sections: list[dict]
    ) -> dict:
        if (
            not 1 <= len(body) <= 1024
            or not 1 <= len(label) <= 20
            or not 1 <= len(sections) <= 10
        ):
            raise ValueError("Invalid list body, label, or sections")
        ids = set()
        total = 0
        for section in sections:
            rows = section.get("rows", [])
            if not rows or len(section.get("title", "")) > 24:
                raise ValueError("Invalid list section")
            for row in rows:
                row_id = row.get("id", "")
                if (
                    not 1 <= len(row_id) <= 200
                    or row_id in ids
                    or not 1 <= len(row.get("title", "")) <= 24
                    or len(row.get("description", "")) > 72
                ):
                    raise ValueError("Invalid list row")
                ids.add(row_id)
                total += 1
        if total > 10:
            raise ValueError("At most 10 total list rows are permitted")
        return await self._send(
            recipient,
            {
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {"text": body},
                    "action": {"button": label, "sections": sections},
                },
            },
        )

    async def download_media(self, media_id: str) -> tuple[bytes, str]:
        if not media_id.isascii() or not media_id.isdigit() or len(media_id) > 64:
            raise ValueError("Invalid Meta media ID")
        info = await request_json(
            self.client, "GET", f"{self.base}/{media_id}", headers=self.headers
        )
        url = urlsplit(info.get("url", ""))
        if (
            url.scheme != "https"
            or url.port not in (None, 443)
            or url.username
            or url.password
            or not url.hostname
            or not (
                url.hostname == "lookaside.fbsbx.com"
                or url.hostname.endswith(".facebook.com")
                or url.hostname.endswith(".fbcdn.net")
            )
        ):
            raise UpstreamError("Untrusted Meta media URL")
        mime = info.get("mime_type", "").split(";")[0]
        if mime not in {
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/webp",
            "audio/ogg",
            "audio/mpeg",
            "audio/mp4",
            "audio/aac",
            "audio/amr",
            "audio/wav",
        }:
            raise ValueError("Unsupported media type")
        if int(info.get("file_size", 0)) > self.settings.media_max_bytes:
            raise ValueError("Media file is too large")
        data = bytearray()
        async with self.client.stream(
            "GET", info["url"], headers=self.headers, follow_redirects=False
        ) as response:
            response.raise_for_status()
            if response.is_redirect:
                raise UpstreamError("Unexpected media redirect")
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > self.settings.media_max_bytes:
                    raise ValueError("Media download exceeded limit")
        if not data:
            raise ValueError("Empty media file")
        if info.get("sha256") and not hmac.compare_digest(
            hashlib.sha256(data).hexdigest(), info["sha256"]
        ):
            raise UpstreamError("Media checksum mismatch")
        return bytes(data), mime
