"""
Working Memory implementation for the NeuroCognitive Architecture.

This module implements a biologically-inspired working memory system with:
- Limited capacity (7±2 chunks) following Miller's Law
- Activation decay over time
- Recency effects for retrieval priority
- Displacement of least active items when capacity is reached
"""

import time
import uuid
from datetime import datetime
from typing import Any, Optional, TypeVar

from neuroca.core.memory.interfaces import MemoryChunk, MemorySystem

T = TypeVar('T')

class WorkingMemoryChunk(MemoryChunk[T]):
    """Concrete implementation of a memory chunk for working memory."""
    
    def __init__(self, content: T, metadata: dict[str, Any] = None):
        self._id = str(uuid.uuid4())
        self._content = content
        self._activation = 1.0  # Start with full activation
        self._created_at = datetime.now()
        self._last_accessed = self._created_at
        self._metadata = metadata or {}
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def content(self) -> T:
        return self._content
    
    @property
    def activation(self) -> float:
        return self._activation
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def last_accessed(self) -> datetime:
        return self._last_accessed
    
    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata
    
    def update_activation(self, value: Optional[float] = None) -> None:
        """Update the activation level of this chunk."""
        if value is not None:
            self._activation = max(0.0, min(1.0, value))  # Clamp between 0 and 1
        self._last_accessed = datetime.now()


class WorkingMemory(MemorySystem):
    """Working Memory implementation with biological constraints (7±2 chunks)."""
    
    def __init__(self, capacity: int = 7):
        """
        Initialize working memory with Miller's capacity constraint.
        
        Args:
            capacity: The maximum number of chunks this memory can hold (default: 7)
        """
        # Ensure capacity is within biologically plausible range (5-9 chunks)
        if capacity < 5 or capacity > 9:
            raise ValueError(f"Working memory capacity must be between 5-9 chunks (got {capacity})")
        
        self._name = "working_memory"
        self._capacity = capacity
        self._chunks: dict[str, WorkingMemoryChunk] = {}
        self._decay_rate = 0.1  # Activation decays by 10% per time unit
        self._last_decay_time = time.time()
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def capacity(self) -> Optional[int]:
        return self._capacity
    
    def store(self, content: Any, **metadata) -> str:
        """
        Store content in working memory, respecting capacity constraints.
        
        If at capacity, the least activated chunk is forgotten.
        """
        # Apply decay to existing chunks first
        self._apply_decay()
        
        # Create a new memory chunk
        chunk = WorkingMemoryChunk(content, metadata)
        
        # If at capacity, remove least active chunk
        if len(self._chunks) >= self._capacity:
            least_active_id = self._get_least_active_chunk_id()
            if least_active_id:
                del self._chunks[least_active_id]
        
        # Store the new chunk
        self._chunks[chunk.id] = chunk
        return chunk.id
    
    def retrieve(self, query: Any, limit: int = 10, **parameters) -> list[MemoryChunk]:
        """
        Retrieve chunks from working memory based on the query.
        
        Simple implementation that compares string representation for now.
        In a real system, this would use embeddings or other similarity measures.
        """
        self._apply_decay()
        
        results = []
        query_str = str(query).lower()
        
        for chunk in self._chunks.values():
            content_str = str(chunk.content).lower()
            if query_str in content_str:
                # Boost activation when retrieved (recency effect)
                chunk.update_activation(min(1.0, chunk.activation + 0.2))
                results.append(chunk)
                
        # Sort by activation (highest first) and limit results
        results.sort(key=lambda x: x.activation, reverse=True)
        return results[:limit]
    
    def retrieve_by_id(self, chunk_id: str) -> Optional[MemoryChunk]:
        """Retrieve a specific chunk by ID."""
        self._apply_decay()
        
        chunk = self._chunks.get(chunk_id)
        if chunk:
            # Boost activation when retrieved
            chunk.update_activation(min(1.0, chunk.activation + 0.2))
        return chunk
    
    def forget(self, chunk_id: str) -> bool:
        """Explicitly forget a chunk from working memory."""
        if chunk_id in self._chunks:
            del self._chunks[chunk_id]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all chunks from working memory."""
        self._chunks.clear()
    
    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the working memory state."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "used": len(self._chunks),
            "percent_full": len(self._chunks) / self.capacity * 100 if self.capacity else 0,
            "average_activation": sum(c.activation for c in self._chunks.values()) / len(self._chunks) if self._chunks else 0,
        }
    
    def dump(self) -> list[dict[str, Any]]:
        """Dump all chunks for inspection."""
        return [
            {
                "id": chunk.id,
                "content": chunk.content,
                "activation": chunk.activation,
                "created_at": chunk.created_at.isoformat(),
                "last_accessed": chunk.last_accessed.isoformat(),
                "metadata": chunk.metadata,
            }
            for chunk in self._chunks.values()
        ]
    
    def _apply_decay(self) -> None:
        """Apply time-based decay to all chunks in working memory."""
        current_time = time.time()
        time_elapsed = current_time - self._last_decay_time
        
        if time_elapsed < 0.1:  # Only decay if enough time has passed
            return
        
        decay_factor = self._decay_rate * time_elapsed
        
        # Apply decay to all chunks
        chunks_to_remove = []
        for chunk_id, chunk in self._chunks.items():
            new_activation = chunk.activation * (1 - decay_factor)
            
            # If activation falls below threshold, mark for removal
            if new_activation < 0.1:
                chunks_to_remove.append(chunk_id)
            else:
                chunk.update_activation(new_activation)
        
        # Remove chunks with too low activation
        for chunk_id in chunks_to_remove:
            del self._chunks[chunk_id]
        
        self._last_decay_time = current_time
    
    def _get_least_active_chunk_id(self) -> Optional[str]:
        """Get the ID of the least active chunk in memory."""
        if not self._chunks:
            return None
            
        return min(self._chunks.items(), key=lambda x: x[1].activation)[0]

# Registration will be handled by factory.py 