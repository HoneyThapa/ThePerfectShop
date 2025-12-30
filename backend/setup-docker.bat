@echo off
echo ========================================
echo   ThePerfectShop Docker Setup Script
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installation:
    echo 1. Restart your computer
    echo 2. Run this script again
    echo.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed!
    echo Please install Docker Desktop which includes Docker Compose.
    pause
    exit /b 1
)

echo [SUCCESS] Docker is installed!
docker --version
docker-compose --version
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [INFO] Creating .env file from template...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [SUCCESS] .env file created successfully!
    ) else (
        echo [ERROR] .env.example file not found!
        exit /b 1
    )
) else (
    echo [INFO] .env file already exists.
)

echo.
echo ========================================
echo   Ready to Deploy!
echo ========================================
echo.
echo Available commands:
echo   deploy.bat start      - Start all services
echo   deploy.bat stop       - Stop all services
echo   deploy.bat logs       - View logs
echo   deploy.bat health     - Check health
echo   deploy.bat monitoring - Start with monitoring
echo.
echo Quick start:
echo   1. Run: deploy.bat start
echo   2. Wait for services to start (30-60 seconds)
echo   3. Open: http://localhost:8000/docs
echo.

set /p choice="Would you like to start the services now? (y/N): "
if /i "%choice%"=="y" (
    echo.
    echo [INFO] Starting ThePerfectShop services...
    call deploy.bat start
    echo.
    echo [SUCCESS] Services are starting up!
    echo.
    echo Access points:
    echo - API: http://localhost:8000
    echo - Docs: http://localhost:8000/docs
    echo - Health: http://localhost:8000/health
    echo.
    echo Wait 30-60 seconds for all services to be ready.
    echo.
    pause
) else (
    echo.
    echo [INFO] Setup complete! Run 'deploy.bat start' when ready.
    echo.
    pause
)