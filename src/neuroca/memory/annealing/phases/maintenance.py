"""
Maintenance Phase Module

This module implements the maintenance phase of memory annealing.
"""

import logging
from datetime import datetime
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class MaintenancePhase(AnnealingPhase):
    """Maintenance phase of memory annealing.
    
    This phase keeps temperature at a minimal level, focusing on preserving
    established memory structures while allowing for very minor adjustments
    based on new information or access patterns.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement temperature maintenance at low level.
        
        Returns:
            The updated temperature value
        """
        # Maintain a very low, stable temperature
        target_temp = self.config.min_temperature + (
            (self.config.max_temperature - self.config.min_temperature) * 0.1
        )
        
        # Gradually approach target temperature
        temp_diff = target_temp - self.current_temp
        self.current_temp += temp_diff * 0.1
        
        logger.debug(
            "Maintenance phase: progress=%.2f, temperature=%.3f",
            self.phase_progress,
            self.current_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during maintenance phase.
        
        In maintenance, the focus is on preserving memory structures while allowing
        for minor reinforcement of frequently accessed memories.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Set malleability to a very low value
        if hasattr(memory, "malleability"):
            memory.malleability = max(0.05, memory.malleability * 0.9)
        
        # Apply minimal reinforcement for recently accessed memories
        if hasattr(memory, "last_accessed") and hasattr(memory, "strength"):
            time_since_access = (datetime.now() - memory.last_accessed).total_seconds()
            
            # Reinforce recently accessed memories
            if time_since_access < 3600:  # Accessed within the last hour
                recency_factor = max(0, 1 - (time_since_access / 3600))
                reinforcement = 0.01 * recency_factor
                memory.strength = min(1.0, memory.strength + reinforcement)
        
        # Apply very slow decay to all memories
        if hasattr(memory, "strength"):
            minimal_decay = 0.001 * self.current_temp
            memory.strength = max(0.0, memory.strength - minimal_decay)
        
        return memory
