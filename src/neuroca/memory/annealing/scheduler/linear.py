"""
Linear Annealing Scheduler

This module provides the LinearScheduler class that implements a linear cooling schedule.
"""

import logging
from neuroca.memory.annealing.scheduler.core import AnnealingScheduler

logger = logging.getLogger(__name__)


class LinearScheduler(AnnealingScheduler):
    """
    Linear cooling schedule that decreases temperature linearly from start_temp to end_temp.
    
    The temperature follows the formula: T(step) = start_temp - step * (start_temp - end_temp) / max_steps
    """
    
    def __init__(self, start_temp: float, end_temp: float, max_steps: int, min_temp: float = 1e-6):
        """
        Initialize a linear cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            end_temp: The final temperature value
            max_steps: The total number of steps in the schedule
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.end_temp = max(end_temp, min_temp)
        self.max_steps = max_steps
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate linear scheduler parameters."""
        if self.end_temp > self.start_temp:
            raise ValueError("End temperature must be less than or equal to start temperature")
        if self.max_steps <= 0:
            raise ValueError("Maximum steps must be positive")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using linear cooling.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        if step >= self.max_steps:
            return self.end_temp
            
        temp = self.start_temp - step * (self.start_temp - self.end_temp) / self.max_steps
        return max(temp, self.min_temp)
