"""
Redis Stats Component

This module provides the RedisStats class for collecting statistics about Redis storage.
"""

import logging
from typing import Dict, Any

from neuroca.memory.backends.redis.components.connection import RedisConnection
from neuroca.memory.backends.redis.components.utils import RedisUtils
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.interfaces import StorageStats

logger = logging.getLogger(__name__)


class RedisStats:
    """
    Collects and reports statistics about Redis storage.
    
    This class provides methods for retrieving various metrics about the
    Redis storage, such as item count, memory usage, and status distributions.
    """
    
    def __init__(self, connection: RedisConnection, utils: RedisUtils):
        """
        Initialize the Redis stats component.
        
        Args:
            connection: Redis connection component
            utils: Redis utilities
        """
        self.connection = connection
        self.utils = utils
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the Redis storage.
        
        Returns:
            StorageStats: Statistics about the Redis storage
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Get basic stats from the stats hash
            stats_key = self.utils.create_stats_key()
            stats_data = await self.connection.execute("hgetall", stats_key)
            
            # Get Redis server stats
            redis_info = await self.connection.execute("info", "memory")
            
            # Parse basic stats
            total_memories = int(stats_data.get("total_memories", 0))
            active_memories = int(stats_data.get("active_memories", 0))
            archived_memories = int(stats_data.get("archived_memories", 0))
            
            # Estimate storage size by scanning keys (approximate)
            total_size_bytes = await self._estimate_storage_size()
            
            # Get additional info from Redis
            used_memory = 0
            for line in redis_info.splitlines():
                if line.startswith("used_memory:"):
                    used_memory = int(line.split(":")[1].strip())
                    break
            
            # Create additional info
            additional_info = {
                "redis_used_memory": used_memory,
                "redis_url": self.connection.redis_url,
                "redis_db": self.connection.db
            }
            
            # Create StorageStats object
            stats = StorageStats(
                backend_type="RedisBackend",
                item_count=total_memories,
                storage_size_bytes=total_size_bytes,
                metadata_size_bytes=await self._estimate_metadata_size(),
                average_item_age_seconds=await self._calculate_average_age(),
                oldest_item_age_seconds=await self._get_oldest_item_age(),
                newest_item_age_seconds=await self._get_newest_item_age(),
                max_capacity=-1,  # Redis has no fixed capacity
                capacity_used_percent=0.0,
                additional_info=additional_info
            )
            
            logger.debug(f"Retrieved storage stats: {total_memories} memories")
            return stats
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _estimate_storage_size(self) -> int:
        """
        Estimate the amount of storage used by memory items.
        
        Returns:
            int: Estimated size in bytes
        """
        try:
            # Get all keys with the prefix
            prefix_pattern = f"{self.utils.prefix}:*"
            
            # Use scan to efficiently iterate through keys
            total_size = 0
            cursor = "0"
            
            while True:
                cursor, keys = await self.connection.execute(
                    "scan", 
                    cursor, 
                    match=prefix_pattern, 
                    count=100
                )
                
                # For each key, estimate its size
                for key in keys:
                    # Get key type
                    key_type = await self.connection.execute("type", key)
                    
                    # Estimate size based on type
                    if key_type == "string":
                        size = await self.connection.execute("strlen", key)
                        total_size += int(size)
                    elif key_type == "hash":
                        # Get all fields
                        fields = await self.connection.execute("hkeys", key)
                        for field in fields:
                            value = await self.connection.execute("hget", key, field)
                            total_size += len(field) + len(value) if value else 0
                    elif key_type == "set":
                        members = await self.connection.execute("smembers", key)
                        total_size += sum(len(member) for member in members)
                
                # Stop when scan is complete
                if cursor == "0":
                    break
            
            return total_size
        except Exception as e:
            logger.warning(f"Failed to estimate storage size: {str(e)}")
            return 0
    
    async def _estimate_metadata_size(self) -> int:
        """
        Estimate the amount of storage used by metadata.
        
        Returns:
            int: Estimated size in bytes
        """
        try:
            # Get all metadata keys
            metadata_pattern = f"{self.utils.prefix}:metadata:*"
            
            # Use scan to efficiently iterate through keys
            total_size = 0
            cursor = "0"
            
            while True:
                cursor, keys = await self.connection.execute(
                    "scan", 
                    cursor, 
                    match=metadata_pattern, 
                    count=100
                )
                
                # For each key, get its size
                for key in keys:
                    value = await self.connection.execute("get", key)
                    total_size += len(value) if value else 0
                
                # Stop when scan is complete
                if cursor == "0":
                    break
            
            return total_size
        except Exception as e:
            logger.warning(f"Failed to estimate metadata size: {str(e)}")
            return 0
    
    async def _calculate_average_age(self) -> float:
        """
        Calculate the average age of items in storage.
        
        Returns:
            float: Average age in seconds
        """
        try:
            # Get all memory keys
            memory_pattern = f"{self.utils.prefix}:*"
            memory_prefix = f"{self.utils.prefix}:"
            
            # Use scan to efficiently iterate through keys
            memory_keys = []
            cursor = "0"
            
            while True:
                cursor, keys = await self.connection.execute(
                    "scan", 
                    cursor, 
                    match=memory_pattern, 
                    count=100
                )
                
                # Filter keys to only include memory items
                for key in keys:
                    if ":" not in key[len(memory_prefix):] and key.startswith(memory_prefix):
                        memory_keys.append(key)
                
                # Stop when scan is complete
                if cursor == "0":
                    break
            
            if not memory_keys:
                return 0.0
            
            # Get created_at field from each memory item
            total_age = 0.0
            count = 0
            
            for key in memory_keys:
                created_at = await self.connection.execute("hget", key, "created_at")
                if created_at:
                    # Convert to timestamp and calculate age
                    created_timestamp = self.utils.timestamp_to_seconds(created_at)
                    current_timestamp = self.utils.get_current_timestamp_seconds()
                    age = current_timestamp - created_timestamp
                    total_age += age
                    count += 1
            
            return total_age / count if count > 0 else 0.0
        except Exception as e:
            logger.warning(f"Failed to calculate average age: {str(e)}")
            return 0.0
    
    async def _get_oldest_item_age(self) -> float:
        """
        Get the age of the oldest item in storage.
        
        Returns:
            float: Age in seconds
        """
        try:
            # Get all memory keys
            memory_pattern = f"{self.utils.prefix}:*"
            memory_prefix = f"{self.utils.prefix}:"
            
            # Use scan to efficiently iterate through keys
            memory_keys = []
            cursor = "0"
            
            while True:
                cursor, keys = await self.connection.execute(
                    "scan", 
                    cursor, 
                    match=memory_pattern, 
                    count=100
                )
                
                # Filter keys to only include memory items
                for key in keys:
                    if ":" not in key[len(memory_prefix):] and key.startswith(memory_prefix):
                        memory_keys.append(key)
                
                # Stop when scan is complete
                if cursor == "0":
                    break
            
            if not memory_keys:
                return 0.0
            
            # Get oldest created_at timestamp
            oldest_timestamp = None
            current_timestamp = self.utils.get_current_timestamp_seconds()
            
            for key in memory_keys:
                created_at = await self.connection.execute("hget", key, "created_at")
                if created_at:
                    timestamp = self.utils.timestamp_to_seconds(created_at)
                    if oldest_timestamp is None or timestamp < oldest_timestamp:
                        oldest_timestamp = timestamp
            
            if oldest_timestamp is None:
                return 0.0
                
            return current_timestamp - oldest_timestamp
        except Exception as e:
            logger.warning(f"Failed to get oldest item age: {str(e)}")
            return 0.0
    
    async def _get_newest_item_age(self) -> float:
        """
        Get the age of the newest item in storage.
        
        Returns:
            float: Age in seconds
        """
        try:
            # Get all memory keys
            memory_pattern = f"{self.utils.prefix}:*"
            memory_prefix = f"{self.utils.prefix}:"
            
            # Use scan to efficiently iterate through keys
            memory_keys = []
            cursor = "0"
            
            while True:
                cursor, keys = await self.connection.execute(
                    "scan", 
                    cursor, 
                    match=memory_pattern, 
                    count=100
                )
                
                # Filter keys to only include memory items
                for key in keys:
                    if ":" not in key[len(memory_prefix):] and key.startswith(memory_prefix):
                        memory_keys.append(key)
                
                # Stop when scan is complete
                if cursor == "0":
                    break
            
            if not memory_keys:
                return 0.0
            
            # Get newest created_at timestamp
            newest_timestamp = None
            current_timestamp = self.utils.get_current_timestamp_seconds()
            
            for key in memory_keys:
                created_at = await self.connection.execute("hget", key, "created_at")
                if created_at:
                    timestamp = self.utils.timestamp_to_seconds(created_at)
                    if newest_timestamp is None or timestamp > newest_timestamp:
                        newest_timestamp = timestamp
            
            if newest_timestamp is None:
                return 0.0
                
            return current_timestamp - newest_timestamp
        except Exception as e:
            logger.warning(f"Failed to get newest item age: {str(e)}")
            return 0.0
