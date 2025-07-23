#!/usr/bin/env pwsh

Write-Host "Stopping Docker build..." -ForegroundColor Yellow
docker-compose down
docker stop $(docker ps -q) 2>$null
Write-Host "Docker build stopped." -ForegroundColor Green
Write-Host ""
Write-Host "Try the local development mode instead:" -ForegroundColor Cyan
Write-Host "   ./run-local-dev.ps1" -ForegroundColor White