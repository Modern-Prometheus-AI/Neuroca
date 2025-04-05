"""
Health Monitoring Module for NeuroCognitive Architecture (NCA)

This module provides comprehensive health monitoring capabilities for the NCA system,
including health checks, status reporting, and component monitoring. It serves as the
central point for system health observability and diagnostics.

The health monitoring system follows a hierarchical approach:
1. Component-level health checks
2. Subsystem-level aggregation
3. System-wide health status reporting

Usage:
    from neuroca.monitoring.health import HealthStatus, HealthCheck, register_component
    
    # Register a component for health monitoring
    @register_component("memory_subsystem")
    class MemorySubsystem:
        def get_health(self) -> HealthStatus:
            # Implement health check logic
            return HealthStatus.HEALTHY
    
    # Perform a health check
    health_check = HealthCheck()
    system_health = health_check.check_system_health()
    
    if system_health.status == HealthStatus.DEGRADED:
        logger.warning(f"System health is degraded: {system_health.details}")
"""

import enum
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

# Configure module logger
logger = logging.getLogger(__name__)

# Registry to store components that can be health-checked
_component_registry: dict[str, Any] = {}


class HealthStatus(enum.Enum):
    """
    Enumeration of possible health statuses for system components.
    
    HEALTHY: Component is functioning normally
    DEGRADED: Component is functioning but with reduced capabilities
    UNHEALTHY: Component is not functioning properly
    CRITICAL: Component has failed and requires immediate attention
    UNKNOWN: Component health status cannot be determined
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthResult:
    """
    Data class representing the result of a health check.
    
    Attributes:
        component_id: Identifier of the component
        status: Health status of the component
        details: Additional details about the health status
        timestamp: When the health check was performed
        metrics: Optional metrics associated with the health check
        dependencies: Health results of dependencies
    """
    component_id: str
    status: HealthStatus
    details: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: dict[str, Any] = field(default_factory=dict)
    dependencies: dict[str, 'HealthResult'] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the health result to a dictionary representation."""
        result = {
            "component_id": self.component_id,
            "status": self.status.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
        }
        
        if self.dependencies:
            result["dependencies"] = {
                dep_id: dep_result.to_dict() 
                for dep_id, dep_result in self.dependencies.items()
            }
            
        return result


@dataclass
class SystemHealthSummary:
    """
    Data class representing the overall health of the system.
    
    Attributes:
        status: Overall health status of the system
        component_results: Health results for individual components
        timestamp: When the system health check was performed
        details: Additional details about the system health
    """
    status: HealthStatus
    component_results: dict[str, HealthResult]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the system health summary to a dictionary representation."""
        return {
            "status": self.status.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "components": {
                comp_id: result.to_dict() 
                for comp_id, result in self.component_results.items()
            }
        }


def register_component(component_id: str) -> Callable:
    """
    Decorator to register a component for health monitoring.
    
    Args:
        component_id: Unique identifier for the component
        
    Returns:
        Decorator function that registers the component
        
    Example:
        @register_component("memory_manager")
        class MemoryManager:
            def get_health(self) -> HealthStatus:
                # Health check implementation
                return HealthStatus.HEALTHY
    """
    def decorator(cls):
        if component_id in _component_registry:
            logger.warning(f"Component with ID '{component_id}' already registered. Overwriting.")
        
        # Validate that the class has a get_health method
        if not hasattr(cls, 'get_health'):
            raise AttributeError(
                f"Class {cls.__name__} must implement 'get_health()' method to be registered for health monitoring"
            )
        
        _component_registry[component_id] = cls
        logger.debug(f"Registered component '{component_id}' for health monitoring")
        return cls
    
    return decorator


def unregister_component(component_id: str) -> bool:
    """
    Unregister a component from health monitoring.
    
    Args:
        component_id: Unique identifier for the component
        
    Returns:
        True if component was unregistered, False if component was not found
    """
    if component_id in _component_registry:
        del _component_registry[component_id]
        logger.debug(f"Unregistered component '{component_id}' from health monitoring")
        return True
    
    logger.warning(f"Attempted to unregister unknown component '{component_id}'")
    return False


def get_registered_components() -> set[str]:
    """
    Get the set of all registered component IDs.
    
    Returns:
        Set of component IDs
    """
    return set(_component_registry.keys())


class HealthCheck:
    """
    Class responsible for performing health checks on system components.
    
    This class provides methods to check the health of individual components,
    subsystems, or the entire system. It aggregates health results and provides
    a comprehensive view of system health.
    """
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize the health check system.
        
        Args:
            timeout: Maximum time in seconds to wait for a health check to complete
        """
        self.timeout = timeout
        logger.debug(f"Initialized HealthCheck with timeout={timeout}s")
    
    def check_component_health(self, component_id: str) -> HealthResult:
        """
        Check the health of a specific component.
        
        Args:
            component_id: Identifier of the component to check
            
        Returns:
            HealthResult for the component
            
        Raises:
            KeyError: If the component is not registered
        """
        if component_id not in _component_registry:
            logger.error(f"Component '{component_id}' not registered for health monitoring")
            raise KeyError(f"Component '{component_id}' not registered for health monitoring")
        
        component = _component_registry[component_id]
        start_time = time.time()
        
        try:
            # Set a timeout for the health check
            if time.time() - start_time > self.timeout:
                return HealthResult(
                    component_id=component_id,
                    status=HealthStatus.UNKNOWN,
                    details=f"Health check timed out after {self.timeout}s"
                )
            
            # Get the health status from the component
            health_status = component.get_health()
            
            # If the component returns a full HealthResult, use it
            if isinstance(health_status, HealthResult):
                return health_status
            
            # If the component returns just a status, create a HealthResult
            if isinstance(health_status, HealthStatus):
                return HealthResult(
                    component_id=component_id,
                    status=health_status
                )
            
            # If the component returns something unexpected
            logger.warning(
                f"Component '{component_id}' returned unexpected health type: {type(health_status)}"
            )
            return HealthResult(
                component_id=component_id,
                status=HealthStatus.UNKNOWN,
                details=f"Component returned unexpected health type: {type(health_status)}"
            )
            
        except Exception as e:
            logger.exception(f"Error checking health of component '{component_id}': {str(e)}")
            return HealthResult(
                component_id=component_id,
                status=HealthStatus.UNHEALTHY,
                details=f"Exception during health check: {str(e)}"
            )
    
    def check_system_health(self) -> SystemHealthSummary:
        """
        Check the health of the entire system.
        
        Returns:
            SystemHealthSummary containing the overall system health status
            and individual component health results
        """
        component_results = {}
        
        # Check health of all registered components
        for component_id in _component_registry:
            try:
                result = self.check_component_health(component_id)
                component_results[component_id] = result
            except Exception as e:
                logger.exception(f"Failed to check health of component '{component_id}': {str(e)}")
                component_results[component_id] = HealthResult(
                    component_id=component_id,
                    status=HealthStatus.UNKNOWN,
                    details=f"Failed to perform health check: {str(e)}"
                )
        
        # Determine overall system health based on component health
        overall_status = self._determine_overall_status(component_results)
        details = self._generate_system_health_details(overall_status, component_results)
        
        return SystemHealthSummary(
            status=overall_status,
            component_results=component_results,
            details=details
        )
    
    def _determine_overall_status(self, component_results: dict[str, HealthResult]) -> HealthStatus:
        """
        Determine the overall system health status based on component health results.
        
        Args:
            component_results: Dictionary of component health results
            
        Returns:
            Overall system health status
        """
        if not component_results:
            return HealthStatus.UNKNOWN
        
        # Count components in each status
        status_counts = {status: 0 for status in HealthStatus}
        for result in component_results.values():
            status_counts[result.status] += 1
        
        # Determine overall status based on component statuses
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.UNKNOWN] == len(component_results):
            return HealthStatus.UNKNOWN
        elif status_counts[HealthStatus.HEALTHY] + status_counts[HealthStatus.UNKNOWN] == len(component_results):
            if status_counts[HealthStatus.UNKNOWN] > 0:
                return HealthStatus.DEGRADED
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.DEGRADED
    
    def _generate_system_health_details(
        self, 
        overall_status: HealthStatus, 
        component_results: dict[str, HealthResult]
    ) -> str:
        """
        Generate a detailed description of the system health.
        
        Args:
            overall_status: Overall system health status
            component_results: Dictionary of component health results
            
        Returns:
            Detailed description of system health
        """
        if not component_results:
            return "No components registered for health monitoring"
        
        # Count components in each status
        status_counts = {status: 0 for status in HealthStatus}
        for result in component_results.values():
            status_counts[result.status] += 1
        
        # Generate details based on overall status
        if overall_status == HealthStatus.HEALTHY:
            return f"All {len(component_results)} components are healthy"
        
        details = []
        if status_counts[HealthStatus.CRITICAL] > 0:
            critical_components = [
                comp_id for comp_id, result in component_results.items() 
                if result.status == HealthStatus.CRITICAL
            ]
            details.append(f"{status_counts[HealthStatus.CRITICAL]} critical components: {', '.join(critical_components)}")
        
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            unhealthy_components = [
                comp_id for comp_id, result in component_results.items() 
                if result.status == HealthStatus.UNHEALTHY
            ]
            details.append(f"{status_counts[HealthStatus.UNHEALTHY]} unhealthy components: {', '.join(unhealthy_components)}")
        
        if status_counts[HealthStatus.DEGRADED] > 0:
            degraded_components = [
                comp_id for comp_id, result in component_results.items() 
                if result.status == HealthStatus.DEGRADED
            ]
            details.append(f"{status_counts[HealthStatus.DEGRADED]} degraded components: {', '.join(degraded_components)}")
        
        if status_counts[HealthStatus.UNKNOWN] > 0:
            unknown_components = [
                comp_id for comp_id, result in component_results.items() 
                if result.status == HealthStatus.UNKNOWN
            ]
            details.append(f"{status_counts[HealthStatus.UNKNOWN]} components with unknown status: {', '.join(unknown_components)}")
        
        return "; ".join(details)


# Convenience functions for external usage

def get_system_health() -> SystemHealthSummary:
    """
    Convenience function to get the current system health.
    
    Returns:
        SystemHealthSummary containing the overall system health
    """
    health_check = HealthCheck()
    return health_check.check_system_health()


def get_component_health(component_id: str) -> HealthResult:
    """
    Convenience function to get the health of a specific component.
    
    Args:
        component_id: Identifier of the component to check
        
    Returns:
        HealthResult for the component
        
    Raises:
        KeyError: If the component is not registered
    """
    health_check = HealthCheck()
    return health_check.check_component_health(component_id)


def is_system_healthy() -> bool:
    """
    Convenience function to check if the system is healthy.
    
    Returns:
        True if the system is healthy, False otherwise
    """
    health = get_system_health()
    return health.status == HealthStatus.HEALTHY