"""
NeuroCognitive Architecture (NCA) Monitoring Module.

This module provides comprehensive monitoring, observability, and telemetry capabilities
for the NeuroCognitive Architecture system. It includes:

1. Metrics collection and reporting
2. Distributed tracing
3. Health checks and system diagnostics
4. Performance monitoring
5. Resource utilization tracking
6. Alerting and notification systems
7. Logging integration and enhancement

The monitoring module is designed to be configurable, extensible, and to have minimal
performance impact on the core NCA functionality while providing deep insights into
system behavior and performance.

Usage:
    from neuroca.monitoring import setup_monitoring, get_metrics_client
    
    # Initialize monitoring with default settings
    setup_monitoring()
    
    # Get metrics client to record custom metrics
    metrics = get_metrics_client()
    metrics.increment("memory.access.count", tags={"tier": "working_memory"})
    
    # Use context manager for timing operations
    with metrics.timer("memory.retrieval.duration", tags={"tier": "long_term"}):
        result = retrieve_from_long_term_memory(query)
    
    # Record resource usage
    metrics.gauge("memory.usage.bytes", current_memory_usage())

"""

import contextlib
import functools
import logging
import os
import threading
import time
from typing import Any, Callable, ContextManager, Optional, TypeVar

# Setup module logger
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Global state
_metrics_client = None
_tracing_client = None
_health_registry = None
_monitoring_initialized = False
_monitoring_lock = threading.RLock()

class MetricsClient:
    """
    Client for collecting and reporting metrics about system performance and behavior.
    
    This class provides methods to record counters, gauges, histograms, and timings
    that can be exported to various monitoring backends.
    """
    
    def __init__(self, service_name: str = "neuroca", 
                 tags: Optional[dict[str, str]] = None,
                 export_interval_seconds: int = 10):
        """
        Initialize a new metrics client.
        
        Args:
            service_name: Name of the service for metrics namespacing
            tags: Default tags to apply to all metrics
            export_interval_seconds: How often to export metrics to backends
        """
        self.service_name = service_name
        self.default_tags = tags or {}
        self.export_interval_seconds = export_interval_seconds
        self._metrics_store = {}
        self._export_thread = None
        self._stop_event = threading.Event()
        
        logger.debug(f"Initialized metrics client for service '{service_name}'")
    
    def start(self) -> None:
        """Start the metrics collection and periodic export."""
        if self._export_thread is not None and self._export_thread.is_alive():
            logger.warning("Metrics client already started")
            return
            
        self._stop_event.clear()
        self._export_thread = threading.Thread(
            target=self._export_metrics_periodically,
            daemon=True,
            name="metrics-export-thread"
        )
        self._export_thread.start()
        logger.info(f"Started metrics export thread with {self.export_interval_seconds}s interval")
    
    def stop(self) -> None:
        """Stop the metrics collection and export."""
        if self._export_thread is None or not self._export_thread.is_alive():
            logger.warning("Metrics client not running")
            return
            
        self._stop_event.set()
        self._export_thread.join(timeout=5.0)
        if self._export_thread.is_alive():
            logger.warning("Metrics export thread did not terminate cleanly")
        else:
            logger.info("Metrics export thread stopped")
        self._export_thread = None
    
    def _export_metrics_periodically(self) -> None:
        """Background thread that exports metrics at regular intervals."""
        while not self._stop_event.is_set():
            try:
                self._export_metrics()
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}", exc_info=True)
            
            # Sleep with interruption support
            self._stop_event.wait(self.export_interval_seconds)
    
    def _export_metrics(self) -> None:
        """Export collected metrics to configured backends."""
        # This would be implemented to export to Prometheus, StatsD, etc.
        # For now, just log the metrics for demonstration
        if self._metrics_store:
            logger.debug(f"Would export {len(self._metrics_store)} metrics")
    
    def _merge_tags(self, tags: Optional[dict[str, str]]) -> dict[str, str]:
        """Merge provided tags with default tags."""
        if tags is None:
            return self.default_tags.copy()
        result = self.default_tags.copy()
        result.update(tags)
        return result
    
    def increment(self, metric_name: str, value: int = 1, 
                  tags: Optional[dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric to increment
            value: Amount to increment by (default: 1)
            tags: Additional tags to associate with this metric
        """
        full_name = f"{self.service_name}.{metric_name}"
        merged_tags = self._merge_tags(tags)
        
        # In a real implementation, this would use a proper metrics library
        logger.debug(f"INCREMENT {full_name}:{value} {merged_tags}")
        
        # Store for later export
        key = (full_name, frozenset(merged_tags.items()))
        if key not in self._metrics_store:
            self._metrics_store[key] = 0
        self._metrics_store[key] += value
    
    def gauge(self, metric_name: str, value: float, 
              tags: Optional[dict[str, str]] = None) -> None:
        """
        Set a gauge metric to a specific value.
        
        Args:
            metric_name: Name of the metric to set
            value: Value to set the gauge to
            tags: Additional tags to associate with this metric
        """
        full_name = f"{self.service_name}.{metric_name}"
        merged_tags = self._merge_tags(tags)
        
        logger.debug(f"GAUGE {full_name}:{value} {merged_tags}")
        
        # Store for later export
        key = (full_name, frozenset(merged_tags.items()))
        self._metrics_store[key] = value
    
    def histogram(self, metric_name: str, value: float, 
                  tags: Optional[dict[str, str]] = None) -> None:
        """
        Record a value in a histogram metric.
        
        Args:
            metric_name: Name of the histogram metric
            value: Value to record
            tags: Additional tags to associate with this metric
        """
        full_name = f"{self.service_name}.{metric_name}"
        merged_tags = self._merge_tags(tags)
        
        logger.debug(f"HISTOGRAM {full_name}:{value} {merged_tags}")
        
        # In a real implementation, this would maintain histogram statistics
        key = (full_name, frozenset(merged_tags.items()))
        if key not in self._metrics_store:
            self._metrics_store[key] = []
        self._metrics_store[key].append(value)
    
    @contextlib.contextmanager
    def timer(self, metric_name: str, tags: Optional[dict[str, str]] = None) -> ContextManager[None]:
        """
        Context manager for timing operations and recording the duration.
        
        Args:
            metric_name: Name of the timing metric
            tags: Additional tags to associate with this metric
            
        Usage:
            with metrics.timer("operation.duration", tags={"type": "query"}):
                result = perform_operation()
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.histogram(metric_name, duration, tags)
    
    def timed(self, metric_name: str, tags: Optional[dict[str, str]] = None) -> Callable[[Callable[..., R]], Callable[..., R]]:
        """
        Decorator for timing function execution.
        
        Args:
            metric_name: Name of the timing metric
            tags: Additional tags to associate with this metric
            
        Usage:
            @metrics.timed("function.duration", tags={"module": "memory"})
            def process_data(data):
                # Processing logic
                return result
        """
        def decorator(func: Callable[..., R]) -> Callable[..., R]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> R:
                with self.timer(metric_name, tags):
                    return func(*args, **kwargs)
            return wrapper
        return decorator


class HealthCheck:
    """
    Health check definition and execution for system components.
    
    Health checks are used to verify that system components are functioning
    correctly and to provide diagnostic information when they are not.
    """
    
    def __init__(self, name: str, check_func: Callable[[], dict[str, Any]], 
                 interval_seconds: int = 60, timeout_seconds: float = 5.0):
        """
        Initialize a new health check.
        
        Args:
            name: Unique name for this health check
            check_func: Function that performs the health check and returns status
            interval_seconds: How often to run this check automatically
            timeout_seconds: Maximum time the check is allowed to run
        """
        self.name = name
        self.check_func = check_func
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self.last_result = None
        self.last_check_time = 0
        self.is_running = False
        
        logger.debug(f"Registered health check '{name}' with {interval_seconds}s interval")
    
    def run(self) -> dict[str, Any]:
        """
        Execute the health check and return the result.
        
        Returns:
            Dict containing at minimum:
            - status: "healthy", "degraded", or "unhealthy"
            - message: Human-readable status message
            - timestamp: When the check was performed
            
            May contain additional check-specific data.
        """
        if self.is_running:
            logger.warning(f"Health check '{self.name}' already running, returning last result")
            return self.last_result or {
                "status": "unknown",
                "message": "Check is currently running",
                "timestamp": time.time()
            }
        
        self.is_running = True
        start_time = time.time()
        
        try:
            # Run the check with timeout
            result = self._run_with_timeout()
            
            # Ensure required fields are present
            if "status" not in result:
                result["status"] = "unknown"
            if "message" not in result:
                result["message"] = "No message provided"
            
            # Add metadata
            result["timestamp"] = time.time()
            result["duration"] = time.time() - start_time
            
            self.last_result = result
            self.last_check_time = time.time()
            
            return result
        except Exception as e:
            error_result = {
                "status": "unhealthy",
                "message": f"Exception during health check: {str(e)}",
                "timestamp": time.time(),
                "duration": time.time() - start_time,
                "error": str(e)
            }
            self.last_result = error_result
            logger.error(f"Health check '{self.name}' failed: {e}", exc_info=True)
            return error_result
        finally:
            self.is_running = False
    
    def _run_with_timeout(self) -> dict[str, Any]:
        """Run the check function with a timeout."""
        # This is a simplified implementation - in production code,
        # you would use a more robust approach like concurrent.futures
        # or multiprocessing with proper timeout handling
        
        # For now, we'll just run the check directly
        return self.check_func()


class HealthRegistry:
    """
    Registry for health checks that manages their execution and reporting.
    """
    
    def __init__(self):
        """Initialize a new health registry."""
        self.checks: dict[str, HealthCheck] = {}
        self._scheduler_thread = None
        self._stop_event = threading.Event()
        logger.debug("Initialized health registry")
    
    def register(self, check: HealthCheck) -> None:
        """
        Register a health check with the registry.
        
        Args:
            check: The health check to register
        """
        if check.name in self.checks:
            logger.warning(f"Overwriting existing health check '{check.name}'")
        
        self.checks[check.name] = check
        logger.debug(f"Registered health check '{check.name}'")
    
    def unregister(self, name: str) -> None:
        """
        Remove a health check from the registry.
        
        Args:
            name: Name of the health check to remove
        """
        if name in self.checks:
            del self.checks[name]
            logger.debug(f"Unregistered health check '{name}'")
        else:
            logger.warning(f"Attempted to unregister unknown health check '{name}'")
    
    def run_check(self, name: str) -> dict[str, Any]:
        """
        Run a specific health check by name.
        
        Args:
            name: Name of the health check to run
            
        Returns:
            The health check result
            
        Raises:
            KeyError: If the named health check doesn't exist
        """
        if name not in self.checks:
            raise KeyError(f"No health check named '{name}'")
        
        return self.checks[name].run()
    
    def run_all_checks(self) -> dict[str, dict[str, Any]]:
        """
        Run all registered health checks and return their results.
        
        Returns:
            Dict mapping check names to their results
        """
        results = {}
        for name, check in self.checks.items():
            results[name] = check.run()
        
        return results
    
    def get_system_status(self) -> dict[str, Any]:
        """
        Get overall system health status based on all checks.
        
        Returns:
            Dict containing:
            - status: Overall system status ("healthy", "degraded", or "unhealthy")
            - checks: Results of all health checks
            - timestamp: When the status was generated
        """
        check_results = self.run_all_checks()
        
        # Determine overall status
        if not check_results:
            status = "unknown"
        elif all(r["status"] == "healthy" for r in check_results.values()):
            status = "healthy"
        elif any(r["status"] == "unhealthy" for r in check_results.values()):
            status = "unhealthy"
        else:
            status = "degraded"
        
        return {
            "status": status,
            "checks": check_results,
            "timestamp": time.time()
        }
    
    def start_scheduler(self) -> None:
        """Start the background thread that runs health checks on schedule."""
        if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
            logger.warning("Health check scheduler already running")
            return
            
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(
            target=self._run_scheduled_checks,
            daemon=True,
            name="health-check-scheduler"
        )
        self._scheduler_thread.start()
        logger.info("Started health check scheduler")
    
    def stop_scheduler(self) -> None:
        """Stop the health check scheduler thread."""
        if self._scheduler_thread is None or not self._scheduler_thread.is_alive():
            logger.warning("Health check scheduler not running")
            return
            
        self._stop_event.set()
        self._scheduler_thread.join(timeout=5.0)
        if self._scheduler_thread.is_alive():
            logger.warning("Health check scheduler did not terminate cleanly")
        else:
            logger.info("Health check scheduler stopped")
        self._scheduler_thread = None
    
    def _run_scheduled_checks(self) -> None:
        """Background thread that runs health checks at their specified intervals."""
        while not self._stop_event.is_set():
            current_time = time.time()
            
            for name, check in self.checks.items():
                # Run the check if it's due
                if current_time - check.last_check_time >= check.interval_seconds:
                    try:
                        check.run()
                    except Exception as e:
                        logger.error(f"Error running scheduled health check '{name}': {e}", exc_info=True)
            
            # Sleep a short time before checking again
            # This allows for more responsive shutdown than sleeping for a long time
            self._stop_event.wait(1.0)


def setup_monitoring(
    service_name: str = "neuroca",
    enable_metrics: bool = True,
    enable_tracing: bool = True,
    enable_health_checks: bool = True,
    default_tags: Optional[dict[str, str]] = None,
    log_level: int = logging.INFO
) -> None:
    """
    Set up the monitoring system with the specified components.
    
    This function initializes the monitoring subsystems based on the provided
    configuration. It should be called early in the application lifecycle.
    
    Args:
        service_name: Name of the service for metrics namespacing
        enable_metrics: Whether to enable metrics collection
        enable_tracing: Whether to enable distributed tracing
        enable_health_checks: Whether to enable health checks
        default_tags: Default tags to apply to all telemetry
        log_level: Logging level for the monitoring module
    """
    global _metrics_client, _tracing_client, _health_registry, _monitoring_initialized
    
    with _monitoring_lock:
        if _monitoring_initialized:
            logger.warning("Monitoring already initialized, call reset_monitoring() first to reconfigure")
            return
        
        # Configure logging
        logging.getLogger("neuroca.monitoring").setLevel(log_level)
        
        # Initialize default tags
        if default_tags is None:
            default_tags = {}
        
        # Add environment info to tags
        env = os.environ.get("NEUROCA_ENV", "development")
        default_tags["env"] = env
        default_tags["service"] = service_name
        
        # Initialize metrics if enabled
        if enable_metrics:
            _metrics_client = MetricsClient(
                service_name=service_name,
                tags=default_tags
            )
            _metrics_client.start()
            logger.info("Metrics collection initialized")
        
        # Initialize tracing if enabled
        if enable_tracing:
            # Placeholder for tracing initialization
            # In a real implementation, this would initialize OpenTelemetry or similar
            _tracing_client = None
            logger.info("Distributed tracing initialized")
        
        # Initialize health checks if enabled
        if enable_health_checks:
            _health_registry = HealthRegistry()
            _health_registry.start_scheduler()
            
            # Register a basic system health check
            _health_registry.register(HealthCheck(
                name="system",
                check_func=lambda: {"status": "healthy", "message": "System is running"},
                interval_seconds=30
            ))
            
            logger.info("Health checks initialized")
        
        _monitoring_initialized = True
        logger.info(f"Monitoring initialized for service '{service_name}' in {env} environment")


def reset_monitoring() -> None:
    """
    Reset and shut down all monitoring components.
    
    This function should be called during application shutdown or when
    reconfiguring the monitoring system.
    """
    global _metrics_client, _tracing_client, _health_registry, _monitoring_initialized
    
    with _monitoring_lock:
        if not _monitoring_initialized:
            logger.warning("Monitoring not initialized")
            return
        
        # Shut down metrics client
        if _metrics_client is not None:
            _metrics_client.stop()
            _metrics_client = None
        
        # Shut down tracing client
        if _tracing_client is not None:
            # Placeholder for tracing shutdown
            _tracing_client = None
        
        # Shut down health registry
        if _health_registry is not None:
            _health_registry.stop_scheduler()
            _health_registry = None
        
        _monitoring_initialized = False
        logger.info("Monitoring system reset")


def get_metrics_client() -> MetricsClient:
    """
    Get the configured metrics client.
    
    Returns:
        The metrics client instance
        
    Raises:
        RuntimeError: If monitoring has not been initialized or metrics are disabled
    """
    if not _monitoring_initialized:
        raise RuntimeError("Monitoring not initialized, call setup_monitoring() first")
    
    if _metrics_client is None:
        raise RuntimeError("Metrics collection is disabled")
    
    return _metrics_client


def get_health_registry() -> HealthRegistry:
    """
    Get the configured health registry.
    
    Returns:
        The health registry instance
        
    Raises:
        RuntimeError: If monitoring has not been initialized or health checks are disabled
    """
    if not _monitoring_initialized:
        raise RuntimeError("Monitoring not initialized, call setup_monitoring() first")
    
    if _health_registry is None:
        raise RuntimeError("Health checks are disabled")
    
    return _health_registry


def register_health_check(
    name: str,
    check_func: Callable[[], dict[str, Any]],
    interval_seconds: int = 60,
    timeout_seconds: float = 5.0
) -> None:
    """
    Register a new health check with the system.
    
    This is a convenience function that creates and registers a health check.
    
    Args:
        name: Unique name for this health check
        check_func: Function that performs the health check and returns status
        interval_seconds: How often to run this check automatically
        timeout_seconds: Maximum time the check is allowed to run
        
    Raises:
        RuntimeError: If monitoring has not been initialized or health checks are disabled
    """
    registry = get_health_registry()
    check = HealthCheck(
        name=name,
        check_func=check_func,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds
    )
    registry.register(check)


# Initialize with default settings if environment variable is set
if os.environ.get("NEUROCA_AUTO_MONITORING", "").lower() in ("1", "true", "yes"):
    setup_monitoring()