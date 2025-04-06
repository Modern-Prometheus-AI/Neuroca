"""Shared fixtures for memory integration tests.

This module provides pytest fixtures for testing integrated memory systems,
including fully configured memory tiers with consolidation mechanisms.
"""

import time

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
def integrated_memory_system():
    """Provides a fully integrated memory system with all three tiers.
    
    Returns:
        tuple: Contains (working_memory, episodic_memory, semantic_memory, consolidator)
    """
    working_memory = WorkingMemory()
    episodic_memory = EpisodicMemory()
    semantic_memory = SemanticMemory()
    consolidator = MemoryConsolidator()
    
    yield (working_memory, episodic_memory, semantic_memory, consolidator)
    
    # Clean up after test
    working_memory.clear()
    episodic_memory.clear()
    semantic_memory.clear()


@pytest.fixture()
def populated_knowledge_graph():
    """Provides a semantic memory populated with a starter knowledge graph.
    
    The knowledge graph includes a taxonomy of:
    - Animals (mammals, birds, reptiles)
    - Vehicles (cars, boats, planes)
    - Locations (countries, cities)
    
    With appropriate relationships between concepts.
    
    Returns:
        SemanticMemory: A populated semantic memory system
    """
    memory = SemanticMemory()
    
    # Create base concepts
    concepts = {
        # Top level categories
        "entity": Concept(id="entity", name="Entity", description="Any object or concept"),
        "living": Concept(id="living", name="Living Entity", description="Entities that are alive"),
        "nonliving": Concept(id="nonliving", name="Non-living Entity", description="Entities that are not alive"),
        
        # Animal kingdom
        "animal": Concept(id="animal", name="Animal", description="Living organism of the kingdom Animalia"),
        "mammal": Concept(id="mammal", name="Mammal", description="Warm-blooded vertebrate animal"),
        "bird": Concept(id="bird", name="Bird", description="Warm-blooded vertebrate with feathers"),
        "reptile": Concept(id="reptile", name="Reptile", description="Cold-blooded vertebrate animal"),
        
        # Mammals
        "dog": Concept(id="dog", name="Dog", description="Domesticated canine, Canis familiaris"),
        "cat": Concept(id="cat", name="Cat", description="Domesticated feline, Felis catus"),
        "human": Concept(id="human", name="Human", description="Homo sapiens"),
        
        # Birds
        "eagle": Concept(id="eagle", name="Eagle", description="Large bird of prey"),
        "sparrow": Concept(id="sparrow", name="Sparrow", description="Small passerine bird"),
        
        # Reptiles
        "snake": Concept(id="snake", name="Snake", description="Elongated legless reptile"),
        "turtle": Concept(id="turtle", name="Turtle", description="Reptile with a shell"),
        
        # Vehicles
        "vehicle": Concept(id="vehicle", name="Vehicle", description="Machine that transports people or cargo"),
        "car": Concept(id="car", name="Car", description="Four-wheeled motor vehicle"),
        "boat": Concept(id="boat", name="Boat", description="Watercraft"),
        "plane": Concept(id="plane", name="Plane", description="Aircraft"),
        
        # Locations
        "location": Concept(id="location", name="Location", description="A place or position"),
        "country": Concept(id="country", name="Country", description="Political territory"),
        "city": Concept(id="city", name="City", description="Large human settlement"),
        
        # Specific examples
        "germany": Concept(id="germany", name="Germany", description="Country in central Europe"),
        "berlin": Concept(id="berlin", name="Berlin", description="Capital city of Germany"),
        "golden": Concept(id="golden", name="Golden Retriever", description="Breed of dog"),
        "tesla": Concept(id="tesla", name="Tesla", description="Brand of electric car"),
    }
    
    # Set properties
    concepts["mammal"].properties = {"warm_blooded": True, "has_fur": True}
    concepts["bird"].properties = {"warm_blooded": True, "has_feathers": True, "can_fly": True}
    concepts["reptile"].properties = {"cold_blooded": True, "has_scales": True}
    
    concepts["dog"].properties = {"domesticated": True, "loyal": True}
    concepts["cat"].properties = {"domesticated": True, "independent": True}
    concepts["human"].properties = {"intelligent": True, "tool_user": True}
    
    concepts["golden"].properties = {"friendly": True, "color": "golden"}
    concepts["tesla"].properties = {"electric": True, "modern": True}
    
    concepts["car"].properties = {"wheels": 4, "requires_road": True}
    concepts["boat"].properties = {"requires_water": True}
    concepts["plane"].properties = {"flies": True, "requires_airport": True}
    
    # Store all concepts
    for concept in concepts.values():
        memory.store(concept)
    
    # Create relationships
    relationships = [
        # Basic taxonomy
        Relationship("living", "entity", RelationshipType.IS_A),
        Relationship("nonliving", "entity", RelationshipType.IS_A),
        
        Relationship("animal", "living", RelationshipType.IS_A),
        Relationship("vehicle", "nonliving", RelationshipType.IS_A),
        Relationship("location", "nonliving", RelationshipType.IS_A),
        
        # Animal taxonomy
        Relationship("mammal", "animal", RelationshipType.IS_A),
        Relationship("bird", "animal", RelationshipType.IS_A),
        Relationship("reptile", "animal", RelationshipType.IS_A),
        
        Relationship("dog", "mammal", RelationshipType.IS_A),
        Relationship("cat", "mammal", RelationshipType.IS_A),
        Relationship("human", "mammal", RelationshipType.IS_A),
        
        Relationship("eagle", "bird", RelationshipType.IS_A),
        Relationship("sparrow", "bird", RelationshipType.IS_A),
        
        Relationship("snake", "reptile", RelationshipType.IS_A),
        Relationship("turtle", "reptile", RelationshipType.IS_A),
        
        # Vehicle taxonomy
        Relationship("car", "vehicle", RelationshipType.IS_A),
        Relationship("boat", "vehicle", RelationshipType.IS_A),
        Relationship("plane", "vehicle", RelationshipType.IS_A),
        
        # Location taxonomy
        Relationship("country", "location", RelationshipType.IS_A),
        Relationship("city", "location", RelationshipType.IS_A),
        
        # Specific examples
        Relationship("golden", "dog", RelationshipType.IS_A),
        Relationship("tesla", "car", RelationshipType.IS_A),
        Relationship("germany", "country", RelationshipType.IS_A),
        Relationship("berlin", "city", RelationshipType.IS_A),
        
        # Other relationships
        Relationship("berlin", "germany", RelationshipType.LOCATED_IN),
        Relationship("dog", "cat", RelationshipType.OPPOSITE_OF),
        Relationship("cat", "dog", RelationshipType.OPPOSITE_OF),
    ]
    
    # Store relationships
    for rel in relationships:
        memory.store(rel)
    
    return memory


@pytest.fixture()
def realistic_memory_load():
    """Provides a memory system loaded with realistic cognitive data.
    
    The system includes:
    - Working memory with a mix of high and low activation items
    - Episodic memory with varied emotional salience and temporal contexts
    - Semantic memory with a reasonable knowledge graph
    - Consolidation thresholds set to biologically plausible values
    
    Returns:
        tuple: Contains (working_memory, episodic_memory, semantic_memory, consolidator)
    """
    # Create base memory systems
    working_memory = WorkingMemory()
    episodic_memory = EpisodicMemory()
    # Instantiate the concrete class
    semantic_memory = SemanticMemory() 
    # Instantiate the concrete class
    consolidator = StandardMemoryConsolidator() 
    
    # Load working memory with mixed content (simulating active thought process)
    working_items = [
        ("Need to pick up groceries later", 0.9, {"priority": "high", "category": "task"}),
        ("The capital of France is Paris", 0.7, {"category": "fact", "learned_at": time.time() - 3600}),
        ("That presentation is due on Friday", 0.85, {"priority": "high", "emotional_salience": 0.6}),
        ("My friend's phone number is 555-1234", 0.6, {"category": "contact"}),
        ("The weather forecast mentioned rain", 0.5, {"category": "observation"}),
        ("The movie was really entertaining", 0.4, {"category": "opinion", "emotional_salience": 0.5}),
        ("Need to fix that bug in the code", 0.75, {"category": "task", "priority": "medium"}),
    ]
    
    for content, activation, metadata in working_items:
        working_memory.store(content, activation=activation, metadata=metadata)
    
    # Load episodic memory with experiences
    episodic_items = [
        # Recent memories (last 24 hours)
        ("Had coffee with Sarah this morning", {"emotional_salience": 0.6, "timestamp": time.time() - 3600}),
        ("Read an interesting article about space", {"emotional_salience": 0.4, "timestamp": time.time() - 7200}),
        ("Got stuck in traffic on the way to work", {"emotional_salience": 0.5, "timestamp": time.time() - 10800}),
        
        # Memory sequence (breakfast routine)
        ("Woke up at 7 AM", {"sequence_id": "morning-routine", "sequence_index": 1, 
                            "timestamp": time.time() - 86400}),
        ("Took a shower", {"sequence_id": "morning-routine", "sequence_index": 2, 
                          "timestamp": time.time() - 86400 + 1200}),
        ("Had breakfast", {"sequence_id": "morning-routine", "sequence_index": 3, 
                          "timestamp": time.time() - 86400 + 2400}),
        ("Drove to work", {"sequence_id": "morning-routine", "sequence_index": 4, 
                          "timestamp": time.time() - 86400 + 3600}),
        
        # Emotional memories
        ("My graduation day", {"emotional_salience": 0.9, "timestamp": time.time() - 31536000}),
        ("First day at new job", {"emotional_salience": 0.85, "timestamp": time.time() - 7776000}),
        ("The argument with Tom", {"emotional_salience": 0.8, "timestamp": time.time() - 1209600}),
        
        # Regular memories with varying emotional content
        ("Went to the grocery store", {"emotional_salience": 0.2, "timestamp": time.time() - 172800}),
        ("Watched a documentary about dolphins", {"emotional_salience": 0.4, "timestamp": time.time() - 259200}),
        ("Cooked pasta for dinner", {"emotional_salience": 0.3, "timestamp": time.time() - 345600}),
    ]
    
    for content, metadata in episodic_items:
        episodic_memory.store(content, metadata=metadata)
    
    # Load semantic memory with a basic knowledge graph
    concepts = {
        # Basic concepts
        "person": Concept(id="person", name="Person", properties={"sentient": True, "human": True}),
        "food": Concept(id="food", name="Food", properties={"edible": True}),
        "vehicle": Concept(id="vehicle", name="Vehicle", properties={"transportation": True}),
        
        # People concepts
        "friend": Concept(id="friend", name="Friend", properties={"trusted": True, "positive_relationship": True}),
        "colleague": Concept(id="colleague", name="Colleague", properties={"professional_relationship": True}),
        
        # Food concepts
        "fruit": Concept(id="fruit", name="Fruit", properties={"sweet": True, "grows_on_plants": True}),
        "vegetable": Concept(id="vegetable", name="Vegetable", properties={"nutritious": True}),
        "pasta": Concept(id="pasta", name="Pasta", properties={"carbohydrate": True}),
        
        # Transportation concepts
        "car": Concept(id="car", name="Car", properties={"wheels": 4, "requires_fuel": True}),
        "bus": Concept(id="bus", name="Bus", properties={"public_transport": True}),
        
        # Specific instances
        "sarah": Concept(id="sarah", name="Sarah", properties={"female": True}),
        "tom": Concept(id="tom", name="Tom", properties={"male": True}),
        "my_car": Concept(id="my_car", name="My Car", properties={"color": "blue", "model": "sedan"}),
    }
    
    # Store all concepts
    for concept in concepts.values():
        semantic_memory.store(concept)
    
    # Create relationships
    relationships = [
        # Taxonomy relationships
        Relationship("friend", "person", RelationshipType.IS_A),
        Relationship("colleague", "person", RelationshipType.IS_A),
        
        Relationship("fruit", "food", RelationshipType.IS_A),
        Relationship("vegetable", "food", RelationshipType.IS_A),
        Relationship("pasta", "food", RelationshipType.IS_A),
        
        Relationship("car", "vehicle", RelationshipType.IS_A),
        Relationship("bus", "vehicle", RelationshipType.IS_A),
        
        # Instance relationships
        Relationship("sarah", "friend", RelationshipType.IS_A),
        Relationship("tom", "colleague", RelationshipType.IS_A),
        Relationship("my_car", "car", RelationshipType.IS_A),
    ]
    
    # Store all relationships
    for rel in relationships:
        semantic_memory.store(rel)
    
    yield (working_memory, episodic_memory, semantic_memory, consolidator)
    
    # Clean up
    working_memory.clear()
    episodic_memory.clear()
    semantic_memory.clear()
