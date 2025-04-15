"""
In-Memory Storage Backend Core

This module provides the main InMemoryBackend class that integrates all in-memory
component modules to implement the BaseStorageBackend interface for the memory system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.in_memory.components.batch import InMemoryBatch
from neuroca.memory.backends.in_memory.components.crud import InMemoryCRUD
from neuroca.memory.backends.in_memory.components.search import InMemorySearch
from neuroca.memory.backends.in_memory.components.stats import InMemoryStats
from neuroca.memory.backends.in_memory.components.storage import InMemoryStorage
from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError, StorageOperationError
from neuroca.memory.interfaces import StorageStats
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import SearchFilter, SearchResults

logger = logging.getLogger(__name__)


class InMemoryBackend(BaseStorageBackend):
    """
    In-memory implementation of the storage backend interface.
    
    This class integrates the in-memory component modules to provide a complete
    implementation of the BaseStorageBackend interface.
    
    Features:
    - Full CRUD operations for memory items
    - Text-based search with filtering
    - Transaction support for batch operations
    - Statistics tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the in-memory backend.
        
        Args:
            config: Optional configuration parameters:
                - max_items: Maximum number of items to store (defaults to no limit)
        """
        super().__init__(config)
        self.config = config or {}
        
        # Create components
        self._create_components()
    
    def _create_components(self) -> None:
        """
        Create the component instances.
        """
        # Extract configuration settings
        max_items = self.config.get("max_items")
        
        # Create storage component
        self.storage = InMemoryStorage(max_items=max_items)
        
        # Create other components
        self.crud = InMemoryCRUD(self.storage)
        self.search = InMemorySearch(self.storage)
        self.batch = InMemoryBatch(self.storage, self.crud)
        self.stats = InMemoryStats(self.storage)
    
    async def initialize(self) -> None:
        """
        Initialize the in-memory backend.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Nothing special to initialize for in-memory backend
            logger.info("Initialized in-memory backend")
        except Exception as e:
            error_msg = f"Failed to initialize in-memory backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the in-memory backend, releasing resources.
        
        Raises:
            StorageBackendError: If shutdown fails
        """
        try:
            # Release resources
            self.storage.clear_all_items()
            logger.info("In-memory backend shutdown successfully")
        except Exception as e:
            error_msg = f"Failed to shutdown in-memory backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the in-memory database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            StorageOperationError: If the store operation fails
        """
        try:
            # Convert MemoryItem to dict
            item_dict = memory_item.model_dump()
            
            # Delegate to the CRUD component
            success = await self.crud.create_item(memory_item.id, item_dict)
            
            if not success:
                raise StorageOperationError(f"Failed to store memory item {memory_item.id}")
            
            return memory_item.id
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from the in-memory database by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
            
        Raises:
            StorageOperationError: If the retrieve operation fails
        """
        try:
            # Delegate to the CRUD component
            item_dict = await self.crud.read_item(memory_id)
            
            if item_dict is None:
                return None
            
            # Convert dict back to MemoryItem
            return MemoryItem.model_validate(item_dict)
        except Exception as e:
            error_msg = f"Failed to retrieve memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the in-memory database.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            bool: True if update was successful, False if memory not found
            
        Raises:
            StorageOperationError: If the update operation fails
        """
        try:
            # Convert MemoryItem to dict
            item_dict = memory_item.model_dump()
            
            # Delegate to the CRUD component
            return await self.crud.update_item(memory_item.id, item_dict)
        except Exception as e:
            error_msg = f"Failed to update memory {memory_item.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the in-memory database.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            bool: True if deletion was successful, False if memory not found
            
        Raises:
            StorageOperationError: If the delete operation fails
        """
        try:
            # Delegate to the CRUD component
            return await self.crud.delete_item(memory_id)
        except Exception as e:
            error_msg = f"Failed to delete memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_store(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Store multiple memory items in a single transaction.
        
        Args:
            memory_items: List of memory items to store
            
        Returns:
            List[str]: List of stored memory IDs
            
        Raises:
            StorageOperationError: If the batch store operation fails
        """
        try:
            # Convert MemoryItems to dicts
            items_dict = {item.id: item.model_dump() for item in memory_items}
            
            # Delegate to the Batch component
            results = await self.batch.batch_create_items(items_dict)
            
            # Return IDs of successfully stored items
            return [item_id for item_id, success in results.items() if success]
        except Exception as e:
            error_msg = f"Failed to batch store memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_delete(self, memory_ids: List[str]) -> int:
        """
        Delete multiple memory items in a single transaction.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            int: Number of memories actually deleted
            
        Raises:
            StorageOperationError: If the batch delete operation fails
        """
        try:
            # Delegate to the Batch component
            results = await self.batch.batch_delete_items(memory_ids)
            
            # Count successful deletions
            deleted_count = sum(1 for success in results.values() if success)
            
            return deleted_count
        except Exception as e:
            error_msg = f"Failed to batch delete memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def search(
        self,
        query: str,
        filter: Optional[SearchFilter] = None,
        limit: int = 10,
        offset: int = 0
    ) -> SearchResults:
        """
        Search for memory items in the in-memory database.
        
        Args:
            query: Search query string
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            SearchResults: Search results containing memory items and metadata
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            # Convert SearchFilter to dict if provided
            filter_dict = filter.model_dump() if filter else None
            
            # Perform text search on content field
            matching_items = await self.search.text_search(
                query=query,
                fields=["content.text", "tags", "summary"],  # Search in these fields
                limit=None  # We'll apply filters and pagination below
            )
            
            # Apply filters if provided
            if filter_dict:
                filtered_items = []
                for item in matching_items:
                    if self.search._matches_filters(item, filter_dict):
                        filtered_items.append(item)
                matching_items = filtered_items
            
            # Apply pagination
            total_count = len(matching_items)
            matching_items = matching_items[offset:offset + limit]
            
            # Convert dicts back to MemoryItems
            memory_items = [MemoryItem.model_validate(item) for item in matching_items]
            
            # Create and return SearchResults
            return SearchResults(
                items=memory_items,
                total_count=total_count,
                offset=offset,
                limit=limit,
                query=query
            )
        except Exception as e:
            error_msg = f"Failed to search memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count(self, filter: Optional[SearchFilter] = None) -> int:
        """
        Count memory items matching the given filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        try:
            # Convert SearchFilter to dict if provided
            filter_dict = filter.model_dump() if filter else None
            
            # Delegate to the Search component
            return await self.search.count_items(filters=filter_dict)
        except Exception as e:
            error_msg = f"Failed to count memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the in-memory storage.
        
        Returns:
            StorageStats: Storage statistics
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Delegate to the Stats component
            return await self.stats.get_stats()
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
