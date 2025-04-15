"""
Optimization Types and Enumerations

This module defines the enumerations of available optimization strategies and metrics
used in the annealing memory optimizer.
"""

from enum import Enum, auto


class OptimizationStrategy(Enum):
    """Enumeration of available optimization strategies."""
    STANDARD = auto()     # Balanced approach with equal weights
    AGGRESSIVE = auto()   # Prioritizes reducing redundancy
    CONSERVATIVE = auto() # Prioritizes maintaining relevance
    ADAPTIVE = auto()     # Adjusts weights based on current state


class OptimizationMetric(Enum):
    """Enumeration of metrics used to evaluate optimization quality."""
    ENERGY = auto()         # Overall energy (cost) function
    COHERENCE = auto()      # Memory coherence/consistency
    RELEVANCE = auto()      # Memory importance/relevance
    COMPRESSION = auto()    # Memory size reduction
    RETRIEVAL_SPEED = auto() # Speed of memory retrieval
