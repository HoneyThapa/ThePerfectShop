@echo off
REM ExpiryShield Backend Deployment Script for Windows
REM This script handles deployment for different environments

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=expiryshield
set ENVIRONMENT=%ENVIRONMENT%
if "%ENVIRONMENT%"=="" set ENVIRONMENT=development
set COMPOSE_FILE=docker-compose.yml

REM Help function
if "%1"=="help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help

REM Check prerequisites
call :check_prerequisites
if errorlevel 1 exit /b 1

REM Parse command
if "%1"=="start" goto :start_services
if "%1"=="stop" goto :stop_services
if "%1"=="restart" goto :restart_services
if "%1"=="build" goto :build_images
if "%1"=="logs" goto :show_logs
if "%1"=="status" goto :show_status
if "%1"=="clean" goto :clean_up
if "%1"=="migrate" goto :run_migrations
if "%1"=="health" goto :check_health
if "%1"=="monitoring" goto :start_monitoring
if "%1"=="backup" goto :backup_database

echo [ERROR] Unknown command: %1
goto :show_help

:show_help
echo ExpiryShield Backend Deployment Script
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo     start           Start all services
echo     stop            Stop all services
echo     restart         Restart all services
echo     build           Build Docker images
echo     logs            Show service logs
echo     status          Show service status
echo     clean           Clean up containers and volumes
echo     migrate         Run database migrations
echo     health          Check service health
echo     monitoring      Start with monitoring stack
echo     backup          Backup database
echo     help            Show this help message
echo.
echo Examples:
echo     %0 start
echo     %0 logs
echo     %0 migrate
echo     %0 monitoring
goto :eof

:check_prerequisites
echo [INFO] Checking prerequisites...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found. Creating from .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [INFO] Please edit .env file with your configuration before proceeding.
    ) else (
        echo [ERROR] .env.example file not found. Cannot create .env file.
        exit /b 1
    )
)

echo [SUCCESS] Prerequisites check completed
goto :eof

:build_images
echo [INFO] Building Docker images...
docker-compose -f %COMPOSE_FILE% build --no-cache
if errorlevel 1 (
    echo [ERROR] Failed to build Docker images
    exit /b 1
)
echo [SUCCESS] Docker images built successfully
goto :eof

:start_services
echo [INFO] Starting ExpiryShield services...
docker-compose -f %COMPOSE_FILE% up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    exit /b 1
)
echo [SUCCESS] Services started in detached mode
call :show_status
goto :eof

:stop_services
echo [INFO] Stopping ExpiryShield services...
docker-compose -f %COMPOSE_FILE% down
if errorlevel 1 (
    echo [ERROR] Failed to stop services
    exit /b 1
)
echo [SUCCESS] Services stopped
goto :eof

:restart_services
echo [INFO] Restarting ExpiryShield services...
docker-compose -f %COMPOSE_FILE% restart
if errorlevel 1 (
    echo [ERROR] Failed to restart services
    exit /b 1
)
echo [SUCCESS] Services restarted
goto :eof

:show_logs
echo [INFO] Showing service logs...
if "%2"=="" (
    docker-compose -f %COMPOSE_FILE% logs -f
) else (
    docker-compose -f %COMPOSE_FILE% logs -f %2
)
goto :eof

:show_status
echo [INFO] Service status:
docker-compose -f %COMPOSE_FILE% ps
goto :eof

:clean_up
echo [WARNING] This will remove all containers, networks, and volumes. Are you sure? (y/N)
set /p response=
if /i "%response%"=="y" (
    echo [INFO] Cleaning up...
    docker-compose -f %COMPOSE_FILE% down -v --remove-orphans
    docker system prune -f
    echo [SUCCESS] Cleanup completed
) else (
    echo [INFO] Cleanup cancelled
)
goto :eof

:run_migrations
echo [INFO] Running database migrations...
echo [INFO] Waiting for database to be ready...

REM Wait for database
timeout /t 10 /nobreak >nul

REM Run migrations
docker-compose -f %COMPOSE_FILE% exec -T api alembic upgrade head
if errorlevel 1 (
    echo [ERROR] Failed to run migrations
    exit /b 1
)
echo [SUCCESS] Database migrations completed
goto :eof

:check_health
echo [INFO] Checking service health...

REM Check API health
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] API is not responding
) else (
    echo [SUCCESS] API is healthy
)

REM Check database
docker-compose -f %COMPOSE_FILE% exec -T postgres pg_isready -U expiryshield >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Database is not responding
) else (
    echo [SUCCESS] Database is healthy
)

REM Check Redis
docker-compose -f %COMPOSE_FILE% exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis is not responding
) else (
    echo [SUCCESS] Redis is healthy
)
goto :eof

:start_monitoring
echo [INFO] Starting ExpiryShield with monitoring stack...
docker-compose -f %COMPOSE_FILE% --profile monitoring up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services with monitoring
    exit /b 1
)
echo [SUCCESS] Services with monitoring started
echo [INFO] Grafana available at: http://localhost:3000 (admin/admin)
echo [INFO] Prometheus available at: http://localhost:9091
goto :eof

:backup_database
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "backup_file=backup_%YYYY%%MM%%DD%_%HH%%Min%%Sec%.sql"

echo [INFO] Creating database backup: %backup_file%
docker-compose -f %COMPOSE_FILE% exec -T postgres pg_dump -U expiryshield expiryshield > %backup_file%
if errorlevel 1 (
    echo [ERROR] Failed to create database backup
    exit /b 1
)
echo [SUCCESS] Database backup created: %backup_file%
goto :eof