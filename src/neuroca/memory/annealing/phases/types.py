"""
Phase Type Definitions

This module defines the enumeration of available annealing phase types.
"""

import enum


class PhaseType(enum.Enum):
    """Enumeration of available annealing phase types."""
    
    HEATING = "heating"
    RAPID_COOLING = "rapid_cooling"
    SLOW_COOLING = "slow_cooling"
    STABILIZATION = "stabilization"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"
