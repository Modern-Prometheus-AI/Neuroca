"""Semantic Memory Implementation for NeuroCognitive Architecture.

This module implements the Semantic Memory system, which serves as long-term
knowledge storage with the following biological characteristics:
- Knowledge graph with typed relationships between concepts
- Abstraction mechanisms to convert episodic experiences to semantic knowledge
- Consistency management and contradiction resolution
- Hierarchical concept organization
- Inference mechanisms across knowledge structures

Semantic memory represents the LTM (Long-Term Memory) tier in the three-tier
memory architecture of the NCA system, storing consolidated knowledge derived
from episodic experiences and direct learning.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any

from neuroca.core.memory.interfaces import MemoryChunk, MemorySystem

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between concepts in semantic memory."""
    
    IS_A = auto()           # Hierarchical relationship (dog IS_A mammal)
    HAS_A = auto()          # Compositional relationship (car HAS_A engine)
    PART_OF = auto()        # Membership relationship (wheel PART_OF bicycle)
    CAUSES = auto()         # Causal relationship (rain CAUSES wetness)
    OPPOSITE_OF = auto()    # Antonym relationship (hot OPPOSITE_OF cold)
    SYNONYM_OF = auto()     # Similar meaning (large SYNONYM_OF big)
    LOCATED_IN = auto()     # Spatial relationship (book LOCATED_IN library)
    OCCURS_BEFORE = auto()  # Temporal precedence (cooking OCCURS_BEFORE eating)
    OCCURS_AFTER = auto()   # Temporal succession (eating OCCURS_AFTER cooking)
    RELATED_TO = auto()     # Generic association (less specific)
    DERIVED_FROM = auto()   # Source relationship (abstractions DERIVED_FROM experiences)


@dataclass
class Concept:
    """Represents a concept node in the semantic knowledge graph.
    
    A concept is a fundamental unit of semantic knowledge and can be connected
    to other concepts through typed relationships.
    """
    
    id: str
    name: str
    description: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # Confidence score (0.0 to 1.0)
    # Sources that contributed to this concept (e.g., episodic memory IDs)
    sources: list[str] = field(default_factory=list)
    # Alternative forms/synonyms of the concept
    forms: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert concept to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "confidence": self.confidence,
            "sources": self.sources,
            "forms": self.forms
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Concept:
        """Create concept from dictionary representation."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()
            
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            properties=data.get("properties", {}),
            created_at=created_at,
            confidence=data.get("confidence", 1.0),
            sources=data.get("sources", []),
            forms=data.get("forms", [])
        )


@dataclass
class Relationship:
    """Represents a typed relationship between two concepts."""
    
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    confidence: float = 1.0  # Confidence score (0.0 to 1.0)
    # Sources that contributed to this relationship (e.g., episodic memory IDs)
    sources: list[str] = field(default_factory=list)
    # Additional attributes specific to this relationship
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert relationship to dictionary representation."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.name,
            "confidence": self.confidence,
            "sources": self.sources,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Relationship:
        """Create relationship from dictionary representation."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()
            
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=RelationshipType[data["relationship_type"]],
            confidence=data.get("confidence", 1.0),
            sources=data.get("sources", []),
            attributes=data.get("attributes", {}),
            created_at=created_at
        )


class SemanticMemoryChunk(MemoryChunk):
    """Chunk implementation for Semantic Memory."""
    
    def __init__(
        self, 
        chunk_id: str, 
        content: Concept | Relationship,
        created_at: float = None,
        metadata: dict[str, Any] = None
    ):
        """Initialize a semantic memory chunk.
        
        Args:
            chunk_id: Unique identifier for the chunk
            content: The content of the chunk (Concept or Relationship)
            created_at: Timestamp when the chunk was created
            metadata: Additional metadata for the chunk
        """
        super().__init__(chunk_id, content, created_at or time.time(), metadata or {})
        self.content_type = "concept" if isinstance(content, Concept) else "relationship"
    
    @property
    def activation(self) -> float:
        """Semantic memory has persistent activation."""
        # Semantic memory doesn't decay the same way as working memory,
        # but we use confidence as a form of "activation" for retrievability
        if self.content_type == "concept":
            return self.content.confidence
        else:
            return self.content.confidence
    
    @activation.setter
    def activation(self, value: float) -> None:
        """Update activation (confidence) of the semantic content."""
        if self.content_type == "concept":
            self.content.confidence = max(0.0, min(1.0, value))
        else:
            self.content.confidence = max(0.0, min(1.0, value))


class SemanticMemory(MemorySystem):
    """Semantic Memory implementation using a knowledge graph structure.
    
    This class implements the MemorySystem interface to provide semantic
    memory capabilities, which include:
    1. Long-term knowledge storage as a graph of interconnected concepts
    2. Typed relationships between concepts (IS-A, HAS-A, etc.)
    3. Inference capabilities across the knowledge graph
    4. Consistency management to maintain a coherent knowledge base
    5. Abstraction from episodic to semantic knowledge
    """
    
    def __init__(self):
        """Initialize the semantic memory system."""
        # Maps concept IDs to SemanticMemoryChunks containing Concepts
        self._concepts: dict[str, SemanticMemoryChunk] = {}
        
        # Maps (source_id, relationship_type, target_id) to SemanticMemoryChunks containing Relationships
        self._relationships: dict[tuple[str, RelationshipType, str], SemanticMemoryChunk] = {}
        
        # Index of outgoing relationships for each concept
        self._outgoing_relationships: dict[str, dict[RelationshipType, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Index of incoming relationships for each concept
        self._incoming_relationships: dict[str, dict[RelationshipType, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Contradiction detection cache
        self._contradiction_cache: dict[str, set[str]] = defaultdict(set)
        
        logger.info("Semantic memory system initialized")
    
    def store(self, content: Concept | Relationship | dict[str, Any], **metadata) -> str:
        """Store a concept or relationship in semantic memory.
        
        Args:
            content: Either a Concept, Relationship, or dictionary representation
            **metadata: Additional metadata for the memory chunk
        
        Returns:
            The unique identifier for the stored chunk
        """
        # Convert dictionary to proper object if needed
        if isinstance(content, dict):
            if "source_id" in content and "target_id" in content and "relationship_type" in content:
                content = Relationship.from_dict(content)
            else:
                content = Concept.from_dict(content)
        
        # Generate chunk ID based on content type
        if isinstance(content, Concept):
            chunk_id = f"concept:{content.id}"
            # Check for existing concept
            if content.id in self._concepts:
                # Update existing concept with new information
                self._update_concept(content, metadata)
                return chunk_id
            
            # Store new concept
            chunk = SemanticMemoryChunk(chunk_id, content, metadata=metadata)
            self._concepts[content.id] = chunk
            logger.debug(f"Stored concept '{content.name}' with ID {content.id}")
            
        elif isinstance(content, Relationship):
            # Validate that source and target concepts exist
            if content.source_id not in self._concepts:
                raise ValueError(f"Source concept {content.source_id} does not exist")
            if content.target_id not in self._concepts:
                raise ValueError(f"Target concept {content.target_id} does not exist")
            
            rel_key = (content.source_id, content.relationship_type, content.target_id)
            chunk_id = f"relationship:{content.source_id}:{content.relationship_type.name}:{content.target_id}"
            
            # Check for contradictions
            self._check_relationship_contradictions(content)
            
            # Check for existing relationship
            if rel_key in self._relationships:
                # Update existing relationship
                self._update_relationship(content, metadata)
                return chunk_id
            
            # Store new relationship
            chunk = SemanticMemoryChunk(chunk_id, content, metadata=metadata)
            self._relationships[rel_key] = chunk
            
            # Update relationship indices
            self._outgoing_relationships[content.source_id][content.relationship_type].append(content.target_id)
            self._incoming_relationships[content.target_id][content.relationship_type].append(content.source_id)
            
            logger.debug(
                f"Stored relationship {content.source_id} {content.relationship_type.name} "
                f"{content.target_id}"
            )
        else:
            raise TypeError(f"Content must be a Concept or Relationship, got {type(content)}")
        
        return chunk_id
    
    def retrieve(self, query: Any, **parameters) -> list[MemoryChunk]:
        """Retrieve semantic memory chunks based on a query.
        
        Args:
            query: The query to match against semantic memory. Can be:
                - A concept ID
                - A concept name
                - A tuple of (source_concept, relationship_type, target_concept)
                - A dictionary with filtering criteria
            **parameters: Additional retrieval parameters such as:
                - limit: Maximum number of results to return
                - relationship_types: List of relationship types to include
                - min_confidence: Minimum confidence threshold
                - include_related: Whether to include related concepts
        
        Returns:
            A list of matching memory chunks
        """
        limit = parameters.get("limit", 100)
        min_confidence = parameters.get("min_confidence", 0.0)
        include_related = parameters.get("include_related", False)
        relationship_types = parameters.get("relationship_types", None)
        
        results = []
        
        # If query is a string, treat as concept ID or name
        if isinstance(query, str):
            # First try as concept ID
            if query in self._concepts:
                chunk = self._concepts[query]
                if chunk.activation >= min_confidence:
                    results.append(chunk)
                    
                # Include related concepts if requested
                if include_related:
                    related_chunks = self._get_related_concepts(query, relationship_types)
                    results.extend([c for c in related_chunks if c.activation >= min_confidence])
            else:
                # Try to find concepts by name or forms
                for concept_id, chunk in self._concepts.items():
                    concept = chunk.content
                    if (concept.name.lower() == query.lower() or 
                        query.lower() in [f.lower() for f in concept.forms]):
                        if chunk.activation >= min_confidence:
                            results.append(chunk)
                        
                        # Include related concepts if requested
                        if include_related:
                            related_chunks = self._get_related_concepts(concept_id, relationship_types)
                            results.extend([c for c in related_chunks if c.activation >= min_confidence])
        
        # If query is a tuple, treat as relationship pattern
        elif isinstance(query, tuple) and len(query) == 3:
            source, rel_type, target = query
            
            # Convert string relationship type to enum if needed
            if isinstance(rel_type, str):
                try:
                    rel_type = RelationshipType[rel_type]
                except KeyError:
                    logger.warning(f"Invalid relationship type: {rel_type}")
                    return []
            
            # Find matching relationships
            for rel_key, chunk in self._relationships.items():
                src_id, rel, tgt_id = rel_key
                relationship = chunk.content
                
                # Match source, relationship type, and target
                source_match = source is None or src_id == source or self._concepts[src_id].content.name == source
                rel_match = rel_type is None or rel == rel_type
                target_match = target is None or tgt_id == target or self._concepts[tgt_id].content.name == target
                
                if source_match and rel_match and target_match and relationship.confidence >= min_confidence:
                    results.append(chunk)
        
        # If query is a dictionary, use it as filter criteria
        elif isinstance(query, dict):
            # Filter concepts
            if "concept" in query:
                concept_filter = query["concept"]
                for concept_id, chunk in self._concepts.items():
                    concept = chunk.content
                    
                    # Match any specified field
                    match = True
                    for key, value in concept_filter.items():
                        if key == "properties":
                            # Match properties as subset
                            for prop_key, prop_value in value.items():
                                if prop_key not in concept.properties or concept.properties[prop_key] != prop_value:
                                    match = False
                                    break
                        elif hasattr(concept, key) and getattr(concept, key) != value:
                            match = False
                            break
                    
                    if match and concept.confidence >= min_confidence:
                        results.append(chunk)
            
            # Filter relationships
            if "relationship" in query:
                rel_filter = query["relationship"]
                for rel_key, chunk in self._relationships.items():
                    relationship = chunk.content
                    
                    # Match any specified field
                    match = True
                    for key, value in rel_filter.items():
                        if key == "attributes":
                            # Match attributes as subset
                            for attr_key, attr_value in value.items():
                                if attr_key not in relationship.attributes or relationship.attributes[attr_key] != attr_value:
                                    match = False
                                    break
                        elif hasattr(relationship, key) and getattr(relationship, key) != value:
                            match = False
                            break
                    
                    if match and relationship.confidence >= min_confidence:
                        results.append(chunk)
        
        # Apply limit after collecting all results
        return results[:limit]
    
    def forget(self, chunk_id: str) -> bool:
        """Remove a chunk from semantic memory.
        
        Args:
            chunk_id: ID of the chunk to forget
            
        Returns:
            True if the chunk was forgotten, False otherwise
        """
        # Check if this is a concept or relationship
        if chunk_id.startswith("concept:"):
            concept_id = chunk_id[len("concept:"):]
            if concept_id in self._concepts:
                # Check if there are any relationships involving this concept
                has_relationships = False
                for src, _, _ in self._relationships:
                    if src == concept_id:
                        has_relationships = True
                        break
                
                if not has_relationships:
                    for _, _, tgt in self._relationships:
                        if tgt == concept_id:
                            has_relationships = True
                            break
                
                if has_relationships:
                    logger.warning(
                        f"Cannot forget concept {concept_id} as it has active relationships. "
                        "Remove relationships first."
                    )
                    return False
                
                # Remove the concept
                del self._concepts[concept_id]
                # Clean up indices
                if concept_id in self._outgoing_relationships:
                    del self._outgoing_relationships[concept_id]
                if concept_id in self._incoming_relationships:
                    del self._incoming_relationships[concept_id]
                # Clean up contradiction cache
                if concept_id in self._contradiction_cache:
                    del self._contradiction_cache[concept_id]
                
                logger.debug(f"Forgot concept {concept_id}")
                return True
            return False
            
        elif chunk_id.startswith("relationship:"):
            # Extract relationship components from ID
            parts = chunk_id[len("relationship:"):].split(":")
            if len(parts) != 3:
                return False
            
            source_id, rel_type_str, target_id = parts
            try:
                rel_type = RelationshipType[rel_type_str]
            except KeyError:
                return False
            
            rel_key = (source_id, rel_type, target_id)
            if rel_key in self._relationships:
                # Remove the relationship
                del self._relationships[rel_key]
                
                # Update indices
                if source_id in self._outgoing_relationships and rel_type in self._outgoing_relationships[source_id]:
                    self._outgoing_relationships[source_id][rel_type].remove(target_id)
                    
                if target_id in self._incoming_relationships and rel_type in self._incoming_relationships[target_id]:
                    self._incoming_relationships[target_id][rel_type].remove(source_id)
                
                logger.debug(f"Forgot relationship {source_id} {rel_type.name} {target_id}")
                return True
            return False
            
        return False
    
    def clear(self) -> None:
        """Clear all semantic memory contents."""
        self._concepts.clear()
        self._relationships.clear()
        self._outgoing_relationships.clear()
        self._incoming_relationships.clear()
        self._contradiction_cache.clear()
        logger.info("Cleared semantic memory")
    
    def get_concept(self, concept_id: str) -> Concept | None:
        """Get a concept by its ID.
        
        Args:
            concept_id: ID of the concept to retrieve
            
        Returns:
            The concept if found, None otherwise
        """
        chunk = self._concepts.get(concept_id)
        return chunk.content if chunk else None
    
    def get_relationship(self, source_id: str, relationship_type: RelationshipType, target_id: str) -> Relationship | None:
        """Get a specific relationship.
        
        Args:
            source_id: ID of the source concept
            relationship_type: Type of relationship
            target_id: ID of the target concept
            
        Returns:
            The relationship if found, None otherwise
        """
        rel_key = (source_id, relationship_type, target_id)
        chunk = self._relationships.get(rel_key)
        return chunk.content if chunk else None
    
    def get_related_concepts(self, concept_id: str, relationship_types: list[RelationshipType] = None) -> dict[RelationshipType, list[Concept]]:
        """Get concepts related to the given concept.
        
        Args:
            concept_id: ID of the concept
            relationship_types: Optional list of relationship types to filter by
            
        Returns:
            Dictionary mapping relationship types to lists of related concepts
        """
        result = defaultdict(list)
        
        # Get outgoing relationships
        for rel_type, target_ids in self._outgoing_relationships[concept_id].items():
            if relationship_types is None or rel_type in relationship_types:
                for target_id in target_ids:
                    target_concept = self.get_concept(target_id)
                    if target_concept:
                        result[rel_type].append(target_concept)
        
        # Get incoming relationships
        for rel_type, source_ids in self._incoming_relationships[concept_id].items():
            if relationship_types is None or rel_type in relationship_types:
                for source_id in source_ids:
                    source_concept = self.get_concept(source_id)
                    if source_concept:
                        result[rel_type].append(source_concept)
        
        return dict(result)
    
    def infer_path(self, start_concept_id: str, end_concept_id: str, max_depth: int = 5) -> list[list[tuple[Relationship, bool]]]:
        """Find paths between two concepts in the knowledge graph.
        
        Args:
            start_concept_id: ID of the starting concept
            end_concept_id: ID of the ending concept
            max_depth: Maximum path length to consider
            
        Returns:
            List of paths, where each path is a list of (relationship, is_forward) tuples
        """
        if start_concept_id not in self._concepts or end_concept_id not in self._concepts:
            return []
        
        # Use breadth-first search to find paths
        visited = set()
        queue = [(start_concept_id, [])]
        paths = []
        
        while queue and len(paths) < 10:  # Limit to 10 paths
            current_id, path = queue.pop(0)
            
            if current_id == end_concept_id:
                paths.append(path)
                continue
            
            if len(path) >= max_depth or current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Try outgoing relationships
            for rel_type, target_ids in self._outgoing_relationships[current_id].items():
                for target_id in target_ids:
                    if target_id not in visited:
                        rel = self.get_relationship(current_id, rel_type, target_id)
                        if rel:
                            new_path = path + [(rel, True)]
                            queue.append((target_id, new_path))
            
            # Try incoming relationships
            for rel_type, source_ids in self._incoming_relationships[current_id].items():
                for source_id in source_ids:
                    if source_id not in visited:
                        rel = self.get_relationship(source_id, rel_type, current_id)
                        if rel:
                            new_path = path + [(rel, False)]
                            queue.append((source_id, new_path))
        
        return paths
    
    def infer_concept_properties(self, concept_id: str) -> dict[str, Any]:
        """Infer properties for a concept based on its relationships.
        
        This method uses the IS_A hierarchy to inherit properties from parent concepts.
        
        Args:
            concept_id: ID of the concept
            
        Returns:
            Dictionary of inferred properties
        """
        concept = self.get_concept(concept_id)
        if not concept:
            return {}
        
        # Start with the concept's own properties
        inferred_properties = dict(concept.properties)
        
        # Find all IS_A relationships and inherit properties
        parent_ids = self._outgoing_relationships[concept_id].get(RelationshipType.IS_A, [])
        for parent_id in parent_ids:
            parent_properties = self.infer_concept_properties(parent_id)
            
            # Add parent properties that don't exist in the concept
            for key, value in parent_properties.items():
                if key not in inferred_properties:
                    inferred_properties[key] = value
        
        return inferred_properties
    
    def abstract_from_episodic(self, episodic_chunks: list[MemoryChunk], min_occurrences: int = 3) -> list[str]:
        """Abstract semantic knowledge from episodic memories.
        
        This method identifies patterns in episodic memories and creates
        semantic concepts and relationships.
        
        Args:
            episodic_chunks: List of episodic memory chunks to analyze
            min_occurrences: Minimum number of occurrences to consider a pattern
            
        Returns:
            List of IDs for newly created semantic memory chunks
        """
        # This would be a complex implementation that identifies patterns
        # and abstracts concepts and relationships from episodic memories.
        # For now, we'll implement a simple version that just extracts
        # entities and relationships mentioned in the content.
        
        # Simple implementation placeholder
        created_chunk_ids = []
        
        # Here we would:
        # 1. Extract entities and relationships from episodic memories
        # 2. Count occurrences and identify patterns
        # 3. Create semantic concepts and relationships for patterns
        # 4. Connect them to existing knowledge
        
        logger.info(f"Abstracted {len(created_chunk_ids)} new semantic chunks from episodic memories")
        return created_chunk_ids
    
    def check_consistency(self) -> list[dict[str, Any]]:
        """Check the knowledge graph for inconsistencies and contradictions.
        
        Returns:
            List of identified inconsistencies
        """
        inconsistencies = []
        
        # Check for symmetric relationship violations
        # (e.g., if A OPPOSITE_OF B then B should OPPOSITE_OF A)
        for (src, rel_type, tgt) in self._relationships:
            if rel_type == RelationshipType.OPPOSITE_OF:
                # Check if the symmetric relationship exists
                if (tgt, rel_type, src) not in self._relationships:
                    inconsistencies.append({
                        "type": "missing_symmetric_relationship",
                        "source": src,
                        "relationship": rel_type.name,
                        "target": tgt
                    })
            
            # Check for transitive relationship violations
            # (e.g., if A IS_A B and B IS_A C then A should IS_A C)
            if rel_type == RelationshipType.IS_A:
                # Get all targets that the target is related to with the same relationship
                transitive_targets = self._outgoing_relationships[tgt].get(RelationshipType.IS_A, [])
                for trans_tgt in transitive_targets:
                    # Check if the transitive relationship exists
                    if trans_tgt not in self._outgoing_relationships[src].get(RelationshipType.IS_A, []):
                        inconsistencies.append({
                            "type": "missing_transitive_relationship",
                            "source": src,
                            "intermediate": tgt,
                            "target": trans_tgt,
                            "relationship": rel_type.name
                        })
        
        # Check for contradictions in the contradiction cache
        for concept_id, contradicting_ids in self._contradiction_cache.items():
            for contra_id in contradicting_ids:
                inconsistencies.append({
                    "type": "contradiction",
                    "concept1": concept_id,
                    "concept2": contra_id
                })
        
        return inconsistencies
    
    def _update_concept(self, concept: Concept, metadata: dict[str, Any]) -> None:
        """Update an existing concept with new information."""
        existing_chunk = self._concepts[concept.id]
        existing_concept = existing_chunk.content
        
        # Update confidence based on accumulated evidence
        evidence_count = len(existing_concept.sources) + len(concept.sources)
        if evidence_count > 0:
            # Average the confidences, weighted by evidence
            existing_weight = len(existing_concept.sources) / evidence_count
            new_weight = len(concept.sources) / evidence_count
            new_confidence = (existing_concept.confidence * existing_weight +
                             concept.confidence * new_weight)
            existing_concept.confidence = new_confidence
        
        # Merge sources
        for source in concept.sources:
            if source not in existing_concept.sources:
                existing_concept.sources.append(source)
        
        # Merge forms/synonyms
        for form in concept.forms:
            if form not in existing_concept.forms:
                existing_concept.forms.append(form)
        
        # Update description if provided and either no existing description or higher confidence
        if (concept.description and 
            (not existing_concept.description or concept.confidence > existing_concept.confidence)):
            existing_concept.description = concept.description
        
        # Merge properties
        for key, value in concept.properties.items():
            existing_concept.properties[key] = value
        
        # Update metadata
        existing_chunk.metadata.update(metadata)
        
        logger.debug(f"Updated concept {concept.id} with new information")
    
    def _update_relationship(self, relationship: Relationship, metadata: dict[str, Any]) -> None:
        """Update an existing relationship with new information."""
        rel_key = (relationship.source_id, relationship.relationship_type, relationship.target_id)
        existing_chunk = self._relationships[rel_key]
        existing_relationship = existing_chunk.content
        
        # Update confidence based on accumulated evidence
        evidence_count = len(existing_relationship.sources) + len(relationship.sources)
        if evidence_count > 0:
            # Average the confidences, weighted by evidence
            existing_weight = len(existing_relationship.sources) / evidence_count
            new_weight = len(relationship.sources) / evidence_count
            new_confidence = (existing_relationship.confidence * existing_weight +
                             relationship.confidence * new_weight)
            existing_relationship.confidence = new_confidence
        
        # Merge sources
        for source in relationship.sources:
            if source not in existing_relationship.sources:
                existing_relationship.sources.append(source)
        
        # Merge attributes
        for key, value in relationship.attributes.items():
            existing_relationship.attributes[key] = value
        
        # Update metadata
        existing_chunk.metadata.update(metadata)
        
        logger.debug(f"Updated relationship {relationship.source_id} {relationship.relationship_type.name} "
                    f"{relationship.target_id} with new information")
    
    def _get_related_concepts(self, concept_id: str, relationship_types: list[RelationshipType] = None) -> list[MemoryChunk]:
        """Get memory chunks for concepts related to the given concept."""
        related_chunks = []
        
        # Add outgoing relationships
        for rel_type, target_ids in self._outgoing_relationships[concept_id].items():
            if relationship_types is None or rel_type in relationship_types:
                for target_id in target_ids:
                    if target_id in self._concepts:
                        related_chunks.append(self._concepts[target_id])
        
        # Add incoming relationships
        for rel_type, source_ids in self._incoming_relationships[concept_id].items():
            if relationship_types is None or rel_type in relationship_types:
                for source_id in source_ids:
                    if source_id in self._concepts:
                        related_chunks.append(self._concepts[source_id])
        
        return related_chunks
    
    def _check_relationship_contradictions(self, relationship: Relationship) -> None:
        """Check if a new relationship contradicts existing knowledge."""
        source_id = relationship.source_id
        rel_type = relationship.relationship_type
        target_id = relationship.target_id
        
        # Check for direct contradictions
        if rel_type == RelationshipType.OPPOSITE_OF:
            # If A is OPPOSITE_OF B, then A cannot be SYNONYM_OF B
            synonym_key = (source_id, RelationshipType.SYNONYM_OF, target_id)
            if synonym_key in self._relationships:
                self._contradiction_cache[source_id].add(target_id)
                logger.warning(
                    f"Contradiction detected: {source_id} cannot be both OPPOSITE_OF "
                    f"and SYNONYM_OF {target_id}"
                )
        
        elif rel_type == RelationshipType.SYNONYM_OF:
            # If A is SYNONYM_OF B, then A cannot be OPPOSITE_OF B
            opposite_key = (source_id, RelationshipType.OPPOSITE_OF, target_id)
            if opposite_key in self._relationships:
                self._contradiction_cache[source_id].add(target_id)
                logger.warning(
                    f"Contradiction detected: {source_id} cannot be both SYNONYM_OF "
                    f"and OPPOSITE_OF {target_id}"
                )
        
        # Check for circular IS_A relationships
        elif rel_type == RelationshipType.IS_A:
            # If A IS_A B, then B cannot IS_A A (would create a circular hierarchy)
            circular_key = (target_id, RelationshipType.IS_A, source_id)
            if circular_key in self._relationships:
                self._contradiction_cache[source_id].add(target_id)
                logger.warning(
                    f"Contradiction detected: Circular IS_A relationship between "
                    f"{source_id} and {target_id}"
                )
            
            # Check for longer circular paths (e.g., A IS_A B, B IS_A C, C IS_A A)
            visited = {source_id}
            queue = [target_id]
            
            while queue:
                current = queue.pop(0)
                
                # If we find the source again, we have a circular path
                if current == source_id:
                    self._contradiction_cache[source_id].add(target_id)
                    logger.warning(
                        f"Contradiction detected: Adding {source_id} IS_A {target_id} "
                        f"would create a circular hierarchy"
                    )
                    break
                
                # Add parents of current to the queue if not visited
                parents = self._outgoing_relationships[current].get(RelationshipType.IS_A, [])
                for parent in parents:
                    if parent not in visited:
                        visited.add(parent)
                        queue.append(parent) 