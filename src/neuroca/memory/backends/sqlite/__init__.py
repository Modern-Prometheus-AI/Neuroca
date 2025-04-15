"""
SQLite Storage Backend for Memory System

This package provides a SQLite implementation of the storage backend interface.
It enables persistent storage of memory items in a SQLite database with full
CRUD operations, search capabilities, and metadata handling.

The implementation is modularized following AMOS guidelines:
- components/connection.py: Database connection management
- components/schema.py: Database schema definitions
- components/crud.py: CRUD operations for memory items
- components/search.py: Search functionality
- components/batch.py: Batch operations
- components/stats.py: Statistics and metrics

core.py integrates all components to provide the SQLiteBackend class.
"""

from neuroca.memory.backends.sqlite.core import SQLiteBackend

__all__ = ['SQLiteBackend']
