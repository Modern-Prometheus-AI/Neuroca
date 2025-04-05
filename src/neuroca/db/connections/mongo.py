"""
MongoDB Connection Manager for NeuroCognitive Architecture (NCA).

This module provides a robust MongoDB connection management system for the NCA project.
It handles connection pooling, authentication, error handling, and reconnection strategies.
The implementation follows MongoDB best practices for production environments.

Usage:
    from neuroca.db.connections.mongo import MongoDBConnection
    
    # Using as a context manager (recommended)
    with MongoDBConnection(config) as mongo_client:
        db = mongo_client.get_database("nca_memory")
        collection = db.get_collection("working_memory")
        result = collection.find_one({"memory_id": "12345"})
    
    # Using directly (connection will be managed by the class)
    mongo_conn = MongoDBConnection(config)
    mongo_conn.connect()
    db = mongo_conn.get_database("nca_memory")
    # ... perform operations ...
    mongo_conn.close()
"""

import logging
import os
import time
from typing import Any, Optional, Union
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (
    AutoReconnect,
    ConfigurationError,
    ConnectionFailure,
    NetworkTimeout,
    OperationFailure,
    ServerSelectionTimeoutError,
)

from neuroca.config.settings import get_settings

# Configure logger
logger = logging.getLogger(__name__)

class MongoDBConnectionError(Exception):
    """Custom exception for MongoDB connection issues."""
    pass

class MongoDBConnection:
    """
    MongoDB Connection Manager for NCA.
    
    This class handles MongoDB connection lifecycle, including:
    - Connection establishment with retry logic
    - Authentication
    - Connection pooling
    - Graceful disconnection
    - Error handling and recovery
    
    Attributes:
        config (Dict[str, Any]): Configuration dictionary for MongoDB connection
        client (Optional[MongoClient]): PyMongo client instance
        connected (bool): Connection status flag
        max_retry_attempts (int): Maximum number of connection retry attempts
        retry_delay (int): Delay between retry attempts in seconds
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize MongoDB connection manager.
        
        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary for MongoDB connection.
                If None, configuration will be loaded from environment variables.
                
        Configuration parameters:
            - MONGO_URI: Full MongoDB connection URI (overrides other parameters if provided)
            - MONGO_HOST: MongoDB host (default: localhost)
            - MONGO_PORT: MongoDB port (default: 27017)
            - MONGO_USERNAME: MongoDB username
            - MONGO_PASSWORD: MongoDB password
            - MONGO_AUTH_SOURCE: Authentication database (default: admin)
            - MONGO_AUTH_MECHANISM: Authentication mechanism
            - MONGO_SSL: Use SSL for connection (default: False)
            - MONGO_SSL_CERT_REQS: SSL certificate requirements
            - MONGO_RETRY_WRITES: Enable retry writes (default: True)
            - MONGO_MAX_POOL_SIZE: Connection pool size (default: 100)
            - MONGO_MIN_POOL_SIZE: Minimum pool size (default: 0)
            - MONGO_MAX_IDLE_TIME_MS: Max connection idle time in ms (default: 10000)
            - MONGO_CONNECT_TIMEOUT_MS: Connection timeout in ms (default: 20000)
            - MONGO_SERVER_SELECTION_TIMEOUT_MS: Server selection timeout in ms (default: 30000)
            - MONGO_MAX_RETRY_ATTEMPTS: Max connection retry attempts (default: 3)
            - MONGO_RETRY_DELAY_SECONDS: Delay between retry attempts in seconds (default: 2)
        """
        self.config = config or self._load_config_from_env()
        self.client: Optional[MongoClient] = None
        self.connected = False
        self.max_retry_attempts = self.config.get('max_retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay_seconds', 2)
        
        # Validate configuration
        self._validate_config()
        
        logger.debug("MongoDB connection manager initialized with config: %s", 
                    {k: v if k != 'password' else '******' for k, v in self.config.items()})

    def _load_config_from_env(self) -> dict[str, Any]:
        """
        Load MongoDB configuration from environment variables.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        settings = get_settings()
        
        # Check if a full URI is provided
        mongo_uri = os.environ.get('MONGO_URI') or getattr(settings, 'MONGO_URI', None)
        
        if mongo_uri:
            return {
                'uri': mongo_uri,
                'max_retry_attempts': int(os.environ.get('MONGO_MAX_RETRY_ATTEMPTS', '3')),
                'retry_delay_seconds': int(os.environ.get('MONGO_RETRY_DELAY_SECONDS', '2')),
            }
        
        # Otherwise, build configuration from individual settings
        config = {
            'host': os.environ.get('MONGO_HOST', getattr(settings, 'MONGO_HOST', 'localhost')),
            'port': int(os.environ.get('MONGO_PORT', getattr(settings, 'MONGO_PORT', '27017'))),
            'username': os.environ.get('MONGO_USERNAME', getattr(settings, 'MONGO_USERNAME', None)),
            'password': os.environ.get('MONGO_PASSWORD', getattr(settings, 'MONGO_PASSWORD', None)),
            'auth_source': os.environ.get('MONGO_AUTH_SOURCE', getattr(settings, 'MONGO_AUTH_SOURCE', 'admin')),
            'auth_mechanism': os.environ.get('MONGO_AUTH_MECHANISM', getattr(settings, 'MONGO_AUTH_MECHANISM', None)),
            'ssl': os.environ.get('MONGO_SSL', getattr(settings, 'MONGO_SSL', 'False')).lower() == 'true',
            'ssl_cert_reqs': os.environ.get('MONGO_SSL_CERT_REQS', getattr(settings, 'MONGO_SSL_CERT_REQS', None)),
            'retry_writes': os.environ.get('MONGO_RETRY_WRITES', getattr(settings, 'MONGO_RETRY_WRITES', 'True')).lower() == 'true',
            'max_pool_size': int(os.environ.get('MONGO_MAX_POOL_SIZE', getattr(settings, 'MONGO_MAX_POOL_SIZE', '100'))),
            'min_pool_size': int(os.environ.get('MONGO_MIN_POOL_SIZE', getattr(settings, 'MONGO_MIN_POOL_SIZE', '0'))),
            'max_idle_time_ms': int(os.environ.get('MONGO_MAX_IDLE_TIME_MS', getattr(settings, 'MONGO_MAX_IDLE_TIME_MS', '10000'))),
            'connect_timeout_ms': int(os.environ.get('MONGO_CONNECT_TIMEOUT_MS', getattr(settings, 'MONGO_CONNECT_TIMEOUT_MS', '20000'))),
            'server_selection_timeout_ms': int(os.environ.get('MONGO_SERVER_SELECTION_TIMEOUT_MS', 
                                                            getattr(settings, 'MONGO_SERVER_SELECTION_TIMEOUT_MS', '30000'))),
            'max_retry_attempts': int(os.environ.get('MONGO_MAX_RETRY_ATTEMPTS', getattr(settings, 'MONGO_MAX_RETRY_ATTEMPTS', '3'))),
            'retry_delay_seconds': int(os.environ.get('MONGO_RETRY_DELAY_SECONDS', getattr(settings, 'MONGO_RETRY_DELAY_SECONDS', '2'))),
        }
        
        return config

    def _validate_config(self) -> None:
        """
        Validate MongoDB configuration.
        
        Raises:
            MongoDBConnectionError: If configuration is invalid
        """
        # If URI is provided, no need to validate other parameters
        if 'uri' in self.config and self.config['uri']:
            return
            
        # Check required parameters
        if not self.config.get('host'):
            raise MongoDBConnectionError("MongoDB host is required")
            
        # Validate port range
        port = self.config.get('port')
        if port is not None and (port < 1 or port > 65535):
            raise MongoDBConnectionError(f"Invalid MongoDB port: {port}. Must be between 1 and 65535.")
            
        # If username is provided, password should also be provided
        if self.config.get('username') and not self.config.get('password'):
            logger.warning("MongoDB username provided without password. Authentication may fail.")

    def _build_connection_uri(self) -> str:
        """
        Build MongoDB connection URI from configuration parameters.
        
        Returns:
            str: MongoDB connection URI
        """
        # If URI is already provided, use it
        if 'uri' in self.config and self.config['uri']:
            return self.config['uri']
            
        # Build URI from components
        auth_part = ""
        if self.config.get('username') and self.config.get('password'):
            username = quote_plus(self.config['username'])
            password = quote_plus(self.config['password'])
            auth_part = f"{username}:{password}@"
            
        host_part = self.config['host']
        port_part = f":{self.config['port']}" if 'port' in self.config else ""
        
        # Build query parameters
        query_params = []
        
        if self.config.get('auth_source'):
            query_params.append(f"authSource={self.config['auth_source']}")
            
        if self.config.get('auth_mechanism'):
            query_params.append(f"authMechanism={self.config['auth_mechanism']}")
            
        if self.config.get('ssl'):
            query_params.append("ssl=true")
            
        if self.config.get('ssl_cert_reqs'):
            query_params.append(f"ssl_cert_reqs={self.config['ssl_cert_reqs']}")
            
        if 'retry_writes' in self.config:
            query_params.append(f"retryWrites={'true' if self.config['retry_writes'] else 'false'}")
            
        query_string = f"?{'&'.join(query_params)}" if query_params else ""
        
        return f"mongodb://{auth_part}{host_part}{port_part}/{query_string}"

    def connect(self) -> 'MongoDBConnection':
        """
        Establish connection to MongoDB with retry logic.
        
        Returns:
            MongoDBConnection: Self reference for method chaining
            
        Raises:
            MongoDBConnectionError: If connection fails after all retry attempts
        """
        if self.connected and self.client:
            logger.debug("Already connected to MongoDB")
            return self
            
        uri = self._build_connection_uri()
        
        # Connection options
        options = {
            'maxPoolSize': self.config.get('max_pool_size', 100),
            'minPoolSize': self.config.get('min_pool_size', 0),
            'maxIdleTimeMS': self.config.get('max_idle_time_ms', 10000),
            'connectTimeoutMS': self.config.get('connect_timeout_ms', 20000),
            'serverSelectionTimeoutMS': self.config.get('server_selection_timeout_ms', 30000),
        }
        
        # Attempt connection with retry logic
        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                logger.debug(f"Connecting to MongoDB (attempt {attempt}/{self.max_retry_attempts})")
                self.client = MongoClient(uri, **options)
                
                # Verify connection by executing a command
                self.client.admin.command('ping')
                
                self.connected = True
                logger.info("Successfully connected to MongoDB")
                return self
                
            except (ConnectionFailure, ServerSelectionTimeoutError, NetworkTimeout) as e:
                logger.warning(f"MongoDB connection attempt {attempt} failed: {str(e)}")
                
                if attempt < self.max_retry_attempts:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Failed to connect to MongoDB after maximum retry attempts")
                    raise MongoDBConnectionError(f"Failed to connect to MongoDB: {str(e)}") from e
                    
            except OperationFailure as e:
                # Authentication or authorization failure
                logger.error(f"MongoDB authentication failed: {str(e)}")
                raise MongoDBConnectionError(f"MongoDB authentication failed: {str(e)}") from e
                
            except ConfigurationError as e:
                # Configuration error
                logger.error(f"MongoDB configuration error: {str(e)}")
                raise MongoDBConnectionError(f"MongoDB configuration error: {str(e)}") from e
                
            except Exception as e:
                # Unexpected error
                logger.error(f"Unexpected error connecting to MongoDB: {str(e)}", exc_info=True)
                raise MongoDBConnectionError(f"Unexpected error connecting to MongoDB: {str(e)}") from e
                
        # This should never be reached due to the raise in the loop, but added for completeness
        raise MongoDBConnectionError("Failed to connect to MongoDB")

    def close(self) -> None:
        """
        Close MongoDB connection.
        
        This method gracefully closes the MongoDB connection, ensuring all operations
        are completed and resources are properly released.
        """
        if self.client and self.connected:
            logger.debug("Closing MongoDB connection")
            try:
                self.client.close()
                logger.info("MongoDB connection closed successfully")
            except Exception as e:
                logger.warning(f"Error while closing MongoDB connection: {str(e)}")
            finally:
                self.connected = False
                self.client = None
        else:
            logger.debug("No active MongoDB connection to close")

    def get_client(self) -> MongoClient:
        """
        Get the MongoDB client instance.
        
        Returns:
            MongoClient: PyMongo client instance
            
        Raises:
            MongoDBConnectionError: If not connected to MongoDB
        """
        if not self.connected or not self.client:
            raise MongoDBConnectionError("Not connected to MongoDB. Call connect() first.")
        return self.client

    def get_database(self, db_name: str) -> Database:
        """
        Get a MongoDB database instance.
        
        Args:
            db_name (str): Name of the database
            
        Returns:
            Database: PyMongo database instance
            
        Raises:
            MongoDBConnectionError: If not connected to MongoDB
            ValueError: If db_name is invalid
        """
        if not db_name or not isinstance(db_name, str):
            raise ValueError("Database name must be a non-empty string")
            
        if not self.connected or not self.client:
            raise MongoDBConnectionError("Not connected to MongoDB. Call connect() first.")
            
        return self.client[db_name]

    def get_collection(self, db_name: str, collection_name: str) -> Collection:
        """
        Get a MongoDB collection instance.
        
        Args:
            db_name (str): Name of the database
            collection_name (str): Name of the collection
            
        Returns:
            Collection: PyMongo collection instance
            
        Raises:
            MongoDBConnectionError: If not connected to MongoDB
            ValueError: If db_name or collection_name is invalid
        """
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("Collection name must be a non-empty string")
            
        db = self.get_database(db_name)
        return db[collection_name]

    def is_connected(self) -> bool:
        """
        Check if connected to MongoDB.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connected or not self.client:
            return False
            
        try:
            # Verify connection by executing a command
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection check failed: {str(e)}")
            self.connected = False
            return False

    def reconnect(self) -> 'MongoDBConnection':
        """
        Reconnect to MongoDB.
        
        This method closes the existing connection if any and establishes a new one.
        
        Returns:
            MongoDBConnection: Self reference for method chaining
            
        Raises:
            MongoDBConnectionError: If reconnection fails
        """
        logger.info("Attempting to reconnect to MongoDB")
        self.close()
        return self.connect()

    def __enter__(self) -> 'MongoDBConnection':
        """
        Context manager entry point.
        
        Returns:
            MongoDBConnection: Self reference
            
        Raises:
            MongoDBConnectionError: If connection fails
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit point.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        self.close()

    def execute_with_retry(self, operation, max_retries: int = 3, retry_delay: int = 1, *args, **kwargs) -> Any:
        """
        Execute a MongoDB operation with automatic retry on transient errors.
        
        Args:
            operation: Callable MongoDB operation
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
            *args: Positional arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Any: Result of the operation
            
        Raises:
            Exception: If operation fails after all retry attempts
        """
        if not self.connected or not self.client:
            raise MongoDBConnectionError("Not connected to MongoDB. Call connect() first.")
            
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                return operation(*args, **kwargs)
                
            except AutoReconnect as e:
                last_error = e
                logger.warning(f"MongoDB operation attempt {attempt} failed with AutoReconnect: {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Ensure we're still connected
                    if not self.is_connected():
                        self.reconnect()
                        
            except (ConnectionFailure, ServerSelectionTimeoutError, NetworkTimeout) as e:
                last_error = e
                logger.warning(f"MongoDB operation attempt {attempt} failed with connection error: {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Try to reconnect
                    self.reconnect()
                    
            except Exception as e:
                # Non-retriable error
                logger.error(f"MongoDB operation failed with non-retriable error: {str(e)}")
                raise
                
        # If we get here, all retries failed
        logger.error(f"MongoDB operation failed after {max_retries} attempts")
        raise last_error or Exception("MongoDB operation failed after maximum retry attempts")

    def create_indexes(self, db_name: str, collection_name: str, indexes: list[tuple[Union[str, list[tuple[str, int]]], dict[str, Any]]]) -> list[str]:
        """
        Create indexes on a MongoDB collection.
        
        Args:
            db_name (str): Name of the database
            collection_name (str): Name of the collection
            indexes (List[Tuple[Union[str, List[Tuple[str, int]]], Dict[str, Any]]]): 
                List of index specifications. Each specification is a tuple of:
                - Key specification (string or list of (field, direction) tuples)
                - Index options dictionary
                
        Returns:
            List[str]: List of created index names
            
        Example:
            indexes = [
                ("username", {"unique": True}),
                ([("email", 1), ("created_at", -1)], {"background": True}),
            ]
            mongo_conn.create_indexes("users_db", "users", indexes)
        """
        collection = self.get_collection(db_name, collection_name)
        
        created_indexes = []
        for key_spec, options in indexes:
            try:
                index_name = collection.create_index(key_spec, **options)
                created_indexes.append(index_name)
                logger.info(f"Created index '{index_name}' on {db_name}.{collection_name}")
            except Exception as e:
                logger.error(f"Failed to create index on {db_name}.{collection_name}: {str(e)}")
                raise
                
        return created_indexes

    def ping(self) -> bool:
        """
        Ping MongoDB server to check connectivity.
        
        Returns:
            bool: True if ping succeeds, False otherwise
        """
        if not self.connected or not self.client:
            return False
            
        try:
            result = self.client.admin.command('ping')
            return result.get('ok', 0) == 1
        except Exception as e:
            logger.warning(f"MongoDB ping failed: {str(e)}")
            return False

    def get_server_info(self) -> dict[str, Any]:
        """
        Get MongoDB server information.
        
        Returns:
            Dict[str, Any]: Server information dictionary
            
        Raises:
            MongoDBConnectionError: If not connected to MongoDB
        """
        if not self.connected or not self.client:
            raise MongoDBConnectionError("Not connected to MongoDB. Call connect() first.")
            
        try:
            return self.client.server_info()
        except Exception as e:
            logger.error(f"Failed to get MongoDB server info: {str(e)}")
            raise MongoDBConnectionError(f"Failed to get MongoDB server info: {str(e)}") from e

    def get_connection_status(self) -> dict[str, Any]:
        """
        Get detailed connection status information.
        
        Returns:
            Dict[str, Any]: Connection status information
        """
        status = {
            "connected": self.is_connected(),
            "client_initialized": self.client is not None,
        }
        
        if self.is_connected():
            try:
                server_info = self.get_server_info()
                status.update({
                    "server_version": server_info.get("version", "unknown"),
                    "server_uptime_seconds": server_info.get("uptime", 0),
                    "connection_pool_info": self.client.address if self.client else None,
                })
            except Exception as e:
                status["error"] = str(e)
                
        return status