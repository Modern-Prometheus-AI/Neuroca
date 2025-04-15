"""
In-Memory Storage Backend for Memory System

This package provides an in-memory implementation of the storage backend interface.
It stores all data in memory using Python dictionaries and is useful for 
development, testing, and small-scale deployments.

This implementation is modularized following AMOS guidelines:
- components/storage.py: Core storage functionality
- components/crud.py: CRUD operations
- components/batch.py: Batch operations
- components/search.py: Search functionality
- components/stats.py: Statistics and metrics

core.py integrates all components to provide the InMemoryBackend class.
"""

from neuroca.memory.backends.in_memory.core import InMemoryBackend

__all__ = ['InMemoryBackend']
