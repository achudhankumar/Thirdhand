"""Bounded JSON requests and explicit upstream failures."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class UpstreamError(RuntimeError):
    """The upstream service could not provide a trustworthy result."""


async def request_json(
    client: httpx.AsyncClient, method: str, url: str, **kwargs: Any
) -> dict:
    try:
        async with client.stream(method, url, **kwargs) as response:
            response.raise_for_status()
            raw = bytearray()
            async for chunk in response.aiter_bytes():
                raw.extend(chunk)
                if len(raw) > 2097152:
                    raise UpstreamError("Provider response exceeded size limit")
        import json

        result = json.loads(raw)
        if not isinstance(result, dict):
            raise UpstreamError("Provider returned an invalid response")
        return result
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Upstream request failed: %s", type(exc).__name__)
        raise UpstreamError("Provider unavailable; please try again later") from exc
