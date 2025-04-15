"""
Slow Cooling Phase Module

This module implements the slow cooling phase of memory annealing.
"""

import logging
import math
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class SlowCoolingPhase(AnnealingPhase):
    """Slow cooling phase of memory annealing.
    
    This phase gradually decreases temperature, allowing for more optimal
    organization of memory structures. It balances between preserving important
    memories and allowing for some flexibility in memory organization.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement gradual temperature decrease.
        
        Returns:
            The updated temperature value
        """
        # Linear cooling with slight curve
        temp_range = self.config.max_temperature - self.config.min_temperature
        cooling_progress = math.pow(self.phase_progress, 1.2)  # Slightly curved cooling
        
        self.current_temp = self.config.max_temperature - (temp_range * cooling_progress)
        self.current_temp = max(self.current_temp, self.config.min_temperature)
        
        logger.debug(
            "Slow cooling phase: progress=%.2f, temperature=%.3f",
            self.phase_progress,
            self.current_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during slow cooling phase.
        
        In slow cooling, memories are gradually consolidated, with important and
        frequently accessed memories being strengthened while less important ones
        may be weakened.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Gradually decrease malleability
        if hasattr(memory, "malleability"):
            memory.malleability = max(0.1, memory.malleability - (0.05 * (1 - self.current_temp)))
        
        # Apply nuanced consolidation based on multiple factors
        if hasattr(memory, "strength") and hasattr(memory, "access_count"):
            # Consider both strength and access frequency
            consolidation_score = (memory.strength * 0.7) + (min(1.0, memory.access_count / 10) * 0.3)
            
            if consolidation_score > self.config.consolidation_threshold:
                # Strengthen memories with high consolidation score
                reinforcement = self.config.reinforcement_factor * (1 - self.current_temp)
                memory.strength = min(1.0, memory.strength + reinforcement)
            else:
                # Gradually weaken memories with low consolidation score
                decay = self.config.decay_factor * (1 - self.current_temp) * 0.5
                memory.strength = max(0.0, memory.strength - decay)
        
        return memory
