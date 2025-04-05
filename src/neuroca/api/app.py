"""
NeuroCognitive Architecture (NCA) API Application

This module defines the main FastAPI application for the NeuroCognitive Architecture system.
It sets up the API routes, middleware, exception handlers, and integrates with the core NCA
components. The API provides endpoints for interacting with the NCA system, managing memory
tiers, health dynamics, and LLM integration.

Usage:
    To run the API server:
    ```
    uvicorn neuroca.api.app:app --host 0.0.0.0 --port 8000
    ```

Security:
    - API authentication via JWT tokens
    - Rate limiting to prevent abuse
    - Input validation on all endpoints
    - Secure error handling to prevent information leakage
    - CORS configuration for controlled access

Dependencies:
    - FastAPI for API framework
    - Pydantic for data validation
    - SQLAlchemy for database interactions
    - Redis for caching and rate limiting
"""

import logging
import time
from typing import Callable

import sentry_sdk
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware

from neuroca.api.routes import admin, cognitive, health, integration, memory
from neuroca.config import settings
from neuroca.core.exceptions import (
    NCAAuthenticationError,
    NCAAuthorizationError,
    NCACoreException,
    NCAResourceNotFoundError,
    NCAValidationError,
)

# Import health registration and component IDs
from neuroca.core.health.dynamics import get_health_dynamics, register_component_for_health_tracking
from neuroca.core.logging import configure_logging
from neuroca.memory.manager import (
    EPISODIC_MEMORY_COMPONENT_ID,
    MEMORY_MANAGER_COMPONENT_ID,
    SEMANTIC_MEMORY_COMPONENT_ID,
    WORKING_MEMORY_COMPONENT_ID,
)

# Configure logging
logger = logging.getLogger(__name__)
configure_logging()

# Initialize Sentry for error tracking if configured
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.2,
    )
    logger.info("Sentry integration initialized")

# Create FastAPI application
app = FastAPI(
    title="NeuroCognitive Architecture API",
    description="API for interacting with the NeuroCognitive Architecture (NCA) system",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
)

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request information and timing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", "")
        logger.debug(f"Request started: {request.method} {request.url.path} (ID: {request_id})")
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.debug(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.3f}s "
                f"(ID: {request_id})"
            )
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.exception(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Time: {process_time:.3f}s "
                f"(ID: {request_id})"
            )
            raise


# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(NCAAuthenticationError)
async def authentication_exception_handler(request: Request, exc: NCAAuthenticationError) -> JSONResponse:
    """Handle authentication errors."""
    logger.warning(f"Authentication error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.exception_handler(NCAAuthorizationError)
async def authorization_exception_handler(request: Request, exc: NCAAuthorizationError) -> JSONResponse:
    """Handle authorization errors."""
    logger.warning(f"Authorization error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


@app.exception_handler(NCAResourceNotFoundError)
async def not_found_exception_handler(request: Request, exc: NCAResourceNotFoundError) -> JSONResponse:
    """Handle resource not found errors."""
    logger.info(f"Resource not found: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(NCAValidationError)
async def validation_exception_handler(request: Request, exc: NCAValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.info(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(NCACoreException)
async def core_exception_handler(request: Request, exc: NCACoreException) -> JSONResponse:
    """Handle general NCA core exceptions."""
    logger.error(f"Core exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify API is running.
    
    Returns:
        Dict with status information
    """
    return {"status": "ok", "version": app.version}


# Include routers from route modules
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(cognitive.router, prefix="/api/cognitive", tags=["Cognitive"])
app.include_router(integration.router, prefix="/api/integration", tags=["Integration"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.on_event("startup")
async def startup_event() -> None:
    """
    Execute startup tasks when the API server starts.
    
    This includes:
    - Connecting to databases
    - Initializing caches
    - Setting up background tasks
    - Validating configurations
    - Registering components with the health system
    """
    logger.info("API server starting up")
    
    # Register core components with the Health Dynamics Manager
    try:
        logger.info("Registering components for health tracking...")
        register_component_for_health_tracking(WORKING_MEMORY_COMPONENT_ID)
        register_component_for_health_tracking(EPISODIC_MEMORY_COMPONENT_ID)
        register_component_for_health_tracking(SEMANTIC_MEMORY_COMPONENT_ID)
        register_component_for_health_tracking(MEMORY_MANAGER_COMPONENT_ID)
        # Register other core components as needed (e.g., database, external APIs)
        
        # Start scheduled health updates
        health_manager = get_health_dynamics()
        health_manager.start_scheduled_updates(interval_seconds=settings.HEALTH_UPDATE_INTERVAL) # Assuming interval is in settings
        
        logger.info("Health system components registered and scheduler started.")
        
    except Exception as e:
        logger.exception(f"Failed to initialize health system components: {e}")
        # Decide if this is a fatal error preventing startup

    # Initialize other connections and resources here
    # e.g., database connections, cache initialization


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Execute shutdown tasks when the API server stops.
    
    This includes:
    - Closing database connections
    - Cleaning up resources
    - Stopping background tasks
    - Stopping health scheduler
    """
    logger.info("API server shutting down")

    # Stop health dynamics scheduler
    try:
        health_manager = get_health_dynamics()
        health_manager.stop_scheduled_updates()
        logger.info("Health dynamics scheduler stopped.")
    except Exception as e:
        logger.exception(f"Error stopping health dynamics scheduler: {e}")

    # Clean up other connections and resources here
    # e.g., closing database connections


if __name__ == "__main__":
    # This block is used when running the app directly (not recommended for production)
    import uvicorn
    
    logger.warning("Running API directly with uvicorn. This is not recommended for production.")
    uvicorn.run(
        "neuroca.api.app:app",
        host="127.0.0.1",  # Default to localhost for direct execution
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
