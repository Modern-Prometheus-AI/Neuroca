"""
Storage Backend Factory Facade

This module serves as a facade for the factory package, reexporting the classes
from the factory subfolder. This maintains backward compatibility while
following the Apex standard of one class per file.
"""

from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.memory_tier import MemoryTier
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory

__all__ = [
    "BackendType",
    "MemoryTier",
    "StorageBackendFactory",
]
