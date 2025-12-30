"""
API versioning system for the ExpiryShield backend.

This module provides comprehensive API version management including:
- Version detection from headers and URL paths
- Backward compatibility handling
- Version deprecation warnings
- Migration guides and documentation
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum
from fastapi import Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re

from app.response_models import create_success_response, APIResponse, HTTPStatus


class APIVersion(str, Enum):
    """Supported API versions."""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


class VersionStatus(str, Enum):
    """Version lifecycle status."""
    CURRENT = "current"
    SUPPORTED = "supported"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class VersionInfo(BaseModel):
    """Version information model."""
    version: str
    status: VersionStatus
    release_date: date
    sunset_date: Optional[date] = None
    deprecation_date: Optional[date] = None
    changelog_url: Optional[str] = None
    migration_guide_url: Optional[str] = None
    breaking_changes: List[str] = []
    new_features: List[str] = []


class VersionCompatibility(BaseModel):
    """Version compatibility information."""
    requested_version: str
    resolved_version: str
    is_exact_match: bool
    compatibility_warnings: List[str] = []
    migration_required: bool = False
    migration_guide_url: Optional[str] = None


# Version registry with metadata
VERSION_REGISTRY: Dict[str, VersionInfo] = {
    "1.0": VersionInfo(
        version="1.0",
        status=VersionStatus.CURRENT,
        release_date=date(2024, 1, 1),
        new_features=[
            "Initial API release",
            "File upload and data ingestion",
            "Risk analysis and scoring",
            "Action recommendations",
            "KPI tracking and reporting"
        ]
    ),
    "1.1": VersionInfo(
        version="1.1",
        status=VersionStatus.SUPPORTED,
        release_date=date(2024, 2, 1),
        new_features=[
            "Bulk operations support",
            "Enhanced pagination",
            "Improved error handling",
            "API response consistency"
        ]
    ),
    "2.0": VersionInfo(
        version="2.0",
        status=VersionStatus.SUPPORTED,
        release_date=date(2024, 6, 1),
        breaking_changes=[
            "Response format standardization",
            "Authentication token format change",
            "Date format standardization to ISO 8601",
            "Pagination parameter changes"
        ],
        new_features=[
            "GraphQL support",
            "Real-time notifications",
            "Advanced analytics",
            "Multi-tenant support"
        ],
        migration_guide_url="https://docs.expiryshield.com/migration/v1-to-v2"
    )
}

# Default version for new clients
DEFAULT_VERSION = APIVersion.V1_0

# Current latest version
LATEST_VERSION = APIVersion.V1_1


def extract_version_from_header(
    accept_version: Optional[str] = Header(None, alias="Accept-Version"),
    api_version: Optional[str] = Header(None, alias="API-Version")
) -> Optional[str]:
    """Extract API version from request headers."""
    # Try Accept-Version header first (preferred)
    if accept_version and isinstance(accept_version, str):
        return accept_version.strip()
    
    # Fall back to API-Version header
    if api_version and isinstance(api_version, str):
        return api_version.strip()
    
    return None


def extract_version_from_path(request: Request) -> Optional[str]:
    """Extract API version from URL path."""
    path = request.url.path
    
    # Match patterns like /v1.0/endpoint or /api/v1.0/endpoint
    version_pattern = r'/v?(\d+\.\d+)/'
    match = re.search(version_pattern, path)
    
    if match:
        return match.group(1)
    
    return None


def resolve_version_compatibility(requested_version: str) -> VersionCompatibility:
    """
    Resolve version compatibility and determine the actual version to use.
    
    This function handles:
    - Exact version matches
    - Backward compatibility
    - Version deprecation warnings
    - Migration requirements
    """
    
    # Check if exact version exists
    if requested_version in VERSION_REGISTRY:
        version_info = VERSION_REGISTRY[requested_version]
        
        warnings = []
        migration_required = False
        migration_guide_url = None
        
        # Add deprecation warnings
        if version_info.status == VersionStatus.DEPRECATED:
            warnings.append(f"API version {requested_version} is deprecated")
            if version_info.sunset_date:
                warnings.append(f"This version will be sunset on {version_info.sunset_date}")
        
        # Check if migration is recommended
        if version_info.status in [VersionStatus.DEPRECATED, VersionStatus.SUNSET]:
            migration_required = True
            migration_guide_url = version_info.migration_guide_url
        
        return VersionCompatibility(
            requested_version=requested_version,
            resolved_version=requested_version,
            is_exact_match=True,
            compatibility_warnings=warnings,
            migration_required=migration_required,
            migration_guide_url=migration_guide_url
        )
    
    # Handle version compatibility (e.g., 1.x -> 1.0)
    major_version = requested_version.split('.')[0]
    
    # Find the latest compatible version
    compatible_versions = [
        v for v in VERSION_REGISTRY.keys()
        if v.startswith(f"{major_version}.")
    ]
    
    if compatible_versions:
        # Use the latest compatible version
        resolved_version = max(compatible_versions, key=lambda x: tuple(map(int, x.split('.'))))
        
        return VersionCompatibility(
            requested_version=requested_version,
            resolved_version=resolved_version,
            is_exact_match=False,
            compatibility_warnings=[
                f"Requested version {requested_version} not found, using compatible version {resolved_version}"
            ]
        )
    
    # No compatible version found
    raise HTTPException(
        status_code=HTTPStatus.BAD_REQUEST,
        detail=f"Unsupported API version: {requested_version}"
    )


def get_api_version(request: Request) -> VersionCompatibility:
    """
    Determine the API version to use for the request.
    
    Version resolution order:
    1. URL path version (e.g., /v1.0/endpoint)
    2. Accept-Version header
    3. API-Version header
    4. Default version
    """
    
    # Try to extract version from different sources
    path_version = extract_version_from_path(request)
    header_version = extract_version_from_header()
    
    # Determine requested version
    requested_version = path_version or header_version or DEFAULT_VERSION.value
    
    # Resolve compatibility
    return resolve_version_compatibility(requested_version)


def add_version_headers(response: JSONResponse, version_info: VersionCompatibility) -> JSONResponse:
    """Add version-related headers to the response."""
    
    response.headers["API-Version"] = version_info.resolved_version
    response.headers["API-Version-Requested"] = version_info.requested_version
    response.headers["API-Latest-Version"] = LATEST_VERSION.value
    
    if version_info.compatibility_warnings:
        response.headers["API-Compatibility-Warning"] = "; ".join(version_info.compatibility_warnings)
    
    if version_info.migration_required and version_info.migration_guide_url:
        response.headers["API-Migration-Guide"] = version_info.migration_guide_url
    
    return response


class VersionedResponse:
    """Wrapper for versioned API responses."""
    
    def __init__(self, version_info: VersionCompatibility):
        self.version_info = version_info
    
    def create_response(self, data: Any, message: str = "Success") -> JSONResponse:
        """Create a versioned API response."""
        
        # Create base response
        if isinstance(data, APIResponse):
            response_data = data.model_dump()
        else:
            response_data = create_success_response(message, data).model_dump()
        
        # Add version metadata
        if response_data.get("metadata") is None:
            response_data["metadata"] = {}
        response_data["metadata"]["api_version"] = self.version_info.resolved_version
        
        if self.version_info.compatibility_warnings:
            response_data["metadata"]["compatibility_warnings"] = self.version_info.compatibility_warnings
        
        # Handle datetime serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        response_data = serialize_datetime(response_data)
        
        # Create JSON response
        json_response = JSONResponse(content=response_data)
        
        # Add version headers
        return add_version_headers(json_response, self.version_info)


def get_version_dependency():
    """FastAPI dependency for version resolution."""
    def _get_version(request: Request) -> VersionCompatibility:
        return get_api_version(request)
    return Depends(_get_version)


def create_versioned_router(version: str, prefix: str = ""):
    """Create a versioned router with automatic version handling."""
    from fastapi import APIRouter
    
    # Add version to prefix if not already present
    if not prefix.startswith(f"/v{version}"):
        prefix = f"/v{version}{prefix}"
    
    router = APIRouter(prefix=prefix)
    
    # Add version validation middleware
    @router.middleware("http")
    async def version_middleware(request: Request, call_next):
        # Validate version compatibility
        try:
            version_info = get_api_version(request)
            
            # Add version info to request state
            request.state.version_info = version_info
            
            # Process request
            response = await call_next(request)
            
            # Add version headers to response
            if isinstance(response, JSONResponse):
                response = add_version_headers(response, version_info)
            
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )
    
    return router


# Version information endpoints
def create_version_info_router():
    """Create router for version information endpoints."""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/version", tags=["version-info"])
    
    @router.get("/", response_model=APIResponse)
    async def get_version_info():
        """
        Get information about all supported API versions.
        
        Returns comprehensive version information including:
        - Supported versions and their status
        - Release dates and sunset schedules
        - Breaking changes and new features
        - Migration guides and documentation links
        
        **Use this endpoint to:**
        - Discover available API versions
        - Plan version migrations
        - Understand breaking changes
        - Access migration documentation
        """
        
        return create_success_response(
            message="API version information retrieved",
            data={
                "current_version": LATEST_VERSION.value,
                "default_version": DEFAULT_VERSION.value,
                "supported_versions": {
                    version: info.dict() for version, info in VERSION_REGISTRY.items()
                },
                "version_selection": {
                    "methods": [
                        "URL path: /v1.0/endpoint",
                        "Accept-Version header",
                        "API-Version header"
                    ],
                    "precedence": "URL path > Accept-Version > API-Version > default"
                }
            }
        )
    
    @router.get("/{version}", response_model=APIResponse)
    async def get_specific_version_info(version: str):
        """
        Get detailed information about a specific API version.
        
        Returns comprehensive details about the requested version including:
        - Version status and lifecycle information
        - Release and deprecation dates
        - Breaking changes and new features
        - Migration guides and compatibility notes
        """
        
        if version not in VERSION_REGISTRY:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"API version {version} not found"
            )
        
        version_info = VERSION_REGISTRY[version]
        
        return create_success_response(
            message=f"Version {version} information retrieved",
            data=version_info.dict()
        )
    
    return router