"""
Short-Term Memory (STM) Storage Module.

This module provides the storage implementation for the Short-Term Memory component
of the NeuroCognitive Architecture. It handles persistence, retrieval, and management
of short-term memory items with appropriate time-based decay mechanisms.

The STM storage is designed to:
1. Store memory items with timestamps and metadata
2. Support efficient retrieval with filtering capabilities
3. Implement automatic decay of items based on configurable parameters
4. Provide transaction support for data consistency
5. Handle concurrent access safely

Usage:
    storage = STMStorage()
    
    # Store a memory item
    item_id = await storage.store(
        content="Meeting with John at 3pm",
        metadata={"source": "calendar", "importance": 0.8}
    )
    
    # Retrieve items
    items = await storage.retrieve(limit=10, filter_criteria={"source": "calendar"})
    
    # Update an item
    await storage.update(item_id, {"importance": 0.9})
    
    # Delete an item
    await storage.delete(item_id)
"""

import asyncio
import contextlib
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Union

import aiofiles
import aiofiles.os
from pydantic import BaseModel, Field, ValidationError

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import (
    ItemNotFoundError,
    StorageInitializationError,
    StorageOperationError,
)
from neuroca.core.models.memory import MemoryItem

# Configure logger
logger = logging.getLogger(__name__)


class STMStorageConfig(BaseModel):
    """Configuration for STM Storage."""
    
    base_path: Path = Field(
        default_factory=lambda: Path(get_settings().storage_path) / "stm"
    )
    max_items: int = Field(default=1000, ge=1, description="Maximum number of items to store")
    default_ttl: int = Field(
        default=3600, 
        ge=1, 
        description="Default time-to-live for items in seconds"
    )
    cleanup_interval: int = Field(
        default=300, 
        ge=10, 
        description="Interval between cleanup operations in seconds"
    )
    file_extension: str = Field(default=".json", description="File extension for stored items")
    use_compression: bool = Field(default=True, description="Whether to compress stored data")
    index_file: str = Field(default="index.json", description="Name of the index file")


class STMStorage:
    """
    Storage implementation for Short-Term Memory (STM).
    
    This class provides persistent storage for short-term memory items with
    automatic time-based decay and efficient retrieval mechanisms.
    
    Attributes:
        config (STMStorageConfig): Configuration for the storage
        _index (Dict[str, Dict]): In-memory index of stored items
        _lock (asyncio.Lock): Lock for thread-safe operations
        _cleanup_task (Optional[asyncio.Task]): Background task for cleanup operations
    """
    
    def __init__(self, config: Optional[STMStorageConfig] = None):
        """
        Initialize the STM storage.
        
        Args:
            config: Optional configuration for the storage. If not provided,
                   default configuration will be used.
        """
        self.config = config or STMStorageConfig()
        self._index: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """
        Initialize the storage system.
        
        This method:
        1. Creates necessary directories
        2. Loads existing index if available
        3. Starts the background cleanup task
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(self.config.base_path, exist_ok=True)
            
            # Load existing index if available
            index_path = self.config.base_path / self.config.index_file
            if os.path.exists(index_path):
                async with aiofiles.open(index_path, 'r') as f:
                    content = await f.read()
                    self._index = json.loads(content)
                logger.info(f"Loaded {len(self._index)} items from STM index")
            else:
                logger.info("No existing STM index found, starting with empty index")
            
            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._run_periodic_cleanup())
            logger.debug("Started STM storage cleanup task")
            
        except Exception as e:
            error_msg = f"Failed to initialize STM storage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the storage system gracefully.
        
        This method:
        1. Cancels the background cleanup task
        2. Persists the current index
        
        Raises:
            StorageOperationError: If shutdown operations fail
        """
        try:
            # Cancel cleanup task if running
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._cleanup_task

                logger.debug("Cancelled STM storage cleanup task")
            
            # Persist index
            await self._persist_index()
            logger.info("STM storage shutdown complete")
            
        except Exception as e:
            error_msg = f"Error during STM storage shutdown: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def store(
        self, 
        content: Any, 
        metadata: Optional[dict[str, Any]] = None, 
        ttl: Optional[int] = None
    ) -> str:
        """
        Store a new memory item.
        
        Args:
            content: The content to store
            metadata: Optional metadata associated with the content
            ttl: Optional time-to-live in seconds, defaults to config.default_ttl
        
        Returns:
            str: The ID of the stored item
        
        Raises:
            StorageOperationError: If the storage operation fails
        """
        try:
            item_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            expiry_time = (
                datetime.utcnow() + timedelta(seconds=ttl or self.config.default_ttl)
            ).timestamp()
            
            item = {
                "id": item_id,
                "content": content,
                "metadata": metadata or {},
                "created_at": timestamp,
                "updated_at": timestamp,
                "expires_at": expiry_time
            }
            
            # Validate using Pydantic
            try:
                MemoryItem(**item)
            except ValidationError as e:
                raise ValueError(f"Invalid memory item: {e}") from e
            
            async with self._lock:
                # Check if we need to make room for new items
                if len(self._index) >= self.config.max_items:
                    await self._remove_oldest_items(1)
                
                # Store the item
                item_path = self._get_item_path(item_id)
                async with aiofiles.open(item_path, 'w') as f:
                    await f.write(json.dumps(item))
                
                # Update index
                self._index[item_id] = {
                    "path": str(item_path),
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "expires_at": expiry_time,
                    "metadata": metadata or {}
                }
                
                # Persist index periodically (could optimize to not write on every store)
                await self._persist_index()
            
            logger.debug(f"Stored STM item with ID: {item_id}")
            return item_id
            
        except Exception as e:
            error_msg = f"Failed to store STM item: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(
        self,
        item_id: Optional[str] = None,
        filter_criteria: Optional[dict[str, Any]] = None,
        limit: int = 100,
        include_expired: bool = False
    ) -> Union[Optional[dict[str, Any]], list[dict[str, Any]]]:
        """
        Retrieve memory items from storage.
        
        Args:
            item_id: Optional ID of a specific item to retrieve
            filter_criteria: Optional criteria to filter items by
            limit: Maximum number of items to return
            include_expired: Whether to include expired items
        
        Returns:
            A single item dict if item_id is provided, otherwise a list of items
        
        Raises:
            ItemNotFoundError: If the specified item_id is not found
            StorageOperationError: If the retrieval operation fails
        """
        try:
            current_time = datetime.utcnow().timestamp()
            
            # If a specific item ID is requested
            if item_id:
                async with self._lock:
                    if item_id not in self._index:
                        raise ItemNotFoundError(f"Item with ID {item_id} not found")
                    
                    item_info = self._index[item_id]
                    
                    # Check if item is expired
                    if not include_expired and item_info["expires_at"] < current_time:
                        raise ItemNotFoundError(f"Item with ID {item_id} has expired")
                    
                    # Load the item
                    item_path = Path(item_info["path"])
                    if not item_path.exists():
                        # Remove from index if file doesn't exist
                        del self._index[item_id]
                        await self._persist_index()
                        raise ItemNotFoundError(f"Item file for ID {item_id} not found")
                    
                    async with aiofiles.open(item_path, 'r') as f:
                        content = await f.read()
                        return json.loads(content)
            
            # Otherwise, retrieve multiple items based on criteria
            results = []
            async with self._lock:
                # Filter items based on criteria and expiration
                filtered_ids = []
                for id, info in self._index.items():
                    # Skip expired items unless explicitly included
                    if not include_expired and info["expires_at"] < current_time:
                        continue
                    
                    # Apply filter criteria if provided
                    if filter_criteria:
                        match = True
                        for key, value in filter_criteria.items():
                            # Handle nested metadata fields
                            if key.startswith("metadata."):
                                meta_key = key.split(".", 1)[1]
                                if meta_key not in info["metadata"] or info["metadata"][meta_key] != value:
                                    match = False
                                    break
                            # Handle top-level fields
                            elif key not in info or info[key] != value:
                                match = False
                                break
                        
                        if not match:
                            continue
                    
                    filtered_ids.append(id)
                
                # Sort by updated_at (most recent first) and apply limit
                filtered_ids.sort(
                    key=lambda id: self._index[id]["updated_at"], 
                    reverse=True
                )
                filtered_ids = filtered_ids[:limit]
                
                # Load the actual items
                for id in filtered_ids:
                    item_path = Path(self._index[id]["path"])
                    if item_path.exists():
                        async with aiofiles.open(item_path, 'r') as f:
                            content = await f.read()
                            results.append(json.loads(content))
                    else:
                        # Remove from index if file doesn't exist
                        logger.warning(f"Item file for ID {id} not found, removing from index")
                        del self._index[id]
                
                # Persist index if we had to clean up missing files
                if len(filtered_ids) != len(results):
                    await self._persist_index()
            
            logger.debug(f"Retrieved {len(results)} STM items")
            return results
            
        except ItemNotFoundError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve STM items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(
        self, 
        item_id: str, 
        updates: dict[str, Any],
        extend_ttl: bool = False
    ) -> dict[str, Any]:
        """
        Update an existing memory item.
        
        Args:
            item_id: ID of the item to update
            updates: Dictionary of fields to update
            extend_ttl: Whether to reset the TTL to the default
        
        Returns:
            Dict: The updated item
        
        Raises:
            ItemNotFoundError: If the item is not found
            StorageOperationError: If the update operation fails
        """
        try:
            # First retrieve the item
            item = await self.retrieve(item_id)
            if not item:
                raise ItemNotFoundError(f"Item with ID {item_id} not found")
            
            # Apply updates
            if "content" in updates:
                item["content"] = updates["content"]
            
            if "metadata" in updates:
                if isinstance(updates["metadata"], dict):
                    item["metadata"].update(updates["metadata"])
                else:
                    item["metadata"] = updates["metadata"]
            
            # Update timestamps
            current_time = datetime.utcnow()
            item["updated_at"] = current_time.isoformat()
            
            # Extend TTL if requested
            if extend_ttl:
                item["expires_at"] = (
                    current_time + timedelta(seconds=self.config.default_ttl)
                ).timestamp()
            
            # Validate using Pydantic
            try:
                MemoryItem(**item)
            except ValidationError as e:
                raise ValueError(f"Invalid memory item after update: {e}") from e
            
            # Save the updated item
            async with self._lock:
                item_path = self._get_item_path(item_id)
                async with aiofiles.open(item_path, 'w') as f:
                    await f.write(json.dumps(item))
                
                # Update index
                self._index[item_id].update({
                    "updated_at": item["updated_at"],
                    "expires_at": item["expires_at"],
                    "metadata": item["metadata"]
                })
                
                await self._persist_index()
            
            logger.debug(f"Updated STM item with ID: {item_id}")
            return item
            
        except ItemNotFoundError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            error_msg = f"Failed to update STM item {item_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            item_id: ID of the item to delete
        
        Returns:
            bool: True if the item was deleted, False if it didn't exist
        
        Raises:
            StorageOperationError: If the delete operation fails
        """
        try:
            async with self._lock:
                if item_id not in self._index:
                    return False
                
                # Get the file path and remove the file
                item_path = Path(self._index[item_id]["path"])
                if item_path.exists():
                    await aiofiles.os.remove(item_path)
                
                # Remove from index
                del self._index[item_id]
                await self._persist_index()
            
            logger.debug(f"Deleted STM item with ID: {item_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete STM item {item_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def clear(self) -> int:
        """
        Clear all items from storage.
        
        Returns:
            int: Number of items cleared
        
        Raises:
            StorageOperationError: If the clear operation fails
        """
        try:
            count = 0
            async with self._lock:
                # Get all item IDs
                item_ids = list(self._index.keys())
                
                # Delete each item file
                for item_id in item_ids:
                    item_path = Path(self._index[item_id]["path"])
                    if item_path.exists():
                        await aiofiles.os.remove(item_path)
                        count += 1
                
                # Clear the index
                self._index = {}
                await self._persist_index()
            
            logger.info(f"Cleared {count} items from STM storage")
            return count
            
        except Exception as e:
            error_msg = f"Failed to clear STM storage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired items from storage.
        
        Returns:
            int: Number of expired items removed
        
        Raises:
            StorageOperationError: If the cleanup operation fails
        """
        try:
            current_time = datetime.utcnow().timestamp()
            expired_ids = []
            
            async with self._lock:
                # Identify expired items
                for item_id, info in self._index.items():
                    if info["expires_at"] < current_time:
                        expired_ids.append(item_id)
                
                # Remove expired items
                for item_id in expired_ids:
                    item_path = Path(self._index[item_id]["path"])
                    if item_path.exists():
                        await aiofiles.os.remove(item_path)
                    del self._index[item_id]
                
                # Persist index if any items were removed
                if expired_ids:
                    await self._persist_index()
            
            if expired_ids:
                logger.debug(f"Removed {len(expired_ids)} expired items from STM storage")
            return len(expired_ids)
            
        except Exception as e:
            error_msg = f"Failed to cleanup expired STM items: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _persist_index(self) -> None:
        """
        Persist the current index to disk.
        
        This is an internal method used to save the in-memory index to a file.
        """
        index_path = self.config.base_path / self.config.index_file
        async with aiofiles.open(index_path, 'w') as f:
            await f.write(json.dumps(self._index))
    
    async def _remove_oldest_items(self, count: int) -> None:
        """
        Remove the oldest items from storage to make room for new ones.
        
        Args:
            count: Number of items to remove
        """
        # Sort items by creation time (oldest first)
        sorted_items = sorted(
            self._index.items(),
            key=lambda x: x[1]["created_at"]
        )
        
        # Take the oldest 'count' items
        items_to_remove = sorted_items[:count]
        
        # Remove these items
        for item_id, info in items_to_remove:
            item_path = Path(info["path"])
            if item_path.exists():
                await aiofiles.os.remove(item_path)
            del self._index[item_id]
        
        logger.debug(f"Removed {len(items_to_remove)} oldest items from STM storage")
    
    async def _run_periodic_cleanup(self) -> None:
        """
        Run periodic cleanup of expired items.
        
        This method runs in a background task and periodically removes expired items.
        """
        try:
            while True:
                await asyncio.sleep(self.config.cleanup_interval)
                try:
                    removed = await self.cleanup_expired()
                    if removed > 0:
                        logger.info(f"Periodic cleanup removed {removed} expired STM items")
                except Exception as e:
                    logger.error(f"Error during periodic STM cleanup: {str(e)}", exc_info=True)
        except asyncio.CancelledError:
            logger.debug("STM storage cleanup task cancelled")
            raise
    
    def _get_item_path(self, item_id: str) -> Path:
        """
        Get the file path for a given item ID.
        
        Args:
            item_id: The ID of the item
        
        Returns:
            Path: The file path for the item
        """
        return self.config.base_path / f"{item_id}{self.config.file_extension}"