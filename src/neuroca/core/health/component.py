"""
Component status management for the NeuroCognitive Architecture health system.

This module provides the ComponentStatus class and related utilities for tracking
the health and operational status of different architecture components.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ComponentStatus(Enum):
    """
    Defines the possible operational statuses for system components.
    
    Status levels are biologically inspired, representing different states that
    a cognitive component might be in.
    """
    OPTIMAL = "optimal"        # Fully operational, all parameters within ideal ranges
    FUNCTIONAL = "functional"  # Working normally with acceptable parameters
    DEGRADED = "degraded"      # Working but with suboptimal performance
    STRAINED = "strained"      # Under stress, performance significantly reduced
    CRITICAL = "critical"      # Severe issues, barely operational
    FAILED = "failed"          # Component has ceased to function
    UNKNOWN = "unknown"        # Status cannot be determined


@dataclass
class ComponentHealthMetrics:
    """
    Holds health metrics for a component, tracking key biological-inspired measures.
    
    Attributes:
        resource_utilization: Percentage of available resources being used (0.0-1.0)
        energy_levels: Available energy for operations (0.0-1.0)
        response_time: Average operation response time in milliseconds
        error_rate: Proportion of operations resulting in errors (0.0-1.0)
        throughput: Operations processed per second
        saturation: How close the component is to capacity (0.0-1.0)
        last_updated: Timestamp of the last metrics update
    """
    component_id: str
    resource_utilization: float = 0.0
    energy_levels: float = 1.0
    response_time: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    saturation: float = 0.0
    last_updated: float = field(default_factory=time.time)
    custom_metrics: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate metrics are within expected ranges."""
        # Ensure percentage values are between 0.0 and 1.0
        for attr_name in ['resource_utilization', 'energy_levels', 'error_rate', 'saturation']:
            value = getattr(self, attr_name)
            if not 0.0 <= value <= 1.0:
                setattr(self, attr_name, max(0.0, min(1.0, value)))
    
    def update(self, **metrics):
        """Update metrics with new values."""
        for key, value in metrics.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif key != 'component_id':  # Don't update component_id
                self.custom_metrics[key] = value
        
        self.last_updated = time.time()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        result = {
            'component_id': self.component_id,
            'resource_utilization': self.resource_utilization,
            'energy_levels': self.energy_levels,
            'response_time': self.response_time,
            'error_rate': self.error_rate,
            'throughput': self.throughput,
            'saturation': self.saturation,
            'last_updated': self.last_updated
        }
        result.update(self.custom_metrics)
        return result


@dataclass
class ComponentHealthStatus:
    """
    Represents the current health status of a component with metrics and diagnostics.
    
    Attributes:
        component_id: Unique identifier for the component
        status: Current operational status
        metrics: Detailed metrics for the component
        issues: List of current issues affecting the component
        last_status_change: When the status last changed
    """
    component_id: str
    status: ComponentStatus = ComponentStatus.UNKNOWN
    metrics: ComponentHealthMetrics = None
    issues: list[str] = field(default_factory=list)
    last_status_change: float = field(default_factory=time.time)
    details: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metrics if not provided."""
        if self.metrics is None:
            self.metrics = ComponentHealthMetrics(component_id=self.component_id)
    
    def update_status(self, new_status: ComponentStatus, issue: Optional[str] = None):
        """
        Update the component status and record the change time.
        
        Args:
            new_status: The new status to set for the component
            issue: Optional issue description to record
        """
        if new_status != self.status:
            self.status = new_status
            self.last_status_change = time.time()
        
        if issue and issue not in self.issues:
            self.issues.append(issue)
    
    def resolve_issue(self, issue: str):
        """
        Remove an issue from the list of active issues.
        
        Args:
            issue: The issue to remove
        """
        if issue in self.issues:
            self.issues.remove(issue)
    
    def is_healthy(self) -> bool:
        """
        Check if the component is in a healthy state.
        
        Returns:
            True if the component is OPTIMAL or FUNCTIONAL, False otherwise
        """
        return self.status in [ComponentStatus.OPTIMAL, ComponentStatus.FUNCTIONAL]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert component health status to dictionary for serialization."""
        return {
            'component_id': self.component_id,
            'status': self.status.value,
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'issues': self.issues,
            'last_status_change': self.last_status_change,
            'details': self.details
        } 