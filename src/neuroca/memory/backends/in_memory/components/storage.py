"""
In-Memory Storage Component

This module provides the core storage functionality for the in-memory backend,
including data structures and management operations.
"""

import asyncio
import copy
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


class InMemoryStorage:
    """
    Core storage functionality for the in-memory backend.
    
    This class manages the internal data structures that store the memory items,
    handles locking for concurrent access, and provides utility methods for
    data operations.
    """
    
    def __init__(self, max_items: Optional[int] = None):
        """
        Initialize the storage component.
        
        Args:
            max_items: Maximum number of items to store (defaults to no limit)
        """
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self.max_items = max_items
    
    async def acquire_lock(self) -> None:
        """
        Acquire the storage lock.
        
        This method should be called before any operation that modifies
        the storage.
        """
        await self._lock.acquire()
    
    def release_lock(self) -> None:
        """
        Release the storage lock.
        
        This method should be called after operations that modify
        the storage are complete.
        """
        if self._lock.locked():
            self._lock.release()
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item from storage by ID (no locking).
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data if found, None otherwise
        """
        if item_id not in self._data:
            return None
        
        # Return a deep copy to ensure data isolation
        return copy.deepcopy(self._data[item_id])
    
    def set_item(self, item_id: str, data: Dict[str, Any]) -> None:
        """
        Set an item in storage (no locking).
        
        Args:
            item_id: The ID of the item to set
            data: The data to store
        """
        # Store a deep copy to ensure data isolation
        self._data[item_id] = copy.deepcopy(data)
    
    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item from storage (no locking).
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if the item was deleted, False if it didn't exist
        """
        if item_id not in self._data:
            return False
        
        del self._data[item_id]
        return True
    
    def has_item(self, item_id: str) -> bool:
        """
        Check if an item exists in storage (no locking).
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            bool: True if the item exists, False otherwise
        """
        return item_id in self._data
    
    def get_all_items(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all items in storage (no locking).
        
        Returns:
            A deep copy of all stored items
        """
        # Return a deep copy to ensure data isolation
        return copy.deepcopy(self._data)
    
    def clear_all_items(self) -> None:
        """
        Clear all items from storage (no locking).
        """
        self._data.clear()
    
    def count_items(self) -> int:
        """
        Count the number of items in storage (no locking).
        
        Returns:
            The number of items in storage
        """
        return len(self._data)
    
    def evict_oldest_item(self) -> Optional[str]:
        """
        Evict the oldest item from storage when max_items is reached.
        
        Returns:
            The ID of the evicted item, or None if no item was evicted
        """
        if not self._data:
            return None
            
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
            return oldest_id
        else:
            # If we couldn't determine the oldest by timestamp, remove the first item
            if self._data:
                first_id = next(iter(self._data))
                del self._data[first_id]
                return first_id
            
        return None
    
    def prepare_item_metadata(self, data: Dict[str, Any], is_new: bool = False) -> Dict[str, Any]:
        """
        Prepare item metadata for storage.
        
        Args:
            data: The item data
            is_new: Whether this is a new item (True) or an update (False)
            
        Returns:
            The data with updated metadata
        """
        # Create a deep copy to ensure data isolation
        data_copy = copy.deepcopy(data)
        
        # Add or update metadata
        if "_meta" not in data_copy:
            data_copy["_meta"] = {}
        
        # Set timestamps
        now = datetime.now().isoformat()
        
        if is_new:
            data_copy["_meta"]["created_at"] = now
        
        data_copy["_meta"]["updated_at"] = now
        
        return data_copy
    
    def update_access_timestamp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the last accessed timestamp in the item's metadata.
        
        Args:
            data: The item data
            
        Returns:
            The data with updated last_accessed timestamp
        """
        # Create a deep copy to ensure data isolation
        data_copy = copy.deepcopy(data)
        
        # Add or update metadata
        if "_meta" not in data_copy:
            data_copy["_meta"] = {}
        
        # Set last accessed timestamp
        data_copy["_meta"]["last_accessed"] = datetime.now().isoformat()
        
        return data_copy
    
    def should_evict(self) -> bool:
        """
        Check if we should evict an item based on max_items.
        
        Returns:
            bool: True if an item should be evicted, False otherwise
        """
        if self.max_items is None:
            return False
            
        return len(self._data) >= self.max_items
