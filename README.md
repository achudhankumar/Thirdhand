# Thirdhand AI — Phase 1 stabilization

This is the canonical modular repository, based on the original user ZIP. It is a **single-business development baseline**, not a multi-tenant SaaS release. No customer accounts, Embedded Signup or Coexistence have been added. Nothing has been deployed.

Read `PHASE1_IMPLEMENTATION_REPORT.md` for verification, limitations and the exact changed-file list. `PHASE1_CHANGELOG.md` records logical changes. `docs/PHASE1_MIGRATIONS.md` covers data upgrade, operator review, backup and rollback. Original modular baseline: commit `d347177` on branch `phase1/stabilize`; the original ZIP is retained in `../phase1-checkpoint/`.

## Preserved functionality

- Official Meta Cloud API message/media transport, signed durable incoming webhooks, buttons and lists.
- Real AI function calling with validated tool arguments; Tamil, Tanglish and English support.
- Railway live status/PNR/search (RapidAPI), scheduled bus routes (Google), flight offers (Amadeus), Google Places and storefront product comparison. Each needs its actual provider credentials and entitlement. Amadeus defaults to test data.
- Booking slots, explicit separate checkout confirmation, optimistic revision claims and real Playwright checkout. No active merchant profile is included; checkout is not a completed booking or payment.
- ffmpeg voice normalization, OpenAI transcription, supported image extraction and bounded PDF text extraction. Gemini-only chat does not supply Whisper transcription.
- Global checkout city confirmation, pending city requests, timezone/currency context, name memory, tasks, short reminders, DST ambiguity rejection, regional discovery/adapter freshness and offer ranking. The preserved catalog contains 14 cities, not arbitrary worldwide geocoding.

Fixtures are confined to tests. No real integration has been replaced by a fake provider. Provider/model failures report unavailability. Unknown postcodes do not infer coordinates, merchants, live prices, train positions or opening hours. Old postcode catalog data is explicitly unverified; a city-level reference is not a precise user location. Real shared coordinates still support nearby searches outside the city catalog.

## Runtime and verification setup

Use Python 3.11 through 3.14. Python 3.10 is rejected because the implementation uses `asyncio.timeout`. Production Docker uses Python 3.12. Runtime requirements and transitive constraints are pinned; test tools are separate.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install --no-shell chromium
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pip check
```

Install ffmpeg separately and confirm it is on PATH. The browser fixture requires the matching Playwright Chromium install, or `BROWSER_CHANNEL=chrome` with an installed compatible Chrome. Linux can use `python -m playwright install --with-deps --no-shell chromium`. Docker installs ffmpeg/browser prerequisites. Linux/macOS and hosted CI are not certified merely because Windows tests pass.

## Private local simulator

Run `START_THIRDHAND_WINDOWS.bat`, `./start_thirdhand_mac_linux.sh`, or after installing dependencies:

```powershell
.\.venv\Scripts\python.exe run_thirdhand.py --local
```

The launcher creates `.env.development` once with random private session and simulator secrets, explicitly selects development/local storage and binds to `127.0.0.1`. It does not overwrite `.env` or install packages into a system interpreter. Open `http://127.0.0.1:8000/simulator`. Enter the `SIMULATOR_TOKEN` from your private `.env.development` in the password field. Do not paste it into a shared chat, terminal log or source control. It is not embedded in the HTML or printed by the launcher.

The simulator requires a loopback peer and Host, same-origin requests and a private bearer token. It rejects caller-supplied `from`/phone identities. Each browser gets separate opaque local session state, outside production memory. Merchant checkout and live reminder delivery are disabled there; provider reads and AI calls are real if you explicitly configure their keys. Production simulator routes return 404.

Without AI/provider credentials, the UI can exercise language, city, tasks and memory, and truthfully reports unavailable live results. It does not simulate successful provider calls. Local storage imports legacy JSON once into adjacent `.sqlite3` files without changing the original JSON; corrupt imports fail closed.

## Explicit production settings — configuration only

Copy `.env.example` to a private `.env` and fill real Astra, stable random session-HMAC, AI and Meta fields. `ENVIRONMENT=production` is the default. Missing credentials, known published default secrets, demo/local fallback and simulator flags cause startup failure. There is no automatic demo conversion.

Set `META_API_VERSION` explicitly only after verifying your app and currently supported official Meta version. There is no v20.0 default. The audit could not retrieve some Meta developer pages (HTTP 429); no supported-version/live transport certification is implied by fixture tests. Keep any unverified setup offline. `.env` aliases from the original repository remain supported.

`THIRDHAND_ENV_FILE` explicitly selects another environment file. `PROVIDER_REGISTRY` can select an administrator-maintained global-provider configuration; its `token_env` credentials must be supplied in the process environment. Registry endpoints are not customer-editable. `ENABLE_OPEN_METEO=true` enables the existing optional weather adapter. Do not store real customer data in a cloud-synced development folder.

## Queue and outgoing delivery

The SQLite inbox acknowledges a signed webhook only after atomic persistence. Overload returns 503 for the whole new batch, with no silent per-sender discard. Nested input, sender, timestamps, media and status shapes are bounded/validated. Delivery statuses are stored and reconciled; Coexistence events are not implemented in Phase 1.

Claims use tokens, expiry and heartbeats. A later job for the same sender cannot overtake processing/quarantined work. Startup does not steal an unexpired claim. Expired or legacy processing jobs need operator review: an external effect might already have happened. SQLite connections are explicitly closed.

Every application send records intent and then provider acceptance/ID. `accepted` is not `delivered`; delivered/read/failed webhook events are retained without status regression. A timeout, cancellation, missing acceptance ID or uncertain server response preserves the outgoing payload and records uncertainty. It is never blindly resent. Ambiguous merchant checkout also quarantines the job, keeps the booking pending and informs the user when possible; model fallback cannot hide that ambiguity.

Free-form processing/delivery checks the original verified incoming 24-hour window. Stale jobs cannot run tools. There is no approved-template sender in Phase 1, so expired sends/reminders are blocked rather than improvised. `stop` cancels booking/reminders and records opt-out; `start` resumes replies. `reset`/`delete my data` clears session memory and queued reminders, but does not promise erasure of operational records/backups.

Use **one worker on one host with persistent local storage**. The claim improvements do not certify distributed Astra/SQLite atomicity or multi-host execution. Stop the owning worker before resolving an expired/uncertain job. See the migration runbook for the metadata-only operator tools. Successful payloads are cleared after seven days; dedup tombstones remain. Full retention, alerting and disaster recovery remain open.

## Commands and regional behavior

Examples: `London`, `trichy`, `Madurai`, `yes` to confirm a pin/city switch; `clear location`; `time`; `my name is ...`; `task call home`; `tasks`; `done 1`; `calendar`; `remind YYYY-MM-DD HH:MM description`; `cancel`; `stop`; `start`; `reset`. Language selection remains available; postal codes are optional.

Reminders use the confirmed city's timezone, reject skipped/repeated DST times, require a recent verified WhatsApp message, and must fit both the next 23 hours and the remaining customer-service window. Dispatch is transactional and deduplicated. Delayed reminders expire instead of sending late/outside the window.

A shared location is a snapshot. Known city centroids support explicitly city-scoped discovery, not a claim of device position. Named directories and Maps search links have unverified current inventory/hours. Indian rail/shopping adapters remain regional; no universal country coverage is claimed.

## Booking safety

Active `config/booking_profiles.json` stays empty until a merchant-specific flow, permissions, inventory and portable checkout URL are actually verified. `booking_profiles.default.json` contains unverified examples, not production integrations. Do not activate generic selectors as a substitute for that work. No payment-submission profile is approved.

Configured profiles use HTTPS host allowlists and public-address checks. Browser requests and actions check active job ownership. A network egress firewall and OS resource isolation are still required before production merchant use; DNS prechecks alone cannot remove rebinding races. PDF work has input/page/output/time limits and runs in a killable subprocess, with CPU/address-space limits where the OS supports them.

## Container checks, without deployment

```powershell
docker compose build
# To run tests in an image, include the test tools explicitly:
docker build --build-arg INSTALL_TEST_DEPS=true -t thirdhand-phase1-tests .
docker run --rm thirdhand-phase1-tests python -m pytest -q
```

Docker was unavailable on the implementation host; these image builds were not executed. Compose binds the published API port to loopback and uses a persistent volume. Do not start a public service as part of Phase 1. `/health` is a basic liveness response; `/ready` checks worker liveness and SQLite access, not every external integration or queue-lag SLO.

## Known remaining work

No multi-tenancy, user accounts, per-tenant credentials, Embedded Signup, Coexistence, billing or subscription management exists. No live WhatsApp handset, Astra, AI inference, merchant, rail, maps or flight transaction was certified. Full security testing, regional eligibility/compliance, production monitoring, complete erasure/retention, load/failover and deployment verification remain open. Phase 2 must wait for explicit approval of Phase 1 completion.
