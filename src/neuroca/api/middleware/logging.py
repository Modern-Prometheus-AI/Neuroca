"""
Logging Middleware for NeuroCognitive Architecture API

This module provides middleware components for comprehensive API request/response logging,
performance tracking, and diagnostic information capture. It implements structured logging
with correlation IDs to track requests across the system and configurable log levels based
on environment settings.

Features:
- Request/response logging with configurable verbosity
- Performance metrics for request processing time
- Correlation ID generation and propagation
- Sanitization of sensitive data in logs
- Integration with the application's logging infrastructure
- Support for both synchronous and asynchronous request handling

Usage:
    In a FastAPI application:
    ```python
    from fastapi import FastAPI
    from neuroca.api.middleware.logging import RequestLoggingMiddleware

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    ```

    For manual usage in route handlers:
    ```python
    from fastapi import Depends, FastAPI
    from neuroca.api.middleware.logging import get_request_logger

    app = FastAPI()

    @app.get("/example")
    async def example_route(logger=Depends(get_request_logger)):
        logger.info("Processing example route")
        return {"status": "success"}
    ```
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Create a context variable to store the correlation ID
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="")

# Configure module logger
logger = logging.getLogger("neuroca.api.middleware.logging")

# Default paths that won't be logged (health checks, metrics, etc.)
DEFAULT_EXCLUDE_PATHS: set[str] = {
    "/health", 
    "/metrics", 
    "/ping", 
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json"
}

# Default headers that should be redacted from logs
SENSITIVE_HEADERS: set[str] = {
    "authorization", 
    "x-api-key", 
    "api-key", 
    "cookie", 
    "password",
    "token",
    "secret"
}

# Default fields in request/response bodies that should be redacted
SENSITIVE_FIELDS: set[str] = {
    "password", 
    "token", 
    "secret", 
    "api_key", 
    "apiKey", 
    "access_token", 
    "refresh_token",
    "credit_card",
    "creditCard",
    "ssn",
    "social_security"
}


def get_correlation_id() -> str:
    """
    Get the current correlation ID from context or generate a new one.
    
    Returns:
        str: The correlation ID for the current context
    """
    try:
        return correlation_id_context.get()
    except LookupError:
        # If no correlation ID exists, generate a new one
        new_id = str(uuid.uuid4())
        correlation_id_context.set(new_id)
        return new_id


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set a correlation ID in the current context.
    
    Args:
        correlation_id: Optional correlation ID to use. If None, generates a new UUID.
        
    Returns:
        str: The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    correlation_id_context.set(correlation_id)
    return correlation_id


def get_request_logger() -> logging.Logger:
    """
    Get a logger with the current correlation ID attached.
    
    This function can be used as a FastAPI dependency to inject a logger
    into route handlers.
    
    Returns:
        logging.Logger: A logger with correlation ID in the extra field
    """
    correlation_id = get_correlation_id()
    request_logger = logging.LoggerAdapter(
        logger, 
        {"correlation_id": correlation_id}
    )
    return request_logger


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """
    Sanitize headers by redacting sensitive information.
    
    Args:
        headers: Dictionary of HTTP headers
        
    Returns:
        Dict[str, str]: Sanitized headers with sensitive values redacted
    """
    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower in SENSITIVE_HEADERS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


def sanitize_body(body: Union[dict[str, Any], list[Any], str, None]) -> Union[dict[str, Any], list[Any], str, None]:
    """
    Sanitize request/response body by redacting sensitive fields.
    
    Args:
        body: The body to sanitize, can be dict, list, string or None
        
    Returns:
        The sanitized body with sensitive values redacted
    """
    if body is None:
        return None
    
    if isinstance(body, str):
        try:
            # Try to parse as JSON
            parsed_body = json.loads(body)
            sanitized = sanitize_body(parsed_body)
            return json.dumps(sanitized)
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, return as is
            return body
    
    if isinstance(body, dict):
        sanitized = {}
        for key, value in body.items():
            if key.lower() in SENSITIVE_FIELDS:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_body(value)
            else:
                sanitized[key] = value
        return sanitized
    
    if isinstance(body, list):
        return [sanitize_body(item) if isinstance(item, (dict, list)) else item for item in body]
    
    return body


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    This middleware logs information about incoming requests and outgoing responses,
    including timing information, status codes, and sanitized request/response data.
    It also manages correlation IDs for request tracing.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        exclude_paths: Optional[set[str]] = None,
        log_request_body: bool = True,
        log_response_body: bool = True,
        log_level: int = logging.INFO,
        correlation_id_header: str = "X-Correlation-ID"
    ):
        """
        Initialize the request logging middleware.
        
        Args:
            app: The ASGI application
            exclude_paths: Set of URL paths to exclude from logging
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            log_level: The logging level to use
            correlation_id_header: The header name for correlation IDs
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or DEFAULT_EXCLUDE_PATHS
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_level = log_level
        self.correlation_id_header = correlation_id_header
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request, log details, and return the response.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint in the chain
            
        Returns:
            Response: The HTTP response
        """
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Extract or generate correlation ID
        correlation_id = request.headers.get(self.correlation_id_header)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set correlation ID in context
        set_correlation_id(correlation_id)
        
        # Get logger with correlation ID
        request_logger = get_request_logger()
        
        # Start timing the request
        start_time = time.time()
        
        # Log request details
        await self._log_request(request, request_logger)
        
        # Process the request and catch any exceptions
        try:
            response = await call_next(request)
            
            # Calculate request processing time
            process_time = time.time() - start_time
            
            # Log response details
            self._log_response(response, process_time, request_logger)
            
            # Add correlation ID to response headers
            response.headers[self.correlation_id_header] = correlation_id
            
            return response
            
        except Exception as e:
            # Log exception details
            process_time = time.time() - start_time
            request_logger.exception(
                f"Request failed after {process_time:.4f}s: {str(e)}",
                extra={"exception": str(e), "process_time": process_time}
            )
            # Re-raise the exception to be handled by exception handlers
            raise
    
    async def _log_request(self, request: Request, request_logger: logging.LoggerAdapter) -> None:
        """
        Log details about the incoming request.
        
        Args:
            request: The incoming HTTP request
            request_logger: Logger with correlation ID
        """
        # Prepare request info for logging
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "headers": sanitize_headers(dict(request.headers)),
            "query_params": dict(request.query_params),
            "path_params": request.path_params,
        }
        
        # Log request body if enabled
        if self.log_request_body:
            try:
                # Clone the request body to avoid consuming it
                body_bytes = await request.body()
                request.scope["_body"] = body_bytes  # Save for later reuse
                
                # Try to parse as JSON
                try:
                    body = json.loads(body_bytes.decode("utf-8"))
                    request_info["body"] = sanitize_body(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If not JSON, include the content type but not the raw body
                    content_type = request.headers.get("content-type", "unknown")
                    request_info["body"] = f"<binary or non-JSON data: {content_type}>"
            except Exception as e:
                request_logger.warning(f"Failed to capture request body: {str(e)}")
                request_info["body"] = "<error reading body>"
        
        request_logger.log(
            self.log_level,
            f"Incoming request: {request.method} {request.url.path}",
            extra={"request": request_info}
        )
    
    def _log_response(
        self, response: Response, process_time: float, response_logger: logging.LoggerAdapter
    ) -> None:
        """
        Log details about the outgoing response.
        
        Args:
            response: The HTTP response
            process_time: Time taken to process the request in seconds
            response_logger: Logger with correlation ID
        """
        # Prepare response info for logging
        response_info = {
            "status_code": response.status_code,
            "headers": sanitize_headers(dict(response.headers)),
            "process_time": f"{process_time:.4f}s",
        }
        
        # Log response body if enabled and not a binary response
        if self.log_response_body:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # For JSON responses, we can safely log the body
                    body = json.loads(response.body.decode("utf-8"))
                    response_info["body"] = sanitize_body(body)
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                    response_info["body"] = "<error decoding JSON body>"
            elif "text/" in content_type:
                # For text responses, log as string
                try:
                    response_info["body"] = response.body.decode("utf-8")
                except (UnicodeDecodeError, AttributeError):
                    response_info["body"] = "<error decoding text body>"
            else:
                # For binary responses, just log the content type
                response_info["body"] = f"<binary data: {content_type}>"
        
        # Log at appropriate level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = self.log_level
        
        response_logger.log(
            log_level,
            f"Response: {response.status_code} (took {process_time:.4f}s)",
            extra={"response": response_info}
        )


class LoggingRoute(APIRoute):
    """
    Custom API route that logs request and response details.
    
    This can be used as an alternative to the middleware approach for more
    fine-grained control over logging at the route level.
    """
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            # Extract or generate correlation ID
            correlation_id = request.headers.get("X-Correlation-ID")
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
            
            # Set correlation ID in context
            set_correlation_id(correlation_id)
            
            # Get logger with correlation ID
            request_logger = get_request_logger()
            
            # Start timing
            start_time = time.time()
            
            # Log request
            request_logger.info(
                f"Request: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "headers": sanitize_headers(dict(request.headers))
                }
            )
            
            # Process request
            try:
                response = await original_route_handler(request)
                
                # Calculate processing time
                process_time = time.time() - start_time
                
                # Log response
                request_logger.info(
                    f"Response: {response.status_code} (took {process_time:.4f}s)",
                    extra={
                        "status_code": response.status_code,
                        "process_time": f"{process_time:.4f}s",
                        "headers": sanitize_headers(dict(response.headers))
                    }
                )
                
                # Add correlation ID to response
                response.headers["X-Correlation-ID"] = correlation_id
                
                return response
                
            except Exception as e:
                # Log exception
                process_time = time.time() - start_time
                request_logger.exception(
                    f"Error processing request: {str(e)} (after {process_time:.4f}s)",
                    extra={"exception": str(e), "process_time": process_time}
                )
                raise
        
        return custom_route_handler


def setup_request_logging(
    app: FastAPI,
    exclude_paths: Optional[set[str]] = None,
    log_request_body: bool = True,
    log_response_body: bool = True,
    log_level: int = logging.INFO,
    correlation_id_header: str = "X-Correlation-ID"
) -> None:
    """
    Set up request logging for a FastAPI application.
    
    This is a convenience function to add the RequestLoggingMiddleware
    to a FastAPI application with the specified configuration.
    
    Args:
        app: The FastAPI application
        exclude_paths: Set of URL paths to exclude from logging
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        log_level: The logging level to use
        correlation_id_header: The header name for correlation IDs
    """
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=exclude_paths,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        log_level=log_level,
        correlation_id_header=correlation_id_header
    )
    
    logger.info("Request logging middleware configured")