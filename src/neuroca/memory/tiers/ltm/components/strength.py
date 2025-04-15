"""
LTM Strength Calculation

This module provides the LTMStrengthCalculator class which handles
calculating and updating memory strength for the LTM tier.
"""

import logging
import time
from typing import Any, Dict, Optional

from neuroca.memory.models.memory_item import MemoryItem, MemoryStatus


logger = logging.getLogger(__name__)


class LTMStrengthCalculator:
    """
    Calculates and manages memory strength for LTM memories.
    
    In the LTM tier, strength is calculated based on several factors:
    1. Importance - user-defined or system-calculated importance
    2. Connectivity - how connected this memory is to other memories
    3. Frequency - how often this memory is accessed
    4. Recency - how recently this memory was accessed, with a much slower
       decay rate than in STM or MTM
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the strength calculator.
        
        Args:
            tier_name: The name of the tier (always "ltm" for this class)
        """
        self._tier_name = tier_name
        
        # Strength factor weights
        self._importance_weight = 0.40
        self._connectivity_weight = 0.30
        self._frequency_weight = 0.20
        self._recency_weight = 0.10
        
        # Other settings
        self._decay_rate = 0.001  # Very slow decay rate (per day, not minute)
        self._lifecycle = None  # For accessing relationship data
    
    def configure(self, lifecycle: Any, config: Dict[str, Any]) -> None:
        """
        Configure the strength calculator.
        
        Args:
            lifecycle: The lifecycle manager
            config: Configuration options
        """
        self._lifecycle = lifecycle
        
        # Configure weights
        self._importance_weight = config.get("importance_weight", 0.40)
        self._connectivity_weight = config.get("connectivity_weight", 0.30)
        self._frequency_weight = config.get("frequency_weight", 0.20)
        self._recency_weight = config.get("recency_weight", 0.10)
        
        # Configure decay rate
        self._decay_rate = config.get("decay_rate", 0.001)
    
    async def calculate_strength(self, memory_item: MemoryItem) -> float:
        """
        Calculate the strength of a memory based on tier-specific criteria.
        
        In LTM, strength is a function of importance, connectivity, 
        frequency, and recency (with a much slower decay).
        
        Args:
            memory_item: The memory item
            
        Returns:
            Strength value between 0.0 and 1.0
        """
        # Get importance score (0.0-1.0)
        importance_score = memory_item.metadata.importance
        
        # Get connectivity score based on relationships
        connectivity_score = self._calculate_connectivity_score(memory_item)
        
        # Get frequency score based on access count
        frequency_score = self._calculate_frequency_score(memory_item)
        
        # Get recency score based on last accessed time
        recency_score = self._calculate_recency_score(memory_item)
        
        # Calculate combined score
        combined_score = (
            self._importance_weight * importance_score +
            self._connectivity_weight * connectivity_score +
            self._frequency_weight * frequency_score +
            self._recency_weight * recency_score
        )
        
        # Ensure within 0.0-1.0 range
        return max(0.0, min(1.0, combined_score))
    
    async def update_strength(self, memory_item: MemoryItem, delta: float) -> float:
        """
        Update the strength of a memory.
        
        In LTM, adjusting strength directly is less common, as strength
        is mainly derived from relationships and importance. Instead, we
        primarily adjust importance here.
        
        Args:
            memory_item: The memory item
            delta: Amount to adjust strength by
            
        Returns:
            New strength value
        """
        # In LTM, we adjust importance rather than directly manipulating strength
        current = memory_item.metadata.importance
        new_importance = max(0.0, min(1.0, current + delta))
        memory_item.metadata.importance = new_importance
        
        # Recalculate and return new strength
        return await self.calculate_strength(memory_item)
    
    def _calculate_connectivity_score(self, memory_item: MemoryItem) -> float:
        """
        Calculate a connectivity score based on relationships.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Connectivity score (0.0-1.0)
        """
        # Get relationships from the memory item
        relationships = memory_item.metadata.tags.get("relationships", {})
        
        # If no relationships or no lifecycle manager, return 0
        if not relationships or not self._lifecycle:
            return 0.0
        
        # Get relationship map to check if this memory appears in other memories' relationships
        relationship_map = self._lifecycle.get_relationship_map()
        
        # Count outgoing relationships (from this memory to others)
        outgoing_count = len(relationships)
        
        # Count incoming relationships (from other memories to this one)
        incoming_count = sum(
            1 for rel_dict in relationship_map.values()
            if memory_item.id in rel_dict
        )
        
        # Calculate total relationship count
        total_count = outgoing_count + incoming_count
        
        # Map to 0.0-1.0 scale - assume 10+ relationships is maximum score
        return min(1.0, total_count / 10.0)
    
    def _calculate_frequency_score(self, memory_item: MemoryItem) -> float:
        """
        Calculate a frequency score based on access count.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Frequency score (0.0-1.0)
        """
        # Get access count
        access_count = memory_item.metadata.access_count
        
        # Map to 0.0-1.0 scale - assume 20+ accesses is maximum score
        return min(1.0, access_count / 20.0)
    
    def _calculate_recency_score(self, memory_item: MemoryItem) -> float:
        """
        Calculate a recency score based on last accessed time.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Recency score (0.0-1.0)
        """
        # Get last accessed timestamp
        last_accessed = memory_item.metadata.tags.get("last_accessed_timestamp")
        if last_accessed is None:
            return 0.5  # Default if no access timestamp
        
        # Calculate days since last access
        days_since_access = (time.time() - last_accessed) / (24 * 3600.0)
        
        # Calculate decay based on days (much slower than STM/MTM)
        decay = days_since_access * self._decay_rate
        
        # Calculate recency score (1.0 = recent, 0.0 = very old)
        return max(0.0, 1.0 - decay)
    
    def get_weights(self) -> Dict[str, float]:
        """
        Get the current weight configuration.
        
        Returns:
            Dictionary of weight names to values
        """
        return {
            "importance_weight": self._importance_weight,
            "connectivity_weight": self._connectivity_weight,
            "frequency_weight": self._frequency_weight,
            "recency_weight": self._recency_weight,
        }
    
    def set_weights(
        self, 
        importance_weight: Optional[float] = None,
        connectivity_weight: Optional[float] = None,
        frequency_weight: Optional[float] = None,
        recency_weight: Optional[float] = None,
    ) -> None:
        """
        Set new weight values.
        
        Args:
            importance_weight: New importance weight (0-1)
            connectivity_weight: New connectivity weight (0-1)
            frequency_weight: New frequency weight (0-1)
            recency_weight: New recency weight (0-1)
            
        Raises:
            ValueError: If weights are invalid or don't sum to approximately 1.0
        """
        # Only update provided weights
        new_importance = self._importance_weight if importance_weight is None else importance_weight
        new_connectivity = self._connectivity_weight if connectivity_weight is None else connectivity_weight
        new_frequency = self._frequency_weight if frequency_weight is None else frequency_weight
        new_recency = self._recency_weight if recency_weight is None else recency_weight
        
        # Validate each weight
        for name, weight in [
            ("importance", new_importance),
            ("connectivity", new_connectivity),
            ("frequency", new_frequency),
            ("recency", new_recency),
        ]:
            if weight < 0 or weight > 1:
                raise ValueError(f"{name} weight must be between 0 and 1")
        
        # Validate sum is approximately 1.0
        total = new_importance + new_connectivity + new_frequency + new_recency
        if abs(total - 1.0) > 0.01:  # Allow small rounding errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        # Update weights
        self._importance_weight = new_importance
        self._connectivity_weight = new_connectivity
        self._frequency_weight = new_frequency
        self._recency_weight = new_recency
        
        logger.info(f"LTM strength weights updated: importance={new_importance}, connectivity={new_connectivity}, frequency={new_frequency}, recency={new_recency}")
