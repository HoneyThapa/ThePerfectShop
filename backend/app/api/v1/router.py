"""
API v1.0 router configuration.

This module sets up the v1.0 API routes with proper versioning,
backward compatibility, and deprecation handling.
"""

from fastapi import APIRouter, Depends, Request
from app.versioning import get_version_dependency, VersionCompatibility, VersionedResponse
from app.api.routes_upload import router as upload_router
from app.api.routes_risk import router as risk_router
from app.api.routes_actions import router as actions_router
from app.api.routes_kpis import router as kpis_router
from app.api.routes_auth import router as auth_router
from app.api.routes_jobs import router as jobs_router


def create_v1_router() -> APIRouter:
    """Create the v1.0 API router with version handling."""
    
    router = APIRouter(
        prefix="/v1.0",
        tags=["v1.0"],
        responses={
            400: {"description": "Bad Request"},
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden"},
            404: {"description": "Not Found"},
            422: {"description": "Validation Error"},
            500: {"description": "Internal Server Error"}
        }
    )
    
    # Include all v1.0 routes
    router.include_router(auth_router, prefix="")
    router.include_router(upload_router, prefix="")
    router.include_router(risk_router, prefix="")
    router.include_router(actions_router, prefix="")
    router.include_router(kpis_router, prefix="")
    router.include_router(jobs_router, prefix="")
    
    @router.get("/")
    async def v1_root(
        request: Request,
        version_info: VersionCompatibility = get_version_dependency()
    ):
        """
        API v1.0 root endpoint.
        
        Provides version information and available endpoints for v1.0.
        """
        versioned_response = VersionedResponse(version_info)
        
        return versioned_response.create_response(
            data={
                "version": "1.0",
                "message": "ExpiryShield Backend API v1.0",
                "status": "active",
                "endpoints": {
                    "authentication": "/v1.0/auth",
                    "file_upload": "/v1.0/upload",
                    "risk_analysis": "/v1.0/risk",
                    "actions": "/v1.0/actions",
                    "kpis": "/v1.0/kpis",
                    "jobs": "/v1.0/jobs"
                },
                "documentation": {
                    "swagger": "/docs",
                    "redoc": "/redoc"
                }
            },
            message="API v1.0 information"
        )
    
    return router