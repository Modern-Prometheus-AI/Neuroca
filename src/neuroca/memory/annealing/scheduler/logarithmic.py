"""
Logarithmic Annealing Scheduler

This module provides the LogarithmicScheduler class that implements a logarithmic cooling schedule.
"""

import logging
import math
from neuroca.memory.annealing.scheduler.core import AnnealingScheduler

logger = logging.getLogger(__name__)


class LogarithmicScheduler(AnnealingScheduler):
    """
    Logarithmic cooling schedule that decreases temperature logarithmically.
    
    The temperature follows the formula: T(step) = start_temp / (1 + c * log(1 + step))
    """
    
    def __init__(self, start_temp: float, c: float = 1.0, min_temp: float = 1e-6):
        """
        Initialize a logarithmic cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            c: The cooling coefficient (controls cooling speed)
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.c = c
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate logarithmic scheduler parameters."""
        if self.c <= 0:
            raise ValueError("Cooling coefficient must be positive")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using logarithmic cooling.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        temp = self.start_temp / (1 + self.c * math.log(1 + step))
        return max(temp, self.min_temp)
