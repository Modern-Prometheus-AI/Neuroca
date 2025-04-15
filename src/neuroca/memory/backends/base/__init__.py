"""
Base Storage Backend Package

This package provides the base classes and components for all storage backend
implementations, including the BaseStorageBackend class which implements the
StorageBackendInterface.

It serves as the foundation for all specific storage backend implementations
and provides common functionality that backends can inherit and extend.
"""

from neuroca.memory.backends.base.core import BaseStorageBackend
from neuroca.memory.backends.base.stats import BackendStats
from neuroca.memory.backends.base.operations import CoreOperations
from neuroca.memory.backends.base.batch import BatchOperations

# Re-export key classes
__all__ = [
    'BaseStorageBackend',
    'BackendStats',
    'CoreOperations',
    'BatchOperations'
]
