"""Explicit loopback development launcher; dependencies stay in the chosen venv."""

import argparse
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local",
        action="store_true",
        help="Create/select isolated development settings and simulator",
    )
    args = parser.parse_args(argv)
    if not (3, 11) <= sys.version_info[:2] < (3, 15):
        raise SystemExit("Use Python 3.11 through 3.14; Python 3.10 is not supported.")
    os.chdir(ROOT)
    if args.local:
        config = ROOT / ".env.development"
        if not config.exists():
            descriptor = os.open(config, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                file.write(
                    "ENVIRONMENT=development\nENABLE_SIMULATOR=true\nUSE_LOCAL_MEMORY_FALLBACK=true\n"
                )
                file.write("SESSION_HASH_KEY=" + secrets.token_urlsafe(48) + "\n")
                file.write("SIMULATOR_TOKEN=" + secrets.token_urlsafe(48) + "\n")
                file.write(
                    "SIMULATOR_PATH=data/simulator/sessions.json\nLOCAL_MEMORY_PATH=data/development/sessions.json\nINBOX_PATH=data/development/inbox.sqlite3\n"
                )
        os.environ["THIRDHAND_ENV_FILE"] = str(config)
        print(
            "Using private .env.development. Enter its SIMULATOR_TOKEN in the local page; it is never printed here."
        )
    if shutil.which("ffmpeg") is None:
        print(
            "Voice decoding requires ffmpeg on PATH. Text/image features remain available."
        )
    from config.settings import get_settings

    try:
        settings = get_settings()
        settings.validate_startup()
    except Exception:
        raise SystemExit(
            "Configuration is missing or unsafe. Review the selected private environment file and README; secret values are not printed."
        ) from None
    print("Starting on http://127.0.0.1:8000 (simulator only when explicitly enabled).")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--workers",
            "1",
            "--timeout-graceful-shutdown",
            "260",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
