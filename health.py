"""
Health monitoring functionality for the NCA system.

This module provides health checking and monitoring services for ensuring
the system is functioning properly.
"""

from typing import Dict, List, Any, Callable, Optional
from enum import Enum
import time
import logging
import threading
from datetime import datetime, timedelta

# Set up logger
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enum for service health checks."""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    
    def __str__(self) -> str:
        return self.value


class HealthCheck:
    """Represents a health check for a specific component."""
    
    def __init__(self, name: str, check_func: Callable[[], HealthStatus], 
                description: str = "", dependencies: List[str] = None):
        """
        Initialize a health check.
        
        Args:
            name: Name of the component being checked
            check_func: Function to call to get health status
            description: Description of what this check validates
            dependencies: List of dependent component names
        """
        self.name = name
        self.check_func = check_func
        self.description = description
        self.dependencies = dependencies or []
        self.last_status = HealthStatus.UNKNOWN
        self.last_check_time = None
        self.consecutive_failures = 0
        
    def check(self) -> HealthStatus:
        """
        Perform the health check.
        
        Returns:
            Current health status
        """
        try:
            self.last_check_time = datetime.now()
            self.last_status = self.check_func()
            
            if self.last_status != HealthStatus.HEALTHY:
                self.consecutive_failures += 1
            else:
                self.consecutive_failures = 0
                
            return self.last_status
        except Exception as e:
            logger.error(f"Health check error for {self.name}: {str(e)}")
            self.last_status = HealthStatus.UNHEALTHY
            self.consecutive_failures += 1
            return HealthStatus.UNHEALTHY
            
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert health check to a dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": str(self.last_status),
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "consecutive_failures": self.consecutive_failures,
            "dependencies": self.dependencies
        }


class HealthMonitor:
    """Service health monitoring system."""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize the health monitor.
        
        Args:
            check_interval: Interval between checks in seconds
        """
        self.checks: Dict[str, HealthCheck] = {}
        self.check_interval = check_interval
        self.monitoring_thread = None
        self.should_stop = threading.Event()
        self.last_report: Dict[str, Any] = {}
        
    def register_check(self, check: HealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            check: The health check to register
        """
        self.checks[check.name] = check
        logger.info(f"Registered health check: {check.name}")
        
    def register_simple_check(self, name: str, check_func: Callable[[], bool], 
                             description: str = "", dependencies: List[str] = None) -> None:
        """
        Register a simple boolean health check.
        
        Args:
            name: Name of the component
            check_func: Function returning True if healthy, False otherwise
            description: Check description
            dependencies: Component dependencies
        """
        def wrapped_check() -> HealthStatus:
            try:
                result = check_func()
                return HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
            except Exception:
                return HealthStatus.UNHEALTHY
                
        self.register_check(HealthCheck(name, wrapped_check, description, dependencies))
        
    def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks and return a health report.
        
        Returns:
            Health report dictionary
        """
        start_time = time.time()
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name, check in self.checks.items():
            status = check.check()
            results[name] = check.to_dict()
            
            # Update overall status
            if status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif status == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.DEGRADED
                
        elapsed_time = time.time() - start_time
        
        self.last_report = {
            "status": str(overall_status),
            "timestamp": datetime.now().isoformat(),
            "checks": results,
            "check_duration_seconds": round(elapsed_time, 3)
        }
        
        return self.last_report
        
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        logger.info("Health monitoring started")
        
        while not self.should_stop.is_set():
            try:
                self.check_all()
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {str(e)}")
                
            # Sleep for the check interval or until stopped
            self.should_stop.wait(self.check_interval)
            
        logger.info("Health monitoring stopped")
        
    def start_monitoring(self) -> None:
        """Start background health monitoring."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Health monitoring already running")
            return
            
        self.should_stop.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            name="health-monitor",
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Health monitoring thread started")
        
    def stop_monitoring(self) -> None:
        """Stop background health monitoring."""
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            logger.warning("Health monitoring not running")
            return
            
        logger.info("Stopping health monitoring...")
        self.should_stop.set()
        self.monitoring_thread.join(timeout=10.0)
        if self.monitoring_thread.is_alive():
            logger.warning("Health monitoring thread did not exit gracefully")
        else:
            logger.info("Health monitoring stopped successfully")


# Create a singleton instance
health_monitor = HealthMonitor()

def get_health_report() -> Dict[str, Any]:
    """
    Get the current health report.
    
    Returns:
        Health report dictionary
    """
    return health_monitor.check_all()


def register_health_check(name: str, check_func: Callable[[], bool], 
                         description: str = "", dependencies: List[str] = None) -> None:
    """
    Register a simple health check function.
    
    Args:
        name: Component name
        check_func: Function returning True if healthy
        description: Check description
        dependencies: Component dependencies
    """
    health_monitor.register_simple_check(name, check_func, description, dependencies) 