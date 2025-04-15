"""
SQL Storage Backend for Memory System (Import Redirection)

This module redirects imports of SQLBackend to the new modular implementation
in the sql package. This maintains backward compatibility with existing code
that imports SQLBackend from this module.
"""

# Re-export SQLBackend from the new location
from neuroca.memory.backends.sql.core import SQLBackend

# Export only the SQLBackend class
__all__ = ['SQLBackend']
