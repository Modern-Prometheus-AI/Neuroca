"""
Scheduler Factory Module

This module provides the SchedulerFactory class and convenience functions
for creating annealing scheduler instances.
"""

import logging
from typing import Type

from neuroca.memory.annealing.scheduler.types import SchedulerType
from neuroca.memory.annealing.scheduler.core import AnnealingScheduler
from neuroca.memory.annealing.scheduler.linear import LinearScheduler
from neuroca.memory.annealing.scheduler.exponential import ExponentialScheduler
from neuroca.memory.annealing.scheduler.logarithmic import LogarithmicScheduler
from neuroca.memory.annealing.scheduler.cosine import CosineScheduler
from neuroca.memory.annealing.scheduler.adaptive import AdaptiveScheduler
from neuroca.memory.annealing.scheduler.custom import CustomScheduler
from neuroca.memory.annealing.scheduler.config import SchedulerConfig

logger = logging.getLogger(__name__)


class SchedulerFactory:
    """
    Factory class for creating annealing schedulers.
    
    This factory simplifies the creation of different scheduler types
    based on configuration parameters.
    """
    
    @staticmethod
    def create_scheduler(config: SchedulerConfig) -> AnnealingScheduler:
        """
        Create an annealing scheduler based on the provided configuration.
        
        Args:
            config: Configuration parameters for the scheduler
            
        Returns:
            An instance of the specified scheduler type
            
        Raises:
            ValueError: If the configuration is invalid for the specified scheduler type
        """
        try:
            if config.scheduler_type == SchedulerType.LINEAR:
                if config.end_temp is None or config.max_steps is None:
                    raise ValueError("Linear scheduler requires end_temp and max_steps")
                return LinearScheduler(
                    start_temp=config.start_temp,
                    end_temp=config.end_temp,
                    max_steps=config.max_steps,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.EXPONENTIAL:
                if config.decay_rate is None:
                    raise ValueError("Exponential scheduler requires decay_rate")
                return ExponentialScheduler(
                    start_temp=config.start_temp,
                    decay_rate=config.decay_rate,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.LOGARITHMIC:
                c = config.c if config.c is not None else 1.0
                return LogarithmicScheduler(
                    start_temp=config.start_temp,
                    c=c,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.COSINE:
                if config.end_temp is None or config.max_steps is None:
                    raise ValueError("Cosine scheduler requires end_temp and max_steps")
                return CosineScheduler(
                    start_temp=config.start_temp,
                    end_temp=config.end_temp,
                    max_steps=config.max_steps,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.ADAPTIVE:
                target = config.target_acceptance if config.target_acceptance is not None else 0.4
                adj_rate = config.adjustment_rate if config.adjustment_rate is not None else 0.1
                history = config.history_window if config.history_window is not None else 100
                return AdaptiveScheduler(
                    start_temp=config.start_temp,
                    target_acceptance=target,
                    adjustment_rate=adj_rate,
                    history_window=history,
                    min_temp=config.min_temp
                )
                
            elif config.scheduler_type == SchedulerType.CUSTOM:
                if config.temp_func is None:
                    raise ValueError("Custom scheduler requires a temperature function")
                return CustomScheduler(
                    temp_func=config.temp_func,
                    start_temp=config.start_temp,
                    min_temp=config.min_temp
                )
                
            else:
                raise ValueError(f"Unknown scheduler type: {config.scheduler_type}")
                
        except Exception as e:
            logger.error(f"Failed to create scheduler: {str(e)}")
            raise ValueError(f"Failed to create scheduler: {str(e)}") from e


# Convenience functions for common scheduler configurations
def create_linear_scheduler(
    start_temp: float, 
    end_temp: float, 
    max_steps: int,
    min_temp: float = 1e-6
) -> LinearScheduler:
    """
    Create a linear cooling schedule.
    
    Args:
        start_temp: The initial temperature value
        end_temp: The final temperature value
        max_steps: The total number of steps in the schedule
        min_temp: The minimum temperature value
        
    Returns:
        A configured LinearScheduler instance
    """
    return LinearScheduler(start_temp, end_temp, max_steps, min_temp)


def create_exponential_scheduler(
    start_temp: float, 
    decay_rate: float,
    min_temp: float = 1e-6
) -> ExponentialScheduler:
    """
    Create an exponential cooling schedule.
    
    Args:
        start_temp: The initial temperature value
        decay_rate: The rate at which temperature decreases (between 0 and 1)
        min_temp: The minimum temperature value
        
    Returns:
        A configured ExponentialScheduler instance
    """
    return ExponentialScheduler(start_temp, decay_rate, min_temp)


def create_adaptive_scheduler(
    start_temp: float, 
    target_acceptance: float = 0.4,
    min_temp: float = 1e-6
) -> AdaptiveScheduler:
    """
    Create an adaptive cooling schedule.
    
    Args:
        start_temp: The initial temperature value
        target_acceptance: The target acceptance rate (between 0 and 1)
        min_temp: The minimum temperature value
        
    Returns:
        A configured AdaptiveScheduler instance
    """
    return AdaptiveScheduler(start_temp, target_acceptance, min_temp=min_temp)
