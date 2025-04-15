"""
Rapid Cooling Phase Module

This module implements the rapid cooling phase of memory annealing.
"""

import logging
import math
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class RapidCoolingPhase(AnnealingPhase):
    """Rapid cooling phase of memory annealing.
    
    This phase rapidly decreases temperature, quickly solidifying memory structures.
    It's useful for preserving important insights or patterns discovered during
    the heating phase, but may result in suboptimal memory organization.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement rapid temperature decrease.
        
        Returns:
            The updated temperature value
        """
        # Exponential cooling function for rapid decrease
        cooling_factor = math.exp(-5 * self.phase_progress)
        temp_range = self.config.max_temperature - self.config.min_temperature
        
        self.current_temp = self.config.min_temperature + temp_range * cooling_factor
        
        logger.debug(
            "Rapid cooling phase: progress=%.2f, temperature=%.3f, cooling_factor=%.3f",
            self.phase_progress,
            self.current_temp,
            cooling_factor
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during rapid cooling phase.
        
        In rapid cooling, strong memories are preserved while weak ones may be
        rapidly forgotten. This creates a more focused but potentially less nuanced
        memory structure.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Decrease malleability rapidly
        if hasattr(memory, "malleability"):
            memory.malleability = max(0.0, memory.malleability - (0.2 * (1 - self.current_temp)))
        
        # Apply threshold-based consolidation
        if hasattr(memory, "strength"):
            if memory.strength > self.config.consolidation_threshold:
                # Strengthen memories above threshold
                memory.strength = min(1.0, memory.strength + (0.1 * (1 - self.current_temp)))
            else:
                # Weaken memories below threshold
                memory.strength = max(0.0, memory.strength - (0.15 * (1 - self.current_temp)))
        
        return memory
