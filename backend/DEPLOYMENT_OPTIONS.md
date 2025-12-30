# 🚀 ThePerfectShop Deployment Options

## Quick Overview

| Option | Complexity | Cost/Month | Best For |
|--------|------------|------------|----------|
| **Local Docker** | ⭐ Easy | Free | Development & Testing |
| **AWS App Runner** | ⭐⭐ Simple | $25-50 | Quick Production |
| **AWS ECS Fargate** | ⭐⭐⭐ Medium | $15-30 | Scalable Production |
| **AWS Lambda** | ⭐⭐⭐⭐ Advanced | $5-15 | Serverless/Low Traffic |

---

## 🐳 Option 1: Local Docker (Recommended for Development)

### Quick Start:
```bash
cd backend
copy .env.example .env
docker-compose up -d
```

### What You Get:
- ✅ Full backend with database
- ✅ API at http://localhost:8000
- ✅ Interactive docs at /docs
- ✅ Monitoring dashboard
- ✅ Perfect for frontend development

### Files:
- `docker-compose.yml` - Main configuration
- `DOCKER_SETUP.md` - Detailed instructions

---

## ☁️ Option 2: AWS App Runner (Easiest Cloud Deployment)

### Quick Start:
1. **Install AWS CLI and configure:**
   ```bash
   aws configure
   ```

2. **Create apprunner.yaml:**
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
         value: "your-32-character-secret-key"
   ```

3. **Deploy via AWS Console:**
   - Go to AWS App Runner
   - Connect your GitHub repository
   - Select `backend-only` branch
   - Deploy!

### What You Get:
- ✅ Automatic scaling
- ✅ HTTPS included
- ✅ Custom domain support
- ✅ Zero server management
- ✅ Built-in monitoring

### Cost: ~$25-50/month

---

## 🏗️ Option 3: AWS ECS Fargate (Production Ready)

### Automated Deployment:
```bash
# Windows
deploy-aws.bat deploy

# Linux/Mac
./deploy-aws.sh deploy
```

### Manual Steps:
1. **Deploy infrastructure:**
   ```bash
   aws cloudformation deploy \
     --template-file aws-infrastructure.yaml \
     --stack-name theperfectshop-infrastructure \
     --capabilities CAPABILITY_IAM
   ```

2. **Build and push image:**
   ```bash
   # Get account ID
   ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and push
   docker build -t theperfectshop-backend .
   docker tag theperfectshop-backend:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/theperfectshop-backend:latest
   docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/theperfectshop-backend:latest
   ```

3. **Update service:**
   ```bash
   aws ecs update-service --cluster theperfectshop-cluster --service theperfectshop-service --force-new-deployment
   ```

### What You Get:
- ✅ Full container orchestration
- ✅ Auto-scaling
- ✅ Load balancing ready
- ✅ VPC networking
- ✅ CloudWatch monitoring
- ✅ Production-grade security

### Files:
- `aws-infrastructure.yaml` - CloudFormation template
- `deploy-aws.sh` - Linux/Mac deployment script
- `deploy-aws.bat` - Windows deployment script

### Cost: ~$15-30/month

---

## ⚡ Option 4: AWS Lambda (Serverless)

### Setup:
1. **Install Mangum:**
   ```bash
   pip install mangum
   ```

2. **Create lambda_handler.py:**
   ```python
   from mangum import Mangum
   from app.main import app
   import os
   
   os.environ.setdefault("SKIP_DB_HEALTH_CHECK", "true")
   handler = Mangum(app)
   ```

3. **Deploy with SAM:**
   ```bash
   sam build
   sam deploy --guided
   ```

### What You Get:
- ✅ Pay per request
- ✅ Automatic scaling
- ✅ No server management
- ✅ API Gateway included
- ✅ Perfect for low traffic

### Cost: ~$5-15/month (pay per use)

---

## 🎯 Recommendations

### **For Development:**
**Use Local Docker** - Start with `docker-compose up -d`

### **For Quick Production:**
**Use AWS App Runner** - Simplest cloud deployment

### **For Scalable Production:**
**Use AWS ECS Fargate** - Best balance of control and simplicity

### **For Cost-Sensitive/Low Traffic:**
**Use AWS Lambda** - Pay only for what you use

---

## 🔧 Environment Configuration

### Development (.env):
```bash
SKIP_DB_HEALTH_CHECK=true
SECRET_KEY=dev-secret-key-32-characters-long
DEBUG=true
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Production (.env):
```bash
SKIP_DB_HEALTH_CHECK=true
SECRET_KEY=super-secure-production-key-32-chars
DEBUG=false
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com
```

---

## 📋 Quick Commands

### Local Docker:
```bash
cd backend
docker-compose up -d
curl http://localhost:8000/health
```

### AWS App Runner:
- Use AWS Console + GitHub integration

### AWS ECS:
```bash
# Windows
deploy-aws.bat deploy

# Linux/Mac
./deploy-aws.sh deploy
```

### AWS Lambda:
```bash
sam build && sam deploy --guided
```

---

## 🆘 Troubleshooting

### Docker Issues:
```bash
# Restart everything
docker-compose down -v
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### AWS Issues:
```bash
# Check ECS service
aws ecs describe-services --cluster theperfectshop-cluster --services theperfectshop-service

# Check logs
aws logs tail /ecs/theperfectshop --follow
```

---

## 🎉 Next Steps

1. **Choose your deployment option**
2. **Follow the specific guide**
3. **Test your API endpoints**
4. **Update your frontend to use the new API URL**
5. **Set up monitoring and alerts**

Your ThePerfectShop backend will be live and ready for your frontend! 🚀