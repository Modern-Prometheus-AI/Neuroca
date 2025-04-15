"""
In-Memory CRUD Operations Component

This module provides a class for handling CRUD (Create, Read, Update, Delete)
operations on memory items in the in-memory storage.
"""

from typing import Any, Dict, Optional

from neuroca.memory.backends.in_memory.components.storage import InMemoryStorage
from neuroca.memory.exceptions import ItemExistsError, ItemNotFoundError


class InMemoryCRUD:
    """
    Handles CRUD operations for memory items in in-memory storage.
    
    This class provides methods for storing, retrieving, updating, and
    deleting memory items in the storage component.
    """
    
    def __init__(self, storage: InMemoryStorage):
        """
        Initialize the CRUD operations handler.
        
        Args:
            storage: The storage component to use
        """
        self.storage = storage
    
    async def create_item(self, item_id: str, data: Dict[str, Any]) -> bool:
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
        await self.storage.acquire_lock()
        try:
            # Check if item already exists
            if self.storage.has_item(item_id):
                raise ItemExistsError(item_id=item_id)
            
            # Check if we need to evict an item
            if self.storage.should_evict() and not self.storage.has_item(item_id):
                self.storage.evict_oldest_item()
            
            # Prepare the data with metadata
            data_with_meta = self.storage.prepare_item_metadata(data, is_new=True)
            
            # Store the item
            self.storage.set_item(item_id, data_with_meta)
            return True
        finally:
            self.storage.release_lock()
    
    async def read_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Read an item from the in-memory store.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data if found, None otherwise
        """
        await self.storage.acquire_lock()
        try:
            # Get the item from storage
            data = self.storage.get_item(item_id)
            
            if data is None:
                return None
            
            # Update access timestamp
            data = self.storage.update_access_timestamp(data)
            
            # Store the updated data back
            self.storage.set_item(item_id, data)
            
            return data
        finally:
            self.storage.release_lock()
    
    async def update_item(self, item_id: str, data: Dict[str, Any]) -> bool:
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
        await self.storage.acquire_lock()
        try:
            # Check if item exists
            if not self.storage.has_item(item_id):
                raise ItemNotFoundError(item_id=item_id)
            
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
            return True
        finally:
            self.storage.release_lock()
    
    async def delete_item(self, item_id: str) -> bool:
        """
        Delete an item from the in-memory store.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if the item was deleted, False if it didn't exist
        """
        await self.storage.acquire_lock()
        try:
            return self.storage.delete_item(item_id)
        finally:
            self.storage.release_lock()
    
    async def item_exists(self, item_id: str) -> bool:
        """
        Check if an item exists in the in-memory store.
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            bool: True if the item exists, False otherwise
        """
        await self.storage.acquire_lock()
        try:
            return self.storage.has_item(item_id)
        finally:
            self.storage.release_lock()
    
    async def clear_all_items(self) -> bool:
        """
        Clear all items from the in-memory store.
        
        Returns:
            bool: True if the operation was successful
        """
        await self.storage.acquire_lock()
        try:
            self.storage.clear_all_items()
            return True
        finally:
            self.storage.release_lock()
