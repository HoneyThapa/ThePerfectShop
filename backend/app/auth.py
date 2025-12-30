"""
Authentication and authorization utilities for the ExpiryShield backend.

This module provides JWT token validation, user authentication,
and authorization decorators for protecting API endpoints.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
# Password hashing - using a simpler approach for development
import hashlib
from pydantic import BaseModel
from app.logging_config import get_logger, log_security_event, log_authentication_event


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing - using a simpler approach for development
import hashlib

# Security scheme
security = HTTPBearer()

# Logger
logger = get_logger('auth')


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: Optional[list] = None
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model for authentication."""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: list = []
    is_active: bool = True


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    
    def __init__(self, detail: str = "Authentication failed", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": detail,
                "error_code": "AUTHENTICATION_FAILED"
            },
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": detail,
                "error_code": "AUTHORIZATION_FAILED"
            }
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Simple SHA-256 hashing for development (use bcrypt in production)
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Simple SHA-256 hashing for development (use bcrypt in production)
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Log token creation (without sensitive data)
        logger.info(
            "Access token created",
            extra={
                'user_id': data.get('user_id'),
                'username': data.get('username'),
                'expires_at': expire.isoformat(),
                'roles': data.get('roles', [])
            }
        )
        
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise AuthenticationError("Failed to create access token")


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str = payload.get("username")
        user_id: str = payload.get("user_id")
        roles: list = payload.get("roles", [])
        exp_timestamp: int = payload.get("exp")
        
        if username is None or user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        # Check expiration
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            if datetime.utcnow() > exp_datetime:
                raise AuthenticationError("Token has expired")
        
        return TokenData(
            username=username,
            user_id=user_id,
            roles=roles,
            exp=datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
        )
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise AuthenticationError("Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise AuthenticationError("Token verification failed")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get the current authenticated user from JWT token."""
    
    try:
        # Extract token
        token = credentials.credentials
        
        # Verify token
        token_data = verify_token(token)
        
        # In a real application, you would fetch user data from database
        # For now, we'll create a user from token data
        user = User(
            user_id=token_data.user_id,
            username=token_data.username,
            roles=token_data.roles or [],
            is_active=True
        )
        
        # Log successful authentication
        log_authentication_event(
            'user_authenticated',
            user_id=user.user_id,
            username=user.username,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            success=True,
            details={
                'roles': user.roles,
                'path': request.url.path
            }
        )
        
        return user
        
    except AuthenticationError:
        # Log authentication failure
        log_authentication_event(
            'authentication_failed',
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            success=False,
            details={
                'path': request.url.path,
                'reason': 'invalid_token'
            }
        )
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        log_security_event(
            'authentication_error',
            {
                'client_ip': request.client.host if request.client else None,
                'error': str(e),
                'path': request.url.path
            },
            logger
        )
        raise AuthenticationError("Authentication failed")


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None."""
    
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials)
    except AuthenticationError:
        return None


def require_roles(*required_roles: str):
    """Decorator to require specific roles for endpoint access."""
    
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise AuthorizationError("User account is inactive")
        
        if required_roles and not any(role in current_user.roles for role in required_roles):
            log_security_event(
                'authorization_failed',
                {
                    'user_id': current_user.user_id,
                    'username': current_user.username,
                    'user_roles': current_user.roles,
                    'required_roles': list(required_roles),
                    'reason': 'insufficient_roles'
                },
                logger
            )
            raise AuthorizationError(f"Required roles: {', '.join(required_roles)}")
        
        return current_user
    
    return role_checker


def require_permissions(*required_permissions: str):
    """Decorator to require specific permissions for endpoint access."""
    
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise AuthorizationError("User account is inactive")
        
        # In a real application, you would check permissions from database
        # For now, we'll use a simple role-based permission mapping
        role_permissions = {
            'admin': ['read', 'write', 'delete', 'upload', 'approve_actions'],
            'manager': ['read', 'write', 'upload', 'approve_actions'],
            'analyst': ['read', 'write'],
            'viewer': ['read']
        }
        
        user_permissions = set()
        for role in current_user.roles:
            user_permissions.update(role_permissions.get(role, []))
        
        missing_permissions = set(required_permissions) - user_permissions
        if missing_permissions:
            log_security_event(
                'authorization_failed',
                {
                    'user_id': current_user.user_id,
                    'username': current_user.username,
                    'user_roles': current_user.roles,
                    'user_permissions': list(user_permissions),
                    'required_permissions': list(required_permissions),
                    'missing_permissions': list(missing_permissions),
                    'reason': 'insufficient_permissions'
                },
                logger
            )
            raise AuthorizationError(f"Required permissions: {', '.join(missing_permissions)}")
        
        return current_user
    
    return permission_checker


# Convenience functions for common role checks
def require_admin():
    """Require admin role."""
    return require_roles('admin')


def require_manager():
    """Require manager or admin role."""
    return require_roles('manager', 'admin')


def require_analyst():
    """Require analyst, manager, or admin role."""
    return require_roles('analyst', 'manager', 'admin')


# Authentication utilities for testing and development
def create_test_token(user_id: str = "test_user", username: str = "testuser", roles: list = None) -> str:
    """Create a test token for development/testing purposes."""
    if roles is None:
        roles = ['analyst']
    
    token_data = {
        "user_id": user_id,
        "username": username,
        "roles": roles
    }
    
    return create_access_token(token_data)


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password.
    
    In a real application, this would check against a database.
    For now, we'll use hardcoded test users.
    """
    
    # Test users for development
    test_users = {
        "admin": {
            "user_id": "admin_001",
            "username": "admin",
            "password_hash": get_password_hash("admin123"),
            "roles": ["admin"],
            "is_active": True
        },
        "manager": {
            "user_id": "manager_001", 
            "username": "manager",
            "password_hash": get_password_hash("manager123"),
            "roles": ["manager"],
            "is_active": True
        },
        "analyst": {
            "user_id": "analyst_001",
            "username": "analyst", 
            "password_hash": get_password_hash("analyst123"),
            "roles": ["analyst"],
            "is_active": True
        }
    }
    
    user_data = test_users.get(username)
    if not user_data:
        return None
    
    if not verify_password(password, user_data["password_hash"]):
        return None
    
    return User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        roles=user_data["roles"],
        is_active=user_data["is_active"]
    )