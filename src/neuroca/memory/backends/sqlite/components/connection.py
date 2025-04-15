"""
SQLite Connection Management Component

This module provides a class for managing SQLite database connections.
"""

import asyncio
import logging
import os
import sqlite3
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SQLiteConnection:
    """
    Manages SQLite database connections with async support and locking.
    
    This class provides a connection pool for SQLite database operations
    with support for asynchronous execution and thread safety.
    """
    
    def __init__(
        self,
        db_path: str,
        connection_timeout: float = 30.0
    ):
        """
        Initialize the SQLite connection manager.
        
        Args:
            db_path: Path to the SQLite database file
            connection_timeout: Connection timeout in seconds
        """
        self.db_path = db_path
        self.connection_timeout = connection_timeout
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
    
    def _ensure_connection(self) -> None:
        """
        Ensure a database connection exists.
        
        Creates a new connection if one doesn't exist.
        """
        if self._conn is None:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Create connection with desired settings
            self._conn = sqlite3.connect(
                self.db_path,
                timeout=self.connection_timeout,
                isolation_level=None,  # autocommit mode
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._conn.row_factory = sqlite3.Row
            
            logger.debug(f"Created new SQLite connection to {self.db_path}")
    
    async def execute_async(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a database operation asynchronously.
        
        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            T: Result of the function
        """
        async with self._lock:
            # Run the database operation in an executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._execute_with_connection(func, *args, **kwargs)
            )
    
    def _execute_with_connection(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with a guaranteed connection.
        
        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            T: Result of the function
        """
        self._ensure_connection()
        return func(*args, **kwargs)
    
    async def close(self) -> None:
        """
        Close the SQLite connection.
        """
        async with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
                logger.debug(f"Closed SQLite connection to {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get the current SQLite connection.
        
        Returns:
            sqlite3.Connection: The current SQLite connection
            
        Raises:
            ValueError: If no connection exists
        """
        self._ensure_connection()
        if self._conn is None:
            raise ValueError("Failed to create SQLite connection")
        return self._conn
