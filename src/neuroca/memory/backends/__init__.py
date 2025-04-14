"""
Storage Backends Package

This package contains the implementations of different storage backends for the
Neuroca memory system. Storage backends are responsible for the low-level
persistence of memory items, handling the direct interaction with specific
database technologies.

Available backends:
- InMemoryBackend: Simple in-memory implementation for development and testing
- RedisBackend: Redis-based implementation for STM and MTM
- SQLBackend: SQL database implementation for LTM structured data
- VectorBackend: Vector database implementation for similarity search

The StorageBackendFactory should be used to create instances of the appropriate
backend based on the configuration.
"""

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.in_memory_backend import InMemoryBackend
from neuroca.memory.backends.factory import (
    BackendType,
    MemoryTier,
    StorageBackendFactory,
)

__all__ = [
    "BaseStorageBackend",
    "InMemoryBackend",
    "BackendType",
    "MemoryTier",
    "StorageBackendFactory",
]
