"""
Distributed Tracing Middleware for NeuroCognitive Architecture API.

This module provides middleware components for implementing distributed tracing
across the NCA system. It integrates with OpenTelemetry to provide detailed
request tracing, performance metrics, and diagnostic capabilities for the API layer.

The tracing middleware automatically:
1. Creates spans for each request
2. Adds relevant request metadata to spans
3. Propagates trace context across service boundaries
4. Handles error tracking and reporting
5. Provides configurable sampling and filtering

Usage:
    In a FastAPI application:
    ```python
    from fastapi import FastAPI
    from neuroca.api.middleware.tracing import TracingMiddleware, setup_tracing

    # Initialize tracing with the service name
    setup_tracing("neuroca-api")

    app = FastAPI()
    app.add_middleware(TracingMiddleware)
    ```

    In an ASGI application:
    ```python
    from neuroca.api.middleware.tracing import TracingMiddleware
    
    app = TracingMiddleware(your_asgi_app)
    ```
"""

import functools
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio, TraceIdRatioBased
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Configure logger
logger = logging.getLogger(__name__)

# Context variable to store the current request ID
current_request_id: ContextVar[str] = ContextVar("current_request_id", default="")

# Context variable to store the current trace ID
current_trace_id: ContextVar[str] = ContextVar("current_trace_id", default="")

# List of paths that should not be traced
DEFAULT_EXCLUDE_PATHS = [
    "/health",
    "/metrics",
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json",
]


def setup_tracing(
    service_name: str,
    sample_rate: float = 0.1,
    otlp_endpoint: Optional[str] = None,
    console_export: bool = False,
    exclude_paths: Optional[list[str]] = None,
) -> None:
    """
    Set up OpenTelemetry tracing for the application.

    Args:
        service_name: Name of the service for identification in traces
        sample_rate: Percentage of traces to sample (0.0 to 1.0)
        otlp_endpoint: Optional OTLP exporter endpoint (e.g., "localhost:4317")
        console_export: Whether to also export spans to console (for debugging)
        exclude_paths: List of URL paths to exclude from tracing

    Returns:
        None
    
    Raises:
        ValueError: If sample_rate is not between 0.0 and 1.0
    """
    if not 0.0 <= sample_rate <= 1.0:
        raise ValueError("Sample rate must be between 0.0 and 1.0")

    # Create a resource with service information
    resource = Resource.create({"service.name": service_name})
    
    # Configure the tracer provider with the resource
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBasedTraceIdRatio(TraceIdRatioBased(sample_rate))
    )
    
    # Set up exporters
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP exporter configured with endpoint: {otlp_endpoint}")
    
    if console_export or not otlp_endpoint:
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console exporter configured for tracing")
    
    # Set the global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Store excluded paths
    if exclude_paths is not None:
        TracingMiddleware.exclude_paths = exclude_paths
    
    logger.info(f"Tracing initialized for service: {service_name} with sample rate: {sample_rate}")


def get_request_id() -> str:
    """
    Get the current request ID from context.
    
    Returns:
        The current request ID or an empty string if not set
    """
    return current_request_id.get()


def get_trace_id() -> str:
    """
    Get the current trace ID from context.
    
    Returns:
        The current trace ID or an empty string if not set
    """
    return current_trace_id.get()


def with_traced_function(name: Optional[str] = None):
    """
    Decorator to create a span for a function.
    
    Args:
        name: Optional name for the span. If not provided, the function name is used.
    
    Returns:
        Decorator function
    
    Example:
        @with_traced_function("process_user_data")
        async def process_user(user_id: str):
            # This function will create a span named "process_user_data"
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function arguments as span attributes (excluding self/cls)
                # Be careful not to include sensitive data
                safe_args = {}
                if args and hasattr(args[0], '__class__'):
                    # Skip self/cls argument for methods
                    safe_args = {f"arg_{i}": str(arg) for i, arg in enumerate(args[1:])}
                else:
                    safe_args = {f"arg_{i}": str(arg) for i, arg in enumerate(args)}
                
                # Add only non-sensitive kwargs
                safe_kwargs = {
                    k: str(v) for k, v in kwargs.items() 
                    if not any(sensitive in k.lower() for sensitive in 
                              ['password', 'token', 'secret', 'key', 'auth'])
                }
                
                for k, v in safe_args.items():
                    span.set_attribute(k, v)
                
                for k, v in safe_kwargs.items():
                    span.set_attribute(k, v)
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function arguments as span attributes (excluding self/cls)
                # Be careful not to include sensitive data
                safe_args = {}
                if args and hasattr(args[0], '__class__'):
                    # Skip self/cls argument for methods
                    safe_args = {f"arg_{i}": str(arg) for i, arg in enumerate(args[1:])}
                else:
                    safe_args = {f"arg_{i}": str(arg) for i, arg in enumerate(args)}
                
                # Add only non-sensitive kwargs
                safe_kwargs = {
                    k: str(v) for k, v in kwargs.items() 
                    if not any(sensitive in k.lower() for sensitive in 
                              ['password', 'token', 'secret', 'key', 'auth'])
                }
                
                for k, v in safe_args.items():
                    span.set_attribute(k, v)
                
                for k, v in safe_kwargs.items():
                    span.set_attribute(k, v)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding distributed tracing to FastAPI/Starlette applications.
    
    This middleware:
    1. Creates a unique request ID for each request
    2. Creates a trace span for each request
    3. Adds request metadata to the span
    4. Propagates trace context across service boundaries
    5. Records response status and timing information
    
    Attributes:
        exclude_paths: List of URL paths to exclude from tracing
    """
    
    exclude_paths = DEFAULT_EXCLUDE_PATHS
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process an incoming request with tracing.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The HTTP response
        """
        # Skip tracing for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        current_request_id.set(request_id)
        
        # Extract trace context from headers if present
        carrier = dict(request.headers.items())
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        
        # Start a new span for this request
        tracer = trace.get_tracer(__name__)
        span_name = f"{request.method} {request.url.path}"
        
        with tracer.start_as_current_span(
            span_name, context=ctx, kind=trace.SpanKind.SERVER
        ) as span:
            # Store trace ID in context
            span_context = span.get_span_context()
            if span_context.trace_id:
                trace_id_hex = format(span_context.trace_id, '032x')
                current_trace_id.set(trace_id_hex)
            
            # Add request metadata to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.host", request.headers.get("host", ""))
            span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
            span.set_attribute("http.request_id", request_id)
            span.set_attribute("http.route", request.url.path)
            
            # Add client information
            client = request.client
            if client:
                span.set_attribute("http.client_ip", client.host)
                if client.port:
                    span.set_attribute("http.client_port", client.port)
            
            # Record request start time
            start_time = time.time()
            
            try:
                # Process the request
                response = await call_next(request)
                
                # Add response metadata to span
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_time_ms", (time.time() - start_time) * 1000)
                
                # Add the request ID to the response headers
                response.headers["X-Request-ID"] = request_id
                
                # Add trace ID to response headers for debugging
                if current_trace_id.get():
                    response.headers["X-Trace-ID"] = current_trace_id.get()
                
                # Set span status based on response
                if 400 <= response.status_code < 600:
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR,
                            f"HTTP {response.status_code}"
                        )
                    )
                
                return response
            except Exception as e:
                # Record exception in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                # Log the error with trace information
                logger.error(
                    f"Request failed: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "trace_id": current_trace_id.get(),
                        "path": request.url.path,
                        "method": request.method,
                    },
                    exc_info=True,
                )
                
                # Re-raise the exception
                raise


class ASGITracingMiddleware:
    """
    ASGI middleware for distributed tracing.
    
    This middleware implements the ASGI interface directly for applications
    that don't use Starlette's BaseHTTPMiddleware.
    
    Attributes:
        app: The ASGI application
        exclude_paths: List of URL paths to exclude from tracing
    """
    
    def __init__(self, app: ASGIApp, exclude_paths: Optional[list[str]] = None):
        """
        Initialize the ASGI tracing middleware.
        
        Args:
            app: The ASGI application to wrap
            exclude_paths: Optional list of URL paths to exclude from tracing
        """
        self.app = app
        self.exclude_paths = exclude_paths or DEFAULT_EXCLUDE_PATHS
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process an ASGI request with tracing.
        
        Args:
            scope: The ASGI connection scope
            receive: The ASGI receive function
            send: The ASGI send function
        """
        if scope["type"] != "http":
            # Pass through non-HTTP requests (like WebSockets) without tracing
            await self.app(scope, receive, send)
            return
        
        # Extract path from scope
        path = scope.get("path", "")
        
        # Skip tracing for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            await self.app(scope, receive, send)
            return
        
        # Generate or extract request ID from headers
        request_id = None
        for name, value in scope.get("headers", []):
            if name.decode("latin1").lower() == "x-request-id":
                request_id = value.decode("latin1")
                break
        
        if not request_id:
            request_id = str(uuid.uuid4())
        
        current_request_id.set(request_id)
        
        # Extract trace context from headers
        carrier = {}
        for name, value in scope.get("headers", []):
            carrier[name.decode("latin1").lower()] = value.decode("latin1")
        
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        
        # Start a new span for this request
        tracer = trace.get_tracer(__name__)
        method = scope.get("method", "UNKNOWN")
        span_name = f"{method} {path}"
        
        with tracer.start_as_current_span(
            span_name, context=ctx, kind=trace.SpanKind.SERVER
        ) as span:
            # Store trace ID in context
            span_context = span.get_span_context()
            if span_context.trace_id:
                trace_id_hex = format(span_context.trace_id, '032x')
                current_trace_id.set(trace_id_hex)
            
            # Add request metadata to span
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", f"{scope.get('scheme', 'http')}://{scope.get('server', ['localhost', 80])[0]}{path}")
            span.set_attribute("http.request_id", request_id)
            span.set_attribute("http.route", path)
            
            # Add client information
            client = scope.get("client")
            if client:
                span.set_attribute("http.client_ip", client[0])
                span.set_attribute("http.client_port", client[1])
            
            # Record request start time
            start_time = time.time()
            
            # Create a modified send function to capture response data
            response_status = [200]  # Default status code
            
            async def send_with_tracing(message: Message) -> None:
                if message["type"] == "http.response.start":
                    # Capture the status code
                    response_status[0] = message["status"]
                    
                    # Add headers to the response
                    headers = message.get("headers", [])
                    
                    # Add request ID header
                    headers.append((b"x-request-id", request_id.encode("latin1")))
                    
                    # Add trace ID header if available
                    if current_trace_id.get():
                        headers.append((b"x-trace-id", current_trace_id.get().encode("latin1")))
                    
                    # Update headers in the message
                    message["headers"] = headers
                
                await send(message)
            
            try:
                # Process the request
                await self.app(scope, receive, send_with_tracing)
                
                # Add response metadata to span
                span.set_attribute("http.status_code", response_status[0])
                span.set_attribute("http.response_time_ms", (time.time() - start_time) * 1000)
                
                # Set span status based on response
                if 400 <= response_status[0] < 600:
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR,
                            f"HTTP {response_status[0]}"
                        )
                    )
            except Exception as e:
                # Record exception in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                # Log the error with trace information
                logger.error(
                    f"Request failed: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "trace_id": current_trace_id.get(),
                        "path": path,
                        "method": method,
                    },
                    exc_info=True,
                )
                
                # Re-raise the exception
                raise


def instrument_fastapi(app: FastAPI, excluded_urls: Optional[list[str]] = None) -> None:
    """
    Instrument a FastAPI application with OpenTelemetry.
    
    This function uses the FastAPIInstrumentor to automatically instrument
    all routes in a FastAPI application.
    
    Args:
        app: The FastAPI application to instrument
        excluded_urls: Optional list of URL patterns to exclude from instrumentation
        
    Returns:
        None
    """
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=excluded_urls or DEFAULT_EXCLUDE_PATHS,
        tracer_provider=trace.get_tracer_provider(),
    )
    logger.info("FastAPI application instrumented with OpenTelemetry")


# Import asyncio at the end to avoid circular imports with the decorator
import asyncio