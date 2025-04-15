"""
SQLite Storage Backend Components

This package contains the modular components of the SQLite storage backend:
- connection.py: Database connection management
- schema.py: Database schema definitions
- crud.py: CRUD operations for memory items
- search.py: Search functionality
- batch.py: Batch operations
- stats.py: Statistics and metrics
"""

from neuroca.memory.backends.sqlite.components.connection import SQLiteConnection
from neuroca.memory.backends.sqlite.components.schema import SQLiteSchema
from neuroca.memory.backends.sqlite.components.crud import SQLiteCRUD
from neuroca.memory.backends.sqlite.components.search import SQLiteSearch
from neuroca.memory.backends.sqlite.components.batch import SQLiteBatch
from neuroca.memory.backends.sqlite.components.stats import SQLiteStats

__all__ = [
    'SQLiteConnection',
    'SQLiteSchema',
    'SQLiteCRUD',
    'SQLiteSearch',
    'SQLiteBatch',
    'SQLiteStats'
]
