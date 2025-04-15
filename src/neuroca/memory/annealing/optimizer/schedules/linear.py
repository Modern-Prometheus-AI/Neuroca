"""
Linear Annealing Schedule Module

This module provides the LinearAnnealingSchedule class that implements a linear cooling schedule.
"""

import logging
from neuroca.core.exceptions import ValidationError
from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule

# Configure logger
logger = logging.getLogger(__name__)


class LinearAnnealingSchedule(AnnealingSchedule):
    """
    Linear cooling schedule for simulated annealing.
    
    Temperature decreases linearly from start_temp to end_temp.
    """
    
    def __init__(self, start_temp: float = 1.0, end_temp: float = 0.01):
        """
        Initialize linear annealing schedule.
        
        Args:
            start_temp: Starting temperature (default: 1.0)
            end_temp: Ending temperature (default: 0.01)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if start_temp <= 0 or end_temp <= 0:
            raise ValidationError("Temperatures must be positive")
        if start_temp <= end_temp:
            raise ValidationError("Start temperature must be greater than end temperature")
            
        self.start_temp = start_temp
        self.end_temp = end_temp
        
        logger.debug(
            f"Initialized LinearAnnealingSchedule with "
            f"start_temp={start_temp}, end_temp={end_temp}"
        )
        
    def get_temperature(self, step: int, max_steps: int) -> float:
        """
        Calculate temperature using linear interpolation.
        
        Args:
            step: Current step number (0-indexed)
            max_steps: Total number of steps in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        # Call the parent method for validation
        super().get_temperature(step, max_steps)
        
        if max_steps <= 1:
            return self.end_temp
            
        progress = min(1.0, step / (max_steps - 1))
        return self.start_temp - progress * (self.start_temp - self.end_temp)
