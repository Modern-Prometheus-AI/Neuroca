"""
Custom Annealing Scheduler

This module provides the CustomScheduler class that uses a user-provided function for temperature scheduling.
"""

import logging
from typing import Callable
from neuroca.memory.annealing.scheduler.core import AnnealingScheduler

logger = logging.getLogger(__name__)


class CustomScheduler(AnnealingScheduler):
    """
    Custom cooling schedule using a user-provided temperature function.
    
    This scheduler allows for arbitrary temperature schedules by accepting
    a custom function that calculates temperature based on step number.
    """
    
    def __init__(
        self, 
        temp_func: Callable[[int], float], 
        start_temp: float,
        min_temp: float = 1e-6
    ):
        """
        Initialize a custom cooling schedule.
        
        Args:
            temp_func: A function that takes a step number and returns a temperature
            start_temp: The initial temperature value (used for validation)
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.temp_func = temp_func
        
        # Validate that the function returns expected values
        try:
            test_temp = self.temp_func(0)
            if not isinstance(test_temp, (int, float)):
                raise ValueError("Temperature function must return a numeric value")
            if test_temp < 0:
                raise ValueError("Temperature function must return non-negative values")
        except Exception as e:
            raise ValueError(f"Invalid temperature function: {str(e)}")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using the custom function.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        
        Raises:
            ValueError: If step is negative or the temperature function fails
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        try:
            temp = self.temp_func(step)
            return max(temp, self.min_temp)
        except Exception as e:
            logger.error(f"Error in custom temperature function: {str(e)}")
            # Return minimum temperature as fallback
            return self.min_temp
