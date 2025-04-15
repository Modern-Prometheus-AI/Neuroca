"""
Redis CRUD Operations Component

This module provides the RedisCRUD class for performing CRUD operations on memory items.
"""

import logging
from typing import Any, Dict, Optional

from neuroca.memory.backends.redis.components.connection import RedisConnection
from neuroca.memory.backends.redis.components.indexing import RedisIndexing
from neuroca.memory.backends.redis.components.utils import RedisUtils
from neuroca.memory.exceptions import ItemExistsError, ItemNotFoundError, StorageOperationError
from neuroca.memory.models.memory_item import MemoryItem

logger = logging.getLogger(__name__)


class RedisCRUD:
    """
    Handles CRUD operations for memory items in Redis.
    
    This class provides methods for creating, reading, updating, and
    deleting memory items in Redis.
    """
    
    def __init__(
        self, 
        connection: RedisConnection, 
        utils: RedisUtils, 
        indexing: RedisIndexing
    ):
        """
        Initialize the Redis CRUD operations component.
        
        Args:
            connection: Redis connection component
            utils: Redis utilities
            indexing: Redis indexing component
        """
        self.connection = connection
        self.utils = utils
        self.indexing = indexing
    
    async def create(self, memory_item: MemoryItem) -> str:
        """
        Create a memory item in Redis.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            ItemExistsError: If an item with the same ID already exists
            StorageOperationError: If the create operation fails
        """
        try:
            # Ensure memory has an ID
            memory_id = memory_item.id or self.utils.generate_id()
            
            # Check if memory exists
            memory_key = self.utils.create_memory_key(memory_id)
            exists = await self.connection.execute("exists", memory_key)
            
            if exists:
                raise ItemExistsError(item_id=memory_id)
            
            # Prepare memory data
            memory_data = self.utils.prepare_memory_data(
                memory_id=memory_id,
                content=memory_item.content,
                summary=memory_item.summary
            )
            
            # Start pipeline
            async with await self.connection.pipeline() as pipe:
                # Store memory data
                await pipe.hset(memory_key, mapping=memory_data)
                
                # Store metadata if exists
                if memory_item.metadata:
                    metadata_key = self.utils.create_metadata_key(memory_id)
                    metadata_json = self.utils.serialize_metadata(memory_item.metadata)
                    await pipe.set(metadata_key, metadata_json)
                    
                    # Update statistics
                    stats_key = self.utils.create_stats_key()
                    await pipe.hincrby(stats_key, "total_memories", 1)
                    
                    # Index status if present
                    if "status" in memory_item.metadata:
                        status = memory_item.metadata["status"]
                        await pipe.hincrby(stats_key, f"{status}_memories", 1)
                
                # Execute pipeline
                await pipe.execute()
            
            # Index content and metadata
            if memory_item.content:
                await self.indexing.index_content(memory_id, memory_item.content)
                
            if memory_item.metadata:
                # Index tags
                if "tags" in memory_item.metadata and memory_item.metadata["tags"]:
                    await self.indexing.index_tags(memory_id, memory_item.metadata["tags"])
                
                # Index status
                if "status" in memory_item.metadata:
                    await self.indexing.index_status(memory_id, memory_item.metadata["status"])
            
            logger.debug(f"Created memory with ID: {memory_id}")
            return memory_id
        except ItemExistsError:
            raise  # Re-raise the specific exception
        except Exception as e:
            error_msg = f"Failed to create memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def read(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a memory item from Redis.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The memory item data if found, None otherwise
            
        Raises:
            StorageOperationError: If the read operation fails
        """
        try:
            # Get memory data
            memory_key = self.utils.create_memory_key(memory_id)
            memory_data = await self.connection.execute("hgetall", memory_key)
            
            if not memory_data:
                logger.debug(f"Memory with ID {memory_id} not found")
                return None
            
            # Get metadata
            metadata_key = self.utils.create_metadata_key(memory_id)
            metadata_json = await self.connection.execute("get", metadata_key)
            metadata = self.utils.deserialize_metadata(metadata_json)
            
            # Update access time
            await self.connection.execute(
                "hset", 
                memory_key, 
                "last_accessed", 
                self.utils.get_current_timestamp()
            )
            
            # Combine data and metadata
            result = {**memory_data, "metadata": metadata}
            
            logger.debug(f"Read memory with ID: {memory_id}")
            return result
        except Exception as e:
            error_msg = f"Failed to read memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update a memory item in Redis.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            bool: True if update was successful, False if memory not found
            
        Raises:
            ItemNotFoundError: If the item does not exist
            StorageOperationError: If the update operation fails
        """
        try:
            # Ensure memory has an ID
            memory_id = memory_item.id
            if not memory_id:
                raise ValueError("Cannot update memory without ID")
            
            # Check if memory exists
            memory_key = self.utils.create_memory_key(memory_id)
            exists = await self.connection.execute("exists", memory_key)
            
            if not exists:
                raise ItemNotFoundError(item_id=memory_id)
            
            # Get current memory data for comparison
            current_data = await self.connection.execute("hgetall", memory_key)
            
            # Get current metadata for comparison
            metadata_key = self.utils.create_metadata_key(memory_id)
            current_metadata_json = await self.connection.execute("get", metadata_key)
            current_metadata = self.utils.deserialize_metadata(current_metadata_json)
            
            # Prepare memory data for update
            memory_data = self.utils.update_memory_data(
                content=memory_item.content,
                summary=memory_item.summary
            )
            
            # Start pipeline
            async with await self.connection.pipeline() as pipe:
                # Update memory data
                await pipe.hset(memory_key, mapping=memory_data)
                
                # Update metadata if exists
                if memory_item.metadata:
                    metadata_json = self.utils.serialize_metadata(memory_item.metadata)
                    await pipe.set(metadata_key, metadata_json)
                
                # Execute pipeline
                await pipe.execute()
            
            # Update indices
            
            # Update content index if content changed
            if memory_item.content and memory_item.content != current_data.get("content"):
                await self.indexing.update_content_index(
                    memory_id, 
                    current_data.get("content"), 
                    memory_item.content
                )
            
            # Update metadata indices
            if memory_item.metadata:
                # Update tag indices
                old_tags = current_metadata.get("tags", [])
                new_tags = memory_item.metadata.get("tags", [])
                if old_tags != new_tags:
                    await self.indexing.update_tag_indices(memory_id, old_tags, new_tags)
                
                # Update status index
                old_status = current_metadata.get("status")
                new_status = memory_item.metadata.get("status")
                if old_status != new_status and new_status:
                    await self.indexing.update_status_index(memory_id, old_status, new_status)
                    
                    # Update statistics
                    stats_key = self.utils.create_stats_key()
                    async with await self.connection.pipeline() as pipe:
                        if old_status:
                            await pipe.hincrby(stats_key, f"{old_status}_memories", -1)
                        if new_status:
                            await pipe.hincrby(stats_key, f"{new_status}_memories", 1)
                        await pipe.execute()
            
            logger.debug(f"Updated memory with ID: {memory_id}")
            return True
        except ItemNotFoundError:
            raise  # Re-raise the specific exception
        except Exception as e:
            error_msg = f"Failed to update memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from Redis.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            bool: True if deletion was successful, False if memory not found
            
        Raises:
            StorageOperationError: If the delete operation fails
        """
        try:
            # Check if memory exists
            memory_key = self.utils.create_memory_key(memory_id)
            exists = await self.connection.execute("exists", memory_key)
            
            if not exists:
                logger.warning(f"Memory with ID {memory_id} not found for deletion")
                return False
            
            # Get memory data for cleanup
            memory_data = await self.connection.execute("hgetall", memory_key)
            
            # Get metadata for cleanup
            metadata_key = self.utils.create_metadata_key(memory_id)
            metadata_json = await self.connection.execute("get", metadata_key)
            metadata = self.utils.deserialize_metadata(metadata_json)
            
            # Start pipeline
            async with await self.connection.pipeline() as pipe:
                # Delete memory data
                await pipe.delete(memory_key)
                
                # Delete metadata
                await pipe.delete(metadata_key)
                
                # Update statistics
                stats_key = self.utils.create_stats_key()
                await pipe.hincrby(stats_key, "total_memories", -1)
                
                if metadata and "status" in metadata:
                    status = metadata["status"]
                    await pipe.hincrby(stats_key, f"{status}_memories", -1)
                
                # Execute pipeline
                await pipe.execute()
            
            # Remove indices
            
            # Remove content indices
            if "content" in memory_data:
                await self.indexing.remove_content_index(memory_id, memory_data["content"])
            
            # Remove metadata indices
            if metadata:
                # Remove tag indices
                if "tags" in metadata and metadata["tags"]:
                    await self.indexing.remove_tag_indices(memory_id, metadata["tags"])
                
                # Remove status index
                if "status" in metadata:
                    await self.indexing.remove_status_index(memory_id, metadata["status"])
            
            logger.debug(f"Deleted memory with ID: {memory_id}")
            return True
        except Exception as e:
            error_msg = f"Failed to delete memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def exists(self, memory_id: str) -> bool:
        """
        Check if a memory item exists in Redis.
        
        Args:
            memory_id: ID of the memory to check
            
        Returns:
            bool: True if the memory exists, False otherwise
            
        Raises:
            StorageOperationError: If the exists operation fails
        """
        try:
            memory_key = self.utils.create_memory_key(memory_id)
            exists = await self.connection.execute("exists", memory_key)
            return bool(exists)
        except Exception as e:
            error_msg = f"Failed to check if memory {memory_id} exists: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
