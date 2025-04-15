"""
LTM Operations

This module provides the LTMOperations class which handles the core
memory operations for the Long-Term Memory (LTM) tier.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from neuroca.memory.models.memory_item import MemoryItem


logger = logging.getLogger(__name__)


class LTMOperations:
    """
    Handles core memory operations for the LTM tier.
    
    This class provides methods for processing memory operations such as
    store, retrieve, update, and delete, delegating to specialized
    components for tier-specific behavior.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the operations manager.
        
        Args:
            tier_name: The name of the tier (always "ltm" for this class)
        """
        self._tier_name = tier_name
        self._category_manager = None
        self._relationship_manager = None
        self._strength_calculator = None
    
    def configure(
        self,
        category_manager: Any,
        relationship_manager: Any,
        strength_calculator: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the operations manager.
        
        Args:
            category_manager: The category manager
            relationship_manager: The relationship manager
            strength_calculator: The strength calculator
            config: Configuration options
        """
        self._category_manager = category_manager
        self._relationship_manager = relationship_manager
        self._strength_calculator = strength_calculator
    
    def process_pre_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item before storage.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Add LTM-specific metadata
        memory_item.metadata.tags["tier"] = "ltm"
        memory_item.metadata.tags["created_timestamp"] = memory_item.metadata.created_at.timestamp()
        memory_item.metadata.tags["last_accessed_timestamp"] = time.time()
        
        # Initialize relationships and categories
        if self._relationship_manager:
            self._relationship_manager.process_on_store(memory_item)
            
        if self._category_manager:
            self._category_manager.process_on_store(memory_item)
    
    def process_post_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after storage.
        
        Args:
            memory_item: The stored memory item
        """
        # Update category map
        if self._category_manager:
            self._category_manager.process_post_store(memory_item)
    
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
        
        # If metadata is being updated, check for category changes
        if metadata and "categories" in metadata:
            # This will be handled in post_update when we have the updated item
            pass
    
    def process_post_update(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after updating.
        
        Args:
            memory_item: The updated memory item
        """
        # For LTM, we don't need any special post-update processing
        pass
    
    def process_pre_delete(self, memory_id: str) -> None:
        """
        Process a memory before deletion.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Clean up relationship and category maps
        if self._relationship_manager:
            self._relationship_manager.process_pre_delete(memory_id)
            
        if self._category_manager:
            self._category_manager.process_pre_delete(memory_id)
    
    def process_post_delete(self, memory_id: str) -> None:
        """
        Process a memory after deletion.
        
        Args:
            memory_id: The ID of the deleted memory
        """
        # For LTM, no special post-delete processing is needed
        pass
    
    async def get_important_memories(
        self,
        query_func: Callable[..., Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get the most important memories based on tier-specific criteria.
        
        In LTM, importance is based primarily on strength (which factors in
        relationships, importance, etc.) and user-defined importance.
        
        Args:
            query_func: Function to query the backend
            limit: Maximum number of memories to return
            
        Returns:
            List of important memories
        """
        from neuroca.memory.models.memory_item import MemoryStatus
        
        # Get active memories, sorted by importance
        # Note: In a real implementation with a rich query language, we might
        # calculate a combined score of strength and importance
        filters = {
            "metadata.status": MemoryStatus.ACTIVE.value,
        }
        
        # Sort by importance
        memories = await query_func(
            filters=filters,
            sort_by="metadata.importance",
            ascending=False,
            limit=limit,
        )
        
        return memories
    
    async def get_memories_by_category(
        self,
        category: str,
        query_func: Callable[..., Any],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get memories in a specific category.
        
        Args:
            category: The category to query
            query_func: Function to query the backend
            limit: Maximum number of memories to return
            
        Returns:
            List of memories in the category
        """
        if not self._category_manager:
            return []
            
        return await self._category_manager.get_memories_by_category(
            category=category,
            limit=limit,
            importance_order=True
        )
    
    async def get_related_memories(
        self,
        memory_id: str,
        query_func: Callable[..., Any],
        relationship_type: Optional[str] = None,
        min_strength: float = 0.0,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get memories related to the specified memory.
        
        Args:
            memory_id: The ID of the memory
            query_func: Function to query the backend
            relationship_type: Type of relationship to filter by (or None for all)
            min_strength: Minimum relationship strength
            limit: Maximum number of memories to return
            
        Returns:
            List of related memories
        """
        if not self._relationship_manager:
            return []
            
        return await self._relationship_manager.get_related_memories(
            memory_id=memory_id,
            relationship_type=relationship_type,
            min_strength=min_strength,
            limit=limit
        )
