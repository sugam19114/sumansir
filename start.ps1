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

# Start app
Write-Host " [2/3] Starting FastAPI app (port 8000)..." -ForegroundColor Yellow
$backendCmd = "& '$PYTHON' -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$scriptDir'; $backendCmd" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host " [3/3] FastAPI is serving the frontend and API together." -ForegroundColor Yellow

# Open browser
Write-Host " Opening application in default browser..." -ForegroundColor Yellow
Start-Process "http://localhost:8000/"

Write-Host ""
Write-Host " ================================================================" -ForegroundColor Green
Write-Host "  APPLICATION IS RUNNING!" -ForegroundColor Green
Write-Host ""
Write-Host "  App:       http://localhost:8000/" -ForegroundColor Cyan
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Sign in with any email to access the platform." -ForegroundColor Gray
Write-Host "  Close the server window to stop." -ForegroundColor Gray
Write-Host " ================================================================" -ForegroundColor Green
Write-Host ""
