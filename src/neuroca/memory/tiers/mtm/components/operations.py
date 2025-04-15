"""
MTM Operations

This module provides the MTMOperations class which handles the core
memory operations for the Medium-Term Memory (MTM) tier.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from neuroca.memory.models.memory_item import MemoryItem


logger = logging.getLogger(__name__)


class MTMOperations:
    """
    Handles core memory operations for the MTM tier.
    
    This class provides methods for processing memory operations such as
    store, retrieve, update, and delete, delegating to specialized
    components for tier-specific behavior.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the operations manager.
        
        Args:
            tier_name: The name of the tier (always "mtm" for this class)
        """
        self._tier_name = tier_name
        self._priority_manager = None
        self._strength_calculator = None
        self._promotion_manager = None
        self._min_access_threshold = 3  # Default: Minimum access count for priority/promotion evaluation
    
    def configure(
        self,
        priority_manager: Any,
        strength_calculator: Any,
        promotion_manager: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the operations manager.
        
        Args:
            priority_manager: The priority manager
            strength_calculator: The strength calculator
            promotion_manager: The promotion manager
            config: Configuration options
        """
        self._priority_manager = priority_manager
        self._strength_calculator = strength_calculator
        self._promotion_manager = promotion_manager
        self._min_access_threshold = config.get("min_access_threshold", 3)
    
    def process_pre_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item before storage.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Add MTM-specific metadata
        memory_item.metadata.tags["tier"] = "mtm"
        memory_item.metadata.tags["created_timestamp"] = time.time()
        memory_item.metadata.tags["last_accessed_timestamp"] = time.time()
        
        # Set priority through priority manager
        if self._priority_manager:
            self._priority_manager.process_pre_store(memory_item)
            
        # Check for promotion candidacy
        if self._promotion_manager:
            self._promotion_manager.process_on_store(memory_item)
    
    def process_post_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after storage.
        
        Args:
            memory_item: The stored memory item
        """
        # Update priority map through priority manager
        if self._priority_manager:
            self._priority_manager.process_post_store(memory_item)
    
    def process_on_retrieve(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when retrieved.
        
        Args:
            memory_item: The retrieved memory item
        """
        # Update last accessed timestamp
        memory_item.metadata.tags["last_accessed_timestamp"] = time.time()
    
    def process_on_access(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when accessed.
        
        Args:
            memory_item: The accessed memory item
        """
        # Update last accessed timestamp
        memory_item.metadata.tags["last_accessed_timestamp"] = time.time()
        
        # Check for priority update through priority manager
        if self._priority_manager:
            self._priority_manager.process_on_access(memory_item, self._min_access_threshold)
            
        # Check for promotion candidacy
        if self._promotion_manager:
            self._promotion_manager.process_on_access(memory_item)
    
    def process_pre_update(
        self,
        memory_item: MemoryItem,
        content: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        """
        Process a memory item before updating.
        
        Args:
            memory_item: The memory item to be updated
            content: New content (if None, keeps existing content)
            metadata: New/updated metadata (if None, keeps existing metadata)
        """
        # Update last accessed timestamp
        memory_item.metadata.tags["last_accessed_timestamp"] = time.time()
        
        # If metadata is being updated, check for priority changes
        if metadata and "priority" in metadata:
            # This will be handled in post_update when we have the updated item
            pass
    
    def process_post_update(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after updating.
        
        Args:
            memory_item: The updated memory item
        """
        # Check for promotion after update
        if self._promotion_manager:
            self._promotion_manager.process_on_update(memory_item)
    
    def process_pre_delete(self, memory_id: str) -> None:
        """
        Process a memory before deletion.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Update priority map through priority manager
        if self._priority_manager:
            self._priority_manager.process_pre_delete(memory_id)
    
    def process_post_delete(self, memory_id: str) -> None:
        """
        Process a memory after deletion.
        
        Args:
            memory_id: The ID of the deleted memory
        """
        # For MTM, no special post-delete processing is needed
        pass
    
    async def get_important_memories(
        self,
        query_func: Callable[..., Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get the most important memories based on tier-specific criteria.
        
        In MTM, importance is based on a combination of priority, recency,
        and access frequency.
        
        Args:
            query_func: Function to query the backend
            limit: Maximum number of memories to return
            
        Returns:
            List of important memories
        """
        from neuroca.memory.models.memory_item import MemoryStatus
        
        # Get high priority memories first
        high_priority_filter = {
            "metadata.status": MemoryStatus.ACTIVE.value,
            "metadata.tags.priority": "high",
        }
        
        high_priority_memories = await query_func(
            filters=high_priority_filter,
            sort_by="metadata.tags.last_accessed_timestamp",
            ascending=False,  # Most recently accessed first
            limit=limit,
        )
        
        # If we have enough high priority memories, return them
        if len(high_priority_memories) >= limit:
            return high_priority_memories[:limit]
        
        # Otherwise, get medium priority memories to fill the rest
        remaining = limit - len(high_priority_memories)
        medium_priority_filter = {
            "metadata.status": MemoryStatus.ACTIVE.value,
            "metadata.tags.priority": "medium",
        }
        
        medium_priority_memories = await query_func(
            filters=medium_priority_filter,
            sort_by="metadata.tags.last_accessed_timestamp",
            ascending=False,
            limit=remaining,
        )
        
        # Combine and return
        return high_priority_memories + medium_priority_memories
