# Phase 1 engineering record

Scope: approved Phase 1 only. No multi-tenancy, Embedded Signup, Coexistence or deployment.

## Canonical source and recovery

Canonical source is this modular `thirdhand-ai-agent` repository, extracted without changes from the original user ZIP (SHA-256 `ffdec5b770623f3aa9568280865038f4aa4b15ad28017e5ba0aa9afedc55897d`). No repository evidence contradicts using it as the baseline. Branch: `phase1/stabilize`. Baseline commit: `d347177`. Recoverable original ZIP and source manifest are in `../phase1-checkpoint/`. Existing `../thirdhand-global` stays intact as provenance and a verified behavior reference.

Baseline rerun before code changes: modular **51 passed**, global **21 passed** on Python 3.14.7 / Windows. XML results are in `../phase1-checkpoint/`. Original modular lint: 10 findings, 6 files fail formatting (audit evidence).

Preservation contract: retain real AI/function calling, media/ffmpeg, provider adapters, slot/confirmation/CAS booking, bounded WhatsApp payloads and signed durable intake. Carry forward global city confirmation, timezone/currency, tasks/name memory, short reminders and DST checks, region-aware honest discovery, PDF extraction, and uncertain-send quarantine. The original global checkout and its tests remain available. Unverified merchants stay disabled; no fixture becomes a production provider.

## Logical changes

Implementation and verification entries are appended as each logical change completes. Final changed-file list, remaining issues, security results and rollback instructions will accompany the implementation report.

### 1. Explicit configuration and isolated simulation

Changed `config/__init__.py`, `config/settings.py`, `main.py`, `routers/simulator.py`, `services/simulator.html`, required SDK imports in memory/orchestration, booking simulator guard, test configuration and security regressions. Production simulator is inaccessible; development requires loopback peer/Host, same-origin checks and a private token. Browser identities use separate simulator storage; arbitrary phone identities are rejected. No payment/merchant checkout can run from simulation. Missing configuration no longer synthesizes secrets or demo mode. Required Pydantic 2/SDK imports fail explicitly. Targeted verification: **42 passed**. Security review: no token embedded in HTML/errors; no production session access from local simulation.

### 2. Durable intake, fenced claims and outgoing delivery

Changed `database/inbox.py`, `routers/webhook.py`, `main.py`, `services/jobs.py`, `services/outbound.py`, `services/http.py`, `services/whatsapp_client.py`, webhook fixtures and reliability regressions. Additive SQLite schema version 2; explicit connection closure; atomic bounded intake; validated event field/body/timestamps; durable delivery statuses; claim tokens, per-sender serialization and heartbeats. Startup never steals live work. Expired work is held for review because external effects may already have happened. Outgoing payload and provider ID/status are preserved; ambiguous/cancelled sends never automatically repeat. Free-form delivery checks the trusted incoming service window. Existing recovery test now asserts non-stealing behavior rather than the audited unsafe reset. Targeted verification: **58 passed**. Security review: no raw upstream errors or bearer tokens logged; stale workers cannot finish or begin another outgoing action; no Coexistence handler was added.

### 3. Honest location/results and preserved global functionality

Changed onboarding/fallback helpers, LocalScout unknown-location behavior, local memory persistence, global-support adapters/catalog, `services/global_features.py`, orchestration and PDF processing. Unknown postcodes do not infer coordinates, merchants or live information. Existing postal references are explicitly unverified and require confirmation. Global city confirmation, pending requests, timezone/currency, tasks/name memory, regional discovery/freshness/ranking and DST-aware reminders are integrated with real session/inbox storage. Reminder dispatch is durable, deduplicated, bounded by the original incoming service window and cancelled by stop/reset. PDF text extraction uses a bounded killable subprocess; real ffmpeg and browser booking paths remain. Legacy JSON imports once to transactional local SQLite and remains intact; corrupt imports fail instead of erasing data. Cancellation commands precede onboarding. Targeted verification: **48 passed**. Security review: city catalog centroids never become a precise user location; simulated checkout/delivery remains disabled; Gemini-only chat cannot silently invoke unsupported Whisper transcription.

### 4. Recovery operations, dependency/runtime support and final review

Added `manage_inbox.py` and the migration/rollback runbook. Operator backups include committed SQLite WAL data and run an integrity check. Reviewed quarantine decisions are recorded without resending or replaying handlers. Successful payload cleanup preserves deduplication tombstones; unresolved effects remain available for review. Expired incoming work is stopped before AI/tools. Session operations and merchant browser steps also check job ownership. A final review found that generic AI fallback could hide ambiguous checkout; a dedicated exception now reaches the worker quarantine and a regression verifies the complete path. Another regression preserves real nearby searches outside the catalog using user-shared coordinates.

Pinned runtime/dev requirements and transitive constraints, including the existing Linux uvicorn optional event-loop dependency (version sourced from the official PyPI project). Updated Python compatibility checks, loopback launchers, production/local examples, Docker inputs, CI checks and safe setup documentation; restored source references remain intact. Test tooling is not installed in the production image unless requested. Ruff formatting and lint now pass. Intermediate full suite: **107 passed** on Python 3.14 and **107 passed** on Python 3.12 before the final review regressions. Python 3.12's installed patch level emits an Astra SSL-reuse warning; this is recorded, not suppressed. Final run results supersede intermediate counts in the implementation report.

A temporary development server was started only on loopback and then stopped. `/health` and `/ready` returned 200; private simulator page loaded without embedding its token; unsigned requests returned 403; arbitrary phone identities returned 400; cross-origin requests returned 403; real isolated task persistence worked. No external credentials/provider call or public deployment was used. Security review: no environment files or runtime data are tracked, recovery never infers an external outcome, and the existing global checkout is retained unchanged.
