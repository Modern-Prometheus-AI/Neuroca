"""
Memory Schema Definitions for NeuroCognitive Architecture (NCA).

This module defines Pydantic models for the three-tiered memory system:
- Working Memory: Short-term, limited capacity memory for active processing
- Episodic Memory: Autobiographical events and experiences
- Semantic Memory: General knowledge, concepts, and facts

These schemas provide validation, serialization, and documentation for memory
objects throughout the NCA system, ensuring data integrity and consistency.
"""

import datetime
import enum
import logging
import uuid
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.types import confloat, conint

# Configure module logger
logger = logging.getLogger(__name__)


class MemoryStatus(str, enum.Enum):
    """Status of a memory item in the system."""
    ACTIVE = "active"           # Currently in use/accessible
    DORMANT = "dormant"         # Not currently active but can be retrieved
    CONSOLIDATED = "consolidated"  # Processed and stored for long-term
    DECAYING = "decaying"       # Losing activation/accessibility
    FORGOTTEN = "forgotten"     # No longer directly accessible


class MemoryTier(str, enum.Enum):
    """The memory tier to which a memory item belongs."""
    WORKING = "working"         # Working memory (short-term)
    EPISODIC = "episodic"       # Episodic memory (experiences)
    SEMANTIC = "semantic"       # Semantic memory (knowledge)


class MemoryPriority(int, enum.Enum):
    """Priority level for memory items affecting retention and retrieval."""
    CRITICAL = 5    # Highest priority, essential information
    HIGH = 4        # Important information
    MEDIUM = 3      # Standard priority
    LOW = 2         # Lower importance
    MINIMAL = 1     # Lowest priority, easily discarded


class MemoryEmotion(BaseModel):
    """Emotional valence associated with a memory."""
    valence: confloat(ge=-1.0, le=1.0) = Field(
        default=0.0,
        description="Emotional valence from negative (-1.0) to positive (1.0)"
    )
    arousal: confloat(ge=0.0, le=1.0) = Field(
        default=0.0,
        description="Emotional intensity/arousal from calm (0.0) to excited (1.0)"
    )
    dominant_emotion: Optional[str] = Field(
        default=None,
        description="Primary emotion label (e.g., 'joy', 'fear', 'surprise')"
    )
    emotion_labels: dict[str, float] = Field(
        default_factory=dict,
        description="Mapping of emotion labels to their confidence scores"
    )

    @validator('emotion_labels')
    def validate_emotion_scores(cls, v):
        """Ensure emotion confidence scores are between 0.0 and 1.0."""
        for emotion, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Emotion score for '{emotion}' must be between 0.0 and 1.0")
        return v


class MemoryContext(BaseModel):
    """Contextual information about when and where a memory was formed."""
    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="When the memory was created/recorded"
    )
    location: Optional[str] = Field(
        default=None,
        description="Physical or virtual location associated with the memory"
    )
    source: Optional[str] = Field(
        default=None,
        description="Origin of the memory (e.g., 'user', 'system', 'inference')"
    )
    related_task: Optional[str] = Field(
        default=None,
        description="Task or activity associated with this memory"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional contextual metadata"
    )


class MemoryAssociation(BaseModel):
    """Association between memory items."""
    target_id: uuid.UUID = Field(
        ...,
        description="ID of the target memory this association points to"
    )
    association_type: str = Field(
        ...,
        description="Type of association (e.g., 'causal', 'temporal', 'semantic')"
    )
    strength: confloat(ge=0.0, le=1.0) = Field(
        default=0.5,
        description="Strength of the association from 0.0 (weak) to 1.0 (strong)"
    )
    bidirectional: bool = Field(
        default=False,
        description="Whether the association applies in both directions"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the association"
    )


class BaseMemory(BaseModel):
    """Base model for all memory items in the system."""
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for the memory item"
    )
    content: Any = Field(
        ...,
        description="The actual content of the memory (can be any data type)"
    )
    tier: MemoryTier = Field(
        ...,
        description="The memory tier this item belongs to"
    )
    status: MemoryStatus = Field(
        default=MemoryStatus.ACTIVE,
        description="Current status of the memory item"
    )
    priority: MemoryPriority = Field(
        default=MemoryPriority.MEDIUM,
        description="Priority level affecting retention and retrieval"
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="When the memory was initially created"
    )
    last_accessed: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="When the memory was last accessed/retrieved"
    )
    access_count: int = Field(
        default=0,
        description="Number of times this memory has been accessed"
    )
    tags: set[str] = Field(
        default_factory=set,
        description="Tags for categorizing and retrieving the memory"
    )
    context: MemoryContext = Field(
        default_factory=MemoryContext,
        description="Contextual information about the memory"
    )
    emotion: Optional[MemoryEmotion] = Field(
        default=None,
        description="Emotional aspects associated with the memory"
    )
    associations: list[MemoryAssociation] = Field(
        default_factory=list,
        description="Associations to other memory items"
    )
    decay_rate: confloat(ge=0.0, le=1.0) = Field(
        default=0.1,
        description="Rate at which this memory decays if not accessed"
    )
    activation_level: confloat(ge=0.0, le=1.0) = Field(
        default=1.0,
        description="Current activation/accessibility level"
    )

    def update_access_metadata(self):
        """Update access metadata when memory is retrieved."""
        self.last_accessed = datetime.datetime.utcnow()
        self.access_count += 1
        self.activation_level = min(1.0, self.activation_level + 0.1)
        logger.debug(f"Updated access metadata for memory {self.id}")

    @validator('associations')
    def validate_associations(cls, v, values):
        """Validate that associations don't reference the memory itself."""
        if 'id' in values:
            for assoc in v:
                if assoc.target_id == values['id']:
                    raise ValueError("Memory cannot have an association to itself")
        return v

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"
        schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "content": "The sky is blue because of Rayleigh scattering",
                "tier": "semantic",
                "status": "active",
                "priority": 3,
                "tags": ["science", "physics", "sky"],
                "activation_level": 0.8
            }
        }


class WorkingMemory(BaseMemory):
    """
    Working Memory representation for short-term, limited capacity memory.
    
    Working memory has a limited capacity and typically holds information
    that is currently being processed or manipulated.
    """
    tier: MemoryTier = Field(
        default=MemoryTier.WORKING,
        const=True,
        description="Working memory tier"
    )
    expiration: Optional[datetime.datetime] = Field(
        default=None,
        description="When this working memory item will expire if not reinforced"
    )
    attention_weight: confloat(ge=0.0, le=1.0) = Field(
        default=0.5,
        description="Attention allocation weight for this memory item"
    )
    processing_stage: str = Field(
        default="initial",
        description="Current processing stage (e.g., 'initial', 'processing', 'ready')"
    )

    @root_validator
    def set_default_expiration(cls, values):
        """Set default expiration time if not provided."""
        if values.get('expiration') is None:
            # Default working memory items expire in 30 minutes if not accessed
            values['expiration'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        return values

    def is_expired(self) -> bool:
        """Check if the working memory item has expired."""
        if self.expiration is None:
            return False
        return datetime.datetime.utcnow() > self.expiration

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "content": "Current user request to analyze market trends",
                "priority": 4,
                "attention_weight": 0.8,
                "processing_stage": "processing",
                "tags": ["user_request", "current_task"]
            }
        }


class EpisodicMemory(BaseMemory):
    """
    Episodic Memory representation for autobiographical events and experiences.
    
    Episodic memory stores specific events, situations, and experiences, including
    their temporal and spatial context.
    """
    tier: MemoryTier = Field(
        default=MemoryTier.EPISODIC,
        const=True,
        description="Episodic memory tier"
    )
    episode_type: str = Field(
        ...,
        description="Type of episode (e.g., 'conversation', 'observation', 'action')"
    )
    participants: list[str] = Field(
        default_factory=list,
        description="Entities involved in this episode"
    )
    sequence_position: Optional[int] = Field(
        default=None,
        description="Position in a sequence of related episodes"
    )
    narrative_importance: confloat(ge=0.0, le=1.0) = Field(
        default=0.5,
        description="Importance of this episode in the overall narrative"
    )
    vividness: confloat(ge=0.0, le=1.0) = Field(
        default=0.5,
        description="Vividness/clarity of the memory"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "content": "User John asked about climate change impacts on agriculture",
                "episode_type": "conversation",
                "participants": ["user:john", "system"],
                "emotion": {
                    "valence": 0.1,
                    "arousal": 0.3,
                    "dominant_emotion": "interest"
                },
                "narrative_importance": 0.7,
                "tags": ["conversation", "climate_change", "agriculture"]
            }
        }


class SemanticMemory(BaseMemory):
    """
    Semantic Memory representation for general knowledge, concepts, and facts.
    
    Semantic memory contains general world knowledge, concepts, facts, and
    information that is not tied to specific experiences.
    """
    tier: MemoryTier = Field(
        default=MemoryTier.SEMANTIC,
        const=True,
        description="Semantic memory tier"
    )
    knowledge_domain: list[str] = Field(
        default_factory=list,
        description="Knowledge domains this memory belongs to"
    )
    certainty: confloat(ge=0.0, le=1.0) = Field(
        default=0.9,
        description="Certainty level about this knowledge"
    )
    source_reliability: confloat(ge=0.0, le=1.0) = Field(
        default=0.8,
        description="Reliability of the source of this knowledge"
    )
    contradictions: list[uuid.UUID] = Field(
        default_factory=list,
        description="IDs of memories that contradict this knowledge"
    )
    is_belief: bool = Field(
        default=False,
        description="Whether this is a belief rather than a verified fact"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "content": "Paris is the capital city of France",
                "knowledge_domain": ["geography", "cities", "europe"],
                "certainty": 1.0,
                "source_reliability": 0.95,
                "is_belief": False,
                "tags": ["france", "paris", "capital", "geography"]
            }
        }


class MemoryQuery(BaseModel):
    """Query parameters for searching and retrieving memories."""
    content_keywords: Optional[list[str]] = Field(
        default=None,
        description="Keywords to search for in memory content"
    )
    tiers: Optional[list[MemoryTier]] = Field(
        default=None,
        description="Memory tiers to search in"
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Tags to filter memories by"
    )
    status: Optional[list[MemoryStatus]] = Field(
        default=None,
        description="Memory statuses to include"
    )
    min_priority: Optional[MemoryPriority] = Field(
        default=None,
        description="Minimum priority level"
    )
    min_activation: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Minimum activation level"
    )
    created_after: Optional[datetime.datetime] = Field(
        default=None,
        description="Only include memories created after this time"
    )
    created_before: Optional[datetime.datetime] = Field(
        default=None,
        description="Only include memories created before this time"
    )
    accessed_after: Optional[datetime.datetime] = Field(
        default=None,
        description="Only include memories accessed after this time"
    )
    limit: Optional[conint(ge=1, le=1000)] = Field(
        default=100,
        description="Maximum number of results to return"
    )
    include_forgotten: bool = Field(
        default=False,
        description="Whether to include forgotten memories"
    )
    sort_by: str = Field(
        default="relevance",
        description="How to sort results (relevance, recency, priority, activation)"
    )
    
    @root_validator
    def validate_date_ranges(cls, values):
        """Validate that date ranges are logical."""
        created_after = values.get('created_after')
        created_before = values.get('created_before')
        
        if created_after and created_before and created_after > created_before:
            raise ValueError("created_after must be earlier than created_before")
        
        return values


class MemoryUpdateRequest(BaseModel):
    """Request model for updating memory attributes."""
    status: Optional[MemoryStatus] = None
    priority: Optional[MemoryPriority] = None
    tags: Optional[set[str]] = None
    activation_level: Optional[confloat(ge=0.0, le=1.0)] = None
    decay_rate: Optional[confloat(ge=0.0, le=1.0)] = None
    content: Optional[Any] = None
    associations_to_add: Optional[list[MemoryAssociation]] = None
    associations_to_remove: Optional[list[uuid.UUID]] = None
    emotion: Optional[MemoryEmotion] = None
    
    @validator('associations_to_add')
    def validate_associations(cls, v):
        """Validate that associations are properly formed."""
        if v is not None:
            seen_ids = set()
            for assoc in v:
                if assoc.target_id in seen_ids:
                    raise ValueError(f"Duplicate association to target {assoc.target_id}")
                seen_ids.add(assoc.target_id)
        return v


class MemoryOperationResponse(BaseModel):
    """Response model for memory operations."""
    success: bool = Field(
        ...,
        description="Whether the operation was successful"
    )
    memory_id: Optional[uuid.UUID] = Field(
        default=None,
        description="ID of the affected memory"
    )
    operation: str = Field(
        ...,
        description="The operation that was performed"
    )
    message: str = Field(
        ...,
        description="Human-readable result message"
    )
    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="When the operation was performed"
    )
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional operation details"
    )


# Type alias for any memory type
AnyMemory = Union[WorkingMemory, EpisodicMemory, SemanticMemory]