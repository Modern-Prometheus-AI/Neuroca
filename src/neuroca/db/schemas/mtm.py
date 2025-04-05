"""
Many-to-Many (MTM) Relationship Schemas for NeuroCognitive Architecture.

This module defines SQLAlchemy models for many-to-many relationship tables used throughout
the NeuroCognitive Architecture system. These tables facilitate complex relationships
between primary entities in the system such as memories, concepts, and cognitive processes.

The schemas follow SQLAlchemy best practices and include appropriate indexes, constraints,
and relationship definitions to ensure data integrity and query performance.

Usage:
    from neuroca.db.schemas.mtm import ConceptMemoryAssociation
    
    # Create a new association
    association = ConceptMemoryAssociation(concept_id=1, memory_id=2, strength=0.75)
    session.add(association)
    session.commit()
"""

import datetime
import enum
import logging
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from neuroca.core.exceptions import ValidationError
from neuroca.db.base import Base

logger = logging.getLogger(__name__)


class AssociationType(enum.Enum):
    """Defines the types of associations between entities in the system."""
    DIRECT = "direct"           # Direct, explicit association
    INFERRED = "inferred"       # Association inferred by the system
    TEMPORAL = "temporal"       # Temporal/sequential relationship
    CAUSAL = "causal"           # Causal relationship
    SEMANTIC = "semantic"       # Semantic/meaning-based relationship
    EPISODIC = "episodic"       # Episode-based relationship


class ConceptMemoryAssociation(Base):
    """
    Associates concepts with memories with a strength value.
    
    This relationship is fundamental to the semantic memory system, allowing
    concepts to be linked to specific memories with varying degrees of strength.
    """
    __tablename__ = "concept_memory_associations"
    
    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    memory_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    
    # Association metadata
    strength = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    association_type = Column(Enum(AssociationType), nullable=False, default=AssociationType.DIRECT)
    last_activated = Column(DateTime, nullable=False, default=func.now())
    activation_count = Column(Integer, nullable=False, default=1)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships (back-references)
    concept = relationship("Concept", back_populates="memories")
    memory = relationship("Memory", back_populates="concepts")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('concept_id', 'memory_id', name='uix_concept_memory'),
        Index('idx_concept_memory_strength', 'strength'),
        Index('idx_concept_memory_last_activated', 'last_activated'),
    )
    
    def __init__(self, concept_id: int, memory_id: int, strength: float = 0.5, 
                 association_type: AssociationType = AssociationType.DIRECT):
        """
        Initialize a new concept-memory association.
        
        Args:
            concept_id: ID of the concept
            memory_id: ID of the memory
            strength: Association strength (0.0 to 1.0)
            association_type: Type of association
            
        Raises:
            ValidationError: If strength is not between 0.0 and 1.0
        """
        self.validate_strength(strength)
        
        self.concept_id = concept_id
        self.memory_id = memory_id
        self.strength = strength
        self.association_type = association_type
        
        logger.debug(f"Created concept-memory association: concept_id={concept_id}, "
                    f"memory_id={memory_id}, strength={strength}")
    
    @staticmethod
    def validate_strength(strength: float) -> None:
        """
        Validate that the association strength is between 0.0 and 1.0.
        
        Args:
            strength: The association strength to validate
            
        Raises:
            ValidationError: If strength is not between 0.0 and 1.0
        """
        if not 0.0 <= strength <= 1.0:
            error_msg = f"Association strength must be between 0.0 and 1.0, got {strength}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
    
    def activate(self, strength_increment: float = 0.1) -> None:
        """
        Activate this association, updating its strength and activation metadata.
        
        Args:
            strength_increment: Amount to increase the strength by
            
        Raises:
            ValidationError: If the resulting strength would be invalid
        """
        new_strength = min(1.0, self.strength + strength_increment)
        self.validate_strength(new_strength)
        
        self.strength = new_strength
        self.last_activated = func.now()
        self.activation_count += 1
        self.updated_at = func.now()
        
        logger.debug(f"Activated association {self.id}: new strength={new_strength}, "
                    f"activation_count={self.activation_count}")


class ConceptConceptAssociation(Base):
    """
    Associates concepts with other concepts, forming a semantic network.
    
    This relationship enables the creation of a concept graph where concepts
    can be related to each other with varying degrees of strength and different
    types of relationships.
    """
    __tablename__ = "concept_concept_associations"
    
    id = Column(Integer, primary_key=True)
    source_concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    target_concept_id = Column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    
    # Association metadata
    strength = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    association_type = Column(Enum(AssociationType), nullable=False, default=AssociationType.SEMANTIC)
    bidirectional = Column(Boolean, nullable=False, default=True)
    last_activated = Column(DateTime, nullable=False, default=func.now())
    activation_count = Column(Integer, nullable=False, default=1)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships (back-references)
    source_concept = relationship("Concept", foreign_keys=[source_concept_id], 
                                 back_populates="outgoing_associations")
    target_concept = relationship("Concept", foreign_keys=[target_concept_id], 
                                 back_populates="incoming_associations")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('source_concept_id', 'target_concept_id', name='uix_concept_concept'),
        Index('idx_concept_concept_strength', 'strength'),
        Index('idx_concept_concept_last_activated', 'last_activated'),
    )
    
    def __init__(self, source_concept_id: int, target_concept_id: int, strength: float = 0.5,
                association_type: AssociationType = AssociationType.SEMANTIC, 
                bidirectional: bool = True):
        """
        Initialize a new concept-concept association.
        
        Args:
            source_concept_id: ID of the source concept
            target_concept_id: ID of the target concept
            strength: Association strength (0.0 to 1.0)
            association_type: Type of association
            bidirectional: Whether the association is bidirectional
            
        Raises:
            ValidationError: If strength is not between 0.0 and 1.0 or if source equals target
        """
        self.validate_strength(strength)
        self.validate_concepts(source_concept_id, target_concept_id)
        
        self.source_concept_id = source_concept_id
        self.target_concept_id = target_concept_id
        self.strength = strength
        self.association_type = association_type
        self.bidirectional = bidirectional
        
        logger.debug(f"Created concept-concept association: source={source_concept_id}, "
                    f"target={target_concept_id}, strength={strength}, "
                    f"bidirectional={bidirectional}")
    
    @staticmethod
    def validate_strength(strength: float) -> None:
        """
        Validate that the association strength is between 0.0 and 1.0.
        
        Args:
            strength: The association strength to validate
            
        Raises:
            ValidationError: If strength is not between 0.0 and 1.0
        """
        if not 0.0 <= strength <= 1.0:
            error_msg = f"Association strength must be between 0.0 and 1.0, got {strength}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
    
    @staticmethod
    def validate_concepts(source_id: int, target_id: int) -> None:
        """
        Validate that source and target concepts are different.
        
        Args:
            source_id: Source concept ID
            target_id: Target concept ID
            
        Raises:
            ValidationError: If source and target are the same
        """
        if source_id == target_id:
            error_msg = f"Source and target concepts must be different, got {source_id} for both"
            logger.error(error_msg)
            raise ValidationError(error_msg)
    
    def activate(self, strength_increment: float = 0.1) -> None:
        """
        Activate this association, updating its strength and activation metadata.
        
        Args:
            strength_increment: Amount to increase the strength by
            
        Raises:
            ValidationError: If the resulting strength would be invalid
        """
        new_strength = min(1.0, self.strength + strength_increment)
        self.validate_strength(new_strength)
        
        self.strength = new_strength
        self.last_activated = func.now()
        self.activation_count += 1
        self.updated_at = func.now()
        
        logger.debug(f"Activated association {self.id}: new strength={new_strength}, "
                    f"activation_count={self.activation_count}")


class MemoryMemoryAssociation(Base):
    """
    Associates memories with other memories, enabling episodic and temporal connections.
    
    This relationship allows memories to be connected to each other, supporting
    episodic memory chains, temporal sequences, and causal relationships between memories.
    """
    __tablename__ = "memory_memory_associations"
    
    id = Column(Integer, primary_key=True)
    source_memory_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    target_memory_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    
    # Association metadata
    strength = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    association_type = Column(Enum(AssociationType), nullable=False, default=AssociationType.TEMPORAL)
    temporal_distance = Column(Float, nullable=True)  # Time distance in seconds, if applicable
    last_activated = Column(DateTime, nullable=False, default=func.now())
    activation_count = Column(Integer, nullable=False, default=1)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships (back-references)
    source_memory = relationship("Memory", foreign_keys=[source_memory_id], 
                               back_populates="outgoing_associations")
    target_memory = relationship("Memory", foreign_keys=[target_memory_id], 
                               back_populates="incoming_associations")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('source_memory_id', 'target_memory_id', name='uix_memory_memory'),
        Index('idx_memory_memory_strength', 'strength'),
        Index('idx_memory_memory_association_type', 'association_type'),
        Index('idx_memory_memory_last_activated', 'last_activated'),
    )
    
    def __init__(self, source_memory_id: int, target_memory_id: int, strength: float = 0.5,
                association_type: AssociationType = AssociationType.TEMPORAL,
                temporal_distance: Optional[float] = None):
        """
        Initialize a new memory-memory association.
        
        Args:
            source_memory_id: ID of the source memory
            target_memory_id: ID of the target memory
            strength: Association strength (0.0 to 1.0)
            association_type: Type of association
            temporal_distance: Time distance in seconds between memories (if applicable)
            
        Raises:
            ValidationError: If strength is not between 0.0 and 1.0 or if source equals target
        """
        self.validate_strength(strength)
        self.validate_memories(source_memory_id, target_memory_id)
        
        self.source_memory_id = source_memory_id
        self.target_memory_id = target_memory_id
        self.strength = strength
        self.association_type = association_type
        self.temporal_distance = temporal_distance
        
        logger.debug(f"Created memory-memory association: source={source_memory_id}, "
                    f"target={target_memory_id}, strength={strength}, "
                    f"type={association_type.value}")
    
    @staticmethod
    def validate_strength(strength: float) -> None:
        """
        Validate that the association strength is between 0.0 and 1.0.
        
        Args:
            strength: The association strength to validate
            
        Raises:
            ValidationError: If strength is not between 0.0 and 1.0
        """
        if not 0.0 <= strength <= 1.0:
            error_msg = f"Association strength must be between 0.0 and 1.0, got {strength}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
    
    @staticmethod
    def validate_memories(source_id: int, target_id: int) -> None:
        """
        Validate that source and target memories are different.
        
        Args:
            source_id: Source memory ID
            target_id: Target memory ID
            
        Raises:
            ValidationError: If source and target are the same
        """
        if source_id == target_id:
            error_msg = f"Source and target memories must be different, got {source_id} for both"
            logger.error(error_msg)
            raise ValidationError(error_msg)
    
    def activate(self, strength_increment: float = 0.1) -> None:
        """
        Activate this association, updating its strength and activation metadata.
        
        Args:
            strength_increment: Amount to increase the strength by
            
        Raises:
            ValidationError: If the resulting strength would be invalid
        """
        new_strength = min(1.0, self.strength + strength_increment)
        self.validate_strength(new_strength)
        
        self.strength = new_strength
        self.last_activated = func.now()
        self.activation_count += 1
        self.updated_at = func.now()
        
        logger.debug(f"Activated association {self.id}: new strength={new_strength}, "
                    f"activation_count={self.activation_count}")


# Additional utility functions for working with associations

def create_bidirectional_concept_association(
    session: Any,
    concept_id1: int,
    concept_id2: int,
    strength: float = 0.5,
    association_type: AssociationType = AssociationType.SEMANTIC
) -> list[ConceptConceptAssociation]:
    """
    Create bidirectional associations between two concepts.
    
    Args:
        session: SQLAlchemy session
        concept_id1: First concept ID
        concept_id2: Second concept ID
        strength: Association strength (0.0 to 1.0)
        association_type: Type of association
        
    Returns:
        List of created associations
        
    Raises:
        ValidationError: If strength is invalid or concept IDs are the same
    """
    if concept_id1 == concept_id2:
        error_msg = "Cannot create bidirectional association between the same concept"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    # Create forward association
    forward = ConceptConceptAssociation(
        source_concept_id=concept_id1,
        target_concept_id=concept_id2,
        strength=strength,
        association_type=association_type,
        bidirectional=True
    )
    
    # Create backward association
    backward = ConceptConceptAssociation(
        source_concept_id=concept_id2,
        target_concept_id=concept_id1,
        strength=strength,
        association_type=association_type,
        bidirectional=True
    )
    
    session.add_all([forward, backward])
    logger.info(f"Created bidirectional concept association between {concept_id1} and {concept_id2}")
    
    return [forward, backward]


def decay_associations(session: Any, decay_factor: float = 0.05, 
                      older_than_days: int = 7) -> dict[str, int]:
    """
    Apply decay to association strengths based on time since last activation.
    
    This function implements the memory decay aspect of the cognitive architecture,
    gradually reducing the strength of associations that haven't been activated recently.
    
    Args:
        session: SQLAlchemy session
        decay_factor: Amount to decrease strength by (0.0 to 1.0)
        older_than_days: Only decay associations older than this many days
        
    Returns:
        Dictionary with counts of updated associations by type
        
    Raises:
        ValidationError: If decay_factor is not between 0.0 and 1.0
    """
    if not 0.0 <= decay_factor <= 1.0:
        error_msg = f"Decay factor must be between 0.0 and 1.0, got {decay_factor}"
        logger.error(error_msg)
        raise ValidationError(error_msg)
    
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=older_than_days)
    results = {"concept_memory": 0, "concept_concept": 0, "memory_memory": 0}
    
    # Process each association type
    for association_class, key in [
        (ConceptMemoryAssociation, "concept_memory"),
        (ConceptConceptAssociation, "concept_concept"),
        (MemoryMemoryAssociation, "memory_memory")
    ]:
        associations = session.query(association_class).filter(
            association_class.last_activated < cutoff_date
        ).all()
        
        for assoc in associations:
            # Apply decay but don't let strength go below 0.0
            assoc.strength = max(0.0, assoc.strength - decay_factor)
            results[key] += 1
    
    logger.info(f"Decayed associations: {results}")
    return results