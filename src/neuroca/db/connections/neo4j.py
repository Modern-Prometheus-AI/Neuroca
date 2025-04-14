"""
Neo4j Database Connection Module for NeuroCognitive Architecture.

This module provides a robust connection interface to Neo4j graph databases
for the NeuroCognitive Architecture (NCA) system. It handles connection pooling,
authentication, query execution, and transaction management with comprehensive
error handling and logging.

Usage:
    from neuroca.db.connections.neo4j import Neo4jConnection, Neo4jConnectionPool
    
    # Single connection usage
    conn = Neo4jConnection(uri="bolt://localhost:7687", 
                          username="neo4j", 
                          password="password")
    result = conn.query("MATCH (n) RETURN n LIMIT 10")
    
    # Connection pool usage
    pool = Neo4jConnectionPool(uri="bolt://localhost:7687",
                              username="neo4j",
                              password="password",
                              max_connections=5)
    with pool.get_connection() as conn:
        result = conn.query("MATCH (n) RETURN n LIMIT 10")
"""

import logging
import os
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Any
from urllib.parse import urlparse

# Neo4j driver imports
try:
    from neo4j import Driver, GraphDatabase, Result, Session, Transaction
    from neo4j.exceptions import (
        AuthError,
        ClientError,
        ConstraintError,
        CypherSyntaxError,
        CypherTypeError,
        DatabaseError,
        DatabaseUnavailable,
        Neo4jError,
        ServiceUnavailable,
        TransientError,
    )
except ImportError:
    raise ImportError(
        "Neo4j driver not installed. Please install it with: pip install neo4j"
    )

# Configure logger
logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Base exception for Neo4j connection errors in the NCA system."""
    pass


class Neo4jQueryError(Exception):
    """Exception raised for errors during query execution."""
    pass


class Neo4jConnection:
    """
    A class to manage connections to a Neo4j database.
    
    This class handles connection establishment, authentication, query execution,
    and transaction management with comprehensive error handling and logging.
    
    Attributes:
        uri (str): The URI of the Neo4j database.
        username (str): The username for authentication.
        password (str): The password for authentication.
        driver (Driver): The Neo4j driver instance.
        max_retry_time (int): Maximum time in seconds to retry connection attempts.
        retry_interval (int): Time in seconds between retry attempts.
    """
    
    def __init__(
        self,
        uri: str = None,
        username: str = None,
        password: str = None,
        max_retry_time: int = 30,
        retry_interval: int = 5,
        database: str = None,
        encrypted: bool = True,
        trust: str = "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
        connection_timeout: int = 30,
        max_transaction_retry_time: int = 30,
        connection_acquisition_timeout: int = 60,
    ):
        """
        Initialize a Neo4j connection.
        
        Args:
            uri (str, optional): The URI of the Neo4j database. Defaults to environment variable NEO4J_URI.
            username (str, optional): The username for authentication. Defaults to environment variable NEO4J_USERNAME.
            password (str, optional): The password for authentication. Defaults to environment variable NEO4J_PASSWORD.
            max_retry_time (int, optional): Maximum time in seconds to retry connection attempts. Defaults to 30.
            retry_interval (int, optional): Time in seconds between retry attempts. Defaults to 5.
            database (str, optional): The name of the database to connect to. Defaults to None (uses default database).
            encrypted (bool, optional): Whether to use encryption. Defaults to True.
            trust (str, optional): Trust strategy for certificates. Defaults to "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES".
            connection_timeout (int, optional): Connection timeout in seconds. Defaults to 30.
            max_transaction_retry_time (int, optional): Maximum transaction retry time in seconds. Defaults to 30.
            connection_acquisition_timeout (int, optional): Connection acquisition timeout in seconds. Defaults to 60.
        
        Raises:
            Neo4jConnectionError: If connection to the database fails after retries.
        """
        # Get connection parameters from environment variables if not provided
        self.uri = uri or os.environ.get("NEO4J_URI")
        self.username = username or os.environ.get("NEO4J_USERNAME")
        self.password = password or os.environ.get("NEO4J_PASSWORD")
        self.database = database or os.environ.get("NEO4J_DATABASE")
        self.max_retry_time = max_retry_time
        self.retry_interval = retry_interval
        
        # Validate connection parameters
        if not self.uri:
            raise Neo4jConnectionError("Neo4j URI is required")
        
        # Validate URI format
        try:
            parsed_uri = urlparse(self.uri)
            if parsed_uri.scheme not in ["bolt", "neo4j", "neo4j+s", "neo4j+ssc", "bolt+s", "bolt+ssc"]:
                raise Neo4jConnectionError(f"Invalid Neo4j URI scheme: {parsed_uri.scheme}")
        except Exception as e:
            raise Neo4jConnectionError(f"Invalid Neo4j URI format: {str(e)}")
        
        # Initialize driver to None
        self.driver = None
        
        # Connection configuration
        self.config = {
            "encrypted": encrypted,
            "trust": trust,
            "connection_timeout": connection_timeout,
            "max_transaction_retry_time": max_transaction_retry_time,
            "connection_acquisition_timeout": connection_acquisition_timeout,
        }
        
        # Establish connection with retry logic
        self._connect_with_retry()
    
    def _connect_with_retry(self) -> None:
        """
        Establish connection to Neo4j with retry logic.
        
        Attempts to connect to the Neo4j database, retrying if connection fails
        up to the configured max_retry_time.
        
        Raises:
            Neo4jConnectionError: If connection to the database fails after retries.
        """
        start_time = time.time()
        last_exception = None
        
        while time.time() - start_time < self.max_retry_time:
            try:
                logger.debug(f"Attempting to connect to Neo4j at {self.uri}")
                
                # Create driver with authentication if provided
                if self.username and self.password:
                    self.driver = GraphDatabase.driver(
                        self.uri,
                        auth=(self.username, self.password),
                        **self.config
                    )
                else:
                    self.driver = GraphDatabase.driver(
                        self.uri,
                        **self.config
                    )
                
                # Verify connection by running a simple query
                with self.driver.session(database=self.database) as session:
                    session.run("RETURN 1").single()
                
                logger.info(f"Successfully connected to Neo4j at {self.uri}")
                return
            
            except AuthError as e:
                # Authentication errors won't be resolved by retrying
                logger.error(f"Neo4j authentication failed: {str(e)}")
                raise Neo4jConnectionError(f"Neo4j authentication failed: {str(e)}")
            
            except (ServiceUnavailable, DatabaseUnavailable) as e:
                # These are potentially transient errors, so we'll retry
                last_exception = e
                logger.warning(f"Neo4j connection attempt failed: {str(e)}. Retrying in {self.retry_interval} seconds...")
                time.sleep(self.retry_interval)
            
            except Exception as e:
                # Unexpected errors
                last_exception = e
                logger.error(f"Unexpected error connecting to Neo4j: {str(e)}")
                time.sleep(self.retry_interval)
        
        # If we've exhausted our retry attempts
        error_msg = f"Failed to connect to Neo4j after {self.max_retry_time} seconds"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        
        logger.error(error_msg)
        raise Neo4jConnectionError(error_msg)
    
    def close(self) -> None:
        """
        Close the Neo4j connection.
        
        Safely closes the driver connection to the Neo4j database.
        """
        if self.driver:
            logger.debug("Closing Neo4j connection")
            self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")
    
    def __enter__(self) -> 'Neo4jConnection':
        """
        Context manager entry point.
        
        Returns:
            Neo4jConnection: The connection instance.
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit point.
        
        Ensures the connection is properly closed when exiting a context.
        
        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        self.close()
    
    def query(
        self, 
        query: str, 
        parameters: dict[str, Any] = None, 
        database: str = None,
        read_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return the results.
        
        Args:
            query (str): The Cypher query to execute.
            parameters (Dict[str, Any], optional): Parameters for the query. Defaults to None.
            database (str, optional): The database to run the query against. Defaults to None.
            read_only (bool, optional): Whether the query is read-only. Defaults to False.
        
        Returns:
            List[Dict[str, Any]]: The query results as a list of dictionaries.
        
        Raises:
            Neo4jQueryError: If the query execution fails.
        """
        if not self.driver:
            raise Neo4jConnectionError("Not connected to Neo4j database")
        
        if parameters is None:
            parameters = {}
        
        # Use the instance database if not specified
        db = database or self.database
        
        try:
            logger.debug(f"Executing query: {query} with parameters: {parameters}")
            
            # Use read transaction for read-only queries, write transaction otherwise
            session_type = "READ" if read_only else "WRITE"
            
            with self.driver.session(database=db, default_access_mode=session_type) as session:
                if read_only:
                    result = session.read_transaction(self._execute_query, query, parameters)
                else:
                    result = session.write_transaction(self._execute_query, query, parameters)
                
                logger.debug(f"Query executed successfully, returning {len(result)} records")
                return result
        
        except CypherSyntaxError as e:
            error_msg = f"Cypher syntax error: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
        
        except CypherTypeError as e:
            error_msg = f"Cypher type error: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
        
        except ConstraintError as e:
            error_msg = f"Neo4j constraint violation: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
        
        except ClientError as e:
            error_msg = f"Neo4j client error: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
        
        except TransientError as e:
            error_msg = f"Neo4j transient error: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
        
        except DatabaseError as e:
            error_msg = f"Neo4j database error: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
        
        except Neo4jError as e:
            error_msg = f"Neo4j error: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error executing Neo4j query: {str(e)}"
            logger.error(error_msg)
            raise Neo4jQueryError(error_msg)
    
    @staticmethod
    def _execute_query(tx: Transaction, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Execute a query within a transaction.
        
        Args:
            tx (Transaction): The Neo4j transaction.
            query (str): The Cypher query to execute.
            parameters (Dict[str, Any]): Parameters for the query.
        
        Returns:
            List[Dict[str, Any]]: The query results as a list of dictionaries.
        """
        result = tx.run(query, parameters)
        return [record.data() for record in result]
    
    @contextmanager
    def transaction(self, database: str = None) -> Generator[Transaction, None, None]:
        """
        Create a transaction context manager.
        
        Args:
            database (str, optional): The database to run the transaction against. Defaults to None.
        
        Yields:
            Transaction: A Neo4j transaction object.
        
        Raises:
            Neo4jConnectionError: If not connected to Neo4j database.
        """
        if not self.driver:
            raise Neo4jConnectionError("Not connected to Neo4j database")
        
        # Use the instance database if not specified
        db = database or self.database
        
        session = self.driver.session(database=db)
        tx = None
        
        try:
            tx = session.begin_transaction()
            logger.debug("Transaction started")
            yield tx
            tx.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            if tx:
                tx.rollback()
                logger.debug("Transaction rolled back")
            raise
        finally:
            session.close()
    
    def is_connected(self) -> bool:
        """
        Check if the connection to Neo4j is active.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1").single()
            return True
        except Exception as e:
            logger.debug(f"Connection check failed: {str(e)}")
            return False
    
    def get_server_info(self) -> dict[str, Any]:
        """
        Get information about the Neo4j server.
        
        Returns:
            Dict[str, Any]: Server information including version, edition, etc.
        
        Raises:
            Neo4jConnectionError: If not connected to Neo4j database.
        """
        if not self.driver:
            raise Neo4jConnectionError("Not connected to Neo4j database")
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition")
                record = result.single()
                if record:
                    return {
                        "name": record["name"],
                        "version": record["versions"][0],
                        "edition": record["edition"]
                    }
                return {}
        except Exception as e:
            logger.error(f"Failed to get server info: {str(e)}")
            raise Neo4jQueryError(f"Failed to get server info: {str(e)}")


class Neo4jConnectionPool:
    """
    A connection pool for Neo4j database connections.
    
    This class manages a pool of Neo4j connections for efficient reuse,
    with support for connection validation, timeout, and automatic reconnection.
    
    Attributes:
        min_connections (int): Minimum number of connections to maintain.
        max_connections (int): Maximum number of connections allowed.
        connection_params (Dict): Parameters for creating new connections.
        pool (Queue): Queue of available connections.
        in_use (Dict): Dictionary of connections currently in use.
        lock (threading.RLock): Lock for thread-safe operations.
    """
    
    def __init__(
        self,
        uri: str = None,
        username: str = None,
        password: str = None,
        database: str = None,
        min_connections: int = 1,
        max_connections: int = 10,
        connection_timeout: int = 30,
        validation_interval: int = 30,
        **connection_kwargs
    ):
        """
        Initialize a Neo4j connection pool.
        
        Args:
            uri (str, optional): The URI of the Neo4j database. Defaults to environment variable.
            username (str, optional): The username for authentication. Defaults to environment variable.
            password (str, optional): The password for authentication. Defaults to environment variable.
            database (str, optional): The database to connect to. Defaults to None.
            min_connections (int, optional): Minimum number of connections to maintain. Defaults to 1.
            max_connections (int, optional): Maximum number of connections allowed. Defaults to 10.
            connection_timeout (int, optional): Timeout for acquiring a connection in seconds. Defaults to 30.
            validation_interval (int, optional): Time interval in seconds to validate idle connections. Defaults to 30.
            **connection_kwargs: Additional arguments to pass to Neo4jConnection.
        
        Raises:
            ValueError: If min_connections > max_connections or if either is negative.
        """
        if min_connections < 0 or max_connections < 1:
            raise ValueError("Connection counts must be positive")
        
        if min_connections > max_connections:
            raise ValueError("min_connections cannot be greater than max_connections")
        
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.validation_interval = validation_interval
        
        # Store connection parameters for creating new connections
        self.connection_params = {
            "uri": uri,
            "username": username,
            "password": password,
            "database": database,
            **connection_kwargs
        }
        
        # Initialize the connection pool
        self.pool = Queue()
        self.in_use = {}  # Track connections in use
        self.lock = threading.RLock()
        self.last_validation_time = time.time()
        
        # Initialize the minimum number of connections
        self._initialize_pool()
        
        # Start validation thread
        self._start_validation_thread()
    
    def _initialize_pool(self) -> None:
        """
        Initialize the connection pool with the minimum number of connections.
        """
        logger.debug(f"Initializing connection pool with {self.min_connections} connections")
        for _ in range(self.min_connections):
            try:
                connection = self._create_connection()
                self.pool.put(connection)
            except Neo4jConnectionError as e:
                logger.error(f"Failed to initialize connection in pool: {str(e)}")
                # Continue initialization even if some connections fail
                continue
    
    def _create_connection(self) -> Neo4jConnection:
        """
        Create a new Neo4j connection.
        
        Returns:
            Neo4jConnection: A new Neo4j connection.
        
        Raises:
            Neo4jConnectionError: If connection creation fails.
        """
        try:
            logger.debug("Creating new Neo4j connection for pool")
            return Neo4jConnection(**self.connection_params)
        except Exception as e:
            logger.error(f"Failed to create Neo4j connection: {str(e)}")
            raise Neo4jConnectionError(f"Failed to create Neo4j connection: {str(e)}")
    
    def _start_validation_thread(self) -> None:
        """
        Start a background thread to periodically validate idle connections.
        """
        def validation_worker():
            while True:
                try:
                    time.sleep(self.validation_interval)
                    self._validate_idle_connections()
                except Exception as e:
                    logger.error(f"Error in connection validation thread: {str(e)}")
        
        thread = threading.Thread(target=validation_worker, daemon=True)
        thread.start()
        logger.debug("Connection validation thread started")
    
    def _validate_idle_connections(self) -> None:
        """
        Validate all idle connections in the pool and replace invalid ones.
        """
        with self.lock:
            # Skip validation if it was done recently
            current_time = time.time()
            if current_time - self.last_validation_time < self.validation_interval:
                return
            
            self.last_validation_time = current_time
            logger.debug("Validating idle connections in pool")
            
            # Get all connections from the pool
            connections = []
            valid_connections = []
            
            try:
                while not self.pool.empty():
                    connections.append(self.pool.get_nowait())
            except Empty:
                pass
            
            # Validate each connection
            for conn in connections:
                if conn.is_connected():
                    valid_connections.append(conn)
                else:
                    logger.warning("Found invalid connection in pool, closing and replacing")
                    try:
                        conn.close()
                    except Exception as e:
                        logger.error(f"Error closing invalid connection: {str(e)}")
                    
                    try:
                        valid_connections.append(self._create_connection())
                    except Neo4jConnectionError as e:
                        logger.error(f"Failed to replace invalid connection: {str(e)}")
            
            # Return valid connections to the pool
            for conn in valid_connections:
                self.pool.put(conn)
            
            logger.debug(f"Connection validation complete. {len(valid_connections)} valid connections in pool")
    
    @contextmanager
    def get_connection(self) -> Generator[Neo4jConnection, None, None]:
        """
        Get a connection from the pool.
        
        This context manager acquires a connection from the pool and returns it
        to the pool when the context exits.
        
        Yields:
            Neo4jConnection: A Neo4j connection from the pool.
        
        Raises:
            Neo4jConnectionError: If unable to acquire a connection within the timeout.
        """
        connection = None
        connection_id = None
        
        try:
            connection = self._acquire_connection()
            connection_id = id(connection)
            
            with self.lock:
                self.in_use[connection_id] = connection
            
            yield connection
        
        finally:
            if connection:
                with self.lock:
                    if connection_id in self.in_use:
                        del self.in_use[connection_id]
                
                # Return the connection to the pool if it's still valid
                if connection.is_connected():
                    self.pool.put(connection)
                else:
                    # If the connection is invalid, close it and create a new one
                    logger.warning("Returning invalid connection to pool, replacing")
                    try:
                        connection.close()
                    except Exception as e:
                        logger.error(f"Error closing invalid connection: {str(e)}")
                    
                    try:
                        new_connection = self._create_connection()
                        self.pool.put(new_connection)
                    except Neo4jConnectionError as e:
                        logger.error(f"Failed to create replacement connection: {str(e)}")
    
    def _acquire_connection(self) -> Neo4jConnection:
        """
        Acquire a connection from the pool or create a new one if needed.

        Returns:
            Neo4jConnection: A Neo4j connection.

        Raises:
            Neo4jConnectionError: If unable to acquire a connection within the timeout.
        """
        start_time = time.time()

        while time.time() - start_time < self.connection_timeout:
            # Try to get a connection from the pool without waiting
            try:
                connection = self.pool.get_nowait()
                logger.debug("Acquired connection from pool")

                # Validate the connection
                if connection.is_connected():
                    return connection # <<< Path 1: Got valid connection immediately

                # RET505 Fix 1: Removed 'else:' and unindented block below
                logger.warning("Acquired invalid connection from pool, closing and retrying")
                try:
                    connection.close()
                except neo4j.exceptions.Neo4jError as e: # BLE001 Fix 1: Catch specific error
                    logger.error(f"Error closing invalid connection: {str(e)}")
                # Loop continues to try again

            except Empty:
                # Pool was empty, try to create or wait
                with self.lock:
                    total_connections = self.pool.qsize() + len(self.in_use) # Assuming self.in_use exists

                    if total_connections < self.max_connections:
                        # Create a new connection if below max capacity
                        try:
                            connection = self._create_connection()
                            logger.debug("Created new connection for pool")
                            return connection # <<< Path 2: Created new connection
                        except Neo4jConnectionError as e:
                            logger.error(f"Failed to create new connection: {str(e)}")
                            # Wait before potentially retrying creation in next loop iteration
                            time.sleep(0.5) # Short sleep after creation failure
                            continue # Continue loop to retry logic

                    # Implicitly else (at max capacity), fall through to wait below

                # At max capacity, wait briefly for a connection
                logger.debug("Connection pool at capacity, waiting for available connection")
                try:
                    connection = self.pool.get(timeout=1) # Wait up to 1 second

                    # Validate the connection acquired after waiting
                    if connection.is_connected():
                        logger.debug("Acquired connection from pool after waiting")
                        return connection # <<< Path 3: Got valid connection after waiting

                    # RET505 Fix 2: Removed 'else:' and unindented block below
                    logger.warning("Acquired invalid connection from pool after waiting, closing and retrying")
                    try:
                        connection.close()
                    except neo4j.exceptions.Neo4jError as e: # BLE001 Fix 2: Catch specific error
                        logger.error(f"Error closing invalid connection after waiting: {str(e)}")
                    # Loop continues to try again

                except Empty:
                    # Timeout waiting for a connection, loop continues
                    logger.debug("Timeout waiting for connection from pool")
                    # Optional: Small sleep if pool is often at capacity and timing out
                    # time.sleep(0.1)
                    continue # Loop continues

            # Optional: Small sleep to prevent extremely tight loops in edge cases
            time.sleep(0.05)

        # If loop finishes, timeout occurred
        raise Neo4jConnectionError(f"Unable to acquire a connection within {self.connection_timeout} seconds")

    def close_all(self) -> None:
        """
        Close all connections in the pool.
        
        This method should be called when shutting down the application to
        properly release all database resources.
        """
        logger.info("Closing all connections in the pool")
        
        with self.lock:
            # Close all connections in the pool
            closed_count = 0
            try:
                while not self.pool.empty():
                    connection = self.pool.get_nowait()
                    try:
                        connection.close()
                        closed_count += 1
                    except Exception as e:
                        logger.error(f"Error closing connection: {str(e)}")
            except Empty:
                pass
            
            # Log warning about in-use connections
            if self.in_use:
                logger.warning(f"{len(self.in_use)} connections still in use during pool shutdown")
            
            logger.info(f"Closed {closed_count} connections in the pool")
    
    def __del__(self) -> None:
        """
        Destructor to ensure all connections are closed when the pool is garbage collected.
        """
        try:
            self.close_all()
        except Exception as e:
            logger.error(f"Error during connection pool cleanup: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example with a single connection
    try:
        conn = Neo4jConnection(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        
        result = conn.query("MATCH (n) RETURN count(n) as count")
        print(f"Node count: {result[0]['count']}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Example with connection pool
    try:
        pool = Neo4jConnectionPool(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password",
            min_connections=2,
            max_connections=5
        )
        
        with pool.get_connection() as conn:
            result = conn.query("MATCH (n) RETURN count(n) as count")
            print(f"Node count: {result[0]['count']}")
        
        pool.close_all()
    except Exception as e:
        print(f"Error: {str(e)}")