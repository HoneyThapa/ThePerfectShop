from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.routes_upload import router as upload_router
from app.api.routes_risk import router as risk_router
from app.api.routes_features import router as features_router
from app.api.routes_actions import router as actions_router
from app.api.routes_kpis import router as kpis_router
from app.auth import get_current_user

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
            "name": "features",
            "description": "Feature calculation and velocity analysis. Compute sales velocities and behavioral patterns.",
        },
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)
app.include_router(risk_router)
app.include_router(features_router)
app.include_router(actions_router)
app.include_router(kpis_router)


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
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "upload": "/upload",
            "risk": "/risk",
            "actions": "/actions",
            "kpis": "/kpis",
            "features": "/features"
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
    
    return health_status
