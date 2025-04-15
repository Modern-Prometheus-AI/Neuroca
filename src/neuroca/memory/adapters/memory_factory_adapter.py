"""
Memory Factory Adapter

This module provides an adapter for the legacy memory factory that creates
instances of the new memory system components. It delegates to the new
Memory Manager and storage backend factory.

This adapter is provided for backward compatibility during migration
and will be removed in a future version.
"""

import asyncio
import logging
import warnings
from typing import Any, Dict, Optional, Union

from neuroca.memory.backends import BackendType
from neuroca.memory.backends.factory import StorageBackendFactory
from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.adapters.episodic_memory_adapter import EpisodicMemoryAdapter
from neuroca.memory.adapters.semantic_memory_adapter import SemanticMemoryAdapter


logger = logging.getLogger(__name__)


class MemoryFactoryAdapter:
    """
    Adapter for the legacy memory factory.
    
    This adapter implements the legacy factory interface but creates
    instances of the new memory system components.
    
    DEPRECATED: Use MemoryManager directly instead.
    """
    
    def __init__(self):
        """
        Initialize the memory factory adapter.
        """
        warnings.warn(
            "MemoryFactoryAdapter is deprecated. Use MemoryManager directly.",
            DeprecationWarning,
            stacklevel=2
        )
        self._memory_manager = None
        
    async def create_memory_manager(
        self,
        backend_type: str = "in_memory",
        backend_config: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> MemoryManager:
        """
        Create a memory manager instance.
        
        Args:
            backend_type: Type of backend to use
            backend_config: Backend configuration
            config: Memory manager configuration
            
        Returns:
            Memory manager instance
            
        DEPRECATED: Use MemoryManager constructor directly.
        """
        warnings.warn(
            "create_memory_manager() is deprecated. Use MemoryManager constructor directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Map legacy backend types to new BackendType enum
        if backend_type == "in_memory":
            backend_type_enum = BackendType.IN_MEMORY
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
        
        # Create memory manager
        self._memory_manager = MemoryManager(
            backend_type=backend_type_enum,
            backend_config=backend_config or {},
            config=config or {},
        )
        
        # Initialize the memory manager
        await self._memory_manager.initialize()
        
        return self._memory_manager
    
    async def create_episodic_memory(self) -> EpisodicMemoryAdapter:
        """
        Create an episodic memory instance.
        
        Returns:
            EpisodicMemoryAdapter instance
            
        Raises:
            RuntimeError: If memory manager is not created yet
            
        DEPRECATED: Use MemoryManager directly.
        """
        warnings.warn(
            "create_episodic_memory() is deprecated. Use MemoryManager directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if self._memory_manager is None:
            raise RuntimeError(
                "Memory manager must be created first. Call create_memory_manager()."
            )
        
        return EpisodicMemoryAdapter(self._memory_manager)
    
    async def create_semantic_memory(self) -> SemanticMemoryAdapter:
        """
        Create a semantic memory instance.
        
        Returns:
            SemanticMemoryAdapter instance
            
        Raises:
            RuntimeError: If memory manager is not created yet
            
        DEPRECATED: Use MemoryManager directly.
        """
        warnings.warn(
            "create_semantic_memory() is deprecated. Use MemoryManager directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if self._memory_manager is None:
            raise RuntimeError(
                "Memory manager must be created first. Call create_memory_manager()."
            )
        
        return SemanticMemoryAdapter(self._memory_manager)
    
    async def shutdown(self) -> None:
        """
        Shut down the memory system.
        
        DEPRECATED: Use MemoryManager.shutdown() directly.
        """
        warnings.warn(
            "shutdown() is deprecated. Use MemoryManager.shutdown() directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if self._memory_manager:
            await self._memory_manager.shutdown()


# Legacy factory functions

async def create_memory_factory() -> MemoryFactoryAdapter:
    """
    Create a memory factory instance.
    
    Returns:
        MemoryFactoryAdapter instance
        
    DEPRECATED: Use MemoryManager directly.
    """
    warnings.warn(
        "create_memory_factory() is deprecated. Use MemoryManager directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return MemoryFactoryAdapter()


# Provide a direct way to create a memory manager
async def create_memory_manager(
    backend_type: str = "in_memory",
    backend_config: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> MemoryManager:
    """
    Create a memory manager instance.
    
    Args:
        backend_type: Type of backend to use
        backend_config: Backend configuration
        config: Memory manager configuration
        
    Returns:
        Memory manager instance
        
    DEPRECATED: Use MemoryManager constructor directly.
    """
    warnings.warn(
        "create_memory_manager() is deprecated. Use MemoryManager constructor directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    factory = await create_memory_factory()
    return await factory.create_memory_manager(
        backend_type=backend_type,
        backend_config=backend_config,
        config=config,
    )
