"""
MTM Strength Calculation

This module provides the MTMStrengthCalculator class which handles
calculating and updating memory strength for the MTM tier.
"""

import logging
import time
from typing import Any, Dict, Optional

from neuroca.memory.models.memory_item import MemoryItem, MemoryStatus


logger = logging.getLogger(__name__)


class MTMStrengthCalculator:
    """
    Calculates and manages memory strength for MTM memories.
    
    In the MTM tier, strength is calculated based on a combination of
    priority level, recency of access, and frequency of access.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the strength calculator.
        
        Args:
            tier_name: The name of the tier (always "mtm" for this class)
        """
        self._tier_name = tier_name
        self._priority_weight = 0.4
        self._recency_weight = 0.3
        self._frequency_weight = 0.3
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the strength calculator.
        
        Args:
            config: Configuration options
        """
        # Configure weights
        self._priority_weight = config.get("priority_weight", 0.4)
        self._recency_weight = config.get("recency_weight", 0.3)
        self._frequency_weight = config.get("frequency_weight", 0.3)
    
    async def calculate_strength(self, memory_item: MemoryItem) -> float:
        """
        Calculate the strength of a memory based on tier-specific criteria.
        
        In MTM, strength is a function of priority, recency, and frequency.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Strength value between 0.0 and 1.0
        """
        # Get priority value
        priority_value = memory_item.metadata.tags.get("priority_value", 2)  # Default to medium
        
        # Normalize to 0-1 range (assuming 3 is max priority)
        max_priority = 3  # high priority value
        priority_score = priority_value / max_priority
        
        # Calculate recency score
        last_accessed = memory_item.metadata.tags.get("last_accessed_timestamp")
        if last_accessed is None:
            recency_score = 0.5  # Default if no access timestamp
        else:
            # Calculate time since last access in hours
            hours_since_access = (time.time() - last_accessed) / 3600.0
            # Exponential decay based on time (higher score = more recent)
            recency_score = max(0.0, 1.0 - min(1.0, hours_since_access / 24.0))
        
        # Calculate frequency score
        access_count = memory_item.metadata.access_count
        # Normalize access count (assume 10+ accesses is maximum score)
        frequency_score = min(1.0, access_count / 10.0)
        
        # Calculate combined score using weights
        combined_score = (
            self._priority_weight * priority_score +
            self._recency_weight * recency_score +
            self._frequency_weight * frequency_score
        )
        
        # Apply importance as a multiplier (0.5-1.5 range)
        importance_multiplier = 0.5 + memory_item.metadata.importance
        
        # Final score
        final_score = min(1.0, combined_score * importance_multiplier)
        
        return final_score
    
    async def update_strength(self, memory_item: MemoryItem, delta: float) -> float:
        """
        Update the strength of a memory.
        
        Args:
            memory_item: The memory item
            delta: Amount to adjust strength by
            
        Returns:
            New strength value
        """
        # In MTM, we can't directly manipulate strength
        # Instead, adjust importance which affects priority score
        current = memory_item.metadata.importance
        new_importance = max(0.0, min(1.0, current + delta))
        memory_item.metadata.importance = new_importance
        
        # Recalculate strength/priority score
        return await self.calculate_strength(memory_item)
    
    def get_weights(self) -> Dict[str, float]:
        """
        Get the current weight configuration.
        
        Returns:
            Dictionary of weight names to values
        """
        return {
            "priority_weight": self._priority_weight,
            "recency_weight": self._recency_weight,
            "frequency_weight": self._frequency_weight,
        }
    
    def set_weights(
        self, 
        priority_weight: Optional[float] = None,
        recency_weight: Optional[float] = None,
        frequency_weight: Optional[float] = None,
    ) -> None:
        """
        Set new weight values.
        
        Args:
            priority_weight: New priority weight (0-1)
            recency_weight: New recency weight (0-1)
            frequency_weight: New frequency weight (0-1)
            
        Raises:
            ValueError: If weights are invalid or don't sum to approximately 1.0
        """
        # Only update provided weights
        new_priority = self._priority_weight if priority_weight is None else priority_weight
        new_recency = self._recency_weight if recency_weight is None else recency_weight
        new_frequency = self._frequency_weight if frequency_weight is None else frequency_weight
        
        # Validate each weight
        for name, weight in [
            ("priority", new_priority),
            ("recency", new_recency),
            ("frequency", new_frequency),
        ]:
            if weight < 0 or weight > 1:
                raise ValueError(f"{name} weight must be between 0 and 1")
        
        # Validate sum is approximately 1.0
        total = new_priority + new_recency + new_frequency
        if abs(total - 1.0) > 0.01:  # Allow small rounding errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        # Update weights
        self._priority_weight = new_priority
        self._recency_weight = new_recency
        self._frequency_weight = new_frequency
        
        logger.info(f"MTM strength weights updated: priority={new_priority}, recency={new_recency}, frequency={new_frequency}")
