"""
Pytest fixtures for memory system tests.

This module provides common fixtures for testing memory components such as
working memory, episodic memory, semantic memory, and consolidation processes.
"""

from datetime import datetime, timedelta

import pytest

# Import the concrete implementation instead of the abstract base class
from neuroca.core.memory.consolidation import StandardMemoryConsolidator
from neuroca.core.memory.episodic_memory import EpisodicMemory

# Re-add imports for Concept, Relationship, RelationshipType (assuming from core)
from neuroca.core.memory.semantic_memory import Concept, Relationship, RelationshipType
from neuroca.core.memory.working_memory import WorkingMemory

# Import the concrete implementation from the correct location
from neuroca.memory.semantic_memory import SemanticMemory


@pytest.fixture()
def working_memory():
    """Fixture that provides a clean working memory instance."""
    memory = WorkingMemory()
    yield memory
    # Cleanup after test completes
    memory.clear()


@pytest.fixture()
def episodic_memory():
    """Fixture that provides a clean episodic memory instance."""
    memory = EpisodicMemory()
    yield memory
    # Cleanup after test completes
    memory.clear()


@pytest.fixture()
def semantic_memory():
    """Fixture that provides a clean semantic memory instance."""
    memory = SemanticMemory()
    yield memory
    # Cleanup after test completes
    memory.clear()


@pytest.fixture()
def memory_consolidator():
    """Fixture that provides a standard memory consolidator."""
    # Instantiate the concrete class
    consolidator = StandardMemoryConsolidator() 
    return consolidator


@pytest.fixture()
def populated_working_memory():
    """Fixture that provides a working memory with some sample memories."""
    memory = WorkingMemory()
    
    # Add some memories with varying activation levels
    ids = []
    ids.append(memory.store("Important fact about cognitive architecture"))
    ids.append(memory.store("Memory with medium importance"))
    ids.append(memory.store("Low priority information"))
    
    # Adjust activation levels
    memory.retrieve_by_id(ids[0]).update_activation(0.9)  # High
    memory.retrieve_by_id(ids[1]).update_activation(0.6)  # Medium
    memory.retrieve_by_id(ids[2]).update_activation(0.3)  # Low
    
    yield memory
    memory.clear()


@pytest.fixture()
def populated_episodic_memory():
    """Fixture that provides an episodic memory with some sample memories."""
    memory = EpisodicMemory()
    
    # Create base time
    now = datetime.now()
    
    # Add memories with different emotional salience
    for i in range(5):
        timestamp = now - timedelta(hours=i)
        memory.store(
            f"Emotional memory {i}",
            emotional_salience=0.2 * i,
            metadata={"timestamp": timestamp.timestamp()}
        )
    
    # Add a sequence of related memories
    sequence_id = "breakfast-routine"
    memory.store(
        "Woke up and got out of bed",
        sequence_id=sequence_id,
        sequence_index=1,
        metadata={"timestamp": (now - timedelta(minutes=60)).timestamp()}
    )
    memory.store(
        "Brushed teeth and washed face", 
        sequence_id=sequence_id,
        sequence_index=2,
        metadata={"timestamp": (now - timedelta(minutes=50)).timestamp()}
    )
    memory.store(
        "Made coffee and toast",
        sequence_id=sequence_id,
        sequence_index=3,
        metadata={"timestamp": (now - timedelta(minutes=40)).timestamp()}
    )
    memory.store(
        "Ate breakfast while reading news",
        sequence_id=sequence_id,
        sequence_index=4,
        metadata={"timestamp": (now - timedelta(minutes=30)).timestamp()}
    )
    
    yield memory
    memory.clear()


@pytest.fixture()
def populated_semantic_memory():
    """Provides a semantic memory with sample concepts and relationships.
    
    Contains:
    - A taxonomy of animals and vehicles
    - Properties assigned to concepts
    - Various relationship types
    """
    memory = SemanticMemory()
    
    # Create some basic concepts
    concepts = {
        "animal": Concept(id="animal", name="Animal", description="Living organism capable of movement"),
        "mammal": Concept(id="mammal", name="Mammal", description="Warm-blooded animal with fur/hair"),
        "dog": Concept(id="dog", name="Dog", description="Domesticated canine"),
        "cat": Concept(id="cat", name="Cat", description="Domesticated feline"),
        "golden": Concept(id="golden", name="Golden Retriever", description="Friendly dog breed"),
        "vehicle": Concept(id="vehicle", name="Vehicle", description="Machine that transports people/goods"),
        "car": Concept(id="car", name="Car", description="Four-wheeled motor vehicle"),
        "electric_car": Concept(id="electric_car", name="Electric Car", description="Car powered by electricity"),
    }
    
    # Add properties to concepts
    concepts["mammal"].properties = {"has_fur": True, "warm_blooded": True}
    concepts["dog"].properties = {"domesticated": True, "loyal": True}
    concepts["golden"].properties = {"friendly": True, "color": "golden"}
    concepts["car"].properties = {"wheels": 4, "requires_fuel": True}
    concepts["electric_car"].properties = {"wheels": 4, "requires_fuel": False, "power_source": "electricity"}
    
    # Store all concepts
    for concept in concepts.values():
        memory.store(concept)
    
    # Create relationships
    relationships = [
        # Taxonomy relationships
        Relationship("mammal", "animal", RelationshipType.IS_A),
        Relationship("dog", "mammal", RelationshipType.IS_A),
        Relationship("cat", "mammal", RelationshipType.IS_A),
        Relationship("golden", "dog", RelationshipType.IS_A),
        Relationship("car", "vehicle", RelationshipType.IS_A),
        Relationship("electric_car", "car", RelationshipType.IS_A),
        
        # Other relationships
        Relationship("dog", "cat", RelationshipType.OPPOSITE_OF),
        Relationship("cat", "dog", RelationshipType.OPPOSITE_OF),  # Symmetric
    ]
    
    # Store all relationships
    for rel in relationships:
        memory.store(rel)
    
    yield memory
    memory.clear()
