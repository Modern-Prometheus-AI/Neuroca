"""
Semantic memory functionality for the NCA system.

This module handles semantic memories - factual knowledge not tied to specific events.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from neuroca.core.memory.interfaces import MemoryChunk, MemorySystem  # Import interface

# Attempt to import Concept and Relationship for type checking in store method
try:
    # Correct import path
    from neuroca.core.models.memory import Concept, Relationship
except ImportError:
    Concept = None # type: ignore
    Relationship = None # type: ignore
    import logging
    logging.warning("Could not import Concept/Relationship for SemanticMemory.store type checking.")

# Placeholder for MemoryChunk implementation
class SemanticMemoryChunk(MemoryChunk[dict[str, Any]]): # Content is facts dict
    def __init__(self, chunk_id: str, concept: str, facts: dict[str, Any],
                 related_concepts: set[str], confidence: float,
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
    def chunk_id(self) -> str: return self._id # A003 Fix: Renamed from id
    @property
    def content(self) -> dict[str, Any]: return self._facts # Return facts as content
    @property
    def activation(self) -> float: return self._activation
    @property
    def created_at(self) -> datetime: return self._created_at
    @property
    def last_accessed(self) -> datetime: return self._last_updated # Use last_updated as proxy
    @property
    def metadata(self) -> dict[str, Any]:
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
    _storage: dict[str, SemanticMemoryChunk] = {} # Store by chunk_id
    _concept_index: dict[str, str] = {} # Map concept name to chunk_id

    def __init__(self, config: Optional[dict[str, Any]] = None): # Accept config
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

    def store(self, content: Any, **metadata) -> str:
        """
        Store content as a semantic memory. Updates if concept exists.

        Args:
            content: The facts dictionary, Concept object, or Relationship object.
            **metadata: Must include 'concept' if content is dict. Optional: 'related_concepts', 'confidence'.

        Returns:
            str: The ID of the stored/updated memory chunk.

        Raises:
            ValueError: If 'concept' is not in metadata (for dict content), content type is unsupported, or concept name cannot be determined.
        """
        now = datetime.now()
        concept_name: Optional[str] = None
        facts = {}
        related_concepts = set(metadata.get('related_concepts', []))
        confidence = metadata.get('confidence', 1.0)
        is_relationship = False
        structured_rel_id: Optional[str] = None # Initialize for clarity

        # --- Determine Content Type and Extract Data ---
        if Concept and isinstance(content, Concept):
            concept_name = content.name
            facts = content.properties
            # Use confidence from Concept object, allow metadata override
            confidence = metadata.get('confidence', content.confidence)
            # Merge metadata passed in kwargs for flexibility
            related_concepts.update(metadata.get('related_concepts', set()))

        elif Relationship and isinstance(content, Relationship):
            is_relationship = True
            # Artificial concept name for logging/debug (optional usage)
            concept_name = f"rel:{content.source_id}-{content.relationship_type.name}-{content.target_id}"
            facts = { # Store relationship details in facts dict
                "source": content.source_id,
                "target": content.target_id,
                "type": content.relationship_type.name,
                "attributes": content.attributes
            }
            confidence = content.confidence
            # Use the structured relationship ID for storage key
            structured_rel_id = f"relationship:{content.source_id}:{content.relationship_type.name}:{content.target_id}"

        elif isinstance(content, dict):
            # Existing logic: content is facts, concept name from metadata
            concept_name = metadata.get('concept')
            if not concept_name:
                raise ValueError("Metadata must include 'concept' when content is a dict.")
            facts = content
            confidence = metadata.get('confidence', 1.0)
            related_concepts = set(metadata.get('related_concepts', []))

        else:
            raise ValueError(f"Unsupported content type for SemanticMemory store: {type(content)}. Expecting Concept, Relationship, or dict.")

        # Ensure we have an identifier (concept name or structured relationship ID)
        if not is_relationship and not concept_name:
             raise ValueError("Could not determine concept name for storage.")
        # Check structured_rel_id specifically if it's a relationship
        if is_relationship and not structured_rel_id:
            # This case should technically be prevented by the Relationship instance check, but good practice
            raise ValueError("Could not determine relationship identifier for storage.")


        # --- Storage Logic ---
        if is_relationship:
            # Handle Relationship update/creation using structured ID
            # We already checked structured_rel_id is not None if is_relationship is True
            existing_chunk_id = structured_rel_id
            if existing_chunk_id in SemanticMemory._storage:
                # Update existing relationship chunk
                chunk = SemanticMemory._storage[existing_chunk_id]
                chunk._facts.update(facts) # Merge/overwrite attributes
                # Consider a more sophisticated confidence update if needed
                new_confidence = (chunk._confidence + confidence) / 2 # Example: Average confidence
                chunk._confidence = new_confidence
                # chunk.update_activation() # Assuming this method exists on the chunk
                chunk.last_updated = now # Update timestamp
                return existing_chunk_id # Return the ID used for storage

            # If relationship chunk doesn't exist, create it (Correctly unindented)
            chunk = SemanticMemoryChunk( # Assuming SemanticMemoryChunk exists and takes these args
                chunk_id=existing_chunk_id, # Use structured ID as the key
                concept=concept_name, # Store artificial concept name if useful
                facts=facts,
                related_concepts=set(), # Relationships typically don't have separate related concepts in this model
                confidence=confidence,
                created_at=now,
                last_updated=now,
                access_count=0
            )
            SemanticMemory._storage[existing_chunk_id] = chunk
            # Do NOT add relationships to the concept_index by default
            return existing_chunk_id # Return the ID used for storage

        # Handle Concept update/creation
        # We already checked concept_name is not None if is_relationship is False
        existing_chunk_id = SemanticMemory._concept_index.get(concept_name)
        if existing_chunk_id and existing_chunk_id in SemanticMemory._storage:
            # Update existing concept chunk
            chunk = SemanticMemory._storage[existing_chunk_id]
            chunk._facts.update(facts) # Merge facts/properties
            chunk._related_concepts.update(related_concepts)
            chunk._confidence = confidence # Update confidence (overwrite or blend as needed)
            # chunk.update_activation() # Assuming this method exists
            chunk.last_updated = now # Update timestamp
            return existing_chunk_id # Return the existing storage key (UUID)

        # If concept chunk doesn't exist, create it (Correctly unindented)
        new_chunk_id = str(uuid.uuid4()) # Generate a new UUID for storage key
        chunk = SemanticMemoryChunk( # Assuming SemanticMemoryChunk exists and takes these args
            chunk_id=new_chunk_id,
            concept=concept_name,
            facts=facts,
            related_concepts=related_concepts,
            confidence=confidence,
            created_at=now,
            last_updated=now,
            access_count=0
        )
        SemanticMemory._storage[new_chunk_id] = chunk # Store using the new UUID
        SemanticMemory._concept_index[concept_name] = new_chunk_id # Map concept name to the new UUID
        return new_chunk_id # Return the new ID

    def retrieve(self, query: Any, limit: int = 10, **parameters) -> list[MemoryChunk]: # Implement retrieve
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

    def get_statistics(self) -> dict[str, Any]: # Implement get_statistics
        """Get statistics about semantic memory."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "current_items": len(SemanticMemory._storage),
            "concepts_indexed": len(SemanticMemory._concept_index),
        }

    def dump(self) -> list[dict[str, Any]]: # Implement dump
        """Dump all content from semantic memory."""
        # Need proper serialization for MemoryChunk
        return [chunk.metadata for chunk in SemanticMemory._storage.values()] # Placeholder dump

# Remove old module-level functions if using factory pattern
# def store_semantic_memory(...) ...
# def retrieve_semantic_memory(...) ...
# def query_semantic_network(...) ...
