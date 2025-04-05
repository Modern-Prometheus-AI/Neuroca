"""
Tracing Middleware for NeuroCognitive Architecture (NCA)

This module provides middleware components for distributed tracing across the NCA system.
It integrates with OpenTelemetry to provide comprehensive tracing capabilities for
monitoring system performance, debugging issues, and understanding request flows.

The middleware can be used with various web frameworks (FastAPI, Flask, Django) and
supports both synchronous and asynchronous request handling.

Usage:
    # FastAPI example
    from fastapi import FastAPI
    from neuroca.monitoring.tracing.middleware import setup_tracing, TracingMiddleware

    app = FastAPI()
    tracer_provider = setup_tracing("my-nca-service")
    app.add_middleware(TracingMiddleware)

    # Flask example
    from flask import Flask
    from neuroca.monitoring.tracing.middleware import setup_tracing, FlaskTracingMiddleware

    app = Flask(__name__)
    tracer_provider = setup_tracing("my-nca-service")
    app.wsgi_app = FlaskTracingMiddleware(app.wsgi_app)
"""

import functools
import inspect
import logging
import time
from contextvars import ContextVar
from typing import Any, Callable, Optional

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio, TraceIdRatioBased
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Starlette/FastAPI specific imports (for type hints)
try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp, Receive, Scope, Send
except ImportError:
    # Define placeholder classes for type checking when Starlette is not installed
    class BaseHTTPMiddleware:
        pass

    class Request:
        pass

    class Response:
        pass

    ASGIApp = Any
    Receive = Any
    Scope = Any
    Send = Any

# Flask specific imports (for type hints)
try:
    from flask import Flask
    from flask import Request as FlaskRequest
    from werkzeug.wsgi import ClosingIterator
except ImportError:
    # Define placeholder classes for type checking when Flask is not installed
    Flask = Any
    FlaskRequest = Any
    ClosingIterator = Any

# Set up module logger
logger = logging.getLogger(__name__)

# Context variable to store the current trace context
current_span_ctx = ContextVar("current_span_ctx", default=None)

# Default attributes to be captured from requests
DEFAULT_REQUEST_ATTRIBUTES = [
    "http.method",
    "http.url",
    "http.host",
    "http.scheme",
    "http.target",
    "http.user_agent",
    "http.request_content_length",
    "http.response_content_length",
    "http.status_code",
    "http.route",
]

# Default headers to be captured from requests
DEFAULT_CAPTURED_HEADERS = [
    "content-type",
    "user-agent",
    "x-request-id",
    "x-correlation-id",
]


def setup_tracing(
    service_name: str,
    sample_rate: float = 1.0,
    otlp_endpoint: Optional[str] = None,
    console_export: bool = False,
    additional_resource_attributes: Optional[dict[str, str]] = None,
) -> TracerProvider:
    """
    Set up OpenTelemetry tracing for the application.

    Args:
        service_name: Name of the service for identification in traces
        sample_rate: Sampling rate between 0.0 and 1.0 (1.0 = 100% of traces)
        otlp_endpoint: Optional OTLP endpoint for sending traces (e.g., "localhost:4317")
        console_export: Whether to also export traces to console (useful for debugging)
        additional_resource_attributes: Additional attributes to add to the resource

    Returns:
        Configured TracerProvider instance

    Example:
        ```python
        # Basic setup with default sampling
        tracer_provider = setup_tracing("nca-memory-service")

        # Setup with custom sampling and OTLP exporter
        tracer_provider = setup_tracing(
            "nca-core-service",
            sample_rate=0.1,  # Sample 10% of traces
            otlp_endpoint="collector:4317",
            additional_resource_attributes={"deployment.environment": "production"}
        )
        ```
    """
    # Validate inputs
    if not service_name:
        raise ValueError("Service name must be provided")
    
    if not 0.0 <= sample_rate <= 1.0:
        raise ValueError("Sample rate must be between 0.0 and 1.0")

    # Create resource with service information
    resource_attributes = {SERVICE_NAME: service_name}
    if additional_resource_attributes:
        resource_attributes.update(additional_resource_attributes)
    
    resource = Resource.create(resource_attributes)

    # Configure trace provider with appropriate sampler
    sampler = ParentBasedTraceIdRatio(TraceIdRatioBased(sample_rate))
    tracer_provider = TracerProvider(resource=resource, sampler=sampler)
    
    # Set up exporters
    if otlp_endpoint:
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"Configured OTLP trace exporter with endpoint: {otlp_endpoint}")
    
    if console_export or not otlp_endpoint:
        # Add console exporter for debugging or as fallback
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Configured console trace exporter")
    
    # Set global trace provider
    trace.set_tracer_provider(tracer_provider)
    
    # Set global propagator
    trace.set_text_map_propagator(TraceContextTextMapPropagator())
    
    logger.info(f"Tracing initialized for service: {service_name} with sample rate: {sample_rate}")
    return tracer_provider


class TracingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware for request tracing.
    
    This middleware creates a span for each request and adds useful attributes
    like HTTP method, URL, status code, and duration.
    
    Example:
        ```python
        from fastapi import FastAPI
        from neuroca.monitoring.tracing.middleware import TracingMiddleware, setup_tracing
        
        app = FastAPI()
        setup_tracing("my-nca-service")
        app.add_middleware(TracingMiddleware)
        ```
    """
    
    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: Optional[list[str]] = None,
        captured_headers: Optional[list[str]] = None,
    ):
        """
        Initialize the tracing middleware.
        
        Args:
            app: The ASGI application
            excluded_paths: List of URL paths to exclude from tracing
            captured_headers: List of HTTP headers to capture in spans
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or []
        self.captured_headers = captured_headers or DEFAULT_CAPTURED_HEADERS
        self.tracer = trace.get_tracer(__name__)
        logger.debug("TracingMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process an incoming request with tracing.
        
        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/route handler
            
        Returns:
            The HTTP response
        """
        # Skip tracing for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        # Extract trace context from headers if present
        carrier = {k.lower(): v for k, v in request.headers.items()}
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        
        # Start a new span for this request
        with self.tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            kind=trace.SpanKind.SERVER,
            context=ctx,
        ) as span:
            # Store span context for potential use in route handlers
            token = current_span_ctx.set(trace.get_current_span(ctx).get_span_context())
            
            # Add request attributes to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname)
            span.set_attribute("http.target", request.url.path)
            
            # Add request headers to span
            for header in self.captured_headers:
                if header in request.headers:
                    span.set_attribute(f"http.request.header.{header}", request.headers[header])
            
            try:
                # Process the request
                response = await call_next(request)
                
                # Add response attributes to span
                span.set_attribute("http.status_code", response.status_code)
                
                # Add response headers to span
                for header in self.captured_headers:
                    if header in response.headers:
                        span.set_attribute(f"http.response.header.{header}", response.headers[header])
                
                # Record if the request was successful
                span.set_attribute("request.success", 200 <= response.status_code < 400)
                
                return response
            
            except Exception as exc:
                # Record exception information in the span
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                span.set_attribute("request.success", False)
                logger.exception("Exception in request processing")
                raise
            
            finally:
                # Reset the context variable
                current_span_ctx.reset(token)
                
                # Record request duration
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("request.duration_ms", duration_ms)


class FlaskTracingMiddleware:
    """
    Flask middleware for request tracing.
    
    This middleware wraps the Flask WSGI application to provide tracing for
    each request.
    
    Example:
        ```python
        from flask import Flask
        from neuroca.monitoring.tracing.middleware import FlaskTracingMiddleware, setup_tracing
        
        app = Flask(__name__)
        setup_tracing("my-nca-service")
        app.wsgi_app = FlaskTracingMiddleware(app.wsgi_app)
        ```
    """
    
    def __init__(
        self,
        app: Any,
        excluded_paths: Optional[list[str]] = None,
        captured_headers: Optional[list[str]] = None,
    ):
        """
        Initialize the Flask tracing middleware.
        
        Args:
            app: The Flask WSGI application
            excluded_paths: List of URL paths to exclude from tracing
            captured_headers: List of HTTP headers to capture in spans
        """
        self.app = app
        self.excluded_paths = excluded_paths or []
        self.captured_headers = captured_headers or DEFAULT_CAPTURED_HEADERS
        self.tracer = trace.get_tracer(__name__)
        logger.debug("FlaskTracingMiddleware initialized")
    
    def __call__(self, environ: dict, start_response: Callable) -> Any:
        """
        Process an incoming WSGI request with tracing.
        
        Args:
            environ: WSGI environment dictionary
            start_response: WSGI start_response callable
            
        Returns:
            WSGI response
        """
        # Skip tracing for excluded paths
        path_info = environ.get("PATH_INFO", "")
        if any(path_info.startswith(path) for path in self.excluded_paths):
            return self.app(environ, start_response)
        
        start_time = time.time()
        
        # Extract trace context from headers if present
        carrier = {
            k.lower().replace("http_", "").replace("_", "-"): v
            for k, v in environ.items()
            if k.startswith("HTTP_")
        }
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        
        # Start a new span for this request
        with self.tracer.start_as_current_span(
            f"{environ.get('REQUEST_METHOD', 'UNKNOWN')} {path_info}",
            kind=trace.SpanKind.SERVER,
            context=ctx,
        ) as span:
            # Store span context for potential use in route handlers
            token = current_span_ctx.set(trace.get_current_span(ctx).get_span_context())
            
            # Add request attributes to span
            span.set_attribute("http.method", environ.get("REQUEST_METHOD", "UNKNOWN"))
            span.set_attribute("http.url", environ.get("PATH_INFO", ""))
            span.set_attribute("http.scheme", environ.get("wsgi.url_scheme", "http"))
            span.set_attribute("http.host", environ.get("HTTP_HOST", "unknown"))
            span.set_attribute("http.target", environ.get("PATH_INFO", ""))
            
            # Add request headers to span
            for header in self.captured_headers:
                header_key = f"HTTP_{header.upper().replace('-', '_')}"
                if header_key in environ:
                    span.set_attribute(f"http.request.header.{header}", environ[header_key])
            
            # Capture the status code using a list to allow modification in the inner function
            status_info = {"code": 200, "success": True}
            
            def _start_response(status, response_headers, exc_info=None):
                # Extract status code from the status string (e.g., "200 OK")
                try:
                    status_info["code"] = int(status.split(" ")[0])
                    status_info["success"] = 200 <= status_info["code"] < 400
                except (ValueError, IndexError):
                    logger.warning(f"Failed to parse status code from: {status}")
                
                # Add response headers to span
                for header_name, header_value in response_headers:
                    if header_name.lower() in self.captured_headers:
                        span.set_attribute(f"http.response.header.{header_name.lower()}", header_value)
                
                return start_response(status, response_headers, exc_info)
            
            try:
                # Process the request
                response_iterable = self.app(environ, _start_response)
                
                # Create a closing iterator that will be called when the response is complete
                def _response_closer():
                    # Add response attributes to span
                    span.set_attribute("http.status_code", status_info["code"])
                    span.set_attribute("request.success", status_info["success"])
                    
                    # Record request duration
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("request.duration_ms", duration_ms)
                    
                    # Reset the context variable
                    current_span_ctx.reset(token)
                
                return ClosingIterator(response_iterable, [_response_closer])
                
            except Exception as exc:
                # Record exception information in the span
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                span.set_attribute("request.success", False)
                
                # Record request duration
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("request.duration_ms", duration_ms)
                
                # Reset the context variable
                current_span_ctx.reset(token)
                
                logger.exception("Exception in request processing")
                raise


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    Decorator to trace a function execution.
    
    This decorator creates a span for the function execution and records
    its duration, arguments, and result.
    
    Args:
        name: Optional custom name for the span (defaults to function name)
        attributes: Optional attributes to add to the span
        kind: Span kind (default: INTERNAL)
    
    Returns:
        Decorated function
    
    Example:
        ```python
        from neuroca.monitoring.tracing.middleware import trace_function
        
        @trace_function(attributes={"component": "memory_service"})
        def process_memory_item(item_id, content):
            # Function implementation
            return result
        
        @trace_function(name="async_memory_operation")
        async def retrieve_memory(memory_id):
            # Async function implementation
            return memory
        ```
    """
    def decorator(func):
        # Get the function name for use in the span name
        func_name = name or func.__qualname__
        tracer = trace.get_tracer(func.__module__)
        
        # Handle both synchronous and asynchronous functions
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Create span attributes from the combined attributes
                span_attributes = {}
                if attributes:
                    span_attributes.update(attributes)
                
                # Add function arguments as span attributes (safely)
                try:
                    # Get argument names from function signature
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    
                    # Add safe string representations of arguments
                    for arg_name, arg_value in bound_args.arguments.items():
                        # Skip 'self' and 'cls' arguments
                        if arg_name in ('self', 'cls'):
                            continue
                        
                        # Add a safe string representation (limit length)
                        try:
                            str_value = str(arg_value)
                            if len(str_value) > 100:
                                str_value = str_value[:97] + "..."
                            span_attributes[f"arg.{arg_name}"] = str_value
                        except Exception:
                            span_attributes[f"arg.{arg_name}"] = "<unprintable>"
                except Exception as e:
                    logger.debug(f"Failed to capture function arguments: {e}")
                
                with tracer.start_as_current_span(func_name, kind=kind, attributes=span_attributes) as span:
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        
                        # Record success and result type
                        span.set_attribute("function.success", True)
                        span.set_attribute("function.result_type", type(result).__name__)
                        
                        return result
                    except Exception as e:
                        # Record exception details
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        span.set_attribute("function.success", False)
                        span.set_attribute("function.error_type", type(e).__name__)
                        raise
                    finally:
                        # Record function duration
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("function.duration_ms", duration_ms)
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Create span attributes from the combined attributes
                span_attributes = {}
                if attributes:
                    span_attributes.update(attributes)
                
                # Add function arguments as span attributes (safely)
                try:
                    # Get argument names from function signature
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    
                    # Add safe string representations of arguments
                    for arg_name, arg_value in bound_args.arguments.items():
                        # Skip 'self' and 'cls' arguments
                        if arg_name in ('self', 'cls'):
                            continue
                        
                        # Add a safe string representation (limit length)
                        try:
                            str_value = str(arg_value)
                            if len(str_value) > 100:
                                str_value = str_value[:97] + "..."
                            span_attributes[f"arg.{arg_name}"] = str_value
                        except Exception:
                            span_attributes[f"arg.{arg_name}"] = "<unprintable>"
                except Exception as e:
                    logger.debug(f"Failed to capture function arguments: {e}")
                
                with tracer.start_as_current_span(func_name, kind=kind, attributes=span_attributes) as span:
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        
                        # Record success and result type
                        span.set_attribute("function.success", True)
                        span.set_attribute("function.result_type", type(result).__name__)
                        
                        return result
                    except Exception as e:
                        # Record exception details
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        span.set_attribute("function.success", False)
                        span.set_attribute("function.error_type", type(e).__name__)
                        raise
                    finally:
                        # Record function duration
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("function.duration_ms", duration_ms)
            
            return sync_wrapper
    
    return decorator


def get_current_span() -> trace.Span:
    """
    Get the current active span.
    
    Returns:
        The current span or a no-op span if none is active
    
    Example:
        ```python
        from neuroca.monitoring.tracing.middleware import get_current_span
        
        def some_function():
            span = get_current_span()
            span.add_event("processing_started")
            # Function implementation
            span.add_event("processing_completed")
        ```
    """
    return trace.get_current_span()


def create_child_span(
    name: str,
    attributes: Optional[dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
) -> trace.Span:
    """
    Create a new child span from the current span.
    
    Args:
        name: Name for the new span
        attributes: Optional attributes to add to the span
        kind: Span kind (default: INTERNAL)
    
    Returns:
        A new span that is a child of the current span
    
    Example:
        ```python
        from neuroca.monitoring.tracing.middleware import create_child_span
        
        def process_data(data):
            with create_child_span("data_processing", {"data_size": len(data)}) as span:
                # Processing logic
                span.add_event("processing_step_completed")
                # More processing
        ```
    """
    tracer = trace.get_tracer(__name__)
    return tracer.start_span(name, kind=kind, attributes=attributes or {})