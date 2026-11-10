"""Explicit local-only simulator with separate sessions and no merchant actions."""

import hashlib
import hmac
import json
import logging
import re
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from database.astra_db import AstraMemory
from services.llm_orchestrator import LLMOrchestrator
from services.tools.booking_tool import BookingTool
from services.tools.local_scout_tool import LocalScoutTool
from services.tools.shopping_tool import ShoppingTool
from services.tools.transit_tool import TransitTool

logger = logging.getLogger(__name__)
router = APIRouter(include_in_schema=False)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class SimulatorInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=8000)


def local_access(request: Request, authenticate: bool = False):
    settings = getattr(request.app.state, "settings", None)
    if (
        settings is None
        or settings.environment != "development"
        or not settings.enable_simulator
        or request.client is None
        or request.client.host not in {"127.0.0.1", "::1"}
        or request.url.hostname not in LOCAL_HOSTS
    ):
        raise HTTPException(404, "Not found")
    origin = request.headers.get("origin")
    if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
        raise HTTPException(403, "Invalid origin")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Invalid origin")
    if authenticate:
        expected = settings.simulator_token.get_secret_value()
        supplied = request.headers.get("authorization", "")
        if len(expected.encode()) < 32 or not hmac.compare_digest(
            supplied.encode(), ("Bearer " + expected).encode()
        ):
            raise HTTPException(403, "Invalid simulator credential")
    return settings


async def initialize_simulator(settings, http):
    config = settings.model_copy(
        update={
            "use_local_memory_fallback": True,
            "local_memory_path": settings.simulator_path,
        }
    )
    memory = AstraMemory(config)
    await memory.initialize()
    return LLMOrchestrator(
        config,
        memory,
        None,
        TransitTool(config, http),
        BookingTool(config, memory, allow_checkout=False),
        ShoppingTool(http),
        LocalScoutTool(config, http),
    )


@router.get("/", response_class=HTMLResponse)
@router.get("/simulator", response_class=HTMLResponse)
async def simulator_page(request: Request):
    local_access(request)
    html = Path(__file__).parents[1] / "services" / "simulator.html"
    return HTMLResponse(
        html.read_text(encoding="utf-8"),
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'",
            "Referrer-Policy": "no-referrer",
        },
    )


@router.post("/api/simulate")
async def api_simulate(request: Request):
    settings = local_access(request, authenticate=True)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 65536:
            raise HTTPException(413, "Request too large")
    try:
        payload = SimulatorInput.model_validate(json.loads(body))
    except (ValueError, ValidationError):
        raise HTTPException(
            400, "Provide text only, between 1 and 8000 characters"
        ) from None
    nonce = request.cookies.get("thirdhand_simulator", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,64}", nonce):
        nonce = secrets.token_urlsafe(32)
    user_id = (
        "sim:"
        + hmac.new(
            settings.simulator_token.get_secret_value().encode(),
            nonce.encode(),
            hashlib.sha256,
        ).hexdigest()
    )
    service = getattr(request.app.state, "simulator_orchestrator", None)
    if service is None:
        raise HTTPException(503, "Simulator unavailable")
    try:
        result = await service.handle_interactive_turn(user_id, payload.text.strip())
    except Exception as exc:
        logger.warning("Simulator turn failed (%s)", type(exc).__name__)
        raise HTTPException(
            503, "Service unavailable; no live result is confirmed"
        ) from None
    response = JSONResponse(
        {"status": "ok", **result}, headers={"Cache-Control": "no-store"}
    )
    response.set_cookie(
        "thirdhand_simulator",
        nonce,
        httponly=True,
        samesite="strict",
        secure=urlsplit(str(request.url)).scheme == "https",
        path="/api/simulate",
    )
    return response
