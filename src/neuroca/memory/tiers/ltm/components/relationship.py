"""
LTM Relationship Management

This module provides the LTMRelationship class which handles the creation,
maintenance, and querying of relationships between memories in the LTM tier.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.backends import BaseStorageBackend
from neuroca.memory.exceptions import TierOperationError


logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of relationships between concepts in long-term memory."""
    IS_A = "is_a"  # Taxonomy/inheritance relationship
    HAS_A = "has_a"  # Composition relationship
    PART_OF = "part_of"  # Part-whole relationship
    RELATED_TO = "related_to"  # Generic relationship
    OPPOSITE_OF = "opposite_of"  # Antonym relationship
    SIMILAR_TO = "similar_to"  # Synonym/similar relationship
    CAUSES = "causes"  # Causal relationship
    PRECEDES = "precedes"  # Temporal relationship
    LOCATED_IN = "located_in"  # Spatial relationship


class Concept:
    """
    Represents a semantic concept stored in long-term memory.
    
    This class models a concept in a semantic network, which can have
    properties, relationships to other concepts, and taxonomic classifications.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a concept.
        
        Args:
            id: Unique identifier for this concept
            name: Human-readable name
            description: Description of the concept
            properties: Dictionary of properties
        """
        self.id = id
        self.name = name
        self.description = description
        self.properties = properties or {}
    
    def __str__(self) -> str:
        return f"Concept(id={self.id}, name={self.name})"


class Relationship:
    """
    Represents a semantic relationship between two concepts.
    
    This class models a directed edge in a semantic network, connecting
    a source concept to a target concept with a specific relationship type.
    """
    
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a relationship.
        
        Args:
            source_id: ID of the source concept
            target_id: ID of the target concept
            relationship_type: Type of relationship
            strength: Strength of relationship (0.0 to 1.0)
            metadata: Additional metadata
        """
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type
        self.strength = strength
        self.metadata = metadata or {}
    
    def __str__(self) -> str:
        return f"Relationship({self.source_id} --{self.relationship_type.value}--> {self.target_id})"


class LTMRelationship:
    """
    Manages relationships between memories in the LTM tier.
    
    This class provides methods for creating, updating, and querying
    relationships between memories, which is a key feature of long-term memory.
    """
    
    RELATIONSHIP_TYPES = {
        "semantic": "Semantic relationship based on content similarity",
        "causal": "One memory caused or led to another",
        "temporal": "Memories occurred close in time",
        "spatial": "Memories occurred in the same location",
        "associative": "Memories are associated through shared context",
        "hierarchical": "One memory is a part or subset of another",
        "contradictory": "Memories contain contradictory information",
    }
    
    def __init__(self, tier_name: str):
        """
        Initialize the relationship manager.
        
        Args:
            tier_name: The name of the tier (always "ltm" for this class)
        """
        self._tier_name = tier_name
        self._lifecycle = None
        self._backend = None
        self._update_func = None  # Function to update a memory
    
    def configure(
        self, 
        lifecycle: Any, 
        backend: BaseStorageBackend,
        update_func: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the relationship manager.
        
        Args:
            lifecycle: The lifecycle manager, used to access relationship map
            backend: The storage backend
            update_func: Function to call for updating a memory
            config: Configuration options
        """
        self._lifecycle = lifecycle
        self._backend = backend
        self._update_func = update_func
        
        # Load custom relationship types if configured
        if "relationship_types" in config:
            self.RELATIONSHIP_TYPES.update(config["relationship_types"])
    
    def process_on_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when stored to initialize relationships.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Initialize relationships container if not present
        if "relationships" not in memory_item.metadata.tags:
            memory_item.metadata.tags["relationships"] = {}
    
    def process_pre_delete(self, memory_id: str) -> None:
        """
        Process a memory before deletion to clean up relationships.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Update the lifecycle relationship map to remove this memory
        if self._lifecycle:
            self._lifecycle.remove_memory(memory_id)
    
    async def add_relationship(
        self,
        memory_id: str,
        related_id: str,
        relationship_type: str = "semantic",
        strength: float = 0.5,
        bidirectional: bool = True
    ) -> bool:
        """
        Add a relationship between two memories.
        
        Args:
            memory_id: The ID of the source memory
            related_id: The ID of the target memory
            relationship_type: Type of relationship
            strength: Relationship strength (0.0 to 1.0)
            bidirectional: Whether to create the reverse relationship too
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ValueError: If parameters are invalid
            TierOperationError: If the operation fails
        """
        # Validate parameters
        if memory_id == related_id:
            raise ValueError("Cannot create a relationship with itself")
            
        if relationship_type not in self.RELATIONSHIP_TYPES:
            raise ValueError(f"Invalid relationship type: {relationship_type}")
            
        if strength < 0.0 or strength > 1.0:
            raise ValueError("Strength must be between 0.0 and 1.0")
        
        # Get the source memory
        source_data = await self._backend.retrieve(memory_id)
        if source_data is None:
            raise TierOperationError(
                operation="add_relationship",
                tier_name=self._tier_name,
                message=f"Source memory {memory_id} not found"
            )
        
        # Get the target memory
        target_data = await self._backend.retrieve(related_id)
        if target_data is None:
            raise TierOperationError(
                operation="add_relationship",
                tier_name=self._tier_name,
                message=f"Target memory {related_id} not found"
            )
        
        # Update source memory relationships
        source_memory = MemoryItem.model_validate(source_data)
        
        # Initialize relationships dict if not present
        if "relationships" not in source_memory.metadata.tags:
            source_memory.metadata.tags["relationships"] = {}
        
        # Create or update the relationship
        relationship_data = {
            "type": relationship_type,
            "strength": strength
        }
        source_memory.metadata.tags["relationships"][related_id] = relationship_data
        
        # Update the memory
        source_success = await self._update_func(memory_id, metadata=source_memory.metadata.tags)
        
        # Update relationship map
        if source_success and self._lifecycle:
            self._lifecycle.update_relationship(memory_id, related_id, strength)
        
        # Create bidirectional relationship if requested
        target_success = True
        if bidirectional:
            target_memory = MemoryItem.model_validate(target_data)
            
            # Initialize relationships dict if not present
            if "relationships" not in target_memory.metadata.tags:
                target_memory.metadata.tags["relationships"] = {}
            
            # Create or update the reverse relationship
            target_memory.metadata.tags["relationships"][memory_id] = relationship_data
            
            # Update the target memory
            target_success = await self._update_func(related_id, metadata=target_memory.metadata.tags)
            
            # Update relationship map
            if target_success and self._lifecycle:
                self._lifecycle.update_relationship(related_id, memory_id, strength)
        
        return source_success and target_success
    
    async def remove_relationship(
        self,
        memory_id: str,
        related_id: str,
        bidirectional: bool = True
    ) -> bool:
        """
        Remove a relationship between two memories.
        
        Args:
            memory_id: The ID of the source memory
            related_id: The ID of the target memory
            bidirectional: Whether to remove the reverse relationship too
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the source memory
        source_data = await self._backend.retrieve(memory_id)
        if source_data is None:
            raise TierOperationError(
                operation="remove_relationship",
                tier_name=self._tier_name,
                message=f"Source memory {memory_id} not found"
            )
        
        # Update source memory relationships
        source_memory = MemoryItem.model_validate(source_data)
        
        # Remove the relationship if it exists
        if "relationships" in source_memory.metadata.tags:
            if related_id in source_memory.metadata.tags["relationships"]:
                del source_memory.metadata.tags["relationships"][related_id]
        
        # Update the memory
        source_success = await self._update_func(memory_id, metadata=source_memory.metadata.tags)
        
        # Update relationship map
        if source_success and self._lifecycle:
            # Update by directly modifying the map - remove_relationship not available
            relationship_map = self._lifecycle.get_relationship_map()
            if memory_id in relationship_map and related_id in relationship_map[memory_id]:
                # Update the cached copy directly
                if memory_id in relationship_map:
                    rel_dict = relationship_map[memory_id]
                    if related_id in rel_dict:
                        del rel_dict[related_id]
        
        # Remove bidirectional relationship if requested and target exists
        target_success = True
        if bidirectional:
            target_data = await self._backend.retrieve(related_id)
            if target_data is not None:
                target_memory = MemoryItem.model_validate(target_data)
                
                # Remove the reverse relationship if it exists
                if "relationships" in target_memory.metadata.tags:
                    if memory_id in target_memory.metadata.tags["relationships"]:
                        del target_memory.metadata.tags["relationships"][memory_id]
                
                # Update the target memory
                target_success = await self._update_func(related_id, metadata=target_memory.metadata.tags)
                
                # Update relationship map
                if target_success and self._lifecycle:
                    # Update by directly modifying the map
                    relationship_map = self._lifecycle.get_relationship_map()
                    if related_id in relationship_map and memory_id in relationship_map[related_id]:
                        # Update the cached copy directly
                        if related_id in relationship_map:
                            rel_dict = relationship_map[related_id]
                            if memory_id in rel_dict:
                                del rel_dict[memory_id]
        
        return source_success and target_success
    
    async def get_related_memories(
        self,
        memory_id: str,
        relationship_type: Optional[str] = None,
        min_strength: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get memories related to the specified memory.
        
        Args:
            memory_id: The ID of the memory
            relationship_type: Type of relationship to filter by (or None for all)
            min_strength: Minimum relationship strength
            limit: Maximum number of memories to return
            
        Returns:
            List of related memories with relationship metadata
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Get the source memory
        source_data = await self._backend.retrieve(memory_id)
        if source_data is None:
            raise TierOperationError(
                operation="get_related_memories",
                tier_name=self._tier_name,
                message=f"Memory {memory_id} not found"
            )
        
        source_memory = MemoryItem.model_validate(source_data)
        
        # Get relationships from memory
        relationships = source_memory.metadata.tags.get("relationships", {})
        
        # Filter relationships
        filtered_relationships = {}
        for related_id, rel_data in relationships.items():
            rel_type = rel_data.get("type", "semantic")
            rel_strength = rel_data.get("strength", 0.5)
            
            # Apply filters
            if relationship_type is not None and rel_type != relationship_type:
                continue
                
            if rel_strength < min_strength:
                continue
                
            filtered_relationships[related_id] = rel_data
        
        # Sort by strength (descending)
        sorted_related_ids = sorted(
            filtered_relationships.keys(),
            key=lambda id: filtered_relationships[id].get("strength", 0.0),
            reverse=True
        )
        
        # Limit the number of results
        sorted_related_ids = sorted_related_ids[:limit]
        
        # Fetch related memories
        related_memories = []
        for related_id in sorted_related_ids:
            related_data = await self._backend.retrieve(related_id)
            if related_data is not None:
                # Add relationship data to the memory
                related_data["_relationship"] = filtered_relationships[related_id]
                related_memories.append(related_data)
        
        return related_memories
    
    async def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 3
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find a path between two memories through relationships.
        
        Args:
            start_id: The ID of the starting memory
            end_id: The ID of the ending memory
            max_depth: Maximum path length/depth
            
        Returns:
            List of memories forming the path, or None if no path found
            
        Raises:
            TierOperationError: If the operation fails
        """
        # Breadth-first search to find the shortest path
        visited = set()
        queue = [(start_id, [])]  # (memory_id, path_so_far)
        
        while queue:
            current_id, path = queue.pop(0)
            
            # Skip if already visited
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            # Get the current memory
            current_data = await self._backend.retrieve(current_id)
            if current_data is None:
                continue
                
            current_memory = MemoryItem.model_validate(current_data)
            current_path = path + [current_data]
            
            # Check if we've reached the end
            if current_id == end_id:
                return current_path
                
            # Stop if we've reached the maximum depth
            if len(current_path) >= max_depth:
                continue
                
            # Get relationships from memory
            relationships = current_memory.metadata.tags.get("relationships", {})
            
            # Add related memories to the queue
            for related_id in relationships:
                if related_id not in visited:
                    queue.append((related_id, current_path))
        
        # No path found
        return None
