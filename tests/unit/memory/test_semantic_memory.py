"""Unit tests for the Semantic Memory system.

These tests verify the functionality of the Semantic Memory implementation,
focusing on:
1. Knowledge graph structure and typed relationships
2. Concept storage and retrieval
3. Consistency management and contradiction detection
4. Inference capabilities across the knowledge graph
5. Abstraction from episodic to semantic memory
"""


import pytest

# Re-add imports for Concept, Relationship, RelationshipType (assuming from core)
from neuroca.core.memory.semantic_memory import Concept, Relationship, RelationshipType

# Import the concrete implementation from the correct location
from neuroca.memory.semantic_memory import SemanticMemory


@pytest.fixture()
def semantic_memory():
    """Fixture providing a clean semantic memory instance for each test."""
    memory = SemanticMemory()
    yield memory
    memory.clear()


@pytest.fixture()
def populated_semantic_memory():
    """Fixture providing a semantic memory with sample concepts and relationships."""
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


def test_concept_storage(semantic_memory):
    """Test basic storage and retrieval of concepts."""
    # Create and store a concept
    concept = Concept(id="test1", name="Test Concept", description="A test concept")
    chunk_id = semantic_memory.store(concept)
    
    # Verify the chunk ID format
    assert chunk_id == "concept:test1"
    
    # Retrieve the concept
    chunks = semantic_memory.retrieve("test1")
    assert len(chunks) == 1
    assert chunks[0].content.id == "test1"
    assert chunks[0].content.name == "Test Concept"
    
    # Retrieve by name
    chunks = semantic_memory.retrieve("Test Concept")
    assert len(chunks) == 1
    assert chunks[0].content.id == "test1"


def test_relationship_storage(semantic_memory):
    """Test storage and retrieval of relationships between concepts."""
    # Create and store two concepts
    concept1 = Concept(id="c1", name="Concept 1")
    concept2 = Concept(id="c2", name="Concept 2")
    semantic_memory.store(concept1)
    semantic_memory.store(concept2)
    
    # Create and store a relationship
    relationship = Relationship("c1", "c2", RelationshipType.IS_A)
    chunk_id = semantic_memory.store(relationship)
    
    # Verify the chunk ID format
    assert chunk_id == "relationship:c1:IS_A:c2"
    
    # Retrieve the relationship
    chunks = semantic_memory.retrieve(("c1", RelationshipType.IS_A, "c2"))
    assert len(chunks) == 1
    assert chunks[0].content.source_id == "c1"
    assert chunks[0].content.target_id == "c2"
    assert chunks[0].content.relationship_type == RelationshipType.IS_A


def test_relationship_validation(semantic_memory):
    """Test that relationships require valid concepts."""
    # Try to create a relationship with non-existent concepts
    relationship = Relationship("nonexistent1", "nonexistent2", RelationshipType.IS_A)
    
    # This should raise a ValueError
    with pytest.raises(ValueError):
        semantic_memory.store(relationship)
    
    # Create one concept but not the other
    concept1 = Concept(id="c1", name="Concept 1")
    semantic_memory.store(concept1)
    
    # This should still raise a ValueError for the missing target
    relationship = Relationship("c1", "nonexistent2", RelationshipType.IS_A)
    with pytest.raises(ValueError):
        semantic_memory.store(relationship)


def test_updating_existing_concept(semantic_memory):
    """Test updating an existing concept with new information."""
    # Create and store initial concept
    concept = Concept(
        id="update_test", 
        name="Initial Name",
        description="Initial description",
        properties={"prop1": "value1"}
    )
    semantic_memory.store(concept)
    
    # Create updated version of the concept
    updated_concept = Concept(
        id="update_test",
        name="Initial Name",  # Same name
        description="Updated description",
        properties={"prop1": "updated", "prop2": "new"}
    )
    
    # Store the updated concept
    semantic_memory.store(updated_concept)
    
    # Retrieve and verify it was updated
    chunks = semantic_memory.retrieve("update_test")
    assert len(chunks) == 1
    updated = chunks[0].content
    
    assert updated.description == "Updated description"
    assert updated.properties["prop1"] == "updated"
    assert updated.properties["prop2"] == "new"


def test_updating_existing_relationship(semantic_memory):
    """Test updating an existing relationship with new information."""
    # Create concepts
    concept1 = Concept(id="c1", name="Concept 1")
    concept2 = Concept(id="c2", name="Concept 2")
    semantic_memory.store(concept1)
    semantic_memory.store(concept2)
    
    # Create initial relationship
    rel = Relationship(
        "c1", "c2", RelationshipType.IS_A,
        confidence=0.5,
        attributes={"attr1": "value1"}
    )
    semantic_memory.store(rel)
    
    # Create updated relationship
    updated_rel = Relationship(
        "c1", "c2", RelationshipType.IS_A,
        confidence=0.8,
        attributes={"attr1": "updated", "attr2": "new"}
    )
    
    # Store the updated relationship
    semantic_memory.store(updated_rel)
    
    # Retrieve and verify it was updated
    chunks = semantic_memory.retrieve(("c1", RelationshipType.IS_A, "c2"))
    assert len(chunks) == 1
    updated = chunks[0].content
    
    # Check that the confidence and attributes were updated
    assert 0.5 < updated.confidence < 0.8  # Should be somewhere in between due to averaging
    assert updated.attributes["attr1"] == "updated"
    assert updated.attributes["attr2"] == "new"


def test_forgetting_concepts_and_relationships(semantic_memory):
    """Test forgetting concepts and relationships."""
    # Create concepts and relationship
    concept1 = Concept(id="forget1", name="Forget Test 1")
    concept2 = Concept(id="forget2", name="Forget Test 2")
    semantic_memory.store(concept1)
    semantic_memory.store(concept2)
    
    rel = Relationship("forget1", "forget2", RelationshipType.IS_A)
    rel_id = semantic_memory.store(rel)
    
    # Try to forget a concept with relationships - should fail
    result = semantic_memory.forget("concept:forget1")
    assert result is False
    
    # Forget the relationship first
    result = semantic_memory.forget(rel_id)
    assert result is True
    
    # Now forget the concept
    result = semantic_memory.forget("concept:forget1")
    assert result is True
    
    # Verify the concept is gone
    chunks = semantic_memory.retrieve("forget1")
    assert len(chunks) == 0


def test_hierarchical_relationships(populated_semantic_memory):
    """Test hierarchical IS_A relationships and property inheritance."""
    # Get properties for a concept
    golden_props = populated_semantic_memory.infer_concept_properties("golden")
    
    # Should inherit properties from dog and mammal
    assert golden_props["friendly"] is True  # Own property
    assert golden_props["loyal"] is True  # From dog
    assert golden_props["domesticated"] is True  # From dog
    assert golden_props["has_fur"] is True  # From mammal
    assert golden_props["warm_blooded"] is True  # From mammal
    
    # Electric car should inherit from car and override some properties
    electric_car_props = populated_semantic_memory.infer_concept_properties("electric_car")
    assert electric_car_props["wheels"] == 4  # From car
    assert electric_car_props["requires_fuel"] is False  # Overridden from car
    assert electric_car_props["power_source"] == "electricity"  # Own property


def test_related_concepts(populated_semantic_memory):
    """Test retrieving related concepts."""
    # Get concepts related to 'dog'
    related = populated_semantic_memory.get_related_concepts("dog")
    
    # Should include mammal (IS_A), golden (dog IS_A golden), and cat (OPPOSITE_OF)
    assert RelationshipType.IS_A in related
    assert RelationshipType.OPPOSITE_OF in related
    
    # Check specific relationships
    is_a_concepts = [c.id for c in related[RelationshipType.IS_A]]
    assert "mammal" in is_a_concepts
    
    opposite_concepts = [c.id for c in related[RelationshipType.OPPOSITE_OF]]
    assert "cat" in opposite_concepts


def test_path_inference(populated_semantic_memory):
    """Test finding paths between concepts in the knowledge graph."""
    # Find paths from golden retriever to animal
    paths = populated_semantic_memory.infer_path("golden", "animal")
    
    # Should find at least one path
    assert len(paths) > 0
    
    # The path should go through dog and mammal
    path = paths[0]
    
    # Extract the concept IDs along the path
    path_ids = []
    for rel, is_forward in path:
        if is_forward:
            path_ids.append(rel.target_id)
        else:
            path_ids.append(rel.source_id)
    
    # The path should be: golden -> dog -> mammal -> animal
    assert "dog" in path_ids
    assert "mammal" in path_ids
    assert "animal" in path_ids
    
    # Check path order (if forward path)
    if all(is_forward for _, is_forward in path):
        dog_idx = path_ids.index("dog")
        mammal_idx = path_ids.index("mammal")
        animal_idx = path_ids.index("animal")
        assert dog_idx < mammal_idx < animal_idx


def test_contradiction_detection(semantic_memory):
    """Test detecting contradictions in the knowledge graph."""
    # Create concepts
    animal = Concept(id="animal", name="Animal")
    plant = Concept(id="plant", name="Plant")
    semantic_memory.store(animal)
    semantic_memory.store(plant)
    
    # Create contradictory relationships
    semantic_memory.store(Relationship("animal", "plant", RelationshipType.OPPOSITE_OF))
    
    # This should trigger a contradiction warning but still be stored
    semantic_memory.store(Relationship("animal", "plant", RelationshipType.SYNONYM_OF))
    
    # Check the consistency
    inconsistencies = semantic_memory.check_consistency()
    
    # Should find the contradiction
    assert len(inconsistencies) > 0
    contradiction = next((i for i in inconsistencies if i["type"] == "contradiction"), None)
    assert contradiction is not None
    assert (contradiction["concept1"] == "animal" and contradiction["concept2"] == "plant") or \
           (contradiction["concept1"] == "plant" and contradiction["concept2"] == "animal")


def test_circular_hierarchy_detection(semantic_memory):
    """Test detecting circular hierarchies."""
    # Create concepts
    a = Concept(id="a", name="A")
    b = Concept(id="b", name="B")
    c = Concept(id="c", name="C")
    semantic_memory.store(a)
    semantic_memory.store(b)
    semantic_memory.store(c)
    
    # Create a chain: A IS_A B, B IS_A C
    semantic_memory.store(Relationship("a", "b", RelationshipType.IS_A))
    semantic_memory.store(Relationship("b", "c", RelationshipType.IS_A))
    
    # Try to create a circular reference: C IS_A A
    # This should be stored but marked as a contradiction
    semantic_memory.store(Relationship("c", "a", RelationshipType.IS_A))
    
    # Check the consistency
    inconsistencies = semantic_memory.check_consistency()
    
    # Should find the circular hierarchy
    circular = next((i for i in inconsistencies if i["type"] == "contradiction"), None)
    assert circular is not None


def test_filtering_by_confidence(semantic_memory):
    """Test filtering retrieval results by confidence threshold."""
    # Create concepts with different confidence levels
    high_conf = Concept(id="high", name="High Confidence", confidence=0.9)
    med_conf = Concept(id="med", name="Medium Confidence", confidence=0.5)
    low_conf = Concept(id="low", name="Low Confidence", confidence=0.2)
    
    semantic_memory.store(high_conf)
    semantic_memory.store(med_conf)
    semantic_memory.store(low_conf)
    
    # Retrieve with different confidence thresholds
    high_threshold = semantic_memory.retrieve("", min_confidence=0.8)
    med_threshold = semantic_memory.retrieve("", min_confidence=0.4)
    low_threshold = semantic_memory.retrieve("", min_confidence=0.1)
    
    # Check results
    high_ids = [c.content.id for c in high_threshold]
    med_ids = [c.content.id for c in med_threshold]
    low_ids = [c.content.id for c in low_threshold]
    
    assert "high" in high_ids
    assert "med" not in high_ids
    assert "low" not in high_ids
    
    assert "high" in med_ids
    assert "med" in med_ids
    assert "low" not in med_ids
    
    assert "high" in low_ids
    assert "med" in low_ids
    assert "low" in low_ids


def test_dictionary_query_filtering(populated_semantic_memory):
    """Test filtering with dictionary-based queries."""
    # Query for concepts with specific properties
    dog_query = {
        "concept": {
            "properties": {"loyal": True}
        }
    }
    
    dog_results = populated_semantic_memory.retrieve(dog_query)
    dog_ids = [c.content.id for c in dog_results]
    assert "dog" in dog_ids
    
    # Query for relationships with specific attributes
    # (Add a relationship with attributes first)
    rel = populated_semantic_memory.get_relationship("dog", RelationshipType.IS_A, "mammal")
    rel.attributes["strength"] = "strong"
    rel_key = ("dog", RelationshipType.IS_A, "mammal")
    populated_semantic_memory._relationships[rel_key].content = rel
    
    rel_query = {
        "relationship": {
            "attributes": {"strength": "strong"}
        }
    }
    
    rel_results = populated_semantic_memory.retrieve(rel_query)
    rel_sources = [c.content.source_id for c in rel_results]
    rel_targets = [c.content.target_id for c in rel_results]
    assert "dog" in rel_sources
    assert "mammal" in rel_targets
