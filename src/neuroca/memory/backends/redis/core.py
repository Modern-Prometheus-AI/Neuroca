"""
Redis Storage Backend Core

This module provides the main RedisBackend class that integrates all Redis
component modules to implement the BaseStorageBackend interface for the memory system.
"""

import logging
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.redis.components.batch import RedisBatch
from neuroca.memory.backends.redis.components.connection import RedisConnection
from neuroca.memory.backends.redis.components.crud import RedisCRUD
from neuroca.memory.backends.redis.components.indexing import RedisIndexing
from neuroca.memory.backends.redis.components.search import RedisSearch
from neuroca.memory.backends.redis.components.stats import RedisStats
from neuroca.memory.backends.redis.components.utils import RedisUtils
from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError, StorageOperationError
from neuroca.memory.interfaces import StorageStats
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import SearchFilter, SearchResults

logger = logging.getLogger(__name__)


class RedisBackend(BaseStorageBackend):
    """
    Redis implementation of the storage backend interface.
    
    This class integrates the Redis component modules to provide a complete
    implementation of the BaseStorageBackend interface.
    
    Features:
    - Full CRUD operations for memory items
    - Text-based search with filtering
    - Tag-based indexing and filtering
    - Status-based indexing and filtering
    - Batch operations for improved performance
    - Statistics and metrics collection
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        tier_name: str = "generic",
        db: int = 0,
        password: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Redis backend.
        
        Args:
            redis_url: Redis connection URL
            tier_name: Name of the memory tier using this backend (for key prefix)
            db: Redis database number
            password: Redis password
            **kwargs: Additional configuration options
        """
        super().__init__()
        
        self.redis_url = redis_url
        self.tier_name = tier_name
        self.db = db
        self.password = password
        self.prefix = f"memory:{tier_name}"
        self.config = kwargs
        
        # Create components
        self._create_components()
    
    def _create_components(self) -> None:
        """
        Create the component instances.
        """
        # Create connection component
        self.connection = RedisConnection(
            redis_url=self.redis_url,
            db=self.db,
            password=self.password,
            **self.config
        )
        
        # Create utilities
        self.utils = RedisUtils(prefix=self.prefix)
        
        # Create other components
        self.indexing = RedisIndexing(self.connection, self.utils)
        self.crud = RedisCRUD(self.connection, self.utils, self.indexing)
        self.search = RedisSearch(self.connection, self.utils)
        self.batch = RedisBatch(self.connection, self.utils, self.crud, self.indexing)
        self.stats = RedisStats(self.connection, self.utils)
    
    async def initialize(self) -> None:
        """
        Initialize the Redis backend.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Initialize connection
            await self.connection.initialize()
            
            logger.info(f"Initialized Redis backend at {self.redis_url}, db={self.db}")
        except Exception as e:
            error_msg = f"Failed to initialize Redis backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the Redis backend, closing the connection.
        
        Raises:
            StorageBackendError: If shutdown fails
        """
        try:
            # Close connection
            await self.connection.close()
            
            logger.info("Redis backend shutdown successfully")
        except Exception as e:
            error_msg = f"Failed to shutdown Redis backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in Redis.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            StorageOperationError: If the store operation fails
        """
        try:
            # Delegate to CRUD component
            return await self.crud.create(memory_item)
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from Redis by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
            
        Raises:
            StorageOperationError: If the retrieve operation fails
        """
        try:
            # Delegate to CRUD component
            data = await self.crud.read(memory_id)
            
            if data is None:
                return None
            
            # Convert to MemoryItem
            return MemoryItem.model_validate(data)
        except Exception as e:
            error_msg = f"Failed to retrieve memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in Redis.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            bool: True if update was successful, False if memory not found
            
        Raises:
            StorageOperationError: If the update operation fails
        """
        try:
            # Delegate to CRUD component
            return await self.crud.update(memory_item)
        except Exception as e:
            error_msg = f"Failed to update memory {memory_item.id}: {str(e)}"
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
            # Delegate to CRUD component
            return await self.crud.delete(memory_id)
        except Exception as e:
            error_msg = f"Failed to delete memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_store(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Store multiple memory items in a single transaction.
        
        Args:
            memory_items: List of memory items to store
            
        Returns:
            List[str]: List of stored memory IDs
            
        Raises:
            StorageOperationError: If the batch store operation fails
        """
        try:
            # Delegate to Batch component
            return await self.batch.batch_create(memory_items)
        except Exception as e:
            error_msg = f"Failed to batch store memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_delete(self, memory_ids: List[str]) -> int:
        """
        Delete multiple memory items in a single transaction.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            int: Number of memories actually deleted
            
        Raises:
            StorageOperationError: If the batch delete operation fails
        """
        try:
            # Delegate to Batch component
            results = await self.batch.batch_delete(memory_ids)
            
            # Count successful deletions
            deleted_count = sum(1 for success in results.values() if success)
            
            return deleted_count
        except Exception as e:
            error_msg = f"Failed to batch delete memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def search(
        self,
        query: str,
        filter: Optional[SearchFilter] = None,
        limit: int = 10,
        offset: int = 0
    ) -> SearchResults:
        """
        Search for memory items in Redis matching the query and filter.
        
        Args:
            query: Search query string
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            SearchResults: Search results containing memory items and metadata
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            # Delegate to Search component for filtering
            search_result = await self.search.search_and_filter(
                query=query,
                filter=filter,
                limit=limit,
                offset=offset
            )
            
            # Get memory items for the result IDs
            memory_ids = search_result["ids"]
            total_count = search_result["total_count"]
            
            # Use batch read to retrieve the memory items
            memory_data = await self.batch.batch_read(memory_ids)
            
            # Convert to MemoryItem objects
            memory_items = []
            for memory_id in memory_ids:
                if memory_data.get(memory_id):
                    memory_item = MemoryItem.model_validate(memory_data[memory_id])
                    memory_items.append(memory_item)
            
            # Create SearchResults
            results = SearchResults(
                query=query,
                items=memory_items,
                total_results=total_count,
                page=offset // limit + 1 if limit > 0 else 1,
                page_size=limit,
                total_pages=(total_count + limit - 1) // limit if limit > 0 else 1
            )
            
            logger.debug(f"Search for '{query}' returned {len(memory_items)} results")
            return results
        except Exception as e:
            error_msg = f"Failed to search memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count(self, filter: Optional[SearchFilter] = None) -> int:
        """
        Count memory items in Redis matching the filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        try:
            # Delegate to Search component
            return await self.search.count_items(filter=filter)
        except Exception as e:
            error_msg = f"Failed to count memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the Redis storage.
        
        Returns:
            StorageStats: Storage statistics
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Delegate to Stats component
            return await self.stats.get_stats()
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
