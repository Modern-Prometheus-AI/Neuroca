"""
Semantic memory functionality for the NCA system.

This module handles semantic memories - factual knowledge not tied to specific events.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import uuid
from neuroca.core.memory.interfaces import MemorySystem, MemoryChunk # Import interface

# Placeholder for MemoryChunk implementation
class SemanticMemoryChunk(MemoryChunk[Dict[str, Any]]): # Content is facts dict
    def __init__(self, chunk_id: str, concept: str, facts: Dict[str, Any],
                 related_concepts: Set[str], confidence: float,
                 created_at: datetime, last_updated: datetime, access_count: int):
        self._id = chunk_id
        self._concept = concept
        self._facts = facts
        self._related_concepts = related_concepts
        self._confidence = confidence
        self._created_at = created_at
        self._last_updated = last_updated
        self._access_count = access_count
        # Activation might depend on confidence, connections, recency
        self._activation = self._calculate_activation()

    def _calculate_activation(self) -> float:
        # Placeholder activation logic
        recency = (datetime.now() - self.last_updated).total_seconds()
        # Simple decay + confidence + access boost
        activation = self.confidence * (0.999 ** (recency / (3600 * 24))) + (self.access_count * 0.001)
        return max(0.0, min(1.0, activation))

    @property
    def id(self) -> str: return self._id
    @property
    def content(self) -> Dict[str, Any]: return self._facts # Return facts as content
    @property
    def activation(self) -> float: return self._activation
    @property
    def created_at(self) -> datetime: return self._created_at
    @property
    def last_accessed(self) -> datetime: return self._last_updated # Use last_updated as proxy
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "concept": self._concept,
            "related_concepts": list(self._related_concepts), # Convert set for serialization
            "confidence": self._confidence,
            "access_count": self._access_count,
            "last_updated": self._last_updated.isoformat()
        }

    def update_activation(self, value: Optional[float] = None) -> None:
        self._last_updated = datetime.now()
        self._access_count += 1
        if value is not None:
            self._activation = value
        else:
            self._activation = self._calculate_activation()


class SemanticMemory(MemorySystem): # Inherit from MemorySystem
    """Class managing the semantic memory system."""

    # In-memory storage for simplicity
    _storage: Dict[str, SemanticMemoryChunk] = {} # Store by chunk_id
    _concept_index: Dict[str, str] = {} # Map concept name to chunk_id

    def __init__(self, config: Optional[Dict[str, Any]] = None): # Accept config
        """
        Initialize the semantic memory system.
        
        Args:
            config: Configuration dictionary. Ignored for now.
        """
        self.config = config or {}
        # Initialize storage (clears previous state if any)
        SemanticMemory._storage = {}
        SemanticMemory._concept_index = {}

    @property
    def name(self) -> str:
        return "semantic_memory"

    @property
    def capacity(self) -> Optional[int]:
        # Assuming unlimited capacity for this simple implementation
        return None

    def store(self, content: Any, **metadata) -> str: # Implement store
        """
        Store content as a semantic memory. Updates if concept exists.
        
        Args:
            content: The facts dictionary.
            **metadata: Must include 'concept'. Optional: 'related_concepts', 'confidence'.
            
        Returns:
            str: The ID of the stored/updated memory chunk.
            
        Raises:
            ValueError: If 'concept' is not in metadata or content is not a dict.
        """
        concept = metadata.get('concept')
        if not concept:
            raise ValueError("Metadata must include 'concept' for semantic memory.")
        if not isinstance(content, dict):
            raise ValueError("Content for semantic memory must be a dictionary of facts.")

        now = datetime.now()
        chunk_id = SemanticMemory._concept_index.get(concept)

        if chunk_id and chunk_id in SemanticMemory._storage:
            # Update existing chunk
            chunk = SemanticMemory._storage[chunk_id]
            chunk._facts.update(content) # Merge facts
            chunk._related_concepts.update(metadata.get('related_concepts', set()))
            chunk._confidence = metadata.get('confidence', chunk._confidence) # Update confidence if provided
            chunk.update_activation() # Mark as updated/accessed
            return chunk_id
        else:
            # Create new chunk
            chunk_id = str(uuid.uuid4())
            chunk = SemanticMemoryChunk(
                chunk_id=chunk_id,
                concept=concept,
                facts=content,
                related_concepts=set(metadata.get('related_concepts', [])),
                confidence=metadata.get('confidence', 1.0),
                created_at=now,
                last_updated=now,
                access_count=0
            )
            SemanticMemory._storage[chunk_id] = chunk
            SemanticMemory._concept_index[concept] = chunk_id
            return chunk_id

    def retrieve(self, query: Any, limit: int = 10, **parameters) -> List[MemoryChunk]: # Implement retrieve
        """
        Retrieve semantic memories matching the query.
        Basic implementation: retrieves by concept name if query is string.
        
        Args:
            query: Search query (expected string concept name)
            limit: Maximum number of results (ignored, returns 0 or 1)
            **parameters: Additional parameters (ignored)
            
        Returns:
            List[MemoryChunk]: List containing the matching memory chunk, or empty list.
        """
        if not isinstance(query, str):
            return []

        concept = query
        chunk = self.retrieve_by_concept(concept) # Use helper
        return [chunk] if chunk else []

    def retrieve_by_id(self, chunk_id: str) -> Optional[MemoryChunk]: # Implement retrieve_by_id
        """
        Retrieve a specific memory chunk by its ID.
        """
        chunk = SemanticMemory._storage.get(chunk_id)
        if chunk:
            chunk.update_activation()
        return chunk

    def retrieve_by_concept(self, concept: str) -> Optional[MemoryChunk]: # Helper method
        """Retrieve a memory chunk by concept name."""
        chunk_id = SemanticMemory._concept_index.get(concept)
        if chunk_id:
            return self.retrieve_by_id(chunk_id)
        return None

    def forget(self, chunk_id: str) -> bool: # Implement forget
        """
        Remove content from semantic memory by chunk ID.
        """
        chunk = SemanticMemory._storage.pop(chunk_id, None)
        if chunk:
            # Remove from concept index as well
            SemanticMemory._concept_index.pop(chunk.metadata.get("concept"), None)
            return True
        return False

    def forget_concept(self, concept: str) -> bool: # Helper method
        """Remove content from semantic memory by concept name."""
        chunk_id = SemanticMemory._concept_index.get(concept)
        if chunk_id:
            return self.forget(chunk_id)
        return False

    def clear(self) -> None: # Implement clear
        """Remove all content from semantic memory."""
        SemanticMemory._storage.clear()
        SemanticMemory._concept_index.clear()

    def get_statistics(self) -> Dict[str, Any]: # Implement get_statistics
        """Get statistics about semantic memory."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "current_items": len(SemanticMemory._storage),
            "concepts_indexed": len(SemanticMemory._concept_index),
        }

    def dump(self) -> List[Dict[str, Any]]: # Implement dump
        """Dump all content from semantic memory."""
        # Need proper serialization for MemoryChunk
        return [chunk.metadata for chunk in SemanticMemory._storage.values()] # Placeholder dump

# Remove old module-level functions if using factory pattern
# def store_semantic_memory(...) ...
# def retrieve_semantic_memory(...) ...
# def query_semantic_network(...) ...
