Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting CampusFix - Campus Maintenance Web App" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    Write-Host "Starting with .venv Python..." -ForegroundColor Green
    & $VenvPython (Join-Path $PSScriptRoot "app.py")
} else {
    Write-Host "Starting with system Python..." -ForegroundColor Green
    python (Join-Path $PSScriptRoot "app.py")
}
