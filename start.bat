@echo off
title Gantabya Sahayak - Nepal Tourism WebGIS Platform
color 0A

echo.
echo  ================================================================
echo   Gantabya Sahayak ^| गन्तब्य सहायक
echo   Nepal Smart Tourism WebGIS Platform
echo  ================================================================
echo.

:: Try to find Python
set PYTHON=
for %%p in (
    "python"
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
) do (
    if exist %%p (
        set PYTHON=%%p
        goto :found_python
    )
    %%p --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=%%p
        goto :found_python
    )
)

echo  [ERROR] Python not found. Please install Python 3.10+
echo  Download: https://www.python.org/downloads/
pause
exit /b 1

:found_python
echo  [OK] Found Python: %PYTHON%

echo  [1/3] Installing Python dependencies...
cd /d "%~dp0backend"
%PYTHON% -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo  [WARN] Some dependencies may not have installed. Continuing...
)

echo  [2/3] Starting FastAPI app on http://localhost:8000 ...
cd /d "%~dp0"
start "GS App - FastAPI" cmd /k "%PYTHON% -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

:: Wait for backend to initialize
timeout /t 3 /nobreak >nul

echo  [3/3] Waiting for app to accept connections on port 8000...
powershell -NoProfile -Command "while (-not (Test-NetConnection -ComputerName '127.0.0.1' -Port 8000 -WarningAction SilentlyContinue).TcpTestSucceeded) { Start-Sleep -Seconds 1 }"

:: Open the app
start "" "http://localhost:8000/"

echo.
echo  ================================================================
echo   APPLICATION IS RUNNING!
echo.
echo   App:       http://localhost:8000/
echo   API Docs:  http://localhost:8000/docs
echo.
echo   To stop: Close the server terminal window.
echo  ================================================================
echo.
pause
