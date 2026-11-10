import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from dotenv import dotenv_values

APP_ID = "1493313052698471"
ENV_PATH = Path(".env.whatsapp")

def sync_meta_webhook(tunnel_url: str):
    if not ENV_PATH.exists():
        print(f"Error: {ENV_PATH} not found.")
        return False
    env = dotenv_values(ENV_PATH)
    app_secret = env.get("META_APP_SECRET")
    verify_token = env.get("META_VERIFY_TOKEN")
    if not app_secret or not verify_token:
        print("Error: Missing META_APP_SECRET or META_VERIFY_TOKEN in .env.whatsapp")
        return False

    callback_url = f"{tunnel_url}/webhook"
    data = urllib.parse.urlencode({
        "object": "whatsapp_business_account",
        "callback_url": callback_url,
        "verify_token": verify_token,
        "fields": "messages",
        "access_token": f"{APP_ID}|{app_secret}",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://graph.facebook.com/v22.0/{APP_ID}/subscriptions",
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            print(f"\n[AUTO-SYNC SUCCESS] Meta Webhook linked to: {callback_url} -> {body}", flush=True)
            return True
    except Exception as exc:
        print(f"\n[AUTO-SYNC FAILED] {exc}", flush=True)
        return False

current_proc = None
active_tunnel_url = None

def health_checker():
    global current_proc, active_tunnel_url
    fail_count = 0
    while True:
        time.sleep(15)
        if active_tunnel_url and current_proc and current_proc.poll() is None:
            try:
                req = urllib.request.Request(f"{active_tunnel_url}/health", headers={"User-Agent": "HealthChecker/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        fail_count = 0
                    else:
                        fail_count += 1
            except Exception as e:
                fail_count += 1
                print(f"[HEALTH] Tunnel ping failed ({fail_count}/3): {e}", flush=True)

            if fail_count >= 3:
                print("[HEALTH] 3 consecutive tunnel failures. Restarting SSH process...", flush=True)
                try:
                    current_proc.terminate()
                except Exception:
                    pass
                fail_count = 0

def run_tunnel_loop():
    global current_proc, active_tunnel_url
    threading.Thread(target=health_checker, daemon=True).start()

    last_synced_url = None
    while True:
        print("[TUNNEL] Starting SSH tunnel to localhost.run on port 8000...", flush=True)
        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=15",
            "-o", "ServerAliveCountMax=3",
            "-R", "80:127.0.0.1:8000",
            "nokey@localhost.run"
        ]
        try:
            current_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="ignore"
            )
            for line in current_proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                match = re.search(r"https://([a-z0-9]+\.lhr\.life)", line)
                if match:
                    tunnel_url = f"https://{match.group(1)}"
                    if tunnel_url != last_synced_url:
                        print(f"\n[TUNNEL DETECTED] New URL: {tunnel_url}", flush=True)
                        active_tunnel_url = tunnel_url
                        try:
                            Path("data/whatsapp/public_url.txt").write_text(tunnel_url, encoding="utf-8")
                        except Exception:
                            pass
                        if sync_meta_webhook(tunnel_url):
                            last_synced_url = tunnel_url
            current_proc.wait()
            print(f"[TUNNEL] Process exited with code {current_proc.returncode}. Reconnecting in 3s...", flush=True)
        except Exception as e:
            print(f"[TUNNEL ERROR] {e}. Reconnecting in 3s...", flush=True)
        time.sleep(3)

if __name__ == "__main__":
    run_tunnel_loop()
