"""
Custom exceptions and error handling for the ExpiryShield backend.

This module defines custom exception classes and provides utilities
for consistent error handling across the application.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ExpiryShieldException(Exception):
    """Base exception class for ExpiryShield-specific errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ExpiryShieldException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field_errors: Dict[str, str] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field_errors = field_errors or {}


class DataProcessingError(ExpiryShieldException):
    """Raised when data processing operations fail."""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, error_code="DATA_PROCESSING_ERROR", **kwargs)
        self.operation = operation


class DatabaseError(ExpiryShieldException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)
        self.operation = operation


class FileProcessingError(ExpiryShieldException):
    """Raised when file processing operations fail."""
    
    def __init__(self, message: str, file_name: str = None, **kwargs):
        super().__init__(message, error_code="FILE_PROCESSING_ERROR", **kwargs)
        self.file_name = file_name


class BusinessLogicError(ExpiryShieldException):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str, rule: str = None, **kwargs):
        super().__init__(message, error_code="BUSINESS_LOGIC_ERROR", **kwargs)
        self.rule = rule


class AuthenticationError(ExpiryShieldException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(ExpiryShieldException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, error_code="AUTHORIZATION_ERROR", **kwargs)


class RateLimitError(ExpiryShieldException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, **kwargs):
        super().__init__(message, error_code="RATE_LIMIT_ERROR", **kwargs)
        self.retry_after = retry_after


class ExternalServiceError(ExpiryShieldException):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service: str = None, **kwargs):
        super().__init__(message, error_code="EXTERNAL_SERVICE_ERROR", **kwargs)
        self.service = service


# HTTP Exception mappings
def to_http_exception(exc: ExpiryShieldException) -> HTTPException:
    """Convert ExpiryShield exceptions to FastAPI HTTPExceptions."""
    
    if isinstance(exc, ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": exc.message,
                "error_code": exc.error_code,
                "field_errors": exc.field_errors,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, AuthenticationError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    elif isinstance(exc, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, RateLimitError):
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            },
            headers=headers
        )
    
    elif isinstance(exc, (FileProcessingError, DataProcessingError, BusinessLogicError)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, DatabaseError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "Database service temporarily unavailable",
                "error_code": exc.error_code,
                "details": {"operation": getattr(exc, 'operation', None)}
            }
        )
    
    elif isinstance(exc, ExternalServiceError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )
    
    else:
        # Generic ExpiryShield exception
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": exc.message,
                "error_code": exc.error_code or "INTERNAL_ERROR",
                "details": exc.details
            }
        )