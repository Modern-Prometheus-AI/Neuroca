"""
MTM Promotion Management

This module provides the MTMPromotion class which handles promotion of
memories from MTM to LTM tier based on various criteria.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set

from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.backends import BaseStorageBackend


logger = logging.getLogger(__name__)


class MTMPromotion:
    """
    Manages promotion of memories from MTM to LTM.
    
    This class evaluates memories for potential promotion to the LTM tier
    based on criteria such as access frequency, importance, and explicit
    tagging for promotion.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the promotion manager.
        
        Args:
            tier_name: The name of the tier (always "mtm" for this class)
        """
        self._tier_name = tier_name
        self._backend = None
        self._min_access_threshold = 3  # Minimum access count for promotion candidacy
        self._min_importance = 0.6      # Minimum importance for promotion
        self._promote_high_priority = True  # Whether to auto-promote high priority items
    
    def configure(
        self, 
        backend: BaseStorageBackend,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the promotion manager.
        
        Args:
            backend: The storage backend to use
            config: Configuration options
        """
        self._backend = backend
        self._min_access_threshold = config.get("min_access_threshold", 3)
        self._min_importance = config.get("min_promotion_importance", 0.6)
        self._promote_high_priority = config.get("promote_high_priority", True)
    
    def process_on_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when stored to check for immediate promotion candidacy.
        
        Args:
            memory_item: The stored memory item
        """
        # Initialize promotion tag
        memory_item.metadata.tags["promote_to_ltm"] = False
        
        # Check for explicit promotion request
        if memory_item.metadata.tags.get("request_ltm_promotion", False):
            memory_item.metadata.tags["promote_to_ltm"] = True
            return
        
        # Check if high priority items should be auto-promoted
        if (self._promote_high_priority and 
            memory_item.metadata.tags.get("priority") == "high" and
            memory_item.metadata.importance >= self._min_importance):
            memory_item.metadata.tags["promote_to_ltm"] = True
    
    def process_on_access(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when accessed to check for promotion candidacy.
        
        Args:
            memory_item: The accessed memory item
        """
        # Skip if already marked for promotion
        if memory_item.metadata.tags.get("promote_to_ltm", False):
            return
            
        # Check access count threshold
        if memory_item.metadata.access_count >= self._min_access_threshold:
            # Check importance threshold
            if memory_item.metadata.importance >= self._min_importance:
                # Mark for promotion if both thresholds are met
                memory_item.metadata.tags["promote_to_ltm"] = True
                logger.debug(f"Memory {memory_item.id} marked as LTM promotion candidate")
    
    def process_on_update(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when updated to check for promotion candidacy.
        
        Args:
            memory_item: The updated memory item
        """
        # Similar logic to on_access, but triggered by updates
        # Skip if already marked for promotion
        if memory_item.metadata.tags.get("promote_to_ltm", False):
            return
            
        # Check for explicit promotion request in update
        if memory_item.metadata.tags.get("request_ltm_promotion", False):
            memory_item.metadata.tags["promote_to_ltm"] = True
            return
            
        # Check if high priority and meets importance threshold
        if (memory_item.metadata.tags.get("priority") == "high" and
            memory_item.metadata.importance >= self._min_importance and
            memory_item.metadata.access_count >= self._min_access_threshold):
            memory_item.metadata.tags["promote_to_ltm"] = True
    
    async def get_promotion_candidates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memories that are candidates for promotion to LTM.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of memory candidates for promotion
            
        Raises:
            Exception: If the operation fails
        """
        if not self._backend:
            return []
        
        # Find memories marked for promotion
        from neuroca.memory.models.memory_item import MemoryStatus
        
        promotion_filter = {
            "metadata.status": MemoryStatus.ACTIVE.value,
            "metadata.tags.promote_to_ltm": True,
        }
        
        # Get candidates
        candidates = await self._backend.query(
            filters=promotion_filter,
            sort_by="metadata.importance",
            ascending=False,
            limit=limit,
        )
        
        return candidates
    
    async def mark_for_promotion(self, memory_id: str, update_func: Any) -> bool:
        """
        Explicitly mark a memory for promotion to LTM.
        
        Args:
            memory_id: The ID of the memory
            update_func: Function to call for updating a memory
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            Exception: If the operation fails
        """
        if not update_func:
            logger.error("No update function provided")
            return False
            
        # Set promotion tags
        metadata = {
            "promote_to_ltm": True,
            "request_ltm_promotion": True,
        }
        
        # Update memory
        return await update_func(memory_id, metadata=metadata)
    
    async def unmark_for_promotion(self, memory_id: str, update_func: Any) -> bool:
        """
        Remove promotion mark from a memory.
        
        Args:
            memory_id: The ID of the memory
            update_func: Function to call for updating a memory
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            Exception: If the operation fails
        """
        if not update_func:
            logger.error("No update function provided")
            return False
            
        # Clear promotion tags
        metadata = {
            "promote_to_ltm": False,
            "request_ltm_promotion": False,
        }
        
        # Update memory
        return await update_func(memory_id, metadata=metadata)
    
    async def get_promotion_stats(self) -> Dict[str, int]:
        """
        Get statistics about promotion candidates.
        
        Returns:
            Dictionary with statistics
            
        Raises:
            Exception: If the operation fails
        """
        if not self._backend:
            return {"total": 0, "high_priority": 0, "medium_priority": 0, "low_priority": 0}
        
        # Base filter for promotion candidates
        from neuroca.memory.models.memory_item import MemoryStatus
        
        base_filter = {
            "metadata.status": MemoryStatus.ACTIVE.value,
            "metadata.tags.promote_to_ltm": True,
        }
        
        # Get total count
        total = await self._backend.count(base_filter)
        
        # Get high priority count
        high_filter = base_filter.copy()
        high_filter["metadata.tags.priority"] = "high"
        high_count = await self._backend.count(high_filter)
        
        # Get medium priority count
        medium_filter = base_filter.copy()
        medium_filter["metadata.tags.priority"] = "medium"
        medium_count = await self._backend.count(medium_filter)
        
        # Get low priority count
        low_filter = base_filter.copy()
        low_filter["metadata.tags.priority"] = "low"
        low_count = await self._backend.count(low_filter)
        
        return {
            "total": total,
            "high_priority": high_count,
            "medium_priority": medium_count,
            "low_priority": low_count,
        }
