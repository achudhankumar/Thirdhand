"""Thirdhand ASGI application. Run a single worker with a persistent inbox volume."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pathlib import Path

from config.settings import get_settings
from database.astra_db import AstraMemory
from database.inbox import Inbox, LostLease
from routers.simulator import router as simulator_router
from routers.webhook import router
from services.jobs import JobContext, current_job
from services.llm_orchestrator import LLMOrchestrator
from services.outbound import SendPolicyError
from services.tools.booking_tool import BookingTool, BookingUncertain
from services.tools.local_scout_tool import LocalScoutTool
from services.tools.shopping_tool import ShoppingTool
from services.tools.transit_tool import TransitTool
from services.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)


async def _renew_lease(inbox, item, handler):
    try:
        while True:
            await asyncio.sleep(max(1, inbox.lease_seconds / 3))
            await inbox.renew(item["id"], item["lease_token"])
    except Exception:
        handler.cancel()
        raise


async def _process_message(app, message):
    now = time.time()
    if not 0 <= now - min(float(message.get("timestamp", 0)), now) < 86400:
        raise SendPolicyError("Incoming job expired; external actions were not run")
    await app.state.orchestrator.handle_message(message)


async def run_worker(app: FastAPI, stop: asyncio.Event) -> None:
    inbox = app.state.inbox
    cleanup_at = 0
    while not stop.is_set():
        try:
            if time.monotonic() >= cleanup_at:
                await inbox.cleanup()
                cleanup_at = time.monotonic() + 3600
            await inbox.dispatch_due()
            item = await inbox.claim()
            if item is None:
                try:
                    await asyncio.wait_for(stop.wait(), 0.05)
                except TimeoutError:
                    pass
                continue
            message = item["message"]
            context = current_job.set(
                JobContext(
                    inbox,
                    item["id"],
                    item["lease_token"],
                    message.get("from", ""),
                    min(float(message.get("timestamp", 0)), time.time()),
                )
            )
            handler = asyncio.create_task(_process_message(app, message))
            heartbeat = asyncio.create_task(_renew_lease(inbox, item, handler))
            success, review, error = False, False, None
            try:
                async with asyncio.timeout(
                    app.state.settings.processing_timeout_seconds
                ):
                    await handler
                success = True
            except SendPolicyError:
                review, error = False, "send_policy_blocked"
            except BookingUncertain as exc:
                review, error = True, type(exc).__name__
                logger.error("Booking checkout needs operator review (%s)", error)
            except asyncio.CancelledError:
                if asyncio.current_task().cancelling():
                    raise
                error = "lease_renewal_failed"
            except Exception as exc:
                error = type(exc).__name__
                logger.error("Message processing failed (%s)", error, exc_info=True)
            finally:
                handler.cancel()
                heartbeat.cancel()
                await asyncio.gather(handler, heartbeat, return_exceptions=True)
                current_job.reset(context)
            try:
                await inbox.finish(
                    item["id"], success, item["lease_token"], review=review, error=error
                )
            except LostLease:
                logger.warning("Stale worker result ignored")
        except Exception as exc:
            logger.error("Inbox worker failed (%s)", type(exc).__name__)
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.validate_startup()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # HTTP client logs can include private IDs in query strings.
    for name in ("httpx", "httpcore", "httpx2", "httpcore2", "openai", "astrapy"):
        logging.getLogger(name).setLevel(logging.WARNING)
    memory = AstraMemory(settings)
    await memory.initialize()
    inbox = Inbox(
        settings.inbox_path, settings.inbox_max_pending, settings.job_lease_seconds
    )
    await inbox.initialize()
    async with httpx.AsyncClient(
        timeout=settings.http_timeout_seconds,
        follow_redirects=False,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    ) as client:
        whatsapp = WhatsAppClient(settings, client, inbox)
        orchestrator = LLMOrchestrator(
            settings,
            memory,
            whatsapp,
            TransitTool(settings, client),
            BookingTool(settings, memory),
            ShoppingTool(client),
            LocalScoutTool(settings, client),
        )
        orchestrator.global_features.inbox = inbox
        app.state.settings = settings
        app.state.inbox = inbox
        app.state.orchestrator = orchestrator
        if settings.enable_simulator:
            from routers.simulator import initialize_simulator

            app.state.simulator_orchestrator = await initialize_simulator(
                settings, client
            )
        stop = asyncio.Event()
        worker = asyncio.create_task(run_worker(app, stop))
        app.state.worker = worker
        try:
            yield
        finally:
            stop.set()
            try:
                await asyncio.wait_for(worker, 250)
            except TimeoutError:
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)
            if orchestrator.client is not None:
                await orchestrator.client.close()
            simulator = getattr(app.state, "simulator_orchestrator", None)
            if simulator is not None and simulator.client is not None:
                await simulator.client.close()


app = FastAPI(title="Thirdhand", version="1.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "Thirdhand"}


@app.get("/ready")
async def ready():
    from fastapi.responses import JSONResponse

    worker = getattr(app.state, "worker", None)
    healthy = worker is not None and not worker.done()
    if healthy:
        try:
            await app.state.inbox.counts()
        except Exception:
            healthy = False
    return JSONResponse({"ready": healthy}, status_code=200 if healthy else 503)


@app.get("/media/{filename}")
async def get_media_file(filename: str):
    safe_name = Path(filename).name
    target = Path("data/generated_diagrams") / safe_name
    if not target.exists():
        raise HTTPException(404, "Media file not found")
    media_type = "image/jpeg" if safe_name.endswith((".jpg", ".jpeg")) else "image/png"
    return FileResponse(target, media_type=media_type)


app.include_router(simulator_router)
