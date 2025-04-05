"""
Health monitoring utilities for the NCA system.

This module provides health checking and monitoring capabilities to track
system health and detect degradation or failures.
"""

import logging
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable

# Set up logger
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enum for service health checks."""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    
    def __str__(self) -> str:
        """Return string representation of the status."""
        return self.value


class HealthCheck:
    """Represents a health check that can be executed to verify system functionality."""
    
    def __init__(self, name: str, check_func: Callable[[], HealthStatus], 
                description: str = "", dependencies: list[str] = None):
        """
        Initialize a health check.
        
        Args:
            name: Unique name for the health check
            check_func: Function that performs the check and returns a HealthStatus
            description: Description of what this check verifies
            dependencies: List of other services/components this check depends on
        """
        self.name = name
        self.check_func = check_func
        self.description = description
        self.dependencies = dependencies or []
        self.last_status = HealthStatus.UNKNOWN
        self.last_check_time = None
        self.last_success_time = None
        self.failure_count = 0
        self.success_count = 0
        
    def check(self) -> HealthStatus:
        """
        Execute the health check.
        
        Returns:
            HealthStatus indicating the result of the check
        """
        self.last_check_time = datetime.now()
        
        try:
            status = self.check_func()
            self.last_status = status
            
            if status == HealthStatus.HEALTHY:
                self.last_success_time = self.last_check_time
                self.success_count += 1
                self.failure_count = 0  # Reset consecutive failures
            else:
                self.failure_count += 1
                
            logger.debug(f"Health check '{self.name}' result: {status}")
            return status
            
        except Exception as e:
            self.last_status = HealthStatus.UNHEALTHY
            self.failure_count += 1
            logger.warning(f"Health check '{self.name}' failed with error: {str(e)}")
            return HealthStatus.UNHEALTHY
            
    def to_dict(self) -> dict[str, Any]:
        """
        Convert health check to a dictionary.
        
        Returns:
            Dictionary representation of the health check
        """
        return {
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": str(self.last_status),
            "lastCheckTime": self.last_check_time.isoformat() if self.last_check_time else None,
            "lastSuccessTime": self.last_success_time.isoformat() if self.last_success_time else None,
            "failureCount": self.failure_count,
            "successCount": self.success_count
        }


class HealthMonitor:
    """Monitors and reports on the health of system components."""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize the health monitor.
        
        Args:
            check_interval: How often to run health checks (in seconds)
        """
        self.checks: dict[str, HealthCheck] = {}
        self.check_interval = check_interval
        self.monitoring_thread = None
        self.is_monitoring = False
        self.lock = threading.Lock()
        
    def register_check(self, check: HealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            check: HealthCheck object to register
        """
        with self.lock:
            self.checks[check.name] = check
            logger.info(f"Registered health check: {check.name}")
            
    def register_simple_check(self, name: str, check_func: Callable[[], bool], 
                             description: str = "", dependencies: list[str] = None) -> None:
        """
        Register a simple boolean health check function.
        
        Args:
            name: Unique name for the health check
            check_func: Function that returns True for healthy, False for unhealthy
            description: Description of what this check verifies
            dependencies: List of other services/components this check depends on
        """
        def wrapped_check() -> HealthStatus:
            try:
                result = check_func()
                return HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
            except Exception:
                return HealthStatus.UNHEALTHY
                
        self.register_check(HealthCheck(
            name=name,
            check_func=wrapped_check,
            description=description,
            dependencies=dependencies
        ))
            
    def check_all(self) -> dict[str, Any]:
        """
        Execute all registered health checks.
        
        Returns:
            Health report with status of all checks
        """
        with self.lock:
            checks_copy = list(self.checks.values())
            
        results = {}
        overall_status = HealthStatus.HEALTHY
        check_time = datetime.now().isoformat()
        
        for check in checks_copy:
            status = check.check()
            results[check.name] = check.to_dict()
            
            # Update overall status (unhealthy > degraded > healthy)
            if status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif status == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.DEGRADED
                
        health_report = {
            "status": str(overall_status),
            "timestamp": check_time,
            "checks": results
        }
        
        return health_report
            
    def _monitoring_loop(self) -> None:
        """Internal monitoring loop that periodically checks health."""
        logger.info(f"Health monitoring started with interval {self.check_interval}s")
        
        while self.is_monitoring:
            try:
                report = self.check_all()
                if report["status"] != "healthy":
                    logger.warning(f"System health is {report['status']}")
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {str(e)}")
                
            time.sleep(self.check_interval)
            
    def start_monitoring(self) -> None:
        """
        Start the background health monitoring thread.
        """
        with self.lock:
            if self.is_monitoring:
                logger.warning("Health monitoring already started")
                return
                
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            logger.info("Health monitoring thread started")
            
    def stop_monitoring(self) -> None:
        """
        Stop the background health monitoring thread.
        """
        with self.lock:
            if not self.is_monitoring:
                logger.warning("Health monitoring not running")
                return
                
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=2.0)
                logger.info("Health monitoring stopped")


# Create a singleton instance for global use
health_monitor = HealthMonitor()

def get_health_report() -> dict[str, Any]:
    """
    Get a comprehensive health report of the system.
    
    Returns:
        Dictionary with health status and details
    """
    return health_monitor.check_all()


def register_health_check(name: str, check_func: Callable[[], bool], 
                         description: str = "", dependencies: list[str] = None) -> None:
    """
    Register a new health check with the system.
    
    Args:
        name: Unique name for the health check
        check_func: Function that returns True for healthy, False for unhealthy
        description: Description of what this check verifies
        dependencies: List of other services/components this check depends on
    """
    health_monitor.register_simple_check(name, check_func, description, dependencies) 