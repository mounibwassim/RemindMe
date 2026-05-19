# run_flutter.ps1  — Run the Flutter app (Chrome by default)
# Usage: .\run_flutter.ps1
#        .\run_flutter.ps1 -Target windows    (Windows desktop)
#        .\run_flutter.ps1 -Target chrome     (Chrome — default)

param(
    [string]$Target = "chrome"
)

$flutter = "C:\flutter_windows_3.41.9-stable\flutter\bin\flutter.bat"

if (-not (Test-Path $flutter)) {
    # Fallback: try C:\src\flutter
    $flutter = "C:\src\flutter\bin\flutter.bat"
}

if (-not (Test-Path $flutter)) {
    Write-Host "ERROR: Flutter not found. Checked:" -ForegroundColor Red
    Write-Host "  C:\flutter_windows_3.41.9-stable\flutter\bin\flutter.bat" -ForegroundColor Yellow
    Write-Host "  C:\src\flutter\bin\flutter.bat" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== RemindMe Flutter App ===" -ForegroundColor Cyan
Write-Host "Target: $Target" -ForegroundColor Green
Write-Host "Backend API should be running at http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

$flutterDir = Join-Path $PSScriptRoot "mobile_flutter"
Set-Location $flutterDir

& $flutter run -d $Target
