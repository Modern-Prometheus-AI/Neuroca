"""
Base Storage Backend (Import Redirection)

This module redirects imports of BaseStorageBackend to the new modular
implementation in the base package. This maintains backward compatibility
with existing code that imports BaseStorageBackend from this module.
"""

# Re-export BaseStorageBackend from the new location
from neuroca.memory.backends.base.core import BaseStorageBackend

# Export only the BaseStorageBackend class
__all__ = ['BaseStorageBackend']

