# Phase 1 verification — 4 November 2026

Canonical source: original modular ZIP, baseline commit `d347177`, branch `phase1/stabilize`.

| Check | Before | Final |
| --- | --- | --- |
| Modular suite, Python 3.14 | 51 passed | 113 passed (17.789 seconds) |
| Modular suite, Python 3.12 | Not rerun as an untouched baseline | 113 passed (20.684 seconds) |
| Preserved global reference | 21 passed | 21 passed |
| Ruff lint | 10 audit findings | Pass |
| Ruff formatting | 6 files fail | Pass |
| Dependency consistency | Audit environment passed | Both pinned test environments pass |

Original 51 test cases are retained; 62 regression cases added. Static comparison confirms no original test function was deleted. Existing fixtures now include valid Meta event fields/timestamps and an explicit fixture API version. Recovery assertions now require non-stealing claim behavior.

Final runtime coverage: 1739/2200 statements (79.05%), 497/760 branches (65.39%). Combined statement/branch coverage: 75.54%. Scope includes the existing and added runtime modules plus operator CLI; this is broader than the original audit scope. The PDF subprocess really ran, but its child-process lines are not traced by the parent coverage session. Coverage is not a security certification.

Real local prerequisites exercised: installed Playwright Chromium checkout fixture, ffmpeg normalization and bounded PDF parsing. External APIs/models/database/merchants were offline fixtures. No paid model inference or credentialed provider action was run.

A temporary loopback Uvicorn server was started and stopped: health/readiness/page 200, missing token 403, supplied phone identity 400, foreign origin 403, token absent from HTML, real isolated local tasks/memory verified. Production simulator denial and remote/Host rejection are automated ASGI regressions.

Python 3.11 syntax was parsed; its runtime suite and Linux/macOS CI have not run locally. The installed Python 3.12.0–3.12.11 patch level produces Astra's SSL-reuse warning. Use a maintained newer patch before eventual deployment. Docker is unavailable, so no image build or runtime certification is claimed.

Evidence outside the source tree: `../phase1-checkpoint/frozen312.xml`, `frozen314.xml`, `global-acceptance.xml`, `frozen-coverage.json`, `phase1-verification.json`, `phase1-integrity.json`, `loopback-smoke.json`, and the original baseline XML/ZIP/manifest. A source archive and recovery Git bundle accompany the report after the final local checkpoint.

The original global checkout and audit extraction hashes remain unchanged. No secrets/environment files or runtime databases are tracked. No production deployment, multi-tenancy, Embedded Signup, Coexistence or Phase 2 work occurred.
