@echo off
title Evergreen AI Video Pipeline - Windows Deployment
echo.
echo 🚀 Evergreen AI Video Pipeline - Windows Deployment
echo ======================================================
echo.

:: Set environment for better performance
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [%time%] Starting pre-deployment checks...
:: Stop any existing containers
docker-compose down --remove-orphans >nul 2>&1

echo [%time%] Building images with optimizations...
:: Build with better Windows performance
docker-compose build --parallel --progress=plain

if %errorlevel% neq 0 (
    echo ❌ Build failed. Check the output above for errors.
    pause
    exit /b 1
)

echo [%time%] Starting services...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ❌ Deployment failed. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ✅ Deployment successful!
echo.
echo 🌐 Services available at:
echo    Web Interface: http://localhost:3000
echo    API Documentation: http://localhost:8000/docs
echo    Flower Monitoring: http://localhost:5555
echo.
echo 📊 Check status with: docker-compose ps
echo 🛑 Stop services with: docker-compose down
echo.

:: Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 10 >nul

:: Check if web service is responding
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Web interface is responding
    echo 🎬 Opening Evergreen Studio...
    start http://localhost:3000
) else (
    echo ⚠️  Web interface may still be starting up
    echo    Try visiting http://localhost:3000 in a few moments
)

echo.
echo 🎉 Evergreen AI Video Pipeline is ready!
echo    Create your first video by uploading a script
echo.
pause