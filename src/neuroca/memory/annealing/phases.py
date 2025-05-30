"""
Memory Annealing Phases Module (Import Redirection)

This module redirects imports to the new modular implementation in the phases package.
This maintains backward compatibility with existing code that imports from this module.

Original module description:
Memory Annealing Phases Module.

This module defines the different phases of memory annealing in the NeuroCognitive Architecture.
Memory annealing is a process inspired by metallurgical annealing, where memories are consolidated,
strengthened, or weakened based on various factors including recency, importance, and relevance.
"""

# Re-export all components from the phases package
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
