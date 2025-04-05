"""
Long-Term Memory (LTM) Module for NeuroCognitive Architecture.

This module implements the Long-Term Memory component of the NCA's three-tiered memory system.
Long-Term Memory stores persistent information that remains accessible over extended periods,
similar to human declarative and procedural memory systems.

The LTM module provides:
- Declarative memory (facts, events, semantic knowledge)
- Procedural memory (skills, routines, implicit knowledge)
- Episodic memory (autobiographical events, experiences)
- Semantic memory (general world knowledge, concepts)

Key Features:
- Persistent storage of information with minimal decay
- Structured knowledge representation
- Associative retrieval mechanisms
- Memory consolidation from Working Memory
- Integration with vector databases for efficient similarity search
- Hierarchical organization of knowledge

Usage Examples:
    # Initialize LTM with default settings
    ltm = LongTermMemory()
    
    # Store a new memory
    memory_id = ltm.store({
        "type": "declarative",
        "content": "Paris is the capital of France",
        "metadata": {"confidence": 0.95, "source": "geography_knowledge"}
    })
    
    # Retrieve memories by content similarity
    related_memories = ltm.retrieve("What is the capital of France?", limit=5)
    
    # Update existing memory
    ltm.update(memory_id, {"confidence": 0.99})
    
    # Perform memory consolidation from working memory
    ltm.consolidate(working_memory_items)
"""

import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional, Union

from neuroca.memory.base import MemoryBase, MemoryItem, MemoryRetrievalResult
from neuroca.memory.exceptions import (
    InvalidMemoryFormatError,
    MemoryConsolidationError,
    MemoryNotFoundError,
    MemoryRetrievalError,
    MemoryStorageError,
)

# Configure module logger
logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Enumeration of long-term memory types."""
    DECLARATIVE = auto()
    PROCEDURAL = auto()
    EPISODIC = auto()
    SEMANTIC = auto()

class LTMItem(MemoryItem):
    """
    Represents an item stored in Long-Term Memory.
    
    Extends the base MemoryItem with LTM-specific attributes.
    """
    
    def __init__(
        self,
        content: Any,
        memory_type: MemoryType,
        metadata: Optional[dict[str, Any]] = None,
        item_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_accessed: Optional[datetime] = None,
        importance: float = 0.5,
        confidence: float = 1.0,
        associations: Optional[list[str]] = None,
        embedding: Optional[list[float]] = None,
    ):
        """
        Initialize a new LTM item.
        
        Args:
            content: The actual content of the memory
            memory_type: Type of long-term memory (declarative, procedural, etc.)
            metadata: Additional information about the memory
            item_id: Unique identifier (generated if not provided)
            created_at: Timestamp of creation (defaults to now)
            last_accessed: Timestamp of last access (defaults to now)
            importance: Subjective importance score (0.0 to 1.0)
            confidence: Confidence level in the memory's accuracy (0.0 to 1.0)
            associations: List of IDs of related memory items
            embedding: Vector representation of the memory content
        
        Raises:
            InvalidMemoryFormatError: If required fields are missing or invalid
        """
        super().__init__(
            content=content,
            metadata=metadata or {},
            item_id=item_id or str(uuid.uuid4()),
            created_at=created_at or datetime.now(),
            last_accessed=last_accessed or datetime.now()
        )
        
        # Validate inputs
        if not isinstance(memory_type, MemoryType):
            raise InvalidMemoryFormatError(f"memory_type must be a MemoryType enum, got {type(memory_type)}")
        if not 0.0 <= importance <= 1.0:
            raise InvalidMemoryFormatError(f"importance must be between 0.0 and 1.0, got {importance}")
        if not 0.0 <= confidence <= 1.0:
            raise InvalidMemoryFormatError(f"confidence must be between 0.0 and 1.0, got {confidence}")
            
        self.memory_type = memory_type
        self.importance = importance
        self.confidence = confidence
        self.associations = associations or []
        self.embedding = embedding
        
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the LTM item to a dictionary representation.
        
        Returns:
            Dict containing all LTM item attributes
        """
        base_dict = super().to_dict()
        ltm_dict = {
            "memory_type": self.memory_type.name,
            "importance": self.importance,
            "confidence": self.confidence,
            "associations": self.associations,
            "embedding": self.embedding
        }
        return {**base_dict, **ltm_dict}
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LTMItem':
        """
        Create an LTM item from a dictionary representation.
        
        Args:
            data: Dictionary containing LTM item attributes
            
        Returns:
            Instantiated LTMItem object
            
        Raises:
            InvalidMemoryFormatError: If the dictionary is missing required fields
        """
        try:
            # Extract and convert memory_type from string to enum
            memory_type_str = data.pop("memory_type")
            memory_type = MemoryType[memory_type_str]
            
            # Convert timestamps from strings if needed
            for time_field in ["created_at", "last_accessed"]:
                if time_field in data and isinstance(data[time_field], str):
                    data[time_field] = datetime.fromisoformat(data[time_field])
            
            return cls(memory_type=memory_type, **data)
        except (KeyError, ValueError) as e:
            raise InvalidMemoryFormatError(f"Invalid LTM item format: {str(e)}") from e

class LongTermMemory(MemoryBase):
    """
    Long-Term Memory implementation for the NeuroCognitive Architecture.
    
    Provides persistent storage and retrieval of memories with minimal decay over time.
    Supports different types of long-term memory (declarative, procedural, etc.) and
    implements associative retrieval mechanisms.
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize the Long-Term Memory system.
        
        Args:
            config: Configuration parameters for the LTM system
                - storage_path: Path to persistent storage location
                - embedding_model: Model to use for generating embeddings
                - consolidation_threshold: Threshold for memory consolidation
                - retrieval_similarity_threshold: Minimum similarity for retrieval
        """
        super().__init__()
        self.config = config or {}
        self._storage = {}  # In-memory storage (would be replaced with persistent storage in production)
        
        # Initialize embedding model if specified
        self._embedding_model = None
        if "embedding_model" in self.config:
            # In a real implementation, load the embedding model here
            pass
            
        logger.info("Long-Term Memory system initialized")
    
    def store(self, item: Union[dict[str, Any], LTMItem]) -> str:
        """
        Store a new item in long-term memory.
        
        Args:
            item: Memory item to store (either LTMItem object or dictionary)
            
        Returns:
            ID of the stored memory item
            
        Raises:
            InvalidMemoryFormatError: If the item format is invalid
            MemoryStorageError: If storage fails
        """
        try:
            # Convert dict to LTMItem if needed
            if isinstance(item, dict):
                # Convert string memory_type to enum if needed
                if "memory_type" in item and isinstance(item["memory_type"], str):
                    try:
                        item["memory_type"] = MemoryType[item["memory_type"]]
                    except KeyError:
                        raise InvalidMemoryFormatError(f"Invalid memory_type: {item['memory_type']}")
                
                memory_item = LTMItem(**item)
            elif isinstance(item, LTMItem):
                memory_item = item
            else:
                raise InvalidMemoryFormatError(f"Expected dict or LTMItem, got {type(item)}")
            
            # Generate embeddings if not present and model available
            if memory_item.embedding is None and self._embedding_model is not None:
                # In a real implementation, generate embeddings here
                pass
            
            # Store the item
            self._storage[memory_item.item_id] = memory_item
            
            logger.debug(f"Stored memory item with ID: {memory_item.item_id}")
            return memory_item.item_id
            
        except Exception as e:
            logger.error(f"Failed to store memory item: {str(e)}")
            raise MemoryStorageError(f"Failed to store memory item: {str(e)}") from e
    
    def retrieve(
        self, 
        query: Any, 
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> list[MemoryRetrievalResult]:
        """
        Retrieve items from long-term memory based on query.
        
        Args:
            query: Search query (text, embedding, or other content)
            memory_type: Optional filter for memory type
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold for results
            
        Returns:
            List of memory retrieval results sorted by relevance
            
        Raises:
            MemoryRetrievalError: If retrieval fails
        """
        try:
            results = []
            
            # In a production implementation, this would use vector similarity search
            # For now, implement a simple search mechanism
            for _item_id, item in self._storage.items():
                # Filter by memory type if specified
                if memory_type is not None and item.memory_type != memory_type:
                    continue
                
                # Calculate similarity (simplified implementation)
                # In production, this would use proper vector similarity or other matching
                similarity = self._calculate_similarity(query, item)
                
                if similarity >= threshold:
                    # Update last accessed time
                    item.last_accessed = datetime.now()
                    
                    results.append(MemoryRetrievalResult(
                        item=item,
                        similarity=similarity
                    ))
            
            # Sort by similarity and limit results
            results.sort(key=lambda x: x.similarity, reverse=True)
            results = results[:limit]
            
            logger.debug(f"Retrieved {len(results)} memory items for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory items: {str(e)}")
            raise MemoryRetrievalError(f"Failed to retrieve memory items: {str(e)}") from e
    
    def update(self, item_id: str, updates: dict[str, Any]) -> None:
        """
        Update an existing memory item.
        
        Args:
            item_id: ID of the memory item to update
            updates: Dictionary of fields to update
            
        Raises:
            MemoryNotFoundError: If the item doesn't exist
            InvalidMemoryFormatError: If updates contain invalid values
        """
        if item_id not in self._storage:
            logger.error(f"Memory item not found: {item_id}")
            raise MemoryNotFoundError(f"Memory item not found: {item_id}")
        
        try:
            item = self._storage[item_id]
            
            # Handle special case for memory_type
            if "memory_type" in updates:
                if isinstance(updates["memory_type"], str):
                    updates["memory_type"] = MemoryType[updates["memory_type"]]
                elif not isinstance(updates["memory_type"], MemoryType):
                    raise InvalidMemoryFormatError(f"Invalid memory_type: {updates['memory_type']}")
            
            # Update fields
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
                else:
                    # Add to metadata if not a direct attribute
                    item.metadata[key] = value
            
            logger.debug(f"Updated memory item: {item_id}")
            
        except Exception as e:
            logger.error(f"Failed to update memory item: {str(e)}")
            raise InvalidMemoryFormatError(f"Failed to update memory item: {str(e)}") from e
    
    def delete(self, item_id: str) -> None:
        """
        Delete a memory item.
        
        Args:
            item_id: ID of the memory item to delete
            
        Raises:
            MemoryNotFoundError: If the item doesn't exist
        """
        if item_id not in self._storage:
            logger.error(f"Memory item not found: {item_id}")
            raise MemoryNotFoundError(f"Memory item not found: {item_id}")
        
        del self._storage[item_id]
        logger.debug(f"Deleted memory item: {item_id}")
    
    def consolidate(self, items: list[dict[str, Any]]) -> list[str]:
        """
        Consolidate items from working memory into long-term memory.
        
        Args:
            items: List of memory items to consolidate
            
        Returns:
            List of IDs of consolidated memory items
            
        Raises:
            MemoryConsolidationError: If consolidation fails
        """
        try:
            consolidated_ids = []
            
            for item in items:
                # Apply consolidation logic (e.g., importance threshold)
                importance = item.get("importance", 0.0)
                threshold = self.config.get("consolidation_threshold", 0.3)
                
                if importance >= threshold:
                    # Determine memory type based on content and metadata
                    memory_type = self._determine_memory_type(item)
                    
                    # Store in long-term memory
                    ltm_item = {
                        "content": item.get("content"),
                        "memory_type": memory_type,
                        "metadata": item.get("metadata", {}),
                        "importance": importance,
                        "confidence": item.get("confidence", 1.0)
                    }
                    
                    item_id = self.store(ltm_item)
                    consolidated_ids.append(item_id)
            
            logger.info(f"Consolidated {len(consolidated_ids)} items into long-term memory")
            return consolidated_ids
            
        except Exception as e:
            logger.error(f"Memory consolidation failed: {str(e)}")
            raise MemoryConsolidationError(f"Memory consolidation failed: {str(e)}") from e
    
    def get_associations(self, item_id: str, depth: int = 1) -> list[tuple[str, float]]:
        """
        Get associated memory items for a given item.
        
        Args:
            item_id: ID of the memory item
            depth: Depth of association traversal
            
        Returns:
            List of tuples containing (item_id, association_strength)
            
        Raises:
            MemoryNotFoundError: If the item doesn't exist
        """
        if item_id not in self._storage:
            logger.error(f"Memory item not found: {item_id}")
            raise MemoryNotFoundError(f"Memory item not found: {item_id}")
        
        item = self._storage[item_id]
        associations = []
        
        # Get direct associations
        for assoc_id in item.associations:
            if assoc_id in self._storage:
                # Calculate association strength (simplified)
                strength = 0.8  # In production, this would be calculated based on various factors
                associations.append((assoc_id, strength))
        
        # If depth > 1, recursively get associations of associations
        if depth > 1:
            indirect_associations = []
            for assoc_id, strength in associations:
                # Recursive call with reduced depth
                next_level = self.get_associations(assoc_id, depth - 1)
                # Adjust strength based on distance
                indirect_associations.extend([(id, s * strength) for id, s in next_level])
            
            # Combine and deduplicate
            all_assocs = dict(associations)
            for id, strength in indirect_associations:
                if id != item_id:  # Avoid self-references
                    all_assocs[id] = max(all_assocs.get(id, 0), strength)
            
            associations = [(id, strength) for id, strength in all_assocs.items()]
        
        # Sort by association strength
        associations.sort(key=lambda x: x[1], reverse=True)
        return associations
    
    def _calculate_similarity(self, query: Any, item: LTMItem) -> float:
        """
        Calculate similarity between query and memory item.
        
        Args:
            query: Search query
            item: Memory item
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # In a production implementation, this would use proper vector similarity
        # or other matching algorithms depending on the query and item types
        
        # Simple implementation for demonstration
        if isinstance(query, str) and isinstance(item.content, str):
            # Simple text matching (very basic)
            query_words = set(query.lower().split())
            content_words = set(item.content.lower().split())
            
            if not query_words or not content_words:
                return 0.0
                
            # Jaccard similarity
            intersection = len(query_words.intersection(content_words))
            union = len(query_words.union(content_words))
            return intersection / union if union > 0 else 0.0
            
        # Default similarity for non-text content
        return 0.0
    
    def _determine_memory_type(self, item: dict[str, Any]) -> MemoryType:
        """
        Determine the appropriate memory type for an item.
        
        Args:
            item: Memory item data
            
        Returns:
            Appropriate MemoryType enum value
        """
        # If memory_type is already specified, use it
        if "memory_type" in item:
            if isinstance(item["memory_type"], MemoryType):
                return item["memory_type"]
            elif isinstance(item["memory_type"], str):
                try:
                    return MemoryType[item["memory_type"]]
                except KeyError:
                    pass
        
        # Otherwise, infer from content and metadata
        metadata = item.get("metadata", {})
        content = item.get("content", "")
        
        # Simple heuristics for memory type classification
        if metadata.get("is_procedural", False) or "how to" in str(content).lower():
            return MemoryType.PROCEDURAL
        elif metadata.get("is_episodic", False) or metadata.get("timestamp"):
            return MemoryType.EPISODIC
        elif metadata.get("is_semantic", False) or metadata.get("is_concept", False):
            return MemoryType.SEMANTIC
        
        # Default to declarative
        return MemoryType.DECLARATIVE

# Export public interfaces
__all__ = [
    'LongTermMemory',
    'LTMItem',
    'MemoryType',
    'MemoryRetrievalResult'
]