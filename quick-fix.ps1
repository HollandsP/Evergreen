#!/usr/bin/env pwsh

Write-Host "Quick Fix for Docker Build Issues" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Clean up problematic directories
Write-Host "Cleaning up build context..." -ForegroundColor Yellow

# Remove Python virtual environment from web directory
if (Test-Path "web\web_venv") {
    Write-Host "Removing web_venv directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "web\web_venv" -ErrorAction SilentlyContinue
}

# Clean Docker build cache
Write-Host "Cleaning Docker build cache..." -ForegroundColor Yellow
docker builder prune -f

# Clean up any stopped containers
Write-Host "Cleaning up containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans

Write-Host ""
Write-Host "[SUCCESS] Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Now try the deployment again:" -ForegroundColor Cyan
Write-Host "   ./deploy-windows.ps1" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to continue"