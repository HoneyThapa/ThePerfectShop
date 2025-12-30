@echo off
REM ThePerfectShop AWS Deployment Script for Windows
REM This script automates the deployment to AWS ECS

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=theperfectshop
set AWS_REGION=us-east-1
set STACK_NAME=%PROJECT_NAME%-infrastructure

REM Check if command is provided
if "%1"=="" (
    set COMMAND=deploy
) else (
    set COMMAND=%1
)

echo [INFO] Starting ThePerfectShop AWS deployment...

REM Check prerequisites
echo [INFO] Checking prerequisites...

REM Check AWS CLI
aws --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS CLI is not installed. Please install AWS CLI first.
    exit /b 1
)

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS credentials not configured. Run 'aws configure' first.
    exit /b 1
)

echo [SUCCESS] Prerequisites check completed

if "%COMMAND%"=="deploy" goto :deploy
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="update" goto :update
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="cleanup" goto :cleanup
if "%COMMAND%"=="help" goto :help

echo [ERROR] Unknown command: %COMMAND%
goto :help

:deploy
echo [INFO] Deploying AWS infrastructure...

aws cloudformation deploy ^
    --template-file aws-infrastructure.yaml ^
    --stack-name %STACK_NAME% ^
    --capabilities CAPABILITY_IAM ^
    --region %AWS_REGION% ^
    --parameter-overrides ProjectName=%PROJECT_NAME%

if errorlevel 1 (
    echo [ERROR] Infrastructure deployment failed
    exit /b 1
)

echo [SUCCESS] Infrastructure deployed successfully

REM Get account ID
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
set ECR_URI=%ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%PROJECT_NAME%-backend

echo [INFO] Building and pushing Docker image...

REM Login to ECR
for /f "tokens=*" %%i in ('aws ecr get-login-password --region %AWS_REGION%') do (
    echo %%i | docker login --username AWS --password-stdin %ECR_URI%
)

REM Build image
docker build -t %PROJECT_NAME%-backend .
if errorlevel 1 (
    echo [ERROR] Docker build failed
    exit /b 1
)

REM Tag image
docker tag %PROJECT_NAME%-backend:latest %ECR_URI%:latest

REM Push image
docker push %ECR_URI%:latest
if errorlevel 1 (
    echo [ERROR] Docker push failed
    exit /b 1
)

echo [SUCCESS] Docker image pushed successfully

echo [INFO] Updating ECS service...

aws ecs update-service ^
    --cluster %PROJECT_NAME%-cluster ^
    --service %PROJECT_NAME%-service ^
    --force-new-deployment ^
    --region %AWS_REGION%

if errorlevel 1 (
    echo [ERROR] ECS service update failed
    exit /b 1
)

echo [SUCCESS] ECS service updated successfully

echo [INFO] Waiting for service to stabilize...
timeout /t 30 /nobreak >nul

goto :get_url

:build
echo [INFO] Building and pushing Docker image...

REM Get account ID
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
set ECR_URI=%ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%PROJECT_NAME%-backend

REM Login to ECR
for /f "tokens=*" %%i in ('aws ecr get-login-password --region %AWS_REGION%') do (
    echo %%i | docker login --username AWS --password-stdin %ECR_URI%
)

REM Build and push
docker build -t %PROJECT_NAME%-backend .
docker tag %PROJECT_NAME%-backend:latest %ECR_URI%:latest
docker push %ECR_URI%:latest

echo [SUCCESS] Docker image built and pushed successfully
goto :end

:update
echo [INFO] Updating ECS service...

aws ecs update-service ^
    --cluster %PROJECT_NAME%-cluster ^
    --service %PROJECT_NAME%-service ^
    --force-new-deployment ^
    --region %AWS_REGION%

echo [SUCCESS] ECS service updated successfully
timeout /t 30 /nobreak >nul
goto :get_url

:status
goto :get_url

:get_url
echo [INFO] Getting service information...

REM Get task ARN
for /f "tokens=*" %%i in ('aws ecs list-tasks --cluster %PROJECT_NAME%-cluster --service-name %PROJECT_NAME%-service --query "taskArns[0]" --output text --region %AWS_REGION%') do set TASK_ARN=%%i

if not "%TASK_ARN%"=="None" if not "%TASK_ARN%"=="" (
    echo [SUCCESS] Service is running!
    echo [INFO] Check AWS Console for the public IP address
    echo [INFO] Or use: aws ecs describe-tasks --cluster %PROJECT_NAME%-cluster --tasks %TASK_ARN%
) else (
    echo [WARNING] Service may still be starting. Check AWS Console.
)

echo [SUCCESS] Deployment completed successfully!
goto :end

:cleanup
echo [WARNING] This will delete all AWS resources. Are you sure? (y/N)
set /p response=
if /i "%response%"=="y" (
    aws cloudformation delete-stack --stack-name %STACK_NAME% --region %AWS_REGION%
    echo [SUCCESS] Cleanup initiated
) else (
    echo [INFO] Cleanup cancelled
)
goto :end

:help
echo ThePerfectShop AWS Deployment Script
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo     deploy          Deploy the complete infrastructure and application
echo     build           Build and push Docker image only
echo     update          Update ECS service only
echo     status          Show deployment status
echo     cleanup         Clean up AWS resources
echo     help            Show this help message
echo.
echo Examples:
echo     %0 deploy       # Full deployment
echo     %0 build        # Build and push image
echo     %0 update       # Update service
goto :end

:end
echo.
echo Deployment script completed.
pause