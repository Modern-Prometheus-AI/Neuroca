"""
Backend Type Enumeration

This module defines the enumeration of supported storage backend types.
"""

from enum import Enum


class BackendType(str, Enum):
    """Supported storage backend types."""
    
    MEMORY = "memory"  # In-memory storage (non-persistent)
    REDIS = "redis"    # Redis-based storage
    SQL = "sql"        # SQL database storage
    VECTOR = "vector"  # Vector database storage
