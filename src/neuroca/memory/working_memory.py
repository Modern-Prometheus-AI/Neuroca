"""
Working memory functionality for the NCA system.

This module implements the working memory component, which handles temporarily active
information that's currently being processed by the system.
"""

from collections import deque
from datetime import datetime
from typing import Any, Optional

from neuroca.core.memory.interfaces import MemoryChunk, MemorySystem  # Import interface


# Placeholder for MemoryChunk implementation if needed
class WorkingMemoryChunk(MemoryChunk[Any]):
    def __init__(self, item_id: str, content: Any, metadata: dict[str, Any], activation_time: datetime):
        self._id = item_id
        self._content = content
        self._metadata = metadata
        self._created_at = activation_time # Assuming creation time is activation time for WM
        self._last_accessed = activation_time
        self._activation = 1.0 # Initial activation
        # Define decay rate (e.g., half-life in seconds)
        self.DECAY_HALF_LIFE_SECONDS = 5.0 # Activation halves every 5 seconds

    @property
    def id(self) -> str: return self._id
    @property
    def content(self) -> Any: return self._content
    @property
    def activation(self) -> float: return self._activation # Needs decay logic
    @property
    def created_at(self) -> datetime: return self._created_at
    @property
    def last_accessed(self) -> datetime: return self._last_accessed
    @property
    def metadata(self) -> dict[str, Any]: return self._metadata

    def update_activation(self, value: Optional[float] = None) -> None:
        if value is not None:
            self._activation = value
        now = datetime.now()
        time_elapsed = (now - self._last_accessed).total_seconds()

        # Calculate decay factor based on half-life
        # activation = initial * (0.5 ^ (time_elapsed / half_life))
        if self.DECAY_HALF_LIFE_SECONDS > 0:
             decay_factor = 0.5 ** (time_elapsed / self.DECAY_HALF_LIFE_SECONDS)
             decayed_activation = self._activation * decay_factor
        else:
             decayed_activation = self._activation # No decay if half-life is zero or less

        # If an explicit value is provided (e.g., boost/reset on retrieval), use it
        if value is not None:
            self._activation = value
        else:
            # Otherwise, just apply decay
            self._activation = decayed_activation

        # Clamp activation
        self._activation = max(0.0, min(1.0, self._activation))

        # Update last accessed time *after* calculations
        self._last_accessed = now


class WorkingMemory(MemorySystem): # Inherit from MemorySystem
    """Class managing the working memory system."""
    
    def __init__(self, config: Optional[dict[str, Any]] = None): # Accept config dict
        """
        Initialize the working memory system.
        
        Args:
            config: Configuration dictionary. Expected keys: 'capacity'.
        """
        config = config or {}
        self._capacity = config.get('capacity', 7)
        self.items: deque[WorkingMemoryChunk] = deque(maxlen=self._capacity) # Store MemoryChunk objects
        # self.activated_at is now part of the MemoryChunk

    @property
    def name(self) -> str:
        return "working_memory"

    @property
    def capacity(self) -> Optional[int]:
        return self._capacity

    def store(self, content: Any, **metadata) -> str: # Implement store method
        """
        Store content in working memory.
        
        Args:
            content: The content to store
            **metadata: Additional metadata. Must include 'id'.
            
        Returns:
            str: The ID of the stored memory chunk
            
        Raises:
            ValueError: If 'id' is not provided in metadata.
        """
        item_id = metadata.pop('id', None)
        if not item_id:
            raise ValueError("An 'id' must be provided in metadata to store in working memory.")

        # Check if item already exists and update it
        for i, existing_chunk in enumerate(self.items):
            if existing_chunk.id == item_id:
                # Update existing chunk - create new object or update in place?
                # Creating new for simplicity, assuming metadata might change
                new_chunk = WorkingMemoryChunk(item_id, content, metadata, datetime.now())
                # Need to handle deque update carefully if not using maxlen side effect
                # For now, let's remove and append to update position/activation implicitly
                del self.items[i]
                self.items.append(new_chunk)
                return item_id

        # If working memory is full, deque's maxlen handles removal of the oldest item
            
        # Add the new item
        new_chunk = WorkingMemoryChunk(item_id, content, metadata, datetime.now())
        self.items.append(new_chunk)
        return item_id

    def retrieve(self, query: Any, limit: int = 1, **parameters) -> list[MemoryChunk]:
        """
        Retrieve content from working memory based on ID query.
        Simple implementation: query is assumed to be the item_id.
        """
        if not isinstance(query, str): # Basic check, could be more robust
             return []
        
        item_id = query
        chunk = self.retrieve_by_id(item_id)
        return [chunk] if chunk else []

    def retrieve_by_id(self, chunk_id: str) -> Optional[MemoryChunk]:
        """
        Retrieve a specific memory chunk by its ID.
        
        Args:
            chunk_id: The ID of the memory chunk to retrieve
            
        Returns:
            Optional[MemoryChunk]: The retrieved memory chunk, or None if not found
        """
        for chunk in self.items:
            if chunk.id == chunk_id:
                chunk.update_activation() # Update last accessed time
                return chunk
        return None

    def peek_activation(self, chunk_id: str) -> Optional[float]:
        """
        Get the current activation of a chunk without updating its access time or activation.
        
        Args:
            chunk_id: The ID of the memory chunk to peek at.
            
        Returns:
            Optional[float]: The current activation level, or None if not found.
        """
        for chunk in self.items:
            if chunk.id == chunk_id:
                # Return the raw activation value without calling update_activation
                return chunk.activation 
        return None

    def forget(self, chunk_id: str) -> bool: # Implement forget method
        """
        Remove content from working memory.
        
        Args:
            chunk_id: The ID of the memory chunk to forget
            
        Returns:
            bool: True if the chunk was forgotten, False otherwise
        """
        for i, chunk in enumerate(self.items):
            if chunk.id == chunk_id:
                del self.items[i]
                return True
        return False

    # Method name corrected from previous implementation attempt
    def get_all_items(self) -> list[MemoryChunk]: # Return list of MemoryChunk 
        """
        Get all items currently in working memory.
        
        Returns:
            List[MemoryChunk]: List of all items
        """
        return list(self.items)

    def clear(self) -> None:
        """Remove all content from this memory system."""
        self.items.clear()

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about this memory system."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "current_items": len(self.items),
            "utilization": len(self.items) / self.capacity if self.capacity else 0,
        }

    def dump(self) -> list[dict[str, Any]]:
        """Dump all content from this memory system for consolidation or inspection."""
        return [
            {
                "id": chunk.id,
                "content": chunk.content,
                "activation": chunk.activation,
                "created_at": chunk.created_at.isoformat(), # Serialize datetime
                "last_accessed": chunk.last_accessed.isoformat(), # Serialize datetime
                "metadata": chunk.metadata, 
            }
            for chunk in self.items
        ]


# Remove singleton instance and related functions if factory pattern is used
# working_memory = WorkingMemory()
# def add_to_working_memory(...) ...
# def get_from_working_memory(...) ...
# def get_all_working_memory(...) ...
# def clear_working_memory(...) ...
