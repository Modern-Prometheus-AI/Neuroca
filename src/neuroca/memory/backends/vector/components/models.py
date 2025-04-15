"""
Vector Backend Models Component

This module provides the data models for the Vector storage backend,
specifically focusing on vector entries that combine an ID, vector, and metadata.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class VectorEntry(BaseModel):
    """
    A single entry in the vector database.
    
    This model represents a vector embedding and its associated metadata,
    including the unique identifier that links it to a memory item.
    
    Attributes:
        id: Unique identifier for the vector entry
        vector: The vector embedding as a list of floats
        metadata: Associated metadata for filtering and retrieval
    """
    
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the vector entry."""
        vector_preview = f"[{self.vector[0]:.4f},...] ({len(self.vector)} dims)"
        metadata_keys = list(self.metadata.keys())
        return f"VectorEntry(id={self.id}, vector={vector_preview}, metadata_keys={metadata_keys})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the vector entry to a dictionary for serialization."""
        return {
            "id": self.id,
            "vector": self.vector,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorEntry":
        """Create a vector entry from a dictionary."""
        return cls(
            id=data["id"],
            vector=data["vector"],
            metadata=data.get("metadata", {})
        )
