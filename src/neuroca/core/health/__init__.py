"""
Health monitoring and regulation system for the NeuroCognitive Architecture.

This module implements biologically-inspired health dynamics including:
- Component status tracking for system health monitoring
- Energy management for tracking resource usage across operations
- Attention allocation for focus and distraction mechanisms
- Homeostatic regulation for system stability
- Metrics collection for comprehensive health monitoring

The health system provides feedback loops that regulate cognitive processes
based on available resources, current load, and system priorities, similar
to biological systems that maintain homeostasis.
"""

# Import key components for easier access
from neuroca.core.health.component import ComponentStatus, ComponentHealthStatus, ComponentHealthMetrics
from neuroca.core.health.monitor import (
    HealthMonitor, HealthCheck, HealthCheckResult, HealthCheckStatus, 
    get_health_monitor, get_health_report, register_health_check, run_health_check,
    MemoryHealthCheck
)
from neuroca.core.health.registry import (
    HealthRegistry, get_health_registry, register_component, register_check,
    health_check, register_component_checks
)
from neuroca.core.health.dynamics import (
    HealthParameterType, HealthState, HealthEventType, HealthParameter,
    HealthEvent, ComponentHealth, HealthDynamicsManager, get_health_dynamics,
    register_component_for_health_tracking, record_cognitive_operation
)

__all__ = [
    # Component status
    'ComponentStatus',
    'ComponentHealthStatus',
    'ComponentHealthMetrics',
    
    # Health checks and monitoring
    'HealthCheck',
    'HealthCheckResult',
    'HealthCheckStatus',
    'HealthMonitor',
    'MemoryHealthCheck',
    
    # Registry management
    'HealthRegistry',
    
    # Health dynamics
    'HealthParameterType',
    'HealthState',
    'HealthEventType',
    'HealthParameter',
    'HealthEvent',
    'ComponentHealth',
    'HealthDynamicsManager',
    
    # Utility functions
    'get_health_monitor',
    'get_health_registry',
    'get_health_dynamics',
    'get_health_report',
    'register_component',
    'register_check',
    'register_health_check',
    'run_health_check',
    'health_check',
    'register_component_checks',
    'register_component_for_health_tracking',
    'record_cognitive_operation',
] 