"""
Base Storage Backend Core Module

This module provides the BaseStorageBackend class, which integrates various
components to implement the StorageBackendInterface and provides common
functionality for all specific storage backend implementations.
"""

import abc
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from neuroca.memory.backends.base.batch import BatchOperations
from neuroca.memory.backends.base.operations import CoreOperations
from neuroca.memory.backends.base.stats import BackendStats
from neuroca.memory.exceptions import (
    StorageInitializationError,
    StorageOperationError,
    ConfigurationError,
)
from neuroca.memory.interfaces.storage_backend import StorageBackendInterface


logger = logging.getLogger(__name__)


class BaseStorageBackend(StorageBackendInterface, CoreOperations, BatchOperations, abc.ABC):
    """
    Base class for all storage backends.
    
    This class integrates the CoreOperations and BatchOperations components
    and implements the StorageBackendInterface. It provides common functionality
    for all specific storage backend implementations.
    
    Subclasses must implement the abstract methods for the specific
    database technology they support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the storage backend.
        
        Args:
            config: Backend-specific configuration options
        """
        CoreOperations.__init__(self)
        BatchOperations.__init__(self)
        
        self.config = config or {}
        self.stats = BackendStats()
    
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
    
    #-----------------------------------------------------------------------
    # Methods that update statistics
    #-----------------------------------------------------------------------
    
    async def create(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Create a new item in storage with statistics tracking.
        
        Args:
            item_id: Unique identifier for the item
            data: Data to store
            
        Returns:
            bool: True if the operation was successful
        """
        self.stats.update_stat("create_count")
        result = await CoreOperations.create(self, item_id, data)
        if result:
            self.stats.increment_items_count()
        return result
    
    async def read(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item by its ID with statistics tracking.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data if found, None otherwise
        """
        self.stats.update_stat("read_count")
        return await CoreOperations.read(self, item_id)
    
    async def update(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing item with statistics tracking.
        
        Args:
            item_id: The ID of the item to update
            data: New data for the item
            
        Returns:
            bool: True if the operation was successful
        """
        self.stats.update_stat("update_count")
        return await CoreOperations.update(self, item_id, data)
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item by its ID with statistics tracking.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if the operation was successful
        """
        self.stats.update_stat("delete_count")
        result = await CoreOperations.delete(self, item_id)
        if result:
            self.stats.decrement_items_count()
        return result
    
    async def batch_create(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Create multiple items in a batch operation with statistics tracking.
        
        Args:
            items: Dictionary mapping item IDs to their data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        self.stats.update_stat("create_count", len(items))
        result = await BatchOperations.batch_create(self, items)
        created_count = sum(1 for success in result.values() if success)
        if created_count > 0:
            self.stats.increment_items_count(created_count)
        return result
    
    async def batch_read(self, item_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve multiple items in a batch operation with statistics tracking.
        
        Args:
            item_ids: List of item IDs to retrieve
            
        Returns:
            Dictionary mapping item IDs to their data (or None if not found)
        """
        self.stats.update_stat("read_count", len(item_ids))
        return await BatchOperations.batch_read(self, item_ids)
    
    async def batch_update(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Update multiple items in a batch operation with statistics tracking.
        
        Args:
            items: Dictionary mapping item IDs to their new data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        self.stats.update_stat("update_count", len(items))
        return await BatchOperations.batch_update(self, items)
    
    async def batch_delete(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items in a batch operation with statistics tracking.
        
        Args:
            item_ids: List of item IDs to delete
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        self.stats.update_stat("delete_count", len(item_ids))
        result = await BatchOperations.batch_delete(self, item_ids)
        deleted_count = sum(1 for success in result.values() if success)
        if deleted_count > 0:
            self.stats.decrement_items_count(deleted_count)
        return result
    
    async def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items based on filter criteria with statistics tracking.
        
        Args:
            filters: Dict of field-value pairs to filter by
            sort_by: Field to sort results by
            ascending: Sort order (True for ascending, False for descending)
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of items matching the query criteria
        """
        self.stats.update_stat("query_count")
        return await CoreOperations.query(
            self, 
            filters=filters, 
            sort_by=sort_by, 
            ascending=ascending, 
            limit=limit, 
            offset=offset
        )
    
    async def clear(self) -> bool:
        """
        Clear all items from storage with statistics tracking.
        
        Returns:
            bool: True if the operation was successful
        """
        result = await CoreOperations.clear(self)
        if result:
            self.stats.set_items_count(0)
        return result
    
    async def get_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics about the storage backend.
        
        Returns:
            Dictionary of statistics
        """
        try:
            # Get backend-specific stats
            backend_stats = await self._get_backend_stats()
            
            # Merge with base stats
            stats = self.stats.merge_stats(backend_stats)
            stats["backend_type"] = self.__class__.__name__
            
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
    async def _get_backend_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """Get statistics from the specific backend."""
        pass
