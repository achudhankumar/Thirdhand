"""One-click Python bootstrap launcher for Thirdhand (works on Windows, Mac, and Linux)."""

import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)


def main() -> None:
    print("=" * 74)
    print("  THIRDHAND 🤝 — WhatsApp AI Super-Agent (Python Direct Launcher)")
    print(f"  Folder: {ROOT}")
    print("=" * 74)

    env_file = ROOT / ".env"
    env_example = ROOT / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copyfile(env_example, env_file)
        print("[1/3] Created .env from .env.example")

    print("[2/3] Ensuring core packages are installed...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "fastapi",
            "uvicorn[standard]",
            "httpx",
            "pydantic>=2.7.0",
            "pydantic-settings>=2.2.0",
            "beautifulsoup4",
            "openai",
            "astrapy",
            "tzdata",
        ]
    )

    url = "http://127.0.0.1:8000/simulator"
    print(f"[3/3] Starting server and opening {url} ...")
    webbrowser.open(url)
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--reload",
        ]
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        input("\nPress Enter to exit...")
