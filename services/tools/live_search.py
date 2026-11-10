"""Live web search for current facts (movies running now, prices, news, study answers).

Providers, in order:
1. Tavily (TAVILY_API_KEY) - free tier 1,000 searches/month.
2. Gemini with Google Search grounding (GEMINI_API_KEY on a billing-enabled project).

When no provider works, returns None. Callers must then say live data is unavailable
instead of inventing an answer.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _secret(settings: Any, name: str) -> str:
    value = getattr(settings, name, None)
    if value is None:
        return ""
    raw = value.get_secret_value() if hasattr(value, "get_secret_value") else str(value)
    raw = raw.strip()
    return "" if raw.startswith("test") else raw


async def _tavily(key: str, query: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=25.0) as http:
        resp = await http.post(
            "https://api.tavily.com/search",
            json={
                "api_key": key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "max_results": 6,
            },
        )
    if resp.status_code != 200:
        logger.warning("Tavily search failed with HTTP %s", resp.status_code)
        return None
    data = resp.json()
    sources = [
        {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:600]}
        for r in data.get("results", [])
    ]
    if not data.get("answer") and not sources:
        return None
    return {"provider": "tavily", "answer": data.get("answer") or "", "sources": sources}


async def _gemini_grounded(key: str, model: str, query: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=40.0) as http:
        resp = await http.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key},
            json={"contents": [{"parts": [{"text": query}]}], "tools": [{"google_search": {}}]},
        )
    if resp.status_code != 200:
        logger.warning("Gemini grounded search unavailable (HTTP %s)", resp.status_code)
        return None
    cand = (resp.json().get("candidates") or [{}])[0]
    answer = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    chunks = cand.get("groundingMetadata", {}).get("groundingChunks", []) or []
    sources = [
        {"title": c.get("web", {}).get("title", ""), "url": c.get("web", {}).get("uri", ""), "content": ""}
        for c in chunks
        if c.get("web")
    ]
    if not sources:
        # Not grounded -> not live. Do not present it as current information.
        return None
    return {"provider": "gemini_search", "answer": answer, "sources": sources}


async def live_search(settings: Any, query: str) -> dict[str, Any] | None:
    """Return {"provider", "answer", "sources"} from a live source, or None."""
    tavily_key = _secret(settings, "tavily_api_key")
    if tavily_key:
        try:
            result = await _tavily(tavily_key, query)
            if result:
                return result
        except Exception as exc:
            logger.warning("Tavily search error (%s)", type(exc).__name__)
    gemini_key = _secret(settings, "gemini_api_key")
    if gemini_key:
        model = getattr(settings, "gemini_chat_model", "gemini-3.5-flash-lite")
        try:
            return await _gemini_grounded(gemini_key, model, query)
        except Exception as exc:
            logger.warning("Gemini grounded search error (%s)", type(exc).__name__)
    return None


def is_live_search_configured(settings: Any) -> bool:
    return bool(_secret(settings, "tavily_api_key") or _secret(settings, "gemini_api_key"))
