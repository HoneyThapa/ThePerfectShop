from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.routes_upload import router as upload_router
from app.api.routes_risk import router as risk_router
from app.api.routes_actions import router as actions_router
from app.api.routes_kpis import router as kpis_router
from app.api.routes_auth import router as auth_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_bulk import router as bulk_router
from app.api.v1.router import create_v1_router
from app.api.v1_1.router import create_v1_1_router
from app.versioning import create_version_info_router
from app.error_handlers import setup_error_handlers
from app.logging_config import setup_logging
from app.middleware import RequestLoggingMiddleware, SecurityMiddleware, RateLimitMiddleware
from app.monitoring import setup_metrics_endpoint, metrics, cleanup_metrics
from app.api.routes_monitoring import router as monitoring_router

# Set up logging first
logger = setup_logging()

app = FastAPI(
    title="ThePerfectShop Backend API",
    description="""
    ## ThePerfectShop Backend API
    
    A comprehensive REST API for inventory expiry prevention system that helps businesses:
    - Upload and validate sales, inventory, and purchase data
    - Analyze expiry risks using advanced scoring algorithms
    - Generate actionable recommendations (transfers, markdowns, liquidations)
    - Track KPIs and measure financial impact
    
    ### Authentication
    Most endpoints require authentication via JWT tokens. Use the `/auth/login` endpoint to obtain a token.
    
    ### Data Flow
    1. **Upload Data**: Use `/upload` endpoints to submit CSV/Excel files
    2. **Risk Analysis**: System automatically calculates risk scores for inventory batches
    3. **Generate Actions**: Use `/actions/generate` to create recommendations
    4. **Track Performance**: Monitor results via `/kpis` endpoints
    
    ### Rate Limits
    - 100 requests per minute per user
    - 1000 requests per hour per user
    
    ### Support
    For technical support, contact the development team.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "ThePerfectShop Development Team",
        "email": "dev@theperfectshop.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://theperfectshop.com/license",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.theperfectshop.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "upload",
            "description": "File upload and data ingestion operations. Upload CSV/Excel files containing sales, inventory, or purchase data.",
        },
        {
            "name": "risk",
            "description": "Risk analysis and scoring operations. Retrieve risk assessments for inventory batches.",
        },
        {
            "name": "actions",
            "description": "Action recommendation management. Generate, approve, and track inventory optimization actions.",
        },
        {
            "name": "KPIs",
            "description": "Key Performance Indicators and metrics. Track savings, inventory health, and financial impact.",
        },
        {
            "name": "auth",
            "description": "Authentication and authorization operations. Manage user sessions and permissions.",
        },
        {
            "name": "jobs",
            "description": "Scheduled job management. Monitor and control background processing tasks.",
        },
        {
            "name": "bulk-operations",
            "description": "Bulk operations for high-volume data processing. Upload multiple files, batch process actions, and handle large-scale operations efficiently.",
        },
        {
            "name": "version-info",
            "description": "API version information and management. Get version details, compatibility info, and migration guides.",
        },
        {
            "name": "v1.0",
            "description": "API version 1.0 endpoints. Initial release with core functionality.",
        },
        {
            "name": "v1.1",
            "description": "API version 1.1 endpoints. Enhanced features including bulk operations and improved pagination.",
        },
    ]
)

# Set up error handlers
setup_error_handlers(app)

# Set up metrics endpoint
setup_metrics_endpoint(app)

# Add middleware (order matters - last added is executed first)
app.add_middleware(RequestLoggingMiddleware, log_requests=True, log_responses=False)
app.add_middleware(SecurityMiddleware, enable_security_headers=True)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100, requests_per_hour=1000)  # Enhanced rate limiting

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Version-specific routers (recommended)
app.include_router(create_v1_router())
app.include_router(create_v1_1_router())
app.include_router(create_version_info_router())

# Legacy unversioned routers (for backward compatibility)
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(risk_router)
app.include_router(actions_router)
app.include_router(kpis_router)
app.include_router(jobs_router)
app.include_router(bulk_router)
app.include_router(monitoring_router)


@app.get("/")
async def root():
    """
    Root endpoint for health check and API information.
    
    Provides basic API information, version details, and available endpoints.
    Use this endpoint to discover API capabilities and version options.
    """
    return {
        "message": "ThePerfectShop Backend API",
        "version": "1.0.0",
        "status": "healthy",
        "api_versions": {
            "current": "1.1",
            "supported": ["1.0", "1.1"],
            "default": "1.0"
        },
        "version_endpoints": {
            "v1.0": "/v1.0/",
            "v1.1": "/v1.1/",
            "version_info": "/version/"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "usage": {
            "version_selection": [
                "URL path: /v1.0/endpoint or /v1.1/endpoint",
                "Accept-Version header: Accept-Version: 1.1",
                "API-Version header: API-Version: 1.1"
            ],
            "recommended": "Use versioned URLs for new integrations"
        }
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint for monitoring.
    
    Checks the health of the application, database, and external dependencies.
    Used by Docker health checks, load balancers, and monitoring systems.
    """
    from datetime import datetime
    import os
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {}
    }
    
    # Skip database check in test environment or when DB is unavailable
    if os.getenv("SKIP_DB_HEALTH_CHECK", "false").lower() == "true":
        health_status["checks"]["database"] = {
            "status": "skipped",
            "message": "Database health check disabled"
        }
    else:
        # Check database connectivity with fast timeout
        try:
            import time
            from app.db.session import get_db
            
            start_time = time.time()
            db = next(get_db())
            # Simple query to test database
            result = db.execute(text("SELECT 1")).fetchone()
            response_time = (time.time() - start_time) * 1000
            
            health_status["checks"]["database"] = {
                "status": "healthy" if result else "unhealthy",
                "response_time_ms": round(response_time, 2)
            }
            db.close()
        except Exception as e:
            health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis connectivity (if configured)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            health_status["checks"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Check disk space for uploads
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    try:
        import shutil
        if os.path.exists(upload_dir):
            total, used, free = shutil.disk_usage(upload_dir)
            free_percent = (free / total) * 100
            health_status["checks"]["disk_space"] = {
                "status": "healthy" if free_percent > 10 else "warning",
                "free_percent": round(free_percent, 2),
                "free_gb": round(free / (1024**3), 2)
            }
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Check scheduled jobs status (if enabled)
    if os.getenv("ENABLE_SCHEDULED_JOBS", "true").lower() == "true":
        try:
            from app.jobs.scheduler import scheduler
            health_status["checks"]["scheduler"] = {
                "status": "healthy" if scheduler.running else "stopped",
                "job_count": len(scheduler.get_jobs())
            }
        except Exception as e:
            health_status["checks"]["scheduler"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return health_status


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes deployments.
    
    Returns 200 when the application is ready to serve traffic.
    """
    # Check critical dependencies
    from app.db.session import get_db
    
    try:
        db = next(get_db())
        db.execute(text("SELECT 1")).fetchone()
        db.close()
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@app.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes deployments.
    
    Returns 200 when the application is alive (not deadlocked).
    """
    from datetime import datetime
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"}


# Log startup
logger.info("ThePerfectShop Backend API started successfully")


@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    from app.jobs.scheduler import scheduler
    
    # Initialize job scheduler
    logger.info("Initializing job scheduler...")
    
    # The scheduler is already initialized when imported
    # Job tracking table is created in scheduler.__init__()
    
    logger.info("Job scheduler initialized successfully")
    
    # Set initial health status
    metrics.set_health_status('healthy')
    logger.info("Monitoring and metrics initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down application...")
    
    # Cleanup metrics collection
    cleanup_metrics()
    
    logger.info("Application shutdown complete")
