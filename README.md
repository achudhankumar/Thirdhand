# Thirdhand

Async WhatsApp concierge for English, Tamil and Tanglish. Python 3.11+,
FastAPI, Astra Data API, OpenAI GPT-4o/Whisper, Playwright and HTTP provider clients.

## What is implemented

| Capability | Implementation | External requirement |
| --- | --- | --- |
| Railway | Live status, PNR and between-station searches | RapidAPI IRCTC subscription |
| Bus | Scheduled bus transit routing | Google Routes API key and regional coverage |
| Flight | INR offers for IATA airport pairs | Amadeus credentials; default test environment is test data |
| Booking | Durable slots, confirmation gate, revision claim and browser checkout | Merchant-specific validated profile |
| Shopping | Parallel Amazon/Flipkart HTML extraction, observed prices and ratings, review samples | Accessible storefront HTML; blocks/layout changes produce explicit unavailable results |
| Local | Google Places New search biased by shared coordinates | Places API key and billing |
| Voice | ffmpeg normalization, Whisper transcription, contextual assistant response | ffmpeg and OpenAI key |
| Image | GPT-4o visible bill/prescription extraction with uncertainty | OpenAI key |

No credentials are shipped. Tests are offline contract/behavior tests with fixture
responses. A real Chromium-based browser exercises a fixture checkout page. Passing them
does not establish live merchant compatibility or language-model accuracy.
There is no verified BookMyShow/Zomato/Kamala integration included: their current
flows, authentication, seat maps and checkout-session portability must be validated
with the merchant. `config/booking_profiles.json` deliberately contains an empty
list. Unsupported merchants fail before creating a cart. This repository is a
production-oriented baseline, not a credentialed, certified live booking service.

## Windows PowerShell setup

Run in the repository directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install --no-shell chromium
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
notepad .env
```

Install ffmpeg with your OS package manager and ensure `ffmpeg -version` works.
Python 3.11 can be selected with `py -3.11` instead. No virtual-environment
activation is needed. Linux uses `python3.12 -m venv .venv` and
`.venv/bin/python`; install Chromium with `--with-deps --no-shell chromium`.
The Docker image installs ffmpeg and browser dependencies automatically.
If an existing system Chrome/Edge is preferred, set BROWSER_CHANNEL=chrome or
BROWSER_CHANNEL=msedge. The default chromium channel uses the Playwright download.
The included validation run used installed Chrome because the browser CDN download
failed with TLS transport errors in the build environment.

Fill ASTRA_DB_API_ENDPOINT, ASTRA_DB_APPLICATION_TOKEN, SESSION_HASH_KEY,
OPENAI_API_KEY, META_ACCESS_TOKEN, META_PHONE_NUMBER_ID, META_VERIFY_TOKEN and
META_APP_SECRET. The random value above is SESSION_HASH_KEY: keep it stable.
Use the database-origin HTTPS Data API endpoint, not a URL with `/api/json`.
The Astra token must create/read/write collections in ASTRA_DB_KEYSPACE.
Optional provider credentials enable their tools; missing credentials produce
explicit tool errors. Amadeus defaults to its test environment. Set
AMADEUS_ENVIRONMENT=production only with production entitlement.

The Graph API defaults to the requested v20.0. Verify that your Meta app still
supports this version before launch and set META_API_VERSION to a supported version
if necessary. Test recipients and business permissions must be configured in Meta.

## Verify and start

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -c "import asyncio; from config.settings import get_settings; from database.astra_db import AstraMemory; asyncio.run(AstraMemory(get_settings()).initialize()); print('Astra ready')"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-graceful-shutdown 260
```

`GET /health` returns the agent identity; `GET /ready` checks that the inbox worker
is running. Startup validates core credentials and opens Astra before serving.
The collection uses only `_id` and `revision` indexes. An existing collection with
incompatible options requires a different ASTRA_DB_COLLECTION name.

In a second terminal run `ngrok http 8000`. Copy its HTTPS forwarding origin and
append `/webhook` in the Meta WhatsApp webhook configuration. Use exactly the
META_VERIFY_TOKEN value, then subscribe to `messages`. Meta signs POST bodies with
META_APP_SECRET; the gateway verifies the raw bytes before JSON parsing.

From an allowed test recipient send:

- `12606 train enga iruku`
- `Trichy to Chennai Egmore trains tomorrow`
- `PNR 1234567890` using your own valid PNR
- `MAA to DEL flights tomorrow`
- `Best earbuds under 2000`
- Share a location, then `Nearby 24 hour pharmacies`
- `Kamala theatre la ticket book pannu`; supply the requested slots one at a time
- Send a Tamil or English voice note shorter than three minutes
- Send a clear bill image; check extracted amounts against the image

A ready booking shows a summary and asks for `confirm checkout`. No payment is
submitted. `cancel`, `stop`, `menu` cancel the active flow. `reset` physically deletes
session memory. Location is a received snapshot; this does not subscribe to
continuous live-location updates. Avoid real prescriptions in shared test systems.

## Booking integration

Profiles are administrator-maintained, never supplied by the model or WhatsApp
user. A profile has these fields:

| Field | Meaning |
| --- | --- |
| merchant | Exact theatre/restaurant slot value, matched case-insensitively |
| kind | `movie` or `food` |
| hosts | Exact HTTPS host allowlist, including required asset/payment hosts |
| start_url | Validated merchant entry page |
| steps | Ordered `fill`, `select`, `check`, or `click` operations |
| step.selector | Exact CSS selector verified against the merchant |
| step.slot | Slot name supplying the fill/select value |
| step.value | Constant fill/select value when no slot is used |
| checkout_selector | Visible selector proving checkout readiness |
| checkout_path_prefix | Path prefix required on the returned checkout URL |
| checkout_link_selector | Optional anchor containing a portable checkout URL |

Movie slots are theatre, movie, date, showtime and seat_count; seat_class is
optional. Food slots are restaurant, items, quantity, date, showtime and
delivery_address. Dates use YYYY-MM-DD and time HH:MM in Asia/Kolkata.
Validate inventory, price, seat mapping and all fixed actions before activating a
profile. Do not configure payment-submission buttons. Profiles support standard
forms, not arbitrary dynamic seat-map protocols. No CAPTCHA bypass, stored OTPs,
merchant login session or fabricated UPI intent is provided. Verify that the link
works on a separate phone after the isolated browser closes; some merchant carts
are cookie-bound and cannot be handed off with a URL alone.

Browser navigation and resources are restricted to configured public HTTPS hosts.
Use a network egress firewall as an additional boundary for browser processes;
application DNS checks alone do not eliminate DNS-rebinding races.

## Reliability and operations

One process/worker/replica is required with the bundled SQLite inbox. Ingress stores
signed messages transactionally before returning 200, deduplicates IDs, and rejects
new work with 503 when full. A single worker serializes processing. SQLite must
reside on persistent local storage; never run multiple replicas sharing this file
or an ephemeral filesystem. Scaling requires a shared durable queue and distributed
per-user execution leases. FastAPI BackgroundTasks alone would lose accepted work
on a crash, so they are not used for business processing here.

Astra stores the last 10 user/assistant messages plus slot state and location in
one HMAC-keyed document with optimistic revision checks. Slot changes and checkout
claims reject stale revisions. External actions are not exactly-once: a crash or
send timeout may leave delivery uncertain. Failed inbox rows are retained for
operator review and are not automatically reprocessed. On restart, rows marked
processing become pending. A previously claimed checkout remains pending and must
be reviewed before a retry. A verified checkout becomes checkout_ready, never paid.
Do not reset booking state merely to repeat an uncertain merchant action.

Inspect the durable queue locally:

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('data/inbox.sqlite3'); print(c.execute('SELECT status,count(*) FROM inbox GROUP BY status').fetchall())"
```

Treat inbox payloads and Astra history as personal data. Restrict volume/database
access and backups. Successfully completed inbox rows expire after seven days on
the next enqueue. Failed rows require manual review and deletion. Astra session
expiry is logical after 24 hours of inactivity; physical erasure requires an
operational retention job. `reset` deletes Astra memory but does not erase inbox
records or backups. Apply a coordinated deletion policy before promising complete
account erasure. No private payment credentials are requested or persisted.

Conversation storage contains visible user/assistant turns, not hidden reasoning.
Tool results are bounded and treated as untrusted. Price extraction is best effort;
the review baseline uses English keywords and does not detect fraudulent reviews.
Places opening hours are provider reports, not verified emergency availability.
This service does not retrieve utility account balances or replace medical advice.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Startup fails | Required environment fields, Astra permissions and collection options |
| GET webhook 403 | Token spelling and hub.mode=subscribe |
| POST webhook 403 | App secret and proxy preserving the raw request body |
| Repeated events | Persistent inbox volume, one replica, message-ID dedup retention |
| Accepted but no answer | Worker logs, failed inbox rows, provider credits, recipient allowlist |
| WhatsApp HTTP 400 | Version, phone ID, recipient access, 3-button/20-character limits |
| Tool unavailable | Provider credential, plan entitlement, quota, coverage or schema changes |
| Browser fails | Matching Playwright/Chromium install, Linux dependencies, allowlisted asset hosts |
| Checkout pending | Review merchant cart and logs before retrying; do not repeat blindly |
| Shopping empty | Storefront blocked automation or changed HTML; no price is invented |

Logs record operation names and exception types without raw messages. Protect log
collection and disable proxy request-body logging. Configure external alerting for
failed queue rows, worker failures, provider quotas and checkout_pending records.

## Docker, Render and Railway

```powershell
docker compose build
docker compose run --rm thirdhand python -m pytest -q
docker compose up -d
docker compose logs -f thirdhand
```

Use Docker deployment on Render/Railway, set the repository root to this directory,
set all environment secrets in the provider dashboard, and attach a persistent
volume at `/app/data`. Set INBOX_PATH=/app/data/inbox.sqlite3. Keep one replica and
one Uvicorn worker. Set the health check to `/ready`, allow a 270-second shutdown,
and use the injected PORT. For Render, use a service plan supporting persistent
disks; for Railway, attach a volume and configure the same path. A service without
a persistent volume is not a supported durable deployment. After the service is
healthy, replace the ngrok webhook origin with its public HTTPS origin in Meta.
No cloud account was accessed or deployment performed by this build.

## References

- [AstraPy collection methods](https://docs.datastax.com/en/astra-api-docs/_attachments/python-client/astrapy/collection.html)
- [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
- [OpenAI transcription](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create)
- [Meta WhatsApp Cloud API collection](https://www.postman.com/meta/whatsapp-business-platform/overview)
- [Google Places Text Search](https://developers.google.com/maps/documentation/places/web-service/text-search)
- [Google transit routing](https://developers.google.com/maps/documentation/routes/transit-route)
- [Amadeus flight offers](https://github.com/amadeus4dev/developer-guides/blob/master/docs/resources/flights.md)
