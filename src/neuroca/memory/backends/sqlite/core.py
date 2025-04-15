"""
SQLite Backend Core

This module provides the main SQLiteBackend class that integrates all SQLite component modules
to implement the BaseStorageBackend interface for the memory system.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

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
    
    # Required abstract methods from BaseStorageBackend
    async def _initialize_backend(self) -> None:
        """Initialize the backend storage."""
        # Already implemented in initialize()
        pass

    async def _shutdown_backend(self) -> None:
        """Shutdown the backend storage."""
        # Already implemented in shutdown()
        pass

    async def _create_item(self, item_data: dict) -> str:
        """Create a new item in storage."""
        try:
            # Convert dict to MemoryItem
            memory_item = MemoryItem.model_validate(item_data)
            return await self.store(memory_item)
        except Exception as e:
            raise StorageOperationError(f"Failed to create item: {str(e)}") from e

    async def _read_item(self, item_id: str) -> Optional[dict]:
        """Read an item from storage by ID."""
        try:
            memory_item = await self.retrieve(item_id)
            if memory_item is None:
                return None
            # Convert MemoryItem to dict
            return memory_item.model_dump()
        except Exception as e:
            raise StorageOperationError(f"Failed to read item {item_id}: {str(e)}") from e

    async def _update_item(self, item_id: str, item_data: dict) -> bool:
        """Update an existing item in storage."""
        try:
            # Convert dict to MemoryItem
            memory_item = MemoryItem.model_validate(item_data)
            return await self.update(memory_item)
        except Exception as e:
            raise StorageOperationError(f"Failed to update item {item_id}: {str(e)}") from e

    async def _delete_item(self, item_id: str) -> bool:
        """Delete an item from storage by ID."""
        try:
            return await self.delete(item_id)
        except Exception as e:
            raise StorageOperationError(f"Failed to delete item {item_id}: {str(e)}") from e

    async def _query_items(self, filter_criteria: dict) -> List[dict]:
        """Query items based on filter criteria."""
        try:
            # Convert to proper search filter
            search_filter = SearchFilter.model_validate(filter_criteria)
            results = await self.search("", search_filter)
            # Ensure results.results is accessed correctly
            return [item.memory.model_dump() for item in getattr(results, 'results', [])]
        except Exception as e:
            raise StorageOperationError(f"Failed to query items: {str(e)}") from e

    async def _count_items(self, filter_criteria: Optional[dict] = None) -> int:
        """Count items matching filter criteria."""
        try:
            # Convert to proper search filter if provided
            search_filter = None
            if filter_criteria:
                search_filter = SearchFilter.model_validate(filter_criteria)
            return await self.count(search_filter)
        except Exception as e:
            raise StorageOperationError(f"Failed to count items: {str(e)}") from e

    async def _clear_all_items(self) -> int:
        """Clear all items from storage."""
        try:
            # Use connection to execute a delete all query
            def _clear_all():
                cursor = self.connection.get_connection().cursor()
                cursor.execute("DELETE FROM memories")
                return cursor.rowcount
            
            return await self.connection.execute_async(_clear_all)
        except Exception as e:
            raise StorageOperationError(f"Failed to clear all items: {str(e)}") from e

    async def _get_backend_stats(self) -> dict:
        """Get statistics about the backend storage."""
        try:
            stats = await self.get_stats()
            return stats.model_dump()
        except Exception as e:
            raise StorageOperationError(f"Failed to get backend stats: {str(e)}") from e
            
    async def exists(self, memory_id: str) -> bool:
        """Check if a memory item exists by ID."""
        try:
            # Use connection to check if item exists
            def _exists():
                cursor = self.connection.get_connection().cursor()
                cursor.execute("SELECT 1 FROM memories WHERE id = ?", (memory_id,))
                return cursor.fetchone() is not None
            
            return await self.connection.execute_async(_exists)
        except Exception as e:
            raise StorageOperationError(f"Failed to check if memory {memory_id} exists: {str(e)}") from e
            
    async def _item_exists(self, item_id: str) -> bool:
        """Check if an item exists in storage by ID."""
        return await self.exists(item_id)
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None,
        tier_name: str = "generic",
        connection_timeout: float = 30.0,
        **kwargs
    ):
        """
        Initialize the SQLite backend.
        
        Args:
            config: Optional configuration dictionary
            db_path: Path to the SQLite database file. If None, uses a default path
                in the system's temporary directory.
            tier_name: Name of the memory tier using this backend (for filename)
            connection_timeout: Connection timeout in seconds
            **kwargs: Additional configuration options
        """
        super().__init__(config)
        
        # Initialize with default configuration structure
        self.config = {
            "cache": {
                "enabled": True,
                "max_size": 1000,
                "ttl_seconds": 300
            },
            "batch": {
                "max_batch_size": 100,
                "auto_commit": True
            },
            "performance": {
                "connection_pool_size": 5,
                "connection_timeout_seconds": 10
            },
            "sqlite": {
                "connection": {
                    "database_path": db_path or ":memory:",
                    "create_if_missing": True,
                    "timeout_seconds": connection_timeout
                },
                "performance": {
                    "journal_mode": "WAL",
                    "synchronous": "NORMAL"
                },
                "schema": {
                    "auto_migrate": True,
                    "enable_fts": True
                }
            }
        }
        
        # Update configuration with provided values (deep merge)
        if config:
            self._deep_update(self.config, config)
            
        # Extract database path from config if provided
        # Ensure db_path is correctly assigned before _setup_path
        db_path_from_config = self.config.get("sqlite", {}).get("connection", {}).get("database_path")
        if db_path_from_config and db_path_from_config != ":memory:":
            db_path = db_path_from_config
        elif not db_path: # If db_path wasn't passed and not in config, use default
             db_path = ":memory:" # Default to in-memory if not specified
            
        # Set up path and create components
        self._setup_path(db_path, tier_name, **kwargs)
        self._create_components(self.config["sqlite"]["connection"]["timeout_seconds"])

    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep update for nested dictionaries.
        
        Updates target dictionary with values from source dictionary, 
        recursively handling nested dictionaries.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively update nested dictionaries
                self._deep_update(target[key], value)
            else:
                # Direct update for non-dictionary values or new keys
                target[key] = value
    
    def _setup_path(self, db_path: Optional[str], tier_name: str, **kwargs) -> None:
        """
        Set up the database path.
        
        Args:
            db_path: Path to the SQLite database file
            tier_name: Name of the memory tier
            **kwargs: Additional configuration options
        """
        import os
        
        if db_path and db_path != ":memory:":
            self.db_path = db_path
            # Ensure directory exists if a file path is given
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                 os.makedirs(db_dir, exist_ok=True)
        elif db_path == ":memory:":
             self.db_path = ":memory:"
        else:
            # Use default path in data directory if db_path is None
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
            
            # Create components with the connection manager rather than a direct connection
            self.schema = SQLiteSchema(self.connection)
            await self.connection.execute_async(self.schema.initialize_schema)
            
            # Create other components using the connection manager
            self.crud = SQLiteCRUD(self.connection)
            self.search = SQLiteSearch(self.connection)
            self.stats = SQLiteStats(self.connection, self.db_path)
            
            # Create batch component last as it depends on crud
            self.batch = SQLiteBatch(self.connection, self.crud)
            
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
