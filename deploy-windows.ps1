#!/usr/bin/env pwsh

Write-Host "Evergreen AI Video Pipeline - Windows PowerShell Deployment" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green
Write-Host ""

# Set environment for better performance
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

# Check if Docker is running
try {
    docker info *>$null
    Write-Host "[SUCCESS] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "$(Get-Date -Format 'HH:mm:ss') Starting pre-deployment checks..." -ForegroundColor Yellow

# Stop any existing containers
docker-compose down --remove-orphans *>$null

Write-Host "$(Get-Date -Format 'HH:mm:ss') Building images with optimizations..." -ForegroundColor Yellow

# Build with parallel processing
$buildResult = docker-compose build --parallel
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed. Check the output above for errors." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "$(Get-Date -Format 'HH:mm:ss') Starting services..." -ForegroundColor Yellow
$deployResult = docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Deployment failed. Check the output above for errors." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] Deployment successful!" -ForegroundColor Green
Write-Host ""
Write-Host "Services available at:" -ForegroundColor Cyan
Write-Host "   Web Interface: http://localhost:3000" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Flower Monitoring: http://localhost:5555" -ForegroundColor White
Write-Host ""

# Wait for services to start
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if web service is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    Write-Host "[SUCCESS] Web interface is responding" -ForegroundColor Green
    Write-Host "Opening Evergreen Studio..." -ForegroundColor Cyan
    Start-Process "http://localhost:3000"
} catch {
    Write-Host "[WARNING] Web interface may still be starting up" -ForegroundColor Yellow
    Write-Host "   Try visiting http://localhost:3000 in a few moments" -ForegroundColor White
}

Write-Host ""
Write-Host "[SUCCESS] Evergreen AI Video Pipeline is ready!" -ForegroundColor Green
Write-Host "   Create your first video by uploading a script" -ForegroundColor White
Write-Host ""
Write-Host "Commands:" -ForegroundColor Gray
Write-Host "   Check status: docker-compose ps" -ForegroundColor Gray
Write-Host "   Stop services: docker-compose down" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to continue"