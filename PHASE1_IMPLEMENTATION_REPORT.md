# Phase 1 implementation report

Date: 4 November 2026. Scope: Phase 1 only, ready for owner review. No Phase 2, customer accounts, multi-tenancy, Embedded Signup, Coexistence, subscriptions or production deployment was performed.

## Canonical source and checkpoint

The canonical repository is `thirdhand-ai-agent`, extracted from the original modular Thirdhand AI ZIP, not a replacement built from scratch. The original 43-file source was committed before application changes as `d347177` on branch `phase1/stabilize`. ZIP SHA-256: `ffdec5b770623f3aa9568280865038f4aa4b15ad28017e5ba0aa9afedc55897d`.

`../phase1-checkpoint/original-modular-baseline.zip` and `original-modular-manifest.json` preserve that checkpoint. The audit reports and original `../thirdhand-global` checkout remain intact. The stale nested global copy was not selected as a baseline. No live customer database, cloud account or deployed configuration was migrated.

## Results against the approved objectives

| Objective | Implemented result | Verification |
| --- | --- | --- |
| Public simulator vulnerability | Production routes return 404; development requires explicit enablement, loopback peer/Host, same-origin checks and private bearer token. Caller-supplied phone identity rejected. Opaque browser sessions use separate real storage. Merchant checkout/live reminder delivery disabled in simulation. | Production/remote/origin/token/identity tests, separate-storage test and real loopback HTTP smoke check |
| Unsafe demo/default secrets | No synthesized demo credentials or automatic fallback after invalid configuration. Production rejects simulator/local/demo flags and known published defaults. Development also rejects known unsafe nonempty Meta secrets. HMAC key and simulator token are explicitly provided/generated privately. | Empty configuration, default credentials and production flag regressions; launcher configuration/secret-output test |
| Fabricated results/geography | Fixed live train/pharmacy/rating/fare replies removed. Unknown postcodes return no inferred geography. Legacy postcode references are labeled unverified and require confirmation. Real shared coordinates still reach nearby tools outside the city catalog. | No-fabrication, unknown postcode, LocalScout and coordinate-preservation regressions |
| Webhook intake | Bounded typed nested validation, explicit `messages` field dispatch, timestamp/body/media checks, atomic acceptance/backpressure and no silent per-sender drops. Existing Cloud API status events are durably reconciled. Coexistence remains unimplemented. | Signed 31-message batch, overload rollback, malformed batch, signature, deduplication and status tests |
| Safe job ownership/recovery | Tokenized transactional claims, same-sender serialization, heartbeat renewal, stale-owner rejection and conservative expiry quarantine. Initialization cannot steal active work. Stale jobs cannot execute AI/tools or new session mutations. | Concurrent claim, initializer, expiry, stale-memory, migration and worker integration tests |
| SQLite lifecycle | Every connection is explicitly closed. Version 2 migration is additive/transactional. Development local memory imports legacy JSON once into SQLite with cross-instance CAS; original JSON remains untouched. | Connection tracking, corrupt import, one-time import, atomic CAS and old-schema tests |
| Outgoing messages/uncertainty | Durable outgoing intent, acceptance ID, errors and delivery events. Provider acceptance is distinct from delivery. Timeouts/cancellation/unknown responses are held as uncertain and never blindly repeated. Ambiguous checkout escapes model fallback and quarantines the job, preserving pending booking state. | Real worker/HTTP-client fixture integration, cancellation/timeout/rejection/replay/status-order tests and end-to-end uncertain checkout test |
| Dependency/runtime/quality | Exact runtime and development pins plus transitive constraints; required SDK imports replace dummy stand-ins. Python 3.10 rejected. Loopback local launcher creates explicit private development configuration without overwriting production `.env`. CI includes Python 3.11/3.12/3.14. Ruff checks pass. | Python 3.12 and 3.14 suites, dependency consistency, launcher regression and lint/format checks |
| Preserve working features | Existing AI/function-calling, provider clients, media normalization/vision, slot/CAS/confirmation booking, interactive messages and webhook controls retained. Global city/timezone/currency, tasks/name memory, reminders/DST, regional discovery/freshness/ranking and real PDF extraction integrated. | Original 51 cases retained, global reference 21 cases still pass, integrated preservation regressions |

## Test baseline and final results

Before application changes, the modular baseline passed **51 tests** and the global checkout reference passed **21 tests**. Historical audit lint had 10 findings and six files requiring formatting.

Final modular suite: **113 passed on Python 3.14**, **113 passed on Python 3.12**. This retains the original 51 cases and adds 62 regressions. Existing test adaptations supply a valid event field/timestamp and explicit fixture Graph version, update the lifespan test double for the added global service, and replace the unsafe “startup steals processing” expectation with the corrected recovery contract. No original test function was deleted to obtain a pass.

The original global reference suite was independently rerun unchanged: **21 passed**. It is a reference application, not an alternate deployment target; its old intake/worker limitations are not claimed repaired there. The corresponding behaviors are preserved and stabilized in the canonical modular application.

Ruff lint and format checks pass. `pip check` reports no broken requirements in both test environments. Syntax parses for declared Python 3.11; its runtime suite and Linux/macOS/container behavior are not locally certified. The installed Python 3.12 patch level emits Astra's warning that SSL connection reuse is disabled on Python 3.12.0–3.12.11; use a maintained newer patch for an eventual deployment. The warning was not hidden.

Tests include actual installed Playwright Chromium fixture checkout, actual ffmpeg audio normalization and actual subprocess PDF parsing. External Meta/Astra/AI/maps/rail/flight/merchant responses are offline test fixtures; no live service success, model accuracy or merchant authorization is inferred from those tests. Coverage and precise run metadata are in `VERIFICATION.md` and the evidence package. PDF child-process lines are not counted as covered by the parent coverage session, although the subprocess is executed.

## Security verification

The original simulator attack is blocked in production before session access. Development callers cannot choose a victim phone number or access production memory. Tokens are not embedded in HTML or launcher output. Requests with missing credentials, foreign origins, remote peers or invalid Hosts are denied. Cookie state is opaque and scoped to local simulation.

No guessed live fallback survives the active reply path. Actual provider errors produce explicit unavailability. Language changes persist, global commands precede onboarding, and changing location clears stale precise coordinates. Optional location context does not replace a real coordinate with a catalog centroid.

The incoming job and lease supply delivery authority; a model or unauthenticated route cannot select another recipient. Jobs outside the original customer-service window do not run external actions; reminders must also fit the remaining window. `stop` records opt-out, cancels booking/reminders and explains how to resume. Delivery/merchant ambiguity cannot be silently labeled success or automatically replayed. Stale-owner checks also guard session operations and browser actions. SDK HTTP/request loggers, including the pinned OpenAI client's HTTPX2 stack, are held at WARNING to avoid debug request-body logging.

Operator recovery exposes metadata by default, creates consistent WAL-aware backups and records review decisions without resending or rerunning tools. Stop the worker that owned an uncertain job before resolving it; local checks cannot make an already in-flight remote effect atomic with SQLite or Astra. Successful raw payloads are cleared after seven days while deduplication tombstones remain. Unresolved effects are retained for review.

A temporary server was run only on loopback and stopped afterward. Health/readiness and private page requests returned 200; unsigned simulation and cross-origin requests returned 403; caller-supplied phone identity returned 400; actual separate local task persistence worked. No secret values were printed and no public service was deployed.

## Preserved global features and boundaries

Adapted code from `thirdhand-global` lives in `services/global_support/` and `services/global_features.py`. The catalog contains 14 cities including the later Trichy/Madurai additions. City confirmation, pending requests, pin suggestions, timezone/currency, local time, tasks/name memory, DST-safe short reminders, regional freshness and honest unavailable/directory results are active. Reminder dispatch now uses the canonical durable queue and outgoing path instead of the old global worker. PDF extraction runs in a killable bounded subprocess.

Existing Indian rail/shopping/flight and modular booking implementations are retained. Unsupported merchants remain disabled; example selector profiles are not activated. Gemini chat is retained, but Whisper transcription explicitly requires an OpenAI transcription credential. Compatibility memory/router/media interfaces remain available; required runtime versions are now explicit.

## Remaining issues and release restrictions

1. This is still a single-business, single-host, single-worker application. It has no customer identity or tenant isolation and must not be marketed/deployed as the requested global SaaS platform. Phase 2 requires separate approval.
2. No live WhatsApp handset, Astra round trip, model inference/language accuracy, authorized merchant flow or external provider entitlement was certified. Current Meta supported-version/app configuration remains a manual verification gate; the old v20.0 default was removed rather than blindly replaced. No Embedded Signup or Coexistence was implemented.
3. Docker is unavailable on the host. Image builds, hosted CI, Linux/macOS execution, load/soak/failover and independent penetration/CVE/container scans were not executed. Pinned versions are not a vulnerability certification or a hash-locked wheel repository.
4. SQLite intent and remote provider/merchant effects cannot be exactly-once. Uncertain work requires review, and a reviewed job blocks later turns for that sender until resolved. Do not add replicas or run mixed old/new workers. A killed worker may leave reviewable uncertainty even if it had not yet sent anything; this is deliberately conservative.
5. No approved-template sender, business-wide human escalation UI, full metrics/alerts, credential vault, multi-region routing, billing, contact-management system or account lifecycle exists. `/ready` checks worker/SQLite health, not every external provider or queue-lag objective.
6. Full physical Astra expiry, account-wide export/erasure, backup retention and encrypted local volumes remain open. Operational records/tombstones and unresolved payloads remain personal data. Do not store live customer data in the cloud-synced development workspace.
7. Browser DNS checks cannot eliminate rebinding races; production merchant execution still needs network egress and OS resource isolation. Windows PDF extraction has parent-enforced byte/page/output/time limits but no claimed Windows OS memory sandbox. Operator-maintained regional adapters and undated legacy tariff/medicine references are not certified live integrations or compliance sources.
8. The fixed city catalog and provider coverage are limited. Provider terms, privacy/regional eligibility, consent/escalation and production operational policies need current verification before commercial use. Existing readonly legacy references do not establish live availability.

## Changed files, recovery and approval boundary

See `PHASE1_CHANGED_FILES.md` for every changed/added file, grouped by purpose. `PHASE1_CHANGELOG.md` records logical changes and relevant test/security checks. `docs/PHASE1_MIGRATIONS.md` contains upgrade, consistent backup, review resolution and rollback procedures.

Rollback must preserve the upgraded queue for reconciliation. Stop workers, back up current SQLite state, then restore the original ZIP/baseline source and pre-upgrade data into a separate private folder. Never run the old worker against version 2 queues, blindly replay uncertain sends, or expose the vulnerable baseline simulator. Any baseline rollback stays offline/loopback; only a repaired verified build may be re-enabled. HMAC key changes must not be incidental because they change Astra document keys. No destructive down-migration is provided.

Phase 1 is ready for owner review. Implementation of Phase 2 remains explicitly unapproved and has not started.
