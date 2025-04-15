"""
Heating Phase Module

This module implements the heating phase of memory annealing.
"""

import logging
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class HeatingPhase(AnnealingPhase):
    """Heating phase of memory annealing.
    
    During this phase, the temperature increases, making memories more volatile
    and susceptible to change. This phase is typically used to prepare memories
    for reorganization or to break down rigid memory structures.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement temperature increase for heating phase.
        
        Returns:
            The updated temperature value
        """
        # Calculate target temperature based on progress
        target_temp = min(
            self.config.max_temperature,
            self.config.min_temperature + 
            (self.config.max_temperature - self.config.min_temperature) * self.phase_progress
        )
        
        # Gradually move current temperature toward target
        temp_diff = target_temp - self.current_temp
        self.current_temp += temp_diff * self.config.heating_rate
        
        logger.debug(
            "Heating phase: progress=%.2f, temperature=%.3f, target=%.3f",
            self.phase_progress,
            self.current_temp,
            target_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during heating phase.
        
        In the heating phase, memories become more malleable and connections
        between related memories may be strengthened or weakened.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Increase memory malleability based on temperature
        if hasattr(memory, "malleability"):
            memory.malleability = min(1.0, memory.malleability + (self.current_temp * 0.1))
        
        # Potentially strengthen important memories that should survive heating
        if hasattr(memory, "importance") and hasattr(memory, "strength"):
            if memory.importance > 0.7:  # Important memories
                # Strengthen important memories to counteract general decay
                reinforcement = self.config.reinforcement_factor * memory.importance
                memory.strength = min(1.0, memory.strength + reinforcement)
        
        return memory
