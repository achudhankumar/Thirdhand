# Phase 1 changed files

Paths are relative to the canonical `thirdhand-ai-agent` repository. M = modified original; A = added. No original application file was deleted. Formatting corrections are included with the functional changes.

| Status | File | Purpose |
| --- | --- | --- |
| M | `.env.example` | Phase 1 documentation, verification, changed-file or recovery instructions |
| A | `.gitattributes` | Build/runtime/CI/formatting and private-file/line-ending settings |
| M | `.github/workflows/tests.yml` | Build/runtime/CI/formatting and private-file/line-ending settings |
| M | `.gitignore` | Build/runtime/CI/formatting and private-file/line-ending settings |
| M | `Dockerfile` | Build/runtime/CI/formatting and private-file/line-ending settings |
| M | `GUIDE_TAMIL_ENGLISH.md` | Phase 1 documentation, verification, changed-file or recovery instructions |
| A | `PHASE1_CHANGED_FILES.md` | Phase 1 documentation, verification, changed-file or recovery instructions |
| A | `PHASE1_CHANGELOG.md` | Phase 1 documentation, verification, changed-file or recovery instructions |
| A | `PHASE1_IMPLEMENTATION_REPORT.md` | Phase 1 documentation, verification, changed-file or recovery instructions |
| M | `README.md` | Phase 1 documentation, verification, changed-file or recovery instructions |
| M | `START_THIRDHAND_WINDOWS.bat` | Explicit private loopback development setup and Python compatibility |
| M | `VERIFICATION.md` | Phase 1 documentation, verification, changed-file or recovery instructions |
| M | `config/__init__.py` | Required Pydantic 2 exports; no unsupported compatibility stand-ins |
| M | `config/settings.py` | Explicit environment/startup, default-secret rejection, simulator and job settings |
| A | `constraints.txt` | Exact runtime/development/transitive dependency pins |
| M | `database/astra_db.py` | Required SDK, lease checks, atomic development SQLite storage and one-time JSON import |
| M | `database/inbox.py` | Transactional migration, bounded intake, fenced claims, outgoing/status/reminder state and explicit connection close |
| M | `docker-compose.yml` | Build/runtime/CI/formatting and private-file/line-ending settings |
| A | `docs/PHASE1_MIGRATIONS.md` | Phase 1 documentation, verification, changed-file or recovery instructions |
| M | `main.py` | Validated startup, leased worker, window checks, shutdown, SDK log privacy and readiness |
| A | `manage_inbox.py` | Local consistent backup, metadata inspection and audited no-replay review resolution |
| M | `pyproject.toml` | Build/runtime/CI/formatting and private-file/line-ending settings |
| A | `requirements-dev.txt` | Exact runtime/development/transitive dependency pins |
| M | `requirements.txt` | Exact runtime/development/transitive dependency pins |
| A | `routers/simulator.py` | Local-only authenticated simulator with separate storage |
| M | `routers/webhook.py` | Signed bounded message/status validation and atomic acceptance |
| M | `run_thirdhand.py` | Explicit private loopback development setup and Python compatibility |
| M | `services/__init__.py` | Honest postcode/onboarding/fallback behavior, persistent language changes, no fabricated live replies |
| A | `services/global_features.py` | Integrated city/timezone/tasks/name/reminder/regional behavior from global checkout |
| A | `services/global_support/__init__.py` | Preserved global catalog and discovery/ranking/freshness/DST helpers |
| A | `services/global_support/cities.json` | Preserved global catalog and discovery/ranking/freshness/DST helpers |
| A | `services/global_support/providers.py` | Preserved global catalog and discovery/ranking/freshness/DST helpers |
| A | `services/global_support/regional.py` | Preserved global catalog and discovery/ranking/freshness/DST helpers |
| A | `services/global_support/schedule.py` | Preserved global catalog and discovery/ranking/freshness/DST helpers |
| M | `services/http.py` | Safe upstream HTTP status classification without raw error content |
| A | `services/jobs.py` | Trusted worker context and active-lease guard |
| M | `services/llm_orchestrator.py` | Preserved AI/media, global commands, opt-out, guarded checkout ambiguity and truthful error handling |
| M | `services/media_processor.py` | Explicit transcription capability guard |
| A | `services/outbound.py` | Durable outgoing intent, provider ID/status and ambiguous-send handling |
| A | `services/pdf_processor.py` | Real bounded subprocess PDF extraction preserved from global checkout |
| A | `services/pdf_worker.py` | Real bounded subprocess PDF extraction preserved from global checkout |
| A | `services/simulator.html` | Preserved chat UI with private token entry, no supplied phone identity and truthful location prompts |
| M | `services/tools/booking_tool.py` | Simulator action restriction, worker lease checks, timezone validation and uncertain checkout classification |
| M | `services/tools/local_scout_tool.py` | Reject unknown geography instead of defaulting to Trichy |
| M | `services/whatsapp_client.py` | Durable outgoing integration, recipient/media validation and preserved PDF transport |
| M | `start_thirdhand_mac_linux.sh` | Explicit private loopback development setup and Python compatibility |
| M | `tests/conftest.py` | Explicit supported-contract fixture API version |
| A | `tests/test_phase1_features.py` | New audit regression / feature-preservation coverage |
| A | `tests/test_phase1_operations.py` | New audit regression / feature-preservation coverage |
| A | `tests/test_phase1_reliability.py` | New audit regression / feature-preservation coverage |
| A | `tests/test_phase1_security.py` | New audit regression / feature-preservation coverage |
| M | `tests/test_webhook.py` | Valid event fixtures, safe claim-recovery assertion, lifespan/logging checks |

Total: 52 files (28 modified originals, 24 additions).

The original `thirdhand-global` checkout, nested copy, ZIP inputs and audit extraction were not edited. Test outputs, temporary synthetic data, virtual environments and original ZIP backups are outside the canonical source tree.
.env, .env.development and runtime data are excluded from Git; no production secrets were added.
