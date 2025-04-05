"""
Long-Term Memory (LTM) Database Schema

This module defines the database schema for the Long-Term Memory component of the
NeuroCognitive Architecture. LTM stores consolidated memories that have been processed
from Working Memory and are intended for long-term retention.

The schema includes:
- Memory entries with semantic, episodic, and procedural components
- Metadata for retrieval, including embeddings and timestamps
- Relationships between memory entries
- Importance and relevance scoring
- Decay and reinforcement mechanisms

Usage:
    from neuroca.db.schemas.ltm import LTMEntry, LTMRelationship
    
    # Create a new LTM entry
    new_memory = LTMEntry(
        content="The sky is blue because of Rayleigh scattering",
        memory_type=MemoryType.SEMANTIC,
        importance=0.75,
        embedding=[0.1, 0.2, 0.3, ...],
        metadata={"source": "conversation", "confidence": 0.92}
    )
    
    # Create a relationship between memories
    relationship = LTMRelationship(
        source_id=memory1.id,
        target_id=memory2.id,
        relationship_type=RelationshipType.CAUSAL,
        strength=0.85
    )
"""

import datetime
import enum
import json
import logging
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field, root_validator, validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Configure module logger
logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

class MemoryType(str, enum.Enum):
    """Types of long-term memories in the cognitive architecture."""
    SEMANTIC = "semantic"  # Factual knowledge
    EPISODIC = "episodic"  # Event-based memories
    PROCEDURAL = "procedural"  # Skill-based memories
    ASSOCIATIVE = "associative"  # Linked memories


class RelationshipType(str, enum.Enum):
    """Types of relationships between memory entries."""
    CAUSAL = "causal"  # Cause-effect relationship
    TEMPORAL = "temporal"  # Time-based relationship
    SPATIAL = "spatial"  # Space-based relationship
    HIERARCHICAL = "hierarchical"  # Parent-child relationship
    ASSOCIATIVE = "associative"  # General association
    CONTRADICTORY = "contradictory"  # Conflicting information


# Association table for memory tags
memory_tags = Table(
    'ltm_memory_tags',
    Base.metadata,
    Column('memory_id', UUID(as_uuid=True), ForeignKey('ltm_entries.id'), primary_key=True),
    Column('tag', String(100), primary_key=True),
    UniqueConstraint('memory_id', 'tag', name='uq_memory_tag')
)


class LTMEntry(Base):
    """
    Long-Term Memory Entry Model
    
    Represents a single memory entry in the long-term memory store.
    Each entry contains the memory content, metadata for retrieval,
    and various attributes for memory management.
    """
    __tablename__ = 'ltm_entries'
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Memory content and type
    content = Column(Text, nullable=False, index=True)
    memory_type = Column(Enum(MemoryType), nullable=False, index=True)
    
    # Vector embedding for similarity search
    embedding = Column(ARRAY(Float), nullable=True)
    
    # Memory management attributes
    importance = Column(Float, nullable=False, default=0.5, index=True)
    relevance = Column(Float, nullable=False, default=0.5, index=True)
    confidence = Column(Float, nullable=False, default=1.0)
    
    # Decay and reinforcement
    access_count = Column(Integer, nullable=False, default=0)
    last_accessed = Column(DateTime, nullable=True)
    reinforcement_factor = Column(Float, nullable=False, default=1.0)
    decay_rate = Column(Float, nullable=False, default=0.01)
    
    # Temporal information
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, 
                        onupdate=datetime.datetime.utcnow)
    
    # Additional metadata (source, context, etc.)
    metadata = Column(JSON, nullable=True)
    
    # Flags
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_core_memory = Column(Boolean, nullable=False, default=False, index=True)
    
    # Relationships
    tags = relationship("Tag", secondary=memory_tags, backref="memories")
    outgoing_relationships = relationship(
        "LTMRelationship", 
        foreign_keys="LTMRelationship.source_id",
        back_populates="source",
        cascade="all, delete-orphan"
    )
    incoming_relationships = relationship(
        "LTMRelationship", 
        foreign_keys="LTMRelationship.target_id",
        back_populates="target",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        """String representation of the memory entry."""
        return f"<LTMEntry(id={self.id}, type={self.memory_type}, importance={self.importance})>"
    
    def access(self):
        """
        Record an access to this memory, updating access count and timestamp.
        This is used for the memory reinforcement mechanism.
        """
        self.access_count += 1
        self.last_accessed = datetime.datetime.utcnow()
        logger.debug(f"Memory {self.id} accessed, new count: {self.access_count}")
    
    def calculate_current_importance(self) -> float:
        """
        Calculate the current importance of this memory based on decay and reinforcement.
        
        Returns:
            float: The current calculated importance value
        """
        if not self.last_accessed:
            return self.importance
            
        # Calculate time-based decay
        time_since_access = (datetime.datetime.utcnow() - self.last_accessed).total_seconds()
        time_factor = 1.0 / (1.0 + self.decay_rate * time_since_access / 86400.0)  # Normalize to days
        
        # Apply reinforcement based on access count
        reinforcement = min(1.0, self.reinforcement_factor * self.access_count / 10.0)
        
        # Calculate final importance
        calculated_importance = self.importance * time_factor * (1.0 + reinforcement)
        
        # Ensure importance stays within bounds
        return max(0.0, min(1.0, calculated_importance))
    
    def update_metadata(self, new_metadata: dict[str, Any]):
        """
        Update the metadata dictionary with new values.
        
        Args:
            new_metadata: Dictionary containing new metadata to merge
        """
        if self.metadata is None:
            self.metadata = {}
            
        current_metadata = self.metadata if isinstance(self.metadata, dict) else json.loads(self.metadata)
        current_metadata.update(new_metadata)
        self.metadata = current_metadata
        self.updated_at = datetime.datetime.utcnow()
        logger.debug(f"Updated metadata for memory {self.id}")


class LTMRelationship(Base):
    """
    Relationship between two memory entries in long-term memory.
    
    Represents semantic connections between memories, such as causal,
    temporal, or associative relationships.
    """
    __tablename__ = 'ltm_relationships'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationship endpoints
    source_id = Column(UUID(as_uuid=True), ForeignKey('ltm_entries.id'), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey('ltm_entries.id'), nullable=False, index=True)
    
    # Relationship attributes
    relationship_type = Column(Enum(RelationshipType), nullable=False, index=True)
    strength = Column(Float, nullable=False, default=0.5)
    bidirectional = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    
    # Relationships
    source = relationship("LTMEntry", foreign_keys=[source_id], back_populates="outgoing_relationships")
    target = relationship("LTMEntry", foreign_keys=[target_id], back_populates="incoming_relationships")
    
    # Ensure we don't have duplicate relationships
    __table_args__ = (
        UniqueConstraint('source_id', 'target_id', 'relationship_type', name='uq_ltm_relationship'),
    )
    
    def __repr__(self):
        """String representation of the relationship."""
        return f"<LTMRelationship(source={self.source_id}, target={self.target_id}, type={self.relationship_type})>"
    
    def strengthen(self, amount: float = 0.1):
        """
        Strengthen this relationship by the specified amount.
        
        Args:
            amount: Amount to increase the relationship strength by
        """
        self.strength = min(1.0, self.strength + amount)
        self.updated_at = datetime.datetime.utcnow()
        logger.debug(f"Strengthened relationship {self.id} to {self.strength}")
    
    def weaken(self, amount: float = 0.1):
        """
        Weaken this relationship by the specified amount.
        
        Args:
            amount: Amount to decrease the relationship strength by
        """
        self.strength = max(0.0, self.strength - amount)
        self.updated_at = datetime.datetime.utcnow()
        logger.debug(f"Weakened relationship {self.id} to {self.strength}")


class Tag(Base):
    """
    Tags for categorizing and retrieving memory entries.
    """
    __tablename__ = 'ltm_tags'
    
    name = Column(String(100), primary_key=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        """String representation of the tag."""
        return f"<Tag(name={self.name})>"


# Pydantic models for API validation and serialization

class LTMEntryCreate(BaseModel):
    """Pydantic model for creating a new LTM entry."""
    content: str
    memory_type: MemoryType
    importance: float = Field(0.5, ge=0.0, le=1.0)
    relevance: float = Field(0.5, ge=0.0, le=1.0)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    embedding: Optional[list[float]] = None
    metadata: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None
    is_core_memory: bool = False
    
    @validator('content')
    def content_not_empty(cls, v):
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("Memory content cannot be empty")
        return v.strip()
    
    @validator('embedding')
    def validate_embedding(cls, v):
        """Validate embedding vector if provided."""
        if v is not None:
            if len(v) == 0:
                raise ValueError("Embedding vector cannot be empty")
            if any(not isinstance(x, (int, float)) for x in v):
                raise ValueError("Embedding vector must contain only numbers")
        return v


class LTMEntryUpdate(BaseModel):
    """Pydantic model for updating an existing LTM entry."""
    content: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    embedding: Optional[list[float]] = None
    metadata: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_core_memory: Optional[bool] = None
    decay_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    reinforcement_factor: Optional[float] = Field(None, ge=0.0)
    
    @validator('content')
    def content_not_empty(cls, v):
        """Validate that content is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Memory content cannot be empty")
        return v.strip() if v else v


class LTMRelationshipCreate(BaseModel):
    """Pydantic model for creating a new LTM relationship."""
    source_id: uuid.UUID
    target_id: uuid.UUID
    relationship_type: RelationshipType
    strength: float = Field(0.5, ge=0.0, le=1.0)
    bidirectional: bool = False
    metadata: Optional[dict[str, Any]] = None
    
    @root_validator
    def validate_not_self_relationship(cls, values):
        """Validate that a memory cannot have a relationship with itself."""
        if values.get('source_id') == values.get('target_id'):
            raise ValueError("A memory cannot have a relationship with itself")
        return values


class LTMRelationshipUpdate(BaseModel):
    """Pydantic model for updating an existing LTM relationship."""
    relationship_type: Optional[RelationshipType] = None
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    bidirectional: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class TagCreate(BaseModel):
    """Pydantic model for creating a new tag."""
    name: str
    description: Optional[str] = None
    
    @validator('name')
    def validate_tag_name(cls, v):
        """Validate tag name format."""
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        if len(v) > 100:
            raise ValueError("Tag name cannot exceed 100 characters")
        # Ensure tag name is lowercase and contains only alphanumeric chars and hyphens
        cleaned = v.lower().strip()
        if not all(c.isalnum() or c == '-' for c in cleaned):
            raise ValueError("Tag name can only contain letters, numbers, and hyphens")
        return cleaned