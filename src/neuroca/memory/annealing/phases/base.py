"""
Base Annealing Phase Module

This module defines the abstract base class for all annealing phases.
"""

import abc
import logging
from datetime import datetime
from typing import Any

import numpy as np

from neuroca.core.exceptions import ConfigurationError
from neuroca.memory.annealing.phases.config import PhaseConfig
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class AnnealingPhase(abc.ABC):
    """Base abstract class for all annealing phases.
    
    This class defines the interface and common functionality for all annealing phases.
    Each phase has a temperature range, duration, and specific behavior for processing memories.
    """
    
    def __init__(self, initial_temp: float, config: PhaseConfig):
        """Initialize the annealing phase.
        
        Args:
            initial_temp: Starting temperature for this phase (0.0 to 1.0)
            config: Configuration parameters for this phase
            
        Raises:
            ConfigurationError: If the initial temperature is outside the valid range
                                or incompatible with the phase configuration
        """
        if not 0 <= initial_temp <= 1:
            raise ConfigurationError(f"Initial temperature {initial_temp} must be between 0 and 1")
        
        if initial_temp < config.min_temperature or initial_temp > config.max_temperature:
            raise ConfigurationError(
                f"Initial temperature {initial_temp} is outside the configured range "
                f"[{config.min_temperature}, {config.max_temperature}]"
            )
        
        self.current_temp = initial_temp
        self.config = config
        self.start_time = datetime.now()
        self.phase_complete = False
        
        logger.debug(
            "Initialized %s phase with temperature %.3f and config: %s",
            self.__class__.__name__,
            initial_temp,
            config
        )
    
    @property
    def elapsed_time(self) -> float:
        """Calculate the elapsed time since the phase started.
        
        Returns:
            Elapsed time in seconds
        """
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def phase_progress(self) -> float:
        """Calculate the progress of the phase as a percentage.
        
        Returns:
            Progress as a value between 0.0 and 1.0
        """
        progress = min(self.elapsed_time / self.config.duration_seconds, 1.0)
        return progress
    
    def update_temperature(self) -> float:
        """Update the current temperature based on phase-specific logic.
        
        This method must be implemented by concrete phase classes.
        
        Returns:
            The updated temperature value
        """
        if self.phase_progress >= 1.0:
            self.phase_complete = True
            
        return self._update_temperature_impl()
    
    @abc.abstractmethod
    def _update_temperature_impl(self) -> float:
        """Implementation of temperature update logic specific to each phase.
        
        Returns:
            The updated temperature value
        """
        pass
    
    def process_memory(self, memory: MemoryItem) -> MemoryItem:
        """Process a memory item according to the current phase and temperature.
        
        This method applies phase-specific transformations to the memory item,
        potentially modifying its strength, connections, or other attributes.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
            
        Raises:
            ValueError: If the memory item is invalid or incompatible with this phase
        """
        if not memory:
            raise ValueError("Cannot process None memory item")
        
        # Update temperature before processing
        self.update_temperature()
        
        # Apply common processing logic
        processed_memory = self._apply_common_processing(memory)
        
        # Apply phase-specific processing
        return self._process_memory_impl(processed_memory)
    
    def _apply_common_processing(self, memory: MemoryItem) -> MemoryItem:
        """Apply common processing logic to a memory item.
        
        This method handles processing steps that are common across all phases.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Create a copy to avoid modifying the original
        processed = memory.copy()
        
        # Apply temperature-based decay
        if hasattr(processed, "strength"):
            decay = self.config.decay_factor * self.current_temp
            processed.strength = max(0.0, processed.strength - decay)
        
        # Apply volatility effects (random fluctuations)
        if hasattr(processed, "strength"):
            volatility_effect = (np.random.random() - 0.5) * self.config.volatility * self.current_temp
            processed.strength = max(0.0, min(1.0, processed.strength + volatility_effect))
        
        return processed
    
    @abc.abstractmethod
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Implementation of memory processing logic specific to each phase.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        pass
    
    def is_complete(self) -> bool:
        """Check if the phase is complete.
        
        Returns:
            True if the phase is complete, False otherwise
        """
        return self.phase_complete or self.phase_progress >= 1.0
    
    def get_state(self) -> dict[str, Any]:
        """Get the current state of the phase.
        
        Returns:
            Dictionary containing the current state
        """
        return {
            "phase_type": self.__class__.__name__,
            "current_temperature": self.current_temp,
            "progress": self.phase_progress,
            "elapsed_time": self.elapsed_time,
            "is_complete": self.is_complete(),
            "config": {
                "duration_seconds": self.config.duration_seconds,
                "min_temperature": self.config.min_temperature,
                "max_temperature": self.config.max_temperature,
                "cooling_rate": self.config.cooling_rate,
                "heating_rate": self.config.heating_rate,
            }
        }
