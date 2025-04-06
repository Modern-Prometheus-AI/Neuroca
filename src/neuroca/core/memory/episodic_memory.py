"""
Episodic Memory implementation for the NeuroCognitive Architecture.

This module implements a biologically-inspired episodic memory system with:
- Temporal context for each memory (when it occurred)
- Emotional salience tagging for prioritized retrieval
- Sequence tracking for reconstructing event timelines
- Adaptive decay based on emotional importance
"""

import time
import uuid
from datetime import datetime
from typing import Any, Optional, TypeVar

from neuroca.core.memory.interfaces import MemoryChunk, MemorySystem

T = TypeVar('T')

class EpisodicMemoryChunk(MemoryChunk[T]):
    """
    Memory chunk for episodic memory with temporal context and emotional salience.
    """
    
    def __init__(
        self, 
        content: T, 
        temporal_context: dict[str, Any] = None,
        emotional_salience: float = 0.5,
        metadata: dict[str, Any] = None
    ):
        self._id = str(uuid.uuid4())
        self._content = content
        self._activation = 1.0  # Start with full activation
        self._created_at = datetime.now()
        self._last_accessed = self._created_at
        
        # Episodic-specific properties
        self._temporal_context = temporal_context or {
            "timestamp": self._created_at.timestamp(),
            "sequence_id": int(time.time() * 1000),  # Millisecond precision
        }
        
        # Ensure emotional_salience is between 0-1
        self._emotional_salience = max(0.0, min(1.0, emotional_salience))
        
        # Combine provided metadata with episodic properties
        self._metadata = metadata or {}
        self._metadata.update({
            "emotional_salience": self._emotional_salience,
            "temporal_context": self._temporal_context,
        })
    
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
    
    @property
    def temporal_context(self) -> dict[str, Any]:
        return self._temporal_context
    
    @property
    def emotional_salience(self) -> float:
        return self._emotional_salience
    
    def update_activation(self, value: Optional[float] = None) -> None:
        """Update the activation level of this chunk."""
        if value is not None:
            self._activation = max(0.0, min(1.0, value))  # Clamp between 0 and 1
        self._last_accessed = datetime.now()
    
    def update_emotional_salience(self, value: float) -> None:
        """Update the emotional salience of this memory."""
        self._emotional_salience = max(0.0, min(1.0, value))
        self._metadata["emotional_salience"] = self._emotional_salience


class EpisodicMemory(MemorySystem):
    """
    Episodic Memory system for storing experiences with temporal context and emotional salience.
    
    Features:
    - Unlimited capacity (unlike working memory)
    - Emotional salience affects retrieval priority and decay rate
    - Temporal context enables sequence reconstruction
    - More robust than working memory but slower to access
    """
    
    def __init__(self, decay_rate: float = 0.01):
        """
        Initialize episodic memory.
        
        Args:
            decay_rate: Base rate of memory decay (per time unit)
        """
        self._name = "episodic_memory"
        self._capacity = None  # Unlimited capacity
        self._chunks: dict[str, EpisodicMemoryChunk] = {}
        self._decay_rate = decay_rate
        self._last_decay_time = time.time()
        
        # Temporal sequence tracking
        self._sequence_map: dict[int, list[str]] = {}  # Maps sequence IDs to chunk IDs
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def capacity(self) -> Optional[int]:
        return self._capacity  # None means unlimited
    
    def store(
        self, 
        content: Any, 
        emotional_salience: float = 0.5,
        temporal_context: dict[str, Any] = None,
        **metadata
    ) -> str:
        """
        Store an experience in episodic memory.
        
        Args:
            content: The memory content
            emotional_salience: How emotionally significant this memory is (0-1)
            temporal_context: Additional temporal information
            **metadata: Any additional metadata
        """
        # Apply decay to existing chunks first
        self._apply_decay()
        
        # Create a new episodic memory chunk
        chunk = EpisodicMemoryChunk(
            content, 
            temporal_context=temporal_context,
            emotional_salience=emotional_salience,
            metadata=metadata
        )
        
        # Store the chunk
        self._chunks[chunk.id] = chunk
        
        # Update sequence tracking
        seq_id = chunk.temporal_context.get("sequence_id")
        if seq_id:
            if seq_id not in self._sequence_map:
                self._sequence_map[seq_id] = []
            self._sequence_map[seq_id].append(chunk.id)
        
        return chunk.id
    
    def retrieve(
        self, 
        query: Any, 
        limit: int = 10, 
        min_emotional_salience: float = 0.0,
        temporal_range: tuple[Optional[float], Optional[float]] = (None, None),
        **parameters
    ) -> list[MemoryChunk]:
        """
        Retrieve episodic memories based on query and filters.
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_emotional_salience: Minimum emotional significance (0-1)
            temporal_range: (start_time, end_time) as timestamps
            **parameters: Additional parameters
        """
        self._apply_decay()
        
        start_time, end_time = temporal_range
        query_str = str(query).lower()
        results = []
        
        # First pass: find matching chunks
        for chunk in self._chunks.values():
            content_str = str(chunk.content).lower()
            
            # Basic content matching
            if query_str in content_str:
                # Check emotional salience filter
                if chunk.emotional_salience < min_emotional_salience:
                    continue
                
                # Check temporal range if specified
                timestamp = chunk.temporal_context.get("timestamp")
                if timestamp:
                    if start_time and timestamp < start_time:
                        continue
                    if end_time and timestamp > end_time:
                        continue
                
                # Boost activation when retrieved
                boost = 0.2 * (1 + chunk.emotional_salience)  # Emotional memories get bigger boost
                chunk.update_activation(min(1.0, chunk.activation + boost))
                results.append(chunk)
        
        # Calculate relevance score for sorting (combination of activation and emotional salience)
        def relevance_score(chunk):
            return 0.7 * chunk.activation + 0.3 * chunk.emotional_salience
        
        # Sort by relevance score and limit results
        results.sort(key=relevance_score, reverse=True)
        return results[:limit]
    
    def retrieve_by_id(self, chunk_id: str) -> Optional[MemoryChunk]:
        """Retrieve a specific episodic memory by ID."""
        self._apply_decay()
        
        chunk = self._chunks.get(chunk_id)
        if chunk:
            # Boost activation when retrieved
            boost = 0.2 * (1 + chunk.emotional_salience)
            chunk.update_activation(min(1.0, chunk.activation + boost))
        return chunk
    
    def retrieve_sequence(self, sequence_id: int) -> list[MemoryChunk]:
        """Retrieve all memories that belong to a particular sequence."""
        self._apply_decay()
        
        if sequence_id not in self._sequence_map:
            return []
        
        chunks = []
        for chunk_id in self._sequence_map[sequence_id]:
            chunk = self._chunks.get(chunk_id)
            if chunk:
                # Boost activation when retrieved
                boost = 0.1 * (1 + chunk.emotional_salience)
                chunk.update_activation(min(1.0, chunk.activation + boost))
                chunks.append(chunk)
        
        # Sort by timestamp to reconstruct sequence
        chunks.sort(key=lambda x: x.temporal_context.get("timestamp", 0))
        return chunks
    
    def forget(self, chunk_id: str) -> bool:
        """Explicitly forget a memory."""
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            return False
        
        # Remove from main storage
        del self._chunks[chunk_id]
        
        # Remove from sequence tracking
        seq_id = chunk.temporal_context.get("sequence_id")
        if seq_id and seq_id in self._sequence_map:
            if chunk_id in self._sequence_map[seq_id]:
                self._sequence_map[seq_id].remove(chunk_id)
            # Clean up empty sequences
            if not self._sequence_map[seq_id]:
                del self._sequence_map[seq_id]
        
        return True
    
    def clear(self) -> None:
        """Clear all episodic memories."""
        self._chunks.clear()
        self._sequence_map.clear()

    def get_all_items(self) -> list[MemoryChunk]:
        """Get all items currently in episodic memory."""
        return list(self._chunks.values())
    
    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the episodic memory state."""
        if not self._chunks:
            return {
                "name": self.name,
                "count": 0,
                "average_activation": 0,
                "average_emotional_salience": 0,
                "oldest_memory_age": 0,
                "newest_memory_age": 0,
                "sequence_count": 0,
            }
        
        now = datetime.now().timestamp()
        oldest = min(c.created_at.timestamp() for c in self._chunks.values())
        newest = max(c.created_at.timestamp() for c in self._chunks.values())
        
        return {
            "name": self.name,
            "count": len(self._chunks),
            "average_activation": sum(c.activation for c in self._chunks.values()) / len(self._chunks),
            "average_emotional_salience": sum(c.emotional_salience for c in self._chunks.values()) / len(self._chunks),
            "oldest_memory_age": now - oldest,
            "newest_memory_age": now - newest,
            "sequence_count": len(self._sequence_map),
        }
    
    def dump(self) -> list[dict[str, Any]]:
        """Dump all episodic memories for consolidation or inspection."""
        # Apply decay before dumping to ensure activations are current
        self._apply_decay() 
        return [
            {
                "id": chunk.id,
                "content": chunk.content,
                "activation": chunk.activation,
                "created_at": chunk.created_at.isoformat(), # Serialize datetime
                "last_accessed": chunk.last_accessed.isoformat(), # Serialize datetime
                # Include all metadata, including emotional_salience and temporal_context
                "metadata": chunk.metadata, 
            }
            for chunk in self._chunks.values()
        ]
    
    def _apply_decay(self) -> None:
        """
        Apply time-based decay to all episodic memories.
        
        Decay is influenced by emotional salience - more emotional memories decay slower.
        """
        current_time = time.time()
        time_elapsed = current_time - self._last_decay_time
        
        if time_elapsed < 0.1:  # Only decay if enough time has passed
            return
        
        decay_factor = self._decay_rate * time_elapsed
        
        # Apply decay to all chunks
        chunks_to_remove = []
        for chunk_id, chunk in self._chunks.items():
            # --- Simplified Decay Logic for Testing ---
            # Simple linear decay based on base rate and time elapsed
            # Emotional modifier: Slower decay for higher salience
            emotional_modifier = 1.0 - (0.9 * chunk.emotional_salience) # 0.1x decay at salience=1.0
            decay_amount = decay_factor * emotional_modifier
            new_activation = chunk.activation - decay_amount
            # --- End Simplified Logic ---

            # If activation falls below threshold, mark for removal only if not emotional
            # Highly emotional memories resist being completely forgotten
            if new_activation < 0.05 and chunk.emotional_salience < 0.7:
                chunks_to_remove.append(chunk_id)
            else:
                chunk.update_activation(new_activation)
        
        # Remove low-activation chunks (forgotten memories)
        for chunk_id in chunks_to_remove:
            self.forget(chunk_id)
        
        self._last_decay_time = current_time
        for chunk_id in chunks_to_remove:
            self.forget(chunk_id)
        
        self._last_decay_time = current_time
