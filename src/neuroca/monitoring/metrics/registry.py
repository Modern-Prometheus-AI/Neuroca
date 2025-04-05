"""
Metrics Registry for the NeuroCognitive Architecture (NCA) system.

This module provides a centralized registry for all metrics in the NCA system.
It allows for registration, retrieval, and management of metrics across the entire
application. The registry supports different metric types (counters, gauges, histograms)
and provides functionality for tagging, grouping, and querying metrics.

Usage:
    # Get the global metrics registry
    registry = MetricsRegistry.get_instance()
    
    # Register a new counter metric
    counter = registry.create_counter("memory_access_count", 
                                     "Count of memory access operations",
                                     tags={"memory_tier": "working"})
    
    # Increment the counter
    counter.increment()
    
    # Register a gauge metric
    gauge = registry.create_gauge("memory_utilization", 
                                 "Current memory utilization percentage",
                                 tags={"memory_tier": "episodic"})
    
    # Set the gauge value
    gauge.set(75.5)
    
    # Get all metrics for a specific component
    memory_metrics = registry.get_metrics_by_tags({"component": "memory"})
"""

import json
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Optional, Union

# Configure logger
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Enumeration of supported metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    METER = "meter"


class MetricValidationError(Exception):
    """Exception raised for metric validation errors."""
    pass


class MetricRegistrationError(Exception):
    """Exception raised for metric registration errors."""
    pass


class MetricNotFoundError(Exception):
    """Exception raised when a requested metric is not found."""
    pass


class Metric(ABC):
    """
    Abstract base class for all metrics.
    
    All specific metric types (Counter, Gauge, etc.) should inherit from this class
    and implement its abstract methods.
    """
    
    def __init__(self, name: str, description: str, tags: Optional[dict[str, str]] = None):
        """
        Initialize a new metric.
        
        Args:
            name: The name of the metric
            description: A human-readable description of what the metric represents
            tags: Optional dictionary of tags to associate with this metric
        
        Raises:
            MetricValidationError: If the name or description is invalid
        """
        self._validate_name(name)
        self._validate_description(description)
        self._validate_tags(tags)
        
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.created_at = time.time()
        self.last_updated_at = self.created_at
        self.id = str(uuid.uuid4())
    
    @staticmethod
    def _validate_name(name: str) -> None:
        """
        Validate the metric name.
        
        Args:
            name: The metric name to validate
            
        Raises:
            MetricValidationError: If the name is invalid
        """
        if not name:
            raise MetricValidationError("Metric name cannot be empty")
        
        if not isinstance(name, str):
            raise MetricValidationError(f"Metric name must be a string, got {type(name)}")
        
        if len(name) > 255:
            raise MetricValidationError(f"Metric name too long (max 255 chars): {name}")
        
        # Check for valid characters (alphanumeric, underscore, dot)
        if not all(c.isalnum() or c in ['_', '.', '-'] for c in name):
            raise MetricValidationError(
                f"Metric name contains invalid characters (use alphanumeric, underscore, dot, dash): {name}"
            )
    
    @staticmethod
    def _validate_description(description: str) -> None:
        """
        Validate the metric description.
        
        Args:
            description: The metric description to validate
            
        Raises:
            MetricValidationError: If the description is invalid
        """
        if not description:
            raise MetricValidationError("Metric description cannot be empty")
        
        if not isinstance(description, str):
            raise MetricValidationError(f"Metric description must be a string, got {type(description)}")
        
        if len(description) > 1000:
            raise MetricValidationError("Metric description too long (max 1000 chars)")
    
    @staticmethod
    def _validate_tags(tags: Optional[dict[str, str]]) -> None:
        """
        Validate the metric tags.
        
        Args:
            tags: The tags to validate
            
        Raises:
            MetricValidationError: If any tag is invalid
        """
        if tags is None:
            return
        
        if not isinstance(tags, dict):
            raise MetricValidationError(f"Tags must be a dictionary, got {type(tags)}")
        
        for key, value in tags.items():
            if not isinstance(key, str) or not key:
                raise MetricValidationError(f"Tag key must be a non-empty string: {key}")
            
            if not isinstance(value, str):
                raise MetricValidationError(f"Tag value must be a string: {value}")
            
            if len(key) > 64:
                raise MetricValidationError(f"Tag key too long (max 64 chars): {key}")
            
            if len(value) > 255:
                raise MetricValidationError(f"Tag value too long (max 255 chars): {value}")
    
    def update_last_updated(self) -> None:
        """Update the last updated timestamp."""
        self.last_updated_at = time.time()
    
    @abstractmethod
    def get_type(self) -> MetricType:
        """
        Get the type of this metric.
        
        Returns:
            The metric type
        """
        pass
    
    @abstractmethod
    def get_value(self) -> Any:
        """
        Get the current value of this metric.
        
        Returns:
            The current metric value
        """
        pass
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the metric to a dictionary representation.
        
        Returns:
            Dictionary representation of the metric
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.get_type().value,
            "value": self.get_value(),
            "tags": self.tags,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at
        }
    
    def __str__(self) -> str:
        """String representation of the metric."""
        return f"{self.name} ({self.get_type().value}): {self.get_value()}"


class Counter(Metric):
    """
    A metric that represents a cumulative counter that can only increase.
    
    Counters are typically used for counting events or operations.
    """
    
    def __init__(self, name: str, description: str, tags: Optional[dict[str, str]] = None):
        """
        Initialize a new counter metric.
        
        Args:
            name: The name of the counter
            description: A human-readable description of what the counter represents
            tags: Optional dictionary of tags to associate with this counter
        """
        super().__init__(name, description, tags)
        self._value = 0
    
    def get_type(self) -> MetricType:
        """Get the metric type."""
        return MetricType.COUNTER
    
    def get_value(self) -> int:
        """Get the current counter value."""
        return self._value
    
    def increment(self, amount: int = 1) -> None:
        """
        Increment the counter by the specified amount.
        
        Args:
            amount: The amount to increment by (default: 1)
            
        Raises:
            ValueError: If the amount is not a positive integer
        """
        if not isinstance(amount, int):
            raise ValueError(f"Increment amount must be an integer, got {type(amount)}")
        
        if amount <= 0:
            raise ValueError(f"Increment amount must be positive, got {amount}")
        
        self._value += amount
        self.update_last_updated()
        logger.debug(f"Counter '{self.name}' incremented by {amount} to {self._value}")
    
    def reset(self) -> None:
        """Reset the counter to zero."""
        self._value = 0
        self.update_last_updated()
        logger.debug(f"Counter '{self.name}' reset to 0")


class Gauge(Metric):
    """
    A metric that represents a single numerical value that can arbitrarily go up and down.
    
    Gauges are typically used for measured values like temperatures or current memory usage.
    """
    
    def __init__(self, name: str, description: str, tags: Optional[dict[str, str]] = None):
        """
        Initialize a new gauge metric.
        
        Args:
            name: The name of the gauge
            description: A human-readable description of what the gauge represents
            tags: Optional dictionary of tags to associate with this gauge
        """
        super().__init__(name, description, tags)
        self._value = 0.0
    
    def get_type(self) -> MetricType:
        """Get the metric type."""
        return MetricType.GAUGE
    
    def get_value(self) -> float:
        """Get the current gauge value."""
        return self._value
    
    def set(self, value: Union[int, float]) -> None:
        """
        Set the gauge to a specific value.
        
        Args:
            value: The new value for the gauge
            
        Raises:
            ValueError: If the value is not a number
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"Gauge value must be a number, got {type(value)}")
        
        self._value = float(value)
        self.update_last_updated()
        logger.debug(f"Gauge '{self.name}' set to {self._value}")
    
    def increment(self, amount: Union[int, float] = 1.0) -> None:
        """
        Increment the gauge by the specified amount.
        
        Args:
            amount: The amount to increment by (default: 1.0)
            
        Raises:
            ValueError: If the amount is not a number
        """
        if not isinstance(amount, (int, float)):
            raise ValueError(f"Increment amount must be a number, got {type(amount)}")
        
        self._value += float(amount)
        self.update_last_updated()
        logger.debug(f"Gauge '{self.name}' incremented by {amount} to {self._value}")
    
    def decrement(self, amount: Union[int, float] = 1.0) -> None:
        """
        Decrement the gauge by the specified amount.
        
        Args:
            amount: The amount to decrement by (default: 1.0)
            
        Raises:
            ValueError: If the amount is not a number
        """
        if not isinstance(amount, (int, float)):
            raise ValueError(f"Decrement amount must be a number, got {type(amount)}")
        
        self._value -= float(amount)
        self.update_last_updated()
        logger.debug(f"Gauge '{self.name}' decremented by {amount} to {self._value}")


class Histogram(Metric):
    """
    A metric that samples observations and counts them in configurable buckets.
    
    Histograms are typically used for measuring the distribution of values,
    such as request durations or response sizes.
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        buckets: Optional[list[float]] = None,
        tags: Optional[dict[str, str]] = None
    ):
        """
        Initialize a new histogram metric.
        
        Args:
            name: The name of the histogram
            description: A human-readable description of what the histogram represents
            buckets: Optional list of bucket boundaries (default: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10])
            tags: Optional dictionary of tags to associate with this histogram
            
        Raises:
            MetricValidationError: If the buckets are invalid
        """
        super().__init__(name, description, tags)
        
        # Default buckets if none provided
        if buckets is None:
            buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        
        self._validate_buckets(buckets)
        self._buckets = sorted(buckets)
        
        # Initialize bucket counters
        self._bucket_counts = {bucket: 0 for bucket in self._buckets}
        self._bucket_counts[float('inf')] = 0  # Add infinity bucket
        
        # Statistics
        self._count = 0
        self._sum = 0.0
        self._min = float('inf')
        self._max = float('-inf')
    
    @staticmethod
    def _validate_buckets(buckets: list[float]) -> None:
        """
        Validate histogram buckets.
        
        Args:
            buckets: The bucket boundaries to validate
            
        Raises:
            MetricValidationError: If the buckets are invalid
        """
        if not buckets:
            raise MetricValidationError("Histogram buckets cannot be empty")
        
        if not isinstance(buckets, list):
            raise MetricValidationError(f"Buckets must be a list, got {type(buckets)}")
        
        if len(buckets) > 100:
            raise MetricValidationError(f"Too many buckets (max 100): {len(buckets)}")
        
        for bucket in buckets:
            if not isinstance(bucket, (int, float)):
                raise MetricValidationError(f"Bucket boundary must be a number, got {type(bucket)}")
            
            if bucket <= 0:
                raise MetricValidationError(f"Bucket boundary must be positive, got {bucket}")
    
    def get_type(self) -> MetricType:
        """Get the metric type."""
        return MetricType.HISTOGRAM
    
    def get_value(self) -> dict[str, Any]:
        """
        Get the current histogram value.
        
        Returns:
            Dictionary containing histogram statistics and bucket counts
        """
        return {
            "count": self._count,
            "sum": self._sum,
            "min": self._min if self._count > 0 else 0,
            "max": self._max if self._count > 0 else 0,
            "avg": (self._sum / self._count) if self._count > 0 else 0,
            "buckets": {str(bucket): count for bucket, count in self._bucket_counts.items()}
        }
    
    def observe(self, value: Union[int, float]) -> None:
        """
        Record an observation in the histogram.
        
        Args:
            value: The value to record
            
        Raises:
            ValueError: If the value is not a positive number
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"Observation value must be a number, got {type(value)}")
        
        if value < 0:
            raise ValueError(f"Observation value must be non-negative, got {value}")
        
        # Update statistics
        self._count += 1
        self._sum += value
        self._min = min(self._min, value)
        self._max = max(self._max, value)
        
        # Update bucket counts
        for bucket in self._buckets:
            if value <= bucket:
                self._bucket_counts[bucket] += 1
                break
        else:
            # If we get here, the value is larger than all defined buckets
            self._bucket_counts[float('inf')] += 1
        
        self.update_last_updated()
        logger.debug(f"Histogram '{self.name}' observed value {value}")
    
    def reset(self) -> None:
        """Reset the histogram to its initial state."""
        self._count = 0
        self._sum = 0.0
        self._min = float('inf')
        self._max = float('-inf')
        
        for bucket in self._bucket_counts:
            self._bucket_counts[bucket] = 0
        
        self.update_last_updated()
        logger.debug(f"Histogram '{self.name}' reset")


class Timer(Metric):
    """
    A metric that measures the duration of events.
    
    Timers are typically used for measuring the time taken by operations.
    """
    
    def __init__(self, name: str, description: str, tags: Optional[dict[str, str]] = None):
        """
        Initialize a new timer metric.
        
        Args:
            name: The name of the timer
            description: A human-readable description of what the timer represents
            tags: Optional dictionary of tags to associate with this timer
        """
        super().__init__(name, description, tags)
        self._histogram = Histogram(
            f"{name}_histogram",
            f"Histogram for {name} timer",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60],
            tags=tags
        )
        self._active_timers = {}  # Dictionary to store active timers
    
    def get_type(self) -> MetricType:
        """Get the metric type."""
        return MetricType.TIMER
    
    def get_value(self) -> dict[str, Any]:
        """
        Get the current timer value.
        
        Returns:
            Dictionary containing timer statistics
        """
        return self._histogram.get_value()
    
    def start(self) -> str:
        """
        Start a new timer.
        
        Returns:
            A timer ID that can be used to stop the timer
        """
        timer_id = str(uuid.uuid4())
        self._active_timers[timer_id] = time.time()
        logger.debug(f"Timer '{self.name}' started with ID {timer_id}")
        return timer_id
    
    def stop(self, timer_id: str) -> float:
        """
        Stop a timer and record its duration.
        
        Args:
            timer_id: The ID of the timer to stop
            
        Returns:
            The duration in seconds
            
        Raises:
            ValueError: If the timer ID is not found
        """
        if timer_id not in self._active_timers:
            raise ValueError(f"Timer ID not found: {timer_id}")
        
        start_time = self._active_timers.pop(timer_id)
        duration = time.time() - start_time
        
        self._histogram.observe(duration)
        logger.debug(f"Timer '{self.name}' stopped with ID {timer_id}, duration: {duration:.6f}s")
        
        return duration
    
    def time(self, func: Callable) -> Callable:
        """
        Decorator to time a function.
        
        Args:
            func: The function to time
            
        Returns:
            Wrapped function that times execution
        """
        def wrapper(*args, **kwargs):
            timer_id = self.start()
            try:
                return func(*args, **kwargs)
            finally:
                self.stop(timer_id)
        
        return wrapper
    
    def reset(self) -> None:
        """Reset the timer to its initial state."""
        self._histogram.reset()
        self._active_timers.clear()
        self.update_last_updated()
        logger.debug(f"Timer '{self.name}' reset")


class MetricsRegistry:
    """
    Central registry for all metrics in the NCA system.
    
    This class implements the Singleton pattern to ensure there's only one
    registry instance throughout the application.
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """Create a new singleton instance if one doesn't exist."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the metrics registry."""
        with self._lock:
            if self._initialized:
                return
            
            self._metrics: dict[str, Metric] = {}
            self._metrics_by_name: dict[str, Metric] = {}
            self._metrics_by_type: dict[MetricType, set[str]] = {
                metric_type: set() for metric_type in MetricType
            }
            self._metrics_by_tag: dict[str, dict[str, set[str]]] = {}
            self._initialized = True
            logger.info("Metrics registry initialized")
    
    @classmethod
    def get_instance(cls) -> 'MetricsRegistry':
        """
        Get the singleton instance of the metrics registry.
        
        Returns:
            The metrics registry instance
        """
        return cls()
    
    def register_metric(self, metric: Metric) -> None:
        """
        Register a metric with the registry.
        
        Args:
            metric: The metric to register
            
        Raises:
            MetricRegistrationError: If a metric with the same name already exists
        """
        with self._lock:
            if metric.name in self._metrics_by_name:
                raise MetricRegistrationError(f"Metric with name '{metric.name}' already exists")
            
            # Store the metric
            self._metrics[metric.id] = metric
            self._metrics_by_name[metric.name] = metric
            self._metrics_by_type[metric.get_type()].add(metric.id)
            
            # Index by tags
            for tag_key, tag_value in metric.tags.items():
                if tag_key not in self._metrics_by_tag:
                    self._metrics_by_tag[tag_key] = {}
                
                if tag_value not in self._metrics_by_tag[tag_key]:
                    self._metrics_by_tag[tag_key][tag_value] = set()
                
                self._metrics_by_tag[tag_key][tag_value].add(metric.id)
            
            logger.info(f"Registered metric: {metric.name} ({metric.get_type().value})")
    
    def unregister_metric(self, metric_id: str) -> None:
        """
        Unregister a metric from the registry.
        
        Args:
            metric_id: The ID of the metric to unregister
            
        Raises:
            MetricNotFoundError: If the metric is not found
        """
        with self._lock:
            if metric_id not in self._metrics:
                raise MetricNotFoundError(f"Metric with ID '{metric_id}' not found")
            
            metric = self._metrics[metric_id]
            
            # Remove from main dictionaries
            del self._metrics[metric_id]
            del self._metrics_by_name[metric.name]
            self._metrics_by_type[metric.get_type()].remove(metric_id)
            
            # Remove from tag indices
            for tag_key, tag_value in metric.tags.items():
                if tag_key in self._metrics_by_tag and tag_value in self._metrics_by_tag[tag_key]:
                    self._metrics_by_tag[tag_key][tag_value].remove(metric_id)
                    
                    # Clean up empty sets
                    if not self._metrics_by_tag[tag_key][tag_value]:
                        del self._metrics_by_tag[tag_key][tag_value]
                    
                    if not self._metrics_by_tag[tag_key]:
                        del self._metrics_by_tag[tag_key]
            
            logger.info(f"Unregistered metric: {metric.name} ({metric.get_type().value})")
    
    def get_metric(self, metric_id: str) -> Metric:
        """
        Get a metric by its ID.
        
        Args:
            metric_id: The ID of the metric to retrieve
            
        Returns:
            The requested metric
            
        Raises:
            MetricNotFoundError: If the metric is not found
        """
        with self._lock:
            if metric_id not in self._metrics:
                raise MetricNotFoundError(f"Metric with ID '{metric_id}' not found")
            
            return self._metrics[metric_id]
    
    def get_metric_by_name(self, name: str) -> Metric:
        """
        Get a metric by its name.
        
        Args:
            name: The name of the metric to retrieve
            
        Returns:
            The requested metric
            
        Raises:
            MetricNotFoundError: If the metric is not found
        """
        with self._lock:
            if name not in self._metrics_by_name:
                raise MetricNotFoundError(f"Metric with name '{name}' not found")
            
            return self._metrics_by_name[name]
    
    def get_metrics_by_type(self, metric_type: MetricType) -> list[Metric]:
        """
        Get all metrics of a specific type.
        
        Args:
            metric_type: The type of metrics to retrieve
            
        Returns:
            List of metrics of the specified type
        """
        with self._lock:
            return [self._metrics[metric_id] for metric_id in self._metrics_by_type[metric_type]]
    
    def get_metrics_by_tag(self, tag_key: str, tag_value: str) -> list[Metric]:
        """
        Get all metrics with a specific tag key and value.
        
        Args:
            tag_key: The tag key to filter by
            tag_value: The tag value to filter by
            
        Returns:
            List of metrics with the specified tag
        """
        with self._lock:
            if tag_key not in self._metrics_by_tag or tag_value not in self._metrics_by_tag[tag_key]:
                return []
            
            return [self._metrics[metric_id] for metric_id in self._metrics_by_tag[tag_key][tag_value]]
    
    def get_metrics_by_tags(self, tags: dict[str, str]) -> list[Metric]:
        """
        Get all metrics that match all the specified tags.
        
        Args:
            tags: Dictionary of tag keys and values to filter by
            
        Returns:
            List of metrics that match all the specified tags
        """
        if not tags:
            return list(self._metrics.values())
        
        with self._lock:
            # Start with all metric IDs
            result_ids = set(self._metrics.keys())
            
            # Filter by each tag
            for tag_key, tag_value in tags.items():
                if tag_key not in self._metrics_by_tag or tag_value not in self._metrics_by_tag[tag_key]:
                    return []  # No metrics match this tag
                
                # Intersect with metrics that have this tag
                result_ids &= self._metrics_by_tag[tag_key][tag_value]
            
            return [self._metrics[metric_id] for metric_id in result_ids]
    
    def get_all_metrics(self) -> list[Metric]:
        """
        Get all registered metrics.
        
        Returns:
            List of all metrics
        """
        with self._lock:
            return list(self._metrics.values())
    
    def create_counter(self, name: str, description: str, tags: Optional[dict[str, str]] = None) -> Counter:
        """
        Create and register a new counter metric.
        
        Args:
            name: The name of the counter
            description: A human-readable description of what the counter represents
            tags: Optional dictionary of tags to associate with this counter
            
        Returns:
            The created counter
            
        Raises:
            MetricRegistrationError: If a metric with the same name already exists
        """
        counter = Counter(name, description, tags)
        self.register_metric(counter)
        return counter
    
    def create_gauge(self, name: str, description: str, tags: Optional[dict[str, str]] = None) -> Gauge:
        """
        Create and register a new gauge metric.
        
        Args:
            name: The name of the gauge
            description: A human-readable description of what the gauge represents
            tags: Optional dictionary of tags to associate with this gauge
            
        Returns:
            The created gauge
            
        Raises:
            MetricRegistrationError: If a metric with the same name already exists
        """
        gauge = Gauge(name, description, tags)
        self.register_metric(gauge)
        return gauge
    
    def create_histogram(
        self, 
        name: str, 
        description: str, 
        buckets: Optional[list[float]] = None,
        tags: Optional[dict[str, str]] = None
    ) -> Histogram:
        """
        Create and register a new histogram metric.
        
        Args:
            name: The name of the histogram
            description: A human-readable description of what the histogram represents
            buckets: Optional list of bucket boundaries
            tags: Optional dictionary of tags to associate with this histogram
            
        Returns:
            The created histogram
            
        Raises:
            MetricRegistrationError: If a metric with the same name already exists
        """
        histogram = Histogram(name, description, buckets, tags)
        self.register_metric(histogram)
        return histogram
    
    def create_timer(self, name: str, description: str, tags: Optional[dict[str, str]] = None) -> Timer:
        """
        Create and register a new timer metric.
        
        Args:
            name: The name of the timer
            description: A human-readable description of what the timer represents
            tags: Optional dictionary of tags to associate with this timer
            
        Returns:
            The created timer
            
        Raises:
            MetricRegistrationError: If a metric with the same name already exists
        """
        timer = Timer(name, description, tags)
        self.register_metric(timer)
        return timer
    
    def export_metrics(self, format_type: str = "json") -> str:
        """
        Export all metrics in the specified format.
        
        Args:
            format_type: The format to export metrics in (currently only 'json' is supported)
            
        Returns:
            String representation of all metrics in the specified format
            
        Raises:
            ValueError: If the format type is not supported
        """
        if format_type.lower() != "json":
            raise ValueError(f"Unsupported export format: {format_type}")
        
        with self._lock:
            metrics_data = [metric.to_dict() for metric in self._metrics.values()]
            return json.dumps(metrics_data, indent=2)
    
    def reset_all_metrics(self) -> None:
        """Reset all metrics to their initial state."""
        with self._lock:
            for metric in self._metrics.values():
                if hasattr(metric, 'reset') and callable(metric.reset):
                    metric.reset()
            
            logger.info("All metrics have been reset")
    
    def clear_registry(self) -> None:
        """Clear all metrics from the registry."""
        with self._lock:
            self._metrics.clear()
            self._metrics_by_name.clear()
            for metric_type in self._metrics_by_type:
                self._metrics_by_type[metric_type].clear()
            self._metrics_by_tag.clear()
            
            logger.info("Metrics registry cleared")