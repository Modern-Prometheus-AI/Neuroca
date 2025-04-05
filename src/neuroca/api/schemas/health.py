"""
Pydantic Schemas for Health API Responses.

These schemas define the structure of data returned by the health API endpoints,
particularly for detailed health status incorporating dynamics like energy, fatigue,
and component states.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

# Import enums from the dynamics module to ensure consistency
from neuroca.core.health.dynamics import HealthEventType, HealthParameterType, HealthState


class HealthParameterSchema(BaseModel):
    """Schema representing a tracked health parameter."""
    name: str = Field(..., description="Name of the parameter")
    type: HealthParameterType = Field(..., description="Type of health parameter")
    value: float = Field(..., description="Current value of the parameter")
    min_value: float = Field(..., description="Minimum healthy value")
    max_value: float = Field(..., description="Maximum healthy value")
    optimal_value: Optional[float] = Field(None, description="Ideal value for peak performance")
    decay_rate: float = Field(..., description="Rate of natural decay")
    recovery_rate: float = Field(..., description="Rate of natural recovery")
    last_updated: datetime = Field(..., description="Timestamp of the last update")
    is_optimal: bool = Field(..., description="Whether the parameter is currently within the optimal range")

    class Config:
        use_enum_values = True # Serialize enums as their string values


class HealthEventSchema(BaseModel):
    """Schema representing a health-related event."""
    event_type: HealthEventType = Field(..., description="Type of health event")
    component_id: str = Field(..., description="ID of the component where the event occurred")
    parameter_name: Optional[str] = Field(None, description="Name of the parameter involved, if applicable")
    old_value: Optional[Any] = Field(None, description="Previous value, if applicable")
    new_value: Optional[Any] = Field(None, description="New value, if applicable")
    timestamp: datetime = Field(..., description="Timestamp when the event occurred")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional event details")

    class Config:
        use_enum_values = True # Serialize enums as their string values


class DetailedComponentHealthSchema(BaseModel):
    """Schema for detailed health status of a single component, including dynamics."""
    component_id: str = Field(..., description="Unique identifier for the component")
    status: HealthState = Field(..., description="Current overall health state of the component")
    parameters: dict[str, HealthParameterSchema] = Field(..., description="Tracked health parameters and their current values")
    recent_events: list[HealthEventSchema] = Field(..., description="List of recent health events for this component")
    last_state_change: datetime = Field(..., description="Timestamp of the last state change")

    class Config:
        use_enum_values = True # Serialize enums as their string values

# It might be useful to keep the existing ResourceUtilization and MemoryTierHealth
# schemas from routes/health.py here as well for consistency, or import them.
# For now, defining only the new/changed ones.
