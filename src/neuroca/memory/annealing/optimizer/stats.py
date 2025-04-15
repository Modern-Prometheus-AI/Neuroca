"""
Optimization Statistics Module

This module provides the OptimizationStats dataclass for tracking and analyzing
the results of memory optimization operations.
"""

from dataclasses import dataclass
from typing import Any, List


@dataclass
class OptimizationStats:
    """Statistics collected during the optimization process."""
    
    initial_energy: float
    final_energy: float
    iterations: int
    accepted_moves: int
    rejected_moves: int
    duration_seconds: float
    temperature_history: List[float]
    energy_history: List[float]
    
    @property
    def acceptance_ratio(self) -> float:
        """Calculate the ratio of accepted moves to total iterations."""
        if self.iterations == 0:
            return 0.0
        return self.accepted_moves / self.iterations
    
    @property
    def energy_reduction(self) -> float:
        """Calculate the percentage of energy reduction."""
        if self.initial_energy == 0:
            return 0.0
        return (self.initial_energy - self.final_energy) / self.initial_energy * 100
    
    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary for serialization."""
        return {
            "initial_energy": self.initial_energy,
            "final_energy": self.final_energy,
            "iterations": self.iterations,
            "accepted_moves": self.accepted_moves,
            "rejected_moves": self.rejected_moves,
            "duration_seconds": self.duration_seconds,
            "acceptance_ratio": self.acceptance_ratio,
            "energy_reduction": self.energy_reduction
        }
