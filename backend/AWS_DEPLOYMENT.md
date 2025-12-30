# ☁️ AWS Deployment Guide for ThePerfectShop

## Option 1: AWS App Runner (Easiest)

### Step 1: Prepare Your Code
```bash
# 1. Make sure your code is pushed to GitHub
git push origin backend-only

# 2. Create apprunner.yaml in backend directory
```

Create `apprunner.yaml`:
```yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  runtime-version: 3.11
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
  env:
    - name: SKIP_DB_HEALTH_CHECK
      value: "true"
    - name: SECRET_KEY
      value: "your-super-secure-secret-key-32-characters"
    - name: ENVIRONMENT
      value: "production"
```

### Step 2: Deploy with AWS Console
1. Go to AWS App Runner in AWS Console
2. Click "Create service"
3. Choose "Source code repository"
4. Connect your GitHub account
5. Select your repository and branch `backend-only`
6. Set build settings to use `apprunner.yaml`
7. Click "Create & deploy"

**Cost:** ~$25/month

---

## Option 2: AWS ECS Fargate (Production-Ready)

### Step 1: Install AWS CLI
```bash
# Windows (using chocolatey)
choco install awscli

# Or download from: https://aws.amazon.com/cli/
```

### Step 2: Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your region (e.g., us-east-1)
# Enter output format: json
```

### Step 3: Create ECR Repository
```bash
aws ecr create-repository --repository-name theperfectshop-backend --region us-east-1
```

### Step 4: Build and Push Docker Image
```bash
# Get your AWS account ID
aws sts get-caller-identity --query Account --output text

# Login to ECR (replace <account-id> with your account ID)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t theperfectshop-backend .

# Tag image
docker tag theperfectshop-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/theperfectshop-backend:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/theperfectshop-backend:latest
```

### Step 5: Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name theperfectshop-cluster
```

### Step 6: Create Task Definition
Create `task-definition.json`:
```json
{
  "family": "theperfectshop-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "theperfectshop-backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/theperfectshop-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SKIP_DB_HEALTH_CHECK",
          "value": "true"
        },
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "SECRET_KEY",
          "value": "your-super-secure-secret-key-32-characters"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/theperfectshop",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Step 7: Register Task Definition and Create Service
```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/theperfectshop

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service (you'll need to get subnet and security group IDs from AWS Console)
aws ecs create-service \
  --cluster theperfectshop-cluster \
  --service-name theperfectshop-service \
  --task-definition theperfectshop-backend:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxx],securityGroups=[sg-xxxxxxxxx],assignPublicIp=ENABLED}"
```

**Cost:** ~$15-30/month

---

## Option 3: AWS Lambda (Serverless)

### Step 1: Install Mangum
```bash
pip install mangum
```

### Step 2: Create Lambda Handler
Create `lambda_handler.py`:
```python
from mangum import Mangum
from app.main import app

# Configure for Lambda
import os
os.environ.setdefault("SKIP_DB_HEALTH_CHECK", "true")
os.environ.setdefault("ENVIRONMENT", "production")

handler = Mangum(app)
```

### Step 3: Deploy with AWS SAM
Install AWS SAM CLI, then create `template.yaml`:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  ThePerfectShopAPI:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.handler
      Runtime: python3.11
      Timeout: 30
      Environment:
        Variables:
          SKIP_DB_HEALTH_CHECK: "true"
          ENVIRONMENT: "production"
          SECRET_KEY: "your-super-secure-secret-key-32-characters"
      Events:
        ApiGateway:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY

Outputs:
  ApiGatewayUrl:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

Deploy:
```bash
sam build
sam deploy --guided
```

**Cost:** ~$5-15/month (pay per request)

---

## Recommended Approach

### For Testing/Development:
**Use Option 1 (App Runner)** - It's the simplest and handles everything for you.

### For Production:
**Use Option 2 (ECS Fargate)** - More control, better for scaling, and cost-effective.

### For Low Traffic:
**Use Option 3 (Lambda)** - Pay only for what you use.

---

## Environment Variables for Production

```bash
# Required
SECRET_KEY=your-super-secure-secret-key-32-characters-long
ENVIRONMENT=production
SKIP_DB_HEALTH_CHECK=true

# Optional
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
```

---

## Next Steps After Deployment

1. **Get your API URL** from AWS Console
2. **Test the API:**
   ```bash
   curl https://your-api-url.amazonaws.com/health
   ```
3. **Update your frontend** to use the new API URL
4. **Set up a custom domain** (optional)
5. **Configure SSL certificate** (optional)

Your ThePerfectShop backend will be live on AWS! 🚀