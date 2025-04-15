"""
STM Strength Calculation

This module provides the STMStrengthCalculator class which handles
calculating and updating memory strength (freshness) for the STM tier.
"""

import logging
import time
from typing import Any, Dict, Optional

from neuroca.memory.models.memory_item import MemoryItem, MemoryStatus


logger = logging.getLogger(__name__)


class STMStrengthCalculator:
    """
    Calculates and manages memory strength for STM memories.
    
    In the STM tier, strength represents the "freshness" of memories,
    with a decay over time that represents the natural decay of
    short-term memories in cognitive systems.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the strength calculator.
        
        Args:
            tier_name: The name of the tier (always "stm" for this class)
        """
        self._tier_name = tier_name
        self._decay_rate = 0.05  # Default strength loss per minute
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the strength calculator.
        
        Args:
            config: Configuration options
        """
        self._decay_rate = config.get("decay_rate", 0.05)
    
    def process_on_access(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when accessed to reset strength.
        
        Args:
            memory_item: The accessed memory item
        """
        # Reset decay on access - "refreshing" the memory
        memory_item.metadata.strength = 1.0
    
    async def calculate_strength(self, memory_item: MemoryItem) -> float:
        """
        Calculate the strength of a memory based on tier-specific criteria.
        
        In STM, strength represents freshness - a recently created memory
        has high strength, which decays over time.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Strength value between 0.0 and 1.0
        """
        # If already expired, strength is 0
        if memory_item.metadata.status == MemoryStatus.EXPIRED:
            return 0.0
        
        # Calculate time since creation
        created_timestamp = memory_item.metadata.tags.get("created_timestamp")
        if created_timestamp is None:
            # If no creation timestamp, use a default strength
            return 0.5
        
        # Calculate elapsed time in minutes
        elapsed_minutes = (time.time() - created_timestamp) / 60.0
        
        # Apply decay rate
        strength = max(0.0, 1.0 - (elapsed_minutes * self._decay_rate))
        
        return strength
    
    async def update_strength(self, memory_item: MemoryItem, delta: float) -> float:
        """
        Update the strength of a memory.
        
        Args:
            memory_item: The memory item
            delta: Amount to adjust strength by
            
        Returns:
            New strength value
        """
        # In STM, we adjust the strength directly
        current = memory_item.metadata.strength
        new_strength = max(0.0, min(1.0, current + delta))
        memory_item.metadata.strength = new_strength
        
        return new_strength
    
    def get_decay_rate(self) -> float:
        """
        Get the current decay rate.
        
        Returns:
            Decay rate (strength loss per minute)
        """
        return self._decay_rate
    
    def set_decay_rate(self, decay_rate: float) -> None:
        """
        Set the decay rate.
        
        Args:
            decay_rate: New decay rate (strength loss per minute)
            
        Raises:
            ValueError: If decay_rate is negative
        """
        if decay_rate < 0:
            raise ValueError("Decay rate cannot be negative")
            
        self._decay_rate = decay_rate
        logger.info(f"STM decay rate set to {decay_rate}")
