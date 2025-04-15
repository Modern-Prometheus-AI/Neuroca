"""
Stabilization Phase Module

This module implements the stabilization phase of memory annealing.
"""

import logging
import math
from neuroca.memory.annealing.phases.base import AnnealingPhase
from neuroca.memory.models import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class StabilizationPhase(AnnealingPhase):
    """Stabilization phase of memory annealing.
    
    This phase maintains a low but non-zero temperature, allowing for minor
    adjustments to memory structures while generally preserving their organization.
    It helps to fine-tune memory connections and strengths.
    """
    
    def _update_temperature_impl(self) -> float:
        """Implement temperature stabilization.
        
        Returns:
            The updated temperature value
        """
        # Maintain a low, slightly fluctuating temperature
        base_temp = self.config.min_temperature + (
            (self.config.max_temperature - self.config.min_temperature) * 0.2
        )
        
        # Add small oscillations
        oscillation = math.sin(self.phase_progress * 6 * math.pi) * 0.05
        self.current_temp = max(self.config.min_temperature, 
                               min(self.config.max_temperature, 
                                  base_temp + oscillation))
        
        logger.debug(
            "Stabilization phase: progress=%.2f, temperature=%.3f",
            self.phase_progress,
            self.current_temp
        )
        
        return self.current_temp
    
    def _process_memory_impl(self, memory: MemoryItem) -> MemoryItem:
        """Process memory during stabilization phase.
        
        In stabilization, memory structures are fine-tuned, with minor adjustments
        to strengths and connections based on importance and relevance.
        
        Args:
            memory: The memory item to process
            
        Returns:
            The processed memory item
        """
        # Fine-tune memory attributes
        if hasattr(memory, "malleability"):
            # Reduce malleability to a stable low value
            target_malleability = 0.2
            memory.malleability = memory.malleability * 0.9 + target_malleability * 0.1
        
        if hasattr(memory, "strength") and hasattr(memory, "importance"):
            # Align strength with importance during stabilization
            strength_diff = memory.importance - memory.strength
            adjustment = strength_diff * 0.05
            memory.strength = max(0.0, min(1.0, memory.strength + adjustment))
        
        # Stabilize connections if they exist
        if hasattr(memory, "connections") and isinstance(memory.connections, dict):
            for connection_id, strength in memory.connections.items():
                # Strengthen important connections, weaken trivial ones
                if strength > 0.6:  # Important connection
                    memory.connections[connection_id] = min(1.0, strength + 0.01)
                elif strength < 0.3:  # Weak connection
                    memory.connections[connection_id] = max(0.0, strength - 0.01)
        
        return memory
