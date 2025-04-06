"""
Registry for health checks and monitored components.

This module provides a central registry for registering health checks
and components that need health monitoring.
"""

import functools
import inspect
import logging
from typing import Any, Callable, Optional

from neuroca.core.health.monitor import HealthCheck

logger = logging.getLogger(__name__)


class HealthRegistry:
    """
    Registry for health checks and monitored components.
    
    This class maintains a registry of components that need health monitoring
    and the health checks associated with them.
    """
    def __init__(self):
        """Initialize the health registry."""
        self._checks: dict[str, HealthCheck] = {}
        self._components: dict[str, Any] = {}
        self._component_checks: dict[str, set[str]] = {}
        self._check_components: dict[str, str] = {}
    
    def register_component(self, component_id: str, component: Any) -> None:
        """
        Register a component for health monitoring.
        
        Args:
            component_id: Unique identifier for the component
            component: The component object
        """
        self._components[component_id] = component
        if component_id not in self._component_checks:
            self._component_checks[component_id] = set()
    
    def unregister_component(self, component_id: str) -> None:
        """
        Remove a component from health monitoring.
        
        Args:
            component_id: The ID of the component to remove
        """
        if component_id in self._components:
            del self._components[component_id]
        
        # Remove component from check associations
        if component_id in self._component_checks:
            check_ids = list(self._component_checks[component_id])
            for check_id in check_ids:
                self.unregister_check(check_id)
            del self._component_checks[component_id]
    
    def register_check(self, check: HealthCheck) -> None:
        """
        Register a health check with the registry.
        
        Args:
            check: The health check to register
        """
        check_id = check.check_id
        component_id = check.component_id
        
        self._checks[check_id] = check
        self._check_components[check_id] = component_id
        
        # Associate check with component
        if component_id not in self._component_checks:
            self._component_checks[component_id] = set()
        self._component_checks[component_id].add(check_id)
    
    def unregister_check(self, check_id: str) -> None:
        """
        Remove a health check from the registry.
        
        Args:
            check_id: The ID of the check to remove
        """
        if check_id in self._checks:
            component_id = self._check_components[check_id]
            
            # Remove from maps
            del self._checks[check_id]
            del self._check_components[check_id]
            
            # Remove from component association
            if component_id in self._component_checks:
                if check_id in self._component_checks[component_id]:
                    self._component_checks[component_id].remove(check_id)
    
    def get_check(self, check_id: str) -> Optional[HealthCheck]:
        """
        Get a health check by ID.
        
        Args:
            check_id: The ID of the check to retrieve
        
        Returns:
            The health check or None if not found
        """
        return self._checks.get(check_id)
    
    def get_component(self, component_id: str) -> Optional[Any]:
        """
        Get a component by ID.
        
        Args:
            component_id: The ID of the component to retrieve
        
        Returns:
            The component or None if not found
        """
        return self._components.get(component_id)
    
    def get_component_checks(self, component_id: str) -> list[HealthCheck]:
        """
        Get all health checks for a specific component.
        
        Args:
            component_id: The ID of the component
        
        Returns:
            List of health checks for the component
        """
        if component_id not in self._component_checks:
            return []
        
        return [self._checks[check_id] for check_id in self._component_checks[component_id]
                if check_id in self._checks]
    
    def get_all_checks(self) -> list[HealthCheck]:
        """
        Get all registered health checks.
        
        Returns:
            List of all health checks
        """
        return list(self._checks.values())
    
    def get_all_components(self) -> dict[str, Any]:
        """
        Get all registered components.
        
        Returns:
            Dictionary mapping component IDs to components
        """
        return dict(self._components)


# Global instance for singleton access
_health_registry = HealthRegistry()

def get_health_registry() -> HealthRegistry:
    """Get the global health registry instance."""
    return _health_registry

def register_component(component_id: str, component: Any) -> None:
    """Register a component with the global registry."""
    get_health_registry().register_component(component_id, component)

def register_check(check: HealthCheck) -> None:
    """Register a health check with the global registry."""
    get_health_registry().register_check(check)


def health_check(component_id: str, check_id: Optional[str] = None, 
                description: str = "", **kwargs) -> Callable:
    """
    Decorator for registering a method as a health check.
    
    This decorator converts a method to a health check and registers it.
    The method should return a tuple of (status, message, details_dict).
    
    Args:
        component_id: ID of the component this check is for
        check_id: Optional unique ID for this check (default: method name)
        description: Human-readable description of what this check does
        **kwargs: Additional arguments for the health check
    
    Returns:
        Decorator function
    """
    def decorator(func):
        func_check_id = check_id or f"{component_id}.{func.__name__}"
        
        # Define a wrapper that sets up the health check
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Call the original method
            return func(self, *args, **kwargs)
        
        # Create a health check adapter class
        class MethodHealthCheck(HealthCheck):
            def __init__(self, instance):
                super().__init__(func_check_id, component_id, description)
                self.instance = instance
                self.__dict__.update(kwargs)
            
            def execute(self):
                try:
                    status, message, details = func(self.instance)
                    return self.create_result(status, message, **details)
                except Exception as e:
                    logger.exception(f"Error in health check {self.check_id}: {e}")
                    from neuroca.core.health.monitor import HealthCheckStatus
                    return self.create_result(
                        HealthCheckStatus.ERROR,
                        f"Health check failed with error: {str(e)}",
                        error=str(e),
                        error_type=type(e).__name__
                    )
        
        # Store the health check class on the method for later use
        wrapper.health_check_class = MethodHealthCheck
        
        return wrapper
    
    return decorator


def register_component_checks(component_id: str, instance: Any) -> None:
    """
    Register all health check methods on a component instance.
    
    This function finds all methods decorated with @health_check and
    registers them as health checks for the component.
    
    Args:
        component_id: The ID of the component
        instance: The component instance
    """
    for _name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
        if hasattr(method, 'health_check_class'):
            # Create a health check from the decorated method
            check_class = method.health_check_class
            check = check_class(instance)
            
            # Register the check
            register_check(check)
            logger.debug(f"Registered health check {check.check_id} for component {component_id}")
    
    # Register the component itself
    register_component(component_id, instance) 