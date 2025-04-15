"""
Vector Backend Components Package

This package contains the modular components for the Vector storage backend.
"""

# Import components for easier access
from neuroca.memory.backends.vector.components.models import VectorEntry
from neuroca.memory.backends.vector.components.index import VectorIndex
from neuroca.memory.backends.vector.components.storage import VectorStorage
from neuroca.memory.backends.vector.components.search import VectorSearch
from neuroca.memory.backends.vector.components.crud import VectorCRUD
from neuroca.memory.backends.vector.components.stats import VectorStats

# Export components
__all__ = [
    'VectorEntry',
    'VectorIndex',
    'VectorStorage',
    'VectorSearch',
    'VectorCRUD',
    'VectorStats'
]
