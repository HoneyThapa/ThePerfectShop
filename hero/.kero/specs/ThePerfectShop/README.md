# ThePerfectShop Backend API

A comprehensive REST API for inventory expiry prevention system that helps businesses minimize losses from expired products.

## Features

- **Data Ingestion**: Upload and validate CSV/Excel files containing sales, inventory, and purchase data
- **Risk Analysis**: Calculate expiry risk scores using advanced algorithms
- **Action Recommendations**: Generate transfer, markdown, and liquidation recommendations
- **KPI Tracking**: Monitor financial impact and system effectiveness
- **RESTful API**: Comprehensive API with authentication and rate limiting

## Quick Start

### Using Docker (Recommended)

1. **Clone and setup**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env file with your configuration
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Database: localhost:5432
   - Redis: localhost:6379

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database**:
   ```bash
   # Start PostgreSQL and Redis locally
   # Update DATABASE_URL and REDIS_URL in .env
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Core Endpoints
- `POST /upload/` - Upload data files
- `GET /risk/` - Get risk analysis
- `POST /actions/generate` - Generate action recommendations
- `GET /kpis/dashboard` - Get dashboard metrics

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /health` - Health check endpoint

## Architecture

The system follows a layered architecture:

- **API Layer**: FastAPI routes with authentication and validation
- **Service Layer**: Business logic for ingestion, risk analysis, actions, and KPIs
- **Data Layer**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for performance optimization

## Database Schema

Key tables:
- `raw_uploads` - File upload tracking
- `sales_daily` - Daily sales data
- `inventory_batches` - Inventory batch information
- `batch_risk` - Risk scores and analysis
- `actions` - Action recommendations
- `action_outcomes` - Action results tracking

## Configuration

Environment variables (see `.env.example`):
- Database connection settings
- Redis configuration
- Authentication settings
- File upload limits
- Rate limiting configuration

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .
```

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Deployment

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
Ensure all production environment variables are set:
- Strong `SECRET_KEY`
- Production database credentials
- Appropriate `CORS_ORIGINS`
- Monitoring configuration

## Monitoring

The API includes:
- Health check endpoints
- Prometheus metrics (optional)
- Structured logging
- Performance monitoring

## Support

For technical support or questions:
- Check the API documentation at `/docs`
- Review the health check at `/health`
- Check application logs