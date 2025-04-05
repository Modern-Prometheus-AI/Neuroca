"""
Distributed Tracing Module for NeuroCognitive Architecture (NCA)

This module provides a comprehensive distributed tracing implementation for the NCA system,
enabling detailed monitoring and debugging of request flows across system components.
It integrates with OpenTelemetry for standardized tracing and supports multiple exporters
for flexibility in observability backends.

Features:
- Automatic instrumentation of common libraries and frameworks
- Custom span creation for NCA-specific operations
- Context propagation across asynchronous boundaries
- Configurable sampling and exporting
- Integration with the broader NCA monitoring system

Usage:
    from neuroca.monitoring.tracing import configure_tracing, get_tracer, trace

    # Initialize tracing at application startup
    configure_tracing(
        service_name="memory-service",
        environment="production",
        exporter="jaeger"
    )

    # Get a tracer for a specific component
    tracer = get_tracer("neuroca.memory.working_memory")

    # Use the tracer directly
    with tracer.start_as_current_span("process_memory_item") as span:
        span.set_attribute("item.id", item_id)
        span.set_attribute("item.type", item_type)
        # Process the memory item
        result = process_item(item)
        span.set_attribute("result.status", "success")

    # Or use the decorator
    @trace("retrieve_memory")
    def retrieve_memory(memory_id: str) -> dict:
        # This function will be automatically traced
        return memory_store.get(memory_id)
"""

import functools
import logging
import os
import sys
from contextlib import contextmanager
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Union, cast

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_OFF,
        ALWAYS_ON,
        ParentBased,
        TraceIdRatioBased,
    )
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    
    # Optional exporters - will be imported conditionally
    jaeger_exporter = None
    zipkin_exporter = None
    
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Create stub classes/functions for type checking when OpenTelemetry is not available
    class TracerProvider:
        pass
    
    class trace:
        @staticmethod
        def get_tracer(*args, **kwargs):
            return DummyTracer()
    
    class DummyTracer:
        @contextmanager
        def start_as_current_span(self, *args, **kwargs):
            yield DummySpan()
    
    class DummySpan:
        def set_attribute(self, *args, **kwargs):
            pass
        
        def record_exception(self, *args, **kwargs):
            pass
        
        def set_status(self, *args, **kwargs):
            pass

# Set up module logger
logger = logging.getLogger(__name__)

# Type variables for decorators
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

class ExporterType(str, Enum):
    """Supported trace exporters."""
    CONSOLE = "console"
    OTLP = "otlp"
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    NONE = "none"

class SamplingStrategy(str, Enum):
    """Supported sampling strategies."""
    ALWAYS_ON = "always_on"
    ALWAYS_OFF = "always_off"
    PARENT_BASED = "parent_based"
    TRACE_ID_RATIO = "trace_id_ratio"

# Global variables
_tracer_provider: Optional[TracerProvider] = None
_initialized: bool = False

def get_tracer(name: str) -> Any:
    """
    Get a tracer instance for the specified component.
    
    Args:
        name: The name of the component requesting the tracer.
              Should follow the format "neuroca.{module}.{submodule}".
    
    Returns:
        A tracer instance that can be used to create spans.
    
    Example:
        ```python
        tracer = get_tracer("neuroca.memory.episodic")
        with tracer.start_as_current_span("store_memory") as span:
            # Your code here
            pass
        ```
    """
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not available. Using dummy tracer.")
        return DummyTracer() if 'DummyTracer' in globals() else None
    
    if not _initialized:
        logger.warning(
            "Tracing not initialized. Call configure_tracing() first. "
            "Using default tracer with no exporters."
        )
        # Return the default tracer which won't export spans
        return trace.get_tracer(name)
    
    return trace.get_tracer(name)

def configure_tracing(
    service_name: str,
    environment: str = "development",
    exporter: Union[ExporterType, str] = ExporterType.CONSOLE,
    sampling_strategy: Union[SamplingStrategy, str] = SamplingStrategy.PARENT_BASED,
    sampling_rate: float = 1.0,
    otlp_endpoint: Optional[str] = None,
    jaeger_host: Optional[str] = None,
    jaeger_port: Optional[int] = None,
    zipkin_endpoint: Optional[str] = None,
    additional_attributes: Optional[dict[str, str]] = None,
    auto_instrument_libraries: bool = True,
) -> bool:
    """
    Configure the tracing system for the NCA application.
    
    Args:
        service_name: Name of the service (e.g., "memory-service", "core-processor")
        environment: Deployment environment (e.g., "development", "production")
        exporter: The type of exporter to use for traces
        sampling_strategy: The sampling strategy to use
        sampling_rate: The sampling rate (0.0 to 1.0) when using trace_id_ratio strategy
        otlp_endpoint: The endpoint for OTLP exporter (e.g., "localhost:4317")
        jaeger_host: The host for Jaeger exporter
        jaeger_port: The port for Jaeger exporter
        zipkin_endpoint: The endpoint for Zipkin exporter
        additional_attributes: Additional resource attributes to include with all spans
        auto_instrument_libraries: Whether to automatically instrument common libraries
    
    Returns:
        bool: True if tracing was successfully configured, False otherwise
    
    Example:
        ```python
        configure_tracing(
            service_name="memory-service",
            environment="production",
            exporter=ExporterType.JAEGER,
            jaeger_host="jaeger.monitoring.svc.cluster.local",
            jaeger_port=6831
        )
        ```
    """
    global _tracer_provider, _initialized
    
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning(
            "OpenTelemetry packages not installed. Tracing will not be available. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return False
    
    # Convert string enum values to enum instances if needed
    if isinstance(exporter, str):
        try:
            exporter = ExporterType(exporter.lower())
        except ValueError:
            logger.error(f"Invalid exporter type: {exporter}. Using console exporter.")
            exporter = ExporterType.CONSOLE
    
    if isinstance(sampling_strategy, str):
        try:
            sampling_strategy = SamplingStrategy(sampling_strategy.lower())
        except ValueError:
            logger.error(f"Invalid sampling strategy: {sampling_strategy}. Using parent-based strategy.")
            sampling_strategy = SamplingStrategy.PARENT_BASED
    
    # Create resource with service information
    resource_attributes = {
        "service.name": service_name,
        "service.namespace": "neuroca",
        "deployment.environment": environment,
    }
    
    # Add additional attributes if provided
    if additional_attributes:
        resource_attributes.update(additional_attributes)
    
    resource = Resource.create(resource_attributes)
    
    # Configure sampling strategy
    if sampling_strategy == SamplingStrategy.ALWAYS_ON:
        sampler = ALWAYS_ON
    elif sampling_strategy == SamplingStrategy.ALWAYS_OFF:
        sampler = ALWAYS_OFF
    elif sampling_strategy == SamplingStrategy.TRACE_ID_RATIO:
        sampler = TraceIdRatioBased(sampling_rate)
    else:  # Default to parent-based
        sampler = ParentBased(root_sampler=TraceIdRatioBased(sampling_rate))
    
    # Create tracer provider with the configured resource and sampler
    _tracer_provider = TracerProvider(resource=resource, sampler=sampler)
    
    # Configure the exporter
    try:
        if exporter == ExporterType.CONSOLE:
            _tracer_provider.add_span_processor(
                SimpleSpanProcessor(ConsoleSpanExporter())
            )
            logger.info("Configured console trace exporter")
        
        elif exporter == ExporterType.OTLP:
            if not otlp_endpoint:
                otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
            
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            _tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.info(f"Configured OTLP trace exporter with endpoint: {otlp_endpoint}")
        
        elif exporter == ExporterType.JAEGER:
            # Import Jaeger exporter only if needed
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                
                if not jaeger_host:
                    jaeger_host = os.environ.get("JAEGER_HOST", "localhost")
                
                if not jaeger_port:
                    jaeger_port = int(os.environ.get("JAEGER_PORT", "6831"))
                
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_host,
                    agent_port=jaeger_port,
                )
                
                _tracer_provider.add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )
                logger.info(f"Configured Jaeger trace exporter with host: {jaeger_host}, port: {jaeger_port}")
            
            except ImportError:
                logger.error(
                    "Jaeger exporter requested but not installed. "
                    "Install with: pip install opentelemetry-exporter-jaeger"
                )
                return False
        
        elif exporter == ExporterType.ZIPKIN:
            # Import Zipkin exporter only if needed
            try:
                from opentelemetry.exporter.zipkin.json import ZipkinExporter
                
                if not zipkin_endpoint:
                    zipkin_endpoint = os.environ.get("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans")
                
                zipkin_exporter = ZipkinExporter(
                    endpoint=zipkin_endpoint,
                )
                
                _tracer_provider.add_span_processor(
                    BatchSpanProcessor(zipkin_exporter)
                )
                logger.info(f"Configured Zipkin trace exporter with endpoint: {zipkin_endpoint}")
            
            except ImportError:
                logger.error(
                    "Zipkin exporter requested but not installed. "
                    "Install with: pip install opentelemetry-exporter-zipkin"
                )
                return False
        
        elif exporter == ExporterType.NONE:
            logger.info("No trace exporter configured (exporter=none)")
        
        else:
            logger.error(f"Unknown exporter type: {exporter}")
            return False
        
    except Exception as e:
        logger.exception(f"Failed to configure trace exporter: {e}")
        return False
    
    # Set the global tracer provider
    trace.set_tracer_provider(_tracer_provider)
    
    # Set up propagator for distributed tracing context
    trace.set_tracer_provider(_tracer_provider)
    
    # Auto-instrument libraries if requested
    if auto_instrument_libraries:
        try:
            # HTTP client libraries
            RequestsInstrumentor().instrument()
            AioHttpClientInstrumentor().instrument()
            
            # Database libraries
            AsyncPGInstrumentor().instrument()
            RedisInstrumentor().instrument()
            
            # Note: FastAPI instrumentation should be done after app creation:
            # FastAPIInstrumentor.instrument_app(app)
            
            logger.info("Auto-instrumented common libraries")
        except Exception as e:
            logger.warning(f"Failed to auto-instrument some libraries: {e}")
    
    _initialized = True
    logger.info(f"Tracing initialized for service: {service_name} in {environment} environment")
    return True

def trace(
    name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
    kind: Optional[Any] = None,
) -> Callable[[F], F]:
    """
    Decorator to trace a function.
    
    Args:
        name: The name of the span. If None, the function name will be used.
        attributes: Attributes to set on the span.
        kind: The span kind.
    
    Returns:
        A decorator function that will trace the decorated function.
    
    Example:
        ```python
        @trace("process_memory_item", {"memory.type": "episodic"})
        def process_item(item_id: str) -> dict:
            # This function will be traced
            return get_item(item_id)
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not OPENTELEMETRY_AVAILABLE or not _initialized:
                return func(*args, **kwargs)
            
            # Get the tracer for the module where the function is defined
            module_name = func.__module__
            tracer = get_tracer(module_name)
            
            # Use function name if span name not provided
            span_name = name if name is not None else func.__name__
            
            with tracer.start_as_current_span(span_name, kind=kind) as span:
                # Add attributes if provided
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as span attributes if they are simple types
                # Skip 'self' and 'cls' arguments for methods
                for i, arg in enumerate(args):
                    # Skip first argument if it might be self/cls
                    if i == 0 and module_name != "__main__" and arg.__class__.__module__ == module_name:
                        continue
                    
                    # Only add simple types as attributes
                    if isinstance(arg, (str, int, float, bool)):
                        span.set_attribute(f"arg.{i}", arg)
                
                for key, value in kwargs.items():
                    # Only add simple types as attributes
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"arg.{key}", value)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Record the exception in the span
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return cast(F, wrapper)
    
    # Handle case where decorator is used without parentheses
    if callable(name):
        func, name = name, None
        return decorator(func)
    
    return decorator

def trace_async(
    name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
    kind: Optional[Any] = None,
) -> Callable[[F], F]:
    """
    Decorator to trace an async function.
    
    Args:
        name: The name of the span. If None, the function name will be used.
        attributes: Attributes to set on the span.
        kind: The span kind.
    
    Returns:
        A decorator function that will trace the decorated async function.
    
    Example:
        ```python
        @trace_async("fetch_memory_async", {"memory.type": "working"})
        async def fetch_memory(memory_id: str) -> dict:
            # This async function will be traced
            return await memory_store.get_async(memory_id)
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not OPENTELEMETRY_AVAILABLE or not _initialized:
                return await func(*args, **kwargs)
            
            # Get the tracer for the module where the function is defined
            module_name = func.__module__
            tracer = get_tracer(module_name)
            
            # Use function name if span name not provided
            span_name = name if name is not None else func.__name__
            
            with tracer.start_as_current_span(span_name, kind=kind) as span:
                # Add attributes if provided
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as span attributes if they are simple types
                # Skip 'self' and 'cls' arguments for methods
                for i, arg in enumerate(args):
                    # Skip first argument if it might be self/cls
                    if i == 0 and module_name != "__main__" and arg.__class__.__module__ == module_name:
                        continue
                    
                    # Only add simple types as attributes
                    if isinstance(arg, (str, int, float, bool)):
                        span.set_attribute(f"arg.{i}", arg)
                
                for key, value in kwargs.items():
                    # Only add simple types as attributes
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"arg.{key}", value)
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Record the exception in the span
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return cast(F, wrapper)
    
    # Handle case where decorator is used without parentheses
    if callable(name):
        func, name = name, None
        return decorator(func)
    
    return decorator

def add_span_attributes(attributes: dict[str, Any]) -> None:
    """
    Add attributes to the current active span.
    
    Args:
        attributes: A dictionary of attributes to add to the current span.
    
    Example:
        ```python
        add_span_attributes({
            "memory.size": len(memory_items),
            "memory.processing_time_ms": processing_time
        })
        ```
    """
    if not OPENTELEMETRY_AVAILABLE or not _initialized:
        return
    
    current_span = trace.get_current_span()
    for key, value in attributes.items():
        current_span.set_attribute(key, value)

def record_exception(exception: Exception, attributes: Optional[dict[str, Any]] = None) -> None:
    """
    Record an exception in the current active span.
    
    Args:
        exception: The exception to record.
        attributes: Optional attributes to add to the exception event.
    
    Example:
        ```python
        try:
            process_memory()
        except Exception as e:
            record_exception(e, {"memory.state": "corrupted"})
            # Handle the exception
        ```
    """
    if not OPENTELEMETRY_AVAILABLE or not _initialized:
        return
    
    current_span = trace.get_current_span()
    current_span.record_exception(exception, attributes=attributes)
    current_span.set_status(Status(StatusCode.ERROR, str(exception)))

def set_span_status(status_code: Any, description: Optional[str] = None) -> None:
    """
    Set the status of the current active span.
    
    Args:
        status_code: The status code (StatusCode.OK or StatusCode.ERROR).
        description: Optional description for the status.
    
    Example:
        ```python
        from opentelemetry.trace import StatusCode
        
        # Mark span as successful
        set_span_status(StatusCode.OK)
        
        # Mark span as failed with description
        set_span_status(StatusCode.ERROR, "Failed to process memory item")
        ```
    """
    if not OPENTELEMETRY_AVAILABLE or not _initialized:
        return
    
    current_span = trace.get_current_span()
    current_span.set_status(Status(status_code, description))

@contextmanager
def start_span(
    name: str,
    attributes: Optional[dict[str, Any]] = None,
    kind: Optional[Any] = None,
    tracer_name: Optional[str] = None,
) -> Any:
    """
    Context manager to create and manage a span.
    
    Args:
        name: The name of the span.
        attributes: Optional attributes to set on the span.
        kind: Optional span kind.
        tracer_name: Optional tracer name. If not provided, the caller's module name is used.
    
    Yields:
        The created span.
    
    Example:
        ```python
        with start_span("process_memory_batch", {"batch.size": len(items)}) as span:
            results = process_items(items)
            span.set_attribute("processed.count", len(results))
        ```
    """
    if not OPENTELEMETRY_AVAILABLE or not _initialized:
        # Create a dummy span context manager when tracing is not available
        @contextmanager
        def dummy_context():
            class DummySpan:
                def set_attribute(self, *args, **kwargs):
                    pass
                def record_exception(self, *args, **kwargs):
                    pass
                def set_status(self, *args, **kwargs):
                    pass
            yield DummySpan()
        
        with dummy_context() as dummy_span:
            yield dummy_span
        return
    
    # Get the caller's module name if tracer_name is not provided
    if tracer_name is None:
        frame = sys._getframe(1)
        tracer_name = frame.f_globals.get('__name__', 'neuroca.unknown')
    
    tracer = get_tracer(tracer_name)
    
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

# Export public API
__all__ = [
    'configure_tracing',
    'get_tracer',
    'trace',
    'trace_async',
    'add_span_attributes',
    'record_exception',
    'set_span_status',
    'start_span',
    'ExporterType',
    'SamplingStrategy',
]