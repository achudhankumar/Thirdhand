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
    parser.add_argument(
        "--whatsapp",
        action="store_true",
        help="Create/select WhatsApp Business live webhook settings (.env.whatsapp)",
    )
    args = parser.parse_args(argv)
    if not (3, 11) <= sys.version_info[:2] < (3, 15):
        raise SystemExit("Use Python 3.11 through 3.14; Python 3.10 is not supported.")
    os.chdir(ROOT)
    host = "127.0.0.1"
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
    elif args.whatsapp:
        host = os.getenv("HOST", "0.0.0.0")
        config = ROOT / ".env.whatsapp"
        if not config.exists():
            descriptor = os.open(config, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                file.write(
                    "# Thirdhand WhatsApp Business Live Configuration\n"
                    "ENVIRONMENT=development\n"
                    "ENABLE_SIMULATOR=false\n"
                    "DEMO_FALLBACK=false\n"
                    "USE_LOCAL_MEMORY_FALLBACK=true\n"
                    "LOCAL_MEMORY_PATH=data/whatsapp/sessions.json\n"
                    "INBOX_PATH=data/whatsapp/inbox.sqlite3\n"
                    f"SESSION_HASH_KEY={secrets.token_urlsafe(48)}\n"
                    f"META_VERIFY_TOKEN=thirdhand_{secrets.token_hex(16)}\n"
                    "META_API_VERSION=v22.0\n"
                    "META_ACCESS_TOKEN=\n"
                    "META_PHONE_NUMBER_ID=\n"
                    "META_APP_SECRET=\n"
                    "OPENAI_API_KEY=\n"
                    "GEMINI_API_KEY=\n"
                    "RAPIDAPI_KEY=\n"
                    "GOOGLE_PLACES_API_KEY=\n"
                    "GOOGLE_ROUTES_API_KEY=\n"
                    "AMADEUS_CLIENT_ID=\n"
                    "AMADEUS_CLIENT_SECRET=\n"
                )
        os.environ["THIRDHAND_ENV_FILE"] = str(config)
        print(
            "Using private .env.whatsapp for WhatsApp Business webhook mode (/webhook)."
        )
    if shutil.which("ffmpeg") is None:
        print(
            "Voice decoding requires ffmpeg on PATH. Text/image features remain available."
        )
    from config.settings import get_settings

    try:
        settings = get_settings()
        settings.validate_startup()
        if args.whatsapp:
            missing = [
                name
                for name, val in [
                    (
                        "META_ACCESS_TOKEN",
                        settings.meta_access_token.get_secret_value().strip(),
                    ),
                    ("META_PHONE_NUMBER_ID", settings.meta_phone_number_id.strip()),
                    (
                        "META_APP_SECRET",
                        settings.meta_app_secret.get_secret_value().strip(),
                    ),
                    (
                        "META_VERIFY_TOKEN",
                        settings.meta_verify_token.get_secret_value().strip(),
                    ),
                ]
                if not val
            ]
            if not (
                settings.openai_api_key.get_secret_value().strip()
                or settings.gemini_api_key.get_secret_value().strip()
            ):
                missing.append("OPENAI_API_KEY (or GEMINI_API_KEY)")
            if missing:
                raise SystemExit(
                    "WhatsApp mode requires these keys in .env.whatsapp: "
                    + ", ".join(missing)
                )
    except SystemExit:
        raise
    except Exception:
        raise SystemExit(
            "Configuration is missing or unsafe. Review the selected private environment file and README; secret values are not printed."
        ) from None
    port = os.getenv("PORT", "8000")
    print(f"Starting on http://{host}:{port} (simulator only when explicitly enabled).")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            host,
            "--port",
            port,
            "--workers",
            "1",
            "--timeout-graceful-shutdown",
            "260",
            "--no-access-log",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
