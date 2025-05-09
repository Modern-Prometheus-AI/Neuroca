"""
Memory Annealing Optimizer for Memory Optimization (Import Redirection)

This module redirects imports to the new modular implementation in the optimizer package.
This maintains backward compatibility with existing code that imports from this module.

Original module description:
Simulated Annealing Memory Optimizer for NeuroCognitive Architecture.

This module implements a simulated annealing optimization approach for memory consolidation
and optimization within the NeuroCognitive Architecture. It provides mechanisms to:
1. Optimize memory representations through simulated annealing
2. Consolidate related memory fragments
3. Prune less relevant memories based on configurable criteria
4. Adjust memory weights and connections based on usage patterns
"""

# Re-export all optimizer components from the optimizer package
from neuroca.memory.annealing.optimizer.types import OptimizationStrategy, OptimizationMetric
from neuroca.memory.annealing.optimizer.stats import OptimizationStats
from neuroca.memory.annealing.optimizer.core import AnnealingOptimizer
from neuroca.memory.annealing.optimizer.factory import create_optimizer
from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.exponential import ExponentialAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.linear import LinearAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.adaptive import AdaptiveAnnealingSchedule

# Re-export components for backward compatibility
__all__ = [
    'AnnealingOptimizer',
    'OptimizationStrategy',
    'OptimizationMetric',
    'OptimizationStats',
    'AnnealingSchedule',
    'ExponentialAnnealingSchedule', 
    'LinearAnnealingSchedule',
    'AdaptiveAnnealingSchedule',
    'create_optimizer'
]
