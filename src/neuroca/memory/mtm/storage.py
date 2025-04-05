"""
Medium-Term Memory (MTM) Storage Module.

This module provides the storage layer for the Medium-Term Memory (MTM) component of the
NeuroCognitive Architecture. It handles the persistence, retrieval, and management of
medium-term memories, implementing appropriate storage strategies, indexing, and
garbage collection mechanisms.

The MTM storage layer is designed to:
1. Efficiently store and retrieve medium-term memories
2. Support various storage backends (in-memory, file-based, database)
3. Implement memory consolidation and forgetting mechanisms
4. Provide transaction support for memory operations
5. Handle concurrent access to memory storage

Usage:
    # Initialize storage with default settings
    storage = MTMStorage()
    
    # Store a memory
    memory_id = storage.store(memory_data)
    
    # Retrieve a memory
    memory = storage.retrieve(memory_id)
    
    # Update a memory
    storage.update(memory_id, updated_memory_data)
    
    # Delete a memory
    storage.delete(memory_id)
"""

import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from threading import Lock
from typing import Any, Optional

import aiofiles
from pydantic import BaseModel, Field, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for all storage-related errors."""
    pass


class MemoryNotFoundError(StorageError):
    """Exception raised when a memory cannot be found in storage."""
    pass


class StorageInitializationError(StorageError):
    """Exception raised when storage initialization fails."""
    pass


class StorageOperationError(StorageError):
    """Exception raised when a storage operation fails."""
    pass


class MemoryValidationError(StorageError):
    """Exception raised when memory validation fails."""
    pass


class StorageBackendType(Enum):
    """Enumeration of supported storage backend types."""
    IN_MEMORY = auto()
    FILE = auto()
    DATABASE = auto()


class MemoryStatus(Enum):
    """Enumeration of possible memory statuses."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CONSOLIDATED = "consolidated"
    FORGOTTEN = "forgotten"


class MemoryPriority(Enum):
    """Enumeration of memory priority levels."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class MTMMemory(BaseModel):
    """
    Medium-Term Memory data model.
    
    Represents a single memory entry in the Medium-Term Memory system.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0)
    priority: MemoryPriority = Field(default=MemoryPriority.MEDIUM)
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def increment_access(self) -> None:
        """Increment the access count and update the last accessed timestamp."""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the memory to a dictionary."""
        result = self.dict()
        result["priority"] = self.priority.value
        result["status"] = self.status.value
        return result


@dataclass
class StorageStats:
    """Statistics about the storage system."""
    total_memories: int = 0
    active_memories: int = 0
    archived_memories: int = 0
    consolidated_memories: int = 0
    forgotten_memories: int = 0
    total_size_bytes: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass
    
    @abstractmethod
    async def store(self, memory: MTMMemory) -> str:
        """
        Store a memory in the backend.
        
        Args:
            memory: The memory to store
            
        Returns:
            The ID of the stored memory
            
        Raises:
            StorageOperationError: If the storage operation fails
        """
        pass
    
    @abstractmethod
    async def retrieve(self, memory_id: str) -> MTMMemory:
        """
        Retrieve a memory from the backend.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The retrieved memory
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, memory: MTMMemory) -> None:
        """
        Update a memory in the backend.
        
        Args:
            memory_id: The ID of the memory to update
            memory: The updated memory
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the update operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> None:
        """
        Delete a memory from the backend.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the delete operation fails
        """
        pass
    
    @abstractmethod
    async def list_all(self) -> list[MTMMemory]:
        """
        List all memories in the backend.
        
        Returns:
            A list of all memories
            
        Raises:
            StorageOperationError: If the list operation fails
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the storage.
        
        Returns:
            Statistics about the storage
            
        Raises:
            StorageOperationError: If the stats operation fails
        """
        pass


class InMemoryStorageBackend(StorageBackend):
    """In-memory implementation of the storage backend."""
    
    def __init__(self):
        """Initialize the in-memory storage backend."""
        self._memories: dict[str, MTMMemory] = {}
        self._lock = Lock()
        logger.debug("Initialized in-memory storage backend")
    
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        # Nothing to initialize for in-memory storage
        logger.info("In-memory storage backend initialized")
    
    async def store(self, memory: MTMMemory) -> str:
        """Store a memory in the backend."""
        try:
            with self._lock:
                self._memories[memory.id] = memory
            logger.debug(f"Stored memory with ID {memory.id}")
            return memory.id
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> MTMMemory:
        """Retrieve a memory from the backend."""
        try:
            with self._lock:
                if memory_id not in self._memories:
                    raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                memory = self._memories[memory_id]
                memory.increment_access()
                return memory
        except MemoryNotFoundError:
            logger.warning(f"Memory with ID {memory_id} not found")
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_id: str, memory: MTMMemory) -> None:
        """Update a memory in the backend."""
        try:
            with self._lock:
                if memory_id not in self._memories:
                    raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                self._memories[memory_id] = memory
            logger.debug(f"Updated memory with ID {memory_id}")
        except MemoryNotFoundError:
            logger.warning(f"Memory with ID {memory_id} not found for update")
            raise
        except Exception as e:
            error_msg = f"Failed to update memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> None:
        """Delete a memory from the backend."""
        try:
            with self._lock:
                if memory_id not in self._memories:
                    raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                del self._memories[memory_id]
            logger.debug(f"Deleted memory with ID {memory_id}")
        except MemoryNotFoundError:
            logger.warning(f"Memory with ID {memory_id} not found for deletion")
            raise
        except Exception as e:
            error_msg = f"Failed to delete memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def list_all(self) -> list[MTMMemory]:
        """List all memories in the backend."""
        try:
            with self._lock:
                return list(self._memories.values())
        except Exception as e:
            error_msg = f"Failed to list memories: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """Get statistics about the storage."""
        try:
            with self._lock:
                total = len(self._memories)
                active = sum(1 for m in self._memories.values() if m.status == MemoryStatus.ACTIVE)
                archived = sum(1 for m in self._memories.values() if m.status == MemoryStatus.ARCHIVED)
                consolidated = sum(1 for m in self._memories.values() if m.status == MemoryStatus.CONSOLIDATED)
                forgotten = sum(1 for m in self._memories.values() if m.status == MemoryStatus.FORGOTTEN)
                
                # Estimate size in bytes (rough approximation)
                size_bytes = sum(len(json.dumps(m.dict())) for m in self._memories.values())
                
                return StorageStats(
                    total_memories=total,
                    active_memories=active,
                    archived_memories=archived,
                    consolidated_memories=consolidated,
                    forgotten_memories=forgotten,
                    total_size_bytes=size_bytes,
                    last_updated=datetime.now()
                )
        except Exception as e:
            error_msg = f"Failed to get storage stats: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e


class FileStorageBackend(StorageBackend):
    """File-based implementation of the storage backend."""
    
    def __init__(self, storage_dir: str = "./mtm_storage"):
        """
        Initialize the file storage backend.
        
        Args:
            storage_dir: Directory to store memory files
        """
        self.storage_dir = Path(storage_dir)
        self.index_file = self.storage_dir / "index.json"
        self._index: dict[str, dict[str, Any]] = {}
        self._lock = Lock()
        logger.debug(f"Initialized file storage backend with directory {storage_dir}")
    
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(self.storage_dir, exist_ok=True)
            
            # Load index if it exists
            if self.index_file.exists():
                async with aiofiles.open(self.index_file, "r") as f:
                    content = await f.read()
                    self._index = json.loads(content) if content else {}
            
            logger.info(f"File storage backend initialized at {self.storage_dir}")
        except Exception as e:
            error_msg = f"Failed to initialize file storage backend: {str(e)}"
            logger.error(error_msg)
            raise StorageInitializationError(error_msg) from e
    
    async def _save_index(self) -> None:
        """Save the index to disk."""
        try:
            async with aiofiles.open(self.index_file, "w") as f:
                await f.write(json.dumps(self._index, indent=2))
        except Exception as e:
            error_msg = f"Failed to save index: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def store(self, memory: MTMMemory) -> str:
        """Store a memory in the backend."""
        try:
            memory_path = self.storage_dir / f"{memory.id}.json"
            memory_dict = memory.to_dict()
            
            # Write memory to file
            async with aiofiles.open(memory_path, "w") as f:
                await f.write(json.dumps(memory_dict, indent=2))
            
            # Update index
            with self._lock:
                self._index[memory.id] = {
                    "path": str(memory_path),
                    "created_at": memory.created_at.isoformat(),
                    "status": memory.status.value,
                    "tags": memory.tags
                }
                await self._save_index()
            
            logger.debug(f"Stored memory with ID {memory.id} to {memory_path}")
            return memory.id
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> MTMMemory:
        """Retrieve a memory from the backend."""
        try:
            with self._lock:
                if memory_id not in self._index:
                    raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                
                memory_path = Path(self._index[memory_id]["path"])
            
            if not memory_path.exists():
                error_msg = f"Memory file {memory_path} does not exist"
                logger.error(error_msg)
                raise MemoryNotFoundError(error_msg)
            
            # Read memory from file
            async with aiofiles.open(memory_path, "r") as f:
                content = await f.read()
                memory_dict = json.loads(content)
            
            # Convert dictionary to MTMMemory
            try:
                # Convert string values back to enum values
                memory_dict["priority"] = MemoryPriority(memory_dict["priority"])
                memory_dict["status"] = MemoryStatus(memory_dict["status"])
                
                memory = MTMMemory(**memory_dict)
                memory.increment_access()
                
                # Update the file with incremented access count
                await self.update(memory_id, memory)
                
                return memory
            except ValidationError as e:
                error_msg = f"Invalid memory format: {str(e)}"
                logger.error(error_msg)
                raise MemoryValidationError(error_msg) from e
            
        except MemoryNotFoundError:
            logger.warning(f"Memory with ID {memory_id} not found")
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_id: str, memory: MTMMemory) -> None:
        """Update a memory in the backend."""
        try:
            with self._lock:
                if memory_id not in self._index:
                    raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                
                memory_path = Path(self._index[memory_id]["path"])
            
            if not memory_path.exists():
                error_msg = f"Memory file {memory_path} does not exist"
                logger.error(error_msg)
                raise MemoryNotFoundError(error_msg)
            
            # Write updated memory to file
            memory_dict = memory.to_dict()
            async with aiofiles.open(memory_path, "w") as f:
                await f.write(json.dumps(memory_dict, indent=2))
            
            # Update index
            with self._lock:
                self._index[memory_id] = {
                    "path": str(memory_path),
                    "created_at": memory.created_at.isoformat(),
                    "status": memory.status.value,
                    "tags": memory.tags
                }
                await self._save_index()
            
            logger.debug(f"Updated memory with ID {memory_id}")
        except MemoryNotFoundError:
            logger.warning(f"Memory with ID {memory_id} not found for update")
            raise
        except Exception as e:
            error_msg = f"Failed to update memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> None:
        """Delete a memory from the backend."""
        try:
            with self._lock:
                if memory_id not in self._index:
                    raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                
                memory_path = Path(self._index[memory_id]["path"])
                
                # Delete file if it exists
                if memory_path.exists():
                    os.remove(memory_path)
                
                # Remove from index
                del self._index[memory_id]
                await self._save_index()
            
            logger.debug(f"Deleted memory with ID {memory_id}")
        except MemoryNotFoundError:
            logger.warning(f"Memory with ID {memory_id} not found for deletion")
            raise
        except Exception as e:
            error_msg = f"Failed to delete memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def list_all(self) -> list[MTMMemory]:
        """List all memories in the backend."""
        try:
            memories = []
            
            with self._lock:
                memory_ids = list(self._index.keys())
            
            for memory_id in memory_ids:
                try:
                    memory = await self.retrieve(memory_id)
                    memories.append(memory)
                except (MemoryNotFoundError, StorageOperationError) as e:
                    # Log error but continue with other memories
                    logger.warning(f"Error retrieving memory {memory_id}: {str(e)}")
            
            return memories
        except Exception as e:
            error_msg = f"Failed to list memories: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """Get statistics about the storage."""
        try:
            with self._lock:
                total = len(self._index)
                
                # Count by status
                active = sum(1 for info in self._index.values() if info["status"] == MemoryStatus.ACTIVE.value)
                archived = sum(1 for info in self._index.values() if info["status"] == MemoryStatus.ARCHIVED.value)
                consolidated = sum(1 for info in self._index.values() if info["status"] == MemoryStatus.CONSOLIDATED.value)
                forgotten = sum(1 for info in self._index.values() if info["status"] == MemoryStatus.FORGOTTEN.value)
                
                # Calculate total size
                total_size = 0
                for _memory_id, info in self._index.items():
                    path = Path(info["path"])
                    if path.exists():
                        total_size += path.stat().st_size
                
                return StorageStats(
                    total_memories=total,
                    active_memories=active,
                    archived_memories=archived,
                    consolidated_memories=consolidated,
                    forgotten_memories=forgotten,
                    total_size_bytes=total_size,
                    last_updated=datetime.now()
                )
        except Exception as e:
            error_msg = f"Failed to get storage stats: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e


class MTMStorage:
    """
    Medium-Term Memory (MTM) Storage Manager.
    
    This class provides a unified interface for storing, retrieving, and managing
    medium-term memories, abstracting away the details of the underlying storage backend.
    """
    
    def __init__(self, backend_type: StorageBackendType = StorageBackendType.IN_MEMORY, **backend_options):
        """
        Initialize the MTM storage manager.
        
        Args:
            backend_type: Type of storage backend to use
            **backend_options: Options to pass to the storage backend
        
        Raises:
            StorageInitializationError: If storage initialization fails
        """
        self.backend_type = backend_type
        self.backend_options = backend_options
        self.backend = self._create_backend()
        logger.info(f"Initialized MTM storage with backend type {backend_type}")
    
    def _create_backend(self) -> StorageBackend:
        """Create and return the appropriate storage backend."""
        try:
            if self.backend_type == StorageBackendType.IN_MEMORY:
                return InMemoryStorageBackend()
            elif self.backend_type == StorageBackendType.FILE:
                storage_dir = self.backend_options.get("storage_dir", "./mtm_storage")
                return FileStorageBackend(storage_dir=storage_dir)
            elif self.backend_type == StorageBackendType.DATABASE:
                # Database backend not implemented yet
                raise NotImplementedError("Database storage backend not implemented yet")
            else:
                raise ValueError(f"Unsupported backend type: {self.backend_type}")
        except Exception as e:
            error_msg = f"Failed to create storage backend: {str(e)}"
            logger.error(error_msg)
            raise StorageInitializationError(error_msg) from e
    
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        try:
            await self.backend.initialize()
            logger.info("MTM storage initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize MTM storage: {str(e)}"
            logger.error(error_msg)
            raise StorageInitializationError(error_msg) from e
    
    async def store(self, content: dict[str, Any], tags: list[str] = None, 
                   priority: MemoryPriority = MemoryPriority.MEDIUM,
                   metadata: dict[str, Any] = None) -> str:
        """
        Store a new memory.
        
        Args:
            content: The content of the memory
            tags: Optional tags for categorizing the memory
            priority: Priority level of the memory
            metadata: Additional metadata for the memory
        
        Returns:
            The ID of the stored memory
            
        Raises:
            StorageOperationError: If the storage operation fails
        """
        try:
            # Validate content
            if not content:
                raise ValueError("Memory content cannot be empty")
            
            # Create memory object
            memory = MTMMemory(
                content=content,
                tags=tags or [],
                priority=priority,
                metadata=metadata or {}
            )
            
            # Store in backend
            memory_id = await self.backend.store(memory)
            logger.info(f"Stored new memory with ID {memory_id}")
            return memory_id
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def retrieve(self, memory_id: str) -> MTMMemory:
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The retrieved memory
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the retrieval operation fails
        """
        try:
            memory = await self.backend.retrieve(memory_id)
            logger.debug(f"Retrieved memory with ID {memory_id}")
            return memory
        except Exception as e:
            if isinstance(e, MemoryNotFoundError):
                logger.warning(f"Memory with ID {memory_id} not found")
                raise
            error_msg = f"Failed to retrieve memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_id: str, content: Optional[dict[str, Any]] = None,
                    tags: Optional[list[str]] = None, priority: Optional[MemoryPriority] = None,
                    status: Optional[MemoryStatus] = None, metadata: Optional[dict[str, Any]] = None) -> None:
        """
        Update a memory.
        
        Args:
            memory_id: The ID of the memory to update
            content: New content (if None, keeps existing content)
            tags: New tags (if None, keeps existing tags)
            priority: New priority (if None, keeps existing priority)
            status: New status (if None, keeps existing status)
            metadata: New metadata (if None, keeps existing metadata)
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the update operation fails
        """
        try:
            # Retrieve existing memory
            memory = await self.backend.retrieve(memory_id)
            
            # Update fields if provided
            if content is not None:
                memory.content = content
            if tags is not None:
                memory.tags = tags
            if priority is not None:
                memory.priority = priority
            if status is not None:
                memory.status = status
            if metadata is not None:
                memory.metadata = metadata
            
            # Store updated memory
            await self.backend.update(memory_id, memory)
            logger.info(f"Updated memory with ID {memory_id}")
        except Exception as e:
            if isinstance(e, MemoryNotFoundError):
                logger.warning(f"Memory with ID {memory_id} not found for update")
                raise
            error_msg = f"Failed to update memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> None:
        """
        Delete a memory.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the delete operation fails
        """
        try:
            await self.backend.delete(memory_id)
            logger.info(f"Deleted memory with ID {memory_id}")
        except Exception as e:
            if isinstance(e, MemoryNotFoundError):
                logger.warning(f"Memory with ID {memory_id} not found for deletion")
                raise
            error_msg = f"Failed to delete memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def list_all(self) -> list[MTMMemory]:
        """
        List all memories.
        
        Returns:
            A list of all memories
            
        Raises:
            StorageOperationError: If the list operation fails
        """
        try:
            memories = await self.backend.list_all()
            logger.debug(f"Listed {len(memories)} memories")
            return memories
        except Exception as e:
            error_msg = f"Failed to list memories: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def search(self, query: str = None, tags: list[str] = None, 
                    status: MemoryStatus = None, min_priority: MemoryPriority = None) -> list[MTMMemory]:
        """
        Search for memories based on criteria.
        
        Args:
            query: Text to search for in memory content
            tags: Tags to filter by
            status: Status to filter by
            min_priority: Minimum priority level
            
        Returns:
            A list of matching memories
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            # Get all memories
            all_memories = await self.backend.list_all()
            
            # Filter based on criteria
            filtered_memories = all_memories
            
            if query:
                query = query.lower()
                filtered_memories = [
                    m for m in filtered_memories 
                    if query in json.dumps(m.content).lower()
                ]
            
            if tags:
                filtered_memories = [
                    m for m in filtered_memories 
                    if any(tag in m.tags for tag in tags)
                ]
            
            if status:
                filtered_memories = [
                    m for m in filtered_memories 
                    if m.status == status
                ]
            
            if min_priority:
                filtered_memories = [
                    m for m in filtered_memories 
                    if m.priority.value >= min_priority.value
                ]
            
            logger.debug(f"Search returned {len(filtered_memories)} results")
            return filtered_memories
        except Exception as e:
            error_msg = f"Failed to search memories: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the storage.
        
        Returns:
            Statistics about the storage
            
        Raises:
            StorageOperationError: If the stats operation fails
        """
        try:
            stats = await self.backend.get_stats()
            logger.debug("Retrieved storage statistics")
            return stats
        except Exception as e:
            error_msg = f"Failed to get storage stats: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def archive_memory(self, memory_id: str) -> None:
        """
        Archive a memory.
        
        Args:
            memory_id: The ID of the memory to archive
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the archive operation fails
        """
        try:
            await self.update(memory_id, status=MemoryStatus.ARCHIVED)
            logger.info(f"Archived memory with ID {memory_id}")
        except Exception as e:
            if isinstance(e, MemoryNotFoundError):
                raise
            error_msg = f"Failed to archive memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def consolidate_memory(self, memory_id: str) -> None:
        """
        Mark a memory as consolidated (moved to long-term memory).
        
        Args:
            memory_id: The ID of the memory to consolidate
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the consolidation operation fails
        """
        try:
            await self.update(memory_id, status=MemoryStatus.CONSOLIDATED)
            logger.info(f"Consolidated memory with ID {memory_id}")
        except Exception as e:
            if isinstance(e, MemoryNotFoundError):
                raise
            error_msg = f"Failed to consolidate memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def forget_memory(self, memory_id: str) -> None:
        """
        Mark a memory as forgotten.
        
        Args:
            memory_id: The ID of the memory to forget
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            StorageOperationError: If the forget operation fails
        """
        try:
            await self.update(memory_id, status=MemoryStatus.FORGOTTEN)
            logger.info(f"Marked memory with ID {memory_id} as forgotten")
        except Exception as e:
            if isinstance(e, MemoryNotFoundError):
                raise
            error_msg = f"Failed to forget memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e
    
    async def cleanup(self, max_age_days: int = 30, statuses_to_remove: list[MemoryStatus] = None) -> int:
        """
        Clean up old or forgotten memories.
        
        Args:
            max_age_days: Maximum age in days for memories to keep
            statuses_to_remove: List of statuses to remove (defaults to [FORGOTTEN])
            
        Returns:
            Number of memories removed
            
        Raises:
            StorageOperationError: If the cleanup operation fails
        """
        try:
            if statuses_to_remove is None:
                statuses_to_remove = [MemoryStatus.FORGOTTEN]
            
            all_memories = await self.backend.list_all()
            now = datetime.now()
            cutoff_date = now - timedelta(days=max_age_days)
            
            memories_to_remove = []
            for memory in all_memories:
                # Check if memory is old enough and has a status that should be removed
                if (memory.status in statuses_to_remove or 
                    memory.created_at < cutoff_date):
                    memories_to_remove.append(memory.id)
            
            # Delete memories
            for memory_id in memories_to_remove:
                try:
                    await self.backend.delete(memory_id)
                except MemoryNotFoundError:
                    # Ignore if memory was already deleted
                    pass
            
            logger.info(f"Cleaned up {len(memories_to_remove)} memories")
            return len(memories_to_remove)
        except Exception as e:
            error_msg = f"Failed to clean up memories: {str(e)}"
            logger.error(error_msg)
            raise StorageOperationError(error_msg) from e