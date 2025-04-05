"""
Redis Connection Module for NeuroCognitive Architecture

This module provides a robust Redis connection management system for the NeuroCognitive Architecture.
It handles connection pooling, automatic reconnection, serialization/deserialization,
and provides a clean interface for Redis operations with proper error handling.

Usage:
    from neuroca.db.connections.redis import RedisConnection, get_redis_connection

    # Using the singleton pattern
    redis = get_redis_connection()
    redis.set('key', 'value')
    value = redis.get('key')

    # Or creating a specific connection
    redis = RedisConnection(host='localhost', port=6379, db=0)
    with redis.pipeline() as pipe:
        pipe.set('key1', 'value1')
        pipe.set('key2', 'value2')
        pipe.execute()
"""

import json
import logging
import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from redis.client import Pipeline, Redis
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from neuroca.config.settings import get_settings

# Configure logger
logger = logging.getLogger(__name__)

# Type variables for better type hinting
T = TypeVar('T')
RedisValue = Union[str, bytes, int, float, None]
RedisMappingType = dict[str, Any]

# Default connection settings
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0
DEFAULT_REDIS_PASSWORD = None
DEFAULT_REDIS_SOCKET_TIMEOUT = 5.0
DEFAULT_REDIS_SOCKET_CONNECT_TIMEOUT = 5.0
DEFAULT_REDIS_RETRY_ON_TIMEOUT = True
DEFAULT_REDIS_MAX_CONNECTIONS = 10
DEFAULT_REDIS_HEALTH_CHECK_INTERVAL = 30
DEFAULT_REDIS_RETRY_COUNT = 3
DEFAULT_REDIS_RETRY_DELAY = 0.5


def retry_on_connection_error(max_retries: int = 3, delay: float = 0.5) -> Callable:
    """
    Decorator to retry Redis operations on connection errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Redis connection error: {str(e)}. "
                            f"Retrying {attempt+1}/{max_retries} in {delay} seconds..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Redis operation failed after {max_retries} retries: {str(e)}")
                        raise
            # This should never happen, but keeps mypy happy
            assert last_exception is not None
            raise last_exception
        return wrapper
    return decorator


class RedisConnection:
    """
    Redis connection manager with connection pooling, automatic reconnection,
    and serialization/deserialization support.
    
    This class provides a robust interface to Redis operations with proper error handling,
    connection management, and helper methods for common Redis operations.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        socket_timeout: Optional[float] = None,
        socket_connect_timeout: Optional[float] = None,
        retry_on_timeout: bool = True,
        max_connections: int = DEFAULT_REDIS_MAX_CONNECTIONS,
        health_check_interval: int = DEFAULT_REDIS_HEALTH_CHECK_INTERVAL,
        retry_count: int = DEFAULT_REDIS_RETRY_COUNT,
        retry_delay: float = DEFAULT_REDIS_RETRY_DELAY,
        **kwargs: Any
    ) -> None:
        """
        Initialize a Redis connection with the specified parameters.
        
        Args:
            host: Redis server hostname
            port: Redis server port
            db: Redis database number
            password: Redis password
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            max_connections: Maximum number of connections in the pool
            health_check_interval: Health check interval in seconds
            retry_count: Number of retries for operations
            retry_delay: Delay between retries in seconds
            **kwargs: Additional arguments to pass to Redis
        """
        # Load settings from environment or config
        settings = get_settings()
        
        # Set connection parameters with fallbacks
        self.host = host or os.environ.get("REDIS_HOST", settings.get("REDIS_HOST", DEFAULT_REDIS_HOST))
        self.port = port or int(os.environ.get("REDIS_PORT", settings.get("REDIS_PORT", DEFAULT_REDIS_PORT)))
        self.db = db if db is not None else int(os.environ.get("REDIS_DB", settings.get("REDIS_DB", DEFAULT_REDIS_DB)))
        self.password = password or os.environ.get("REDIS_PASSWORD", settings.get("REDIS_PASSWORD", DEFAULT_REDIS_PASSWORD))
        self.socket_timeout = socket_timeout or float(os.environ.get(
            "REDIS_SOCKET_TIMEOUT", settings.get("REDIS_SOCKET_TIMEOUT", DEFAULT_REDIS_SOCKET_TIMEOUT)
        ))
        self.socket_connect_timeout = socket_connect_timeout or float(os.environ.get(
            "REDIS_SOCKET_CONNECT_TIMEOUT", 
            settings.get("REDIS_SOCKET_CONNECT_TIMEOUT", DEFAULT_REDIS_SOCKET_CONNECT_TIMEOUT)
        ))
        self.retry_on_timeout = retry_on_timeout
        self.max_connections = max_connections
        self.health_check_interval = health_check_interval
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.additional_kwargs = kwargs
        
        # Initialize connection pool and client
        self._pool = None
        self._client = None
        self._initialize_connection()
        
        logger.debug(
            f"Initialized Redis connection to {self.host}:{self.port}/db{self.db} "
            f"with max_connections={self.max_connections}"
        )

    def _initialize_connection(self) -> None:
        """Initialize the Redis connection pool and client."""
        try:
            self._pool = ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                max_connections=self.max_connections,
                health_check_interval=self.health_check_interval,
                **self.additional_kwargs
            )
            
            self._client = Redis(connection_pool=self._pool)
            # Test connection
            self._client.ping()
            logger.info(f"Successfully connected to Redis at {self.host}:{self.port}/db{self.db}")
        except RedisError as e:
            logger.error(f"Failed to initialize Redis connection: {str(e)}")
            # We don't raise here to allow for lazy connection initialization
            # The error will be raised when an actual operation is attempted

    @property
    def client(self) -> Redis:
        """
        Get the Redis client instance.
        
        Returns:
            Redis client instance
            
        Raises:
            RedisError: If the client is not initialized
        """
        if self._client is None:
            logger.warning("Redis client not initialized, attempting to initialize now")
            self._initialize_connection()
            if self._client is None:
                raise RedisError("Redis client could not be initialized")
        return self._client

    @contextmanager
    def pipeline(self, transaction: bool = True) -> Pipeline:
        """
        Get a Redis pipeline for executing multiple commands in a batch.
        
        Args:
            transaction: Whether to execute the commands as a transaction
            
        Yields:
            Redis pipeline object
            
        Example:
            ```
            with redis_conn.pipeline() as pipe:
                pipe.set('key1', 'value1')
                pipe.set('key2', 'value2')
                pipe.execute()
            ```
        """
        pipe = self.client.pipeline(transaction=transaction)
        try:
            yield pipe
        finally:
            pipe.reset()

    def close(self) -> None:
        """Close the Redis connection pool."""
        if self._pool:
            logger.debug("Closing Redis connection pool")
            self._pool.disconnect()
            self._pool = None
            self._client = None

    def __enter__(self) -> 'RedisConnection':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with proper cleanup."""
        self.close()

    # Serialization and deserialization helpers
    @staticmethod
    def serialize(value: Any) -> str:
        """
        Serialize a Python object to a string for Redis storage.
        
        Args:
            value: Python object to serialize
            
        Returns:
            JSON string representation
        """
        if isinstance(value, (str, int, float, bool, type(None))):
            return json.dumps(value)
        return json.dumps(value)

    @staticmethod
    def deserialize(value: Optional[bytes]) -> Any:
        """
        Deserialize a Redis value to a Python object.
        
        Args:
            value: Bytes from Redis to deserialize
            
        Returns:
            Deserialized Python object or None if value is None
        """
        if value is None:
            return None
        try:
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If not JSON, return as is (decoded if possible)
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value

    # Core Redis operations with retry logic
    @retry_on_connection_error()
    def get(self, key: str, deserialize: bool = True) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            deserialize: Whether to deserialize the value
            
        Returns:
            Deserialized value or None if key doesn't exist
        """
        value = self.client.get(key)
        return self.deserialize(value) if deserialize and value is not None else value

    @retry_on_connection_error()
    def set(
        self, 
        key: str, 
        value: Any, 
        ex: Optional[int] = None, 
        px: Optional[int] = None,
        nx: bool = False, 
        xx: bool = False,
        serialize: bool = True
    ) -> bool:
        """
        Set a value in Redis.
        
        Args:
            key: Redis key
            value: Value to store
            ex: Expiry time in seconds
            px: Expiry time in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            serialize: Whether to serialize the value
            
        Returns:
            True if successful, False otherwise
        """
        serialized_value = self.serialize(value) if serialize else value
        return bool(self.client.set(key, serialized_value, ex=ex, px=px, nx=nx, xx=xx))

    @retry_on_connection_error()
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0
        return self.client.delete(*keys)

    @retry_on_connection_error()
    def exists(self, *keys: str) -> int:
        """
        Check if one or more keys exist in Redis.
        
        Args:
            *keys: Keys to check
            
        Returns:
            Number of keys that exist
        """
        if not keys:
            return 0
        return self.client.exists(*keys)

    @retry_on_connection_error()
    def expire(self, key: str, time_seconds: int) -> bool:
        """
        Set a key's time to live in seconds.
        
        Args:
            key: Redis key
            time_seconds: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        return bool(self.client.expire(key, time_seconds))

    @retry_on_connection_error()
    def ttl(self, key: str) -> int:
        """
        Get the time to live for a key in seconds.
        
        Args:
            key: Redis key
            
        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        return self.client.ttl(key)

    # Hash operations
    @retry_on_connection_error()
    def hset(self, name: str, key: str, value: Any, serialize: bool = True) -> int:
        """
        Set a hash field to a value.
        
        Args:
            name: Hash name
            key: Field name
            value: Field value
            serialize: Whether to serialize the value
            
        Returns:
            1 if field is new, 0 if field existed
        """
        serialized_value = self.serialize(value) if serialize else value
        return self.client.hset(name, key, serialized_value)

    @retry_on_connection_error()
    def hget(self, name: str, key: str, deserialize: bool = True) -> Any:
        """
        Get the value of a hash field.
        
        Args:
            name: Hash name
            key: Field name
            deserialize: Whether to deserialize the value
            
        Returns:
            Field value or None if field or hash doesn't exist
        """
        value = self.client.hget(name, key)
        return self.deserialize(value) if deserialize and value is not None else value

    @retry_on_connection_error()
    def hmset(self, name: str, mapping: dict[str, Any], serialize: bool = True) -> bool:
        """
        Set multiple hash fields to multiple values.
        
        Args:
            name: Hash name
            mapping: Dict of field/value pairs
            serialize: Whether to serialize the values
            
        Returns:
            True if successful
        """
        if serialize:
            serialized_mapping = {k: self.serialize(v) for k, v in mapping.items()}
        else:
            serialized_mapping = mapping
        return bool(self.client.hset(name, mapping=serialized_mapping))

    @retry_on_connection_error()
    def hmget(self, name: str, keys: list[str], deserialize: bool = True) -> list[Any]:
        """
        Get the values of all given hash fields.
        
        Args:
            name: Hash name
            keys: List of field names
            deserialize: Whether to deserialize the values
            
        Returns:
            List of values (None for non-existent fields)
        """
        values = self.client.hmget(name, keys)
        if deserialize:
            return [self.deserialize(v) for v in values]
        return values

    @retry_on_connection_error()
    def hgetall(self, name: str, deserialize: bool = True) -> dict[str, Any]:
        """
        Get all fields and values in a hash.
        
        Args:
            name: Hash name
            deserialize: Whether to deserialize the values
            
        Returns:
            Dict of field/value pairs
        """
        result = self.client.hgetall(name)
        if not result:
            return {}
            
        if deserialize:
            return {k.decode('utf-8') if isinstance(k, bytes) else k: 
                    self.deserialize(v) for k, v in result.items()}
        return {k.decode('utf-8') if isinstance(k, bytes) else k: 
                v for k, v in result.items()}

    @retry_on_connection_error()
    def hdel(self, name: str, *keys: str) -> int:
        """
        Delete one or more hash fields.
        
        Args:
            name: Hash name
            *keys: Field names to delete
            
        Returns:
            Number of fields deleted
        """
        if not keys:
            return 0
        return self.client.hdel(name, *keys)

    # List operations
    @retry_on_connection_error()
    def lpush(self, name: str, *values: Any, serialize: bool = True) -> int:
        """
        Prepend values to a list.
        
        Args:
            name: List name
            *values: Values to prepend
            serialize: Whether to serialize the values
            
        Returns:
            Length of list after operation
        """
        if not values:
            return 0
            
        serialized_values = [self.serialize(v) for v in values] if serialize else values
        return self.client.lpush(name, *serialized_values)

    @retry_on_connection_error()
    def rpush(self, name: str, *values: Any, serialize: bool = True) -> int:
        """
        Append values to a list.
        
        Args:
            name: List name
            *values: Values to append
            serialize: Whether to serialize the values
            
        Returns:
            Length of list after operation
        """
        if not values:
            return 0
            
        serialized_values = [self.serialize(v) for v in values] if serialize else values
        return self.client.rpush(name, *serialized_values)

    @retry_on_connection_error()
    def lpop(self, name: str, deserialize: bool = True) -> Any:
        """
        Remove and get the first element in a list.
        
        Args:
            name: List name
            deserialize: Whether to deserialize the value
            
        Returns:
            First element or None if list is empty
        """
        value = self.client.lpop(name)
        return self.deserialize(value) if deserialize and value is not None else value

    @retry_on_connection_error()
    def rpop(self, name: str, deserialize: bool = True) -> Any:
        """
        Remove and get the last element in a list.
        
        Args:
            name: List name
            deserialize: Whether to deserialize the value
            
        Returns:
            Last element or None if list is empty
        """
        value = self.client.rpop(name)
        return self.deserialize(value) if deserialize and value is not None else value

    @retry_on_connection_error()
    def lrange(self, name: str, start: int, end: int, deserialize: bool = True) -> list[Any]:
        """
        Get a range of elements from a list.
        
        Args:
            name: List name
            start: Start index
            end: End index
            deserialize: Whether to deserialize the values
            
        Returns:
            List of elements in the specified range
        """
        values = self.client.lrange(name, start, end)
        if deserialize:
            return [self.deserialize(v) for v in values]
        return values

    # Set operations
    @retry_on_connection_error()
    def sadd(self, name: str, *values: Any, serialize: bool = True) -> int:
        """
        Add members to a set.
        
        Args:
            name: Set name
            *values: Values to add
            serialize: Whether to serialize the values
            
        Returns:
            Number of members added (excluding existing members)
        """
        if not values:
            return 0
            
        serialized_values = [self.serialize(v) for v in values] if serialize else values
        return self.client.sadd(name, *serialized_values)

    @retry_on_connection_error()
    def smembers(self, name: str, deserialize: bool = True) -> set:
        """
        Get all members of a set.
        
        Args:
            name: Set name
            deserialize: Whether to deserialize the values
            
        Returns:
            Set of all members
        """
        values = self.client.smembers(name)
        if deserialize:
            return {self.deserialize(v) for v in values}
        return values

    @retry_on_connection_error()
    def srem(self, name: str, *values: Any, serialize: bool = True) -> int:
        """
        Remove members from a set.
        
        Args:
            name: Set name
            *values: Values to remove
            serialize: Whether to serialize the values
            
        Returns:
            Number of members removed
        """
        if not values:
            return 0
            
        serialized_values = [self.serialize(v) for v in values] if serialize else values
        return self.client.srem(name, *serialized_values)

    # Sorted set operations
    @retry_on_connection_error()
    def zadd(self, name: str, mapping: dict[Any, float], serialize_keys: bool = True) -> int:
        """
        Add members to a sorted set, or update their scores.
        
        Args:
            name: Sorted set name
            mapping: Dict mapping members to scores
            serialize_keys: Whether to serialize the members
            
        Returns:
            Number of new members added
        """
        if not mapping:
            return 0
            
        if serialize_keys:
            serialized_mapping = {self.serialize(k): v for k, v in mapping.items()}
        else:
            serialized_mapping = mapping
        return self.client.zadd(name, serialized_mapping)

    @retry_on_connection_error()
    def zrange(
        self, 
        name: str, 
        start: int, 
        end: int, 
        desc: bool = False, 
        withscores: bool = False,
        deserialize: bool = True
    ) -> Union[list[Any], list[tuple[Any, float]]]:
        """
        Get a range of members from a sorted set.
        
        Args:
            name: Sorted set name
            start: Start index
            end: End index
            desc: Whether to return elements in descending order
            withscores: Whether to include scores
            deserialize: Whether to deserialize the members
            
        Returns:
            List of members or list of (member, score) tuples if withscores=True
        """
        values = self.client.zrange(name, start, end, desc=desc, withscores=withscores)
        
        if not values:
            return []
            
        if withscores:
            if deserialize:
                return [(self.deserialize(v[0]), v[1]) for v in values]
            return values
        else:
            if deserialize:
                return [self.deserialize(v) for v in values]
            return values

    @retry_on_connection_error()
    def zrem(self, name: str, *values: Any, serialize: bool = True) -> int:
        """
        Remove members from a sorted set.
        
        Args:
            name: Sorted set name
            *values: Members to remove
            serialize: Whether to serialize the members
            
        Returns:
            Number of members removed
        """
        if not values:
            return 0
            
        serialized_values = [self.serialize(v) for v in values] if serialize else values
        return self.client.zrem(name, *serialized_values)

    # Pub/Sub operations
    def publish(self, channel: str, message: Any, serialize: bool = True) -> int:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            serialize: Whether to serialize the message
            
        Returns:
            Number of clients that received the message
        """
        serialized_message = self.serialize(message) if serialize else message
        return self.client.publish(channel, serialized_message)

    # Health check
    @retry_on_connection_error(max_retries=1, delay=0.1)
    def ping(self) -> bool:
        """
        Check if Redis server is responding.
        
        Returns:
            True if server is responding, False otherwise
        """
        try:
            return self.client.ping()
        except RedisError:
            return False

    def health_check(self) -> dict[str, Any]:
        """
        Perform a comprehensive health check on the Redis connection.
        
        Returns:
            Dict with health check results
        """
        health_data = {
            "status": "unknown",
            "ping": False,
            "connection_info": f"{self.host}:{self.port}/db{self.db}",
            "errors": []
        }
        
        try:
            # Basic ping check
            health_data["ping"] = self.ping()
            
            # Check info
            info = self.client.info()
            health_data["redis_version"] = info.get("redis_version")
            health_data["used_memory_human"] = info.get("used_memory_human")
            health_data["connected_clients"] = info.get("connected_clients")
            
            # Check if we can set and get a value
            test_key = "_health_check_test_key"
            test_value = f"health_check_{time.time()}"
            set_result = self.set(test_key, test_value, ex=10)
            get_result = self.get(test_key)
            health_data["set_get_test"] = set_result and get_result == test_value
            
            # Clean up
            self.delete(test_key)
            
            # Overall status
            if health_data["ping"] and health_data.get("set_get_test", False):
                health_data["status"] = "healthy"
            else:
                health_data["status"] = "unhealthy"
                
        except RedisError as e:
            health_data["status"] = "unhealthy"
            health_data["errors"].append(str(e))
            logger.error(f"Redis health check failed: {str(e)}")
        
        return health_data


# Singleton instance for global use
_redis_connection: Optional[RedisConnection] = None


def get_redis_connection() -> RedisConnection:
    """
    Get or create a singleton Redis connection.
    
    This function ensures that only one Redis connection is created
    throughout the application, following the singleton pattern.
    
    Returns:
        Redis connection instance
        
    Example:
        ```
        redis = get_redis_connection()
        redis.set('key', 'value')
        ```
    """
    global _redis_connection
    if _redis_connection is None:
        _redis_connection = RedisConnection()
    return _redis_connection


def close_redis_connection() -> None:
    """
    Close the singleton Redis connection.
    
    This function should be called during application shutdown
    to properly clean up resources.
    """
    global _redis_connection
    if _redis_connection is not None:
        _redis_connection.close()
        _redis_connection = None
        logger.info("Closed global Redis connection")