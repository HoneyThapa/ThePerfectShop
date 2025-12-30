"""
Standardized API response models and utilities.

This module provides consistent response formatting across all API endpoints,
ensuring uniform structure, error handling, and HTTP status codes.
"""

from typing import Any, Optional, Dict, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
import json


class APIResponse(BaseModel):
    """
    Standard API response wrapper for all endpoints.
    
    Provides consistent structure across all API responses with:
    - Success/error status indication
    - Human-readable messages
    - Structured data payload
    - Metadata for pagination, timing, etc.
    """
    
    success: bool = Field(..., description="Indicates if the request was successful")
    message: str = Field(..., description="Human-readable status message")
    data: Optional[Any] = Field(None, description="Response payload data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": 123, "name": "Example"},
                "metadata": {"total_count": 1, "page": 1},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = Field(None, description="Field name for validation errors")
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    
    class Config:
        schema_extra = {
            "example": {
                "field": "email",
                "code": "INVALID_FORMAT",
                "message": "Email address format is invalid"
            }
        }


class APIErrorResponse(BaseModel):
    """
    Standard API error response for all error conditions.
    
    Provides consistent error reporting with:
    - Clear error categorization
    - Detailed error information
    - HTTP status code mapping
    - Request correlation for debugging
    """
    
    success: bool = Field(False, description="Always false for error responses")
    message: str = Field(..., description="High-level error message")
    error_code: str = Field(..., description="Machine-readable error code")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "errors": [
                    {
                        "field": "email",
                        "code": "REQUIRED",
                        "message": "Email is required"
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_123456"
            }
        }


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""
    
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=1000, description="Number of items per page")
    total_count: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    
    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 50,
                "total_count": 150,
                "total_pages": 3,
                "has_next": True,
                "has_previous": False
            }
        }


# Response builder utilities
def create_success_response(
    message: str,
    data: Any = None,
    metadata: Optional[Dict[str, Any]] = None
) -> APIResponse:
    """Create a standardized success response."""
    return APIResponse(
        success=True,
        message=message,
        data=data,
        metadata=metadata
    )


def create_error_response(
    message: str,
    error_code: str,
    errors: Optional[List[ErrorDetail]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a standardized error response with appropriate HTTP status."""
    error_response = APIErrorResponse(
        message=message,
        error_code=error_code,
        errors=errors,
        request_id=request_id
    )
    
    # Convert to dict and handle datetime serialization
    response_dict = error_response.model_dump()
    
    # Convert datetime objects to ISO format strings
    if 'timestamp' in response_dict and isinstance(response_dict['timestamp'], datetime):
        response_dict['timestamp'] = response_dict['timestamp'].isoformat()
    
    return JSONResponse(
        status_code=status_code,
        content=response_dict
    )


def create_validation_error_response(
    validation_errors: List[Dict[str, Any]],
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a standardized validation error response."""
    errors = [
        ErrorDetail(
            field=error.get('field'),
            code=error.get('code', 'VALIDATION_ERROR'),
            message=error.get('message', 'Validation failed')
        )
        for error in validation_errors
    ]
    
    return create_error_response(
        message="Request validation failed",
        error_code="VALIDATION_ERROR",
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id
    )


def create_paginated_response(
    message: str,
    data: List[Any],
    page: int,
    page_size: int,
    total_count: int
) -> APIResponse:
    """Create a standardized paginated response."""
    total_pages = (total_count + page_size - 1) // page_size
    
    pagination = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    
    return APIResponse(
        success=True,
        message=message,
        data=data,
        metadata={"pagination": pagination.dict()}
    )


# HTTP Status Code Constants
class HTTPStatus:
    """Standard HTTP status codes for consistent usage."""
    
    # Success codes
    OK = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    ACCEPTED = status.HTTP_202_ACCEPTED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    
    # Client error codes
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    METHOD_NOT_ALLOWED = status.HTTP_405_METHOD_NOT_ALLOWED
    CONFLICT = status.HTTP_409_CONFLICT
    UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
    TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS
    
    # Server error codes
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    BAD_GATEWAY = status.HTTP_502_BAD_GATEWAY
    SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE
    GATEWAY_TIMEOUT = status.HTTP_504_GATEWAY_TIMEOUT


# Common error codes for the application
class ErrorCodes:
    """Standard error codes for consistent error handling."""
    
    # Authentication & Authorization
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALUE_OUT_OF_RANGE = "VALUE_OUT_OF_RANGE"
    
    # Business Logic
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    
    # File Operations
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    
    # System
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"