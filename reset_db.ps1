# Reset RemindMe Database
Write-Host "Stopping backend if running..." -ForegroundColor Cyan
Stop-Process -Name "python" -ErrorAction SilentlyContinue

$dataPath = "backend_api\data"
if (Test-Path $dataPath) {
    Write-Host "Clearing database and salts..." -ForegroundColor Yellow
    Remove-Item -Path "$dataPath\*" -Include "*.db","*.bin" -Force
    Write-Host "Database reset complete. You can now start fresh." -ForegroundColor Green
} else {
    Write-Host "Data directory not found." -ForegroundColor Red
}
