"""
MTM Consolidation Management

This module provides the MTMConsolidation class which handles memory
consolidation for the Medium-Term Memory (MTM) tier.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from neuroca.memory.backends import BaseStorageBackend


logger = logging.getLogger(__name__)


class MTMConsolidation:
    """
    Manages memory consolidation for MTM memories.
    
    This class provides functionality for memory consolidation, which is
    responsible for managing tier capacity by removing low-priority memories
    when the capacity is exceeded.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the consolidation manager.
        
        Args:
            tier_name: The name of the tier (always "mtm" for this class)
        """
        self._tier_name = tier_name
        self._backend = None
        self._priority_manager = None
        self._delete_func = None  # Function to delete a memory
        self._max_capacity = 1000  # Default capacity
    
    def configure(
        self, 
        backend: BaseStorageBackend,
        priority_manager: Any,
        delete_func: Callable[[str], Any],
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the consolidation manager.
        
        Args:
            backend: The storage backend to use
            priority_manager: The priority manager
            delete_func: Function to call for deleting a memory
            config: Configuration options
        """
        self._backend = backend
        self._priority_manager = priority_manager
        self._delete_func = delete_func
        self._max_capacity = config.get("max_capacity", 1000)
    
    async def perform_consolidation(self) -> int:
        """
        Perform consolidation by removing low-priority memories when over capacity.
        
        Returns:
            Number of memories removed
        """
        logger.debug("Performing MTM consolidation")
        
        # Check if we have necessary components
        if not self._backend or not self._priority_manager or not self._delete_func:
            logger.warning("Cannot perform consolidation: missing components")
            return 0
        
        # Check if we're over capacity
        current_count = await self._count_memories()
        if current_count <= self._max_capacity:
            logger.debug(f"MTM below capacity ({current_count}/{self._max_capacity}), no consolidation needed")
            return 0
        
        # Amount to reduce
        to_remove = current_count - self._max_capacity
        
        # Get low priority memories first
        low_priority_ids = self._priority_manager.get_memories_by_priority("low")
        
        # If we don't have enough low priority memories, we'll need to consider medium priority ones
        remaining_to_remove = to_remove - len(low_priority_ids)
        memories_to_remove = low_priority_ids[:to_remove]
        
        if remaining_to_remove > 0:
            # Get medium priority memories ordered by oldest accessed first
            from neuroca.memory.models.memory_item import MemoryStatus
            
            medium_priority_filter = {
                "metadata.status": MemoryStatus.ACTIVE.value,
                "metadata.tags.priority": "medium",
            }
            
            medium_priority_memories = await self._backend.query(
                filters=medium_priority_filter,
                sort_by="metadata.tags.last_accessed_timestamp",
                ascending=True,  # Oldest first
                limit=remaining_to_remove,
            )
            
            # Extract IDs
            medium_priority_ids = [mem["id"] for mem in medium_priority_memories]
            memories_to_remove.extend(medium_priority_ids)
        
        # Delete memories
        count = 0
        for memory_id in memories_to_remove:
            try:
                # Delete memory
                success = await self._delete_func(memory_id)
                if success:
                    count += 1
            except Exception as e:
                logger.error(f"Error during consolidation when deleting memory {memory_id}: {str(e)}")
        
        if count > 0:
            logger.info(f"Consolidated {count} memories from MTM")
        
        return count
    
    async def is_over_capacity(self) -> bool:
        """
        Check if the tier is currently over capacity.
        
        Returns:
            True if over capacity, False otherwise
        """
        current_count = await self._count_memories()
        return current_count > self._max_capacity
    
    async def get_capacity_usage(self) -> Dict[str, int]:
        """
        Get the current capacity usage information.
        
        Returns:
            Dictionary with current count, max capacity, and available slots
        """
        current_count = await self._count_memories()
        available = max(0, self._max_capacity - current_count)
        
        return {
            "current": current_count,
            "max": self._max_capacity,
            "available": available,
        }
    
    def set_max_capacity(self, capacity: int) -> None:
        """
        Set the maximum capacity.
        
        Args:
            capacity: New maximum capacity
            
        Raises:
            ValueError: If capacity is not positive
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
            
        self._max_capacity = capacity
    
    #-----------------------------------------------------------------------
    # Internal helper methods
    #-----------------------------------------------------------------------
    
    async def _count_memories(self) -> int:
        """
        Count the total number of memories.
        
        Returns:
            Number of memories
        """
        if not self._backend:
            return 0
            
        count = await self._backend.count({})
        return count
