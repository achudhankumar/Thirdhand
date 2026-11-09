@echo off
setlocal
cd /d "%~dp0"
py -3.12 -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,15)" >nul 2>&1
if not errorlevel 1 (
  set "THIRDHAND_PY=py -3.12"
) else (
  py -3 -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,15)" >nul 2>&1
  if errorlevel 1 (
    echo Install Python 3.11 through 3.14 from python.org before continuing.
    pause
    exit /b 1
  )
  set "THIRDHAND_PY=py -3"
)
if not exist ".venv\Scripts\python.exe" %THIRDHAND_PY% -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_thirdhand.py --whatsapp
pause
