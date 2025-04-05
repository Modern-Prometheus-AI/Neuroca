"""
Pathways Module for NeuroCognitive Architecture (NCA)

This module implements the neural pathways that connect different memory tubules
in the NCA memory system. Pathways represent the connections between memory components,
facilitating information flow, association building, and memory consolidation.

The implementation is inspired by biological neural pathways that connect different
brain regions, allowing for complex cognitive processes like memory formation,
recall, and association.

Usage:
    from neuroca.memory.tubules.pathways import Pathway, PathwayManager
    
    # Create pathways between memory components
    pathway = Pathway(source_id="semantic_123", target_id="episodic_456", 
                     strength=0.75, pathway_type=PathwayType.ASSOCIATIVE)
    
    # Register pathway with the manager
    pathway_manager = PathwayManager()
    pathway_manager.register_pathway(pathway)
    
    # Activate pathways to facilitate memory retrieval
    activated_targets = pathway_manager.activate_pathways(source_id="semantic_123", 
                                                         activation_threshold=0.5)
"""

import enum
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np

from neuroca.core.exceptions import PathwayError, ValidationError

# Configure logger
logger = logging.getLogger(__name__)


class PathwayType(enum.Enum):
    """
    Enumeration of different types of pathways between memory tubules.
    
    Each type represents a different kind of relationship or connection
    between memory components, inspired by biological neural pathways.
    """
    ASSOCIATIVE = "associative"  # Connects related concepts/memories
    HIERARCHICAL = "hierarchical"  # Connects general to specific memories
    TEMPORAL = "temporal"  # Connects sequential memories
    CAUSAL = "causal"  # Connects cause-effect memories
    EMOTIONAL = "emotional"  # Connects memories with emotional valence
    CONTEXTUAL = "contextual"  # Connects memories sharing context


@dataclass
class PathwayMetrics:
    """
    Metrics and statistics for a pathway to track its usage and effectiveness.
    
    These metrics help in pathway maintenance, pruning, and optimization.
    """
    creation_time: datetime = field(default_factory=datetime.now)
    last_activation: Optional[datetime] = None
    activation_count: int = 0
    success_rate: float = 1.0  # Ratio of successful activations
    average_activation_time: float = 0.0  # In milliseconds
    
    def record_activation(self, success: bool, activation_time_ms: float) -> None:
        """
        Record a pathway activation event and update metrics.
        
        Args:
            success: Whether the activation was successful
            activation_time_ms: Time taken for activation in milliseconds
        """
        self.last_activation = datetime.now()
        self.activation_count += 1
        
        # Update success rate using weighted average
        if self.activation_count > 1:
            weight = 1.0 / self.activation_count
            self.success_rate = (self.success_rate * (1 - weight)) + (float(success) * weight)
        else:
            self.success_rate = float(success)
            
        # Update average activation time
        if self.activation_count > 1:
            self.average_activation_time = (
                (self.average_activation_time * (self.activation_count - 1) + activation_time_ms) / 
                self.activation_count
            )
        else:
            self.average_activation_time = activation_time_ms


@dataclass
class Pathway:
    """
    Represents a connection between two memory tubules in the NCA system.
    
    A pathway facilitates information flow between memory components and
    can have different types, strengths, and directionality.
    """
    source_id: str
    target_id: str
    pathway_type: PathwayType
    strength: float = 0.5  # Connection strength (0.0 to 1.0)
    bidirectional: bool = False  # Whether the connection works both ways
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    metrics: PathwayMetrics = field(default_factory=PathwayMetrics)
    
    def __post_init__(self) -> None:
        """Validate pathway attributes after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate pathway attributes to ensure they meet requirements.
        
        Raises:
            ValidationError: If any attribute fails validation
        """
        if not self.source_id:
            raise ValidationError("Pathway source_id cannot be empty")
        
        if not self.target_id:
            raise ValidationError("Pathway target_id cannot be empty")
            
        if self.source_id == self.target_id:
            raise ValidationError("Pathway source and target cannot be the same")
            
        if not isinstance(self.pathway_type, PathwayType):
            raise ValidationError(f"Invalid pathway_type: {self.pathway_type}")
            
        if not 0.0 <= self.strength <= 1.0:
            raise ValidationError(f"Pathway strength must be between 0.0 and 1.0, got {self.strength}")
    
    def strengthen(self, amount: float = 0.1) -> None:
        """
        Increase the strength of the pathway, simulating learning or reinforcement.
        
        Args:
            amount: Amount to increase strength by (default: 0.1)
            
        Raises:
            ValidationError: If resulting strength would be invalid
        """
        new_strength = min(1.0, self.strength + amount)
        if new_strength < 0.0 or new_strength > 1.0:
            raise ValidationError(f"Invalid strength adjustment: {amount}")
            
        self.strength = new_strength
        self.last_modified = datetime.now()
        logger.debug(f"Pathway {self.id} strengthened to {self.strength}")
    
    def weaken(self, amount: float = 0.1) -> None:
        """
        Decrease the strength of the pathway, simulating forgetting or decay.
        
        Args:
            amount: Amount to decrease strength by (default: 0.1)
            
        Raises:
            ValidationError: If resulting strength would be invalid
        """
        new_strength = max(0.0, self.strength - amount)
        if new_strength < 0.0 or new_strength > 1.0:
            raise ValidationError(f"Invalid strength adjustment: {amount}")
            
        self.strength = new_strength
        self.last_modified = datetime.now()
        logger.debug(f"Pathway {self.id} weakened to {self.strength}")
    
    def activate(self, activation_strength: float = 1.0) -> float:
        """
        Activate the pathway with a given strength and return the output activation.
        
        Args:
            activation_strength: Input activation strength (0.0 to 1.0)
            
        Returns:
            float: Output activation strength (pathway strength * input strength)
            
        Raises:
            ValidationError: If activation_strength is invalid
        """
        if not 0.0 <= activation_strength <= 1.0:
            raise ValidationError(f"Activation strength must be between 0.0 and 1.0, got {activation_strength}")
        
        start_time = time.time()
        
        # Calculate output activation
        output_activation = self.strength * activation_strength
        
        # Record activation metrics
        activation_time_ms = (time.time() - start_time) * 1000
        success = output_activation >= 0.1  # Consider activation successful if output is significant
        self.metrics.record_activation(success, activation_time_ms)
        
        logger.debug(f"Pathway {self.id} activated: {activation_strength} -> {output_activation}")
        return output_activation
    
    def to_dict(self) -> dict:
        """
        Convert the pathway to a dictionary representation.
        
        Returns:
            Dict: Dictionary representation of the pathway
        """
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "pathway_type": self.pathway_type.value,
            "strength": self.strength,
            "bidirectional": self.bidirectional,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "metadata": self.metadata,
            "metrics": {
                "creation_time": self.metrics.creation_time.isoformat(),
                "last_activation": self.metrics.last_activation.isoformat() if self.metrics.last_activation else None,
                "activation_count": self.metrics.activation_count,
                "success_rate": self.metrics.success_rate,
                "average_activation_time": self.metrics.average_activation_time
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Pathway':
        """
        Create a Pathway instance from a dictionary representation.
        
        Args:
            data: Dictionary containing pathway data
            
        Returns:
            Pathway: New Pathway instance
            
        Raises:
            ValidationError: If dictionary data is invalid
        """
        try:
            # Create metrics object
            metrics_data = data.get("metrics", {})
            metrics = PathwayMetrics(
                creation_time=datetime.fromisoformat(metrics_data.get("creation_time", datetime.now().isoformat())),
                last_activation=datetime.fromisoformat(metrics_data.get("last_activation")) if metrics_data.get("last_activation") else None,
                activation_count=metrics_data.get("activation_count", 0),
                success_rate=metrics_data.get("success_rate", 1.0),
                average_activation_time=metrics_data.get("average_activation_time", 0.0)
            )
            
            # Create pathway object
            return cls(
                id=data.get("id", str(uuid.uuid4())),
                source_id=data["source_id"],
                target_id=data["target_id"],
                pathway_type=PathwayType(data["pathway_type"]),
                strength=data.get("strength", 0.5),
                bidirectional=data.get("bidirectional", False),
                created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                last_modified=datetime.fromisoformat(data.get("last_modified", datetime.now().isoformat())),
                metadata=data.get("metadata", {}),
                metrics=metrics
            )
        except (KeyError, ValueError) as e:
            raise ValidationError(f"Invalid pathway data: {str(e)}") from e


class PathwayManager:
    """
    Manages the creation, storage, retrieval, and activation of pathways between memory tubules.
    
    The PathwayManager is responsible for maintaining the network of connections
    between memory components and facilitating information flow through these connections.
    """
    
    def __init__(self) -> None:
        """Initialize the PathwayManager with empty pathway collections."""
        # Main pathway storage: pathway_id -> Pathway
        self._pathways: dict[str, Pathway] = {}
        
        # Index for source_id -> set of pathway_ids
        self._source_index: dict[str, set[str]] = {}
        
        # Index for target_id -> set of pathway_ids
        self._target_index: dict[str, set[str]] = {}
        
        # Index for pathway_type -> set of pathway_ids
        self._type_index: dict[PathwayType, set[str]] = {
            pathway_type: set() for pathway_type in PathwayType
        }
        
        logger.info("PathwayManager initialized")
    
    def register_pathway(self, pathway: Pathway) -> str:
        """
        Register a new pathway in the manager.
        
        Args:
            pathway: The pathway to register
            
        Returns:
            str: ID of the registered pathway
            
        Raises:
            PathwayError: If pathway already exists or is invalid
        """
        # Validate pathway
        if pathway.id in self._pathways:
            raise PathwayError(f"Pathway with ID {pathway.id} already exists")
        
        # Store pathway
        self._pathways[pathway.id] = pathway
        
        # Update indices
        if pathway.source_id not in self._source_index:
            self._source_index[pathway.source_id] = set()
        self._source_index[pathway.source_id].add(pathway.id)
        
        if pathway.target_id not in self._target_index:
            self._target_index[pathway.target_id] = set()
        self._target_index[pathway.target_id].add(pathway.id)
        
        self._type_index[pathway.pathway_type].add(pathway.id)
        
        # If bidirectional, create reverse pathway reference in indices
        if pathway.bidirectional:
            if pathway.target_id not in self._source_index:
                self._source_index[pathway.target_id] = set()
            self._source_index[pathway.target_id].add(pathway.id)
            
            if pathway.source_id not in self._target_index:
                self._target_index[pathway.source_id] = set()
            self._target_index[pathway.source_id].add(pathway.id)
        
        logger.debug(f"Registered pathway {pathway.id}: {pathway.source_id} -> {pathway.target_id}")
        return pathway.id
    
    def get_pathway(self, pathway_id: str) -> Pathway:
        """
        Retrieve a pathway by its ID.
        
        Args:
            pathway_id: ID of the pathway to retrieve
            
        Returns:
            Pathway: The requested pathway
            
        Raises:
            PathwayError: If pathway does not exist
        """
        if pathway_id not in self._pathways:
            raise PathwayError(f"Pathway with ID {pathway_id} not found")
        
        return self._pathways[pathway_id]
    
    def remove_pathway(self, pathway_id: str) -> None:
        """
        Remove a pathway from the manager.
        
        Args:
            pathway_id: ID of the pathway to remove
            
        Raises:
            PathwayError: If pathway does not exist
        """
        if pathway_id not in self._pathways:
            raise PathwayError(f"Pathway with ID {pathway_id} not found")
        
        pathway = self._pathways[pathway_id]
        
        # Remove from indices
        if pathway.source_id in self._source_index:
            self._source_index[pathway.source_id].discard(pathway_id)
            if not self._source_index[pathway.source_id]:
                del self._source_index[pathway.source_id]
        
        if pathway.target_id in self._target_index:
            self._target_index[pathway.target_id].discard(pathway_id)
            if not self._target_index[pathway.target_id]:
                del self._target_index[pathway.target_id]
        
        self._type_index[pathway.pathway_type].discard(pathway_id)
        
        # If bidirectional, remove reverse references
        if pathway.bidirectional:
            if pathway.target_id in self._source_index:
                self._source_index[pathway.target_id].discard(pathway_id)
                if not self._source_index[pathway.target_id]:
                    del self._source_index[pathway.target_id]
            
            if pathway.source_id in self._target_index:
                self._target_index[pathway.source_id].discard(pathway_id)
                if not self._target_index[pathway.source_id]:
                    del self._target_index[pathway.source_id]
        
        # Remove pathway
        del self._pathways[pathway_id]
        logger.debug(f"Removed pathway {pathway_id}")
    
    def get_pathways_from_source(self, source_id: str) -> list[Pathway]:
        """
        Get all pathways originating from a specific source.
        
        Args:
            source_id: ID of the source tubule
            
        Returns:
            List[Pathway]: List of pathways from the source
        """
        if source_id not in self._source_index:
            return []
        
        return [self._pathways[pid] for pid in self._source_index[source_id]]
    
    def get_pathways_to_target(self, target_id: str) -> list[Pathway]:
        """
        Get all pathways leading to a specific target.
        
        Args:
            target_id: ID of the target tubule
            
        Returns:
            List[Pathway]: List of pathways to the target
        """
        if target_id not in self._target_index:
            return []
        
        return [self._pathways[pid] for pid in self._target_index[target_id]]
    
    def get_pathways_by_type(self, pathway_type: PathwayType) -> list[Pathway]:
        """
        Get all pathways of a specific type.
        
        Args:
            pathway_type: Type of pathways to retrieve
            
        Returns:
            List[Pathway]: List of pathways of the specified type
        """
        return [self._pathways[pid] for pid in self._type_index[pathway_type]]
    
    def get_connected_tubules(self, tubule_id: str) -> set[str]:
        """
        Get all tubules connected to a specific tubule (in either direction).
        
        Args:
            tubule_id: ID of the tubule
            
        Returns:
            Set[str]: Set of connected tubule IDs
        """
        connected = set()
        
        # Get tubules connected as targets
        if tubule_id in self._source_index:
            for pid in self._source_index[tubule_id]:
                pathway = self._pathways[pid]
                connected.add(pathway.target_id)
        
        # Get tubules connected as sources
        if tubule_id in self._target_index:
            for pid in self._target_index[tubule_id]:
                pathway = self._pathways[pid]
                # Only add if not bidirectional (to avoid duplicates)
                if not pathway.bidirectional:
                    connected.add(pathway.source_id)
        
        return connected
    
    def activate_pathways(
        self, 
        source_id: str, 
        activation_strength: float = 1.0,
        activation_threshold: float = 0.1
    ) -> dict[str, float]:
        """
        Activate all pathways from a source and return activated targets with their strengths.
        
        Args:
            source_id: ID of the source tubule
            activation_strength: Strength of the initial activation (0.0 to 1.0)
            activation_threshold: Minimum activation strength to include in results
            
        Returns:
            Dict[str, float]: Dictionary mapping target_ids to their activation strengths
            
        Raises:
            ValidationError: If activation parameters are invalid
        """
        if not 0.0 <= activation_strength <= 1.0:
            raise ValidationError(f"Activation strength must be between 0.0 and 1.0, got {activation_strength}")
        
        if not 0.0 <= activation_threshold <= 1.0:
            raise ValidationError(f"Activation threshold must be between 0.0 and 1.0, got {activation_threshold}")
        
        activated_targets = {}
        
        # Get all pathways from the source
        pathways = self.get_pathways_from_source(source_id)
        
        # Activate each pathway
        for pathway in pathways:
            output_activation = pathway.activate(activation_strength)
            
            # Only include targets with activation above threshold
            if output_activation >= activation_threshold:
                # If target already activated, use maximum activation
                if pathway.target_id in activated_targets:
                    activated_targets[pathway.target_id] = max(
                        activated_targets[pathway.target_id], 
                        output_activation
                    )
                else:
                    activated_targets[pathway.target_id] = output_activation
        
        logger.debug(f"Activated {len(activated_targets)} targets from source {source_id}")
        return activated_targets
    
    def spread_activation(
        self,
        initial_activations: dict[str, float],
        max_depth: int = 3,
        decay_factor: float = 0.7,
        activation_threshold: float = 0.1
    ) -> dict[str, float]:
        """
        Spread activation through the pathway network from multiple initial sources.
        
        This implements spreading activation, a cognitive science concept where
        activation flows from initially activated nodes to connected nodes.
        
        Args:
            initial_activations: Dictionary mapping tubule_ids to initial activation strengths
            max_depth: Maximum propagation depth
            decay_factor: Factor by which activation decays at each step (0.0 to 1.0)
            activation_threshold: Minimum activation strength to continue propagation
            
        Returns:
            Dict[str, float]: Dictionary mapping all activated tubule_ids to their final activation strengths
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not 0.0 <= decay_factor <= 1.0:
            raise ValidationError(f"Decay factor must be between 0.0 and 1.0, got {decay_factor}")
        
        if not 0.0 <= activation_threshold <= 1.0:
            raise ValidationError(f"Activation threshold must be between 0.0 and 1.0, got {activation_threshold}")
        
        if max_depth < 1:
            raise ValidationError(f"Max depth must be at least 1, got {max_depth}")
        
        # Initialize with the starting activations
        all_activations = dict(initial_activations)
        current_activations = dict(initial_activations)
        
        # Track which tubules have been processed at each depth
        processed = set()
        
        # Spread activation for max_depth steps
        for _depth in range(max_depth):
            next_activations = {}
            
            # Process each currently activated tubule
            for tubule_id, activation in current_activations.items():
                # Skip if activation is below threshold
                if activation < activation_threshold:
                    continue
                
                # Skip if already processed at this depth to prevent cycles
                if tubule_id in processed:
                    continue
                
                processed.add(tubule_id)
                
                # Get all pathways from this tubule
                pathways = self.get_pathways_from_source(tubule_id)
                
                # Activate each pathway
                for pathway in pathways:
                    # Calculate decayed activation
                    output_activation = pathway.activate(activation) * decay_factor
                    
                    # Skip if below threshold
                    if output_activation < activation_threshold:
                        continue
                    
                    target_id = pathway.target_id
                    
                    # Update next_activations with maximum activation
                    if target_id in next_activations:
                        next_activations[target_id] = max(
                            next_activations[target_id],
                            output_activation
                        )
                    else:
                        next_activations[target_id] = output_activation
                    
                    # Update all_activations with maximum activation
                    if target_id in all_activations:
                        all_activations[target_id] = max(
                            all_activations[target_id],
                            output_activation
                        )
                    else:
                        all_activations[target_id] = output_activation
            
            # If no new activations, stop spreading
            if not next_activations:
                break
            
            # Update current activations for next iteration
            current_activations = next_activations
            # Reset processed set for next depth level
            processed = set()
        
        logger.debug(f"Spread activation to {len(all_activations)} tubules (max depth: {max_depth})")
        return all_activations
    
    def create_pathway(
        self,
        source_id: str,
        target_id: str,
        pathway_type: PathwayType,
        strength: float = 0.5,
        bidirectional: bool = False,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Create and register a new pathway.
        
        Args:
            source_id: ID of the source tubule
            target_id: ID of the target tubule
            pathway_type: Type of the pathway
            strength: Initial strength of the pathway (0.0 to 1.0)
            bidirectional: Whether the pathway is bidirectional
            metadata: Optional metadata for the pathway
            
        Returns:
            str: ID of the created pathway
            
        Raises:
            ValidationError: If pathway parameters are invalid
        """
        pathway = Pathway(
            source_id=source_id,
            target_id=target_id,
            pathway_type=pathway_type,
            strength=strength,
            bidirectional=bidirectional,
            metadata=metadata or {}
        )
        
        return self.register_pathway(pathway)
    
    def strengthen_pathway(self, pathway_id: str, amount: float = 0.1) -> None:
        """
        Strengthen an existing pathway.
        
        Args:
            pathway_id: ID of the pathway to strengthen
            amount: Amount to increase strength by (default: 0.1)
            
        Raises:
            PathwayError: If pathway does not exist
        """
        pathway = self.get_pathway(pathway_id)
        pathway.strengthen(amount)
    
    def weaken_pathway(self, pathway_id: str, amount: float = 0.1) -> None:
        """
        Weaken an existing pathway.
        
        Args:
            pathway_id: ID of the pathway to weaken
            amount: Amount to decrease strength by (default: 0.1)
            
        Raises:
            PathwayError: If pathway does not exist
        """
        pathway = self.get_pathway(pathway_id)
        pathway.weaken(amount)
    
    def prune_weak_pathways(self, threshold: float = 0.1) -> int:
        """
        Remove all pathways with strength below the threshold.
        
        Args:
            threshold: Strength threshold below which to remove pathways
            
        Returns:
            int: Number of pathways removed
        """
        weak_pathways = [
            pid for pid, pathway in self._pathways.items() 
            if pathway.strength < threshold
        ]
        
        for pid in weak_pathways:
            self.remove_pathway(pid)
        
        logger.info(f"Pruned {len(weak_pathways)} weak pathways (threshold: {threshold})")
        return len(weak_pathways)
    
    def find_path(
        self, 
        source_id: str, 
        target_id: str, 
        max_depth: int = 5
    ) -> Optional[list[Pathway]]:
        """
        Find a path between source and target tubules through the pathway network.
        
        Uses breadth-first search to find the shortest path.
        
        Args:
            source_id: ID of the source tubule
            target_id: ID of the target tubule
            max_depth: Maximum search depth
            
        Returns:
            Optional[List[Pathway]]: List of pathways forming the path, or None if no path found
        """
        if source_id == target_id:
            return []
        
        # Queue of (current_id, path_so_far)
        queue = [(source_id, [])]
        visited = {source_id}
        
        while queue and len(visited) <= max_depth:
            current_id, path = queue.pop(0)
            
            # Get all pathways from current node
            pathways = self.get_pathways_from_source(current_id)
            
            for pathway in pathways:
                next_id = pathway.target_id
                
                # If found target, return path
                if next_id == target_id:
                    return path + [pathway]
                
                # If not visited, add to queue
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [pathway]))
        
        # No path found
        return None
    
    def get_stats(self) -> dict:
        """
        Get statistics about the pathway network.
        
        Returns:
            Dict: Dictionary containing pathway statistics
        """
        pathway_types = {ptype: 0 for ptype in PathwayType}
        for pathway in self._pathways.values():
            pathway_types[pathway.pathway_type] += 1
        
        return {
            "total_pathways": len(self._pathways),
            "total_sources": len(self._source_index),
            "total_targets": len(self._target_index),
            "pathway_types": {ptype.value: count for ptype, count in pathway_types.items()},
            "bidirectional_count": sum(1 for p in self._pathways.values() if p.bidirectional),
            "average_strength": np.mean([p.strength for p in self._pathways.values()]) if self._pathways else 0.0,
        }
    
    def to_dict(self) -> dict:
        """
        Convert the pathway manager to a dictionary representation.
        
        Returns:
            Dict: Dictionary representation of the pathway manager
        """
        return {
            "pathways": {pid: pathway.to_dict() for pid, pathway in self._pathways.items()},
            "stats": self.get_stats()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PathwayManager':
        """
        Create a PathwayManager instance from a dictionary representation.
        
        Args:
            data: Dictionary containing pathway manager data
            
        Returns:
            PathwayManager: New PathwayManager instance
        """
        manager = cls()
        
        # Load pathways
        pathways_data = data.get("pathways", {})
        for _pid, pathway_data in pathways_data.items():
            pathway = Pathway.from_dict(pathway_data)
            manager.register_pathway(pathway)
        
        return manager
    
    def clear(self) -> None:
        """Clear all pathways and indices."""
        self._pathways.clear()
        self._source_index.clear()
        self._target_index.clear()
        for pathway_type in PathwayType:
            self._type_index[pathway_type] = set()
        
        logger.info("PathwayManager cleared")