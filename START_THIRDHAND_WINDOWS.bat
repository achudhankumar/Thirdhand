@echo off
cd /d "%~dp0"
title Thirdhand WhatsApp AI Agent - Windows Launcher
color 0A
echo ======================================================================
echo   THIRDHAND - WhatsApp AI Super-Agent (Windows Launcher)
echo   Folder: %CD%
echo ======================================================================
echo.
if exist "%~dp0run_thirdhand.py" goto :CHECK_PY
color 0C
echo [ERROR] Please Extract (Unzip) thirdhand-ai-agent-complete.zip first!
echo Right-click the ZIP file and click Extract All.
pause
exit /b 1

:CHECK_PY
py -3 -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if not errorlevel 1 goto :RUN_WITH_PY
python -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if not errorlevel 1 goto :RUN_WITH_PYTHON
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" goto :RUN_LOCAL_312
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" goto :RUN_LOCAL_311

color 0E
echo [INFO] Installing Python 3.12 via Windows Winget (please wait 1-2 mins)...
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" goto :RUN_LOCAL_312
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto :RUN_WITH_PY
color 0C
echo [ACTION REQUIRED] Please install Python 3.12 from python.org
echo Tick the box Add python.exe to PATH during installation!
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:RUN_WITH_PY
py -3 run_thirdhand.py
pause
exit /b 0

:RUN_WITH_PYTHON
python run_thirdhand.py
pause
exit /b 0

:RUN_LOCAL_312
"%LocalAppData%\Programs\Python\Python312\python.exe" run_thirdhand.py
pause
exit /b 0

:RUN_LOCAL_311
"%LocalAppData%\Programs\Python\Python311\python.exe" run_thirdhand.py
pause
exit /b 0
