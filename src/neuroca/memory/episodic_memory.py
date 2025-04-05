"""
Episodic memory functionality for the NCA system.

This module handles episodic memories - memories of specific events, times, and places.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from neuroca.core.memory.interfaces import MemoryChunk, MemorySystem  # Import interface


# Placeholder for MemoryChunk implementation
class EpisodicMemoryChunk(MemoryChunk[str]): # Assuming content is string for now
    def __init__(self, chunk_id: str, content: str, timestamp: datetime, location: Optional[str],
                 context: dict[str, Any], importance: float, last_accessed: datetime, retrieval_count: int):
        self._id = chunk_id
        self._content = content
        self._timestamp = timestamp
        self._location = location
        self._context = context
        self._importance = importance
        self._last_accessed = last_accessed
        self._retrieval_count = retrieval_count
        # Activation might depend on importance, recency, retrieval count
        self._activation = self._calculate_activation()

    def _calculate_activation(self) -> float:
        # Placeholder activation logic
        recency = (datetime.now() - self.last_accessed).total_seconds()
        # Simple decay + importance + retrieval boost
        activation = self.importance * (0.99 ** (recency / 3600)) + (self.retrieval_count * 0.01)
        return max(0.0, min(1.0, activation))

    @property
    def id(self) -> str: return self._id
    @property
    def content(self) -> str: return self._content
    @property
    def activation(self) -> float: return self._activation
    @property
    def created_at(self) -> datetime: return self._timestamp
    @property
    def last_accessed(self) -> datetime: return self._last_accessed
    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "location": self._location,
            "context": self._context,
            "importance": self._importance,
            "retrieval_count": self._retrieval_count,
            "timestamp": self._timestamp.isoformat() # Store original timestamp
        }

    def update_activation(self, value: Optional[float] = None) -> None:
        self._last_accessed = datetime.now()
        self._retrieval_count += 1
        if value is not None:
            self._activation = value
        else:
            self._activation = self._calculate_activation()


class EpisodicMemory(MemorySystem): # Inherit from MemorySystem
    """Class managing the episodic memory system."""
    
    # In-memory storage for simplicity in this example
    _storage: dict[str, EpisodicMemoryChunk] = {}

    def __init__(self, config: Optional[dict[str, Any]] = None): # Accept config
        """
        Initialize the episodic memory system.
        
        Args:
            config: Configuration dictionary (e.g., storage backend, limits). Ignored for now.
        """
        self.config = config or {}
        # Initialize storage (clears previous state if any)
        EpisodicMemory._storage = {}

    @property
    def name(self) -> str:
        return "episodic_memory"

    @property
    def capacity(self) -> Optional[int]:
        # Assuming unlimited capacity for this simple implementation
        return None

    def store(self, content: Any, **metadata) -> str: # Implement store
        """
        Store content as an episodic memory.
        
        Args:
            content: The main content of the memory (expected str)
            **metadata: Must include timestamp, location, context, importance.
            
        Returns:
            str: The ID of the stored memory chunk.
        """
        chunk_id = str(uuid.uuid4())
        now = datetime.now()
        
        chunk = EpisodicMemoryChunk(
            chunk_id=chunk_id,
            content=str(content), # Ensure content is string
            timestamp=metadata.get("timestamp", now),
            location=metadata.get("location"),
            context=metadata.get("context", {}),
            importance=metadata.get("importance", 0.5),
            last_accessed=now,
            retrieval_count=0
        )
        EpisodicMemory._storage[chunk_id] = chunk
        return chunk_id

    def retrieve(self, query: Any, limit: int = 10, **parameters) -> list[MemoryChunk]: # Implement retrieve
        """
        Retrieve episodic memories matching the query.
        Very basic stub implementation: returns most recent memories.
        A real implementation would use embedding search, keyword matching, etc.
        
        Args:
            query: Search parameters (ignored in this stub)
            limit: Maximum number of results
            **parameters: Additional parameters (ignored)
            
        Returns:
            List[MemoryChunk]: List of matching memory chunks
        """
        # Sort by last accessed time (descending) as a simple relevance proxy
        sorted_chunks = sorted(
            EpisodicMemory._storage.values(),
            key=lambda chunk: chunk.last_accessed,
            reverse=True
        )
        
        results = sorted_chunks[:limit]
        
        # Update activation for retrieved items
        for chunk in results:
            chunk.update_activation()
            
        return results # Return list of MemoryChunk objects

    def retrieve_by_id(self, chunk_id: str) -> Optional[MemoryChunk]: # Implement retrieve_by_id
        """
        Retrieve a specific memory chunk by its ID.
        """
        chunk = EpisodicMemory._storage.get(chunk_id)
        if chunk:
            chunk.update_activation()
        return chunk

    def forget(self, chunk_id: str) -> bool: # Implement forget
        """
        Remove content from episodic memory.
        """
        if chunk_id in EpisodicMemory._storage:
            del EpisodicMemory._storage[chunk_id]
            return True
        return False

    def clear(self) -> None: # Implement clear
        """Remove all content from episodic memory."""
        EpisodicMemory._storage.clear()

    def get_statistics(self) -> dict[str, Any]: # Implement get_statistics
        """Get statistics about episodic memory."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "current_items": len(EpisodicMemory._storage),
        }

    def dump(self) -> list[dict[str, Any]]: # Implement dump
        """Dump all content from episodic memory."""
        # Need proper serialization for MemoryChunk
        return [chunk.metadata for chunk in EpisodicMemory._storage.values()] # Placeholder dump

# Remove old module-level functions if using factory pattern
# def store_episodic_memory(...) ...
# def retrieve_episodic_memories(...) ...
