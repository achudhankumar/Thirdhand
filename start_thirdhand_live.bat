@echo off
title ThirdHand AI - Live Auto Server & Webhook
cd /d "%~dp0"

echo ======================================================
echo   ThirdHand AI - 24/7 Live Server & Tunnel Launcher
echo ======================================================

:: Kill any old lingering instances on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Start WhatsApp Backend Server
echo [1/2] Starting WhatsApp Server on port 8000...
start /b "" "..\phase1-checkpoint\test-env312\Scripts\python.exe" run_thirdhand.py --whatsapp

:: Give it 3 seconds to boot
timeout /t 3 /nobreak >nul

:: Start Auto-Tunnel & Meta Webhook Auto-Sync Daemon
echo [2/2] Starting Persistent Auto-Tunnel and Meta Webhook Sync...
"..\phase1-checkpoint\test-env312\Scripts\python.exe" auto_tunnel_and_webhook.py
