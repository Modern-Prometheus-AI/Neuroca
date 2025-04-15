"""
Scheduler Type Definitions

This module defines the enumeration of available annealing scheduler types.
"""

from enum import Enum, auto


class SchedulerType(Enum):
    """Enumeration of available annealing scheduler types."""
    LINEAR = auto()
    EXPONENTIAL = auto()
    LOGARITHMIC = auto()
    COSINE = auto()
    ADAPTIVE = auto()
    CUSTOM = auto()
