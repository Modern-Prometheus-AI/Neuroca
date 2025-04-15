"""
Annealing Schedules Package

This package provides temperature scheduling functionality for simulated annealing processes
in the memory optimizer. It defines various cooling schedules that control how the
"temperature" parameter decreases over time during annealing.
"""

from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.exponential import ExponentialAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.linear import LinearAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.adaptive import AdaptiveAnnealingSchedule

__all__ = [
    'AnnealingSchedule',
    'ExponentialAnnealingSchedule',
    'LinearAnnealingSchedule',
    'AdaptiveAnnealingSchedule'
]
