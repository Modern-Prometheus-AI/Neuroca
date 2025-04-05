"""
Middleware Package for NeuroCognitive Architecture (NCA) API

This package contains middleware components that process requests and responses
for the NCA API. Middleware functions are executed in the order they are applied
to the application and can modify the request/response objects or terminate the
request-response cycle early.

The middleware components in this package handle cross-cutting concerns such as:
- Authentication and authorization
- Request logging and tracing
- Error handling and normalization
- Rate limiting and throttling
- Request validation
- Response formatting
- CORS (Cross-Origin Resource Sharing)
- Health monitoring integration

Usage:
    In your FastAPI application:

    ```python
    from fastapi import FastAPI
    from neuroca.api.middleware import (
        setup_middleware,
        AuthMiddleware,
        LoggingMiddleware,
        ErrorHandlingMiddleware,
    )

    app = FastAPI()
    
    # Apply all default middleware
    setup_middleware(app)
    
    # Or apply specific middleware individually
    app.add_middleware(AuthMiddleware)
    app.add_middleware(LoggingMiddleware)
    ```
"""

import logging
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from neuroca.api.middleware.auth import AuthMiddleware
from neuroca.api.middleware.error_handling import ErrorHandlingMiddleware
from neuroca.api.middleware.logging import LoggingMiddleware
from neuroca.api.middleware.rate_limiting import RateLimitingMiddleware
from neuroca.api.middleware.request_validation import RequestValidationMiddleware
from neuroca.api.middleware.response_formatting import ResponseFormattingMiddleware
from neuroca.api.middleware.tracing import TracingMiddleware
from neuroca.config import settings

logger = logging.getLogger(__name__)

__all__ = [
    "setup_middleware",
    "AuthMiddleware",
    "ErrorHandlingMiddleware",
    "LoggingMiddleware",
    "RateLimitingMiddleware",
    "RequestValidationMiddleware",
    "ResponseFormattingMiddleware",
    "TracingMiddleware",
]


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS (Cross-Origin Resource Sharing) for the application.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )
    logger.debug("CORS middleware configured with origins: %s", settings.CORS_ALLOW_ORIGINS)


def setup_trusted_hosts(app: FastAPI) -> None:
    """
    Configure trusted hosts middleware to prevent host header attacks.
    
    Args:
        app: The FastAPI application instance
    """
    if settings.TRUSTED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.TRUSTED_HOSTS,
        )
        logger.debug("Trusted hosts middleware configured with hosts: %s", settings.TRUSTED_HOSTS)


def setup_compression(app: FastAPI) -> None:
    """
    Configure response compression middleware.
    
    Args:
        app: The FastAPI application instance
    """
    if settings.ENABLE_GZIP_COMPRESSION:
        app.add_middleware(
            GZipMiddleware,
            minimum_size=settings.GZIP_MIN_SIZE,
        )
        logger.debug("GZip compression middleware configured with minimum size: %d bytes", 
                    settings.GZIP_MIN_SIZE)


def setup_custom_middleware(
    app: FastAPI,
    middleware_classes: Optional[list[type[BaseHTTPMiddleware]]] = None,
    skip_default: bool = False,
) -> None:
    """
    Configure custom middleware for the application.
    
    Args:
        app: The FastAPI application instance
        middleware_classes: Optional list of custom middleware classes to add
        skip_default: If True, skip adding the default middleware classes
    """
    # Default middleware classes in order of execution (first to last)
    default_middleware = [
        ErrorHandlingMiddleware,  # Should be first to catch errors from other middleware
        LoggingMiddleware,
        TracingMiddleware,
        AuthMiddleware,
        RateLimitingMiddleware,
        RequestValidationMiddleware,
        ResponseFormattingMiddleware,
    ]
    
    # Apply default middleware unless skipped
    if not skip_default:
        for middleware_class in default_middleware:
            try:
                app.add_middleware(middleware_class)
                logger.debug("Added middleware: %s", middleware_class.__name__)
            except Exception as e:
                logger.error("Failed to add middleware %s: %s", middleware_class.__name__, str(e))
                # Continue adding other middleware even if one fails
    
    # Apply custom middleware if provided
    if middleware_classes:
        for middleware_class in middleware_classes:
            try:
                app.add_middleware(middleware_class)
                logger.debug("Added custom middleware: %s", middleware_class.__name__)
            except Exception as e:
                logger.error("Failed to add custom middleware %s: %s", middleware_class.__name__, str(e))


def setup_middleware(
    app: FastAPI,
    custom_middleware: Optional[list[type[BaseHTTPMiddleware]]] = None,
    skip_default_middleware: bool = False,
    skip_cors: bool = False,
    skip_trusted_hosts: bool = False,
    skip_compression: bool = False,
) -> None:
    """
    Configure all middleware for the FastAPI application.
    
    This function sets up all middleware components in the correct order.
    The order of middleware is important as they are executed in reverse order
    of addition (last added, first executed).
    
    Args:
        app: The FastAPI application instance
        custom_middleware: Optional list of custom middleware classes to add
        skip_default_middleware: If True, skip adding the default middleware classes
        skip_cors: If True, skip CORS middleware setup
        skip_trusted_hosts: If True, skip trusted hosts middleware setup
        skip_compression: If True, skip compression middleware setup
        
    Example:
        ```python
        from fastapi import FastAPI
        from neuroca.api.middleware import setup_middleware
        
        app = FastAPI()
        setup_middleware(app)
        ```
    """
    logger.info("Setting up API middleware")
    
    # Setup middleware in reverse order of execution (last executed first)
    
    # Setup custom middleware (executed first in the chain)
    setup_custom_middleware(
        app, 
        middleware_classes=custom_middleware,
        skip_default=skip_default_middleware
    )
    
    # Setup compression (executed after custom middleware)
    if not skip_compression:
        setup_compression(app)
    
    # Setup trusted hosts (executed after compression)
    if not skip_trusted_hosts:
        setup_trusted_hosts(app)
    
    # Setup CORS (executed last in the chain)
    if not skip_cors:
        setup_cors(app)
    
    logger.info("API middleware setup complete")


# Middleware initialization hook for plugin systems or extensions
def register_middleware_plugin(plugin_func: Callable[[FastAPI], None]) -> None:
    """
    Register a middleware plugin function that will be called during middleware setup.
    
    This function is intended for use by plugins or extensions that need to add
    their own middleware to the application.
    
    Args:
        plugin_func: A callable that takes a FastAPI instance and adds middleware
        
    Example:
        ```python
        from fastapi import FastAPI
        from neuroca.api.middleware import register_middleware_plugin
        
        def add_my_plugin_middleware(app: FastAPI):
            app.add_middleware(MyPluginMiddleware)
        
        register_middleware_plugin(add_my_plugin_middleware)
        ```
    """
    # This is a placeholder for a more complex plugin registration system
    # In a real implementation, this would store the plugin function in a registry
    # that would be accessed during setup_middleware
    logger.warning("Middleware plugin registration is not fully implemented")
    # For now, just log that we received a plugin registration request
    logger.info("Received middleware plugin registration: %s", plugin_func.__name__)