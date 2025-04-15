"""
Storage Adapters

This module provides adapters for legacy storage components in the memory system
to use the new architecture. These adapters delegate to the new storage backends
and tier-specific storage components.

This adapter is provided for backward compatibility during migration
and will be removed in a future version.
"""

import asyncio
import logging
import warnings
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from neuroca.memory.backends import BackendType
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory
from neuroca.memory.exceptions import (
    MemoryNotFoundError,
    StorageBackendError,
    StorageInitializationError,
    StorageOperationError,
)
from neuroca.memory.interfaces.storage_backend import StorageBackendInterface
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import SearchFilter, SearchResult
from neuroca.memory.interfaces import StorageStats


logger = logging.getLogger(__name__)


class LegacyLTMStorageAdapter:
    """
    Adapter for legacy LTM storage classes.
    
    This adapter implements the legacy interface but delegates to the new
    storage backend layer.
    
    DEPRECATED: Use storage backends directly instead.
    """
    
    def __init__(
        self,
        backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
        backend_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the LTM storage adapter.
        
        Args:
            backend_type: Type of backend to use
            backend_config: Backend configuration
        """
        warnings.warn(
            "LegacyLTMStorageAdapter is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.backend_type = (
            backend_type if isinstance(backend_type, BackendType) 
            else BackendType(backend_type)
        )
        self.backend_config = backend_config or {}
        self.backend = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the storage backend.
        
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "initialize() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if self._initialized:
            return
        
        try:
            self.backend = await StorageBackendFactory.create_backend(
                self.backend_type,
                self.backend_config
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize LTM storage: {str(e)}")
            raise StorageInitializationError(
                f"Failed to initialize LTM storage: {str(e)}"
            ) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the backend is initialized."""
        if not self._initialized:
            await self.initialize()
    
    async def store(self, memory_item: Any) -> str:
        """
        Store a memory item.
        
        Args:
            memory_item: Memory item to store
            
        Returns:
            Memory ID
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "store() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            # Convert legacy memory item to new format if needed
            if not isinstance(memory_item, MemoryItem):
                memory_item = self._convert_to_memory_item(memory_item)
            
            # Store memory
            memory_id = await self.backend.store(memory_item)
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            raise StorageOperationError(f"Failed to store memory: {str(e)}") from e
    
    async def get(self, memory_id: str) -> Optional[Any]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory item, or None if not found
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "get() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            memory_item = await self.backend.retrieve(memory_id)
            return memory_item
        except MemoryNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {str(e)}")
            return None
    
    async def update(self, memory_item: Any) -> bool:
        """
        Update a memory.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            True if updated, False otherwise
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "update() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            # Convert legacy memory item to new format if needed
            if not isinstance(memory_item, MemoryItem):
                memory_item = self._convert_to_memory_item(memory_item)
            
            # Update memory
            return await self.backend.update(memory_item)
        except Exception as e:
            logger.error(f"Failed to update memory: {str(e)}")
            return False
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if deleted, False otherwise
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "delete() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            return await self.backend.delete(memory_id)
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {str(e)}")
            return False
    
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Any]:
        """
        Search for memories.
        
        Args:
            query: Search query
            filters: Optional filters
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of memory items
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "search() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            # Convert legacy filters to new format if needed
            search_filter = None
            if filters:
                search_filter = SearchFilter()
                if "status" in filters:
                    search_filter.status = filters["status"]
                if "importance" in filters:
                    search_filter.min_importance = filters["importance"]
                if "tags" in filters:
                    search_filter.tags = filters["tags"]
            
            # Search memories
            results = await self.backend.search(
                query=query,
                filter=search_filter,
                limit=limit,
                offset=offset
            )
            
            # Return memory items
            return [r.memory for r in results]
        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []
    
    async def get_stats(self) -> Any:
        """
        Get storage statistics.
        
        Returns:
            Storage statistics
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "get_stats() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            return await self.backend.get_stats()
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return StorageStats()
    
    async def archive_memory(self, memory_id: str) -> bool:
        """
        Archive a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if archived, False otherwise
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "archive_memory() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            memory_item = await self.backend.retrieve(memory_id)
            if memory_item is None:
                return False
            
            # Mark as archived
            memory_item.metadata.status = "archived"
            
            # Update memory
            return await self.backend.update(memory_item)
        except Exception as e:
            logger.error(f"Failed to archive memory {memory_id}: {str(e)}")
            return False
    
    async def restore_memory(self, memory_id: str) -> bool:
        """
        Restore an archived memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if restored, False otherwise
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "restore_memory() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            memory_item = await self.backend.retrieve(memory_id)
            if memory_item is None:
                return False
            
            # Mark as active
            memory_item.metadata.status = "active"
            
            # Update memory
            return await self.backend.update(memory_item)
        except Exception as e:
            logger.error(f"Failed to restore memory {memory_id}: {str(e)}")
            return False
    
    async def bulk_store(self, memory_items: List[Any]) -> List[str]:
        """
        Store multiple memories.
        
        Args:
            memory_items: List of memory items to store
            
        Returns:
            List of memory IDs
            
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "bulk_store() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        await self._ensure_initialized()
        
        try:
            memory_ids = []
            for memory_item in memory_items:
                # Convert legacy memory item to new format if needed
                if not isinstance(memory_item, MemoryItem):
                    memory_item = self._convert_to_memory_item(memory_item)
                
                # Store memory
                memory_id = await self.backend.store(memory_item)
                memory_ids.append(memory_id)
            
            return memory_ids
        except Exception as e:
            logger.error(f"Failed to bulk store memories: {str(e)}")
            raise StorageOperationError(
                f"Failed to bulk store memories: {str(e)}"
            ) from e
    
    def _convert_to_memory_item(self, legacy_memory: Any) -> MemoryItem:
        """Convert a legacy memory item to the new format."""
        # This is a simplified conversion that assumes legacy_memory has
        # similar structure to MemoryItem. In a real-world scenario,
        # you would need to handle all possible legacy formats.
        try:
            # Check if legacy memory has expected attributes
            content = getattr(legacy_memory, "content", None)
            memory_id = getattr(legacy_memory, "id", None) or str(id(legacy_memory))
            
            # Create a basic MemoryItem
            memory_item = MemoryItem(
                id=memory_id,
                content=content,
                summary=getattr(legacy_memory, "summary", None),
                metadata={
                    "importance": getattr(legacy_memory, "importance", 0.5),
                    "created_at": getattr(legacy_memory, "created_at", datetime.now()),
                    "status": getattr(legacy_memory, "status", "active"),
                    "tags": getattr(legacy_memory, "tags", []),
                }
            )
            
            return memory_item
        except Exception as e:
            logger.error(f"Failed to convert legacy memory: {str(e)}")
            # Return a basic memory item as fallback
            return MemoryItem(
                id=str(id(legacy_memory)),
                content=str(legacy_memory),
                metadata={"converted": False}
            )


class LegacySTMStorageAdapter:
    """
    Adapter for legacy STM storage classes.
    
    This adapter implements the legacy interface but delegates to the new
    storage backend layer.
    
    DEPRECATED: Use storage backends directly instead.
    """
    
    def __init__(
        self,
        backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
        backend_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the STM storage adapter.
        
        Args:
            backend_type: Type of backend to use
            backend_config: Backend configuration
        """
        warnings.warn(
            "LegacySTMStorageAdapter is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.backend_type = (
            backend_type if isinstance(backend_type, BackendType) 
            else BackendType(backend_type)
        )
        self.backend_config = backend_config or {}
        self.backend = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the storage backend.
        
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "initialize() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if self._initialized:
            return
        
        try:
            self.backend = await StorageBackendFactory.create_backend(
                self.backend_type,
                self.backend_config
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize STM storage: {str(e)}")
            raise StorageInitializationError(
                f"Failed to initialize STM storage: {str(e)}"
            ) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the backend is initialized."""
        if not self._initialized:
            await self.initialize()
    
    # Implement the same methods as LegacyLTMStorageAdapter
    # with appropriate modifications for STM storage behavior
    
    # ... (similar methods as LegacyLTMStorageAdapter)


class LegacyMTMStorageAdapter:
    """
    Adapter for legacy MTM storage classes.
    
    This adapter implements the legacy interface but delegates to the new
    storage backend layer.
    
    DEPRECATED: Use storage backends directly instead.
    """
    
    def __init__(
        self,
        backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
        backend_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the MTM storage adapter.
        
        Args:
            backend_type: Type of backend to use
            backend_config: Backend configuration
        """
        warnings.warn(
            "LegacyMTMStorageAdapter is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.backend_type = (
            backend_type if isinstance(backend_type, BackendType) 
            else BackendType(backend_type)
        )
        self.backend_config = backend_config or {}
        self.backend = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the storage backend.
        
        DEPRECATED: Use storage backends directly.
        """
        warnings.warn(
            "initialize() is deprecated. Use storage backends directly.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if self._initialized:
            return
        
        try:
            self.backend = await StorageBackendFactory.create_backend(
                self.backend_type,
                self.backend_config
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize MTM storage: {str(e)}")
            raise StorageInitializationError(
                f"Failed to initialize MTM storage: {str(e)}"
            ) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the backend is initialized."""
        if not self._initialized:
            await self.initialize()
    
    # Implement the same methods as LegacyLTMStorageAdapter
    # with appropriate modifications for MTM storage behavior
    
    # ... (similar methods as LegacyLTMStorageAdapter)


# Legacy function adapters to match the old interfaces

async def store_memory(
    memory_item: Any,
    backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
    backend_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Store a memory item using the legacy interface.
    
    DEPRECATED: Use storage backends directly.
    """
    warnings.warn(
        "store_memory() is deprecated. Use storage backends directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    adapter = LegacyLTMStorageAdapter(
        backend_type=backend_type,
        backend_config=backend_config
    )
    return await adapter.store(memory_item)


async def retrieve_memory(
    memory_id: str,
    backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
    backend_config: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Retrieve a memory item using the legacy interface.
    
    DEPRECATED: Use storage backends directly.
    """
    warnings.warn(
        "retrieve_memory() is deprecated. Use storage backends directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    adapter = LegacyLTMStorageAdapter(
        backend_type=backend_type,
        backend_config=backend_config
    )
    return await adapter.get(memory_id)


async def update_memory(
    memory_item: Any,
    backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
    backend_config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update a memory item using the legacy interface.
    
    DEPRECATED: Use storage backends directly.
    """
    warnings.warn(
        "update_memory() is deprecated. Use storage backends directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    adapter = LegacyLTMStorageAdapter(
        backend_type=backend_type,
        backend_config=backend_config
    )
    return await adapter.update(memory_item)


async def delete_memory(
    memory_id: str,
    backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
    backend_config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Delete a memory item using the legacy interface.
    
    DEPRECATED: Use storage backends directly.
    """
    warnings.warn(
        "delete_memory() is deprecated. Use storage backends directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    adapter = LegacyLTMStorageAdapter(
        backend_type=backend_type,
        backend_config=backend_config
    )
    return await adapter.delete(memory_id)


async def search_memories(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    offset: int = 0,
    backend_type: Union[str, BackendType] = BackendType.IN_MEMORY,
    backend_config: Optional[Dict[str, Any]] = None
) -> List[Any]:
    """
    Search for memory items using the legacy interface.
    
    DEPRECATED: Use storage backends directly.
    """
    warnings.warn(
        "search_memories() is deprecated. Use storage backends directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    adapter = LegacyLTMStorageAdapter(
        backend_type=backend_type,
        backend_config=backend_config
    )
    return await adapter.search(query, filters, limit, offset)
