"""
SQLite Storage Backend for Memory System (Import Redirection)

This module redirects imports of SQLiteBackend to the new modular implementation
in the sqlite package. This maintains backward compatibility with existing code
that imports SQLiteBackend from this module.
"""

# Re-export SQLiteBackend from the new location
from neuroca.memory.backends.sqlite.core import SQLiteBackend

# Export only the SQLiteBackend class
__all__ = ['SQLiteBackend']
