# 🐳 ThePerfectShop Docker Quick Start

## 📋 Prerequisites

### 1. Install Docker Desktop

**Windows:**
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Run the installer
3. Restart your computer
4. Start Docker Desktop

**Mac:**
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Drag to Applications folder
3. Launch Docker Desktop

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in
```

### 2. Verify Installation
```bash
docker --version
docker-compose --version
```

## 🚀 Quick Deployment (Windows)

### Option A: Automated Setup
```cmd
# 1. Navigate to backend directory
cd backend

# 2. Run setup script
setup-docker.bat
```

### Option B: Manual Setup
```cmd
# 1. Navigate to backend directory
cd backend

# 2. Create environment file
copy .env.example .env

# 3. Start services
deploy.bat start

# 4. Check status
deploy.bat status
```

## 🚀 Quick Deployment (Linux/Mac)

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create environment file
cp .env.example .env

# 3. Start services
./deploy.sh start

# 4. Check status
./deploy.sh status
```

## ✅ Verify Deployment

### 1. Check Services
```bash
# Windows
deploy.bat status

# Linux/Mac
./deploy.sh status
```

Expected output:
```
      Name                     Command               State                    Ports
------------------------------------------------------------------------------------------------
theperfectshop-api      uvicorn app.main:app --ho ...   Up      0.0.0.0:8000->8000/tcp, 9090/tcp
theperfectshop-postgres docker-entrypoint.sh postgres   Up      0.0.0.0:5432->5432/tcp
theperfectshop-redis    docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
```

### 2. Test API Health
```bash
# Windows
curl http://localhost:8000/health

# Or open in browser
start http://localhost:8000/health
```

### 3. Access API Documentation
Open in browser: http://localhost:8000/docs

## 🎯 Access Points

After successful deployment:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | Main API endpoint |
| **Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health** | http://localhost:8000/health | Health check endpoint |
| **Database** | localhost:5432 | PostgreSQL (theperfectshop/theperfectshop123) |
| **Redis** | localhost:6379 | Redis cache |

## 🔧 Common Commands

### Basic Operations
```bash
# Windows
deploy.bat start      # Start all services
deploy.bat stop       # Stop all services
deploy.bat restart    # Restart all services
deploy.bat logs       # View logs
deploy.bat health     # Check health

# Linux/Mac
./deploy.sh start     # Start all services
./deploy.sh stop      # Stop all services
./deploy.sh restart   # Restart all services
./deploy.sh logs      # View logs
./deploy.sh health    # Check health
```

### Advanced Operations
```bash
# Start with monitoring (Grafana + Prometheus)
deploy.bat monitoring

# Run database migrations
deploy.bat migrate

# Create database backup
deploy.bat backup

# Clean up everything
deploy.bat clean
```

## 🔍 Troubleshooting

### Issue: Port Already in Use
```bash
# Windows - Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac - Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Issue: Docker Not Running
```bash
# Windows - Start Docker Desktop
# Check system tray for Docker icon

# Linux - Start Docker service
sudo systemctl start docker
```

### Issue: Services Not Starting
```bash
# Check logs
deploy.bat logs

# Rebuild containers
deploy.bat stop
docker-compose build
deploy.bat start
```

### Issue: Database Connection Failed
```bash
# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

## 📊 Monitoring (Optional)

### Start with Monitoring Stack
```bash
deploy.bat monitoring
```

This adds:
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091

### Available Metrics
- API request/response times
- Database connection status
- System resource usage
- Error rates

## 🔄 Updates

### Update Application
```bash
# Pull latest changes
git pull origin backend-only

# Rebuild and restart
docker-compose build
deploy.bat restart
```

### Update Docker Images
```bash
# Pull latest base images
docker-compose pull

# Rebuild
docker-compose build --no-cache
deploy.bat restart
```

## 🧹 Cleanup

### Stop Services
```bash
deploy.bat stop
```

### Remove Everything (including data)
```bash
deploy.bat clean
```

### Remove Docker Images
```bash
docker system prune -a
```

## 🔐 Production Configuration

### Environment Variables (.env)
```bash
# Change these for production
SECRET_KEY=your-super-secure-32-character-key
POSTGRES_PASSWORD=your-secure-database-password
ENVIRONMENT=production
DEBUG=false

# Add your frontend domain
CORS_ORIGINS=https://your-frontend-domain.com
```

### SSL Configuration
```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem

# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## 📞 Getting Help

### Check Logs
```bash
# All services
deploy.bat logs

# Specific service
docker-compose logs api
docker-compose logs postgres
docker-compose logs redis
```

### Health Checks
```bash
# Overall health
deploy.bat health

# Individual service health
curl http://localhost:8000/health
docker-compose exec postgres pg_isready -U theperfectshop
docker-compose exec redis redis-cli ping
```

### Service Status
```bash
deploy.bat status
```

---

## 🎉 Success!

Your ThePerfectShop backend is now running in Docker!

**Next Steps:**
1. Test the API: http://localhost:8000/docs
2. Integrate with your frontend
3. Configure monitoring (optional)
4. Set up production deployment

**API Base URL for Frontend:** `http://localhost:8000`