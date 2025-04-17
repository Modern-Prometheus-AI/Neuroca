"""
Redis Connection Component

This module provides the RedisConnection class for managing Redis client connections.
"""

import asyncio
import logging
from typing import Optional

import redis
from asyncio import Redis

from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError

logger = logging.getLogger(__name__)


class RedisConnection:
    """
    Manages connections to Redis for the Redis backend.
    
    This class handles creating, maintaining, and closing the Redis client connection.
    It also provides methods for executing Redis commands safely.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db: int = 0,
        password: Optional[str] = None,
        connection_timeout: float = 30.0,
        **kwargs
    ):
        """
        Initialize the Redis connection component.
        
        Args:
            redis_url: Redis connection URL
            db: Redis database number
            password: Redis password
            connection_timeout: Connection timeout in seconds
            **kwargs: Additional connection options for Redis
        """
        self.redis_url = redis_url
        self.db = db
        self.password = password
        self.connection_timeout = connection_timeout
        self.connection_kwargs = kwargs
        self._redis: Optional[Redis] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """
        Initialize the Redis connection.
        
        This establishes a connection to the Redis server and performs a ping
        to verify connectivity.
        
        Raises:
            StorageInitializationError: If connection fails
        """
        try:
            # Connect to Redis
            self._redis = await redis.from_url(
                self.redis_url,
                db=self.db,
                password=self.password,
                decode_responses=True,
                **self.connection_kwargs
            )
            
            # Ping to verify connection
            await self._redis.ping()
            
            logger.info(f"Connected to Redis at {self.redis_url}, db={self.db}")
        except Exception as e:
            error_msg = f"Failed to connect to Redis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def close(self) -> None:
        """
        Close the Redis connection.
        
        Raises:
            StorageBackendError: If close operation fails
        """
        try:
            if self._redis:
                await self._redis.close()
                self._redis = None
                logger.info("Redis connection closed")
        except Exception as e:
            error_msg = f"Failed to close Redis connection: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get_client(self) -> Redis:
        """
        Get the Redis client instance.
        
        Returns:
            Redis: The Redis client
            
        Raises:
            StorageBackendError: If Redis is not initialized
        """
        if self._redis is None:
            raise StorageBackendError("Redis client not initialized")
        return self._redis
    
    async def execute(self, command: str, *args, **kwargs) -> any:
        """
        Execute a Redis command.
        
        Args:
            command: Redis command name
            *args: Command arguments
            **kwargs: Command keyword arguments
            
        Returns:
            The result of the Redis command
            
        Raises:
            StorageBackendError: If Redis is not initialized or execution fails
        """
        client = await self.get_client()
        try:
            method = getattr(client, command)
            return await method(*args, **kwargs)
        except Exception as e:
            error_msg = f"Redis command '{command}' failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def pipeline(self) -> "RedisPipeline":
        """
        Create a pipeline for batch operations.
        
        Returns:
            RedisPipeline: A pipeline wrapper
            
        Raises:
            StorageBackendError: If Redis is not initialized
        """
        client = await self.get_client()
        try:
            pipeline = await client.pipeline()
            return RedisPipeline(pipeline)
        except Exception as e:
            error_msg = f"Failed to create Redis pipeline: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    def is_connected(self) -> bool:
        """Check if Redis client is connected."""
        return self._redis is not None


class RedisPipeline:
    """
    Wrapper for Redis pipeline to provide async context manager support.
    """
    
    def __init__(self, pipeline):
        """Initialize with a Redis pipeline."""
        self.pipeline = pipeline
    
    async def __aenter__(self):
        """Context manager entry."""
        return self.pipeline
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            # Execute pipeline if no exception
            await self.pipeline.execute()
        # Close pipeline
        await self.pipeline.close()
