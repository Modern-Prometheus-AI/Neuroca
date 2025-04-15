"""
Redis Storage Backend Components

This package contains the modular components of the Redis storage backend:
- connection.py: Redis client connection management
- crud.py: CRUD operations for memory items
- indexing.py: Indexing operations for search and filtering
- search.py: Search functionality with filtering
- batch.py: Batch operations for improved performance
- stats.py: Statistics and metrics collection
- utils.py: Utility functions for Redis operations
"""

from neuroca.memory.backends.redis.components.connection import RedisConnection
from neuroca.memory.backends.redis.components.crud import RedisCRUD
from neuroca.memory.backends.redis.components.indexing import RedisIndexing
from neuroca.memory.backends.redis.components.search import RedisSearch
from neuroca.memory.backends.redis.components.batch import RedisBatch
from neuroca.memory.backends.redis.components.stats import RedisStats
from neuroca.memory.backends.redis.components.utils import RedisUtils

__all__ = [
    'RedisConnection',
    'RedisCRUD',
    'RedisIndexing',
    'RedisSearch',
    'RedisBatch',
    'RedisStats',
    'RedisUtils'
]
