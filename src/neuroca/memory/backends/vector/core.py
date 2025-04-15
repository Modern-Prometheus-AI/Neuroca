"""
Vector Storage Backend Core

This module provides the main VectorBackend class that integrates all vector
component modules to implement the BaseStorageBackend interface for the memory system.
"""

import logging
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.vector.components.crud import VectorCRUD
from neuroca.memory.backends.vector.components.index import VectorIndex
from neuroca.memory.backends.vector.components.models import VectorEntry
from neuroca.memory.backends.vector.components.search import VectorSearch
from neuroca.memory.backends.vector.components.stats import VectorStats
from neuroca.memory.backends.vector.components.storage import VectorStorage
from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError, StorageOperationError
from neuroca.memory.interfaces import StorageStats
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import MemorySearchOptions, MemorySearchResults

logger = logging.getLogger(__name__)


class VectorBackend(BaseStorageBackend):
    """
    Vector database implementation of the storage backend interface.
    
    This class integrates the vector component modules to provide a complete
    implementation of the BaseStorageBackend interface for similarity-based
    memory storage and retrieval.
    
    Features:
    - Storage of memory items with vector embeddings
    - Fast semantic similarity search
    - Metadata filtering
    - Batch operations
    - Persistence to disk (optional)
    """
    
    def __init__(
        self,
        dimension: int = 768,
        similarity_threshold: float = 0.75,
        index_path: Optional[str] = None,
        **config
    ):
        """
        Initialize the vector storage backend.
        
        Args:
            dimension: Dimensionality of the vectors to store
            similarity_threshold: Minimum similarity score for search results
            index_path: Optional path to persist the index
            **config: Additional configuration options
        """
        super().__init__()
        
        self.dimension = dimension
        self.similarity_threshold = similarity_threshold
        self.index_path = index_path
        self.config = config
        
        # Create components
        self._create_components()
    
    def _create_components(self) -> None:
        """Create the component instances."""
        # Create vector index
        self.index = VectorIndex(dimension=self.dimension)
        
        # Create storage component
        self.storage = VectorStorage(
            index=self.index,
            index_path=self.index_path
        )
        
        # Create CRUD component
        self.crud = VectorCRUD(
            index=self.index,
            storage=self.storage
        )
        
        # Create search component
        self.search_component = VectorSearch(
            index=self.index,
            crud=self.crud,
            similarity_threshold=self.similarity_threshold
        )
        
        # Create stats component
        self.stats = VectorStats(
            index=self.index,
            storage=self.storage
        )
    
    async def initialize(self) -> None:
        """
        Initialize the vector storage backend.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Initialize storage (which loads the index if needed)
            await self.storage.initialize()
            
            logger.info(f"Initialized vector backend with dimension {self.dimension}")
        except Exception as e:
            error_msg = f"Failed to initialize vector backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the vector storage backend.
        
        Raises:
            StorageBackendError: If shutdown fails
        """
        try:
            # Save index to disk if path is provided
            if self.index_path:
                await self.storage.save()
            
            logger.info("Vector backend shutdown successfully")
        except Exception as e:
            error_msg = f"Failed to shutdown vector backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the vector database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            StorageOperationError: If the memory cannot be stored
        """
        try:
            # Delegate to CRUD component
            return await self.crud.create(memory_item)
        except Exception as e:
            error_msg = f"Failed to store memory in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID from the vector database.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
            
        Raises:
            StorageOperationError: If the retrieve operation fails
        """
        try:
            # Delegate to CRUD component
            return await self.crud.read(memory_id)
        except Exception as e:
            error_msg = f"Failed to retrieve memory {memory_id} from vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the vector database.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            bool: True if update was successful, False otherwise
            
        Raises:
            StorageOperationError: If the update operation fails
        """
        try:
            # Delegate to CRUD component
            return await self.crud.update(memory_item)
        except Exception as e:
            error_msg = f"Failed to update memory {memory_item.id} in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the vector database.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
            
        Raises:
            StorageOperationError: If the delete operation fails
        """
        try:
            # Delegate to CRUD component
            return await self.crud.delete(memory_id)
        except Exception as e:
            error_msg = f"Failed to delete memory {memory_id} from vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_store(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Store multiple memory items in a batch.
        
        Args:
            memory_items: List of memory items to store
            
        Returns:
            List[str]: List of stored memory IDs
            
        Raises:
            StorageOperationError: If the batch store operation fails
        """
        try:
            # Delegate to CRUD component
            return await self.crud.batch_create(memory_items)
        except Exception as e:
            error_msg = f"Failed to batch store memories in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_delete(self, memory_ids: List[str]) -> int:
        """
        Delete multiple memory items in a batch.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            int: Number of memories actually deleted
            
        Raises:
            StorageOperationError: If the batch delete operation fails
        """
        try:
            # Delegate to CRUD component
            results = await self.crud.batch_delete(memory_ids)
            
            # Count successful deletions
            deleted_count = sum(1 for success in results.values() if success)
            
            return deleted_count
        except Exception as e:
            error_msg = f"Failed to batch delete memories in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def search(
        self, 
        query: str, 
        filter: Optional[MemorySearchOptions] = None,
        limit: int = 10,
        offset: int = 0,
        query_embedding: Optional[List[float]] = None,
    ) -> MemorySearchResults:
        """
        Search for memory items in the vector database.
        
        Args:
            query: The search query
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip
            query_embedding: The embedding vector to search for (required for vector search)
            
        Returns:
            SearchResults: Search results containing memory items and metadata
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            # Query embedding is required for vector search
            if not query_embedding:
                raise StorageOperationError("Query embedding is required for vector search")
            
            # Delegate to Search component
            return await self.search_component.search(
                query=query,
                query_embedding=query_embedding,
                filter=filter,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            error_msg = f"Failed to search memories in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count(self, filter: Optional[MemorySearchOptions] = None) -> int:
        """
        Count memory items in the vector database matching the filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        try:
            # Delegate to Search component
            return await self.search_component.count(filter=filter)
        except Exception as e:
            error_msg = f"Failed to count memories in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the vector storage.
        
        Returns:
            StorageStats: Storage statistics
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Delegate to Stats component
            return await self.stats.get_stats()
        except Exception as e:
            error_msg = f"Failed to get storage statistics from vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
