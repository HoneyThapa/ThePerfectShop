# 🐳 Docker Setup for ThePerfectShop Backend

## Quick Docker Installation & Deployment

### Step 1: Install Docker Desktop (Windows)

1. **Download Docker Desktop:**
   - Go to https://www.docker.com/products/docker-desktop
   - Download Docker Desktop for Windows
   - Install and restart your computer

2. **Verify Installation:**
   ```cmd
   docker --version
   docker-compose --version
   ```

### Step 2: Start ThePerfectShop Backend

```bash
# 1. Navigate to backend directory
cd backend

# 2. Copy environment file
copy .env.example .env

# 3. Start all services with Docker
docker-compose up -d

# 4. Check if services are running
docker-compose ps

# 5. Test the API
curl http://localhost:8000/health
```

### Step 3: Access Your API

- **API Base URL:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Docker Commands You'll Need

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Clean up everything
docker-compose down -v
docker system prune -f
```

### What's Running?

- **PostgreSQL Database** (port 5432)
- **Redis Cache** (port 6379)
- **ThePerfectShop API** (port 8000)
- **Prometheus Monitoring** (port 9091) - optional
- **Grafana Dashboard** (port 3000) - optional

### Troubleshooting

**Port already in use:**
```bash
docker ps
docker stop <container_name>
```

**Services not starting:**
```bash
docker-compose logs
```

**Clean restart:**
```bash
docker-compose down -v
docker-compose up -d
```

That's it! Your backend is now running in Docker containers! 🎉