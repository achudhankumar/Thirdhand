#!/usr/bin/env bash
set -e
echo "============================================================================"
echo "  THIRDHAND 🤝 — All-in-One WhatsApp AI Super-Agent (One-Click Launcher)"
echo "============================================================================"
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi
echo "[2/4] Installing / verifying Python dependencies..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
if [ ! -f ".env" ]; then
    echo "[3/4] Creating .env from .env.example..."
    cp .env.example .env
fi
echo "[4/4] Starting Thirdhand FastAPI Server on http://localhost:8000 ..."
echo "      - Health Check:      http://localhost:8000/health"
echo "      - Local Web Chat:    http://localhost:8000/simulator"
echo "      - WhatsApp Webhook:  http://localhost:8000/webhook"
exec .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
