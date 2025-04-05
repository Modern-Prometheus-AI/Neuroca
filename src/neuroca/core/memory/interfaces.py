"""
Interface definitions for memory systems to prevent circular imports.

This module defines abstract base classes for all memory components,
providing a common interface that different memory implementations must follow.
By centralizing these interfaces, we avoid circular dependencies between
memory implementation modules.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

T = TypeVar('T')  # Content type for memory chunks

class MemoryChunk(Generic[T], ABC):
    """Abstract base class for memory chunks stored in any memory system."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Get the unique identifier for this memory chunk."""
        pass
    
    @property
    @abstractmethod
    def content(self) -> T:
        """Get the content of this memory chunk."""
        pass
    
    @property
    @abstractmethod
    def activation(self) -> float:
        """Get the current activation level of this memory chunk."""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Get the creation timestamp of this memory chunk."""
        pass
    
    @property
    @abstractmethod
    def last_accessed(self) -> datetime:
        """Get the timestamp when this chunk was last accessed."""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Get the metadata associated with this memory chunk."""
        pass
    
    @abstractmethod
    def update_activation(self, value: Optional[float] = None) -> None:
        """
        Update the activation level of this memory chunk.
        
        If value is provided, set activation to that value.
        Otherwise, recalculate activation based on internal rules.
        """
        pass

class MemorySystem(ABC):
    """Abstract base class for all memory systems."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this memory system."""
        pass
    
    @property
    @abstractmethod
    def capacity(self) -> Optional[int]:
        """
        Get the capacity of this memory system.
        
        Returns None if the memory system has unlimited capacity.
        """
        pass
    
    @abstractmethod
    def store(self, content: Any, **metadata) -> str:
        """
        Store content in this memory system.
        
        Args:
            content: The content to store
            **metadata: Additional metadata to associate with the content
            
        Returns:
            str: The ID of the stored memory chunk
        """
        pass
    
    @abstractmethod
    def retrieve(self, query: Any, limit: int = 10, **parameters) -> list[MemoryChunk]:
        """
        Retrieve content from this memory system based on a query.
        
        Args:
            query: The query to match against stored content
            limit: Maximum number of results to return
            **parameters: Additional parameters for the retrieval process
            
        Returns:
            List[MemoryChunk]: The retrieved memory chunks
        """
        pass
    
    @abstractmethod
    def retrieve_by_id(self, chunk_id: str) -> Optional[MemoryChunk]:
        """
        Retrieve a specific memory chunk by its ID.
        
        Args:
            chunk_id: The ID of the memory chunk to retrieve
            
        Returns:
            Optional[MemoryChunk]: The retrieved memory chunk, or None if not found
        """
        pass
    
    @abstractmethod
    def forget(self, chunk_id: str) -> bool:
        """
        Remove content from this memory system.
        
        Args:
            chunk_id: The ID of the memory chunk to forget
            
        Returns:
            bool: True if the chunk was forgotten, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Remove all content from this memory system."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about this memory system.
        
        Returns:
            Dict[str, Any]: Statistics about the memory system
        """
        pass
    
    @abstractmethod
    def dump(self) -> list[dict[str, Any]]:
        """
        Dump all content from this memory system.
        
        Returns:
            List[Dict[str, Any]]: All memory chunks in serializable format
        """
        pass

class MemoryConsolidator(ABC):
    """Abstract base class for memory consolidation processes."""
    
    @abstractmethod
    def consolidate(self, source: MemorySystem, target: MemorySystem, **parameters) -> list[str]:
        """
        Consolidate memories from source to target memory system.
        
        Args:
            source: The source memory system
            target: The target memory system
            **parameters: Additional parameters for the consolidation process
            
        Returns:
            List[str]: IDs of consolidated memory chunks in the target system
        """
        pass

class MemoryDecay(ABC):
    """Abstract base class for memory decay processes."""
    
    @abstractmethod
    def apply(self, memory_system: MemorySystem, **parameters) -> list[str]:
        """
        Apply decay to a memory system.
        
        Args:
            memory_system: The memory system to apply decay to
            **parameters: Additional parameters for the decay process
            
        Returns:
            List[str]: IDs of memory chunks that were forgotten due to decay
        """
        pass
    
    @abstractmethod
    def calculate_decay(self, chunk: MemoryChunk, **parameters) -> float:
        """
        Calculate decay for a specific memory chunk.
        
        Args:
            chunk: The memory chunk to calculate decay for
            **parameters: Additional parameters for the decay calculation
            
        Returns:
            float: The calculated decay value (0.0-1.0)
        """
        pass 