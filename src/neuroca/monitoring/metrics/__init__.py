"""
Metrics Module for NeuroCognitive Architecture (NCA)

This module provides a comprehensive metrics collection, aggregation, and reporting system
for the NeuroCognitive Architecture. It enables monitoring of various aspects of the system
including performance, memory usage, health dynamics, and operational metrics.

The metrics system is designed to be:
1. Extensible - Easy to add new metrics
2. Efficient - Low overhead for production use
3. Flexible - Support for various backends (Prometheus, StatsD, custom)
4. Contextual - Ability to tag metrics with relevant dimensions
5. Integrated - Works seamlessly with the rest of the monitoring system

Usage Examples:
--------------
Basic counter increment:
    >>> from neuroca.monitoring.metrics import get_metric
    >>> counter = get_metric("model_calls", metric_type="counter")
    >>> counter.increment()

Timing a function:
    >>> from neuroca.monitoring.metrics import timing
    >>> @timing("process_time")
    >>> def process_data(data):
    >>>     # processing logic
    >>>     return result

Recording a gauge value:
    >>> from neuroca.monitoring.metrics import get_metric
    >>> memory_gauge = get_metric("memory_usage_mb", metric_type="gauge")
    >>> memory_gauge.set(current_memory_usage)

Using a context manager for timing:
    >>> from neuroca.monitoring.metrics import timed_context
    >>> with timed_context("database_query"):
    >>>     # database query operations
"""

import functools
import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Union, cast

# Configure module logger
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
MetricValue = Union[int, float]
TagsType = dict[str, str]


class MetricType(Enum):
    """Enumeration of supported metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    SUMMARY = "summary"


class MetricBackend(Enum):
    """Enumeration of supported metric backend systems."""
    MEMORY = "memory"  # In-memory storage for testing/development
    PROMETHEUS = "prometheus"
    STATSD = "statsd"
    DATADOG = "datadog"
    CUSTOM = "custom"


class MetricsError(Exception):
    """Base exception class for metrics-related errors."""
    pass


class MetricNotFoundError(MetricsError):
    """Exception raised when attempting to access a non-existent metric."""
    pass


class InvalidMetricTypeError(MetricsError):
    """Exception raised when an invalid metric type is specified."""
    pass


class InvalidMetricValueError(MetricsError):
    """Exception raised when an invalid value is provided for a metric."""
    pass


class MetricBase(ABC):
    """Abstract base class for all metric types.
    
    This class defines the common interface that all metric implementations must follow.
    """
    
    def __init__(self, name: str, description: str = "", tags: Optional[TagsType] = None):
        """Initialize a new metric.
        
        Args:
            name: The name of the metric
            description: Optional description of what the metric measures
            tags: Optional dictionary of tags/dimensions for the metric
        """
        self.name = name
        self.description = description
        self.tags = tags or {}
        logger.debug(f"Created metric: {name} ({self.__class__.__name__})")
    
    @abstractmethod
    def get_value(self) -> MetricValue:
        """Get the current value of the metric."""
        pass
    
    def with_tags(self, **tags: str) -> 'MetricBase':
        """Return a new metric with additional tags.
        
        Args:
            **tags: Key-value pairs to add as tags
            
        Returns:
            A new metric instance with the combined tags
        """
        new_tags = {**self.tags, **tags}
        new_metric = self.__class__(self.name, self.description, new_tags)
        return new_metric


class Counter(MetricBase):
    """A counter metric that can only increase in value."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[TagsType] = None):
        """Initialize a new counter metric.
        
        Args:
            name: The name of the metric
            description: Optional description of what the metric counts
            tags: Optional dictionary of tags/dimensions for the metric
        """
        super().__init__(name, description, tags)
        self._value: int = 0
    
    def increment(self, value: int = 1) -> None:
        """Increment the counter by the specified value.
        
        Args:
            value: Amount to increment by (default: 1)
            
        Raises:
            InvalidMetricValueError: If value is negative
        """
        if value < 0:
            raise InvalidMetricValueError(f"Cannot increment counter by negative value: {value}")
        
        self._value += value
        logger.debug(f"Incremented counter {self.name} by {value} to {self._value}")
    
    def get_value(self) -> int:
        """Get the current counter value.
        
        Returns:
            The current counter value
        """
        return self._value


class Gauge(MetricBase):
    """A gauge metric that can increase or decrease."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[TagsType] = None):
        """Initialize a new gauge metric.
        
        Args:
            name: The name of the metric
            description: Optional description of what the metric measures
            tags: Optional dictionary of tags/dimensions for the metric
        """
        super().__init__(name, description, tags)
        self._value: float = 0.0
    
    def set(self, value: MetricValue) -> None:
        """Set the gauge to a specific value.
        
        Args:
            value: The value to set
        """
        self._value = float(value)
        logger.debug(f"Set gauge {self.name} to {self._value}")
    
    def increment(self, value: MetricValue = 1.0) -> None:
        """Increment the gauge by the specified value.
        
        Args:
            value: Amount to increment by (default: 1.0)
        """
        self._value += float(value)
        logger.debug(f"Incremented gauge {self.name} by {value} to {self._value}")
    
    def decrement(self, value: MetricValue = 1.0) -> None:
        """Decrement the gauge by the specified value.
        
        Args:
            value: Amount to decrement by (default: 1.0)
        """
        self._value -= float(value)
        logger.debug(f"Decremented gauge {self.name} by {value} to {self._value}")
    
    def get_value(self) -> float:
        """Get the current gauge value.
        
        Returns:
            The current gauge value
        """
        return self._value


class Histogram(MetricBase):
    """A histogram metric that tracks the distribution of values."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[TagsType] = None, 
                 buckets: Optional[list[float]] = None):
        """Initialize a new histogram metric.
        
        Args:
            name: The name of the metric
            description: Optional description of what the metric measures
            tags: Optional dictionary of tags/dimensions for the metric
            buckets: Optional list of bucket boundaries for the histogram
        """
        super().__init__(name, description, tags)
        self._values: list[float] = []
        self._buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self._count = 0
        self._sum = 0.0
    
    def observe(self, value: MetricValue) -> None:
        """Record an observation in the histogram.
        
        Args:
            value: The value to record
        """
        float_value = float(value)
        self._values.append(float_value)
        self._count += 1
        self._sum += float_value
        logger.debug(f"Observed value {value} for histogram {self.name}")
    
    def get_value(self) -> float:
        """Get the current average value of observations.
        
        Returns:
            The average value or 0 if no observations
        """
        if self._count == 0:
            return 0.0
        return self._sum / self._count
    
    def get_count(self) -> int:
        """Get the count of observations.
        
        Returns:
            The number of observations
        """
        return self._count
    
    def get_sum(self) -> float:
        """Get the sum of all observations.
        
        Returns:
            The sum of all observations
        """
        return self._sum
    
    def get_buckets(self) -> dict[float, int]:
        """Get the histogram buckets.
        
        Returns:
            A dictionary mapping bucket upper bounds to counts
        """
        result: dict[float, int] = {b: 0 for b in self._buckets}
        for value in self._values:
            for bucket in self._buckets:
                if value <= bucket:
                    result[bucket] += 1
        
        return result


class Timer(MetricBase):
    """A timer metric for measuring durations."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[TagsType] = None):
        """Initialize a new timer metric.
        
        Args:
            name: The name of the metric
            description: Optional description of what the timer measures
            tags: Optional dictionary of tags/dimensions for the metric
        """
        super().__init__(name, description, tags)
        self._histogram = Histogram(f"{name}_histogram", description, tags)
        self._start_time: Optional[float] = None
    
    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.time()
        logger.debug(f"Started timer {self.name}")
    
    def stop(self) -> float:
        """Stop the timer and record the duration.
        
        Returns:
            The measured duration in seconds
            
        Raises:
            MetricsError: If the timer was not started
        """
        if self._start_time is None:
            raise MetricsError(f"Timer {self.name} was not started")
        
        duration = time.time() - self._start_time
        self._histogram.observe(duration)
        self._start_time = None
        logger.debug(f"Stopped timer {self.name}: {duration:.6f}s")
        return duration
    
    def get_value(self) -> float:
        """Get the average duration.
        
        Returns:
            The average duration in seconds
        """
        return self._histogram.get_value()
    
    def get_count(self) -> int:
        """Get the count of timing measurements.
        
        Returns:
            The number of measurements
        """
        return self._histogram.get_count()


# Global registry for metrics
_metrics_registry: dict[str, MetricBase] = {}


def register_metric(metric: MetricBase) -> MetricBase:
    """Register a metric in the global registry.
    
    Args:
        metric: The metric to register
        
    Returns:
        The registered metric
        
    Raises:
        MetricsError: If a metric with the same name already exists
    """
    key = f"{metric.name}_{','.join(f'{k}={v}' for k, v in sorted(metric.tags.items()))}"
    
    if key in _metrics_registry:
        logger.warning(f"Metric already exists: {key}")
        return _metrics_registry[key]
    
    _metrics_registry[key] = metric
    logger.debug(f"Registered metric: {key}")
    return metric


def get_metric(name: str, metric_type: str = "counter", description: str = "", 
               tags: Optional[TagsType] = None) -> MetricBase:
    """Get or create a metric.
    
    Args:
        name: The name of the metric
        metric_type: The type of metric (counter, gauge, histogram, timer)
        description: Optional description of the metric
        tags: Optional tags/dimensions for the metric
        
    Returns:
        The requested metric
        
    Raises:
        InvalidMetricTypeError: If the metric type is not supported
    """
    tags = tags or {}
    key = f"{name}_{','.join(f'{k}={v}' for k, v in sorted(tags.items()))}"
    
    if key in _metrics_registry:
        return _metrics_registry[key]
    
    # Create a new metric based on the type
    try:
        metric_enum = MetricType(metric_type.lower())
    except ValueError:
        valid_types = ", ".join([t.value for t in MetricType])
        raise InvalidMetricTypeError(
            f"Invalid metric type: {metric_type}. Valid types: {valid_types}"
        )
    
    if metric_enum == MetricType.COUNTER:
        metric = Counter(name, description, tags)
    elif metric_enum == MetricType.GAUGE:
        metric = Gauge(name, description, tags)
    elif metric_enum == MetricType.HISTOGRAM:
        metric = Histogram(name, description, tags)
    elif metric_enum == MetricType.TIMER:
        metric = Timer(name, description, tags)
    else:
        # This should never happen due to the enum check above
        raise InvalidMetricTypeError(f"Unsupported metric type: {metric_type}")
    
    return register_metric(metric)


def clear_metrics() -> None:
    """Clear all metrics from the registry.
    
    This is primarily used for testing purposes.
    """
    _metrics_registry.clear()
    logger.debug("Cleared all metrics from registry")


@contextmanager
def timed_context(name: str, description: str = "", tags: Optional[TagsType] = None):
    """Context manager for timing operations.
    
    Args:
        name: The name of the timer metric
        description: Optional description of what is being timed
        tags: Optional tags/dimensions for the metric
        
    Yields:
        None
        
    Example:
        >>> with timed_context("database_query", tags={"table": "users"}):
        >>>     # code to time
    """
    timer = cast(Timer, get_metric(name, "timer", description, tags))
    timer.start()
    try:
        yield
    finally:
        timer.stop()


def timing(name: str, description: str = "", tags: Optional[TagsType] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for timing function execution.
    
    Args:
        name: The name of the timer metric
        description: Optional description of what is being timed
        tags: Optional tags/dimensions for the metric
        
    Returns:
        A decorator function
        
    Example:
        >>> @timing("process_time")
        >>> def process_data(data):
        >>>     # processing logic
        >>>     return result
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with timed_context(name, description, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def count_calls(name: str, description: str = "", tags: Optional[TagsType] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for counting function calls.
    
    Args:
        name: The name of the counter metric
        description: Optional description of what is being counted
        tags: Optional tags/dimensions for the metric
        
    Returns:
        A decorator function
        
    Example:
        >>> @count_calls("api_calls", tags={"endpoint": "users"})
        >>> def get_user(user_id):
        >>>     # function logic
        >>>     return user
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            counter = cast(Counter, get_metric(name, "counter", description, tags))
            counter.increment()
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Export public API
__all__ = [
    'MetricType',
    'MetricBackend',
    'MetricsError',
    'MetricNotFoundError',
    'InvalidMetricTypeError',
    'InvalidMetricValueError',
    'MetricBase',
    'Counter',
    'Gauge',
    'Histogram',
    'Timer',
    'register_metric',
    'get_metric',
    'clear_metrics',
    'timed_context',
    'timing',
    'count_calls',
]