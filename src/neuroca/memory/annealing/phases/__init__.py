"""
Memory Annealing Phases Package

This package defines the different phases of memory annealing in the NeuroCognitive Architecture.
Memory annealing is a process inspired by metallurgical annealing, where memories are consolidated,
strengthened, or weakened based on various factors including recency, importance, and relevance.

The module provides:
1. Base class for annealing phases
2. Concrete implementations of different annealing phases
3. Phase transition logic and scheduling
4. Configuration parameters for each phase
"""

from neuroca.memory.annealing.phases.types import PhaseType
from neuroca.memory.annealing.phases.config import PhaseConfig
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.annealing.phases.heating import HeatingPhase
from neuroca.memory.annealing.phases.rapid_cooling import RapidCoolingPhase
from neuroca.memory.annealing.phases.slow_cooling import SlowCoolingPhase
from neuroca.memory.annealing.phases.stabilization import StabilizationPhase
from neuroca.memory.annealing.phases.maintenance import MaintenancePhase
from neuroca.memory.annealing.phases.custom import CustomPhase
from neuroca.memory.annealing.phases.factory import AnnealingPhaseFactory

# Re-export all components for backward compatibility
__all__ = [
    'PhaseType',
    'PhaseConfig',
    'AnnealingPhase',
    'HeatingPhase',
    'RapidCoolingPhase',
    'SlowCoolingPhase',
    'StabilizationPhase',
    'MaintenancePhase',
    'CustomPhase',
    'AnnealingPhaseFactory'
]
