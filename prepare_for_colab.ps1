# Simple PowerShell script to zip necessary files
cd "c:\Users\User\Documents\Projects\RemindMe"

$destination = "RemindMe_Source.zip"

Write-Host "Creating $destination..."

if (Test-Path $destination) { Remove-Item $destination }

# Explicitly list what we want to include
$include = @(
    "main.py",
    "buildozer.spec",
    "assets",
    "libs",
    "screens",
    "widgets",
    "utils",
    "backend",
    "*.json",
    "*.db"
)

Compress-Archive -Path $include -DestinationPath $destination -Force -ErrorAction SilentlyContinue

if (Test-Path $destination) {
    $size = (Get-Item $destination).Length
    if ($size -gt 0) {
        Write-Host "✅ Success! File created: $destination"
        Write-Host "Size: $($size / 1KB) KB"
    } else {
        Write-Host "❌ Failed: Zip file is empty."
    }
} else {
    Write-Host "❌ Failed: Zip file not created."
}
