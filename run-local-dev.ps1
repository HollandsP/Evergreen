#!/usr/bin/env pwsh

Write-Host "🚀 Evergreen - Local Development Mode (No Docker)" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "This runs the web interface locally without Docker for faster development!" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "[SUCCESS] Node.js $nodeVersion detected" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found. Please install Node.js 18+ from nodejs.org" -ForegroundColor Red
    Start-Process "https://nodejs.org"
    Read-Host "Press Enter to exit"
    exit 1
}

# Navigate to web directory
Set-Location web

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies (one-time setup)..." -ForegroundColor Yellow
    npm install --legacy-peer-deps
}

# Create .env.local if it doesn't exist
if (-not (Test-Path ".env.local")) {
    Write-Host "Creating environment configuration..." -ForegroundColor Yellow
    @"
# API Keys (already in your main .env)
NEXT_PUBLIC_API_URL=http://localhost:8000
OPENAI_API_KEY=$env:OPENAI_API_KEY
ELEVENLABS_API_KEY=$env:ELEVENLABS_API_KEY
RUNWAY_API_KEY=$env:RUNWAY_API_KEY

# Mock mode for local development
NEXT_PUBLIC_MOCK_MODE=false
"@ | Out-File -FilePath ".env.local" -Encoding UTF8
}

Write-Host ""
Write-Host "Starting Evergreen Web Interface..." -ForegroundColor Green
Write-Host "This will open in your browser at http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: Some features require the backend API (Docker)" -ForegroundColor Yellow
Write-Host "But you can explore the UI and test the interface!" -ForegroundColor Yellow
Write-Host ""

# Start the development server
npm run dev