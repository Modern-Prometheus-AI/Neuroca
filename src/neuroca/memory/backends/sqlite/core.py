"""
SQLite Backend Core

This module provides the main SQLiteBackend class that integrates all SQLite component modules
to implement the BaseStorageBackend interface for the memory system.
"""

import asyncio
import logging
import uuid
from typing import List, Optional

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.sqlite.components.batch import SQLiteBatch
from neuroca.memory.backends.sqlite.components.connection import SQLiteConnection
from neuroca.memory.backends.sqlite.components.crud import SQLiteCRUD
from neuroca.memory.backends.sqlite.components.schema import SQLiteSchema
from neuroca.memory.backends.sqlite.components.search import SQLiteSearch
from neuroca.memory.backends.sqlite.components.stats import SQLiteStats
from neuroca.memory.exceptions import (
    ItemNotFoundError,
    StorageBackendError,
    StorageInitializationError,
    StorageOperationError,
)
from neuroca.memory.interfaces import StorageStats
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import MemorySearchOptions as SearchFilter, MemorySearchResults as SearchResults

logger = logging.getLogger(__name__)


class SQLiteBackend(BaseStorageBackend):
    """
    SQLite implementation of the storage backend interface.
    
    This class integrates the SQLite component modules to provide a complete 
    implementation of the BaseStorageBackend interface.
    
    Features:
    - Full CRUD operations for memory items
    - Text-based search with filtering
    - Transaction support for batch operations
    - Automatic schema creation and migration
    - Statistics tracking
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        tier_name: str = "generic",
        connection_timeout: float = 30.0,
        **kwargs
    ):
        """
        Initialize the SQLite backend.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses a default path
                in the system's temporary directory.
            tier_name: Name of the memory tier using this backend (for filename)
            connection_timeout: Connection timeout in seconds
            **kwargs: Additional configuration options
        """
        super().__init__()
        
        # Set up path and create components
        self._setup_path(db_path, tier_name, **kwargs)
        self._create_components(connection_timeout)
    
    def _setup_path(self, db_path: Optional[str], tier_name: str, **kwargs) -> None:
        """
        Set up the database path.
        
        Args:
            db_path: Path to the SQLite database file
            tier_name: Name of the memory tier
            **kwargs: Additional configuration options
        """
        import os
        
        if db_path:
            self.db_path = db_path
        else:
            # Use default path in data directory
            data_dir = kwargs.get('data_dir', os.path.join(os.getcwd(), 'data', 'memory'))
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, f"neuroca_memory_{tier_name}.db")
        
        # Store tier name for reference
        self.tier_name = tier_name
    
    def _create_components(self, connection_timeout: float) -> None:
        """
        Create the component instances.
        
        Args:
            connection_timeout: Connection timeout in seconds
        """
        # Create the connection component
        self.connection = SQLiteConnection(
            db_path=self.db_path,
            connection_timeout=connection_timeout
        )
        
        # Get the raw SQLite connection for other components
        # Note: This is a placeholder - the actual connection will be 
        # created in the initialize method
        self._conn = None
        
        # Create placeholder for other components
        # These will be properly initialized in the initialize method
        self.schema = None
        self.crud = None
        self.search = None
        self.batch = None
        self.stats = None
    
    async def initialize(self) -> None:
        """
        Initialize the SQLite backend, creating necessary tables if they don't exist.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Initialize the connection
            conn = self.connection.get_connection()
            
            # Create schema component and initialize database
            self.schema = SQLiteSchema(conn)
            await self.connection.execute_async(self.schema.initialize_schema)
            
            # Create other components
            self.crud = SQLiteCRUD(conn)
            self.search = SQLiteSearch(conn)
            self.stats = SQLiteStats(conn, self.db_path)
            
            # Create batch component last as it depends on crud
            self.batch = SQLiteBatch(conn, self.crud)
            
            logger.info(f"Initialized SQLite backend at {self.db_path}")
        except Exception as e:
            error_msg = f"Failed to initialize SQLite backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the SQLite backend, closing connections.
        
        Raises:
            StorageBackendError: If shutdown fails
        """
        try:
            await self.connection.close()
            logger.info("SQLite backend shutdown successfully")
        except Exception as e:
            error_msg = f"Failed to shutdown SQLite backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the SQLite database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            StorageOperationError: If the store operation fails
        """
        try:
            # Delegate to the CRUD component
            memory_id = await self.connection.execute_async(
                self.crud.store,
                memory_item
            )
            
            return memory_id
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from the SQLite database by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
            
        Raises:
            StorageOperationError: If the retrieve operation fails
        """
        try:
            # Delegate to the CRUD component
            memory_item = await self.connection.execute_async(
                self.crud.retrieve,
                memory_id
            )
            
            return memory_item
        except Exception as e:
            error_msg = f"Failed to retrieve memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the SQLite database.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            bool: True if update was successful, False if memory not found
            
        Raises:
            StorageOperationError: If the update operation fails
        """
        try:
            # Delegate to the CRUD component
            success = await self.connection.execute_async(
                self.crud.update,
                memory_item
            )
            
            return success
        except Exception as e:
            error_msg = f"Failed to update memory {memory_item.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the SQLite database.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            bool: True if deletion was successful, False if memory not found
            
        Raises:
            StorageOperationError: If the delete operation fails
        """
        try:
            # Delegate to the CRUD component
            success = await self.connection.execute_async(
                self.crud.delete,
                memory_id
            )
            
            return success
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
            # Delegate to the Batch component
            memory_ids = await self.connection.execute_async(
                self.batch.batch_store,
                memory_items
            )
            
            return memory_ids
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
            # Delegate to the Batch component
            deleted_count = await self.connection.execute_async(
                self.batch.batch_delete,
                memory_ids
            )
            
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
        Search for memory items in the SQLite database.
        
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
            # Delegate to the Search component
            results = await self.connection.execute_async(
                self.search.search,
                query, filter, limit, offset
            )
            
            return results
        except Exception as e:
            error_msg = f"Failed to search memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count(self, filter: Optional[SearchFilter] = None) -> int:
        """
        Count memory items matching the given filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        try:
            # Delegate to the Search component
            count = await self.connection.execute_async(
                self.search.count,
                filter
            )
            
            return count
        except Exception as e:
            error_msg = f"Failed to count memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the SQLite storage.
        
        Returns:
            StorageStats: Storage statistics
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Delegate to the Stats component
            stats = await self.connection.execute_async(
                self.stats.get_stats
            )
            
            return stats
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
