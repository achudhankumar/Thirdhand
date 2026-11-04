# Build verification

Completed on 4 November 2026.

- Full local suite: 51 passed, zero failures, zero skips.
- Runtime used for executed tests: Python 3.14 on Windows.
- Python 3.12 syntax compilation: successful.
- Browser checkout test: actual installed Google Chrome in headless mode,
  using the same Playwright checkout engine with intercepted fixture merchant
  pages. Form filling, selection, navigation and checkout-link validation ran.
- Real ffmpeg voice normalization executed successfully.
- OpenAI Python SDK transcription and function-calling contracts exercised against
  offline HTTP fixture responses; no model inference or paid API call was made.
- Astra atomic document operations exercised with a concurrency-aware test double;
  no live database credentials were supplied.
- Signed ASGI requests, SQLite persistence, deduplication, backpressure, application
  worker processing and graceful shutdown exercised locally.
- Direct dependencies installed and pinned; pip check found no conflicts.
- Docker was not available, so image build and container runtime were not tested.
- CI workflow for Python 3.11/3.12 is included but has not run on GitHub.
- No live railway, Places, shopping, flight, WhatsApp or merchant service was
  verified. No production checkout profile is active. No cloud deployment occurred.

Local test command used BROWSER_CHANNEL=chrome because Chromium CDN downloads
repeatedly failed with TLS transport errors. Default deployment uses Playwright
Chromium; install with `python -m playwright install --no-shell chromium`.

The README records remaining integration and operational requirements, including
merchant authentication/selector validation, portable checkout sessions, persistent
inbox storage, single-replica execution and physical retention cleanup.
