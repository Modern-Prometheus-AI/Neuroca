"""
Distributed Tracing Spans Module for NeuroCognitive Architecture

This module provides a comprehensive implementation for creating, managing, and
instrumenting distributed tracing spans within the NCA system. It integrates with
OpenTelemetry to provide standardized tracing capabilities that can be exported
to various backends (Jaeger, Zipkin, etc.).

The module offers:
- Span creation and management
- Context propagation
- Automatic instrumentation helpers
- Custom attribute handling
- Error tracking
- Performance metrics integration

Usage:
    from neuroca.monitoring.tracing.spans import create_span, trace_method

    # Manual span creation
    with create_span("operation_name", attributes={"key": "value"}) as span:
        # Your code here
        span.add_event("milestone_reached")
        
    # Decorator for automatic method tracing
    @trace_method
    def my_function(arg1, arg2):
        # Function will be automatically traced
        pass
"""

import functools
import inspect
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar, Union

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.context import Context, get_current
from opentelemetry.trace import Span, SpanKind, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Local imports
from neuroca.monitoring.logging.logger import get_logger

# Type definitions
T = TypeVar('T')
Attributes = dict[str, Union[str, bool, int, float, list[str]]]

# Configure module logger
logger = get_logger(__name__)

# Get the global tracer provider
tracer = trace.get_tracer(__name__)


@contextmanager
def create_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Attributes] = None,
    links: Optional[list[trace.Link]] = None,
    record_exception: bool = True,
    parent: Optional[Union[Span, Context]] = None,
) -> Span:
    """
    Create and yield a new span as a context manager.
    
    This function provides a convenient way to create spans with proper
    error handling and cleanup.
    
    Args:
        name: The name of the span
        kind: The kind of span (default: INTERNAL)
        attributes: Optional dictionary of span attributes
        links: Optional list of links to other spans
        record_exception: Whether to automatically record exceptions
        parent: Optional parent span or context
        
    Yields:
        An active OpenTelemetry span
        
    Example:
        with create_span("process_data", attributes={"data_size": "large"}) as span:
            result = process_data()
            span.add_event("data_processed", {"item_count": len(result)})
    """
    # Normalize attributes
    if attributes is None:
        attributes = {}
    
    # Create the span with the appropriate context
    with tracer.start_as_current_span(
        name=name,
        kind=kind,
        attributes=attributes,
        links=links,
        context=parent,
    ) as span:
        start_time = time.time()
        try:
            logger.debug(f"Starting span: {name}")
            yield span
            span.set_status(StatusCode.OK)
        except Exception as e:
            # Record the exception if configured to do so
            if record_exception:
                span.record_exception(e)
                span.set_status(
                    StatusCode.ERROR,
                    f"{type(e).__name__}: {str(e)}"
                )
            
            # Add detailed error information
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.stack_trace", traceback.format_exc())
            
            # Log the error
            logger.error(f"Error in span {name}: {str(e)}", exc_info=True)
            
            # Re-raise the exception
            raise
        finally:
            # Record duration as a span attribute
            duration = time.time() - start_time
            span.set_attribute("duration_seconds", duration)
            logger.debug(f"Completed span: {name} in {duration:.3f}s")


def trace_method(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Attributes] = None,
    record_args: bool = True,
    record_return_value: bool = False,
    record_exception: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to automatically trace a method or function.
    
    Args:
        name: Optional custom name for the span (defaults to function name)
        kind: The kind of span to create
        attributes: Static attributes to add to every span
        record_args: Whether to record function arguments as span attributes
        record_return_value: Whether to record the return value
        record_exception: Whether to record exceptions
        
    Returns:
        Decorated function that creates a span for each invocation
        
    Example:
        @trace_method(attributes={"component": "data_processor"})
        def process_data(data_id, options=None):
            # This function will be automatically traced
            return fetch_and_process(data_id, options)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Get the function's signature for better span naming and arg handling
        sig = inspect.signature(func)
        span_name = name or f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Prepare span attributes
            span_attributes = attributes.copy() if attributes else {}
            
            # Add function metadata
            span_attributes["function.name"] = func.__name__
            span_attributes["function.module"] = func.__module__
            
            # Record arguments if configured
            if record_args:
                # Bind the arguments to the signature parameters
                try:
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    
                    # Add safe string representations of arguments as attributes
                    for param_name, param_value in bound_args.arguments.items():
                        # Skip 'self' and 'cls' parameters for methods
                        if param_name in ('self', 'cls'):
                            continue
                            
                        # Convert the value to a safe string representation
                        try:
                            # Limit attribute value length and handle non-serializable objects
                            str_value = str(param_value)
                            if len(str_value) > 1000:
                                str_value = str_value[:997] + "..."
                            span_attributes[f"arg.{param_name}"] = str_value
                        except Exception:
                            span_attributes[f"arg.{param_name}"] = "<non-serializable>"
                except Exception as e:
                    logger.warning(f"Failed to record function arguments: {e}")
                    span_attributes["arg_recording_error"] = str(e)
            
            # Create the span and call the function
            with create_span(
                name=span_name,
                kind=kind,
                attributes=span_attributes,
                record_exception=record_exception
            ) as span:
                result = func(*args, **kwargs)
                
                # Record the return value if configured
                if record_return_value and result is not None:
                    try:
                        # Convert the result to a safe string representation
                        str_result = str(result)
                        if len(str_result) > 1000:
                            str_result = str_result[:997] + "..."
                        span.set_attribute("return_value", str_result)
                    except Exception as e:
                        logger.warning(f"Failed to record return value: {e}")
                        span.set_attribute("return_value_error", str(e))
                
                return result
                
        return wrapper
    
    return decorator


def get_current_span() -> Span:
    """
    Get the current active span.
    
    Returns:
        The current span from the context or a no-op span if none exists
        
    Example:
        span = get_current_span()
        span.add_event("checkpoint_reached")
    """
    return trace.get_current_span()


def add_span_event(name: str, attributes: Optional[Attributes] = None) -> None:
    """
    Add an event to the current active span.
    
    Args:
        name: The name of the event
        attributes: Optional attributes for the event
        
    Example:
        add_span_event("cache_miss", {"key": "user_profile"})
    """
    span = get_current_span()
    span.add_event(name, attributes)


def set_span_status(status: StatusCode, description: Optional[str] = None) -> None:
    """
    Set the status of the current span.
    
    Args:
        status: The status code (OK or ERROR)
        description: Optional description of the status
        
    Example:
        set_span_status(StatusCode.ERROR, "Failed to connect to database")
    """
    span = get_current_span()
    span.set_status(status, description)


def set_span_attribute(key: str, value: Union[str, bool, int, float, list[str]]) -> None:
    """
    Set an attribute on the current span.
    
    Args:
        key: The attribute key
        value: The attribute value
        
    Example:
        set_span_attribute("http.status_code", 200)
    """
    span = get_current_span()
    span.set_attribute(key, value)


def extract_context_from_headers(headers: dict[str, str]) -> Context:
    """
    Extract trace context from HTTP headers.
    
    Args:
        headers: Dictionary of HTTP headers
        
    Returns:
        The extracted context or the current context if none found
        
    Example:
        context = extract_context_from_headers(request.headers)
        with create_span("process_request", parent=context) as span:
            # Process the request
    """
    propagator = TraceContextTextMapPropagator()
    return propagator.extract(get_current(), headers)


def inject_context_into_headers(headers: dict[str, str]) -> dict[str, str]:
    """
    Inject the current trace context into HTTP headers.
    
    Args:
        headers: Dictionary of HTTP headers to inject context into
        
    Returns:
        The headers dictionary with added trace context
        
    Example:
        headers = {"Content-Type": "application/json"}
        headers = inject_context_into_headers(headers)
        response = requests.get("https://api.example.com", headers=headers)
    """
    propagator = TraceContextTextMapPropagator()
    propagator.inject(get_current(), headers)
    return headers


class SpanContextManager:
    """
    A reusable context manager for creating spans with consistent configuration.
    
    This class allows creating a template for spans that can be reused across
    different parts of the application with consistent configuration.
    
    Example:
        # Create a template for database spans
        db_span = SpanContextManager(
            name_prefix="database.",
            kind=SpanKind.CLIENT,
            base_attributes={"db.type": "postgresql"}
        )
        
        # Use it in different places
        with db_span.create("query", attributes={"db.statement": "SELECT * FROM users"}) as span:
            results = db_client.query("SELECT * FROM users")
    """
    
    def __init__(
        self,
        name_prefix: str = "",
        kind: SpanKind = SpanKind.INTERNAL,
        base_attributes: Optional[Attributes] = None,
        record_exception: bool = True,
    ):
        """
        Initialize a span context manager template.
        
        Args:
            name_prefix: Prefix to add to all span names
            kind: Default span kind
            base_attributes: Base attributes to include in all spans
            record_exception: Whether to record exceptions by default
        """
        self.name_prefix = name_prefix
        self.kind = kind
        self.base_attributes = base_attributes or {}
        self.record_exception = record_exception
    
    @contextmanager
    def create(
        self,
        name: str,
        kind: Optional[SpanKind] = None,
        attributes: Optional[Attributes] = None,
        links: Optional[list[trace.Link]] = None,
        record_exception: Optional[bool] = None,
        parent: Optional[Union[Span, Context]] = None,
    ) -> Span:
        """
        Create a span using this template's configuration.
        
        Args:
            name: The name of the span (will be prefixed)
            kind: Optional override for span kind
            attributes: Additional attributes to merge with base attributes
            links: Optional links to other spans
            record_exception: Optional override for exception recording
            parent: Optional parent span or context
            
        Yields:
            An active OpenTelemetry span
        """
        # Merge attributes with base attributes
        merged_attributes = self.base_attributes.copy()
        if attributes:
            merged_attributes.update(attributes)
        
        # Use template defaults unless overridden
        span_kind = kind if kind is not None else self.kind
        should_record_exception = record_exception if record_exception is not None else self.record_exception
        
        # Create the full span name with prefix
        full_name = f"{self.name_prefix}{name}" if self.name_prefix else name
        
        # Create and yield the span
        with create_span(
            name=full_name,
            kind=span_kind,
            attributes=merged_attributes,
            links=links,
            record_exception=should_record_exception,
            parent=parent,
        ) as span:
            yield span