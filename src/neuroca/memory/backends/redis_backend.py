"""
Redis Storage Backend for Memory System (Import Redirection)

This module redirects imports of RedisBackend to the new modular implementation
in the redis package. This maintains backward compatibility with existing code
that imports RedisBackend from this module.
"""

# Re-export RedisBackend from the new location
from neuroca.memory.backends.redis.core import RedisBackend

# Export only the RedisBackend class
__all__ = ['RedisBackend']
