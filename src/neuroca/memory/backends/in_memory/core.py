"""
In-Memory Storage Backend Core

This module provides the main InMemoryBackend class that integrates all in-memory
component modules to implement the BaseStorageBackend interface for the memory system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.in_memory.components.batch import InMemoryBatch
from neuroca.memory.backends.in_memory.components.crud import InMemoryCRUD
from neuroca.memory.backends.in_memory.components.search import InMemorySearch
from neuroca.memory.backends.in_memory.components.stats import InMemoryStats
from neuroca.memory.backends.in_memory.components.storage import InMemoryStorage
from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError, StorageOperationError
from neuroca.memory.interfaces import StorageStats
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import MemorySearchOptions as SearchFilter, MemorySearchResults as SearchResults

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
        self.initialized = False
        
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
    
    # Implementation of required abstract methods from BaseStorageBackend
    async def _initialize_backend(self) -> None:
        """Initialize the specific backend implementation."""
        # Nothing special to initialize for in-memory backend
        logger.info("Initialized in-memory backend")
        self.initialized = True
    
    async def _shutdown_backend(self) -> None:
        """Shutdown the specific backend implementation."""
        # Release resources
        self.storage.clear_all_items()
        logger.info("In-memory backend shutdown successfully")
        self.initialized = False
    
    async def _get_backend_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """Get statistics from the specific backend."""
        stats_obj = await self.stats.get_stats()
        # Convert StorageStats to a dictionary
        return stats_obj.model_dump() if hasattr(stats_obj, "model_dump") else {"items_count": self.storage.count()}
    
    # Additional required abstract methods
    async def _create_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """Create a new item in storage."""
        return await self.crud.create_item(item_id, data)
    
    async def _read_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Read an item from storage."""
        return await self.crud.read_item(item_id)
    
    async def _update_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """Update an item in storage."""
        return await self.crud.update_item(item_id, data)
    
    async def _delete_item(self, item_id: str) -> bool:
        """Delete an item from storage."""
        return await self.crud.delete_item(item_id)
    
    async def _item_exists(self, item_id: str) -> bool:
        """Check if an item exists in storage."""
        return await self.crud.item_exists(item_id)
    
    async def _query_items(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query items in storage."""
        return await self.search.filter_items(filters=query)
    
    async def _count_items(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count items in storage."""
        if query:
            return await self.search.count_items(filters=query)
        else:
            return self.storage.count()
    
    async def _clear_all_items(self) -> bool:
        """Clear all items from storage."""
        self.storage.clear_all_items()
        return True
    
    # Core CRUD operations implementation
    async def create(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Create a new item in storage.
        
        Args:
            item_id: Unique identifier for the item
            data: Data to store
            
        Returns:
            bool: True if the operation was successful
        """
        try:
            return await self.crud.create_item(item_id, data)
        except Exception as e:
            error_msg = f"Failed to create item {item_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def read(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data if found, None otherwise
        """
        try:
            return await self.crud.read_item(item_id)
        except Exception as e:
            error_msg = f"Failed to read item {item_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing item.
        
        Args:
            item_id: The ID of the item to update
            data: New data for the item
            
        Returns:
            bool: True if the operation was successful
        """
        try:
            return await self.crud.update_item(item_id, data)
        except Exception as e:
            error_msg = f"Failed to update item {item_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item by its ID.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if the operation was successful
        """
        try:
            return await self.crud.delete_item(item_id)
        except Exception as e:
            error_msg = f"Failed to delete item {item_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def exists(self, item_id: str) -> bool:
        """
        Check if an item exists.
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            bool: True if the item exists, False otherwise
        """
        try:
            return await self.crud.item_exists(item_id)
        except Exception as e:
            error_msg = f"Failed to check existence of item {item_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    # Batch operations implementation
    async def batch_create(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Create multiple items in a batch operation.
        
        Args:
            items: Dictionary mapping item IDs to their data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        try:
            return await self.batch.batch_create_items(items)
        except Exception as e:
            error_msg = f"Failed to batch create items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_read(self, item_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve multiple items in a batch operation.
        
        Args:
            item_ids: List of item IDs to retrieve
            
        Returns:
            Dictionary mapping item IDs to their data (or None if not found)
        """
        try:
            return await self.batch.batch_read_items(item_ids)
        except Exception as e:
            error_msg = f"Failed to batch read items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_update(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Update multiple items in a batch operation.
        
        Args:
            items: Dictionary mapping item IDs to their new data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        try:
            return await self.batch.batch_update_items(items)
        except Exception as e:
            error_msg = f"Failed to batch update items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_delete(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items in a batch operation.
        
        Args:
            item_ids: List of item IDs to delete
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        try:
            return await self.batch.batch_delete_items(item_ids)
        except Exception as e:
            error_msg = f"Failed to batch delete items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    # Query operations implementation
    async def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items based on filter criteria.
        
        Args:
            filters: Dict of field-value pairs to filter by
            sort_by: Field to sort results by
            ascending: Sort order (True for ascending, False for descending)
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of items matching the query criteria
        """
        try:
            return await self.search.filter_items(
                filters=filters,
                sort_by=sort_by,
                ascending=ascending,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            error_msg = f"Failed to query items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    # Maintenance operations implementation
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count items in storage, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching items
        """
        try:
            if filters:
                return await self.search.count_items(filters=filters)
            else:
                return self.storage.count()
        except Exception as e:
            error_msg = f"Failed to count items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def clear(self) -> bool:
        """
        Clear all items from storage.
        
        Returns:
            bool: True if the operation was successful
        """
        try:
            self.storage.clear_all_items()
            return True
        except Exception as e:
            error_msg = f"Failed to clear storage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics about the storage backend.
        
        Returns:
            Dictionary of statistics
        """
        try:
            stats_obj = await self.stats.get_stats()
            if hasattr(stats_obj, "model_dump"):
                return stats_obj.model_dump()
            return {
                "items_count": self.storage.count(),
                "backend_type": "InMemoryBackend",
                "timestamp": datetime.now()
            }
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    # Legacy method compatibility (mapping to standard interface)
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the in-memory database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
        """
        item_dict = memory_item.model_dump()
        success = await self.create(memory_item.id, item_dict)
        if not success:
            raise StorageOperationError(f"Failed to store memory item {memory_item.id}")
        return memory_item.id
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from the in-memory database by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
        """
        item_dict = await self.read(memory_id)
        if item_dict is None:
            return None
        return MemoryItem.model_validate(item_dict)
    
    async def batch_store(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Store multiple memory items in a single transaction.
        
        Args:
            memory_items: List of memory items to store
            
        Returns:
            List[str]: List of stored memory IDs
        """
        items_dict = {item.id: item.model_dump() for item in memory_items}
        results = await self.batch_create(items_dict)
        return [item_id for item_id, success in results.items() if success]
    
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
        """
        filter_dict = filter.model_dump() if filter else None
        
        matching_items = await self.search.text_search(
            query=query,
            fields=["content.text", "tags", "summary"],
            limit=None
        )
        
        if filter_dict:
            filtered_items = []
            for item in matching_items:
                if self.search._matches_filters(item, filter_dict):
                    filtered_items.append(item)
            matching_items = filtered_items
        
        total_count = len(matching_items)
        matching_items = matching_items[offset:offset + limit]
        
        memory_items = [MemoryItem.model_validate(item) for item in matching_items]
        
        return SearchResults(
            items=memory_items,
            total_count=total_count,
            offset=offset,
            limit=limit,
            query=query
        )
