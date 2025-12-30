# ThePerfectShop Backend Deployment Guide

This guide covers deployment of the ThePerfectShop backend API using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- At least 10GB disk space

## Quick Start

### Development Environment

1. **Clone and setup**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services**:
   ```bash
   # Linux/Mac
   ./deploy.sh start
   
   # Windows
   deploy.bat start
   ```

3. **Run migrations**:
   ```bash
   # Linux/Mac
   ./deploy.sh migrate
   
   # Windows
   deploy.bat migrate
   ```

4. **Check health**:
   ```bash
   # Linux/Mac
   ./deploy.sh health
   
   # Windows
   deploy.bat health
   ```

The API will be available at http://localhost:8000

### Production Environment

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Configure production values in .env
   ```

2. **Generate SSL certificates** (place in `nginx/ssl/`):
   ```bash
   # Self-signed for testing
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem
   ```

3. **Deploy with production configuration**:
   ```bash
   ENVIRONMENT=production ./deploy.sh start
   ```

## Configuration

### Environment Variables

Key environment variables to configure:

#### Database
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `DATABASE_URL`: Full database connection string

#### Security
- `SECRET_KEY`: JWT signing key (32+ characters)
- `CORS_ORIGINS`: Allowed CORS origins
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: API rate limit

#### Application
- `ENVIRONMENT`: development/staging/production
- `DEBUG`: Enable debug mode (false for production)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

#### File Uploads
- `MAX_FILE_SIZE_MB`: Maximum upload file size
- `UPLOAD_DIR`: Directory for uploaded files

#### Monitoring
- `ENABLE_METRICS`: Enable Prometheus metrics
- `GRAFANA_PASSWORD`: Grafana admin password

### Docker Compose Profiles

- **Default**: API, database, Redis
- **monitoring**: Adds Prometheus and Grafana
- **logging**: Adds Fluentd for log aggregation

## Services

### Core Services

1. **PostgreSQL Database** (port 5432)
   - Persistent data storage
   - Automatic health checks
   - Backup volume mounted

2. **Redis Cache** (port 6379)
   - Session storage
   - Job queue backend
   - Caching layer

3. **ThePerfectShop API** (port 8000)
   - Main application server
   - Health check endpoints
   - Metrics endpoint (port 9090)

### Production Services

4. **Nginx Reverse Proxy** (ports 80, 443)
   - SSL termination
   - Rate limiting
   - Static file serving
   - Load balancing

### Monitoring Services

5. **Prometheus** (port 9091)
   - Metrics collection
   - Alerting rules
   - Data retention

6. **Grafana** (port 3000)
   - Dashboards
   - Visualization
   - Alerting

## Health Checks

The application provides multiple health check endpoints:

- `/health` - Comprehensive health check
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe

## Monitoring

### Metrics

Prometheus metrics are available at `/metrics` endpoint:

- HTTP request metrics
- Database connection metrics
- Job execution metrics
- System resource metrics

### Dashboards

Grafana dashboards include:

- API performance metrics
- Database health
- Job execution status
- System resource usage
- Error rates and alerts

### Alerts

Configured alerts for:

- Service downtime
- High error rates
- Resource exhaustion
- Long-running jobs
- Database issues

## Backup and Recovery

### Database Backup

```bash
# Create backup
./deploy.sh backup

# Manual backup
docker-compose exec postgres pg_dump -U theperfectshop theperfectshop > backup.sql
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U theperfectshop theperfectshop < backup.sql
```

### Volume Backup

```bash
# Backup all volumes
docker run --rm -v backend_postgres_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/postgres_backup.tar.gz -C /data .
```

## Scaling

### Horizontal Scaling

To scale the API service:

```bash
docker-compose up --scale api=3
```

### Database Scaling

For production, consider:

- Read replicas for PostgreSQL
- Connection pooling (PgBouncer)
- Database partitioning

### Caching

Redis is configured for:

- Session storage
- Query result caching
- Job queue management

## Security

### Network Security

- Services communicate via internal Docker network
- Only necessary ports exposed
- Nginx handles SSL termination

### Application Security

- JWT token authentication
- Rate limiting
- Input validation
- SQL injection protection
- XSS protection headers

### Data Security

- Sensitive data masked in logs
- Environment variables for secrets
- SSL/TLS encryption
- Database connection encryption

## Troubleshooting

### Common Issues

1. **Database connection failed**:
   ```bash
   # Check database status
   docker-compose ps postgres
   
   # Check logs
   docker-compose logs postgres
   ```

2. **High memory usage**:
   ```bash
   # Check resource usage
   docker stats
   
   # Restart services
   ./deploy.sh restart
   ```

3. **SSL certificate issues**:
   ```bash
   # Verify certificate
   openssl x509 -in nginx/ssl/cert.pem -text -noout
   ```

### Log Analysis

```bash
# View all logs
./deploy.sh logs

# View specific service logs
./deploy.sh logs api

# Follow logs in real-time
docker-compose logs -f api
```

### Performance Tuning

1. **Database optimization**:
   - Adjust `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
   - Monitor slow queries
   - Add appropriate indexes

2. **API optimization**:
   - Adjust worker processes
   - Configure connection pooling
   - Enable response caching

3. **System optimization**:
   - Increase file descriptors
   - Tune kernel parameters
   - Monitor disk I/O

## Maintenance

### Regular Tasks

1. **Update dependencies**:
   ```bash
   # Rebuild with latest base images
   ./deploy.sh build
   ```

2. **Clean up**:
   ```bash
   # Remove unused containers and images
   docker system prune -f
   ```

3. **Monitor logs**:
   ```bash
   # Check for errors
   docker-compose logs | grep ERROR
   ```

### Database Maintenance

1. **Vacuum and analyze**:
   ```bash
   docker-compose exec postgres psql -U theperfectshop -c "VACUUM ANALYZE;"
   ```

2. **Check database size**:
   ```bash
   docker-compose exec postgres psql -U theperfectshop -c "
   SELECT pg_size_pretty(pg_database_size('theperfectshop'));"
   ```

## Support

For deployment issues:

1. Check logs: `./deploy.sh logs`
2. Verify health: `./deploy.sh health`
3. Check configuration: Review `.env` file
4. Consult documentation: `/docs` endpoint
5. Contact development team

## Version Management

The deployment supports multiple API versions:

- v1.0: Initial release
- v1.1: Enhanced features
- Version selection via URL path or headers

Backward compatibility is maintained across versions.