"""
Global error handlers for the ExpiryShield backend.

This module provides centralized error handling for the FastAPI application,
including logging, monitoring, and consistent error responses.
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError as PydanticValidationError

from app.exceptions import ExpiryShieldException, to_http_exception
from app.response_models import (
    APIErrorResponse, ErrorDetail, ErrorCodes, HTTPStatus,
    create_error_response, create_validation_error_response
)


# Configure logging
logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for error tracking."""
    return str(uuid.uuid4())


def log_error(
    correlation_id: str,
    error: Exception,
    request: Request = None,
    additional_context: Dict[str, Any] = None
):
    """Log error with context and correlation ID."""
    context = {
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    
    if request:
        context.update({
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        })
    
    if additional_context:
        context.update(additional_context)
    
    logger.error("Application error occurred", extra=context)


async def expiryshield_exception_handler(request: Request, exc: ExpiryShieldException):
    """Handle custom ExpiryShield exceptions."""
    correlation_id = generate_correlation_id()
    
    # Log the error
    log_error(correlation_id, exc, request)
    
    # Convert to HTTP exception
    http_exc = to_http_exception(exc)
    
    return create_error_response(
        message=str(exc),
        error_code=getattr(exc, 'error_code', ErrorCodes.INTERNAL_ERROR),
        status_code=http_exc.status_code,
        request_id=correlation_id
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions."""
    correlation_id = generate_correlation_id()
    
    # Log non-client errors (5xx and some 4xx)
    if exc.status_code >= 500 or exc.status_code in [401, 403, 429]:
        log_error(correlation_id, exc, request)
    
    # Map status codes to error codes
    error_code_map = {
        HTTPStatus.UNAUTHORIZED: ErrorCodes.INVALID_CREDENTIALS,
        HTTPStatus.FORBIDDEN: ErrorCodes.INSUFFICIENT_PERMISSIONS,
        HTTPStatus.NOT_FOUND: ErrorCodes.RESOURCE_NOT_FOUND,
        HTTPStatus.CONFLICT: ErrorCodes.RESOURCE_ALREADY_EXISTS,
        HTTPStatus.TOO_MANY_REQUESTS: ErrorCodes.RATE_LIMIT_EXCEEDED,
        HTTPStatus.UNPROCESSABLE_ENTITY: ErrorCodes.VALIDATION_ERROR,
        HTTPStatus.INTERNAL_SERVER_ERROR: ErrorCodes.INTERNAL_ERROR,
        HTTPStatus.SERVICE_UNAVAILABLE: ErrorCodes.EXTERNAL_SERVICE_ERROR,
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCodes.INTERNAL_ERROR)
    
    # Extract message from detail
    message = exc.detail
    if isinstance(message, dict):
        message = message.get('message', str(exc.detail))
    
    return create_error_response(
        message=str(message),
        error_code=error_code,
        status_code=exc.status_code,
        request_id=correlation_id
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    correlation_id = generate_correlation_id()
    
    # Extract field errors
    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "code": error["type"].upper(),
            "message": error["msg"]
        })
    
    # Log validation error
    log_error(
        correlation_id, 
        exc, 
        request, 
        {"field_errors": validation_errors}
    )
    
    return create_validation_error_response(
        validation_errors=validation_errors,
        request_id=correlation_id
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    correlation_id = generate_correlation_id()
    
    # Log the database error
    log_error(correlation_id, exc, request, {"database_error": True})
    
    # Determine appropriate response based on error type
    if isinstance(exc, IntegrityError):
        return create_error_response(
            message="Data integrity constraint violation",
            error_code=ErrorCodes.BUSINESS_RULE_VIOLATION,
            status_code=HTTPStatus.CONFLICT,
            request_id=correlation_id
        )
    
    elif isinstance(exc, OperationalError):
        return create_error_response(
            message="Database service temporarily unavailable",
            error_code=ErrorCodes.EXTERNAL_SERVICE_ERROR,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            request_id=correlation_id
        )
    
    else:
        # Generic database error
        return create_error_response(
            message="Database operation failed",
            error_code=ErrorCodes.DATABASE_ERROR,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            request_id=correlation_id
        )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    correlation_id = generate_correlation_id()
    
    # Log the unexpected error
    log_error(correlation_id, exc, request, {"unexpected_error": True})
    
    return create_error_response(
        message="An unexpected error occurred",
        error_code=ErrorCodes.INTERNAL_ERROR,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        request_id=correlation_id
    )


def setup_error_handlers(app):
    """Set up all error handlers for the FastAPI application."""
    
    # Custom exception handlers
    app.add_exception_handler(ExpiryShieldException, expiryshield_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Error handlers configured successfully")