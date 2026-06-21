# Gantabya Sahayak — PowerShell Launcher
# Nepal Smart Tourism WebGIS Platform

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host " ================================================================" -ForegroundColor Green
Write-Host "  Gantabya Sahayak | गन्तब्य सहायक" -ForegroundColor Green
Write-Host "  Nepal Smart Tourism WebGIS Platform" -ForegroundColor Green
Write-Host " ================================================================" -ForegroundColor Green
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Auto-detect Python
$pythonCandidates = @(
    "python",
    "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "C:\Python313\python.exe",
    "C:\Python312\python.exe"
)

$PYTHON = $null
foreach ($candidate in $pythonCandidates) {
    if (Test-Path $candidate -ErrorAction SilentlyContinue) {
        $PYTHON = $candidate
        break
    }
    try {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python") { $PYTHON = $candidate; break }
    } catch {}
}

if (-not $PYTHON) {
    Write-Host " [ERROR] Python not found. Install from https://www.python.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host " [OK] Python: $PYTHON" -ForegroundColor Cyan

# Install dependencies
Write-Host " [1/3] Installing dependencies..." -ForegroundColor Yellow
& $PYTHON -m pip install -r "$scriptDir\backend\requirements.txt" -q

# Start backend
Write-Host " [2/3] Starting FastAPI backend (port 8000)..." -ForegroundColor Yellow
$backendCmd = "& '$PYTHON' -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$scriptDir\backend'; $backendCmd" -WindowStyle Normal

Start-Sleep -Seconds 3

# Start frontend
Write-Host " [3/3] Starting frontend server (port 3000)..." -ForegroundColor Yellow
$frontendCmd = "& '$PYTHON' -m http.server 3000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$scriptDir\frontend'; $frontendCmd" -WindowStyle Normal

Start-Sleep -Seconds 2

# Open browser
Write-Host " Opening application in default browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000/index.html"

Write-Host ""
Write-Host " ================================================================" -ForegroundColor Green
Write-Host "  APPLICATION IS RUNNING!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost:3000/index.html" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Sign in with any email to access the platform." -ForegroundColor Gray
Write-Host "  Close server windows to stop." -ForegroundColor Gray
Write-Host " ================================================================" -ForegroundColor Green
Write-Host ""
