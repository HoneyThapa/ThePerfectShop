"""
API v1.1 router configuration.

This module sets up the v1.1 API routes with enhanced features including:
- Bulk operations support
- Enhanced pagination
- Improved error handling
- API response consistency
"""

from fastapi import APIRouter, Depends, Request
from app.versioning import get_version_dependency, VersionCompatibility, VersionedResponse
from app.api.routes_upload import router as upload_router
from app.api.routes_risk import router as risk_router
from app.api.routes_actions import router as actions_router
from app.api.routes_kpis import router as kpis_router
from app.api.routes_auth import router as auth_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_bulk import router as bulk_router


def create_v1_1_router() -> APIRouter:
    """Create the v1.1 API router with enhanced features."""
    
    router = APIRouter(
        prefix="/v1.1",
        tags=["v1.1"],
        responses={
            400: {"description": "Bad Request"},
            401: {"description": "Unauthorized"},
            403: {"description": "Forbidden"},
            404: {"description": "Not Found"},
            422: {"description": "Validation Error"},
            429: {"description": "Too Many Requests"},
            500: {"description": "Internal Server Error"},
            503: {"description": "Service Unavailable"}
        }
    )
    
    # Include all v1.1 routes (includes all v1.0 + new features)
    router.include_router(auth_router, prefix="")
    router.include_router(upload_router, prefix="")
    router.include_router(risk_router, prefix="")
    router.include_router(actions_router, prefix="")
    router.include_router(kpis_router, prefix="")
    router.include_router(jobs_router, prefix="")
    router.include_router(bulk_router, prefix="")  # New in v1.1
    
    @router.get("/")
    async def v1_1_root(
        request: Request,
        version_info: VersionCompatibility = get_version_dependency()
    ):
        """
        API v1.1 root endpoint.
        
        Provides version information and available endpoints for v1.1.
        Includes all v1.0 functionality plus new features.
        """
        versioned_response = VersionedResponse(version_info)
        
        return versioned_response.create_response(
            data={
                "version": "1.1",
                "message": "ExpiryShield Backend API v1.1",
                "status": "current",
                "new_features": [
                    "Bulk operations support",
                    "Enhanced pagination with metadata",
                    "Improved error handling with correlation IDs",
                    "Standardized API response format"
                ],
                "endpoints": {
                    "authentication": "/v1.1/auth",
                    "file_upload": "/v1.1/upload",
                    "risk_analysis": "/v1.1/risk",
                    "actions": "/v1.1/actions",
                    "kpis": "/v1.1/kpis",
                    "jobs": "/v1.1/jobs",
                    "bulk_operations": "/v1.1/bulk"  # New in v1.1
                },
                "documentation": {
                    "swagger": "/docs",
                    "redoc": "/redoc",
                    "changelog": "https://docs.expiryshield.com/changelog/v1.1"
                },
                "backward_compatibility": {
                    "v1.0": "Full backward compatibility maintained",
                    "migration_required": False
                }
            },
            message="API v1.1 information"
        )
    
    @router.get("/changelog")
    async def v1_1_changelog(
        request: Request,
        version_info: VersionCompatibility = get_version_dependency()
    ):
        """
        Get detailed changelog for v1.1.
        
        Returns comprehensive information about changes, improvements,
        and new features introduced in v1.1.
        """
        versioned_response = VersionedResponse(version_info)
        
        changelog = {
            "version": "1.1",
            "release_date": "2024-02-01",
            "changes": {
                "new_features": [
                    {
                        "feature": "Bulk Operations",
                        "description": "Support for bulk file uploads and batch action processing",
                        "endpoints": ["/bulk/upload", "/bulk/actions", "/bulk/status/{operation_id}"]
                    },
                    {
                        "feature": "Enhanced Pagination",
                        "description": "Improved pagination with metadata including total counts and navigation info",
                        "affected_endpoints": ["/risk", "/actions"]
                    },
                    {
                        "feature": "Standardized Responses",
                        "description": "Consistent API response format across all endpoints",
                        "breaking_changes": False
                    },
                    {
                        "feature": "Improved Error Handling",
                        "description": "Enhanced error responses with correlation IDs and detailed error information",
                        "breaking_changes": False
                    }
                ],
                "improvements": [
                    {
                        "area": "Performance",
                        "description": "Optimized database queries for large datasets"
                    },
                    {
                        "area": "Documentation",
                        "description": "Enhanced OpenAPI documentation with examples and detailed descriptions"
                    },
                    {
                        "area": "Security",
                        "description": "Improved rate limiting and input validation"
                    }
                ],
                "bug_fixes": [
                    "Fixed pagination edge cases in risk analysis endpoints",
                    "Resolved file upload timeout issues for large files",
                    "Corrected KPI calculation precision for financial metrics"
                ]
            },
            "migration": {
                "from_v1_0": {
                    "required": False,
                    "breaking_changes": [],
                    "recommendations": [
                        "Update client code to use new bulk operations for better performance",
                        "Implement pagination metadata handling for improved UX",
                        "Update error handling to use correlation IDs for debugging"
                    ]
                }
            }
        }
        
        return versioned_response.create_response(
            data=changelog,
            message="API v1.1 changelog retrieved"
        )
    
    return router