"""
PostgreSQL Database Connection Module for NeuroCognitive Architecture.

This module provides a robust, secure, and efficient connection interface to PostgreSQL
databases for the NeuroCognitive Architecture (NCA) system. It implements connection
pooling, comprehensive error handling, secure credential management, and detailed logging.

Features:
- Connection pooling for efficient resource utilization
- Automatic reconnection with exponential backoff
- Parameterized queries to prevent SQL injection
- Comprehensive error handling and logging
- Support for both synchronous and asynchronous operations
- Connection health monitoring
- Secure credential management

Usage:
    # Synchronous usage
    with PostgresConnection(config) as conn:
        results = conn.execute_query("SELECT * FROM memory_items WHERE id = %s", [item_id])
    
    # Asynchronous usage
    async with AsyncPostgresConnection(config) as conn:
        results = await conn.execute_query("SELECT * FROM memory_items WHERE id = %s", [item_id])
"""

import json
import logging
import ssl
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union
from urllib.parse import quote_plus

import asyncpg

# Third-party imports
import psycopg2
import psycopg2.extensions
import psycopg2.extras
import psycopg2.pool
from psycopg2.errors import InterfaceError, OperationalError

# Project imports
from neuroca.config.settings import get_settings
from neuroca.core.exceptions import ConnectionError, DatabaseError, QueryError

# Configure module logger
logger = logging.getLogger(__name__)


class PostgresConnectionMode(str, Enum):
    """Enum defining PostgreSQL connection modes."""
    SYNCHRONOUS = "sync"
    ASYNCHRONOUS = "async"


@dataclass
class PostgresConfig:
    """Configuration for PostgreSQL connections.
    
    This dataclass encapsulates all configuration parameters needed for establishing
    and maintaining PostgreSQL connections, with sensible defaults.
    """
    host: str
    port: int = 5432
    database: str = "neuroca"
    user: str = "postgres"
    password: str = ""
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: int = 30
    idle_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 2
    ssl_mode: str = "prefer"
    application_name: str = "neuroca"
    schema: str = "public"
    statement_timeout: int = 30000  # ms
    use_connection_pool: bool = True
    connection_mode: PostgresConnectionMode = PostgresConnectionMode.SYNCHRONOUS
    
    @classmethod
    def from_env(cls) -> 'PostgresConfig':
        """Create a PostgresConfig instance from environment variables."""
        settings = get_settings()
        
        return cls(
            host=settings.get("POSTGRES_HOST", "localhost"),
            port=int(settings.get("POSTGRES_PORT", 5432)),
            database=settings.get("POSTGRES_DB", "neuroca"),
            user=settings.get("POSTGRES_USER", "postgres"),
            password=settings.get("POSTGRES_PASSWORD", ""),
            min_connections=int(settings.get("POSTGRES_MIN_CONNECTIONS", 1)),
            max_connections=int(settings.get("POSTGRES_MAX_CONNECTIONS", 10)),
            connection_timeout=int(settings.get("POSTGRES_CONNECTION_TIMEOUT", 30)),
            idle_timeout=int(settings.get("POSTGRES_IDLE_TIMEOUT", 300)),
            retry_attempts=int(settings.get("POSTGRES_RETRY_ATTEMPTS", 3)),
            retry_delay=int(settings.get("POSTGRES_RETRY_DELAY", 2)),
            ssl_mode=settings.get("POSTGRES_SSL_MODE", "prefer"),
            application_name=settings.get("POSTGRES_APP_NAME", "neuroca"),
            schema=settings.get("POSTGRES_SCHEMA", "public"),
            statement_timeout=int(settings.get("POSTGRES_STATEMENT_TIMEOUT", 30000)),
            use_connection_pool=settings.get("POSTGRES_USE_CONNECTION_POOL", "true").lower() == "true",
            connection_mode=PostgresConnectionMode(settings.get("POSTGRES_CONNECTION_MODE", "sync")),
        )
    
    def get_connection_string(self) -> str:
        """Generate a connection string from the configuration."""
        # Securely encode password to handle special characters
        encoded_password = quote_plus(self.password)
        
        return (
            f"postgresql://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"
            f"?application_name={self.application_name}"
            f"&statement_timeout={self.statement_timeout}"
        )
    
    def get_dsn(self) -> dict[str, Any]:
        """Generate a DSN dictionary for psycopg2."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
            "application_name": self.application_name,
            "options": f"-c search_path={self.schema} -c statement_timeout={self.statement_timeout}",
        }


class PostgresConnection:
    """
    A robust PostgreSQL connection manager with connection pooling, retry logic,
    and comprehensive error handling.
    
    This class provides a high-level interface for interacting with PostgreSQL
    databases in a synchronous manner, with built-in connection pooling and
    automatic retry logic for transient failures.
    """
    
    def __init__(self, config: Optional[PostgresConfig] = None):
        """
        Initialize the PostgreSQL connection manager.
        
        Args:
            config: PostgreSQL connection configuration. If None, loads from environment.
        """
        self.config = config or PostgresConfig.from_env()
        self._pool = None
        self._conn = None
        self._cursor = None
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize the connection pool if enabled in configuration."""
        if not self.config.use_connection_pool:
            logger.debug("Connection pooling disabled, will create individual connections")
            return
        
        try:
            logger.info(
                "Initializing PostgreSQL connection pool with %d-%d connections to %s:%d/%s",
                self.config.min_connections,
                self.config.max_connections,
                self.config.host,
                self.config.port,
                self.config.database
            )
            
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.min_connections,
                maxconn=self.config.max_connections,
                **self.config.get_dsn()
            )
            
            # Test the pool by getting and immediately returning a connection
            test_conn = self._pool.getconn()
            if test_conn:
                self._pool.putconn(test_conn)
                logger.info("Successfully initialized PostgreSQL connection pool")
            else:
                raise ConnectionError("Failed to get a test connection from the pool")
                
        except (OperationalError, InterfaceError) as e:
            logger.error("Failed to initialize PostgreSQL connection pool: %s", str(e))
            self._pool = None
            raise ConnectionError(f"Failed to initialize PostgreSQL connection pool: {str(e)}") from e
    
    def _get_connection(self) -> psycopg2.extensions.connection:
        """
        Get a database connection, either from the pool or by creating a new one.
        
        Returns:
            A psycopg2 connection object
            
        Raises:
            ConnectionError: If unable to establish a connection after retries
        """
        retry_count = 0
        last_exception = None
        
        while retry_count <= self.config.retry_attempts:
            try:
                if self._pool:
                    conn = self._pool.getconn()
                    logger.debug("Acquired connection from pool")
                else:
                    conn = psycopg2.connect(
                        **self.config.get_dsn(),
                        connect_timeout=self.config.connection_timeout
                    )
                    logger.debug("Created new database connection")
                
                # Enable automatic conversion of Python dict to JSON
                psycopg2.extras.register_json(conn)
                
                # Set session parameters
                with conn.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {self.config.schema}")
                    cursor.execute(f"SET statement_timeout TO {self.config.statement_timeout}")
                
                return conn
                
            except (OperationalError, InterfaceError) as e:
                last_exception = e
                retry_count += 1
                
                if retry_count <= self.config.retry_attempts:
                    # Calculate backoff time with exponential increase
                    backoff = self.config.retry_delay * (2 ** (retry_count - 1))
                    logger.warning(
                        "Connection attempt %d/%d failed: %s. Retrying in %d seconds...",
                        retry_count,
                        self.config.retry_attempts + 1,
                        str(e),
                        backoff
                    )
                    time.sleep(backoff)
                else:
                    logger.error(
                        "Failed to establish database connection after %d attempts: %s",
                        self.config.retry_attempts + 1,
                        str(e)
                    )
        
        # If we get here, all retries have failed
        error_msg = f"Could not establish PostgreSQL connection after {self.config.retry_attempts + 1} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        
        raise ConnectionError(error_msg)
    
    def _release_connection(self, conn: psycopg2.extensions.connection) -> None:
        """
        Release a connection back to the pool or close it if not using pooling.
        
        Args:
            conn: The connection to release
        """
        if conn:
            try:
                if self._pool:
                    self._pool.putconn(conn)
                    logger.debug("Released connection back to pool")
                else:
                    conn.close()
                    logger.debug("Closed database connection")
            except Exception as e:
                logger.warning("Error releasing database connection: %s", str(e))
    
    def __enter__(self) -> 'PostgresConnection':
        """Context manager entry point."""
        self._conn = self._get_connection()
        self._cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point with proper resource cleanup."""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        
        if self._conn:
            if exc_type is not None:
                # An exception occurred, rollback any pending transaction
                try:
                    self._conn.rollback()
                    logger.debug("Rolled back transaction due to exception")
                except Exception as e:
                    logger.warning("Error rolling back transaction: %s", str(e))
            else:
                # No exception, commit any pending transaction
                try:
                    self._conn.commit()
                    logger.debug("Committed transaction")
                except Exception as e:
                    logger.warning("Error committing transaction: %s", str(e))
            
            self._release_connection(self._conn)
            self._conn = None
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[list, dict[str, Any]]] = None,
        fetch_all: bool = True
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: SQL query string with parameter placeholders
            params: Parameters to bind to the query
            fetch_all: Whether to fetch all results or just one row
            
        Returns:
            List of dictionaries representing the query results
            
        Raises:
            QueryError: If the query execution fails
        """
        if not self._cursor or not self._conn:
            raise DatabaseError("No active database connection. Use with statement.")
        
        try:
            logger.debug("Executing query: %s with params: %s", query, params)
            self._cursor.execute(query, params or [])
            
            if fetch_all:
                results = self._cursor.fetchall()
                logger.debug("Query returned %d rows", len(results))
                return results
            else:
                result = self._cursor.fetchone()
                return [result] if result else []
                
        except Exception as e:
            # Rollback the transaction
            if self._conn:
                try:
                    self._conn.rollback()
                except Exception as rollback_error:
                    logger.warning("Error rolling back transaction: %s", str(rollback_error))
            
            logger.error("Query execution failed: %s", str(e))
            raise QueryError(f"Query execution failed: {str(e)}") from e
    
    def execute_batch(
        self, 
        query: str, 
        params_list: list[Union[list, dict[str, Any]]]
    ) -> int:
        """
        Execute a batch of SQL commands with the same query but different parameters.
        
        Args:
            query: SQL query string with parameter placeholders
            params_list: List of parameter sets to bind to the query
            
        Returns:
            Number of rows affected
            
        Raises:
            QueryError: If the batch execution fails
        """
        if not self._cursor or not self._conn:
            raise DatabaseError("No active database connection. Use with statement.")
        
        try:
            logger.debug("Executing batch query with %d parameter sets", len(params_list))
            psycopg2.extras.execute_batch(self._cursor, query, params_list)
            affected_rows = self._cursor.rowcount
            logger.debug("Batch query affected %d rows", affected_rows)
            return affected_rows
                
        except Exception as e:
            # Rollback the transaction
            if self._conn:
                try:
                    self._conn.rollback()
                except Exception as rollback_error:
                    logger.warning("Error rolling back transaction: %s", str(rollback_error))
            
            logger.error("Batch execution failed: %s", str(e))
            raise QueryError(f"Batch execution failed: {str(e)}") from e
    
    def execute_transaction(
        self, 
        queries: list[tuple[str, Optional[Union[list, dict[str, Any]]]]]
    ) -> bool:
        """
        Execute multiple queries as a single transaction.
        
        Args:
            queries: List of (query, params) tuples to execute in transaction
            
        Returns:
            True if transaction was successful
            
        Raises:
            QueryError: If any query in the transaction fails
        """
        if not self._cursor or not self._conn:
            raise DatabaseError("No active database connection. Use with statement.")
        
        try:
            logger.debug("Beginning transaction with %d queries", len(queries))
            
            for i, (query, params) in enumerate(queries):
                logger.debug("Executing transaction query %d/%d", i+1, len(queries))
                self._cursor.execute(query, params or [])
            
            self._conn.commit()
            logger.debug("Transaction committed successfully")
            return True
                
        except Exception as e:
            # Rollback the transaction
            if self._conn:
                try:
                    self._conn.rollback()
                    logger.debug("Transaction rolled back due to error")
                except Exception as rollback_error:
                    logger.warning("Error rolling back transaction: %s", str(rollback_error))
            
            logger.error("Transaction failed: %s", str(e))
            raise QueryError(f"Transaction failed: {str(e)}") from e
    
    def close(self) -> None:
        """Close all connections and the connection pool."""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        
        if self._conn:
            self._release_connection(self._conn)
            self._conn = None
        
        if self._pool:
            self._pool.closeall()
            logger.info("Closed all connections in the pool")
            self._pool = None
    
    def check_connection_health(self) -> dict[str, Any]:
        """
        Check the health of the database connection.
        
        Returns:
            Dictionary with health status information
        """
        health_info = {
            "status": "unknown",
            "message": "",
            "details": {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database,
                "pool_enabled": self.config.use_connection_pool,
            }
        }
        
        try:
            with self as conn:
                # Check if we can execute a simple query
                start_time = time.time()
                conn.execute_query("SELECT 1 AS connection_test")
                response_time = time.time() - start_time
                
                # Get server version
                version_info = conn.execute_query("SHOW server_version")
                server_version = version_info[0]["server_version"] if version_info else "unknown"
                
                # Get connection pool stats if available
                if self._pool:
                    health_info["details"]["pool_stats"] = {
                        "min_connections": self.config.min_connections,
                        "max_connections": self.config.max_connections,
                    }
                
                health_info.update({
                    "status": "healthy",
                    "message": "Database connection is healthy",
                    "details": {
                        **health_info["details"],
                        "response_time_ms": round(response_time * 1000, 2),
                        "server_version": server_version,
                    }
                })
                
        except Exception as e:
            health_info.update({
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "error": str(e),
            })
            logger.error("Database health check failed: %s", str(e))
        
        return health_info


class AsyncPostgresConnection:
    """
    Asynchronous PostgreSQL connection manager with connection pooling,
    retry logic, and comprehensive error handling.
    
    This class provides a high-level interface for interacting with PostgreSQL
    databases in an asynchronous manner, using asyncpg for high performance.
    """
    
    def __init__(self, config: Optional[PostgresConfig] = None):
        """
        Initialize the asynchronous PostgreSQL connection manager.
        
        Args:
            config: PostgreSQL connection configuration. If None, loads from environment.
        """
        self.config = config or PostgresConfig.from_env()
        self._pool = None
        self._conn = None
    
    async def _initialize_pool(self) -> None:
        """Initialize the asyncpg connection pool."""
        if not self.config.use_connection_pool:
            logger.debug("Async connection pooling disabled, will create individual connections")
            return
        
        try:
            logger.info(
                "Initializing asyncpg connection pool with %d-%d connections to %s:%d/%s",
                self.config.min_connections,
                self.config.max_connections,
                self.config.host,
                self.config.port,
                self.config.database
            )
            
            # Create SSL context if needed
            ssl_context = None
            if self.config.ssl_mode != "disable":
                ssl_context = ssl.create_default_context()
                if self.config.ssl_mode == "require":
                    ssl_context.check_hostname = True
                    ssl_context.verify_mode = ssl.CERT_REQUIRED
                else:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
            
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.statement_timeout / 1000,  # Convert ms to seconds
                ssl=ssl_context,
                server_settings={
                    'application_name': self.config.application_name,
                    'search_path': self.config.schema,
                }
            )
            
            logger.info("Successfully initialized asyncpg connection pool")
                
        except Exception as e:
            logger.error("Failed to initialize asyncpg connection pool: %s", str(e))
            self._pool = None
            raise ConnectionError(f"Failed to initialize asyncpg connection pool: {str(e)}") from e
    
    async def _get_connection(self) -> asyncpg.Connection:
        """
        Get a database connection, either from the pool or by creating a new one.
        
        Returns:
            An asyncpg connection object
            
        Raises:
            ConnectionError: If unable to establish a connection after retries
        """
        retry_count = 0
        last_exception = None
        
        while retry_count <= self.config.retry_attempts:
            try:
                if self._pool:
                    conn = await self._pool.acquire()
                    logger.debug("Acquired async connection from pool")
                else:
                    conn = await asyncpg.connect(
                        host=self.config.host,
                        port=self.config.port,
                        user=self.config.user,
                        password=self.config.password,
                        database=self.config.database,
                        timeout=self.config.connection_timeout,
                        command_timeout=self.config.statement_timeout / 1000,  # Convert ms to seconds
                        server_settings={
                            'application_name': self.config.application_name,
                            'search_path': self.config.schema,
                        }
                    )
                    logger.debug("Created new async database connection")
                
                # Set up JSON encoding/decoding
                await conn.set_type_codec(
                    'json',
                    encoder=json.dumps,
                    decoder=json.loads,
                    schema='pg_catalog'
                )
                
                await conn.set_type_codec(
                    'jsonb',
                    encoder=json.dumps,
                    decoder=json.loads,
                    schema='pg_catalog'
                )
                
                return conn
                
            except Exception as e:
                last_exception = e
                retry_count += 1
                
                if retry_count <= self.config.retry_attempts:
                    # Calculate backoff time with exponential increase
                    backoff = self.config.retry_delay * (2 ** (retry_count - 1))
                    logger.warning(
                        "Async connection attempt %d/%d failed: %s. Retrying in %d seconds...",
                        retry_count,
                        self.config.retry_attempts + 1,
                        str(e),
                        backoff
                    )
                    await asyncio.sleep(backoff)
                else:
                    logger.error(
                        "Failed to establish async database connection after %d attempts: %s",
                        self.config.retry_attempts + 1,
                        str(e)
                    )
        
        # If we get here, all retries have failed
        error_msg = f"Could not establish async PostgreSQL connection after {self.config.retry_attempts + 1} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        
        raise ConnectionError(error_msg)
    
    async def _release_connection(self, conn: asyncpg.Connection) -> None:
        """
        Release a connection back to the pool or close it if not using pooling.
        
        Args:
            conn: The connection to release
        """
        if conn:
            try:
                if self._pool:
                    await self._pool.release(conn)
                    logger.debug("Released async connection back to pool")
                else:
                    await conn.close()
                    logger.debug("Closed async database connection")
            except Exception as e:
                logger.warning("Error releasing async database connection: %s", str(e))
    
    async def __aenter__(self) -> 'AsyncPostgresConnection':
        """Async context manager entry point."""
        if not self._pool and self.config.use_connection_pool:
            await self._initialize_pool()
        
        self._conn = await self._get_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit point with proper resource cleanup."""
        if self._conn:
            if exc_type is not None:
                # An exception occurred, rollback any pending transaction
                try:
                    await self._conn.execute("ROLLBACK")
                    logger.debug("Rolled back async transaction due to exception")
                except Exception as e:
                    logger.warning("Error rolling back async transaction: %s", str(e))
            
            await self._release_connection(self._conn)
            self._conn = None
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[list] = None,
        fetch_all: bool = True
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query asynchronously and return the results.
        
        Args:
            query: SQL query string with parameter placeholders
            params: Parameters to bind to the query
            fetch_all: Whether to fetch all results or just one row
            
        Returns:
            List of dictionaries representing the query results
            
        Raises:
            QueryError: If the query execution fails
        """
        if not self._conn:
            raise DatabaseError("No active async database connection. Use async with statement.")
        
        try:
            logger.debug("Executing async query: %s with params: %s", query, params)
            
            if fetch_all:
                results = await self._conn.fetch(query, *(params or []))
                logger.debug("Async query returned %d rows", len(results))
                # Convert Record objects to dictionaries
                return [dict(record) for record in results]
            else:
                result = await self._conn.fetchrow(query, *(params or []))
                return [dict(result)] if result else []
                
        except Exception as e:
            logger.error("Async query execution failed: %s", str(e))
            raise QueryError(f"Async query execution failed: {str(e)}") from e
    
    async def execute_transaction(
        self, 
        queries: list[tuple[str, Optional[list]]]
    ) -> bool:
        """
        Execute multiple queries as a single transaction asynchronously.
        
        Args:
            queries: List of (query, params) tuples to execute in transaction
            
        Returns:
            True if transaction was successful
            
        Raises:
            QueryError: If any query in the transaction fails
        """
        if not self._conn:
            raise DatabaseError("No active async database connection. Use async with statement.")
        
        try:
            logger.debug("Beginning async transaction with %d queries", len(queries))
            
            async with self._conn.transaction():
                for i, (query, params) in enumerate(queries):
                    logger.debug("Executing async transaction query %d/%d", i+1, len(queries))
                    await self._conn.execute(query, *(params or []))
            
            logger.debug("Async transaction committed successfully")
            return True
                
        except Exception as e:
            logger.error("Async transaction failed: %s", str(e))
            raise QueryError(f"Async transaction failed: {str(e)}") from e
    
    async def close(self) -> None:
        """Close all connections and the connection pool."""
        if self._conn:
            await self._release_connection(self._conn)
            self._conn = None
        
        if self._pool:
            await self._pool.close()
            logger.info("Closed all connections in the async pool")
            self._pool = None
    
    async def check_connection_health(self) -> dict[str, Any]:
        """
        Check the health of the async database connection.
        
        Returns:
            Dictionary with health status information
        """
        health_info = {
            "status": "unknown",
            "message": "",
            "details": {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database,
                "pool_enabled": self.config.use_connection_pool,
                "connection_type": "async",
            }
        }
        
        try:
            async with self as conn:
                # Check if we can execute a simple query
                start_time = time.time()
                await conn.execute_query("SELECT 1 AS connection_test")
                response_time = time.time() - start_time
                
                # Get server version
                version_info = await conn.execute_query("SHOW server_version")
                server_version = version_info[0]["server_version"] if version_info else "unknown"
                
                health_info.update({
                    "status": "healthy",
                    "message": "Async database connection is healthy",
                    "details": {
                        **health_info["details"],
                        "response_time_ms": round(response_time * 1000, 2),
                        "server_version": server_version,
                    }
                })
                
        except Exception as e:
            health_info.update({
                "status": "unhealthy",
                "message": f"Async database connection failed: {str(e)}",
                "error": str(e),
            })
            logger.error("Async database health check failed: %s", str(e))
        
        return health_info


def get_postgres_connection(
    config: Optional[PostgresConfig] = None,
    async_mode: Optional[bool] = None
) -> Union[PostgresConnection, AsyncPostgresConnection]:
    """
    Factory function to get the appropriate PostgreSQL connection based on configuration.
    
    Args:
        config: PostgreSQL connection configuration. If None, loads from environment.
        async_mode: Override the connection mode from config if provided
        
    Returns:
        Either a synchronous or asynchronous PostgreSQL connection
    """
    config = config or PostgresConfig.from_env()
    
    # Determine if we should use async mode
    use_async = async_mode if async_mode is not None else (
        config.connection_mode == PostgresConnectionMode.ASYNCHRONOUS
    )
    
    if use_async:
        return AsyncPostgresConnection(config)
    else:
        return PostgresConnection(config)


# Import asyncio here to avoid circular imports
import asyncio