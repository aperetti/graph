# build.ps1 - Top-level build script

Write-Host "Building project..." -ForegroundColor Cyan

# Build Frontend
Write-Host "Building Frontend..." -ForegroundColor Yellow
Set-Location -Path "frontend"
npm install
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed." -ForegroundColor Red
    exit 1
}
Set-Location -Path ".."

Write-Host "`nProject build completed successfully!" -ForegroundColor Green
Write-Host "The UI has been built to frontend/dist."
Write-Host "You can start the backend by navigating to 'backend' and running: python -m uvicorn main:app"
