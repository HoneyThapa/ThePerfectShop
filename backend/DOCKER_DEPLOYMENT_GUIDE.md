# 🐳 ThePerfectShop Docker Deployment Guide

## Prerequisites

### 1. Install Docker Desktop
- **Windows**: Download from https://www.docker.com/products/docker-desktop/
- **Mac**: Download from https://www.docker.com/products/docker-desktop/
- **Linux**: Follow instructions at https://docs.docker.com/engine/install/

### 2. Verify Installation
```bash
docker --version
docker-compose --version
```

## 🚀 Quick Start Deployment

### Step 1: Clone and Setup
```bash
# If not already cloned
git clone https://github.com/HoneyThapa/ThePerfectShop.git
cd ThePerfectShop
git checkout backend-only
cd backend
```

### Step 2: Configure Environment
```bash
# Copy environment file
copy .env.example .env

# Edit .env file if needed (optional for development)
# The default values work for local development
```

### Step 3: Deploy with Docker
```bash
# Windows
deploy.bat start

# Linux/Mac
./deploy.sh start
```

### Step 4: Verify Deployment
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f api

# Test API health
curl http://localhost:8000/health
```

## 📋 What Gets Deployed

### Core Services
1. **PostgreSQL Database** (Port 5432)
   - Database: `theperfectshop`
   - User: `theperfectshop`
   - Password: `theperfectshop123`

2. **Redis Cache** (Port 6379)
   - Used for session storage and job queues

3. **ThePerfectShop API** (Port 8000)
   - Main FastAPI application
   - Health checks enabled
   - Metrics endpoint (Port 9090)

### Optional Monitoring Services
4. **Prometheus** (Port 9091)
   - Metrics collection and monitoring

5. **Grafana** (Port 3000)
   - Dashboards and visualization
   - Default login: admin/admin

## 🔧 Configuration Options

### Environment Variables (.env)
```bash
# Database
POSTGRES_DB=theperfectshop
POSTGRES_USER=theperfectshop
POSTGRES_PASSWORD=theperfectshop123

# API
API_PORT=8000
SECRET_KEY=your-secret-key-32-characters-minimum

# Monitoring
PROMETHEUS_PORT=9091
GRAFANA_PORT=3000
GRAFANA_PASSWORD=admin

# CORS (add your frontend URLs)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 🎯 Deployment Commands

### Basic Operations
```bash
# Start all services
deploy.bat start

# Stop all services
deploy.bat stop

# Restart services
deploy.bat restart

# View logs
deploy.bat logs

# Check service status
deploy.bat status

# Check health
deploy.bat health
```

### Advanced Operations
```bash
# Start with monitoring (Prometheus + Grafana)
deploy.bat monitoring

# Run database migrations
deploy.bat migrate

# Create database backup
deploy.bat backup

# Clean up (removes all containers and volumes)
deploy.bat clean
```

## 🌐 Access Points

After successful deployment:

- **API Base URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091

## 🔍 Monitoring & Debugging

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U theperfectshop -d theperfectshop

# Redis CLI
docker-compose exec redis redis-cli
```

### Container Shell Access
```bash
# API container
docker-compose exec api bash

# Database container
docker-compose exec postgres bash
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -ano | findstr :8000
   
   # Kill the process
   taskkill /PID <PID> /F
   ```

2. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

3. **API Not Starting**
   ```bash
   # Check API logs
   docker-compose logs api
   
   # Rebuild API container
   docker-compose build api
   docker-compose up -d api
   ```

4. **Docker Desktop Issues**
   - Restart Docker Desktop
   - Check Docker Desktop settings
   - Ensure WSL2 is enabled (Windows)

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# Database Health
docker-compose exec postgres pg_isready -U theperfectshop

# Redis Health
docker-compose exec redis redis-cli ping
```

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest changes
git pull origin backend-only

# Rebuild and restart
docker-compose build
docker-compose up -d
```

### Database Maintenance
```bash
# Create backup
deploy.bat backup

# Run migrations
deploy.bat migrate

# Check database size
docker-compose exec postgres psql -U theperfectshop -c "SELECT pg_size_pretty(pg_database_size('theperfectshop'));"
```

### Clean Up
```bash
# Remove unused containers and images
docker system prune -f

# Complete cleanup (WARNING: removes all data)
deploy.bat clean
```

## 🌍 Production Deployment

### Environment Configuration
```bash
# Production .env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-production-key-32-characters-long
POSTGRES_PASSWORD=your-secure-database-password
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

### Backup Strategy
```bash
# Automated daily backups
# Add to crontab:
0 2 * * * cd /path/to/backend && ./deploy.sh backup
```

## 📊 Performance Monitoring

### Metrics Available
- HTTP request metrics
- Database connection metrics
- Job execution metrics
- System resource metrics

### Grafana Dashboards
- API Performance
- Database Health
- System Resources
- Error Rates

### Alerts Configuration
- Service downtime
- High error rates
- Resource exhaustion
- Database issues

## 🔐 Security Considerations

### Production Security
- Change default passwords
- Use environment variables for secrets
- Enable SSL/TLS
- Configure firewall rules
- Regular security updates

### Network Security
- Services communicate via internal Docker network
- Only necessary ports exposed
- SSL termination at load balancer

## 📞 Support

### Getting Help
1. Check logs: `deploy.bat logs`
2. Verify health: `deploy.bat health`
3. Check configuration: Review `.env` file
4. Consult documentation: `/docs` endpoint

### Common Commands Reference
```bash
# Quick health check
curl http://localhost:8000/health

# View API documentation
# Open http://localhost:8000/docs in browser

# Check all services
docker-compose ps

# Follow logs
docker-compose logs -f api
```

---

**🎉 Your ThePerfectShop backend is now running in Docker!**

Access your API at: http://localhost:8000
View documentation at: http://localhost:8000/docs