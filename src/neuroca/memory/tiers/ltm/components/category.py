"""
LTM Category Management

This module provides the LTMCategory class which handles the categorization
of memories in the LTM tier.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.backends import BaseStorageBackend
from neuroca.memory.exceptions import TierOperationError


logger = logging.getLogger(__name__)


class LTMCategory:
    """
    Manages categorization of memories in the LTM tier.
    
    This class provides methods for creating, updating, and querying
    categories of memories, which helps with organization and retrieval.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the category manager.
        
        Args:
            tier_name: The name of the tier (always "ltm" for this class)
        """
        self._tier_name = tier_name
        self._lifecycle = None
        self._backend = None
        self._update_func = None  # Function to update a memory
        self._default_categories = ["general"]  # Default category
    
    def configure(
        self, 
        lifecycle: Any, 
        backend: BaseStorageBackend,
        update_func: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the category manager.
        
        Args:
            lifecycle: The lifecycle manager, used to access/update category map
            backend: The storage backend
            update_func: Function to call for updating a memory
            config: Configuration options
        """
        self._lifecycle = lifecycle
        self._backend = backend
        self._update_func = update_func
        
        # Load custom default categories if configured
        if "default_categories" in config:
            self._default_categories = config["default_categories"]
    
    def process_on_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when stored to initialize categories.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Initialize categories if not present
        if "categories" not in memory_item.metadata.tags:
            memory_item.metadata.tags["categories"] = self._default_categories.copy()
    
    def process_post_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after storage to update category map.
        
        Args:
            memory_item: The stored memory item
        """
        # Update category map
        if "categories" in memory_item.metadata.tags and self._lifecycle:
            categories = memory_item.metadata.tags["categories"]
            if isinstance(categories, list):
                self._lifecycle.update_category(memory_item.id, categories)
    
    def process_pre_delete(self, memory_id: str) -> None:
        """
        Process a memory before deletion to update category map.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Update the lifecycle category map to remove this memory
        if self._lifecycle:
            self._lifecycle.remove_memory(memory_id)
    
    async def add_to_category(self, memory_id: str, category: str) -> bool:
        """
        Add a memory to a category.
        
        Args:
            memory_id: The ID of the memory
            category: The category to add to
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the memory
        memory_data = await self._backend.retrieve(memory_id)
        if memory_data is None:
            raise TierOperationError(
                operation="add_to_category",
                tier_name=self._tier_name,
                message=f"Memory {memory_id} not found"
            )
        
        memory_item = MemoryItem.model_validate(memory_data)
        
        # Initialize categories if not present
        if "categories" not in memory_item.metadata.tags:
            memory_item.metadata.tags["categories"] = []
        
        # Get current categories
        categories = memory_item.metadata.tags["categories"]
        
        # Check if already in category
        if category in categories:
            return True
        
        # Add to category
        categories.append(category)
        
        # Update the memory
        success = await self._update_func(memory_id, metadata=memory_item.metadata.tags)
        
        # Update category map
        if success and self._lifecycle:
            self._lifecycle.update_category(memory_id, categories)
        
        return success
    
    async def remove_from_category(self, memory_id: str, category: str) -> bool:
        """
        Remove a memory from a category.
        
        Args:
            memory_id: The ID of the memory
            category: The category to remove from
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the memory
        memory_data = await self._backend.retrieve(memory_id)
        if memory_data is None:
            raise TierOperationError(
                operation="remove_from_category",
                tier_name=self._tier_name,
                message=f"Memory {memory_id} not found"
            )
        
        memory_item = MemoryItem.model_validate(memory_data)
        
        # Check if categories exist
        if "categories" not in memory_item.metadata.tags:
            return True
        
        # Get current categories
        categories = memory_item.metadata.tags["categories"]
        
        # Check if in category
        if category not in categories:
            return True
        
        # Remove from category
        categories.remove(category)
        
        # Update the memory
        success = await self._update_func(memory_id, metadata=memory_item.metadata.tags)
        
        # Update category map
        if success and self._lifecycle:
            self._lifecycle.update_category(memory_id, categories)
        
        return success
    
    async def set_categories(self, memory_id: str, categories: List[str]) -> bool:
        """
        Set the categories for a memory.
        
        Args:
            memory_id: The ID of the memory
            categories: List of categories
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the memory
        memory_data = await self._backend.retrieve(memory_id)
        if memory_data is None:
            raise TierOperationError(
                operation="set_categories",
                tier_name=self._tier_name,
                message=f"Memory {memory_id} not found"
            )
        
        memory_item = MemoryItem.model_validate(memory_data)
        
        # Set categories
        memory_item.metadata.tags["categories"] = categories
        
        # Update the memory
        success = await self._update_func(memory_id, metadata=memory_item.metadata.tags)
        
        # Update category map
        if success and self._lifecycle:
            self._lifecycle.update_category(memory_id, categories)
        
        return success
    
    async def get_categories(self, memory_id: str) -> List[str]:
        """
        Get the categories for a memory.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            List of categories
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the memory
        memory_data = await self._backend.retrieve(memory_id)
        if memory_data is None:
            raise TierOperationError(
                operation="get_categories",
                tier_name=self._tier_name,
                message=f"Memory {memory_id} not found"
            )
        
        memory_item = MemoryItem.model_validate(memory_data)
        
        # Get categories
        categories = memory_item.metadata.tags.get("categories", [])
        
        return categories
    
    async def get_memories_by_category(
        self,
        category: str,
        limit: int = 10,
        importance_order: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get memories in a specific category.
        
        Args:
            category: The category to query
            limit: Maximum number of memories to return
            importance_order: Whether to order by importance
            
        Returns:
            List of memories in the category
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the category map
        if not self._lifecycle:
            return []
            
        category_map = self._lifecycle.get_category_map()
        
        # Check if category exists
        if category not in category_map:
            return []
            
        # Get memory IDs in category
        memory_ids = list(category_map[category])
        
        # Get memories
        from neuroca.memory.models.memory_item import MemoryStatus
        
        memories = []
        for memory_id in memory_ids:
            # Get the memory
            memory_data = await self._backend.retrieve(memory_id)
            if memory_data is not None:
                # Check if active
                memory_item = MemoryItem.model_validate(memory_data)
                if memory_item.metadata.status == MemoryStatus.ACTIVE:
                    memories.append(memory_data)
        
        # Sort by importance if requested
        if importance_order:
            memories.sort(
                key=lambda m: m.get("metadata", {}).get("importance", 0.5),
                reverse=True
            )
        
        # Limit the number of results
        memories = memories[:limit]
        
        return memories
    
    async def get_all_categories(self) -> Dict[str, int]:
        """
        Get all categories and the number of memories in each.
        
        Returns:
            Dictionary mapping categories to memory counts
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the category map
        if not self._lifecycle:
            return {}
            
        category_map = self._lifecycle.get_category_map()
        
        # Get counts
        counts = {
            category: len(memory_ids)
            for category, memory_ids in category_map.items()
        }
        
        return counts
