"""
In-Memory Batch Operations Component

This module provides a class for handling batch operations on memory items
in the in-memory storage, enabling more efficient multi-item operations.
"""

from typing import Any, Dict, List, Optional

from neuroca.memory.backends.in_memory.components.crud import InMemoryCRUD
from neuroca.memory.backends.in_memory.components.storage import InMemoryStorage


class InMemoryBatch:
    """
    Handles batch operations for memory items in in-memory storage.
    
    This class provides methods for performing operations on multiple memory
    items at once, with concurrency control and optimized performance.
    """
    
    def __init__(self, storage: InMemoryStorage, crud: InMemoryCRUD):
        """
        Initialize the batch operations handler.
        
        Args:
            storage: The storage component to use
            crud: The CRUD operations component to use
        """
        self.storage = storage
        self.crud = crud
    
    async def batch_create_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Create multiple items in the in-memory store.
        
        Args:
            items: Dictionary mapping item IDs to their data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        result = {}
        
        await self.storage.acquire_lock()
        try:
            for item_id, data in items.items():
                try:
                    # Check if item already exists
                    if self.storage.has_item(item_id):
                        result[item_id] = False
                        continue
                    
                    # Check if we need to evict an item
                    if self.storage.should_evict() and not self.storage.has_item(item_id):
                        self.storage.evict_oldest_item()
                    
                    # Prepare the data with metadata
                    data_with_meta = self.storage.prepare_item_metadata(data, is_new=True)
                    
                    # Store the item
                    self.storage.set_item(item_id, data_with_meta)
                    result[item_id] = True
                except Exception:
                    result[item_id] = False
        finally:
            self.storage.release_lock()
        
        return result
    
    async def batch_read_items(self, item_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Read multiple items from the in-memory store.
        
        Args:
            item_ids: List of item IDs to retrieve
            
        Returns:
            Dictionary mapping item IDs to their data (or None if not found)
        """
        result = {}
        
        await self.storage.acquire_lock()
        try:
            for item_id in item_ids:
                item = self.storage.get_item(item_id)
                
                if item is not None:
                    # Update access timestamp
                    item = self.storage.update_access_timestamp(item)
                    
                    # Store the updated data back
                    self.storage.set_item(item_id, item)
                
                result[item_id] = item
        finally:
            self.storage.release_lock()
        
        return result
    
    async def batch_update_items(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Update multiple items in the in-memory store.
        
        Args:
            items: Dictionary mapping item IDs to their new data
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        result = {}
        
        await self.storage.acquire_lock()
        try:
            for item_id, data in items.items():
                try:
                    # Check if item exists
                    if not self.storage.has_item(item_id):
                        result[item_id] = False
                        continue
                    
                    # Get the existing item
                    existing_data = self.storage.get_item(item_id)
                    
                    # Prepare the data with updated metadata
                    # We'll preserve existing metadata that's not being updated
                    if "_meta" in existing_data:
                        if "_meta" not in data:
                            data["_meta"] = existing_data["_meta"].copy()
                        else:
                            # Only update specified metadata fields
                            for k, v in existing_data["_meta"].items():
                                if k not in data["_meta"]:
                                    data["_meta"][k] = v
                    
                    # Update the data with metadata
                    data_with_meta = self.storage.prepare_item_metadata(data, is_new=False)
                    
                    # Store the updated item
                    self.storage.set_item(item_id, data_with_meta)
                    result[item_id] = True
                except Exception:
                    result[item_id] = False
        finally:
            self.storage.release_lock()
        
        return result
    
    async def batch_delete_items(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items from the in-memory store.
        
        Args:
            item_ids: List of item IDs to delete
            
        Returns:
            Dictionary mapping item IDs to success status
        """
        result = {}
        
        await self.storage.acquire_lock()
        try:
            for item_id in item_ids:
                result[item_id] = self.storage.delete_item(item_id)
        finally:
            self.storage.release_lock()
        
        return result
    
    async def batch_exists(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Check if multiple items exist in the in-memory store.
        
        Args:
            item_ids: List of item IDs to check
            
        Returns:
            Dictionary mapping item IDs to existence status
        """
        result = {}
        
        await self.storage.acquire_lock()
        try:
            for item_id in item_ids:
                result[item_id] = self.storage.has_item(item_id)
        finally:
            self.storage.release_lock()
        
        return result
