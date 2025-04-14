"""
In-Memory Storage Backend

This module provides an in-memory implementation of the StorageBackendInterface,
which is useful for development, testing, and small-scale deployments.

All data is stored in memory using Python dictionaries and is not persisted
across application restarts.
"""

import asyncio
import copy
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.exceptions import ItemExistsError, ItemNotFoundError


class InMemoryBackend(BaseStorageBackend):
    """
    In-memory implementation of the StorageBackendInterface.
    
    This backend stores all data in memory using Python dictionaries.
    It is useful for development, testing, and small-scale deployments,
    but will not persist data across application restarts.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the in-memory backend.
        
        Args:
            config: Optional configuration parameters:
                - max_items: Maximum number of items to store (defaults to no limit)
        """
        super().__init__(config)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def _initialize_backend(self) -> None:
        """Initialize the in-memory backend."""
        # Nothing special to initialize for in-memory backend
        pass
    
    async def _shutdown_backend(self) -> None:
        """Shutdown the in-memory backend."""
        # Clear data to release memory
        self._data.clear()
    
    async def _create_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Create an item in the in-memory store.
        
        Args:
            item_id: Unique identifier for the item
            data: Data to store
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemExistsError: If an item with the same ID already exists
        """
        # Create a deep copy to ensure data isolation
        data_copy = copy.deepcopy(data)
        
        # Add metadata
        if "_meta" not in data_copy:
            data_copy["_meta"] = {}
        
        data_copy["_meta"]["created_at"] = datetime.now().isoformat()
        data_copy["_meta"]["updated_at"] = datetime.now().isoformat()
        
        # Get config parameter for max items
        max_items = self.config.get("max_items")
        
        async with self._lock:
            # Check if maximum number of items is reached
            if max_items is not None and len(self._data) >= max_items and item_id not in self._data:
                # Evict the oldest item
                self._evict_oldest_item()
            
            # Check if item already exists
            if item_id in self._data:
                raise ItemExistsError(item_id=item_id)
            
            self._data[item_id] = data_copy
            return True
    
    async def _read_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Read an item from the in-memory store.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data if found, None otherwise
        """
        async with self._lock:
            if item_id not in self._data:
                return None
            
            # Return a deep copy to ensure data isolation
            data = copy.deepcopy(self._data[item_id])
            
            # Update access metadata
            if "_meta" in data:
                data["_meta"]["last_accessed"] = datetime.now().isoformat()
            
            return data
    
    async def _update_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an item in the in-memory store.
        
        Args:
            item_id: The ID of the item to update
            data: New data for the item
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemNotFoundError: If the item with the given ID does not exist
        """
        # Create a deep copy to ensure data isolation
        data_copy = copy.deepcopy(data)
        
        async with self._lock:
            if item_id not in self._data:
                raise ItemNotFoundError(item_id=item_id)
            
            # Preserve metadata from the existing item
            if "_meta" in self._data[item_id]:
                if "_meta" not in data_copy:
                    data_copy["_meta"] = self._data[item_id]["_meta"].copy()
                else:
                    # Only update specified metadata fields
                    for k, v in self._data[item_id]["_meta"].items():
                        if k not in data_copy["_meta"]:
                            data_copy["_meta"][k] = v
            
            # Update metadata
            if "_meta" not in data_copy:
                data_copy["_meta"] = {}
            
            data_copy["_meta"]["updated_at"] = datetime.now().isoformat()
            
            # Update the item
            self._data[item_id] = data_copy
            return True
    
    async def _delete_item(self, item_id: str) -> bool:
        """
        Delete an item from the in-memory store.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if the item was deleted, False if it didn't exist
        """
        async with self._lock:
            if item_id not in self._data:
                return False
            
            del self._data[item_id]
            return True
    
    async def _item_exists(self, item_id: str) -> bool:
        """
        Check if an item exists in the in-memory store.
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            bool: True if the item exists, False otherwise
        """
        async with self._lock:
            return item_id in self._data
    
    async def _query_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items in the in-memory store.
        
        Args:
            filters: Dict of field-value pairs to filter by
            sort_by: Field to sort results by
            ascending: Sort order (True for ascending, False for descending)
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of items matching the query criteria
        """
        filters = filters or {}
        
        async with self._lock:
            # Make a copy of all items with their IDs
            items_with_ids = [
                {"_id": item_id, **copy.deepcopy(data)}
                for item_id, data in self._data.items()
            ]
            
            # Apply filters
            if filters:
                filtered_items = []
                for item in items_with_ids:
                    if self._matches_filters(item, filters):
                        filtered_items.append(item)
                items_with_ids = filtered_items
            
            # Apply sorting
            if sort_by:
                items_with_ids = sorted(
                    items_with_ids,
                    key=lambda x: self._get_field_value(x, sort_by),
                    reverse=not ascending,
                )
            
            # Apply pagination
            if offset:
                items_with_ids = items_with_ids[offset:]
            if limit:
                items_with_ids = items_with_ids[:limit]
            
            return items_with_ids
    
    async def _count_items(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count items in the in-memory store.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching items
        """
        if not filters:
            async with self._lock:
                return len(self._data)
        
        # If filters are provided, we need to check each item
        results = await self._query_items(filters=filters)
        return len(results)
    
    async def _clear_all_items(self) -> bool:
        """
        Clear all items from the in-memory store.
        
        Returns:
            bool: True if the operation was successful
        """
        async with self._lock:
            self._data.clear()
            return True
    
    async def _get_backend_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics about the in-memory backend.
        
        Returns:
            Dictionary of statistics
        """
        storage_size = 0
        metadata_size = 0
        created_timestamps = []
        
        async with self._lock:
            for item_id, data in self._data.items():
                # Approximate size calculation
                item_size = len(str(data))
                storage_size += item_size
                
                # Metadata size
                if "_meta" in data:
                    meta_size = len(str(data["_meta"]))
                    metadata_size += meta_size
                    
                    # Collect creation timestamps for average age calculation
                    if "created_at" in data["_meta"]:
                        try:
                            created_at = datetime.fromisoformat(data["_meta"]["created_at"])
                            created_timestamps.append(created_at)
                        except (ValueError, TypeError):
                            pass
        
        # Calculate average age
        avg_age_seconds = 0
        if created_timestamps:
            now = datetime.now()
            total_age = sum((now - created_at).total_seconds() for created_at in created_timestamps)
            avg_age_seconds = total_age / len(created_timestamps)
        
        return {
            "backend_type": "InMemoryBackend",
            "storage_size_bytes": storage_size,
            "metadata_size_bytes": metadata_size,
            "average_age_seconds": avg_age_seconds,
            "max_items": self.config.get("max_items", "unlimited"),
        }
    
    #-----------------------------------------------------------------------
    # Batch operations (overriding defaults for better performance)
    #-----------------------------------------------------------------------
    
    async def _batch_create_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Create multiple items in the in-memory store.
        
        Args:
            items: Dictionary mapping item IDs to their data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        result = {}
        
        async with self._lock:
            for item_id, data in items.items():
                try:
                    # We need to release the lock to allow _create_item to acquire it
                    await self._lock.release()
                    result[item_id] = await self._create_item(item_id, data)
                    await self._lock.acquire()
                except Exception as e:
                    result[item_id] = False
                    # Re-acquire the lock if an exception occurred
                    if not self._lock.locked():
                        await self._lock.acquire()
        
        return result
    
    async def _batch_read_items(self, item_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Read multiple items from the in-memory store.
        
        Args:
            item_ids: List of item IDs to retrieve
            
        Returns:
            Dictionary mapping item IDs to their data (or None if not found)
        """
        result = {}
        
        async with self._lock:
            for item_id in item_ids:
                if item_id in self._data:
                    # Return a deep copy to ensure data isolation
                    data = copy.deepcopy(self._data[item_id])
                    
                    # Update access metadata
                    if "_meta" in data:
                        data["_meta"]["last_accessed"] = datetime.now().isoformat()
                    
                    result[item_id] = data
                else:
                    result[item_id] = None
        
        return result
    
    async def _batch_update_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Update multiple items in the in-memory store.
        
        Args:
            items: Dictionary mapping item IDs to their new data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        result = {}
        
        async with self._lock:
            for item_id, data in items.items():
                try:
                    # We need to release the lock to allow _update_item to acquire it
                    await self._lock.release()
                    result[item_id] = await self._update_item(item_id, data)
                    await self._lock.acquire()
                except Exception as e:
                    result[item_id] = False
                    # Re-acquire the lock if an exception occurred
                    if not self._lock.locked():
                        await self._lock.acquire()
        
        return result
    
    async def _batch_delete_items(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items from the in-memory store.
        
        Args:
            item_ids: List of item IDs to delete
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        result = {}
        
        async with self._lock:
            for item_id in item_ids:
                if item_id in self._data:
                    del self._data[item_id]
                    result[item_id] = True
                else:
                    result[item_id] = False
        
        return result
    
    #-----------------------------------------------------------------------
    # Helper methods
    #-----------------------------------------------------------------------
    
    def _evict_oldest_item(self) -> None:
        """Evict the oldest item from the store when max_items is reached."""
        oldest_id = None
        oldest_timestamp = None
        
        for item_id, data in self._data.items():
            if "_meta" in data and "created_at" in data["_meta"]:
                try:
                    timestamp = datetime.fromisoformat(data["_meta"]["created_at"])
                    if oldest_timestamp is None or timestamp < oldest_timestamp:
                        oldest_timestamp = timestamp
                        oldest_id = item_id
                except (ValueError, TypeError):
                    pass
        
        # If we found an oldest item, remove it
        if oldest_id:
            del self._data[oldest_id]
        else:
            # If we couldn't determine the oldest by timestamp, remove the first item
            if self._data:
                first_id = next(iter(self._data))
                del self._data[first_id]
    
    def _matches_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if an item matches the given filters.
        
        Args:
            item: The item to check
            filters: Dict of field-value pairs to filter by
            
        Returns:
            bool: True if the item matches all filters, False otherwise
        """
        for field, value in filters.items():
            if field.startswith("_meta."):
                # Handle nested fields in metadata
                meta_field = field.split(".", 1)[1]
                if "_meta" not in item or meta_field not in item["_meta"]:
                    return False
                
                if item["_meta"][meta_field] != value:
                    return False
            elif field == "_id":
                # Special case for item ID
                if item.get("_id") != value:
                    return False
            elif "." in field:
                # Handle nested fields
                field_parts = field.split(".")
                current = item
                
                for part in field_parts:
                    if not isinstance(current, dict) or part not in current:
                        return False
                    current = current[part]
                
                if current != value:
                    return False
            elif field not in item:
                return False
            elif item[field] != value:
                return False
        
        return True
    
    def _get_field_value(self, item: Dict[str, Any], field: str) -> Any:
        """
        Get the value of a field from an item, handling nested fields.
        
        Args:
            item: The item to get the field value from
            field: The field to get
            
        Returns:
            The field value or None if not found
        """
        if field == "_id":
            return item.get("_id")
        
        if field.startswith("_meta."):
            meta_field = field.split(".", 1)[1]
            if "_meta" in item and meta_field in item["_meta"]:
                return item["_meta"][meta_field]
            return None
        
        if "." in field:
            field_parts = field.split(".")
            current = item
            
            for part in field_parts:
                if not isinstance(current, dict) or part not in current:
                    return None
                current = current[part]
            
            return current
        
        return item.get(field)
