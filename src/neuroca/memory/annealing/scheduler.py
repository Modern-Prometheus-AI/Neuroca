"""
Annealing Temperature Scheduler for Memory Optimization (Import Redirection)

This module redirects imports to the new modular implementation in the scheduler package.
This maintains backward compatibility with existing code that imports from this module.

Original module description:
This module provides temperature scheduling functionality for simulated annealing processes
in the NeuroCognitive Architecture memory system. It implements various cooling schedules
that control how the "temperature" parameter decreases over time during annealing.
"""

# Re-export all scheduler components from the scheduler package
from neuroca.memory.annealing.scheduler.types import SchedulerType
from neuroca.memory.annealing.scheduler.core import AnnealingScheduler
from neuroca.memory.annealing.scheduler.linear import LinearScheduler
from neuroca.memory.annealing.scheduler.exponential import ExponentialScheduler
from neuroca.memory.annealing.scheduler.logarithmic import LogarithmicScheduler
from neuroca.memory.annealing.scheduler.cosine import CosineScheduler
from neuroca.memory.annealing.scheduler.adaptive import AdaptiveScheduler
from neuroca.memory.annealing.scheduler.custom import CustomScheduler
from neuroca.memory.annealing.scheduler.config import SchedulerConfig
from neuroca.memory.annealing.scheduler.factory import (
    SchedulerFactory,
    create_linear_scheduler,
    create_exponential_scheduler,
    create_adaptive_scheduler
)

# Export all components for backward compatibility
__all__ = [
    'SchedulerType',
    'AnnealingScheduler',
    'LinearScheduler',
    'ExponentialScheduler',
    'LogarithmicScheduler',
    'CosineScheduler',
    'AdaptiveScheduler',
    'CustomScheduler',
    'SchedulerConfig',
    'SchedulerFactory',
    'create_linear_scheduler',
    'create_exponential_scheduler',
    'create_adaptive_scheduler'
]
