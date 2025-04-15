"""
Base Annealing Schedule Module

This module provides the abstract base class for annealing temperature schedulers
used in the memory optimization process.
"""

import logging
from abc import ABC, abstractmethod

from neuroca.core.exceptions import ValidationError

# Configure logger
logger = logging.getLogger(__name__)


class AnnealingSchedule(ABC):
    """
    Abstract base class for temperature scheduling in simulated annealing.
    
    This class defines the interface that all annealing schedule implementations
    must follow, ensuring a consistent API for temperature calculations.
    """
    
    @abstractmethod
    def get_temperature(self, step: int, max_steps: int) -> float:
        """
        Calculate the temperature for the current step.
        
        Args:
            step: Current step number (0-indexed)
            max_steps: Total number of steps in the annealing process
            
        Returns:
            The temperature value for the current step
        
        Raises:
            ValidationError: If step or max_steps parameters are invalid
        """
        if step < 0:
            raise ValidationError("Step cannot be negative")
        if max_steps <= 0:
            raise ValidationError("Maximum steps must be positive")
        if step >= max_steps:
            logger.warning(f"Step {step} exceeds max_steps {max_steps}")
        
        pass  # Implemented by subclasses
