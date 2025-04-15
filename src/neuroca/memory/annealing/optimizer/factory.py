"""
Optimizer Factory Module

This module provides factory functions for creating annealing optimizer instances
with different configurations.
"""

import logging
from typing import Any, Optional, Dict

from neuroca.core.exceptions import ValidationError
from neuroca.memory.annealing.optimizer.types import OptimizationStrategy
from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.exponential import ExponentialAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.linear import LinearAnnealingSchedule
from neuroca.memory.annealing.optimizer.schedules.adaptive import AdaptiveAnnealingSchedule
from neuroca.memory.annealing.optimizer.core import AnnealingOptimizer

# Configure logger
logger = logging.getLogger(__name__)


def create_optimizer(
    config: Optional[Dict[str, Any]] = None,
    strategy: str = "STANDARD",
    schedule_type: str = "exponential",
    **kwargs
) -> AnnealingOptimizer:
    """
    Factory function to create an annealing optimizer with the specified configuration.
    
    Args:
        config: Configuration dictionary (default: None, uses system settings)
        strategy: Optimization strategy name (default: "STANDARD")
        schedule_type: Annealing schedule type (default: "exponential")
        **kwargs: Additional parameters for the optimizer
        
    Returns:
        Configured AnnealingOptimizer instance
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Parse strategy
    try:
        opt_strategy = OptimizationStrategy[strategy.upper()]
    except KeyError:
        raise ValidationError(
            f"Invalid optimization strategy: {strategy}. "
            f"Valid options: {', '.join(s.name for s in OptimizationStrategy)}"
        )
    
    # Create annealing schedule
    schedule: AnnealingSchedule
    if schedule_type.lower() == "exponential":
        schedule_params = kwargs.get("schedule_params", {})
        schedule = ExponentialAnnealingSchedule(**schedule_params)
    elif schedule_type.lower() == "linear":
        schedule_params = kwargs.get("schedule_params", {})
        schedule = LinearAnnealingSchedule(**schedule_params)
    elif schedule_type.lower() == "adaptive":
        schedule_params = kwargs.get("schedule_params", {})
        schedule = AdaptiveAnnealingSchedule(**schedule_params)
    else:
        raise ValidationError(
            f"Invalid schedule type: {schedule_type}. "
            f"Valid options: exponential, linear, adaptive"
        )
    
    # Filter kwargs to only include valid parameters for AnnealingOptimizer
    valid_params = {
        k: v for k, v in kwargs.items() 
        if k in ["max_iterations", "early_stopping_threshold", 
                "early_stopping_iterations", "random_seed"]
    }
    
    return AnnealingOptimizer(
        config=config,
        annealing_schedule=schedule,
        strategy=opt_strategy,
        **valid_params
    )
