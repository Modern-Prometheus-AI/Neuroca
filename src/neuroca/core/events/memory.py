"""
Memory Events Module for NeuroCognitive Architecture (NCA)

This module defines the event system for memory-related operations within the NCA system.
It provides a comprehensive set of event classes for tracking memory operations across
the three-tiered memory system (working memory, episodic memory, and semantic memory).

Events are used to:
1. Track memory operations (creation, retrieval, update, deletion)
2. Monitor memory health and performance
3. Facilitate debugging and observability
4. Support memory consolidation processes
5. Enable event-driven architecture for memory subsystems

Usage:
    from neuroca.core.events.memory import MemoryEvent, MemoryCreatedEvent
    
    # Create a memory event
    event = MemoryCreatedEvent(
        memory_id="mem_12345",
        memory_type=MemoryType.EPISODIC,
        content={"text": "The agent encountered a red door"},
        metadata={"importance": 0.8, "source": "user_interaction"}
    )
    
    # Publish the event
    event_bus.publish(event)
"""

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from neuroca.core.events.base import BaseEvent, EventPriority, EventType


class MemoryType(str, enum.Enum):
    """Enumeration of memory types in the NCA system."""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"  # For future extension


class MemoryOperation(str, enum.Enum):
    """Enumeration of memory operations."""
    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    CONSOLIDATE = "consolidate"
    DECAY = "decay"
    REINFORCE = "reinforce"
    ASSOCIATE = "associate"


class MemoryEventMetadata(BaseModel):
    """Metadata for memory events."""
    importance: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="Importance score of the memory (0.0-1.0)"
    )
    emotional_valence: Optional[float] = Field(
        default=None, 
        ge=-1.0, 
        le=1.0, 
        description="Emotional valence of the memory (-1.0 to 1.0)"
    )
    emotional_arousal: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=1.0, 
        description="Emotional arousal level of the memory (0.0-1.0)"
    )
    source: Optional[str] = Field(
        default=None, 
        description="Source of the memory (e.g., 'user_interaction', 'system_inference')"
    )
    tags: list[str] = Field(
        default_factory=list, 
        description="Tags associated with the memory"
    )
    context_ids: list[str] = Field(
        default_factory=list, 
        description="IDs of related context elements"
    )
    
    @validator('importance', 'emotional_valence', 'emotional_arousal')
    def round_to_two_decimals(cls, v):
        """Round floating point values to two decimal places."""
        if v is not None:
            return round(v, 2)
        return v


@dataclass
class MemoryEvent(BaseEvent):
    """Base class for all memory-related events in the NCA system."""
    memory_id: str
    memory_type: MemoryType
    operation: MemoryOperation
    content: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Default event type for memory events
    event_type: EventType = field(default=EventType.MEMORY)
    
    def __post_init__(self):
        """Validate and process the event after initialization."""
        super().__post_init__()
        
        # Ensure memory_id is valid
        if not self.memory_id:
            self.memory_id = f"mem_{uuid.uuid4().hex[:10]}"
            
        # Convert metadata to MemoryEventMetadata if it's a dict
        if isinstance(self.metadata, dict):
            try:
                self.metadata = MemoryEventMetadata(**self.metadata).dict()
            except Exception as e:
                # If validation fails, keep original metadata but log warning
                import logging
                logging.warning(f"Failed to validate memory metadata: {e}. Using raw metadata.")


@dataclass
class MemoryCreatedEvent(MemoryEvent):
    """Event emitted when a new memory is created."""
    operation: MemoryOperation = field(default=MemoryOperation.CREATE)
    priority: EventPriority = field(default=EventPriority.NORMAL)
    
    def __post_init__(self):
        """Validate the created event."""
        super().__post_init__()
        if not self.content:
            raise ValueError("Content is required for memory creation")


@dataclass
class MemoryRetrievedEvent(MemoryEvent):
    """Event emitted when a memory is retrieved."""
    operation: MemoryOperation = field(default=MemoryOperation.RETRIEVE)
    priority: EventPriority = field(default=EventPriority.LOW)
    retrieval_latency: Optional[float] = None  # in milliseconds
    
    def __post_init__(self):
        """Process the retrieved event."""
        super().__post_init__()
        # Track retrieval count in metadata
        if 'retrieval_count' in self.metadata:
            self.metadata['retrieval_count'] += 1
        else:
            self.metadata['retrieval_count'] = 1
        
        # Record last retrieval time
        self.metadata['last_retrieved_at'] = datetime.utcnow().isoformat()


@dataclass
class MemoryUpdatedEvent(MemoryEvent):
    """Event emitted when a memory is updated."""
    operation: MemoryOperation = field(default=MemoryOperation.UPDATE)
    priority: EventPriority = field(default=EventPriority.NORMAL)
    previous_content: Optional[dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate the updated event."""
        super().__post_init__()
        if not self.content:
            raise ValueError("Content is required for memory update")
        
        # Track update count in metadata
        if 'update_count' in self.metadata:
            self.metadata['update_count'] += 1
        else:
            self.metadata['update_count'] = 1
            
        # Record last update time
        self.metadata['last_updated_at'] = datetime.utcnow().isoformat()


@dataclass
class MemoryDeletedEvent(MemoryEvent):
    """Event emitted when a memory is deleted."""
    operation: MemoryOperation = field(default=MemoryOperation.DELETE)
    priority: EventPriority = field(default=EventPriority.HIGH)
    reason: Optional[str] = None
    
    def __post_init__(self):
        """Process the deleted event."""
        super().__post_init__()
        # Record deletion time
        self.metadata['deleted_at'] = datetime.utcnow().isoformat()
        
        # Record reason if provided
        if self.reason:
            self.metadata['deletion_reason'] = self.reason


@dataclass
class MemoryConsolidatedEvent(MemoryEvent):
    """Event emitted when a memory is consolidated (e.g., from working to long-term)."""
    operation: MemoryOperation = field(default=MemoryOperation.CONSOLIDATE)
    priority: EventPriority = field(default=EventPriority.NORMAL)
    source_memory_type: MemoryType = None
    target_memory_type: MemoryType = None
    
    def __post_init__(self):
        """Validate the consolidated event."""
        super().__post_init__()
        if not self.source_memory_type or not self.target_memory_type:
            raise ValueError("Source and target memory types are required for consolidation")
        
        # Record consolidation time
        self.metadata['consolidated_at'] = datetime.utcnow().isoformat()
        
        # Record source and target memory types
        self.metadata['source_memory_type'] = self.source_memory_type.value
        self.metadata['target_memory_type'] = self.target_memory_type.value


@dataclass
class MemoryDecayEvent(MemoryEvent):
    """Event emitted when a memory decays (loses importance or detail)."""
    operation: MemoryOperation = field(default=MemoryOperation.DECAY)
    priority: EventPriority = field(default=EventPriority.LOW)
    decay_factor: float = 0.1  # How much the memory decayed
    
    def __post_init__(self):
        """Process the decay event."""
        super().__post_init__()
        # Validate decay factor
        if not 0 <= self.decay_factor <= 1:
            raise ValueError("Decay factor must be between 0 and 1")
        
        # Record decay information
        self.metadata['decayed_at'] = datetime.utcnow().isoformat()
        self.metadata['decay_factor'] = self.decay_factor
        
        # Update importance if present
        if 'importance' in self.metadata:
            self.metadata['previous_importance'] = self.metadata['importance']
            self.metadata['importance'] = max(0, self.metadata['importance'] - self.decay_factor)


@dataclass
class MemoryReinforcedEvent(MemoryEvent):
    """Event emitted when a memory is reinforced (becomes stronger)."""
    operation: MemoryOperation = field(default=MemoryOperation.REINFORCE)
    priority: EventPriority = field(default=EventPriority.NORMAL)
    reinforcement_factor: float = 0.1  # How much the memory was reinforced
    
    def __post_init__(self):
        """Process the reinforcement event."""
        super().__post_init__()
        # Validate reinforcement factor
        if not 0 <= self.reinforcement_factor <= 1:
            raise ValueError("Reinforcement factor must be between 0 and 1")
        
        # Record reinforcement information
        self.metadata['reinforced_at'] = datetime.utcnow().isoformat()
        self.metadata['reinforcement_factor'] = self.reinforcement_factor
        
        # Update importance if present
        if 'importance' in self.metadata:
            self.metadata['previous_importance'] = self.metadata['importance']
            self.metadata['importance'] = min(1.0, self.metadata['importance'] + self.reinforcement_factor)


@dataclass
class MemoryAssociationEvent(MemoryEvent):
    """Event emitted when memories are associated with each other."""
    operation: MemoryOperation = field(default=MemoryOperation.ASSOCIATE)
    priority: EventPriority = field(default=EventPriority.NORMAL)
    associated_memory_ids: list[str] = field(default_factory=list)
    association_type: str = "generic"  # Type of association (e.g., "temporal", "semantic")
    association_strength: float = 0.5  # Strength of the association (0-1)
    
    def __post_init__(self):
        """Validate the association event."""
        super().__post_init__()
        # Validate associated memory IDs
        if not self.associated_memory_ids:
            raise ValueError("At least one associated memory ID is required")
        
        # Validate association strength
        if not 0 <= self.association_strength <= 1:
            raise ValueError("Association strength must be between 0 and 1")
        
        # Record association information
        self.metadata['associated_at'] = datetime.utcnow().isoformat()
        self.metadata['association_type'] = self.association_type
        self.metadata['association_strength'] = self.association_strength
        self.metadata['associated_memory_ids'] = self.associated_memory_ids


class MemoryEventFactory:
    """Factory class for creating memory events."""
    
    @staticmethod
    def create_event(
        event_type: str,
        memory_id: str,
        memory_type: MemoryType,
        content: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> MemoryEvent:
        """
        Create a memory event of the specified type.
        
        Args:
            event_type: Type of event to create (e.g., "created", "retrieved")
            memory_id: ID of the memory
            memory_type: Type of memory (working, episodic, semantic)
            content: Memory content
            metadata: Memory metadata
            **kwargs: Additional arguments specific to the event type
            
        Returns:
            A memory event of the appropriate type
            
        Raises:
            ValueError: If the event type is not recognized
        """
        metadata = metadata or {}
        
        # Map event type strings to event classes
        event_map = {
            "created": MemoryCreatedEvent,
            "retrieved": MemoryRetrievedEvent,
            "updated": MemoryUpdatedEvent,
            "deleted": MemoryDeletedEvent,
            "consolidated": MemoryConsolidatedEvent,
            "decayed": MemoryDecayEvent,
            "reinforced": MemoryReinforcedEvent,
            "associated": MemoryAssociationEvent
        }
        
        if event_type not in event_map:
            raise ValueError(f"Unknown memory event type: {event_type}")
        
        # Create and return the appropriate event
        return event_map[event_type](
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            **kwargs
        )