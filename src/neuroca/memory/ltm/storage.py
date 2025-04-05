"""
Long-Term Memory (LTM) Storage Module.

This module provides the storage layer for the Long-Term Memory component of the NeuroCognitive Architecture.
It implements persistent storage mechanisms for memory items with support for various backend storage options,
indexing, retrieval, and management of long-term memories.

The storage layer is designed to be:
1. Persistent - memories survive system restarts
2. Scalable - can handle large volumes of memories
3. Efficient - optimized for fast retrieval of relevant memories
4. Flexible - supports multiple storage backends
5. Secure - implements proper access controls and data protection

Usage:
    # Initialize storage with default settings
    storage = LTMStorage()
    
    # Store a memory
    memory_id = await storage.store(memory_item)
    
    # Retrieve a memory by ID
    memory = await storage.get(memory_id)
    
    # Search for memories
    results = await storage.search(query="project meeting", limit=5)
"""

import asyncio
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import aiofiles
from pydantic import BaseModel, ValidationError

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import (
    LTMStorageError,
    MemoryNotFoundError,
    StorageBackendError,
    StorageInitializationError,
)
from neuroca.memory.models import MemoryItem, MemoryMetadata, MemoryStatus

# Configure logger
logger = logging.getLogger(__name__)


class StorageBackendType(str, Enum):
    """Supported storage backend types."""
    
    FILE_SYSTEM = "file_system"
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    VECTOR_DB = "vector_db"
    IN_MEMORY = "in_memory"  # For testing purposes


class StorageStats(BaseModel):
    """Statistics about the storage system."""
    
    total_memories: int = 0
    active_memories: int = 0
    archived_memories: int = 0
    total_size_bytes: int = 0
    last_access_time: Optional[datetime] = None
    last_write_time: Optional[datetime] = None


class StorageBackend(ABC):
    """Abstract base class for LTM storage backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass
    
    @abstractmethod
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            StorageBackendError: If the memory cannot be stored
        """
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
            
        Raises:
            StorageBackendError: If there's an error retrieving the memory
        """
        pass
    
    @abstractmethod
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item.
        
        Args:
            memory_item: The memory item to update
            
        Returns:
            bool: True if the update was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error updating the memory
        """
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            bool: True if the deletion was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error deleting the memory
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        filters: Optional[dict[str, Any]] = None, 
        limit: int = 10,
        offset: int = 0
    ) -> list[MemoryItem]:
        """
        Search for memory items.
        
        Args:
            query: The search query
            filters: Optional filters to apply to the search
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List[MemoryItem]: List of memory items matching the search criteria
            
        Raises:
            StorageBackendError: If there's an error during search
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the storage.
        
        Returns:
            StorageStats: Statistics about the storage
            
        Raises:
            StorageBackendError: If there's an error retrieving statistics
        """
        pass


class FileSystemBackend(StorageBackend):
    """File system implementation of the storage backend."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the file system backend.
        
        Args:
            base_path: Base directory for storing memories. If None, uses the default path.
        """
        settings = get_settings()
        self.base_path = Path(base_path or settings.ltm_storage_path)
        self.memories_path = self.base_path / "memories"
        self.index_path = self.base_path / "index"
        self.metadata_path = self.base_path / "metadata.json"
        self._lock = asyncio.Lock()
        self._metadata: dict[str, dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """
        Initialize the file system storage.
        
        Creates necessary directories and loads metadata.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Create directories if they don't exist
            os.makedirs(self.memories_path, exist_ok=True)
            os.makedirs(self.index_path, exist_ok=True)
            
            # Load metadata if it exists
            if os.path.exists(self.metadata_path):
                async with aiofiles.open(self.metadata_path, 'r') as f:
                    content = await f.read()
                    self._metadata = json.loads(content) if content else {}
            
            logger.info(f"Initialized file system storage at {self.base_path}")
        except Exception as e:
            error_msg = f"Failed to initialize file system storage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the file system.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            StorageBackendError: If the memory cannot be stored
        """
        try:
            # Ensure memory has an ID
            if not memory_item.id:
                memory_item.id = str(uuid.uuid4())
            
            memory_id = memory_item.id
            file_path = self.memories_path / f"{memory_id}.json"
            
            # Serialize memory item
            memory_data = memory_item.model_dump_json(indent=2)
            
            # Write to file
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(memory_data)
            
            # Update metadata
            async with self._lock:
                self._metadata[memory_id] = {
                    "created_at": datetime.now().isoformat(),
                    "last_accessed": datetime.now().isoformat(),
                    "status": memory_item.metadata.status.value if memory_item.metadata else MemoryStatus.ACTIVE.value,
                    "size_bytes": len(memory_data),
                }
                await self._save_metadata()
            
            logger.debug(f"Stored memory with ID: {memory_id}")
            return memory_id
            
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID from the file system.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
            
        Raises:
            StorageBackendError: If there's an error retrieving the memory
        """
        try:
            file_path = self.memories_path / f"{memory_id}.json"
            
            if not os.path.exists(file_path):
                logger.debug(f"Memory with ID {memory_id} not found")
                return None
            
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                memory_item = MemoryItem.model_validate_json(content)
            
            # Update access metadata
            async with self._lock:
                if memory_id in self._metadata:
                    self._metadata[memory_id]["last_accessed"] = datetime.now().isoformat()
                    await self._save_metadata()
            
            logger.debug(f"Retrieved memory with ID: {memory_id}")
            return memory_item
            
        except ValidationError as e:
            error_msg = f"Invalid memory data format for ID {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to retrieve memory with ID {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the file system.
        
        Args:
            memory_item: The memory item to update
            
        Returns:
            bool: True if the update was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error updating the memory
        """
        try:
            memory_id = memory_item.id
            if not memory_id:
                logger.error("Cannot update memory without ID")
                return False
            
            file_path = self.memories_path / f"{memory_id}.json"
            
            if not os.path.exists(file_path):
                logger.warning(f"Memory with ID {memory_id} not found for update")
                return False
            
            # Serialize memory item
            memory_data = memory_item.model_dump_json(indent=2)
            
            # Write to file
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(memory_data)
            
            # Update metadata
            async with self._lock:
                if memory_id in self._metadata:
                    self._metadata[memory_id]["last_modified"] = datetime.now().isoformat()
                    self._metadata[memory_id]["size_bytes"] = len(memory_data)
                    if memory_item.metadata and memory_item.metadata.status:
                        self._metadata[memory_id]["status"] = memory_item.metadata.status.value
                    await self._save_metadata()
            
            logger.debug(f"Updated memory with ID: {memory_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update memory with ID {memory_item.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the file system.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            bool: True if the deletion was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error deleting the memory
        """
        try:
            file_path = self.memories_path / f"{memory_id}.json"
            
            if not os.path.exists(file_path):
                logger.warning(f"Memory with ID {memory_id} not found for deletion")
                return False
            
            # Remove file
            os.remove(file_path)
            
            # Update metadata
            async with self._lock:
                if memory_id in self._metadata:
                    del self._metadata[memory_id]
                    await self._save_metadata()
            
            logger.debug(f"Deleted memory with ID: {memory_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete memory with ID {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def search(
        self, 
        query: str, 
        filters: Optional[dict[str, Any]] = None, 
        limit: int = 10,
        offset: int = 0
    ) -> list[MemoryItem]:
        """
        Search for memory items in the file system.
        
        Note: This is a basic implementation that loads and filters all memories.
        For production use with large datasets, consider using a proper search index.
        
        Args:
            query: The search query
            filters: Optional filters to apply to the search
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List[MemoryItem]: List of memory items matching the search criteria
            
        Raises:
            StorageBackendError: If there's an error during search
        """
        try:
            results = []
            query = query.lower()
            filters = filters or {}
            
            # List all memory files
            memory_files = list(self.memories_path.glob("*.json"))
            
            # Process files
            for file_path in memory_files:
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        memory_item = MemoryItem.model_validate_json(content)
                    
                    # Check if memory matches query and filters
                    if self._matches_search_criteria(memory_item, query, filters):
                        results.append(memory_item)
                except Exception as e:
                    logger.warning(f"Error processing memory file {file_path}: {str(e)}")
                    continue
            
            # Sort by relevance (simple implementation - by creation time)
            results.sort(key=lambda x: x.metadata.created_at if x.metadata else datetime.min, reverse=True)
            
            # Apply pagination
            paginated_results = results[offset:offset + limit]
            
            logger.debug(f"Search for '{query}' returned {len(paginated_results)} results")
            return paginated_results
            
        except Exception as e:
            error_msg = f"Failed to search memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the file system storage.
        
        Returns:
            StorageStats: Statistics about the storage
            
        Raises:
            StorageBackendError: If there's an error retrieving statistics
        """
        try:
            stats = StorageStats()
            
            # Count files and calculate total size
            memory_files = list(self.memories_path.glob("*.json"))
            stats.total_memories = len(memory_files)
            stats.total_size_bytes = sum(os.path.getsize(f) for f in memory_files)
            
            # Count by status
            active_count = 0
            archived_count = 0
            
            async with self._lock:
                for metadata in self._metadata.values():
                    if metadata.get("status") == MemoryStatus.ACTIVE.value:
                        active_count += 1
                    elif metadata.get("status") == MemoryStatus.ARCHIVED.value:
                        archived_count += 1
            
            stats.active_memories = active_count
            stats.archived_memories = archived_count
            
            # Get last access and write times
            if self._metadata:
                access_times = [
                    datetime.fromisoformat(m["last_accessed"]) 
                    for m in self._metadata.values() 
                    if "last_accessed" in m
                ]
                if access_times:
                    stats.last_access_time = max(access_times)
                
                write_times = [
                    datetime.fromisoformat(m["last_modified"]) 
                    for m in self._metadata.values() 
                    if "last_modified" in m
                ]
                if write_times:
                    stats.last_write_time = max(write_times)
            
            logger.debug(f"Retrieved storage stats: {stats.model_dump()}")
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            async with aiofiles.open(self.metadata_path, 'w') as f:
                await f.write(json.dumps(self._metadata, indent=2))
        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}", exc_info=True)
    
    def _matches_search_criteria(
        self, 
        memory_item: MemoryItem, 
        query: str, 
        filters: dict[str, Any]
    ) -> bool:
        """
        Check if a memory item matches the search criteria.
        
        Args:
            memory_item: The memory item to check
            query: The search query
            filters: Filters to apply
            
        Returns:
            bool: True if the memory matches the criteria, False otherwise
        """
        # Check query match in content
        if query:
            content_match = False
            if memory_item.content and query in memory_item.content.lower():
                content_match = True
            elif memory_item.summary and query in memory_item.summary.lower():
                content_match = True
            elif memory_item.metadata and memory_item.metadata.tags:
                for tag in memory_item.metadata.tags:
                    if query in tag.lower():
                        content_match = True
                        break
            
            if not content_match:
                return False
        
        # Apply filters
        for key, value in filters.items():
            if key == "status" and memory_item.metadata:
                if memory_item.metadata.status != value:
                    return False
            elif key == "importance" and memory_item.metadata:
                if memory_item.metadata.importance < value:
                    return False
            elif key == "tags" and memory_item.metadata and memory_item.metadata.tags:
                if not set(value).issubset(set(memory_item.metadata.tags)):
                    return False
            elif key == "created_after" and memory_item.metadata:
                if memory_item.metadata.created_at < value:
                    return False
            elif key == "created_before" and memory_item.metadata:
                if memory_item.metadata.created_at > value:
                    return False
        
        return True


class LTMStorage:
    """
    Long-Term Memory Storage Manager.
    
    This class provides a unified interface for storing, retrieving, and managing
    long-term memories using configurable backend storage systems.
    """
    
    def __init__(
        self,
        backend_type: Union[StorageBackendType, str] = StorageBackendType.FILE_SYSTEM,
        backend_config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the LTM Storage Manager.
        
        Args:
            backend_type: The type of storage backend to use
            backend_config: Configuration options for the storage backend
            
        Raises:
            StorageInitializationError: If initialization fails
        """
        self.backend_type = backend_type if isinstance(backend_type, StorageBackendType) else StorageBackendType(backend_type)
        self.backend_config = backend_config or {}
        self.backend: Optional[StorageBackend] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the storage backend.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        if self._initialized:
            logger.debug("Storage already initialized")
            return
        
        try:
            # Create the appropriate backend
            if self.backend_type == StorageBackendType.FILE_SYSTEM:
                self.backend = FileSystemBackend(**self.backend_config)
            else:
                raise StorageInitializationError(f"Unsupported backend type: {self.backend_type}")
            
            # Initialize the backend
            await self.backend.initialize()
            self._initialized = True
            logger.info(f"Initialized LTM storage with backend: {self.backend_type}")
            
        except Exception as e:
            error_msg = f"Failed to initialize LTM storage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the storage is initialized before use."""
        if not self._initialized:
            await self.initialize()
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            LTMStorageError: If the memory cannot be stored
        """
        try:
            await self._ensure_initialized()
            
            # Set creation time if not set
            if memory_item.metadata is None:
                memory_item.metadata = MemoryMetadata(
                    created_at=datetime.now(),
                    status=MemoryStatus.ACTIVE
                )
            elif memory_item.metadata.created_at is None:
                memory_item.metadata.created_at = datetime.now()
            
            # Store the memory
            memory_id = await self.backend.store(memory_item)
            return memory_id
            
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def get(self, memory_id: str) -> MemoryItem:
        """
        Retrieve a memory item by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            MemoryItem: The memory item
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            LTMStorageError: If there's an error retrieving the memory
        """
        try:
            await self._ensure_initialized()
            
            memory_item = await self.backend.get(memory_id)
            if memory_item is None:
                raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
            
            return memory_item
            
        except MemoryNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve memory with ID {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item.
        
        Args:
            memory_item: The memory item to update
            
        Returns:
            bool: True if the update was successful, False otherwise
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            LTMStorageError: If there's an error updating the memory
        """
        try:
            await self._ensure_initialized()
            
            # Check if memory exists
            existing_memory = await self.backend.get(memory_item.id)
            if existing_memory is None:
                raise MemoryNotFoundError(f"Memory with ID {memory_item.id} not found")
            
            # Update the memory
            success = await self.backend.update(memory_item)
            return success
            
        except MemoryNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to update memory with ID {memory_item.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            bool: True if the deletion was successful, False otherwise
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            LTMStorageError: If there's an error deleting the memory
        """
        try:
            await self._ensure_initialized()
            
            # Check if memory exists
            existing_memory = await self.backend.get(memory_id)
            if existing_memory is None:
                raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
            
            # Delete the memory
            success = await self.backend.delete(memory_id)
            return success
            
        except MemoryNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to delete memory with ID {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def search(
        self, 
        query: str, 
        filters: Optional[dict[str, Any]] = None, 
        limit: int = 10,
        offset: int = 0
    ) -> list[MemoryItem]:
        """
        Search for memory items.
        
        Args:
            query: The search query
            filters: Optional filters to apply to the search
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List[MemoryItem]: List of memory items matching the search criteria
            
        Raises:
            LTMStorageError: If there's an error during search
        """
        try:
            await self._ensure_initialized()
            
            # Validate parameters
            if limit < 1:
                limit = 10
            if offset < 0:
                offset = 0
            
            # Perform search
            results = await self.backend.search(query, filters, limit, offset)
            return results
            
        except Exception as e:
            error_msg = f"Failed to search memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the storage.
        
        Returns:
            StorageStats: Statistics about the storage
            
        Raises:
            LTMStorageError: If there's an error retrieving statistics
        """
        try:
            await self._ensure_initialized()
            
            stats = await self.backend.get_stats()
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def archive_memory(self, memory_id: str) -> bool:
        """
        Archive a memory item.
        
        Args:
            memory_id: The ID of the memory to archive
            
        Returns:
            bool: True if the archiving was successful, False otherwise
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            LTMStorageError: If there's an error archiving the memory
        """
        try:
            await self._ensure_initialized()
            
            # Get the memory
            memory_item = await self.get(memory_id)
            
            # Update status
            if memory_item.metadata is None:
                memory_item.metadata = MemoryMetadata(status=MemoryStatus.ARCHIVED)
            else:
                memory_item.metadata.status = MemoryStatus.ARCHIVED
            
            # Update the memory
            success = await self.update(memory_item)
            return success
            
        except MemoryNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to archive memory with ID {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def restore_memory(self, memory_id: str) -> bool:
        """
        Restore an archived memory item.
        
        Args:
            memory_id: The ID of the memory to restore
            
        Returns:
            bool: True if the restoration was successful, False otherwise
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            LTMStorageError: If there's an error restoring the memory
        """
        try:
            await self._ensure_initialized()
            
            # Get the memory
            memory_item = await self.get(memory_id)
            
            # Update status
            if memory_item.metadata is None:
                memory_item.metadata = MemoryMetadata(status=MemoryStatus.ACTIVE)
            else:
                memory_item.metadata.status = MemoryStatus.ACTIVE
            
            # Update the memory
            success = await self.update(memory_item)
            return success
            
        except MemoryNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to restore memory with ID {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e
    
    async def bulk_store(self, memory_items: list[MemoryItem]) -> list[str]:
        """
        Store multiple memory items in a batch.
        
        Args:
            memory_items: List of memory items to store
            
        Returns:
            List[str]: List of IDs of the stored memories
            
        Raises:
            LTMStorageError: If there's an error storing the memories
        """
        try:
            await self._ensure_initialized()
            
            memory_ids = []
            for memory_item in memory_items:
                memory_id = await self.store(memory_item)
                memory_ids.append(memory_id)
            
            return memory_ids
            
        except Exception as e:
            error_msg = f"Failed to bulk store memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LTMStorageError(error_msg) from e