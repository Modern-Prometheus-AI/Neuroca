"""
Redis Backend for Memory Storage

This module provides a Redis-based backend implementation for the memory storage system.
It is designed for medium-term memory (MTM) where we need persistence, good performance,
and support for various data structures while maintaining reasonable memory usage.

Features:
- High-performance key-value storage with optional TTL
- Support for complex data structures (lists, sets, hashes)
- Automatic serialization/deserialization of Python objects
- Connection pooling and error handling
- Namespace isolation for different components
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, List, Optional, Set, Union, Dict

from neuroca.core.exceptions import (
    StorageBackendError, 
    StorageInitializationError,
    MemoryNotFoundError
)
from neuroca.db.connections.redis import RedisConnection, get_redis_connection
from neuroca.memory.mtm.storage import StorageBackend, MTMMemory, MemoryStatus, StorageStats

# Configure logger
logger = logging.getLogger(__name__)

class RedisStorageBackend(StorageBackend):
    """
    Redis implementation of the storage backend for memory items.
    
    This implementation uses Redis for storing medium-term memories with:
    - Fast key-value access
    - Built-in expiration/TTL support
    - Flexible data structures
    - High throughput
    """
    
    def __init__(self, namespace: str = "mtm", connection: Optional[RedisConnection] = None, **config):
        """
        Initialize the Redis storage backend.
        
        Args:
            namespace: Namespace prefix for Redis keys to avoid collisions
            connection: Optional Redis connection to use
            **config: Additional configuration for Redis connection if not provided
        """
        self.namespace = namespace
        self._connection = connection
        self._config = config
        self._initialized = False
        self._lock = asyncio.Lock()
    
    def _get_key(self, memory_id: str) -> str:
        """
        Get the full Redis key for a memory ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Prefixed Redis key
        """
        return f"{self.namespace}:memory:{memory_id}"
    
    def _get_index_key(self) -> str:
        """
        Get the Redis key for the memory index.
        
        Returns:
            Prefixed Redis key for the index
        """
        return f"{self.namespace}:index"
    
    def _get_status_key(self, status: MemoryStatus) -> str:
        """
        Get the Redis key for a status set.
        
        Args:
            status: Memory status
            
        Returns:
            Prefixed Redis key for the status set
        """
        return f"{self.namespace}:status:{status.value}"
    
    async def initialize(self) -> None:
        """
        Initialize the Redis storage backend.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Get or create Redis connection
            if self._connection is None:
                self._connection = get_redis_connection()
            
            # Test connection
            if not self._connection.ping():
                raise StorageInitializationError("Redis connection test failed")
            
            self._initialized = True
            logger.info("Initialized Redis storage backend")
        except Exception as e:
            error_msg = f"Failed to initialize Redis storage backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the backend is initialized before use."""
        if not self._initialized:
            await self.initialize()
    
    async def store(self, memory_item: MTMMemory) -> str:
        """
        Store a memory item in Redis.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            The ID of the stored memory
            
        Raises:
            StorageBackendError: If the memory cannot be stored
        """
        try:
            await self._ensure_initialized()
            memory_id = memory_item.id
            
            # Serialize the memory item
            memory_data = memory_item.dict()
            # Convert enum values to strings for JSON serialization
            memory_data["priority"] = memory_item.priority.value
            memory_data["status"] = memory_item.status.value
            
            # Store in Redis
            key = self._get_key(memory_id)
            self._connection.set(key, memory_data)
            
            # Add to index
            index_key = self._get_index_key()
            self._connection.sadd(index_key, memory_id)
            
            # Add to status set
            status_key = self._get_status_key(memory_item.status)
            self._connection.sadd(status_key, memory_id)
            
            logger.debug(f"Stored memory with ID {memory_id} in Redis")
            return memory_id
            
        except Exception as e:
            error_msg = f"Failed to store memory in Redis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> Optional[MTMMemory]:
        """
        Retrieve a memory item from Redis.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The memory item if found, None otherwise
            
        Raises:
            StorageBackendError: If there's an error retrieving the memory
        """
        try:
            await self._ensure_initialized()
            
            # Get from Redis
            key = self._get_key(memory_id)
            memory_data = self._connection.get(key)
            
            if memory_data is None:
                logger.debug(f"Memory with ID {memory_id} not found in Redis")
                return None
            
            # Convert string values back to enum values
            memory_data["priority"] = int(memory_data["priority"])
            memory_data["status"] = memory_data["status"]  # String is acceptable
            
            # Create and return memory item
            memory_item = MTMMemory(**memory_data)
            memory_item.increment_access()
            
            # Update the item in Redis with incremented access count
            await self.update(memory_id, memory_item)
            
            logger.debug(f"Retrieved memory with ID {memory_id} from Redis")
            return memory_item
            
        except Exception as e:
            error_msg = f"Failed to retrieve memory with ID {memory_id} from Redis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def update(self, memory_id: str, memory_item: MTMMemory) -> None:
        """
        Update a memory item in Redis.
        
        Args:
            memory_id: The ID of the memory to update
            memory_item: The updated memory item
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageBackendError: If there's an error updating the memory
        """
        try:
            await self._ensure_initialized()
            
            # Check if memory exists
            key = self._get_key(memory_id)
            exists = self._connection.exists(key)
            
            if not exists:
                raise MemoryNotFoundError(f"Memory with ID {memory_id} not found in Redis")
            
            # Get original memory to check for status change
            original_data = self._connection.get(key)
            if original_data:
                original_status = original_data.get("status")
            else:
                original_status = None
            
            # Serialize the memory item
            memory_data = memory_item.dict()
            # Convert enum values to strings for JSON serialization
            memory_data["priority"] = memory_item.priority.value
            memory_data["status"] = memory_item.status.value
            
            # Store in Redis
            self._connection.set(key, memory_data)
            
            # Update status sets if status changed
            if original_status and original_status != memory_data["status"]:
                # Remove from old status set
                old_status_key = f"{self.namespace}:status:{original_status}"
                self._connection.srem(old_status_key, memory_id)
                
                # Add to new status set
                new_status_key = self._get_status_key(memory_item.status)
                self._connection.sadd(new_status_key, memory_id)
            
            logger.debug(f"Updated memory with ID {memory_id} in Redis")
            
        except MemoryNotFoundError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            error_msg = f"Failed to update memory with ID {memory_id} in Redis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def delete(self, memory_id: str) -> None:
        """
        Delete a memory item from Redis.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageBackendError: If there's an error deleting the memory
        """
        try:
            await self._ensure_initialized()
            
            # Check if memory exists
            key = self._get_key(memory_id)
            exists = self._connection.exists(key)
            
            if not exists:
                raise MemoryNotFoundError(f"Memory with ID {memory_id} not found in Redis")
            
            # Get status before deletion
            memory_data = self._connection.get(key)
            status = memory_data.get("status") if memory_data else None
            
            # Delete from Redis
            self._connection.delete(key)
            
            # Remove from index
            index_key = self._get_index_key()
            self._connection.srem(index_key, memory_id)
            
            # Remove from status set
            if status:
                status_key = f"{self.namespace}:status:{status}"
                self._connection.srem(status_key, memory_id)
            
            logger.debug(f"Deleted memory with ID {memory_id} from Redis")
            
        except MemoryNotFoundError:
            # Re-raise without wrapping
            raise
        except Exception as e:
            error_msg = f"Failed to delete memory with ID {memory_id} from Redis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def list_all(self) -> List[MTMMemory]:
        """
        List all memories in Redis.
        
        Returns:
            A list of all memories
            
        Raises:
            StorageBackendError: If there's an error listing memories
        """
        try:
            await self._ensure_initialized()
            
            # Get all memory IDs from index
            index_key = self._get_index_key()
            memory_ids = self._connection.smembers(index_key)
            
            # Retrieve each memory
            memories = []
            for memory_id in memory_ids:
                memory_item = await self.retrieve(memory_id)
                if memory_item:
                    memories.append(memory_item)
            
            logger.debug(f"Listed {len(memories)} memories from Redis")
            return memories
            
        except Exception as e:
            error_msg = f"Failed to list memories from Redis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the Redis storage.
        
        Returns:
            Statistics about the storage
            
        Raises:
            StorageBackendError: If there's an error retrieving statistics
        """
        try:
            await self._ensure_initialized()
            
            # Get counts by status
            active_count = len(self._connection.smembers(self._get_status_key(MemoryStatus.ACTIVE)))
            archived_count = len(self._connection.smembers(self._get_status_key(MemoryStatus.ARCHIVED)))
            consolidated_count = len(self._connection.smembers(self._get_status_key(MemoryStatus.CONSOLIDATED)))
            forgotten_count = len(self._connection.smembers(self._get_status_key(MemoryStatus.FORGOTTEN)))
            
            # Get total count
            index_key = self._get_index_key()
            total_count = len(self._connection.smembers(index_key))
            
            # Estimate size (rough approximation)
            size_bytes = 0
            memory_ids = self._connection.smembers(index_key)
            for memory_id in memory_ids:
                key = self._get_key(memory_id)
                memory_data = self._connection.get(key)
                if memory_data:
                    size_bytes += len(json.dumps(memory_data))
            
            stats = StorageStats(
                total_memories=total_count,
                active_memories=active_count,
                archived_memories=archived_count,
                consolidated_memories=consolidated_count,
                forgotten_memories=forgotten_count,
                total_size_bytes=size_bytes,
                last_updated=datetime.now()
            )
            
            logger.debug("Retrieved storage statistics from Redis")
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get storage statistics from Redis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
