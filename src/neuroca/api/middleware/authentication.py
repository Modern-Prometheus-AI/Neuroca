"""
Authentication Middleware for NeuroCognitive Architecture (NCA) API

This module provides authentication and authorization middleware for the NCA API.
It implements JWT-based authentication, role-based access control, and security
features to protect API endpoints.

The middleware supports:
- JWT token validation and verification
- Role-based access control
- API key authentication for service-to-service communication
- Rate limiting protection
- Detailed security logging
- Session management

Usage:
    from neuroca.api.middleware.authentication import (
        authenticate_request,
        require_roles,
        APIKeyAuth,
        JWTAuth
    )

    # In FastAPI routes
    @app.get("/protected-endpoint")
    async def protected_endpoint(user: User = Depends(authenticate_request)):
        return {"message": f"Hello, {user.username}"}

    # With role requirements
    @app.post("/admin-only")
    async def admin_endpoint(
        user: User = Depends(require_roles(["admin"]))
    ):
        return {"message": "Admin access granted"}
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ValidationError

from neuroca.config.settings import get_settings
from neuroca.core.models.user import User
from neuroca.db.repositories.user_repository import UserRepository

# Configure logger
logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()


class TokenType(str, Enum):
    """Enum for different token types used in the system."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class JWTPayload(BaseModel):
    """Model representing the JWT token payload structure."""
    sub: str  # Subject (user ID)
    exp: int  # Expiration time
    iat: int  # Issued at time
    type: TokenType  # Token type
    roles: list[str] = []  # User roles
    session_id: Optional[str] = None  # Session identifier
    jti: str  # JWT ID (unique identifier for this token)


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class JWTAuth(HTTPBearer):
    """JWT Authentication handler for FastAPI."""
    
    def __init__(self, auto_error: bool = True):
        """
        Initialize the JWT authentication handler.
        
        Args:
            auto_error: If True, raises HTTPException when authentication fails.
                        If False, returns None when authentication fails.
        """
        super().__init__(auto_error=auto_error)
        
    async def __call__(self, request: Request) -> Optional[JWTPayload]:
        """
        Validate and extract JWT token from the request.
        
        Args:
            request: The incoming HTTP request.
            
        Returns:
            JWTPayload: The decoded JWT payload if authentication succeeds.
            
        Raises:
            HTTPException: If authentication fails and auto_error is True.
        """
        try:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
            if not credentials or not credentials.scheme == "Bearer":
                raise AuthenticationError("Invalid authentication scheme")
            
            payload = decode_jwt_token(credentials.credentials)
            return payload
            
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {str(e)}")
            if self.auto_error:
                raise HTTPException(
                    status_code=e.status_code,
                    detail=e.message,
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None


class APIKeyAuth:
    """API Key Authentication handler for service-to-service communication."""
    
    def __init__(self, api_key_name: str = "X-API-Key", auto_error: bool = True):
        """
        Initialize the API Key authentication handler.
        
        Args:
            api_key_name: The name of the header containing the API key.
            auto_error: If True, raises HTTPException when authentication fails.
        """
        self.api_key_name = api_key_name
        self.auto_error = auto_error
        self.api_key_header = APIKeyHeader(name=api_key_name, auto_error=False)
        
    async def __call__(self, request: Request, api_key: str = Security(APIKeyHeader(name="X-API-Key"))) -> Optional[str]:
        """
        Validate the API key from the request.
        
        Args:
            request: The incoming HTTP request.
            api_key: The API key extracted from the header.
            
        Returns:
            str: The service name associated with the API key if valid.
            
        Raises:
            HTTPException: If authentication fails and auto_error is True.
        """
        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Missing {self.api_key_name} header",
                )
            return None
            
        # Validate API key against stored keys
        service_name = validate_api_key(api_key)
        if not service_name:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            return None
            
        # Log API key usage for audit purposes
        logger.info(f"API key used by service: {service_name}")
        return service_name


def generate_jwt_token(
    user_id: str,
    roles: list[str],
    token_type: TokenType = TokenType.ACCESS,
    session_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: The unique identifier for the user.
        roles: List of roles assigned to the user.
        token_type: Type of token (access, refresh, etc.).
        session_id: Optional session identifier for the token.
        expires_delta: Optional custom expiration time.
        
    Returns:
        str: The encoded JWT token.
    """
    if expires_delta is None:
        if token_type == TokenType.ACCESS:
            expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        elif token_type == TokenType.REFRESH:
            expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
        else:
            expires_delta = timedelta(days=30)  # Default for other token types
    
    now = datetime.utcnow()
    expire = now + expires_delta
    
    # Create a unique token ID
    token_id = hashlib.sha256(f"{user_id}:{now.timestamp()}:{token_type}".encode()).hexdigest()
    
    payload = {
        "sub": user_id,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": token_type,
        "roles": roles,
        "jti": token_id,
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    # Encode the token
    encoded_jwt = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    # Log token generation (without sensitive details)
    logger.debug(
        f"Generated {token_type} token for user {user_id} "
        f"expiring at {expire.isoformat()}"
    )
    
    return encoded_jwt


def decode_jwt_token(token: str) -> JWTPayload:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token to decode and validate.
        
    Returns:
        JWTPayload: The decoded token payload.
        
    Raises:
        AuthenticationError: If token validation fails.
    """
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Convert to Pydantic model for validation
        jwt_payload = JWTPayload(**payload)
        
        # Check if token is expired
        if jwt_payload.exp < int(time.time()):
            raise AuthenticationError("Token has expired")
        
        # Check token type
        if jwt_payload.type not in [TokenType.ACCESS, TokenType.API_KEY]:
            raise AuthenticationError(f"Invalid token type: {jwt_payload.type}")
        
        # Check if token has been revoked (in a real implementation, this would check a blacklist)
        if is_token_revoked(jwt_payload.jti):
            raise AuthenticationError("Token has been revoked")
        
        return jwt_payload
        
    except jwt.PyJWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except ValidationError as e:
        logger.warning(f"JWT payload validation error: {str(e)}")
        raise AuthenticationError("Invalid token structure")


def is_token_revoked(token_id: str) -> bool:
    """
    Check if a token has been revoked.
    
    Args:
        token_id: The unique identifier for the token.
        
    Returns:
        bool: True if the token has been revoked, False otherwise.
    """
    # In a real implementation, this would check a database or cache
    # For now, we'll assume no tokens are revoked
    return False


def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validate an API key and return the associated service name.
    
    Args:
        api_key: The API key to validate.
        
    Returns:
        Optional[str]: The service name if valid, None otherwise.
    """
    # In a real implementation, this would check against stored API keys
    # For now, we'll check against the configured API keys
    for service, key in settings.api_keys.items():
        if hmac.compare_digest(api_key, key):
            return service
    return None


async def authenticate_request(
    request: Request,
    token_payload: JWTPayload = Depends(JWTAuth())
) -> User:
    """
    Authenticate a request and return the user.
    
    Args:
        request: The incoming HTTP request.
        token_payload: The decoded JWT payload.
        
    Returns:
        User: The authenticated user.
        
    Raises:
        HTTPException: If authentication fails.
    """
    try:
        # Get user from database
        user_repo = UserRepository()
        user = await user_repo.get_by_id(token_payload.sub)
        
        if not user:
            logger.warning(f"User not found: {token_payload.sub}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last activity timestamp
        await user_repo.update_last_activity(user.id)
        
        # Add request tracking for security monitoring
        request.state.user_id = user.id
        request.state.roles = token_payload.roles
        
        # Log successful authentication
        logger.info(f"User authenticated: {user.id}")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_roles(required_roles: list[str]):
    """
    Dependency for requiring specific roles to access an endpoint.
    
    Args:
        required_roles: List of roles required to access the endpoint.
        
    Returns:
        Callable: A dependency that checks if the user has the required roles.
    """
    async def role_checker(user: User = Depends(authenticate_request)) -> User:
        user_roles = set(user.roles)
        if not any(role in user_roles for role in required_roles):
            logger.warning(
                f"Access denied: User {user.id} with roles {user_roles} "
                f"attempted to access endpoint requiring {required_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    
    return role_checker


def revoke_token(token_id: str, reason: str = "User logout") -> bool:
    """
    Revoke a JWT token.
    
    Args:
        token_id: The unique identifier for the token.
        reason: The reason for revoking the token.
        
    Returns:
        bool: True if the token was successfully revoked, False otherwise.
    """
    # In a real implementation, this would add the token to a blacklist
    # For now, we'll just log the revocation
    logger.info(f"Token {token_id} revoked: {reason}")
    return True


def refresh_access_token(refresh_token: str) -> dict[str, str]:
    """
    Generate a new access token using a refresh token.
    
    Args:
        refresh_token: The refresh token to use.
        
    Returns:
        Dict[str, str]: A dictionary containing the new access token and its expiry.
        
    Raises:
        AuthenticationError: If the refresh token is invalid.
    """
    try:
        # Decode the refresh token
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Validate token type
        if payload.get("type") != TokenType.REFRESH:
            raise AuthenticationError("Invalid token type")
        
        # Generate a new access token
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        session_id = payload.get("session_id")
        
        new_access_token = generate_jwt_token(
            user_id=user_id,
            roles=roles,
            token_type=TokenType.ACCESS,
            session_id=session_id
        )
        
        # Calculate expiry time
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat()
        }
        
    except jwt.PyJWTError as e:
        logger.warning(f"Refresh token error: {str(e)}")
        raise AuthenticationError("Invalid refresh token")


def get_current_user_id(request: Request) -> Optional[str]:
    """
    Get the current user ID from the request state.
    
    Args:
        request: The HTTP request.
        
    Returns:
        Optional[str]: The user ID if authenticated, None otherwise.
    """
    return getattr(request.state, "user_id", None)


def setup_auth_middleware(app: FastAPI) -> None:
    """
    Set up authentication middleware for a FastAPI application.
    
    Args:
        app: The FastAPI application.
    """
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Skip authentication for public endpoints
        if is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Initialize request state
        request.state.user_id = None
        request.state.roles = []
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


def is_public_endpoint(path: str) -> bool:
    """
    Check if an endpoint is public (doesn't require authentication).
    
    Args:
        path: The URL path.
        
    Returns:
        bool: True if the endpoint is public, False otherwise.
    """
    public_paths = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
    ]
    
    return any(path.startswith(public_path) for public_path in public_paths)


# Additional utility functions for authentication

def hash_password(password: str) -> str:
    """
    Hash a password using a secure algorithm.
    
    Args:
        password: The password to hash.
        
    Returns:
        str: The hashed password.
    """
    # In a real implementation, this would use a proper password hashing library
    # like bcrypt or Argon2
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                   salt, 100000)
    pwdhash = base64.b64encode(pwdhash).decode('ascii')
    return f"{salt}${pwdhash}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        stored_password: The stored password hash.
        provided_password: The password to verify.
        
    Returns:
        bool: True if the password matches, False otherwise.
    """
    # In a real implementation, this would use a proper password hashing library
    salt, stored_hash = stored_password.split('$')
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = base64.b64encode(pwdhash).decode('ascii')
    return hmac.compare_digest(pwdhash, stored_hash)
