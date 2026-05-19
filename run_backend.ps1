# run_backend.ps1  — Start the Python FastAPI backend
# Usage: .\run_backend.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "=== RemindMe Python Backend ===" -ForegroundColor Cyan
Write-Host "Starting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API docs available at http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

$backendDir = Join-Path $root "backend_api"
$venv = Join-Path $backendDir ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path $venv)) {
    Write-Host "ERROR: venv not found. Run setup first:" -ForegroundColor Red
    Write-Host "  cd backend_api" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Set-Location $backendDir
$env:PYTHONPATH = $root
& $venv app.main:app --host 0.0.0.0 --port 8000 --reload
