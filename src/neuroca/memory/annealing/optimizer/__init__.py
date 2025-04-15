"""
Annealing Memory Optimizer Package

This package implements a simulated annealing optimization approach for memory consolidation
and optimization within the NeuroCognitive Architecture. It provides mechanisms to:
1. Optimize memory representations through simulated annealing
2. Consolidate related memory fragments
3. Prune less relevant memories based on configurable criteria
4. Adjust memory weights and connections based on usage patterns

The optimizer follows biological principles of memory consolidation during rest/sleep
periods, implementing a temperature-based annealing schedule that gradually stabilizes
important memories while allowing for exploration of memory space early in the process.
"""

from neuroca.memory.annealing.optimizer.types import OptimizationStrategy, OptimizationMetric
from neuroca.memory.annealing.optimizer.stats import OptimizationStats
from neuroca.memory.annealing.optimizer.core import AnnealingOptimizer
from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.exponential import ExponentialAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.linear import LinearAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.adaptive import AdaptiveAnnealingSchedule
from neuroca.memory.annealing.optimizer.factory import create_optimizer

# Re-export components for backward compatibility
__all__ = [
    'OptimizationStrategy',
    'OptimizationMetric',
    'OptimizationStats',
    'AnnealingSchedule',
    'ExponentialAnnealingSchedule',
    'LinearAnnealingSchedule',
    'AdaptiveAnnealingSchedule',
    'AnnealingOptimizer',
    'create_optimizer'
]
