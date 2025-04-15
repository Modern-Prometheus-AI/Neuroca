"""
In-Memory Storage Backend Components

This package contains the modular components of the in-memory storage backend:
- storage.py: Core storage functionality and data structures
- crud.py: CRUD operations for memory items
- search.py: Search and query functionality
- batch.py: Batch operations for improved performance
- stats.py: Statistics and metrics collection
"""

from neuroca.memory.backends.in_memory.components.storage import InMemoryStorage
from neuroca.memory.backends.in_memory.components.crud import InMemoryCRUD
from neuroca.memory.backends.in_memory.components.search import InMemorySearch
from neuroca.memory.backends.in_memory.components.batch import InMemoryBatch
from neuroca.memory.backends.in_memory.components.stats import InMemoryStats

__all__ = [
    'InMemoryStorage',
    'InMemoryCRUD',
    'InMemorySearch',
    'InMemoryBatch',
    'InMemoryStats'
]
