"""
Redis Storage Backend for Memory System

This package provides a Redis implementation of the storage backend interface.
It enables persistent storage of memory items in Redis with full CRUD operations,
search capabilities, and metadata handling.

This implementation is modularized following AMOS guidelines:
- components/connection.py: Redis client management
- components/crud.py: CRUD operations
- components/indexing.py: Indexing for content and metadata
- components/search.py: Search functionality
- components/batch.py: Batch operations
- components/stats.py: Statistics and metrics
- components/utils.py: Utility functions

core.py integrates all components to provide the RedisBackend class.
"""

from neuroca.memory.backends.redis.core import RedisBackend

__all__ = ['RedisBackend']
