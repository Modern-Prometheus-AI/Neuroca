"""
Short-Term Memory (STM) Database Schema

This module defines the database schema for the Short-Term Memory component of the
NeuroCognitive Architecture. STM represents the intermediate memory tier that holds
information for a limited time with moderate capacity and accessibility.

The STM schema includes:
- Memory item structure with content, metadata, and activation levels
- Temporal decay mechanisms
- Priority and relevance scoring
- Relationships to other memory systems (WM and LTM)
- Indexing for efficient retrieval

Usage:
    from neuroca.db.schemas.stm import STMItem, STMRelation
    
    # Create a new STM item
    stm_item = STMItem(
        content="The user mentioned they prefer visual explanations",
        source="conversation",
        importance=0.75,
        context_id="session-123"
    )
    
    # Store in database
    session.add(stm_item)
    session.commit()
"""

import datetime
import enum
import logging
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from neuroca.core.exceptions import ValidationError
from neuroca.db.base import Base

# Configure module logger
logger = logging.getLogger(__name__)


class MemorySourceType(enum.Enum):
    """Enumeration of possible sources for STM items."""
    CONVERSATION = "conversation"
    OBSERVATION = "observation"
    INFERENCE = "inference"
    REFLECTION = "reflection"
    EXTERNAL = "external"
    SYSTEM = "system"


class MemoryContentType(enum.Enum):
    """Enumeration of content types for STM items."""
    TEXT = "text"
    EMBEDDING = "embedding"
    IMAGE_REFERENCE = "image_reference"
    AUDIO_REFERENCE = "audio_reference"
    STRUCTURED_DATA = "structured_data"
    MIXED = "mixed"


class STMItem(Base):
    """
    Short-Term Memory Item
    
    Represents a single item in the short-term memory store. Items in STM have
    moderate persistence (minutes to hours) and are subject to decay over time
    unless reinforced or transferred to long-term memory.
    """
    __tablename__ = "stm_items"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core memory content
    content = Column(Text, nullable=False)
    content_type = Column(Enum(MemoryContentType), default=MemoryContentType.TEXT, nullable=False)
    embedding = Column(JSONB, nullable=True, comment="Vector embedding of the content for similarity search")
    
    # Metadata
    source = Column(Enum(MemorySourceType), nullable=False)
    source_details = Column(JSONB, nullable=True, comment="Additional details about the source")
    context_id = Column(String(255), nullable=True, index=True, 
                       comment="Session or context identifier this memory belongs to")
    
    # Memory dynamics
    importance = Column(Float, default=0.5, nullable=False, 
                       comment="Importance score between 0-1")
    activation = Column(Float, default=1.0, nullable=False, 
                       comment="Current activation level, decays over time")
    access_count = Column(Integer, default=1, nullable=False, 
                         comment="Number of times this memory has been accessed")
    last_accessed = Column(DateTime, default=func.now(), nullable=False)
    
    # Temporal information
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True, 
                       comment="When this memory item should expire from STM")
    
    # Flags
    is_transferred_to_ltm = Column(Boolean, default=False, 
                                  comment="Whether this item has been transferred to LTM")
    is_active = Column(Boolean, default=True, 
                      comment="Whether this memory is currently active in STM")
    
    # Additional data
    tags = Column(JSONB, default=list, nullable=False, 
                 comment="List of tags for categorization")
    metadata = Column(JSONB, default=dict, nullable=False, 
                     comment="Additional metadata for the memory item")
    
    # Relationships
    relations = relationship("STMRelation", back_populates="source_item",
                           cascade="all, delete-orphan",
                           foreign_keys="STMRelation.source_id")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_stm_items_importance_activation", "importance", "activation"),
        Index("ix_stm_items_created_at", "created_at"),
        Index("ix_stm_items_context_id_created_at", "context_id", "created_at"),
        Index("ix_stm_items_content_type", "content_type"),
    )
    
    @validates('importance', 'activation')
    def validate_score_range(self, key: str, value: float) -> float:
        """Validate that importance and activation are between 0 and 1."""
        if not 0 <= value <= 1:
            error_msg = f"{key} must be between 0 and 1, got {value}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        return value
    
    @validates('content')
    def validate_content(self, key: str, value: str) -> str:
        """Validate that content is not empty."""
        if not value or not value.strip():
            error_msg = "STM item content cannot be empty"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        return value
    
    def update_activation(self, decay_factor: float = 0.1) -> None:
        """
        Update the activation level based on time decay.
        
        Args:
            decay_factor: Rate at which activation decays (0-1)
        """
        current_time = datetime.datetime.now()
        time_diff = (current_time - self.last_accessed).total_seconds() / 3600  # hours
        
        # Apply exponential decay formula
        new_activation = self.activation * (1 - decay_factor) ** time_diff
        
        # Ensure activation stays in valid range
        self.activation = max(0.0, min(1.0, new_activation))
        logger.debug(f"Updated activation for STM item {self.id} to {self.activation}")
    
    def access(self) -> None:
        """
        Record an access to this memory item, updating activation and access count.
        """
        self.access_count += 1
        self.activation = min(1.0, self.activation + 0.2)  # Boost activation
        self.last_accessed = datetime.datetime.now()
        logger.debug(f"Accessed STM item {self.id}, new access count: {self.access_count}")
    
    def should_expire(self) -> bool:
        """
        Determine if this memory item should expire from STM.
        
        Returns:
            bool: True if the item should be removed from STM
        """
        if not self.is_active:
            return True
            
        if self.expires_at and datetime.datetime.now() > self.expires_at:
            return True
            
        # Items with very low activation may expire
        if self.activation < 0.1:
            return True
            
        return False
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the STM item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the STM item
        """
        return {
            "id": str(self.id),
            "content": self.content,
            "content_type": self.content_type.value,
            "source": self.source.value,
            "importance": self.importance,
            "activation": self.activation,
            "created_at": self.created_at.isoformat(),
            "context_id": self.context_id,
            "tags": self.tags,
            "is_active": self.is_active,
            "access_count": self.access_count,
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        """String representation of the STM item."""
        return f"<STMItem id={self.id} importance={self.importance:.2f} activation={self.activation:.2f}>"


class RelationType(enum.Enum):
    """Enumeration of possible relation types between memory items."""
    ASSOCIATION = "association"
    CAUSATION = "causation"
    SEQUENCE = "sequence"
    CONTRADICTION = "contradiction"
    ELABORATION = "elaboration"
    GENERALIZATION = "generalization"
    EXAMPLE = "example"


class STMRelation(Base):
    """
    Relation between STM items
    
    Represents semantic relationships between items in short-term memory,
    allowing for associative retrieval and context building.
    """
    __tablename__ = "stm_relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relation endpoints
    source_id = Column(UUID(as_uuid=True), ForeignKey("stm_items.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("stm_items.id", ondelete="CASCADE"), nullable=False)
    
    # Relation properties
    relation_type = Column(Enum(RelationType), nullable=False)
    strength = Column(Float, default=0.5, nullable=False, 
                     comment="Strength of the relation from 0-1")
    metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    source_item = relationship("STMItem", foreign_keys=[source_id], back_populates="relations")
    target_item = relationship("STMItem", foreign_keys=[target_id])
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('source_id', 'target_id', 'relation_type', name='uq_stm_relation'),
        Index("ix_stm_relations_source_id", "source_id"),
        Index("ix_stm_relations_target_id", "target_id"),
        Index("ix_stm_relations_type_strength", "relation_type", "strength"),
    )
    
    @validates('strength')
    def validate_strength(self, key: str, value: float) -> float:
        """Validate that relation strength is between 0 and 1."""
        if not 0 <= value <= 1:
            error_msg = f"Relation strength must be between 0 and 1, got {value}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        return value
    
    @validates('source_id', 'target_id')
    def validate_different_endpoints(self, key: str, value: uuid.UUID) -> uuid.UUID:
        """Validate that source and target are different items."""
        if key == 'target_id' and hasattr(self, 'source_id') and self.source_id == value:
            error_msg = "STM relation cannot connect an item to itself"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        return value
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the relation to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the relation
        """
        return {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "target_id": str(self.target_id),
            "relation_type": self.relation_type.value,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        """String representation of the STM relation."""
        return f"<STMRelation {self.source_id} --[{self.relation_type.value}:{self.strength:.2f}]--> {self.target_id}>"