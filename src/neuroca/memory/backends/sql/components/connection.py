"""
SQL Connection Component

This module provides the SQLConnection class for managing PostgreSQL database connections.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from neuroca.config.settings import get_settings
from neuroca.db.connections.postgres import (
    AsyncPostgresConnection,
    PostgresConfig,
    get_postgres_connection,
)
from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError

logger = logging.getLogger(__name__)


class SQLConnection:
    """
    Manages connections to a PostgreSQL database for the SQL backend.
    
    This class handles creating, maintaining, and closing the database connection.
    It also provides methods for executing SQL queries safely.
    """
    
    def __init__(
        self,
        connection: Optional[AsyncPostgresConnection] = None,
        **config: Any,
    ):
        """
        Initialize the SQL connection component.
        
        Args:
            connection: Optional pre-existing database connection to use
            **config: Configuration options for the database connection
        """
        self._connection = connection
        self._config = config
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """
        Initialize the database connection.
        
        This creates a connection to the PostgreSQL server if one hasn't
        been provided during initialization.
        
        Raises:
            StorageInitializationError: If connection creation fails
        """
        try:
            # Only initialize if not already initialized
            if self._initialized:
                return
                
            async with self._lock:
                # Check again in case another task initialized while waiting for lock
                if self._initialized:
                    return
                
                # Create connection if not provided
                if self._connection is None:
                    pg_config = PostgresConfig.from_env()
                    # Override with any provided config
                    for key, value in self._config.items():
                        setattr(pg_config, key, value)
                    # Use async mode for better performance
                    pg_config.connection_mode = "async"
                    self._connection = get_postgres_connection(pg_config, async_mode=True)
                
                # Test connection by executing a simple query
                await self.execute_query("SELECT 1")
                
                self._initialized = True
                logger.info("SQL connection initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize SQL connection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def close(self) -> None:
        """
        Close the database connection.
        
        Raises:
            StorageBackendError: If closing the connection fails
        """
        try:
            if self._connection:
                # Close the connection
                await self._connection.close()
                self._connection = None
                self._initialized = False
                logger.info("SQL connection closed")
        except Exception as e:
            error_msg = f"Failed to close SQL connection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[List[Any]] = None, 
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query with parameters.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_all: Whether to fetch all results or just the first row
            
        Returns:
            Query results as a list of dictionaries
            
        Raises:
            StorageBackendError: If query execution fails
        """
        try:
            await self.initialize()
            
            # Execute the query
            async with self._connection as conn:
                result = await conn.execute_query(query, params, fetch_all=fetch_all)
                return result
        except Exception as e:
            error_msg = f"Failed to execute SQL query: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def execute_batch(
        self,
        queries: List[str],
        params_list: Optional[List[List[Any]]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple SQL queries in a batch.
        
        Args:
            queries: List of SQL queries to execute
            params_list: List of parameter lists, one for each query
            
        Returns:
            List of query results
            
        Raises:
            StorageBackendError: If batch execution fails
        """
        try:
            await self.initialize()
            
            # Ensure params_list is provided and has the same length as queries
            if params_list is None:
                params_list = [None] * len(queries)
            elif len(params_list) != len(queries):
                raise ValueError("params_list must have the same length as queries")
            
            # Execute each query and collect results
            results = []
            async with self._connection as conn:
                for i, query in enumerate(queries):
                    result = await conn.execute_query(query, params_list[i])
                    results.append(result)
                
                return results
        except Exception as e:
            error_msg = f"Failed to execute SQL batch: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def execute_transaction(
        self,
        queries: List[str],
        params_list: Optional[List[List[Any]]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple SQL queries in a transaction.
        
        This method ensures that either all queries succeed or none of them
        take effect (ACID compliance).
        
        Args:
            queries: List of SQL queries to execute
            params_list: List of parameter lists, one for each query
            
        Returns:
            List of query results
            
        Raises:
            StorageBackendError: If transaction execution fails
        """
        try:
            await self.initialize()
            
            # Ensure params_list is provided and has the same length as queries
            if params_list is None:
                params_list = [None] * len(queries)
            elif len(params_list) != len(queries):
                raise ValueError("params_list must have the same length as queries")
            
            # Execute transaction
            results = []
            async with self._connection.transaction():
                for i, query in enumerate(queries):
                    result = await self._connection.execute_query(query, params_list[i])
                    results.append(result)
                
                return results
        except Exception as e:
            error_msg = f"Failed to execute SQL transaction: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    def is_initialized(self) -> bool:
        """
        Check if the connection is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
    
    @property
    def connection(self) -> AsyncPostgresConnection:
        """
        Get the underlying database connection.
        
        Returns:
            The database connection
            
        Raises:
            StorageBackendError: If the connection is not initialized
        """
        if not self._connection:
            raise StorageBackendError("SQL connection not initialized")
        return self._connection
