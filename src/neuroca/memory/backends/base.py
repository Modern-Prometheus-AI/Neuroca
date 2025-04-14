"""
Base Storage Backend

This module provides the BaseStorageBackend class, which implements the
StorageBackendInterface and provides common functionality for all specific
storage backend implementations.
"""

import abc
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from neuroca.memory.exceptions import (
    StorageInitializationError,
    StorageOperationError,
    ItemExistsError,
    ItemNotFoundError,
    ConfigurationError,
)
from neuroca.memory.interfaces.storage_backend import StorageBackendInterface


logger = logging.getLogger(__name__)


class BaseStorageBackend(StorageBackendInterface, abc.ABC):
    """
    Base class for all storage backends.
    
    This class implements the StorageBackendInterface and provides common
    functionality for all specific storage backend implementations.
    
    Subclasses must implement the abstract methods for the specific
    database technology they support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the storage backend.
        
        Args:
            config: Backend-specific configuration options
        """
        self.config = config or {}
        self.initialized = False
        self._stats = {
            "created_at": datetime.now(),
            "last_operation_at": None,
            "operations_count": 0,
            "items_count": 0,
            "create_count": 0,
            "read_count": 0,
            "update_count": 0,
            "delete_count": 0,
            "query_count": 0,
        }
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the storage backend.
        
        This method must be called before any other method.
        
        Args:
            config: Optional additional configuration to merge with the existing config
            
        Raises:
            StorageInitializationError: If initialization fails
        """
        if config:
            self.config.update(config)
        
        try:
            await self._initialize_backend()
            self.initialized = True
            logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize {self.__class__.__name__}")
            raise StorageInitializationError(
                backend_type=self.__class__.__name__,
                message=f"Failed to initialize storage backend: {str(e)}"
            ) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the storage backend.
        
        This method should release all resources and ensure pending operations
        are completed.
        
        Raises:
            StorageOperationError: If shutdown fails
        """
        if not self.initialized:
            logger.warning(f"{self.__class__.__name__} shutdown called but not initialized")
            return
        
        try:
            await self._shutdown_backend()
            self.initialized = False
            logger.info(f"{self.__class__.__name__} shutdown successfully")
        except Exception as e:
            logger.exception(f"Failed to shutdown {self.__class__.__name__}")
            raise StorageOperationError(
                operation="shutdown",
                backend_type=self.__class__.__name__,
                message=f"Failed to shutdown storage backend: {str(e)}"
            ) from e
    
    async def create(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Create a new item in storage.
        
        Args:
            item_id: Unique identifier for the item
            data: Data to store
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemExistsError: If an item with the same ID already exists
            StorageOperationError: If the create operation fails
        """
        self._ensure_initialized()
        self._update_stats("create_count")
        
        if await self.exists(item_id):
            raise ItemExistsError(item_id=item_id)
        
        try:
            result = await self._create_item(item_id, data)
            if result:
                self._stats["items_count"] += 1
            return result
        except ItemExistsError:
            # Re-raise ItemExistsError if it was raised by _create_item
            raise
        except Exception as e:
            logger.exception(f"Failed to create item {item_id}")
            raise StorageOperationError(
                operation="create",
                backend_type=self.__class__.__name__,
                message=f"Failed to create item: {str(e)}"
            ) from e
    
    async def read(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data if found, None otherwise
            
        Raises:
            StorageOperationError: If the read operation fails
        """
        self._ensure_initialized()
        self._update_stats("read_count")
        
        try:
            return await self._read_item(item_id)
        except Exception as e:
            logger.exception(f"Failed to read item {item_id}")
            raise StorageOperationError(
                operation="read",
                backend_type=self.__class__.__name__,
                message=f"Failed to read item: {str(e)}"
            ) from e
    
    async def update(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing item.
        
        Args:
            item_id: The ID of the item to update
            data: New data for the item
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemNotFoundError: If the item with the given ID does not exist
            StorageOperationError: If the update operation fails
        """
        self._ensure_initialized()
        self._update_stats("update_count")
        
        if not await self.exists(item_id):
            raise ItemNotFoundError(item_id=item_id)
        
        try:
            return await self._update_item(item_id, data)
        except ItemNotFoundError:
            # Re-raise ItemNotFoundError if it was raised by _update_item
            raise
        except Exception as e:
            logger.exception(f"Failed to update item {item_id}")
            raise StorageOperationError(
                operation="update",
                backend_type=self.__class__.__name__,
                message=f"Failed to update item: {str(e)}"
            ) from e
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item by its ID.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            StorageOperationError: If the delete operation fails
        """
        self._ensure_initialized()
        self._update_stats("delete_count")
        
        try:
            result = await self._delete_item(item_id)
            if result:
                self._stats["items_count"] = max(0, self._stats["items_count"] - 1)
            return result
        except Exception as e:
            logger.exception(f"Failed to delete item {item_id}")
            raise StorageOperationError(
                operation="delete",
                backend_type=self.__class__.__name__,
                message=f"Failed to delete item: {str(e)}"
            ) from e
    
    async def exists(self, item_id: str) -> bool:
        """
        Check if an item exists.
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            bool: True if the item exists, False otherwise
            
        Raises:
            StorageOperationError: If the exists operation fails
        """
        self._ensure_initialized()
        
        try:
            return await self._item_exists(item_id)
        except Exception as e:
            logger.exception(f"Failed to check if item {item_id} exists")
            raise StorageOperationError(
                operation="exists",
                backend_type=self.__class__.__name__,
                message=f"Failed to check if item exists: {str(e)}"
            ) from e
    
    async def batch_create(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Create multiple items in a batch operation.
        
        Args:
            items: Dictionary mapping item IDs to their data
            
        Returns:
            Dictionary mapping item IDs to success status
            
        Raises:
            StorageOperationError: If the batch create operation fails
        """
        self._ensure_initialized()
        self._update_stats("create_count", len(items))
        
        existing_items = {}
        
        # Check which items already exist
        for item_id in items:
            if await self.exists(item_id):
                existing_items[item_id] = True
        
        # Filter out existing items
        filtered_items = {
            item_id: data 
            for item_id, data in items.items() 
            if item_id not in existing_items
        }
        
        if not filtered_items:
            # All items already exist
            return {item_id: False for item_id in items}
        
        try:
            result = await self._batch_create_items(filtered_items)
            # Add the existing items (which were not created) to the result
            for item_id in existing_items:
                result[item_id] = False
            
            # Update item count
            created_count = sum(1 for success in result.values() if success)
            self._stats["items_count"] += created_count
            
            return result
        except Exception as e:
            logger.exception(f"Failed to batch create {len(items)} items")
            raise StorageOperationError(
                operation="batch_create",
                backend_type=self.__class__.__name__,
                message=f"Failed to batch create items: {str(e)}"
            ) from e
    
    async def batch_read(self, item_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve multiple items in a batch operation.
        
        Args:
            item_ids: List of item IDs to retrieve
            
        Returns:
            Dictionary mapping item IDs to their data (or None if not found)
            
        Raises:
            StorageOperationError: If the batch read operation fails
        """
        self._ensure_initialized()
        self._update_stats("read_count", len(item_ids))
        
        try:
            return await self._batch_read_items(item_ids)
        except Exception as e:
            logger.exception(f"Failed to batch read {len(item_ids)} items")
            raise StorageOperationError(
                operation="batch_read",
                backend_type=self.__class__.__name__,
                message=f"Failed to batch read items: {str(e)}"
            ) from e
    
    async def batch_update(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Update multiple items in a batch operation.
        
        Args:
            items: Dictionary mapping item IDs to their new data
            
        Returns:
            Dictionary mapping item IDs to success status
            
        Raises:
            StorageOperationError: If the batch update operation fails
        """
        self._ensure_initialized()
        self._update_stats("update_count", len(items))
        
        try:
            return await self._batch_update_items(items)
        except Exception as e:
            logger.exception(f"Failed to batch update {len(items)} items")
            raise StorageOperationError(
                operation="batch_update",
                backend_type=self.__class__.__name__,
                message=f"Failed to batch update items: {str(e)}"
            ) from e
    
    async def batch_delete(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items in a batch operation.
        
        Args:
            item_ids: List of item IDs to delete
            
        Returns:
            Dictionary mapping item IDs to success status
            
        Raises:
            StorageOperationError: If the batch delete operation fails
        """
        self._ensure_initialized()
        self._update_stats("delete_count", len(item_ids))
        
        try:
            result = await self._batch_delete_items(item_ids)
            # Update item count
            deleted_count = sum(1 for success in result.values() if success)
            self._stats["items_count"] = max(0, self._stats["items_count"] - deleted_count)
            return result
        except Exception as e:
            logger.exception(f"Failed to batch delete {len(item_ids)} items")
            raise StorageOperationError(
                operation="batch_delete",
                backend_type=self.__class__.__name__,
                message=f"Failed to batch delete items: {str(e)}"
            ) from e
    
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
            
        Raises:
            StorageOperationError: If the query operation fails
        """
        self._ensure_initialized()
        self._update_stats("query_count")
        
        try:
            return await self._query_items(filters, sort_by, ascending, limit, offset)
        except Exception as e:
            logger.exception(f"Failed to query items")
            raise StorageOperationError(
                operation="query",
                backend_type=self.__class__.__name__,
                message=f"Failed to query items: {str(e)}"
            ) from e
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count items in storage, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        self._ensure_initialized()
        
        try:
            return await self._count_items(filters)
        except Exception as e:
            logger.exception(f"Failed to count items")
            raise StorageOperationError(
                operation="count",
                backend_type=self.__class__.__name__,
                message=f"Failed to count items: {str(e)}"
            ) from e
    
    async def clear(self) -> bool:
        """
        Clear all items from storage.
        
        Returns:
            bool: True if the operation was successful
            
        Raises:
            StorageOperationError: If the clear operation fails
        """
        self._ensure_initialized()
        
        try:
            result = await self._clear_all_items()
            if result:
                self._stats["items_count"] = 0
            return result
        except Exception as e:
            logger.exception(f"Failed to clear all items")
            raise StorageOperationError(
                operation="clear",
                backend_type=self.__class__.__name__,
                message=f"Failed to clear all items: {str(e)}"
            ) from e
    
    async def get_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics about the storage backend.
        
        Returns:
            Dictionary of statistics
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        self._ensure_initialized()
        
        try:
            # Get backend-specific stats
            backend_stats = await self._get_backend_stats()
            
            # Merge with base stats
            stats = {
                **self._stats,
                **backend_stats,
                "backend_type": self.__class__.__name__,
            }
            
            return stats
        except Exception as e:
            logger.exception(f"Failed to get stats")
            raise StorageOperationError(
                operation="get_stats",
                backend_type=self.__class__.__name__,
                message=f"Failed to get stats: {str(e)}"
            ) from e
    
    #-----------------------------------------------------------------------
    # Protected methods that subclasses must implement
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def _initialize_backend(self) -> None:
        """Initialize the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _shutdown_backend(self) -> None:
        """Shutdown the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _create_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """Create an item in the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _read_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Read an item from the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _update_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """Update an item in the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _delete_item(self, item_id: str) -> bool:
        """Delete an item from the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _item_exists(self, item_id: str) -> bool:
        """Check if an item exists in the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _query_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query items in the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _count_items(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count items in the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _clear_all_items(self) -> bool:
        """Clear all items from the specific backend."""
        pass
    
    @abc.abstractmethod
    async def _get_backend_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """Get statistics from the specific backend."""
        pass
    
    #-----------------------------------------------------------------------
    # Protected methods with default implementations that subclasses may override
    #-----------------------------------------------------------------------
    
    async def _batch_create_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Create multiple items in the specific backend.
        
        Default implementation calls _create_item for each item.
        Subclasses should override this method if the backend supports
        batch operations for better performance.
        """
        result = {}
        for item_id, data in items.items():
            try:
                result[item_id] = await self._create_item(item_id, data)
            except Exception as e:
                logger.warning(f"Failed to create item {item_id}: {str(e)}")
                result[item_id] = False
        return result
    
    async def _batch_read_items(self, item_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Read multiple items from the specific backend.
        
        Default implementation calls _read_item for each item.
        Subclasses should override this method if the backend supports
        batch operations for better performance.
        """
        result = {}
        for item_id in item_ids:
            try:
                result[item_id] = await self._read_item(item_id)
            except Exception as e:
                logger.warning(f"Failed to read item {item_id}: {str(e)}")
                result[item_id] = None
        return result
    
    async def _batch_update_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Update multiple items in the specific backend.
        
        Default implementation calls _update_item for each item.
        Subclasses should override this method if the backend supports
        batch operations for better performance.
        """
        result = {}
        for item_id, data in items.items():
            try:
                result[item_id] = await self._update_item(item_id, data)
            except Exception as e:
                logger.warning(f"Failed to update item {item_id}: {str(e)}")
                result[item_id] = False
        return result
    
    async def _batch_delete_items(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items from the specific backend.
        
        Default implementation calls _delete_item for each item.
        Subclasses should override this method if the backend supports
        batch operations for better performance.
        """
        result = {}
        for item_id in item_ids:
            try:
                result[item_id] = await self._delete_item(item_id)
            except Exception as e:
                logger.warning(f"Failed to delete item {item_id}: {str(e)}")
                result[item_id] = False
        return result
    
    #-----------------------------------------------------------------------
    # Private helper methods
    #-----------------------------------------------------------------------
    
    def _ensure_initialized(self) -> None:
        """
        Ensure the backend is initialized before operations.
        
        Raises:
            StorageOperationError: If the backend is not initialized
        """
        if not self.initialized:
            raise StorageOperationError(
                backend_type=self.__class__.__name__,
                message="Storage backend not initialized. Call initialize() first."
            )
    
    def _update_stats(self, operation_name: str, count: int = 1) -> None:
        """Update operation statistics."""
        self._stats["last_operation_at"] = datetime.now()
        self._stats["operations_count"] += count
        self._stats[operation_name] += count
