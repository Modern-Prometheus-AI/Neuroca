"""
Exponential Annealing Schedule Module

This module provides the ExponentialAnnealingSchedule class that implements an exponential cooling schedule.
"""

import logging
from neuroca.core.exceptions import ValidationError
from neuroca.memory.annealing.optimizer.schedules.base import AnnealingSchedule

# Configure logger
logger = logging.getLogger(__name__)


class ExponentialAnnealingSchedule(AnnealingSchedule):
    """
    Exponential cooling schedule for simulated annealing.
    
    Temperature decreases exponentially from start_temp to end_temp.
    """
    
    def __init__(self, start_temp: float = 1.0, end_temp: float = 0.01, decay: float = 0.95):
        """
        Initialize exponential annealing schedule.
        
        Args:
            start_temp: Starting temperature (default: 1.0)
            end_temp: Ending temperature (default: 0.01)
            decay: Exponential decay factor (default: 0.95)
        
        Raises:
            ValidationError: If parameters are invalid
        """
        if start_temp <= 0 or end_temp <= 0:
            raise ValidationError("Temperatures must be positive")
        if start_temp <= end_temp:
            raise ValidationError("Start temperature must be greater than end temperature")
        if decay <= 0 or decay >= 1:
            raise ValidationError("Decay must be between 0 and 1 exclusive")
            
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.decay = decay
        
        logger.debug(
            f"Initialized ExponentialAnnealingSchedule with "
            f"start_temp={start_temp}, end_temp={end_temp}, decay={decay}"
        )
        
    def get_temperature(self, step: int, max_steps: int) -> float:
        """
        Calculate temperature using exponential decay.
        
        Args:
            step: Current step number (0-indexed)
            max_steps: Total number of steps in the annealing process
            
        Returns:
            The temperature value for the current step
        """
        # Call the parent method for validation
        super().get_temperature(step, max_steps)
        
        # Calculate normalized progress
        progress = min(1.0, step / max_steps)
        
        # Calculate temperature using exponential decay
        temp = self.start_temp * (self.decay ** (progress * max_steps))
        
        # Ensure temperature doesn't drop below end_temp
        return max(temp, self.end_temp)
