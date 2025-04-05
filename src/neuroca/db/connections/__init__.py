"""
Database Connections Module for NeuroCognitive Architecture (NCA)

This module provides a centralized system for managing database connections
across the NeuroCognitive Architecture. It implements connection pooling,
connection lifecycle management, and abstractions for different database types.

The module supports:
- Multiple database types (PostgreSQL, MongoDB, Redis, etc.)
- Connection pooling for performance optimization
- Automatic reconnection strategies
- Connection health monitoring
- Secure credential management
- Contextual usage patterns

Usage Examples:
    # Get a database connection
    with get_connection('memory_store') as conn:
        result = conn.execute_query('SELECT * FROM working_memory')
    
    # Using a specific database type
    mongo_conn = get_mongo_connection('episodic_memory')
    documents = mongo_conn.find({'memory_type': 'episodic'})
    
    # Creating a custom connection
    custom_conn = create_connection(
        name='custom_store',
        conn_type='postgresql',
        config={'host': 'localhost', 'port': 5432}
    )
"""

import logging
import os
import threading
import time
from contextlib import contextmanager
from enum import Enum, auto
from typing import Any, TypeVar

# Import database drivers - these would be installed as dependencies
try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pymongo
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import sqlalchemy
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Configure module logger
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
ConnectionType = TypeVar('ConnectionType')


class DatabaseType(Enum):
    """Enumeration of supported database types."""
    POSTGRESQL = auto()
    MONGODB = auto()
    REDIS = auto()
    SQLITE = auto()
    MYSQL = auto()
    CUSTOM = auto()


class ConnectionStatus(Enum):
    """Enumeration of possible connection statuses."""
    INITIALIZED = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()
    ERROR = auto()
    BUSY = auto()


class ConnectionError(Exception):
    """Base exception for connection-related errors."""
    pass


class ConfigurationError(ConnectionError):
    """Exception raised for configuration issues."""
    pass


class ConnectionTimeoutError(ConnectionError):
    """Exception raised when a connection times out."""
    pass


class ConnectionPoolExhaustedError(ConnectionError):
    """Exception raised when a connection pool is exhausted."""
    pass


class DatabaseNotSupportedError(ConnectionError):
    """Exception raised when a database type is not supported."""
    pass


class ConnectionManager:
    """
    Manages database connections across the application.
    
    This class is responsible for creating, tracking, and managing the lifecycle
    of all database connections. It implements connection pooling and provides
    a centralized interface for obtaining database connections.
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """Implement singleton pattern for ConnectionManager."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the connection manager if not already initialized."""
        with self._lock:
            if self._initialized:
                return
                
            # Connection pools by name and type
            self._pools: dict[str, Any] = {}
            
            # Connection configurations
            self._configs: dict[str, dict[str, Any]] = {}
            
            # Active connections
            self._active_connections: dict[str, list[Any]] = {}
            
            # Connection status tracking
            self._connection_status: dict[str, ConnectionStatus] = {}
            
            # Connection statistics
            self._stats = {
                'created': 0,
                'acquired': 0,
                'released': 0,
                'errors': 0,
                'reconnects': 0
            }
            
            # Health check information
            self._last_health_check = time.time()
            self._health_check_interval = 60  # seconds
            
            self._initialized = True
            logger.info("ConnectionManager initialized")
    
    def register_connection(self, name: str, db_type: DatabaseType, config: dict[str, Any]) -> None:
        """
        Register a new database connection configuration.
        
        Args:
            name: Unique identifier for this connection
            db_type: Type of database (PostgreSQL, MongoDB, etc.)
            config: Configuration parameters for the connection
            
        Raises:
            ConfigurationError: If the configuration is invalid or incomplete
            DatabaseNotSupportedError: If the database type is not supported
        """
        with self._lock:
            # Validate configuration
            self._validate_config(db_type, config)
            
            # Store configuration
            self._configs[name] = {
                'type': db_type,
                'config': config,
                'created_at': time.time(),
                'last_used': None
            }
            
            self._connection_status[name] = ConnectionStatus.INITIALIZED
            logger.info(f"Registered new connection configuration: {name} ({db_type.name})")
    
    def _validate_config(self, db_type: DatabaseType, config: dict[str, Any]) -> None:
        """
        Validate connection configuration for the specified database type.
        
        Args:
            db_type: Type of database
            config: Configuration parameters
            
        Raises:
            ConfigurationError: If configuration is invalid
            DatabaseNotSupportedError: If database type is not supported
        """
        # Check if the database type is supported
        if db_type == DatabaseType.POSTGRESQL and not PSYCOPG2_AVAILABLE:
            raise DatabaseNotSupportedError("PostgreSQL support requires psycopg2 package")
        elif db_type == DatabaseType.MONGODB and not PYMONGO_AVAILABLE:
            raise DatabaseNotSupportedError("MongoDB support requires pymongo package")
        elif db_type == DatabaseType.REDIS and not REDIS_AVAILABLE:
            raise DatabaseNotSupportedError("Redis support requires redis package")
        
        # Validate required configuration parameters
        required_params = {
            DatabaseType.POSTGRESQL: ['host', 'port', 'dbname', 'user', 'password'],
            DatabaseType.MONGODB: ['uri'] if 'uri' in config else ['host', 'port'],
            DatabaseType.REDIS: ['host', 'port'],
            DatabaseType.SQLITE: ['database'],
            DatabaseType.MYSQL: ['host', 'port', 'database', 'user', 'password'],
            DatabaseType.CUSTOM: ['connection_factory']
        }
        
        missing_params = [param for param in required_params.get(db_type, []) 
                         if param not in config]
        
        if missing_params:
            raise ConfigurationError(
                f"Missing required configuration parameters for {db_type.name}: {', '.join(missing_params)}"
            )
    
    def create_pool(self, name: str, min_size: int = 1, max_size: int = 10) -> None:
        """
        Create a connection pool for a registered connection.
        
        Args:
            name: Name of the registered connection
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
            
        Raises:
            ConfigurationError: If the connection is not registered
            ConnectionError: If pool creation fails
        """
        with self._lock:
            if name not in self._configs:
                raise ConfigurationError(f"Connection '{name}' is not registered")
            
            config = self._configs[name]
            db_type = config['type']
            db_config = config['config']
            
            # Create the appropriate connection pool based on database type
            try:
                if db_type == DatabaseType.POSTGRESQL:
                    self._pools[name] = self._create_postgres_pool(db_config, min_size, max_size)
                elif db_type == DatabaseType.MONGODB:
                    self._pools[name] = self._create_mongo_pool(db_config)
                elif db_type == DatabaseType.REDIS:
                    self._pools[name] = self._create_redis_pool(db_config)
                elif db_type == DatabaseType.SQLITE:
                    self._pools[name] = self._create_sqlite_pool(db_config)
                elif db_type == DatabaseType.MYSQL:
                    self._pools[name] = self._create_mysql_pool(db_config, min_size, max_size)
                elif db_type == DatabaseType.CUSTOM:
                    self._pools[name] = self._create_custom_pool(db_config)
                else:
                    raise DatabaseNotSupportedError(f"Unsupported database type: {db_type.name}")
                
                self._active_connections[name] = []
                logger.info(f"Created connection pool for {name} ({db_type.name})")
                
            except Exception as e:
                self._stats['errors'] += 1
                logger.error(f"Failed to create connection pool for {name}: {str(e)}")
                raise ConnectionError(f"Failed to create connection pool: {str(e)}") from e
    
    def _create_postgres_pool(self, config: dict[str, Any], min_size: int, max_size: int) -> Any:
        """Create a PostgreSQL connection pool."""
        if not PSYCOPG2_AVAILABLE:
            raise DatabaseNotSupportedError("PostgreSQL support requires psycopg2 package")
        
        return psycopg2.pool.ThreadedConnectionPool(
            minconn=min_size,
            maxconn=max_size,
            host=config['host'],
            port=config['port'],
            dbname=config['dbname'],
            user=config['user'],
            password=config['password'],
            **{k: v for k, v in config.items() if k not in ['host', 'port', 'dbname', 'user', 'password']}
        )
    
    def _create_mongo_pool(self, config: dict[str, Any]) -> Any:
        """Create a MongoDB connection pool."""
        if not PYMONGO_AVAILABLE:
            raise DatabaseNotSupportedError("MongoDB support requires pymongo package")
        
        if 'uri' in config:
            return MongoClient(config['uri'], **{k: v for k, v in config.items() if k != 'uri'})
        else:
            return MongoClient(
                host=config['host'],
                port=config['port'],
                **{k: v for k, v in config.items() if k not in ['host', 'port']}
            )
    
    def _create_redis_pool(self, config: dict[str, Any]) -> Any:
        """Create a Redis connection pool."""
        if not REDIS_AVAILABLE:
            raise DatabaseNotSupportedError("Redis support requires redis package")
        
        return redis.ConnectionPool(
            host=config['host'],
            port=config['port'],
            **{k: v for k, v in config.items() if k not in ['host', 'port']}
        )
    
    def _create_sqlite_pool(self, config: dict[str, Any]) -> Any:
        """Create a SQLite connection pool using SQLAlchemy."""
        if not SQLALCHEMY_AVAILABLE:
            raise DatabaseNotSupportedError("SQLite pooling requires SQLAlchemy package")
        
        engine = create_engine(f"sqlite:///{config['database']}")
        session_factory = sessionmaker(bind=engine)
        return scoped_session(session_factory)
    
    def _create_mysql_pool(self, config: dict[str, Any], min_size: int, max_size: int) -> Any:
        """Create a MySQL connection pool using SQLAlchemy."""
        if not SQLALCHEMY_AVAILABLE:
            raise DatabaseNotSupportedError("MySQL pooling requires SQLAlchemy package")
        
        url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        engine = create_engine(
            url,
            pool_size=min_size,
            max_overflow=max_size - min_size,
            **{k: v for k, v in config.items() if k not in ['host', 'port', 'database', 'user', 'password']}
        )
        session_factory = sessionmaker(bind=engine)
        return scoped_session(session_factory)
    
    def _create_custom_pool(self, config: dict[str, Any]) -> Any:
        """Create a custom connection pool using the provided factory function."""
        if 'connection_factory' not in config or not callable(config['connection_factory']):
            raise ConfigurationError("Custom connection requires a callable 'connection_factory'")
        
        return config['connection_factory'](**{k: v for k, v in config.items() if k != 'connection_factory'})
    
    @contextmanager
    def get_connection(self, name: str, timeout: float = 30.0) -> Any:
        """
        Get a connection from the pool with context management.
        
        Args:
            name: Name of the registered connection
            timeout: Maximum time to wait for a connection
            
        Yields:
            A database connection
            
        Raises:
            ConfigurationError: If the connection is not registered
            ConnectionPoolExhaustedError: If no connection is available within timeout
            ConnectionError: For other connection-related errors
        """
        conn = None
        try:
            conn = self.acquire_connection(name, timeout)
            yield conn
        finally:
            if conn is not None:
                self.release_connection(name, conn)
    
    def acquire_connection(self, name: str, timeout: float = 30.0) -> Any:
        """
        Acquire a connection from the pool.
        
        Args:
            name: Name of the registered connection
            timeout: Maximum time to wait for a connection
            
        Returns:
            A database connection
            
        Raises:
            ConfigurationError: If the connection is not registered or pool not created
            ConnectionPoolExhaustedError: If no connection is available within timeout
            ConnectionError: For other connection-related errors
        """
        with self._lock:
            if name not in self._configs:
                raise ConfigurationError(f"Connection '{name}' is not registered")
            
            if name not in self._pools:
                raise ConfigurationError(f"Connection pool for '{name}' has not been created")
            
            config = self._configs[name]
            db_type = config['type']
            pool = self._pools[name]
            
            # Update last used timestamp
            self._configs[name]['last_used'] = time.time()
            
            # Attempt to get a connection from the pool
            start_time = time.time()
            conn = None
            last_error = None
            
            while time.time() - start_time < timeout:
                try:
                    if db_type == DatabaseType.POSTGRESQL:
                        conn = pool.getconn()
                    elif db_type == DatabaseType.MONGODB:
                        # MongoDB client is already a connection pool
                        conn = pool
                    elif db_type == DatabaseType.REDIS:
                        conn = redis.Redis(connection_pool=pool)
                    elif db_type == DatabaseType.SQLITE or db_type == DatabaseType.MYSQL:
                        # SQLAlchemy session
                        conn = pool()
                    elif db_type == DatabaseType.CUSTOM:
                        # For custom connections, the pool might be a factory function
                        conn = pool() if callable(pool) else pool
                    
                    if conn is not None:
                        break
                        
                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to acquire connection from pool '{name}': {str(e)}")
                    time.sleep(0.5)  # Short delay before retrying
            
            if conn is None:
                self._stats['errors'] += 1
                error_msg = f"Failed to acquire connection from pool '{name}' within {timeout} seconds"
                if last_error:
                    error_msg += f": {str(last_error)}"
                logger.error(error_msg)
                raise ConnectionPoolExhaustedError(error_msg)
            
            # Track the connection
            self._active_connections[name].append(conn)
            self._stats['acquired'] += 1
            logger.debug(f"Acquired connection from pool '{name}'")
            
            return conn
    
    def release_connection(self, name: str, conn: Any) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            name: Name of the registered connection
            conn: The connection to release
            
        Raises:
            ConfigurationError: If the connection is not registered
            ConnectionError: For connection-related errors
        """
        with self._lock:
            if name not in self._configs:
                raise ConfigurationError(f"Connection '{name}' is not registered")
            
            if name not in self._pools:
                raise ConfigurationError(f"Connection pool for '{name}' has not been created")
            
            if name not in self._active_connections or conn not in self._active_connections[name]:
                logger.warning(f"Attempting to release an untracked connection for '{name}'")
                return
            
            config = self._configs[name]
            db_type = config['type']
            pool = self._pools[name]
            
            try:
                # Release the connection based on database type
                if db_type == DatabaseType.POSTGRESQL:
                    pool.putconn(conn)
                elif db_type == DatabaseType.SQLITE or db_type == DatabaseType.MYSQL:
                    # Close SQLAlchemy session
                    conn.close()
                # For MongoDB and Redis, connections are managed by their respective clients
                
                # Remove from active connections
                self._active_connections[name].remove(conn)
                self._stats['released'] += 1
                logger.debug(f"Released connection back to pool '{name}'")
                
            except Exception as e:
                self._stats['errors'] += 1
                logger.error(f"Error releasing connection back to pool '{name}': {str(e)}")
                raise ConnectionError(f"Failed to release connection: {str(e)}") from e
    
    def close_all_connections(self, name: str = None) -> None:
        """
        Close all connections for a specific pool or all pools.
        
        Args:
            name: Name of the connection pool to close, or None for all pools
            
        Raises:
            ConnectionError: If closing connections fails
        """
        with self._lock:
            pools_to_close = [name] if name else list(self._pools.keys())
            
            for pool_name in pools_to_close:
                if pool_name not in self._pools:
                    logger.warning(f"Attempted to close non-existent pool: {pool_name}")
                    continue
                
                try:
                    # Close active connections
                    active_conns = self._active_connections.get(pool_name, [])
                    for conn in active_conns[:]:  # Create a copy to avoid modification during iteration
                        self.release_connection(pool_name, conn)
                    
                    # Close the pool itself
                    pool = self._pools[pool_name]
                    db_type = self._configs[pool_name]['type']
                    
                    if db_type == DatabaseType.POSTGRESQL:
                        pool.closeall()
                    elif db_type == DatabaseType.MONGODB:
                        pool.close()
                    elif db_type == DatabaseType.REDIS:
                        # Redis connection pools don't need explicit closing
                        pass
                    elif db_type == DatabaseType.SQLITE or db_type == DatabaseType.MYSQL:
                        pool.remove()
                    
                    # Clean up
                    del self._pools[pool_name]
                    self._active_connections[pool_name] = []
                    logger.info(f"Closed all connections for pool '{pool_name}'")
                    
                except Exception as e:
                    self._stats['errors'] += 1
                    logger.error(f"Error closing connections for pool '{pool_name}': {str(e)}")
                    raise ConnectionError(f"Failed to close connections: {str(e)}") from e
    
    def check_health(self) -> dict[str, Any]:
        """
        Check the health of all connection pools.
        
        Returns:
            A dictionary with health information for all pools
        """
        with self._lock:
            now = time.time()
            if now - self._last_health_check < self._health_check_interval:
                # Return cached health info if checked recently
                return self._last_health_info
            
            health_info = {
                'pools': {},
                'stats': self._stats.copy(),
                'timestamp': now
            }
            
            for name, _pool in self._pools.items():
                config = self._configs[name]
                db_type = config['type']
                
                pool_health = {
                    'status': 'unknown',
                    'type': db_type.name,
                    'active_connections': len(self._active_connections.get(name, [])),
                    'last_used': config['last_used'],
                    'created_at': config['created_at']
                }
                
                # Test the connection
                try:
                    # Get a test connection
                    with self.get_connection(name, timeout=5.0) as test_conn:
                        if db_type == DatabaseType.POSTGRESQL:
                            cursor = test_conn.cursor()
                            cursor.execute("SELECT 1")
                            cursor.close()
                        elif db_type == DatabaseType.MONGODB:
                            # Ping the server
                            test_conn.admin.command('ping')
                        elif db_type == DatabaseType.REDIS:
                            test_conn.ping()
                        
                        pool_health['status'] = 'healthy'
                        
                except Exception as e:
                    pool_health['status'] = 'unhealthy'
                    pool_health['error'] = str(e)
                    logger.warning(f"Health check failed for pool '{name}': {str(e)}")
                
                health_info['pools'][name] = pool_health
            
            self._last_health_check = now
            self._last_health_info = health_info
            
            return health_info
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            A dictionary with connection statistics
        """
        with self._lock:
            return {
                'stats': self._stats.copy(),
                'active_connections': {
                    name: len(conns) for name, conns in self._active_connections.items()
                },
                'pools': {
                    name: {
                        'type': config['type'].name,
                        'last_used': config['last_used'],
                        'created_at': config['created_at']
                    } for name, config in self._configs.items() if name in self._pools
                }
            }


# Module-level connection manager instance
_connection_manager = ConnectionManager()


def register_connection(name: str, db_type: DatabaseType, config: dict[str, Any]) -> None:
    """
    Register a new database connection configuration.
    
    Args:
        name: Unique identifier for this connection
        db_type: Type of database (PostgreSQL, MongoDB, etc.)
        config: Configuration parameters for the connection
        
    Raises:
        ConfigurationError: If the configuration is invalid or incomplete
        DatabaseNotSupportedError: If the database type is not supported
    """
    return _connection_manager.register_connection(name, db_type, config)


def create_pool(name: str, min_size: int = 1, max_size: int = 10) -> None:
    """
    Create a connection pool for a registered connection.
    
    Args:
        name: Name of the registered connection
        min_size: Minimum number of connections in the pool
        max_size: Maximum number of connections in the pool
        
    Raises:
        ConfigurationError: If the connection is not registered
        ConnectionError: If pool creation fails
    """
    return _connection_manager.create_pool(name, min_size, max_size)


@contextmanager
def get_connection(name: str, timeout: float = 30.0) -> Any:
    """
    Get a connection from the pool with context management.
    
    Args:
        name: Name of the registered connection
        timeout: Maximum time to wait for a connection
        
    Yields:
        A database connection
        
    Raises:
        ConfigurationError: If the connection is not registered
        ConnectionPoolExhaustedError: If no connection is available within timeout
        ConnectionError: For other connection-related errors
        
    Example:
        with get_connection('my_database') as conn:
            # Use the connection
            result = conn.execute_query('SELECT * FROM my_table')
    """
    with _connection_manager.get_connection(name, timeout) as conn:
        yield conn


def acquire_connection(name: str, timeout: float = 30.0) -> Any:
    """
    Acquire a connection from the pool.
    
    Args:
        name: Name of the registered connection
        timeout: Maximum time to wait for a connection
        
    Returns:
        A database connection
        
    Raises:
        ConfigurationError: If the connection is not registered or pool not created
        ConnectionPoolExhaustedError: If no connection is available within timeout
        ConnectionError: For other connection-related errors
        
    Note:
        When using this function, you must explicitly release the connection
        using release_connection() when done.
    """
    return _connection_manager.acquire_connection(name, timeout)


def release_connection(name: str, conn: Any) -> None:
    """
    Release a connection back to the pool.
    
    Args:
        name: Name of the registered connection
        conn: The connection to release
        
    Raises:
        ConfigurationError: If the connection is not registered
        ConnectionError: For connection-related errors
    """
    return _connection_manager.release_connection(name, conn)


def close_all_connections(name: str = None) -> None:
    """
    Close all connections for a specific pool or all pools.
    
    Args:
        name: Name of the connection pool to close, or None for all pools
        
    Raises:
        ConnectionError: If closing connections fails
    """
    return _connection_manager.close_all_connections(name)


def check_health() -> dict[str, Any]:
    """
    Check the health of all connection pools.
    
    Returns:
        A dictionary with health information for all pools
    """
    return _connection_manager.check_health()


def get_stats() -> dict[str, Any]:
    """
    Get connection statistics.
    
    Returns:
        A dictionary with connection statistics
    """
    return _connection_manager.get_stats()


def create_connection(name: str, conn_type: str, config: dict[str, Any], 
                     min_pool_size: int = 1, max_pool_size: int = 10) -> None:
    """
    Convenience function to create and initialize a connection in one step.
    
    Args:
        name: Unique identifier for this connection
        conn_type: String representation of database type ('postgresql', 'mongodb', etc.)
        config: Configuration parameters for the connection
        min_pool_size: Minimum number of connections in the pool
        max_pool_size: Maximum number of connections in the pool
        
    Raises:
        ConfigurationError: If the configuration is invalid
        DatabaseNotSupportedError: If the database type is not supported
        ConnectionError: If connection creation fails
        
    Example:
        create_connection(
            name='memory_store',
            conn_type='postgresql',
            config={
                'host': 'localhost',
                'port': 5432,
                'dbname': 'memory_db',
                'user': 'neuroca',
                'password': 'secure_password'
            }
        )
    """
    # Map string type to enum
    type_map = {
        'postgresql': DatabaseType.POSTGRESQL,
        'postgres': DatabaseType.POSTGRESQL,
        'mongodb': DatabaseType.MONGODB,
        'mongo': DatabaseType.MONGODB,
        'redis': DatabaseType.REDIS,
        'sqlite': DatabaseType.SQLITE,
        'mysql': DatabaseType.MYSQL,
        'custom': DatabaseType.CUSTOM
    }
    
    if conn_type.lower() not in type_map:
        raise DatabaseNotSupportedError(f"Unsupported database type: {conn_type}")
    
    db_type = type_map[conn_type.lower()]
    
    # Register and create pool
    register_connection(name, db_type, config)
    create_pool(name, min_pool_size, max_pool_size)
    
    logger.info(f"Created and initialized connection '{name}' of type {conn_type}")


# Convenience functions for specific database types
def get_postgres_connection(name: str, timeout: float = 30.0):
    """Get a PostgreSQL connection with context management."""
    return get_connection(name, timeout)


def get_mongo_connection(name: str, timeout: float = 30.0):
    """Get a MongoDB connection with context management."""
    return get_connection(name, timeout)


def get_redis_connection(name: str, timeout: float = 30.0):
    """Get a Redis connection with context management."""
    return get_connection(name, timeout)


def get_sqlite_connection(name: str, timeout: float = 30.0):
    """Get a SQLite connection with context management."""
    return get_connection(name, timeout)


def get_mysql_connection(name: str, timeout: float = 30.0):
    """Get a MySQL connection with context management."""
    return get_connection(name, timeout)


# Initialize from environment if configured
def _init_from_environment():
    """
    Initialize connections from environment variables.
    
    This function looks for environment variables in the format:
    NEUROCA_DB_{NAME}_{PARAM}
    
    For example:
    NEUROCA_DB_MEMORY_TYPE=postgresql
    NEUROCA_DB_MEMORY_HOST=localhost
    NEUROCA_DB_MEMORY_PORT=5432
    ...
    
    It will automatically create connections for all found configurations.
    """
    db_prefix = "NEUROCA_DB_"
    connections = {}
    
    # Find all environment variables with the prefix
    for key, value in os.environ.items():
        if key.startswith(db_prefix):
            parts = key[len(db_prefix):].split('_', 1)
            if len(parts) != 2:
                continue
                
            conn_name, param = parts
            conn_name = conn_name.lower()
            param = param.lower()
            
            if conn_name not in connections:
                connections[conn_name] = {}
            
            connections[conn_name][param] = value
    
    # Create connections for each found configuration
    for conn_name, params in connections.items():
        if 'type' not in params:
            logger.warning(f"Skipping connection '{conn_name}' from environment: missing 'type' parameter")
            continue
            
        try:
            conn_type = params.pop('type')
            
            # Convert string values to appropriate types
            for key, value in params.items():
                if value.isdigit():
                    params[key] = int(value)
                elif value.lower() in ('true', 'false'):
                    params[key] = value.lower() == 'true'
            
            create_connection(conn_name, conn_type, params)
            logger.info(f"Created connection '{conn_name}' from environment variables")
            
        except Exception as e:
            logger.error(f"Failed to create connection '{conn_name}' from environment: {str(e)}")


# Initialize connections from environment variables if available
try:
    _init_from_environment()
except Exception as e:
    logger.warning(f"Failed to initialize connections from environment: {str(e)}")