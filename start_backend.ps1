# Start Backend Server for School Network
Write-Host "Starting TE Measurements Backend..." -ForegroundColor Green
Write-Host ""
Write-Host "Using port 8080 (school network friendly)" -ForegroundColor Yellow
Write-Host "Server will be available at: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080

