"""
Core Storage Operations Component

This module provides the CoreOperations class for implementing basic
CRUD operations that all storage backends must support.
"""

import abc
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from neuroca.memory.exceptions import (
    StorageOperationError,
    ItemExistsError,
    ItemNotFoundError,
)

logger = logging.getLogger(__name__)


class CoreOperations(abc.ABC):
    """
    Core storage operations for all backends.
    
    This class defines the abstract methods for basic CRUD operations
    that all storage backends must implement, along with common functionality
    for checking preconditions and handling errors.
    """
    
    def __init__(self):
        """Initialize core operations."""
        self.initialized = False
    
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
        
        if await self.exists(item_id):
            raise ItemExistsError(item_id=item_id)
        
        try:
            return await self._create_item(item_id, data)
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
        
        try:
            return await self._delete_item(item_id)
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
            return await self._clear_all_items()
        except Exception as e:
            logger.exception(f"Failed to clear all items")
            raise StorageOperationError(
                operation="clear",
                backend_type=self.__class__.__name__,
                message=f"Failed to clear all items: {str(e)}"
            ) from e
    
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
    
    #-----------------------------------------------------------------------
    # Abstract methods that subclasses must implement
    #-----------------------------------------------------------------------
    
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
