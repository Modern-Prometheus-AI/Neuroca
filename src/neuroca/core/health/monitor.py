"""
Health monitoring system for the NeuroCognitive Architecture.

This module implements the health monitoring system, including health check 
definitions, execution, and reporting.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from neuroca.core.health.component import ComponentHealthStatus, ComponentStatus

# Configure logging
logger = logging.getLogger(__name__)


class HealthCheckStatus(Enum):
    """
    Defines the possible outcomes of a health check.
    """
    PASSED = "passed"           # Check passed successfully
    WARNING = "warning"         # Check passed but with concerning metrics
    FAILED = "failed"           # Check failed, component has issues
    ERROR = "error"             # Error occurred while running the check
    SKIPPED = "skipped"         # Check was skipped (dependency failed or not applicable)
    TIMEOUT = "timeout"         # Check timed out while running


@dataclass
class HealthCheckResult:
    """
    Represents the result of a health check execution.
    
    Attributes:
        check_id: Unique identifier for the health check
        status: The outcome of the health check
        component_id: The component being checked
        message: Human-readable description of the result
        details: Additional details about the check result
        timestamp: When the check was executed
        execution_time: How long the check took to execute (ms)
    """
    check_id: str
    status: HealthCheckStatus
    component_id: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    execution_time: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert check result to dictionary for serialization."""
        return {
            'check_id': self.check_id,
            'status': self.status.value,
            'component_id': self.component_id,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp,
            'execution_time': self.execution_time
        }


class HealthCheck(ABC):
    """
    Base class for all health checks in the system.
    
    Health checks inspect components and gather health metrics. Each check
    should focus on a specific aspect of a component's health.
    """
    def __init__(self, check_id: str, component_id: str, description: str = ""):
        """
        Initialize a health check.
        
        Args:
            check_id: Unique identifier for this check
            component_id: The component this check is for
            description: Human-readable description of what this check does
        """
        self.check_id = check_id
        self.component_id = component_id
        self.description = description
        self.timeout_seconds = 5.0  # Default timeout
        self.dependencies: set[str] = set()  # Other checks this depends on
    
    @abstractmethod
    def execute(self) -> HealthCheckResult:
        """
        Execute the health check and return a result.
        
        Returns:
            A HealthCheckResult object with the check outcome
        """
        pass
    
    def create_result(self, status: HealthCheckStatus, message: str = "", **details) -> HealthCheckResult:
        """
        Create a standardized health check result.
        
        Args:
            status: The outcome status of the check
            message: Human-readable message explaining the result
            **details: Additional details to include in the result
        
        Returns:
            A properly formatted HealthCheckResult
        """
        return HealthCheckResult(
            check_id=self.check_id,
            status=status,
            component_id=self.component_id,
            message=message,
            details=details
        )


class MemoryHealthCheck(HealthCheck):
    """
    Health check for memory systems.
    
    Checks memory capacity, utilization, and operational status to ensure
    the memory system is functioning correctly.
    """
    def __init__(self, check_id: str, component_id: str, 
                 memory_system, capacity_threshold: float = 0.9):
        """
        Initialize a memory health check.
        
        Args:
            check_id: Unique identifier for this check
            component_id: The memory component's ID
            memory_system: The memory system to check
            capacity_threshold: Threshold for capacity warning (0.0-1.0)
        """
        super().__init__(check_id, component_id, 
                         f"Memory health check for {component_id}")
        self.memory_system = memory_system
        self.capacity_threshold = capacity_threshold
    
    def execute(self) -> HealthCheckResult:
        """
        Check the health of the memory system.
        
        Returns:
            HealthCheckResult with status and metrics
        """
        start_time = time.time()
        
        try:
            # Get basic metrics
            total_items = len(self.memory_system.retrieve_all())
            capacity = getattr(self.memory_system, 'capacity', float('inf'))
            
            # Attempt basic operations to ensure functionality
            test_content = f"Health check test item - {time.time()}"
            chunk_id = self.memory_system.store(test_content)
            retrieved = self.memory_system.retrieve_by_id(chunk_id)
            
            # Cleanup after ourselves
            if retrieved is not None:
                self.memory_system.forget(chunk_id)
            
            # Calculate metrics
            capacity_ratio = total_items / capacity if capacity != float('inf') else 0.0
            
            # Determine status based on metrics
            if capacity_ratio >= self.capacity_threshold:
                status = HealthCheckStatus.WARNING
                message = f"Memory system is nearing capacity ({capacity_ratio:.1%})"
            else:
                status = HealthCheckStatus.PASSED
                message = f"Memory system is operating normally ({total_items} items, {capacity_ratio:.1%} of capacity)"
            
            # Include detailed metrics
            details = {
                "total_items": total_items,
                "capacity": capacity,
                "capacity_ratio": capacity_ratio,
                "operations_successful": retrieved is not None and retrieved.content == test_content
            }
            
            # Add any memory-system specific metrics if available
            if hasattr(self.memory_system, 'get_metrics'):
                details.update(self.memory_system.get_metrics())
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result = self.create_result(status, message, **details)
            result.execution_time = execution_time
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.exception(f"Error during memory health check: {e}")
            
            result = self.create_result(
                HealthCheckStatus.ERROR,
                f"Health check failed with error: {str(e)}",
                error=str(e),
                error_type=type(e).__name__
            )
            result.execution_time = execution_time
            return result


class HealthMonitor:
    """
    Manages health checks and monitoring for all system components.
    
    This class provides methods to register health checks, run them,
    and report on system health status.
    """
    def __init__(self):
        """Initialize the health monitor."""
        self._checks: dict[str, HealthCheck] = {}
        self._results: dict[str, HealthCheckResult] = {}
        self._component_status: dict[str, ComponentHealthStatus] = {}
        self._lock = threading.RLock()
        self._scheduled_check_interval = 60  # Default: check every minute
        self._scheduler_thread = None
        self._stop_scheduler = threading.Event()
    
    def register_check(self, check: HealthCheck) -> None:
        """
        Register a health check with the monitor.
        
        Args:
            check: The health check to register
        """
        with self._lock:
            self._checks[check.check_id] = check
    
    def unregister_check(self, check_id: str) -> None:
        """
        Remove a health check from the monitor.
        
        Args:
            check_id: The ID of the check to remove
        """
        with self._lock:
            if check_id in self._checks:
                del self._checks[check_id]
    
    def run_check(self, check_id: str) -> HealthCheckResult:
        """
        Run a specific health check and store its result.
        
        Args:
            check_id: The ID of the check to run
        
        Returns:
            The result of the health check
        
        Raises:
            KeyError: If the check ID is not registered
        """
        with self._lock:
            if check_id not in self._checks:
                raise KeyError(f"Health check '{check_id}' not registered")
            
            check = self._checks[check_id]
        
        # Run the check without holding the lock
        result = check.execute()
        
        # Store the result
        with self._lock:
            self._results[check_id] = result
            
            # Update component status based on result
            self._update_component_status(result)
        
        return result
    
    def run_all_checks(self) -> dict[str, HealthCheckResult]:
        """
        Run all registered health checks and return results.
        
        Returns:
            Dictionary mapping check IDs to their results
        """
        results = {}
        
        for check_id in list(self._checks.keys()):
            try:
                results[check_id] = self.run_check(check_id)
            except Exception as e:
                logger.error(f"Error running health check {check_id}: {e}")
                # Create an error result
                check = self._checks.get(check_id)
                if check:
                    results[check_id] = HealthCheckResult(
                        check_id=check_id,
                        status=HealthCheckStatus.ERROR,
                        component_id=check.component_id,
                        message=f"Error executing health check: {str(e)}",
                        details={"error": str(e), "error_type": type(e).__name__}
                    )
        
        return results
    
    def get_result(self, check_id: str) -> Optional[HealthCheckResult]:
        """
        Get the most recent result for a specific health check.
        
        Args:
            check_id: The ID of the check
        
        Returns:
            The most recent result or None if no result available
        """
        with self._lock:
            return self._results.get(check_id)
    
    def get_all_results(self) -> dict[str, HealthCheckResult]:
        """
        Get the most recent results for all health checks.
        
        Returns:
            Dictionary mapping check IDs to their results
        """
        with self._lock:
            return dict(self._results)
    
    def get_component_status(self, component_id: str) -> Optional[ComponentHealthStatus]:
        """
        Get the current health status for a specific component.
        
        Args:
            component_id: The ID of the component
        
        Returns:
            The component's health status or None if not available
        """
        with self._lock:
            return self._component_status.get(component_id)
    
    def get_all_component_statuses(self) -> dict[str, ComponentHealthStatus]:
        """
        Get the current health status for all components.
        
        Returns:
            Dictionary mapping component IDs to their status
        """
        with self._lock:
            return dict(self._component_status)
    
    def _update_component_status(self, result: HealthCheckResult) -> None:
        """
        Update a component's status based on a health check result.
        
        Args:
            result: The health check result to process
        """
        component_id = result.component_id
        
        # Get or create component status
        if component_id not in self._component_status:
            self._component_status[component_id] = ComponentHealthStatus(component_id)
        
        status = self._component_status[component_id]
        
        # Update status based on check result
        if result.status == HealthCheckStatus.PASSED:
            # Consider if we need to improve status
            if status.status in [ComponentStatus.UNKNOWN, ComponentStatus.CRITICAL, ComponentStatus.FAILED]:
                status.update_status(ComponentStatus.FUNCTIONAL)
                
        elif result.status == HealthCheckStatus.WARNING:
            if status.status in [ComponentStatus.OPTIMAL, ComponentStatus.FUNCTIONAL]:
                status.update_status(ComponentStatus.DEGRADED, 
                                    f"Warning from check {result.check_id}: {result.message}")
                
        elif result.status == HealthCheckStatus.FAILED:
            status.update_status(ComponentStatus.CRITICAL, 
                                f"Failed check {result.check_id}: {result.message}")
                
        elif result.status == HealthCheckStatus.ERROR:
            # Only downgrade if we don't already know it's failed
            if status.status != ComponentStatus.FAILED:
                status.update_status(ComponentStatus.STRAINED, 
                                    f"Error during check {result.check_id}: {result.message}")
        
        # Update metrics with check details if available
        if result.details and status.metrics:
            # Extract metrics from check details
            metrics_update = {}
            for key, value in result.details.items():
                # Only copy numeric metrics
                if isinstance(value, (int, float)) and key not in ['timestamp', 'execution_time']:
                    metrics_update[key] = value
            
            if metrics_update:
                status.metrics.update(**metrics_update)
    
    def start_scheduled_checks(self, interval_seconds: int = 60) -> None:
        """
        Start a background thread to run health checks at regular intervals.
        
        Args:
            interval_seconds: How often to run checks (in seconds)
        """
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logger.warning("Health check scheduler already running")
            return
        
        self._scheduled_check_interval = interval_seconds
        self._stop_scheduler.clear()
        
        def scheduler_loop():
            while not self._stop_scheduler.is_set():
                try:
                    self.run_all_checks()
                except Exception as e:
                    logger.error(f"Error in health check scheduler: {e}")
                
                # Wait for the next interval or until stopped
                self._stop_scheduler.wait(self._scheduled_check_interval)
        
        self._scheduler_thread = threading.Thread(
            target=scheduler_loop,
            name="HealthCheckScheduler",
            daemon=True
        )
        self._scheduler_thread.start()
        logger.info(f"Health check scheduler started with {interval_seconds}s interval")
    
    def stop_scheduled_checks(self) -> None:
        """Stop the background health check scheduler."""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._stop_scheduler.set()
            self._scheduler_thread.join(timeout=1.0)
            logger.info("Health check scheduler stopped")


# Global instance for singleton access
_health_monitor = HealthMonitor()

def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    return _health_monitor

def register_health_check(check: HealthCheck) -> None:
    """Register a health check with the global monitor."""
    get_health_monitor().register_check(check)

def run_health_check(check_id: str) -> HealthCheckResult:
    """Run a specific health check using the global monitor."""
    return get_health_monitor().run_check(check_id)

def get_health_report() -> dict[str, Any]:
    """
    Generate a comprehensive health report for all components.
    
    Returns:
        Dictionary with system health information
    """
    monitor = get_health_monitor()
    results = monitor.get_all_results()
    statuses = monitor.get_all_component_statuses()
    
    # Calculate overall system health
    component_health_levels = {
        ComponentStatus.OPTIMAL: 1.0,
        ComponentStatus.FUNCTIONAL: 0.8,
        ComponentStatus.DEGRADED: 0.6,
        ComponentStatus.STRAINED: 0.4,
        ComponentStatus.CRITICAL: 0.2,
        ComponentStatus.FAILED: 0.0,
        ComponentStatus.UNKNOWN: 0.5
    }
    
    overall_health = 1.0
    if statuses:
        # Weight each component equally for overall health
        health_scores = [component_health_levels[s.status] for s in statuses.values()]
        overall_health = sum(health_scores) / len(health_scores)
    
    # Count checks by status
    check_counts = {status.value: 0 for status in HealthCheckStatus}
    for result in results.values():
        check_counts[result.status.value] += 1
    
    # Format report
    report = {
        "timestamp": time.time(),
        "overall_health": overall_health,
        "component_count": len(statuses),
        "check_count": len(results),
        "check_counts": check_counts,
        "components": {
            comp_id: status.to_dict() for comp_id, status in statuses.items()
        },
        "checks": {
            check_id: result.to_dict() for check_id, result in results.items()
        }
    }
    
    return report 