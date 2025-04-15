"""
Vector Storage Backend for Memory System (Import Redirection)

This module redirects imports of VectorBackend to the new modular implementation
in the vector package. This maintains backward compatibility with existing code
that imports VectorBackend from this module.
"""

# Re-export VectorBackend from the new location
from neuroca.memory.backends.vector.core import VectorBackend

# Export only the VectorBackend class
__all__ = ['VectorBackend']
