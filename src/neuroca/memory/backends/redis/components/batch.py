"""
Redis Batch Operations Component

This module provides the RedisBatch class for handling batch operations on memory items.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from neuroca.memory.backends.redis.components.connection import RedisConnection
from neuroca.memory.backends.redis.components.crud import RedisCRUD
from neuroca.memory.backends.redis.components.indexing import RedisIndexing
from neuroca.memory.backends.redis.components.utils import RedisUtils
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.models.memory_item import MemoryItem

logger = logging.getLogger(__name__)


class RedisBatch:
    """
    Handles batch operations for memory items in Redis.
    
    This class provides methods for performing operations on multiple memory
    items at once with optimized performance.
    """
    
    def __init__(
        self, 
        connection: RedisConnection, 
        utils: RedisUtils, 
        crud: RedisCRUD, 
        indexing: RedisIndexing
    ):
        """
        Initialize the Redis batch operations component.
        
        Args:
            connection: Redis connection component
            utils: Redis utilities
            crud: Redis CRUD operations component
            indexing: Redis indexing component
        """
        self.connection = connection
        self.utils = utils
        self.crud = crud
        self.indexing = indexing
    
    async def batch_create(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Create multiple memory items in Redis.
        
        Args:
            memory_items: List of memory items to create
            
        Returns:
            List[str]: List of created memory IDs
            
        Raises:
            StorageOperationError: If the batch create operation fails
        """
        try:
            if not memory_items:
                return []
            
            created_ids = []
            
            # Process in smaller batches for better error handling
            # and to avoid excessive pipeline size
            batch_size = min(len(memory_items), 50)
            
            for i in range(0, len(memory_items), batch_size):
                batch = memory_items[i:i + batch_size]
                batch_ids = await self._create_batch(batch)
                created_ids.extend(batch_ids)
            
            logger.debug(f"Batch created {len(created_ids)} memories")
            return created_ids
        except Exception as e:
            error_msg = f"Failed to batch create memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _create_batch(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Create a batch of memory items.
        
        Args:
            memory_items: List of memory items to create
            
        Returns:
            List[str]: List of created memory IDs
        """
        created_ids = []
        
        # First, check if any items already exist to avoid partial writes
        for memory_item in memory_items:
            memory_id = memory_item.id or self.utils.generate_id()
            exists = await self.crud.exists(memory_id)
            
            if exists:
                logger.warning(f"Memory with ID {memory_id} already exists, skipping in batch create")
                continue
                
            created_ids.append(memory_id)
            
        # If no items can be created, return early
        if not created_ids:
            return []
        
        # Use a pipeline for batch operations
        async with await self.connection.pipeline() as pipe:
            # For each memory item
            for memory_item in memory_items:
                memory_id = memory_item.id or self.utils.generate_id()
                
                # Skip if we found it exists
                if memory_id not in created_ids:
                    continue
                
                # Prepare memory data
                memory_key = self.utils.create_memory_key(memory_id)
                memory_data = self.utils.prepare_memory_data(
                    memory_id=memory_id,
                    content=memory_item.content,
                    summary=memory_item.summary
                )
                
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
        
        # Now handle indexing (could be optimized further)
        for memory_item in memory_items:
            memory_id = memory_item.id or self.utils.generate_id()
            
            # Skip if we found it exists
            if memory_id not in created_ids:
                continue
                
            # Index content
            if memory_item.content:
                await self.indexing.index_content(memory_id, memory_item.content)
            
            # Index metadata
            if memory_item.metadata:
                # Index tags
                if "tags" in memory_item.metadata and memory_item.metadata["tags"]:
                    await self.indexing.index_tags(memory_id, memory_item.metadata["tags"])
                
                # Index status
                if "status" in memory_item.metadata:
                    await self.indexing.index_status(memory_id, memory_item.metadata["status"])
        
        return created_ids
    
    async def batch_read(self, memory_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Read multiple memory items from Redis.
        
        Args:
            memory_ids: List of memory IDs to read
            
        Returns:
            Dict[str, Optional[Dict[str, Any]]]: Dictionary mapping memory IDs to their data
            
        Raises:
            StorageOperationError: If the batch read operation fails
        """
        try:
            if not memory_ids:
                return {}
            
            results = {}
            
            # Process in smaller batches
            batch_size = min(len(memory_ids), 50)
            
            for i in range(0, len(memory_ids), batch_size):
                batch_ids = memory_ids[i:i + batch_size]
                batch_results = await self._read_batch(batch_ids)
                results.update(batch_results)
            
            logger.debug(f"Batch read {len(results)} memories")
            return results
        except Exception as e:
            error_msg = f"Failed to batch read memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _read_batch(self, memory_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Read a batch of memory items.
        
        Args:
            memory_ids: List of memory IDs to read
            
        Returns:
            Dict[str, Optional[Dict[str, Any]]]: Dictionary mapping memory IDs to their data
        """
        results = {}
        
        # Use a pipeline for memory data
        memory_data_pipe = await self.connection.pipeline()
        metadata_pipe = await self.connection.pipeline()
        
        # Queue memory and metadata retrieval
        for memory_id in memory_ids:
            memory_key = self.utils.create_memory_key(memory_id)
            metadata_key = self.utils.create_metadata_key(memory_id)
            
            await memory_data_pipe.hgetall(memory_key)
            await metadata_pipe.get(metadata_key)
        
        # Execute pipelines
        memory_data_results = await memory_data_pipe.execute()
        metadata_results = await metadata_pipe.execute()
        await memory_data_pipe.close()
        await metadata_pipe.close()
        
        # Process results
        for i, memory_id in enumerate(memory_ids):
            memory_data = memory_data_results[i]
            metadata_json = metadata_results[i]
            
            if not memory_data:
                results[memory_id] = None
                continue
            
            # Deserialize metadata
            metadata = self.utils.deserialize_metadata(metadata_json)
            
            # Combine data and metadata
            results[memory_id] = {**memory_data, "metadata": metadata}
            
            # Update access time (non-blocking)
            memory_key = self.utils.create_memory_key(memory_id)
            asyncio.create_task(
                self.connection.execute(
                    "hset", 
                    memory_key, 
                    "last_accessed", 
                    self.utils.get_current_timestamp()
                )
            )
        
        return results
    
    async def batch_delete(self, memory_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple memory items from Redis.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            Dict[str, bool]: Dictionary mapping memory IDs to deletion success
            
        Raises:
            StorageOperationError: If the batch delete operation fails
        """
        try:
            if not memory_ids:
                return {}
            
            results = {}
            
            # Process in smaller batches
            batch_size = min(len(memory_ids), 50)
            
            for i in range(0, len(memory_ids), batch_size):
                batch_ids = memory_ids[i:i + batch_size]
                batch_results = await self._delete_batch(batch_ids)
                results.update(batch_results)
            
            logger.debug(f"Batch deleted {sum(1 for success in results.values() if success)} memories")
            return results
        except Exception as e:
            error_msg = f"Failed to batch delete memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _delete_batch(self, memory_ids: List[str]) -> Dict[str, bool]:
        """
        Delete a batch of memory items.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            Dict[str, bool]: Dictionary mapping memory IDs to deletion success
        """
        results = {}
        memory_data = {}
        metadata = {}
        
        # First, get all data needed for cleanup
        for memory_id in memory_ids:
            # Check if memory exists and get data for cleanup
            memory_key = self.utils.create_memory_key(memory_id)
            exists = await self.connection.execute("exists", memory_key)
            
            if not exists:
                results[memory_id] = False
                continue
                
            # Get memory data and metadata for cleanup
            mem_data = await self.connection.execute("hgetall", memory_key)
            metadata_key = self.utils.create_metadata_key(memory_id)
            meta_json = await self.connection.execute("get", metadata_key)
            meta = self.utils.deserialize_metadata(meta_json)
            
            memory_data[memory_id] = mem_data
            metadata[memory_id] = meta
            results[memory_id] = True
        
        # Now delete everything in one pipeline
        async with await self.connection.pipeline() as pipe:
            for memory_id in memory_ids:
                if not results[memory_id]:
                    continue
                    
                # Delete memory data
                memory_key = self.utils.create_memory_key(memory_id)
                await pipe.delete(memory_key)
                
                # Delete metadata
                metadata_key = self.utils.create_metadata_key(memory_id)
                await pipe.delete(metadata_key)
                
                # Update statistics
                stats_key = self.utils.create_stats_key()
                await pipe.hincrby(stats_key, "total_memories", -1)
                
                if "status" in metadata[memory_id]:
                    status = metadata[memory_id]["status"]
                    await pipe.hincrby(stats_key, f"{status}_memories", -1)
            
            # Execute pipeline
            await pipe.execute()
        
        # Now handle index cleanup
        for memory_id in memory_ids:
            if not results[memory_id]:
                continue
                
            # Remove content indices
            if "content" in memory_data[memory_id]:
                await self.indexing.remove_content_index(memory_id, memory_data[memory_id]["content"])
            
            # Remove metadata indices
            if metadata[memory_id]:
                # Remove tag indices
                if "tags" in metadata[memory_id] and metadata[memory_id]["tags"]:
                    await self.indexing.remove_tag_indices(memory_id, metadata[memory_id]["tags"])
                
                # Remove status index
                if "status" in metadata[memory_id]:
                    await self.indexing.remove_status_index(memory_id, metadata[memory_id]["status"])
                    
        return results
