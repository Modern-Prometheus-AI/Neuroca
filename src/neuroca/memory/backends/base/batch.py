"""
Batch Operations Component

This module provides the BatchOperations class for handling batch operations
such as batch create, read, update, and delete operations.
"""

import abc
import logging
from typing import Any, Dict, List, Optional

from neuroca.memory.exceptions import StorageOperationError

logger = logging.getLogger(__name__)


class BatchOperations(abc.ABC):
    """
    Batch operations for storage backends.
    
    This class provides default implementations for batch operations
    by calling the single-item operations for each item. Specific backends
    that support native batch operations should override these methods
    for better performance.
    """
    
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
        try:
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
            
            # Use the backend-specific batch create method
            result = await self._batch_create_items(filtered_items)
            
            # Add the existing items (which were not created) to the result
            for item_id in existing_items:
                result[item_id] = False
            
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
        try:
            return await self._batch_delete_items(item_ids)
        except Exception as e:
            logger.exception(f"Failed to batch delete {len(item_ids)} items")
            raise StorageOperationError(
                operation="batch_delete",
                backend_type=self.__class__.__name__,
                message=f"Failed to batch delete items: {str(e)}"
            ) from e
    
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
