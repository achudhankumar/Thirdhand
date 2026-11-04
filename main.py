"""Thirdhand ASGI application. Run a single worker with a persistent inbox volume."""

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from config.settings import get_settings
from database.astra_db import AstraMemory
from database.inbox import Inbox
from routers.webhook import router
from services.llm_orchestrator import LLMOrchestrator
from services.tools.booking_tool import BookingTool
from services.tools.local_tool import LocalTool
from services.tools.shopping_tool import ShoppingTool
from services.tools.transit_tool import TransitTool
from services.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)


async def run_worker(app: FastAPI, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            item = await app.state.inbox.claim()
            if item is None:
                try:
                    await asyncio.wait_for(stop.wait(), 0.5)
                except TimeoutError:
                    continue
            else:
                success = False
                try:
                    async with asyncio.timeout(240):
                        await app.state.orchestrator.handle_message(item["message"])
                    success = True
                except Exception as exc:
                    logger.error(
                        "Message processing failed (%s); retained for review",
                        type(exc).__name__,
                    )
                await app.state.inbox.finish(item["id"], success)
        except Exception as exc:
            logger.error("Inbox worker failed (%s)", type(exc).__name__)
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if not getattr(settings, "demo_fallback", False):
        has_llm = bool(
            settings.openai_api_key.get_secret_value()
            or getattr(settings, "gemini_api_key", settings.openai_api_key).get_secret_value()
        )
        if not has_llm:
            raise ValueError("Required credential missing: openai_api_key")
        for field in (
            "meta_access_token",
            "meta_verify_token",
            "meta_app_secret",
        ):
            if not getattr(settings, field).get_secret_value():
                raise ValueError(f"Required credential missing: {field}")
    if not settings.meta_phone_number_id.isdigit():
        raise ValueError("META_PHONE_NUMBER_ID must be numeric")
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # HTTP client logs can include private IDs in query strings.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("astrapy").setLevel(logging.WARNING)
    memory = AstraMemory(settings)
    await memory.initialize()
    inbox = Inbox(settings.inbox_path, settings.inbox_max_pending)
    await inbox.initialize()
    async with httpx.AsyncClient(
        timeout=settings.http_timeout_seconds,
        follow_redirects=False,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    ) as client:
        whatsapp = WhatsAppClient(settings, client)
        orchestrator = LLMOrchestrator(
            settings,
            memory,
            whatsapp,
            TransitTool(settings, client),
            BookingTool(settings, memory),
            ShoppingTool(client),
            LocalTool(settings, client),
        )
        app.state.settings = settings
        app.state.inbox = inbox
        app.state.orchestrator = orchestrator
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
            await orchestrator.client.close()


app = FastAPI(title="Thirdhand", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "Thirdhand"}


@app.get("/ready")
async def ready():
    from fastapi.responses import JSONResponse

    worker = getattr(app.state, "worker", None)
    healthy = worker is not None and not worker.done()
    return JSONResponse({"ready": healthy}, status_code=200 if healthy else 503)



@app.get("/", include_in_schema=False)
@app.get("/simulator", include_in_schema=False)
async def simulator_page():
    from fastapi.responses import HTMLResponse

    return HTMLResponse(
        """<!DOCTYPE html><html lang="ta"><head><meta charset="utf-8"><title>Thirdhand 🤝 Local WhatsApp Simulator</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>body{font-family:system-ui,sans-serif;background:#0b141a;color:#e9edef;margin:0;padding:20px}
        .wrap{max-width:860px;margin:0 auto;display:grid;grid-template-columns:1fr;gap:16px}
        .card{background:#111b21;border:1px solid #222e35;border-radius:16px;padding:20px}
        h1{color:#00a884;margin:0 0 6px;font-size:20px}
        .badge{display:inline-block;background:#202c33;color:#00a884;padding:4px 10px;border-radius:99px;font-size:12px;margin-bottom:10px}
        .chat{background:#0b141a;padding:16px;border-radius:12px;height:380px;overflow-y:auto;margin-bottom:12px;border:1px solid #222e35}
        .msg-u{background:#005c4b;color:#fff;padding:10px 14px;border-radius:12px;margin:8px 0 8px auto;max-width:78%;white-space:pre-wrap;font-size:14px}
        .msg-b{background:#202c33;color:#e9edef;padding:10px 14px;border-radius:12px;margin:8px auto 8px 0;max-width:82%;white-space:pre-wrap;font-size:14px;border:1px solid #2a3942}
        .btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
        .rbtn{background:#182229;color:#00a884;border:1px solid #00a884;padding:7px 14px;border-radius:8px;cursor:pointer;font-weight:600;font-size:13px}
        .rbtn:hover{background:#00a884;color:#0b141a}
        .row{display:flex;gap:8px}
        input{flex:1;padding:12px;border-radius:10px;border:1px solid #2a3942;background:#202c33;color:#fff;font-size:14px}
        button.send{background:#00a884;color:#0b141a;font-weight:700;border:none;padding:12px 20px;border-radius:10px;cursor:pointer}
        button.reset{background:#2a3942;color:#d1d7db;border:none;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:12px;float:right}</style></head>
        <body><div class="wrap"><div class="card">
        <button class="reset" onclick="sendMsg('reset')">🔄 Reset Onboarding</button>
        <h1>Thirdhand 🤝 — WhatsApp AI Super-Agent</h1>
        <div id="pbadge" class="badge">🔒 Onboarding Gate: Language ➔ Place ➔ 6-Digit Pincode</div>
        <div id="chat" class="chat"></div>
        <div class="row">
          <input id="msg" placeholder="Type here (or click a button above)..." onkeydown="if(event.key==='Enter')sendMsg()" />
          <button class="send" onclick="sendMsg()">Send ➤</button>
        </div></div></div>
        <script>
        async function sendMsg(preset){
          const input=document.getElementById('msg');const chat=document.getElementById('chat');
          const text=(preset!==undefined)?preset:input.value.trim();if(!text)return;
          if(preset===undefined)input.value='';
          const u=document.createElement('div');u.className='msg-u';u.textContent=text;chat.appendChild(u);
          const res=await fetch('/api/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:'919876543210',text})});
          const data=await res.json();
          const b=document.createElement('div');b.className='msg-b';b.textContent=data.reply||data.error;
          if(data.buttons&&data.buttons.length){
            const bw=document.createElement('div');bw.className='btns';
            data.buttons.forEach(btn=>{
              const el=document.createElement('button');el.className='rbtn';el.textContent=btn.title;
              el.onclick=()=>sendMsg(btn.id);bw.appendChild(el);
            });
            b.appendChild(bw);
          }
          chat.appendChild(b);chat.scrollTop=chat.scrollHeight;
          if(data.profile){
            const p=data.profile;
            document.getElementById('pbadge').textContent = p.pincode
              ? `✅ Locked: ${p.language?.toUpperCase()} | ${p.place} | Pincode: ${p.pincode} (${(p.surrounding_areas||[]).slice(0,3).join(', ')})`
              : `🔒 Onboarding Step: ${p.onboarding_step||'awaiting_language'} | Lang: ${p.language||'-'} | Place: ${p.place||'-'}`;
          }
        }
        window.onload=()=>sendMsg('hi');
        </script></body></html>"""
    )


@app.post("/api/simulate")
async def api_simulate(payload: dict):
    """Local testing endpoint with full 3-step onboarding (Language -> Place -> Pincode & Surroundings)."""
    user_id = str(payload.get("from", "919876543210"))
    text = str(payload.get("text", "")).strip()
    if not text:
        return {"error": "Message text is required"}
    orchestrator = getattr(app.state, "orchestrator", None)
    if orchestrator is None:
        return {"error": "Orchestrator is not initialized"}
    try:
        result = await orchestrator.handle_interactive_turn(user_id, text)
        return {"status": "ok", **result}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
