"""
Vector Database Backend for Memory Storage

This module provides a vector database backend for the memory storage system,
specifically designed for semantic search and similarity-based retrieval of memories.
It supports storing memory items alongside their vector embeddings for efficient
similarity search operations.

Features:
- Efficient storage and indexing of vector embeddings
- Fast similarity search capabilities
- Support for metadata filtering during search
- Compatibility with various vector database implementations
- Optimized for semantic retrieval use cases
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel

from neuroca.core.exceptions import (
    StorageBackendError,
    StorageInitializationError,
    MemoryNotFoundError,
)
from neuroca.memory.ltm.storage import (
    MemoryItem,
    MemoryMetadata,
    MemoryStatus,
    StorageBackend,
    StorageStats,
)

# Configure logger
logger = logging.getLogger(__name__)


class VectorEntry(BaseModel):
    """A single entry in the vector database."""
    
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = {}


class InMemoryVectorIndex:
    """
    A simple in-memory vector index implementation.
    
    This provides basic vector storage and similarity search functionality.
    For production use, this would be replaced with a more efficient implementation
    backed by a proper vector database like FAISS, Milvus, or similar.
    """
    
    def __init__(self, dimension: int = 768):
        """
        Initialize the in-memory vector index.
        
        Args:
            dimension: Dimensionality of the vectors to store
        """
        self.dimension = dimension
        self.entries: Dict[str, VectorEntry] = {}
        self.vectors: Optional[np.ndarray] = None
        self.ids: List[str] = []
        self._dirty = False
    
    def add(self, entry: VectorEntry) -> None:
        """
        Add an entry to the index.
        
        Args:
            entry: Vector entry to add
        """
        if len(entry.vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(entry.vector)}")
        
        self.entries[entry.id] = entry
        self._dirty = True
    
    def update(self, entry: VectorEntry) -> None:
        """
        Update an existing entry in the index.
        
        Args:
            entry: Vector entry to update
        """
        if entry.id not in self.entries:
            raise KeyError(f"Entry with ID {entry.id} not found")
        
        if len(entry.vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(entry.vector)}")
        
        self.entries[entry.id] = entry
        self._dirty = True
    
    def delete(self, entry_id: str) -> None:
        """
        Delete an entry from the index.
        
        Args:
            entry_id: ID of the entry to delete
        """
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._dirty = True
    
    def get(self, entry_id: str) -> Optional[VectorEntry]:
        """
        Get an entry by ID.
        
        Args:
            entry_id: ID of the entry to retrieve
            
        Returns:
            The vector entry if found, None otherwise
        """
        return self.entries.get(entry_id)
    
    def _rebuild_index(self) -> None:
        """Rebuild the search index."""
        if not self.entries:
            self.vectors = None
            self.ids = []
            self._dirty = False
            return
            
        self.ids = list(self.entries.keys())
        self.vectors = np.array([self.entries[id].vector for id in self.ids])
        self._dirty = False
    
    def search(
        self, 
        query_vector: List[float], 
        k: int = 10, 
        filter_fn: Optional[callable] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Vector to search for
            k: Number of results to return
            filter_fn: Optional function to filter results by metadata
            
        Returns:
            List of (id, similarity) tuples, sorted by similarity (highest first)
        """
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension mismatch: expected {self.dimension}, got {len(query_vector)}")
            
        if self._dirty or self.vectors is None:
            self._rebuild_index()
        
        if not self.entries:
            return []
        
        # Convert query to numpy array
        query_array = np.array(query_vector)
        
        # Compute cosine similarity
        # First normalize vectors for cosine similarity
        norm_query = query_array / np.linalg.norm(query_array)
        norm_vectors = self.vectors / np.linalg.norm(self.vectors, axis=1, keepdims=True)
        similarities = np.dot(norm_vectors, norm_query)
        
        # Sort by similarity
        indices = np.argsort(similarities)[::-1]  # Descending order
        
        # Filter results if filter_fn is provided
        results = []
        for idx in indices:
            entry_id = self.ids[idx]
            entry = self.entries[entry_id]
            
            if filter_fn is None or filter_fn(entry.metadata):
                results.append((entry_id, float(similarities[idx])))
                if len(results) >= k:
                    break
        
        return results
    
    def count(self) -> int:
        """
        Get the number of entries in the index.
        
        Returns:
            Number of entries in the index
        """
        return len(self.entries)


class VectorStorageBackend(StorageBackend):
    """
    Vector database implementation of the storage backend.
    
    This implementation provides:
    - Storage of memory items with vector embeddings
    - Fast semantic similarity search
    - Metadata filtering
    - Integration with the memory system
    """
    
    def __init__(
        self,
        dimension: int = 768,
        similarity_threshold: float = 0.75,
        index_path: Optional[str] = None,
        **config
    ):
        """
        Initialize the vector storage backend.
        
        Args:
            dimension: Dimensionality of the vectors to store
            similarity_threshold: Minimum similarity score for search results
            index_path: Optional path to persist the index
            **config: Additional configuration options
        """
        self.dimension = dimension
        self.similarity_threshold = similarity_threshold
        self.index_path = index_path
        self._config = config
        self._index = InMemoryVectorIndex(dimension=dimension)
        self._memory_metadata: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """
        Initialize the vector storage backend.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Load index from disk if path is provided
            if self.index_path and os.path.exists(self.index_path):
                await self._load_index()
            
            self._initialized = True
            logger.info(f"Initialized vector storage backend with dimension {self.dimension}")
        except Exception as e:
            error_msg = f"Failed to initialize vector storage backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the backend is initialized before use."""
        if not self._initialized:
            await self.initialize()
    
    async def _load_index(self) -> None:
        """Load the index from disk."""
        if not self.index_path:
            return
            
        try:
            if not os.path.exists(self.index_path):
                logger.warning(f"Index file {self.index_path} not found, starting with empty index")
                return
                
            with open(self.index_path, 'r') as f:
                data = json.load(f)
                
            # Re-create index
            self._index = InMemoryVectorIndex(dimension=self.dimension)
            
            # Load entries
            for entry_data in data.get("entries", []):
                entry = VectorEntry(**entry_data)
                self._index.add(entry)
                
            # Load memory metadata
            self._memory_metadata = data.get("memory_metadata", {})
            
            logger.info(f"Loaded vector index from {self.index_path} with {self._index.count()} entries")
        except Exception as e:
            logger.error(f"Failed to load index from {self.index_path}: {str(e)}")
            # Continue with empty index
            self._index = InMemoryVectorIndex(dimension=self.dimension)
    
    async def _save_index(self) -> None:
        """Save the index to disk."""
        if not self.index_path:
            return
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Prepare data for serialization
            data = {
                "entries": [entry.dict() for entry in self._index.entries.values()],
                "memory_metadata": self._memory_metadata
            }
            
            # Write to file
            with open(self.index_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved vector index to {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to save index to {self.index_path}: {str(e)}")
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item with its embedding in the vector database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            The ID of the stored memory
            
        Raises:
            StorageBackendError: If the memory cannot be stored
        """
        try:
            await self._ensure_initialized()
            
            memory_id = memory_item.id
            
            # Check if memory has embedding
            if not memory_item.embedding:
                raise StorageBackendError(f"Memory item {memory_id} does not have an embedding")
            
            # Create vector entry
            vector_entry = VectorEntry(
                id=memory_id,
                vector=memory_item.embedding,
                metadata={
                    "summary": memory_item.summary,
                    "status": memory_item.metadata.status.value if memory_item.metadata and memory_item.metadata.status else "active",
                    "created_at": memory_item.metadata.created_at.isoformat() if memory_item.metadata and memory_item.metadata.created_at else datetime.now().isoformat(),
                    "tags": memory_item.metadata.tags if memory_item.metadata else [],
                    "importance": memory_item.metadata.importance if memory_item.metadata else 0.5,
                }
            )
            
            # Store in index
            if memory_id in self._index.entries:
                self._index.update(vector_entry)
            else:
                self._index.add(vector_entry)
            
            # Store additional metadata
            self._memory_metadata[memory_id] = {
                "content_summary": memory_item.summary or "No summary available",
                "status": memory_item.metadata.status.value if memory_item.metadata and memory_item.metadata.status else "active",
                "created_at": memory_item.metadata.created_at.isoformat() if memory_item.metadata and memory_item.metadata.created_at else datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0,
            }
            
            # Save index to disk if path is provided
            if self.index_path:
                await self._save_index()
            
            logger.debug(f"Stored memory with ID {memory_id} in vector database")
            return memory_id
            
        except Exception as e:
            error_msg = f"Failed to store memory in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID from the vector database.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The memory item if found, None otherwise
            
        Raises:
            StorageBackendError: If there's an error retrieving the memory
        """
        try:
            await self._ensure_initialized()
            
            # Check if memory exists in index
            vector_entry = self._index.get(memory_id)
            if not vector_entry:
                logger.debug(f"Memory with ID {memory_id} not found in vector database")
                return None
            
            # Get metadata
            metadata_dict = self._memory_metadata.get(memory_id, {})
            
            # Update access stats
            metadata_dict["last_accessed"] = datetime.now().isoformat()
            metadata_dict["access_count"] = metadata_dict.get("access_count", 0) + 1
            self._memory_metadata[memory_id] = metadata_dict
            
            # Create metadata object
            metadata = MemoryMetadata(
                status=MemoryStatus(vector_entry.metadata.get("status", "active")),
                created_at=datetime.fromisoformat(vector_entry.metadata.get("created_at", datetime.now().isoformat())),
                tags=vector_entry.metadata.get("tags", []),
                importance=vector_entry.metadata.get("importance", 0.5),
                last_accessed=datetime.fromisoformat(metadata_dict.get("last_accessed", datetime.now().isoformat())),
                access_count=metadata_dict.get("access_count", 0),
            )
            
            # Create memory item
            memory_item = MemoryItem(
                id=memory_id,
                content={},  # Vector database doesn't store full content
                summary=vector_entry.metadata.get("summary", ""),
                embedding=vector_entry.vector,
                metadata=metadata,
            )
            
            # Save updated metadata
            if self.index_path:
                await self._save_index()
            
            logger.debug(f"Retrieved memory with ID {memory_id} from vector database")
            return memory_item
            
        except Exception as e:
            error_msg = f"Failed to retrieve memory with ID {memory_id} from vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the vector database.
        
        Args:
            memory_item: The memory item to update
            
        Returns:
            True if the update was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error updating the memory
        """
        try:
            await self._ensure_initialized()
            
            memory_id = memory_item.id
            
            # Check if memory exists
            if memory_id not in self._index.entries:
                logger.warning(f"Memory with ID {memory_id} not found for update in vector database")
                return False
            
            # Just use store for simplicity (it handles updates)
            await self.store(memory_item)
            logger.debug(f"Updated memory with ID {memory_id} in vector database")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update memory with ID {memory_item.id} in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the vector database.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            True if the deletion was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error deleting the memory
        """
        try:
            await self._ensure_initialized()
            
            # Check if memory exists
            if memory_id not in self._index.entries:
                logger.warning(f"Memory with ID {memory_id} not found for deletion in vector database")
                return False
            
            # Delete from index
            self._index.delete(memory_id)
            
            # Delete metadata
            if memory_id in self._memory_metadata:
                del self._memory_metadata[memory_id]
            
            # Save changes
            if self.index_path:
                await self._save_index()
            
            logger.debug(f"Deleted memory with ID {memory_id} from vector database")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete memory with ID {memory_id} from vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: int = 10,
        offset: int = 0,
        query_embedding: Optional[List[float]] = None,
    ) -> List[MemoryItem]:
        """
        Search for memory items in the vector database by semantic similarity.
        
        Args:
            query: The search query (used only for logging, not actual search)
            filters: Optional filters to apply to the search
            limit: Maximum number of results to return
            offset: Number of results to skip
            query_embedding: The embedding vector to search for (required)
            
        Returns:
            List of memory items matching the search criteria
            
        Raises:
            StorageBackendError: If there's an error during search
        """
        try:
            await self._ensure_initialized()
            
            # Query embedding is required for vector search
            if not query_embedding:
                raise StorageBackendError("Query embedding is required for vector search")
            
            # Create filter function based on provided filters
            filter_fn = None
            if filters:
                def filter_fn(metadata: Dict[str, Any]) -> bool:
                    for key, value in filters.items():
                        if key == "status" and value:
                            status_val = value if isinstance(value, str) else value.value
                            if metadata.get("status") != status_val:
                                return False
                        elif key == "importance" and value is not None:
                            if metadata.get("importance", 0) < float(value):
                                return False
                        elif key == "tags" and value:
                            if not any(tag in metadata.get("tags", []) for tag in value):
                                return False
                        elif key == "created_after" and value:
                            created_at = metadata.get("created_at")
                            if created_at and datetime.fromisoformat(created_at) < value:
                                return False
                        elif key == "created_before" and value:
                            created_at = metadata.get("created_at")
                            if created_at and datetime.fromisoformat(created_at) > value:
                                return False
                    return True
            
            # Search for similar vectors
            results = self._index.search(
                query_vector=query_embedding,
                k=limit + offset,  # We'll apply offset manually after filtering
                filter_fn=filter_fn,
            )
            
            # Apply offset
            results = results[offset:]
            
            # Get memory items for results
            memories = []
            for memory_id, similarity in results:
                # Skip results below threshold
                if similarity < self.similarity_threshold:
                    continue
                    
                # Get the memory item
                memory = await self.get(memory_id)
                if memory:
                    memories.append(memory)
            
            logger.debug(f"Search returned {len(memories)} results from vector database")
            return memories
            
        except Exception as e:
            error_msg = f"Failed to search memories in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the vector database storage.
        
        Returns:
            Statistics about the storage
            
        Raises:
            StorageBackendError: If there's an error retrieving statistics
        """
        try:
            await self._ensure_initialized()
            
            # Count entries by status
            active_count = 0
            archived_count = 0
            
            for entry in self._index.entries.values():
                status = entry.metadata.get("status", "active")
                if status == "active":
                    active_count += 1
                elif status == "archived":
                    archived_count += 1
            
            # Get total count
            total_count = self._index.count()
            
            # Estimate size (rough approximation)
            size_bytes = 0
            for entry in self._index.entries.values():
                # Vector size (assuming float32)
                size_bytes += len(entry.vector) * 4
                # Metadata size (rough estimate)
                size_bytes += len(json.dumps(entry.metadata))
            
            # Get last access time
            last_access = None
            for metadata in self._memory_metadata.values():
                last_accessed = metadata.get("last_accessed")
                if last_accessed:
                    last_accessed_dt = datetime.fromisoformat(last_accessed)
                    if last_access is None or last_accessed_dt > last_access:
                        last_access = last_accessed_dt
            
            stats = StorageStats(
                total_memories=total_count,
                active_memories=active_count,
                archived_memories=archived_count,
                total_size_bytes=size_bytes,
                last_access_time=last_access,
                last_write_time=datetime.now(),  # We don't track writes separately
            )
            
            logger.debug("Retrieved storage statistics from vector database")
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get storage statistics from vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
