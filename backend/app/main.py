from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Set up logging first
logger = setup_logging()

app = FastAPI(
    title="ExpiryShield Backend API",
    description="""
    ## ExpiryShield Backend API
    
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
        "name": "ExpiryShield Development Team",
        "email": "dev@expiryshield.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://expiryshield.com/license",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.expiryshield.com",
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


@app.get("/")
async def root():
    """
    Root endpoint for health check and API information.
    
    Provides basic API information, version details, and available endpoints.
    Use this endpoint to discover API capabilities and version options.
    """
    return {
        "message": "ExpiryShield Backend API",
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
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": "2025-12-30T00:00:00Z",
        "version": "1.0.0"
    }


# Log startup
logger.info("ExpiryShield Backend API started successfully")


@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    from app.jobs.scheduler import scheduler
    
    # Initialize job scheduler
    logger.info("Initializing job scheduler...")
    
    # The scheduler is already initialized when imported
    # Job tracking table is created in scheduler.__init__()
    
    logger.info("Job scheduler initialized successfully")
