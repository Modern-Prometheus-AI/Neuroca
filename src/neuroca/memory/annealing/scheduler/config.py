"""
Scheduler Configuration Module

This module provides the SchedulerConfig dataclass for representing annealing scheduler configurations.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from neuroca.memory.annealing.scheduler.types import SchedulerType


@dataclass
class SchedulerConfig:
    """Configuration parameters for creating annealing schedulers."""
    scheduler_type: SchedulerType
    start_temp: float
    end_temp: Optional[float] = None
    max_steps: Optional[int] = None
    decay_rate: Optional[float] = None
    c: Optional[float] = None
    target_acceptance: Optional[float] = None
    adjustment_rate: Optional[float] = None
    history_window: Optional[int] = None
    temp_func: Optional[Callable[[int], float]] = None
    min_temp: float = 1e-6
