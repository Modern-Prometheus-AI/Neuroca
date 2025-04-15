"""
STM Operations

This module provides the STMOperations class which handles the core
memory operations for the Short-Term Memory (STM) tier.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from neuroca.memory.models.memory_item import MemoryItem


logger = logging.getLogger(__name__)


class STMOperations:
    """
    Handles core memory operations for the STM tier.
    
    This class provides methods for processing memory operations such as
    store, retrieve, update, and delete, delegating to specialized
    components for tier-specific behavior.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the operations manager.
        
        Args:
            tier_name: The name of the tier (always "stm" for this class)
        """
        self._tier_name = tier_name
        self._expiry_manager = None
        self._strength_calculator = None
        self._extend_ttl_on_access = False
    
    def configure(
        self,
        expiry_manager: Any,
        strength_calculator: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the operations manager.
        
        Args:
            expiry_manager: The expiry manager
            strength_calculator: The strength calculator
            config: Configuration options
        """
        self._expiry_manager = expiry_manager
        self._strength_calculator = strength_calculator
        self._extend_ttl_on_access = config.get("extend_ttl_on_access", False)
    
    def process_pre_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item before storage.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Add STM-specific metadata
        memory_item.metadata.tags["tier"] = "stm"
        memory_item.metadata.tags["created_timestamp"] = memory_item.metadata.created_at.timestamp()
        
        # Set expiry time through expiry manager
        if self._expiry_manager:
            self._expiry_manager.process_pre_store(memory_item)
    
    def process_post_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after storage.
        
        Args:
            memory_item: The stored memory item
        """
        # Update expiry map through expiry manager
        if self._expiry_manager:
            self._expiry_manager.process_post_store(memory_item)
    
    def process_on_retrieve(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when retrieved.
        
        Args:
            memory_item: The retrieved memory item
        """
        # Check expiry through expiry manager
        if self._expiry_manager:
            self._expiry_manager.process_on_retrieve(memory_item)
    
    def process_on_access(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when accessed.
        
        Args:
            memory_item: The accessed memory item
        """
        # Reset strength through strength calculator
        if self._strength_calculator:
            self._strength_calculator.process_on_access(memory_item)
            
        # Extend expiry through expiry manager if configured
        if self._expiry_manager:
            self._expiry_manager.process_on_access(memory_item, self._extend_ttl_on_access)
    
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
        # For STM, no special pre-update processing is needed
        pass
    
    def process_post_update(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after updating.
        
        Args:
            memory_item: The updated memory item
        """
        # For STM, no special post-update processing is needed
        pass
    
    def process_pre_delete(self, memory_id: str) -> None:
        """
        Process a memory before deletion.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Update expiry map through expiry manager
        if self._expiry_manager:
            self._expiry_manager.process_pre_delete(memory_id)
    
    def process_post_delete(self, memory_id: str) -> None:
        """
        Process a memory after deletion.
        
        Args:
            memory_id: The ID of the deleted memory
        """
        # For STM, no special post-delete processing is needed
        pass
    
    async def get_important_memories(
        self,
        query_func: Callable[..., Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get the most important memories based on tier-specific criteria.
        
        In STM, importance is based on a combination of recency (strength)
        and configured importance.
        
        Args:
            query_func: Function to query the backend
            limit: Maximum number of memories to return
            
        Returns:
            List of important memories
        """
        from neuroca.memory.models.memory_item import MemoryStatus
        
        # In STM, importance is based on recency and configured importance
        # Get active (non-expired) memories, sorted by metadata.importance
        filters = {
            "metadata.status": MemoryStatus.ACTIVE.value,
        }
        
        # Sort by importance (user-defined importance takes precedence)
        memories = await query_func(
            filters=filters,
            sort_by="metadata.importance",
            ascending=False,
            limit=limit,
        )
        
        return memories
