"""
Annealing Temperature Scheduler Package

This package provides temperature scheduling functionality for simulated annealing processes,
with various cooling schedules to control how the "temperature" parameter decreases over time.

The scheduler components include:
- Base scheduler interface and abstract base class
- Various cooling schedule implementations (Linear, Exponential, etc.)
- Factory for creating schedulers
- Configuration utilities
"""

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

# Re-export all components for backward compatibility
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
