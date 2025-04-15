"""
Annealing Scheduler Core Module

This module provides the abstract base class for annealing temperature schedulers.
All concrete scheduler implementations inherit from this class.
"""

import logging
from abc import ABC, abstractmethod

# Configure logger
logger = logging.getLogger(__name__)


class AnnealingScheduler(ABC):
    """
    Abstract base class for annealing temperature schedulers.
    
    All concrete scheduler implementations should inherit from this class
    and implement the get_temperature method.
    """
    
    def __init__(self, start_temp: float, min_temp: float = 1e-6):
        """
        Initialize the annealing scheduler.
        
        Args:
            start_temp: The initial temperature value (must be positive)
            min_temp: The minimum temperature value to prevent numerical issues
        
        Raises:
            ValueError: If start_temp is not positive or min_temp is negative
        """
        if start_temp <= 0:
            raise ValueError("Starting temperature must be positive")
        if min_temp < 0:
            raise ValueError("Minimum temperature cannot be negative")
            
        self.start_temp = start_temp
        self.min_temp = min_temp
        self._validate_parameters()
        logger.debug(f"Initialized {self.__class__.__name__} with start_temp={start_temp}, min_temp={min_temp}")
    
    @abstractmethod
    def get_temperature(self, step: int) -> float:
        """
        Calculate the temperature for the given step.
        
        Args:
            step: The current step in the annealing process (0-indexed)
            
        Returns:
            The temperature value for the current step
        """
        pass
    
    def _validate_parameters(self) -> None:
        """
        Validate scheduler-specific parameters.
        
        This method should be overridden by subclasses to perform additional
        parameter validation beyond the basic checks in __init__.
        
        Raises:
            ValueError: If any parameters are invalid
        """
        pass
    
    def reset(self) -> None:
        """
        Reset the scheduler to its initial state.
        
        This method should be overridden by subclasses that maintain internal state.
        """
        pass
