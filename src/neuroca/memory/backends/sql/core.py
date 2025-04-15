"""
SQL Storage Backend Core

This module provides the main SQLBackend class that integrates all SQL
component modules to implement the BaseStorageBackend interface for the memory system.
"""

import logging
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.sql.components.batch import SQLBatch
from neuroca.memory.backends.sql.components.connection import SQLConnection
from neuroca.memory.backends.sql.components.crud import SQLCRUD
from neuroca.memory.backends.sql.components.schema import SQLSchema
from neuroca.memory.backends.sql.components.search import SQLSearch
from neuroca.memory.backends.sql.components.stats import SQLStats
from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError, StorageOperationError
from neuroca.memory.interfaces import StorageStats
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import SearchFilter, SearchResults

logger = logging.getLogger(__name__)


class SQLBackend(BaseStorageBackend):
    """
    SQL implementation of the storage backend interface.
    
    This class integrates the SQL component modules to provide a complete
    implementation of the BaseStorageBackend interface using PostgreSQL
    for robust, persistent memory storage.
    
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
        schema: str = "memory",
        table_name: str = "memory_items",
        connection: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize the SQL backend.
        
        Args:
            schema: Database schema to use
            table_name: Table name for storing memory items
            connection: Optional pre-existing database connection to use
            **kwargs: Additional configuration options
        """
        super().__init__()
        
        self.schema_name = schema
        self.table_name = table_name
        self.config = kwargs
        
        # Create components
        self._create_components(connection)
    
    def _create_components(self, connection: Optional[Any] = None) -> None:
        """
        Create the component instances.
        
        Args:
            connection: Optional pre-existing database connection to use
        """
        # Create connection component
        self.connection = SQLConnection(
            connection=connection,
            **self.config
        )
        
        # Create schema component
        self.schema = SQLSchema(
            connection=self.connection,
            schema=self.schema_name,
            table_name=self.table_name
        )
        
        # Create CRUD component
        self.crud = SQLCRUD(
            connection=self.connection,
            schema=self.schema
        )
        
        # Create search component
        self.search_component = SQLSearch(
            connection=self.connection,
            schema=self.schema,
            crud=self.crud
        )
        
        # Create batch component
        self.batch = SQLBatch(
            connection=self.connection,
            schema=self.schema,
            crud=self.crud
        )
        
        # Create stats component
        self.stats = SQLStats(
            connection=self.connection,
            schema=self.schema
        )
    
    async def initialize(self) -> None:
        """
        Initialize the SQL backend.
        
        This initializes the connection and creates the necessary schema,
        tables, and indexes if they don't exist.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Initialize connection
            await self.connection.initialize()
            
            # Initialize schema
            await self.schema.initialize()
            
            logger.info(f"Initialized SQL backend with {self.schema.qualified_table_name}")
        except Exception as e:
            error_msg = f"Failed to initialize SQL backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the SQL backend, closing the connection.
        
        Raises:
            StorageBackendError: If shutdown fails
        """
        try:
            # Close connection
            await self.connection.close()
            
            logger.info("SQL backend shutdown successfully")
        except Exception as e:
            error_msg = f"Failed to shutdown SQL backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the database.
        
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
            error_msg = f"Failed to store memory in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from the database by ID.
        
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
            error_msg = f"Failed to retrieve memory {memory_id} from SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the database.
        
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
            error_msg = f"Failed to update memory {memory_item.id} in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the database.
        
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
            error_msg = f"Failed to delete memory {memory_id} from SQL: {str(e)}"
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
            # Delegate to Batch component
            return await self.batch.batch_create(memory_items)
        except Exception as e:
            error_msg = f"Failed to batch store memories in SQL: {str(e)}"
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
            # Delegate to Batch component
            results = await self.batch.batch_delete(memory_ids)
            
            # Count successful deletions
            deleted_count = sum(1 for success in results.values() if success)
            
            return deleted_count
        except Exception as e:
            error_msg = f"Failed to batch delete memories in SQL: {str(e)}"
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
        Search for memory items in the database.
        
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
            # Delegate to Search component
            return await self.search_component.search(
                query=query,
                filter=filter,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            error_msg = f"Failed to search memories in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count(self, filter: Optional[SearchFilter] = None) -> int:
        """
        Count memory items in the database matching the filter.
        
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
            error_msg = f"Failed to count memories in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the SQL storage.
        
        Returns:
            StorageStats: Storage statistics
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Delegate to Stats component
            return await self.stats.get_stats()
        except Exception as e:
            error_msg = f"Failed to get storage statistics from SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
