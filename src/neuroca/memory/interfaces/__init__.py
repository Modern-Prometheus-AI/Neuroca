"""
Memory System Interfaces

This package defines the core interfaces for the Neuroca memory system architecture.
These interfaces establish the contract between the different layers of the memory system:

1. Storage Backends: Low-level database interfaces (Redis, SQL, Vector)
2. Memory Tiers: Logical tier-specific behaviors (STM, MTM, LTM)
3. Memory Manager: Central orchestration layer for the memory system

By defining these interfaces clearly, we enable:
- Clean separation of concerns
- Pluggable implementations
- Testable components
- Clear contract between layers
"""

from neuroca.memory.interfaces.storage_backend import StorageBackendInterface
from neuroca.memory.interfaces.memory_tier import MemoryTierInterface
from neuroca.memory.interfaces.memory_manager import MemoryManagerInterface

__all__ = [
    "StorageBackendInterface",
    "MemoryTierInterface",
    "MemoryManagerInterface",
]
