"""
Authentication API routes for the ExpiryShield backend.

This module provides endpoints for user authentication,
token management, and user profile operations.
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from app.auth import (
    authenticate_user, create_access_token, get_current_user, get_optional_user,
    User, AuthenticationError, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.schemas import StandardResponse, ErrorResponse
from app.logging_config import get_logger, log_security_event, log_authentication_event


router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger('auth_api')


class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserProfileResponse(BaseModel):
    """User profile response model."""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: list
    is_active: bool


class TokenValidationResponse(BaseModel):
    """Token validation response model."""
    valid: bool
    user: Optional[dict] = None
    expires_at: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest
):
    """
    Authenticate user and return JWT access token.
    
    Validates user credentials and returns a JWT token for API access.
    The token must be included in the Authorization header for protected endpoints.
    
    **Request Body:**
    ```json
    {
        "username": "john.doe",
        "password": "secure_password123"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "user_id": "user_123",
            "username": "john.doe",
            "roles": ["analyst", "manager"],
            "is_active": true
        }
    }
    ```
    
    **Usage:**
    Include the token in subsequent requests:
    ```
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
    
    **Security Features:**
    - Passwords are securely hashed and verified
    - Failed attempts are logged for security monitoring
    - Tokens expire after 60 minutes by default
    - All authentication events are audited
    
    **Error Responses:**
    - 401: Invalid username or password
    - 500: Server error during authentication
    """
    
    try:
        # Authenticate user
        user = authenticate_user(login_data.username, login_data.password)
        
        if not user:
            # Log failed login attempt
            log_authentication_event(
                'login_failed',
                username=login_data.username,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
                success=False,
                details={'reason': 'invalid_credentials'}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Invalid username or password",
                    "error_code": "INVALID_CREDENTIALS"
                }
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": user.user_id,
                "username": user.username,
                "roles": user.roles
            },
            expires_delta=access_token_expires
        )
        
        # Log successful login
        log_authentication_event(
            'login_successful',
            user_id=user.user_id,
            username=user.username,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            success=True,
            details={'roles': user.roles}
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user={
                "user_id": user.user_id,
                "username": user.username,
                "roles": user.roles,
                "is_active": user.is_active
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        log_security_event(
            'login_error',
            {
                'username': login_data.username,
                'client_ip': request.client.host if request.client else None,
                'error': str(e)
            },
            logger
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Login failed due to server error",
                "error_code": "LOGIN_ERROR"
            }
        )


@router.post("/login/form", response_model=LoginResponse)
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate user using OAuth2 password flow.
    
    This endpoint is compatible with OAuth2 password flow
    and can be used with FastAPI's OAuth2PasswordBearer.
    """
    
    login_data = LoginRequest(username=form_data.username, password=form_data.password)
    return await login(request, login_data)


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile information.
    
    Returns the profile information for the currently authenticated user.
    Requires valid JWT token in Authorization header.
    """
    
    return UserProfileResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        roles=current_user.roles,
        is_active=current_user.is_active
    )


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(current_user: Optional[User] = Depends(get_optional_user)):
    """
    Validate the provided JWT token.
    
    Returns token validation status and user information if valid.
    This endpoint can be used by other services to validate tokens.
    """
    
    if not current_user:
        return TokenValidationResponse(valid=False)
    
    return TokenValidationResponse(
        valid=True,
        user={
            "user_id": current_user.user_id,
            "username": current_user.username,
            "roles": current_user.roles,
            "is_active": current_user.is_active
        }
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    In a stateless JWT system, logout is handled client-side by discarding the token.
    This endpoint logs the logout event for audit purposes.
    """
    
    # Log logout event
    log_authentication_event(
        'logout',
        user_id=current_user.user_id,
        username=current_user.username,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent'),
        success=True
    )
    
    return StandardResponse(
        status="success",
        message="Logged out successfully"
    )


@router.get("/test-token")
async def create_test_token():
    """
    Create a test token for development purposes.
    
    WARNING: This endpoint should be removed in production!
    It creates tokens without authentication for testing.
    """
    
    from app.auth import create_test_token
    
    # Create tokens for different roles
    tokens = {
        "admin": create_test_token("admin_001", "admin", ["admin"]),
        "manager": create_test_token("manager_001", "manager", ["manager"]),
        "analyst": create_test_token("analyst_001", "analyst", ["analyst"]),
        "viewer": create_test_token("viewer_001", "viewer", ["viewer"])
    }
    
    return {
        "message": "Test tokens created (remove this endpoint in production!)",
        "tokens": tokens,
        "usage": "Add 'Authorization: Bearer <token>' header to requests"
    }