# ThePerfectShop Backend - Quick Start Guide

## 🚀 For Frontend Integration Testing

### Option 1: Quick Local Development Server (Recommended for Frontend Testing)

```bash
cd backend
python run_local.py
```

This starts the API server at `http://localhost:8000` with:
- ✅ Database features disabled (no setup required)
- ✅ All API endpoints available
- ✅ Interactive documentation at `/docs`
- ✅ Health checks working
- ✅ CORS enabled for frontend development

### Option 2: Full Docker Setup (Production-like)

```bash
cd backend
cp .env.example .env
# Edit .env if needed
./deploy.sh start
```

## 🔗 API Endpoints

- **Base URL**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Health Check**: `http://localhost:8000/health`
- **API Info**: `http://localhost:8000/`

## 📋 Available API Routes

### Core Features
- `POST /upload/sales` - Upload sales data
- `POST /upload/inventory` - Upload inventory data  
- `POST /upload/purchases` - Upload purchase data
- `GET /risk/analysis` - Get risk analysis
- `POST /actions/generate` - Generate recommendations
- `GET /kpis/summary` - Get KPI summary

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user

### Versioned APIs
- `GET /v1.0/*` - Version 1.0 endpoints
- `GET /v1.1/*` - Version 1.1 endpoints (latest)

## 🧪 Test the Setup

Run the deployment test:
```bash
cd backend
python test_deployment.py
```

## 🔧 Configuration

### Environment Variables (Optional)
Create `.env` file for custom configuration:
```bash
# Quick setup - copy example
cp .env.example .env
```

Key variables:
- `SKIP_DB_HEALTH_CHECK=true` - Disable database for testing
- `DEBUG=true` - Enable debug mode
- `CORS_ORIGINS=*` - Allow all origins (development only)

## 📖 Frontend Integration Examples

### JavaScript/Fetch
```javascript
// Health check
const response = await fetch('http://localhost:8000/health');
const health = await response.json();
console.log(health.status); // "healthy"

// Upload sales data
const formData = new FormData();
formData.append('file', salesFile);
const uploadResponse = await fetch('http://localhost:8000/upload/sales', {
    method: 'POST',
    body: formData
});
```

### Python/Requests
```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json()['status'])  # "healthy"

# Get API info
info = requests.get('http://localhost:8000/').json()
print(info['message'])  # "ThePerfectShop Backend API"
```

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Import Errors
```bash
# Install dependencies
pip install -r requirements.txt
```

### CORS Issues
The API is configured with permissive CORS for development. If you encounter CORS issues, check that your frontend is making requests to `http://localhost:8000`.

## 📚 Next Steps

1. **Start the backend**: `python run_local.py`
2. **Open documentation**: Visit `http://localhost:8000/docs`
3. **Test endpoints**: Use the interactive Swagger UI
4. **Integrate with frontend**: Use the API endpoints in your frontend application

## 🔄 Deployment Options

### Development
- Use `python run_local.py` for quick testing
- No database setup required
- All features available except data persistence

### Production
- Use Docker Compose: `./deploy.sh start`
- Full database and Redis setup
- Monitoring and metrics included
- SSL and security features enabled

The backend is now ready for frontend integration! 🎉