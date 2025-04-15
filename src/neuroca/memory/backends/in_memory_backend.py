"""
In-Memory Storage Backend for Memory System (Import Redirection)

This module redirects imports of InMemoryBackend to the new modular implementation
in the in_memory package. This maintains backward compatibility with existing code
that imports InMemoryBackend from this module.
"""

# Re-export InMemoryBackend from the new location
from neuroca.memory.backends.in_memory.core import InMemoryBackend

# Export only the InMemoryBackend class
__all__ = ['InMemoryBackend']
