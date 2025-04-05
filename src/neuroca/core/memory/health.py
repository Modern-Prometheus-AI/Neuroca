"""
Health monitoring integration for memory systems.

This module provides specialized health monitoring for memory systems,
tracking memory-specific health metrics and applying biological constraints.
"""

import logging
import time
from typing import Optional

from neuroca.core.health import (
    ComponentHealth,
    HealthCheckResult,
    HealthCheckStatus,
    MemoryHealthCheck,
    record_cognitive_operation,
    register_component_for_health_tracking,
    register_health_check,
)

logger = logging.getLogger(__name__)


class WorkingMemoryHealthCheck(MemoryHealthCheck):
    """
    Health check for working memory system.
    
    Specializes the generic memory health check for working memory,
    adding specific checks for activation levels and capacity constraints.
    """
    def __init__(self, component_id: str, memory_system, 
                 capacity_threshold: float = 0.8,
                 activation_threshold: float = 0.3):
        """
        Initialize a working memory health check.
        
        Args:
            component_id: The working memory component's ID
            memory_system: The working memory system to check
            capacity_threshold: Threshold for capacity warning (0.0-1.0)
            activation_threshold: Minimum acceptable activation level
        """
        super().__init__(
            check_id=f"{component_id}.health",
            component_id=component_id,
            memory_system=memory_system,
            capacity_threshold=capacity_threshold
        )
        self.activation_threshold = activation_threshold
    
    def execute(self) -> HealthCheckResult:
        """
        Check the health of working memory.
        
        Extends the base check with working memory-specific metrics
        including activation level analysis.
        
        Returns:
            HealthCheckResult with status and metrics
        """
        start_time = time.time()
        
        try:
            # Get all memory chunks using the correct method (assuming get_all_items)
            chunks = self.memory_system.get_all_items() 
            total_items = len(chunks)
            capacity = getattr(self.memory_system, 'capacity', float('inf'))
            
            # Calculate capacity metrics
            capacity_ratio = total_items / capacity if capacity != float('inf') else 0.0
            
            # Analyze activation levels
            if chunks:
                activation_levels = [getattr(chunk, 'activation', 0.0) for chunk in chunks]
                avg_activation = sum(activation_levels) / len(activation_levels)
                low_activation_count = sum(1 for a in activation_levels if a < self.activation_threshold)
                low_activation_ratio = low_activation_count / len(chunks) if chunks else 0.0
            else:
                avg_activation = 0.0
                low_activation_count = 0
                low_activation_ratio = 0.0
            
            # Perform test store/retrieve operation
            test_content = f"Health check test item - {time.time()}"
            chunk_id = self.memory_system.store(test_content, activation=0.9)
            retrieved = self.memory_system.retrieve_by_id(chunk_id)
            operations_successful = retrieved is not None and retrieved.content == test_content
            
            # Cleanup after ourselves
            if retrieved is not None:
                self.memory_system.forget(chunk_id)
            
            # Determine status based on metrics
            if not operations_successful:
                status = HealthCheckStatus.FAILED
                message = "Working memory operations failed"
            elif capacity_ratio >= self.capacity_threshold:
                status = HealthCheckStatus.WARNING
                message = f"Working memory is nearing capacity ({capacity_ratio:.1%})"
            elif low_activation_ratio > 0.5:
                status = HealthCheckStatus.WARNING
                message = f"Working memory has many low activation items ({low_activation_ratio:.1%})"
            else:
                status = HealthCheckStatus.PASSED
                message = f"Working memory is operating normally ({total_items}/{capacity} items)"
            
            # Include detailed metrics
            details = {
                "total_items": total_items,
                "capacity": capacity,
                "capacity_ratio": capacity_ratio,
                "avg_activation": avg_activation,
                "low_activation_count": low_activation_count,
                "low_activation_ratio": low_activation_ratio,
                "operations_successful": operations_successful
            }
            
            # Add any memory-system specific metrics if available
            if hasattr(self.memory_system, 'get_metrics'):
                details.update(self.memory_system.get_metrics())
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result = self.create_result(status, message, **details)
            result.execution_time = execution_time
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.exception(f"Error during working memory health check: {e}")
            
            result = self.create_result(
                HealthCheckStatus.ERROR,
                f"Health check failed with error: {str(e)}",
                error=str(e),
                error_type=type(e).__name__
            )
            result.execution_time = execution_time
            return result


class EpisodicMemoryHealthCheck(MemoryHealthCheck):
    """
    Health check for episodic memory system.
    
    Specializes the generic memory health check for episodic memory,
    adding specific checks for emotional salience and temporal context.
    """
    def __init__(self, component_id: str, memory_system):
        """
        Initialize an episodic memory health check.
        
        Args:
            component_id: The episodic memory component's ID
            memory_system: The episodic memory system to check
        """
        super().__init__(
            check_id=f"{component_id}.health",
            component_id=component_id,
            memory_system=memory_system
        )
    
    def execute(self) -> HealthCheckResult:
        """
        Check the health of episodic memory.
        
        Extends the base check with episodic memory-specific metrics
        including emotional salience and temporal context analysis.
        
        Returns:
            HealthCheckResult with status and metrics
        """
        start_time = time.time()
        
        try:
            # Get all memory chunks using the correct method (assuming get_all_items)
            chunks = self.memory_system.get_all_items() 
            total_items = len(chunks)
            
            # Analyze temporal context
            timestamps = []
            emotional_salience = []
            sequence_items = 0
            
            for chunk in chunks:
                metadata = getattr(chunk, 'metadata', {})
                
                # Check for timestamp
                if 'timestamp' in metadata:
                    timestamps.append(metadata['timestamp'])
                
                # Check for emotional salience
                if 'emotional_salience' in metadata:
                    emotional_salience.append(metadata['emotional_salience'])
                
                # Count sequence items
                if 'sequence_id' in metadata:
                    sequence_items += 1
            
            # Calculate metrics
            timestamp_ratio = len(timestamps) / total_items if total_items else 0.0
            seq_item_ratio = sequence_items / total_items if total_items else 0.0
            
            if emotional_salience:
                avg_emotional_salience = sum(emotional_salience) / len(emotional_salience)
                high_emotion_count = sum(1 for e in emotional_salience if e >= 0.7)
            else:
                avg_emotional_salience = 0.0
                high_emotion_count = 0
            
            # Perform test store/retrieve operation
            test_content = f"Health check test item - {time.time()}"
            metadata = {
                "timestamp": time.time(),
                "emotional_salience": 0.5,
                "health_check": True
            }
            chunk_id = self.memory_system.store(test_content, metadata=metadata)
            retrieved = self.memory_system.retrieve_by_id(chunk_id)
            operations_successful = retrieved is not None and retrieved.content == test_content
            
            # Check metadata preservation
            metadata_preserved = False
            if retrieved:
                retrieved_metadata = getattr(retrieved, 'metadata', {})
                metadata_preserved = 'timestamp' in retrieved_metadata and 'emotional_salience' in retrieved_metadata
            
            # Cleanup after ourselves
            if retrieved is not None:
                self.memory_system.forget(chunk_id)
            
            # Determine status based on metrics
            if not operations_successful:
                status = HealthCheckStatus.FAILED
                message = "Episodic memory operations failed"
            elif not metadata_preserved:
                status = HealthCheckStatus.WARNING
                message = "Episodic memory not preserving metadata correctly"
            elif timestamp_ratio < 0.8:
                status = HealthCheckStatus.WARNING
                message = f"Many episodic memories lack temporal context ({timestamp_ratio:.1%} have timestamps)"
            else:
                status = HealthCheckStatus.PASSED
                message = f"Episodic memory is operating normally ({total_items} items)"
            
            # Include detailed metrics
            details = {
                "total_items": total_items,
                "timestamp_ratio": timestamp_ratio,
                "sequence_item_ratio": seq_item_ratio,
                "avg_emotional_salience": avg_emotional_salience,
                "high_emotion_count": high_emotion_count,
                "operations_successful": operations_successful,
                "metadata_preserved": metadata_preserved
            }
            
            # Add any memory-system specific metrics if available
            if hasattr(self.memory_system, 'get_metrics'):
                details.update(self.memory_system.get_metrics())
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result = self.create_result(status, message, **details)
            result.execution_time = execution_time
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.exception(f"Error during episodic memory health check: {e}")
            
            result = self.create_result(
                HealthCheckStatus.ERROR,
                f"Health check failed with error: {str(e)}",
                error=str(e),
                error_type=type(e).__name__
            )
            result.execution_time = execution_time
            return result


class SemanticMemoryHealthCheck(MemoryHealthCheck):
    """
    Health check for semantic memory system.
    
    Specializes the generic memory health check for semantic memory,
    adding specific checks for knowledge graph integrity and relationships.
    """
    def __init__(self, component_id: str, memory_system):
        """
        Initialize a semantic memory health check.
        
        Args:
            component_id: The semantic memory component's ID
            memory_system: The semantic memory system to check
        """
        super().__init__(
            check_id=f"{component_id}.health",
            component_id=component_id,
            memory_system=memory_system
        )
    
    def execute(self) -> HealthCheckResult:
        """
        Check the health of semantic memory.
        
        Extends the base check with semantic memory-specific metrics
        including knowledge graph integrity and relationship analysis.
        
        Returns:
            HealthCheckResult with status and metrics
        """
        start_time = time.time()
        
        try:
            # Get all concepts and relationships
            concepts = self.memory_system.retrieve_all_concepts()
            relationships = self.memory_system.retrieve_all_relationships()
            
            total_concepts = len(concepts)
            total_relationships = len(relationships)
            
            # Check for orphaned relationships (referencing non-existent concepts)
            concept_ids = {concept.id for concept in concepts}
            orphaned_relationships = 0
            
            for rel in relationships:
                if rel.source_id not in concept_ids or rel.target_id not in concept_ids:
                    orphaned_relationships += 1
            
            # Calculate concept connectivity
            connected_concepts = set()
            for rel in relationships:
                connected_concepts.add(rel.source_id)
                connected_concepts.add(rel.target_id)
            
            connected_concepts = connected_concepts.intersection(concept_ids)
            connectivity_ratio = len(connected_concepts) / total_concepts if total_concepts else 0.0
            
            # Calculate relationship density
            if total_concepts > 1:
                # Maximum possible relationships is n*(n-1) for a directed graph
                max_relationships = total_concepts * (total_concepts - 1)
                density = total_relationships / max_relationships if max_relationships else 0.0
            else:
                density = 0.0
            
            # Perform test store/retrieve operation for concept
            test_concept_id = f"health_check_{int(time.time())}"
            test_concept = self.memory_system._create_concept(
                id=test_concept_id,
                name="Health Check Concept",
                description="Temporary concept for health check",
                properties={"temporary": True}
            )
            
            self.memory_system.store(test_concept)
            retrieved_concept = self.memory_system.get_concept(test_concept_id)
            concept_ops_successful = retrieved_concept is not None and retrieved_concept.id == test_concept_id
            
            # Test relationship creation
            if concept_ops_successful and total_concepts > 0:
                # Find an existing concept to relate to
                existing_concept = concepts[0]
                test_relationship = self.memory_system._create_relationship(
                    source_id=test_concept_id,
                    target_id=existing_concept.id,
                    relationship_type="TEST"
                )
                
                self.memory_system.store(test_relationship)
                retrieved_rels = self.memory_system.retrieve_relationships_for_concept(test_concept_id)
                relationship_ops_successful = len(retrieved_rels) > 0
            else:
                relationship_ops_successful = False
            
            # Cleanup after ourselves
            if concept_ops_successful:
                self.memory_system.forget_concept(test_concept_id)
            
            # Determine status based on metrics
            if not concept_ops_successful:
                status = HealthCheckStatus.FAILED
                message = "Semantic memory concept operations failed"
            elif orphaned_relationships > 0:
                status = HealthCheckStatus.WARNING
                message = f"Semantic memory contains {orphaned_relationships} orphaned relationships"
            elif connectivity_ratio < 0.5 and total_concepts > 5:
                status = HealthCheckStatus.WARNING
                message = f"Low concept connectivity ({connectivity_ratio:.1%} concepts connected)"
            else:
                status = HealthCheckStatus.PASSED
                message = (f"Semantic memory is operating normally "
                          f"({total_concepts} concepts, {total_relationships} relationships)")
            
            # Include detailed metrics
            details = {
                "total_concepts": total_concepts,
                "total_relationships": total_relationships,
                "orphaned_relationships": orphaned_relationships,
                "connectivity_ratio": connectivity_ratio,
                "relationship_density": density,
                "concept_ops_successful": concept_ops_successful,
                "relationship_ops_successful": relationship_ops_successful
            }
            
            # Add any memory-system specific metrics if available
            if hasattr(self.memory_system, 'get_metrics'):
                details.update(self.memory_system.get_metrics())
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result = self.create_result(status, message, **details)
            result.execution_time = execution_time
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.exception(f"Error during semantic memory health check: {e}")
            
            result = self.create_result(
                HealthCheckStatus.ERROR,
                f"Health check failed with error: {str(e)}",
                error=str(e),
                error_type=type(e).__name__
            )
            result.execution_time = execution_time
            return result


class MemoryHealthMonitor:
    """
    Manages health monitoring for memory systems.
    
    This class integrates the generic health system with memory-specific
    monitoring, tracking both health metrics and cognitive dynamics.
    """
    def __init__(self):
        """Initialize the memory health monitor."""
        self._memory_systems = {}
        self._operation_complexity = {
            "store": 0.3,
            "retrieve": 0.2,
            "forget": 0.1,
            "clear": 0.5,
            "update": 0.4,
            "consolidate": 0.6
        }
    
    def register_working_memory(self, memory_system, 
                               component_id: str = "working_memory") -> ComponentHealth:
        """
        Register a working memory system for health monitoring.
        
        Args:
            memory_system: The working memory system
            component_id: Unique identifier for the component
        
        Returns:
            The ComponentHealth object for the component
        """
        # Register with the health dynamics system
        health = register_component_for_health_tracking(component_id)
        
        # Create and register a specialized health check
        check = WorkingMemoryHealthCheck(component_id, memory_system)
        register_health_check(check)
        
        # Store reference to the memory system
        self._memory_systems[component_id] = (memory_system, "working_memory")
        
        return health
    
    def register_episodic_memory(self, memory_system, 
                                component_id: str = "episodic_memory") -> ComponentHealth:
        """
        Register an episodic memory system for health monitoring.
        
        Args:
            memory_system: The episodic memory system
            component_id: Unique identifier for the component
        
        Returns:
            The ComponentHealth object for the component
        """
        # Register with the health dynamics system
        health = register_component_for_health_tracking(component_id)
        
        # Create and register a specialized health check
        check = EpisodicMemoryHealthCheck(component_id, memory_system)
        register_health_check(check)
        
        # Store reference to the memory system
        self._memory_systems[component_id] = (memory_system, "episodic_memory")
        
        return health
    
    def register_semantic_memory(self, memory_system, 
                               component_id: str = "semantic_memory") -> ComponentHealth:
        """
        Register a semantic memory system for health monitoring.
        
        Args:
            memory_system: The semantic memory system
            component_id: Unique identifier for the component
        
        Returns:
            The ComponentHealth object for the component
        """
        # Register with the health dynamics system
        health = register_component_for_health_tracking(component_id)
        
        # Create and register a specialized health check
        check = SemanticMemoryHealthCheck(component_id, memory_system)
        register_health_check(check)
        
        # Store reference to the memory system
        self._memory_systems[component_id] = (memory_system, "semantic_memory")
        
        return health
    
    def record_memory_operation(self, component_id: str, operation: str, 
                              num_items: int = 1) -> None:
        """
        Record a memory operation and update health parameters accordingly.
        
        Args:
            component_id: The ID of the memory component
            operation: Type of memory operation (store, retrieve, etc.)
            num_items: Number of items affected by the operation
        """
        if component_id not in self._memory_systems:
            logger.warning(f"Memory component '{component_id}' not registered for health monitoring")
            return
        
        # Get base complexity for the operation
        base_complexity = self._operation_complexity.get(operation, 0.2)
        
        # Scale complexity based on number of items
        complexity = base_complexity * (1 + 0.1 * (num_items - 1))
        complexity = min(1.0, complexity)  # Cap at 1.0
        
        # Record the operation
        record_cognitive_operation(component_id, operation, complexity)


# Global instance for singleton access
_memory_health_monitor = MemoryHealthMonitor()

def get_memory_health_monitor() -> MemoryHealthMonitor:
    """Get the global memory health monitor instance."""
    return _memory_health_monitor

def register_memory_system(memory_system, memory_type: str, 
                         component_id: Optional[str] = None) -> ComponentHealth:
    """
    Register a memory system with the global health monitor.
    
    Args:
        memory_system: The memory system to register
        memory_type: Type of memory system (working, episodic, semantic)
        component_id: Optional unique identifier for the component
    
    Returns:
        The ComponentHealth object for the component
    
    Raises:
        ValueError: If memory_type is not recognized
    """
    monitor = get_memory_health_monitor()
    
    if memory_type == "working":
        component_id = component_id or "working_memory"
        return monitor.register_working_memory(memory_system, component_id)
    elif memory_type == "episodic":
        component_id = component_id or "episodic_memory"
        return monitor.register_episodic_memory(memory_system, component_id)
    elif memory_type == "semantic":
        component_id = component_id or "semantic_memory"
        return monitor.register_semantic_memory(memory_system, component_id)
    else:
        raise ValueError(f"Unknown memory type: {memory_type}")

def record_memory_operation(component_id: str, operation: str, 
                          num_items: int = 1) -> None:
    """
    Record a memory operation with the global health monitor.
    
    Args:
        component_id: The ID of the memory component
        operation: Type of memory operation (store, retrieve, etc.)
        num_items: Number of items affected by the operation
    """
    get_memory_health_monitor().record_memory_operation(
        component_id, operation, num_items
    )
