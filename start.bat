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

echo  [2/3] Starting FastAPI backend on http://localhost:8000 ...
start "GS Backend - FastAPI" cmd /k "cd /d "%~dp0backend" && %PYTHON% -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

:: Wait for backend to initialize
timeout /t 3 /nobreak >nul

echo  [3/3] Starting frontend server on http://localhost:3000 ...
cd /d "%~dp0frontend"
start "GS Frontend - HTTP Server" cmd /k "%PYTHON% -m http.server 3000"

:: Wait for frontend server
timeout /t 2 /nobreak >nul

:: Open the app
start "" "http://localhost:3000/index.html"

echo.
echo  ================================================================
echo   APPLICATION IS RUNNING!
echo.
echo   Frontend:  http://localhost:3000/index.html
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   To stop: Close the two server terminal windows.
echo  ================================================================
echo.
pause
