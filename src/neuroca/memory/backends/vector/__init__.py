"""
Vector Backend Package

This package contains the modular components for the Vector storage backend
implementation that provides similarity-based memory retrieval and search.

All components are re-exported from the package root for easier access.
"""

from neuroca.memory.backends.vector.core import VectorBackend
from neuroca.memory.backends.vector.components import (
    VectorEntry,
    VectorIndex,
    VectorStorage,
    VectorSearch,
    VectorCRUD,
    VectorStats
)

# Export classes
__all__ = [
    'VectorBackend',
    'VectorEntry',
    'VectorIndex',
    'VectorStorage',
    'VectorSearch',
    'VectorCRUD',
    'VectorStats'
]
