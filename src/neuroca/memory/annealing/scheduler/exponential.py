"""
Exponential Annealing Scheduler

This module provides the ExponentialScheduler class that implements an exponential cooling schedule.
"""

import logging
from neuroca.memory.annealing.scheduler.core import AnnealingScheduler

logger = logging.getLogger(__name__)


class ExponentialScheduler(AnnealingScheduler):
    """
    Exponential cooling schedule that decreases temperature exponentially.
    
    The temperature follows the formula: T(step) = start_temp * (decay_rate ^ step)
    """
    
    def __init__(self, start_temp: float, decay_rate: float, min_temp: float = 1e-6):
        """
        Initialize an exponential cooling schedule.
        
        Args:
            start_temp: The initial temperature value
            decay_rate: The rate at which temperature decreases (between 0 and 1)
            min_temp: The minimum temperature value
            
        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(start_temp, min_temp)
        self.decay_rate = decay_rate
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate exponential scheduler parameters."""
        if not 0 < self.decay_rate < 1:
            raise ValueError("Decay rate must be between 0 and 1 (exclusive)")
    
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step using exponential cooling.
        
        Args:
            step: The current step in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        if step < 0:
            raise ValueError("Step cannot be negative")
            
        temp = self.start_temp * (self.decay_rate ** step)
        return max(temp, self.min_temp)
