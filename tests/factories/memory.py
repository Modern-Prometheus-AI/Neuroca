"""
Memory Test Factories Module

This module provides factory classes and functions for creating test fixtures related to
the memory components of the NeuroCognitive Architecture (NCA). These factories follow
the Factory pattern to generate consistent, customizable test data for unit and integration tests.

The factories in this module support the three-tiered memory system:
- Working Memory (short-term)
- Episodic Memory (medium-term)
- Semantic Memory (long-term)

Usage:
    from neuroca.tests.factories.memory import WorkingMemoryFactory, MemoryItemFactory
    
    # Create a default working memory instance
    working_memory = WorkingMemoryFactory.create()
    
    # Create a working memory with custom capacity
    custom_memory = WorkingMemoryFactory.create(capacity=10)
    
    # Create a batch of memory items
    items = MemoryItemFactory.create_batch(5, importance=0.8)
"""

import datetime
import logging
import random
import uuid
from typing import Any

import factory
from factory.fuzzy import FuzzyChoice, FuzzyDateTime, FuzzyFloat, FuzzyText

# Import memory models
try:
    from neuroca.memory.models import (
        EpisodicMemory,
        MemoryItem,
        SemanticMemory,
        WorkingMemory,
    )
    from neuroca.memory.types import MemoryItemType, MemoryPriority
except ImportError:
    logging.warning(
        "Memory models could not be imported. Using mock classes for testing purposes."
    )
    # Mock classes for testing without dependencies
    class MemoryItemType:
        FACT = "fact"
        CONCEPT = "concept"
        EXPERIENCE = "experience"
        PROCEDURE = "procedure"
        EMOTION = "emotion"
        
    class MemoryPriority:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
        
    class MemoryItem:
        def __init__(
            self,
            id: str = None,
            content: str = "",
            item_type: str = MemoryItemType.FACT,
            created_at: datetime.datetime = None,
            last_accessed: datetime.datetime = None,
            importance: float = 0.5,
            relevance: float = 0.5,
            priority: str = MemoryPriority.MEDIUM,
            metadata: dict[str, Any] = None,
            embedding: list[float] = None,
        ):
            self.id = id or str(uuid.uuid4())
            self.content = content
            self.item_type = item_type
            self.created_at = created_at or datetime.datetime.now()
            self.last_accessed = last_accessed or self.created_at
            self.importance = importance
            self.relevance = relevance
            self.priority = priority
            self.metadata = metadata or {}
            self.embedding = embedding or []
            
    class WorkingMemory:
        def __init__(self, capacity: int = 7, items: list[MemoryItem] = None):
            self.capacity = capacity
            self.items = items or []
            
    class EpisodicMemory:
        def __init__(self, capacity: int = 100, episodes: list[dict] = None):
            self.capacity = capacity
            self.episodes = episodes or []
            
    class SemanticMemory:
        def __init__(self, facts: dict[str, Any] = None, concepts: dict[str, Any] = None):
            self.facts = facts or {}
            self.concepts = concepts or {}


# Configure logger
logger = logging.getLogger(__name__)


class MemoryItemFactory(factory.Factory):
    """
    Factory for creating MemoryItem instances for testing purposes.
    
    This factory generates realistic memory items with customizable properties
    for use in unit and integration tests of the memory system.
    """
    
    class Meta:
        model = MemoryItem
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    content = FuzzyText(length=50)
    item_type = FuzzyChoice([
        MemoryItemType.FACT,
        MemoryItemType.CONCEPT,
        MemoryItemType.EXPERIENCE,
        MemoryItemType.PROCEDURE,
        MemoryItemType.EMOTION,
    ])
    created_at = FuzzyDateTime(
        datetime.datetime.now() - datetime.timedelta(days=30),
        datetime.datetime.now()
    )
    last_accessed = factory.LazyAttribute(
        lambda o: o.created_at + datetime.timedelta(
            seconds=random.randint(0, 60 * 60 * 24 * 30)
        )
    )
    importance = FuzzyFloat(0.0, 1.0)
    relevance = FuzzyFloat(0.0, 1.0)
    priority = FuzzyChoice([
        MemoryPriority.LOW,
        MemoryPriority.MEDIUM,
        MemoryPriority.HIGH,
        MemoryPriority.CRITICAL,
    ])
    metadata = factory.LazyFunction(
        lambda: {
            "source": random.choice(["user", "system", "inference", "external"]),
            "confidence": random.uniform(0.5, 1.0),
            "tags": random.sample(
                ["important", "personal", "work", "health", "goal", "task"],
                k=random.randint(0, 3)
            )
        }
    )
    embedding = factory.LazyFunction(
        lambda: [random.uniform(-1.0, 1.0) for _ in range(random.randint(64, 128))]
    )
    
    @classmethod
    def create_batch_with_related_content(
        cls, size: int, base_content: str, **kwargs
    ) -> list[MemoryItem]:
        """
        Create a batch of memory items with related content based on a common theme.
        
        Args:
            size: Number of memory items to create
            base_content: Base content string to derive related content from
            **kwargs: Additional attributes to set on all created items
            
        Returns:
            List of related memory items
        """
        logger.debug(f"Creating batch of {size} related memory items based on '{base_content}'")
        
        items = []
        for i in range(size):
            # Create variations of the base content
            content_variation = f"{base_content} - Variation {i+1}"
            item = cls.create(content=content_variation, **kwargs)
            items.append(item)
            
        return items


class WorkingMemoryFactory(factory.Factory):
    """
    Factory for creating WorkingMemory instances for testing purposes.
    
    This factory generates working memory instances with configurable capacity
    and pre-populated items for testing the working memory component.
    """
    
    class Meta:
        model = WorkingMemory
    
    capacity = 7  # Default capacity based on cognitive science (Miller's Law)
    items = factory.LazyAttribute(
        lambda o: MemoryItemFactory.create_batch(
            min(o.capacity, 3),  # Populate with some items, but not at full capacity
            importance=FuzzyFloat(0.7, 1.0),  # Working memory tends to have important items
            relevance=FuzzyFloat(0.7, 1.0),
        )
    )
    
    @classmethod
    def create_empty(cls, **kwargs) -> WorkingMemory:
        """
        Create an empty working memory instance.
        
        Args:
            **kwargs: Additional attributes to set on the created instance
            
        Returns:
            Empty WorkingMemory instance
        """
        return cls.create(items=[], **kwargs)
    
    @classmethod
    def create_full(cls, **kwargs) -> WorkingMemory:
        """
        Create a working memory instance at full capacity.
        
        Args:
            **kwargs: Additional attributes to set on the created instance
            
        Returns:
            WorkingMemory instance at full capacity
        """
        capacity = kwargs.get('capacity', 7)
        return cls.create(
            capacity=capacity,
            items=MemoryItemFactory.create_batch(capacity),
            **kwargs
        )


class EpisodicMemoryFactory(factory.Factory):
    """
    Factory for creating EpisodicMemory instances for testing purposes.
    
    This factory generates episodic memory instances with configurable episodes
    for testing the episodic memory component.
    """
    
    class Meta:
        model = EpisodicMemory
    
    capacity = 100
    episodes = factory.LazyFunction(
        lambda: [
            {
                "id": str(uuid.uuid4()),
                "timestamp": (
                    datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
                ).isoformat(),
                "title": f"Episode {i}",
                "description": f"This is a test episode {i}",
                "items": [
                    MemoryItemFactory.create(
                        item_type=MemoryItemType.EXPERIENCE,
                        created_at=datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
                    ) 
                    for _ in range(random.randint(2, 5))
                ],
                "context": {
                    "location": random.choice(["home", "work", "outside", "travel"]),
                    "participants": random.sample(["user", "friend", "family", "colleague"], 
                                                k=random.randint(1, 3)),
                    "emotional_state": random.choice(["happy", "sad", "neutral", "excited", "anxious"])
                }
            }
            for i in range(random.randint(5, 15))
        ]
    )
    
    @classmethod
    def create_with_time_range(
        cls, start_date: datetime.datetime, end_date: datetime.datetime, count: int = 10, **kwargs
    ) -> EpisodicMemory:
        """
        Create an episodic memory with episodes in a specific time range.
        
        Args:
            start_date: Start date for the episodes
            end_date: End date for the episodes
            count: Number of episodes to create
            **kwargs: Additional attributes to set on the created instance
            
        Returns:
            EpisodicMemory instance with episodes in the specified time range
        """
        if start_date > end_date:
            raise ValueError("start_date must be before end_date")
            
        time_range = (end_date - start_date).total_seconds()
        
        episodes = []
        for i in range(count):
            # Create a timestamp within the range
            random_seconds = random.randint(0, int(time_range))
            timestamp = start_date + datetime.timedelta(seconds=random_seconds)
            
            episode = {
                "id": str(uuid.uuid4()),
                "timestamp": timestamp.isoformat(),
                "title": f"Episode {i} in time range",
                "description": f"Test episode {i} created within specified time range",
                "items": [
                    MemoryItemFactory.create(
                        item_type=MemoryItemType.EXPERIENCE,
                        created_at=timestamp
                    ) 
                    for _ in range(random.randint(2, 5))
                ],
                "context": {
                    "location": random.choice(["home", "work", "outside", "travel"]),
                    "participants": random.sample(["user", "friend", "family", "colleague"], 
                                                k=random.randint(1, 3)),
                    "emotional_state": random.choice(["happy", "sad", "neutral", "excited", "anxious"])
                }
            }
            episodes.append(episode)
            
        return cls.create(episodes=episodes, **kwargs)


class SemanticMemoryFactory(factory.Factory):
    """
    Factory for creating SemanticMemory instances for testing purposes.
    
    This factory generates semantic memory instances with configurable facts and concepts
    for testing the semantic memory component.
    """
    
    class Meta:
        model = SemanticMemory
    
    facts = factory.LazyFunction(
        lambda: {
            f"fact_{i}": {
                "id": str(uuid.uuid4()),
                "content": f"This is test fact {i}",
                "confidence": random.uniform(0.7, 1.0),
                "created_at": (
                    datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))
                ).isoformat(),
                "last_updated": (
                    datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
                ).isoformat(),
                "source": random.choice(["user", "system", "inference", "external"]),
                "related_concepts": random.sample([f"concept_{j}" for j in range(10)], 
                                                k=random.randint(0, 3))
            }
            for i in range(random.randint(10, 30))
        }
    )
    
    concepts = factory.LazyFunction(
        lambda: {
            f"concept_{i}": {
                "id": str(uuid.uuid4()),
                "name": f"Test Concept {i}",
                "description": f"This is a description of test concept {i}",
                "attributes": {
                    f"attr_{j}": f"value_{j}" for j in range(random.randint(2, 5))
                },
                "related_facts": random.sample([f"fact_{j}" for j in range(30)], 
                                            k=random.randint(0, 5)),
                "related_concepts": random.sample([f"concept_{j}" for j in range(10) if j != i], 
                                                k=random.randint(0, 3)),
                "importance": random.uniform(0.0, 1.0)
            }
            for i in range(random.randint(5, 10))
        }
    )
    
    @classmethod
    def create_domain_specific(cls, domain: str, fact_count: int = 10, concept_count: int = 5) -> SemanticMemory:
        """
        Create a semantic memory with domain-specific facts and concepts.
        
        Args:
            domain: The domain to create facts and concepts for (e.g., "science", "history")
            fact_count: Number of facts to create
            concept_count: Number of concepts to create
            
        Returns:
            SemanticMemory instance with domain-specific content
        """
        logger.debug(f"Creating domain-specific semantic memory for domain: {domain}")
        
        # Domain-specific prefixes for more realistic test data
        domain_prefixes = {
            "science": ["The scientific method", "Quantum theory", "Evolution", "Chemistry"],
            "history": ["World War II", "Ancient Rome", "The Renaissance", "Industrial Revolution"],
            "technology": ["Artificial Intelligence", "Blockchain", "Cloud Computing", "Internet of Things"],
            "medicine": ["Cardiovascular system", "Immune response", "Neurological disorders", "Genetics"],
        }
        
        # Use generic prefixes if domain not in our predefined list
        prefixes = domain_prefixes.get(domain, [f"{domain.capitalize()} topic"])
        
        facts = {
            f"{domain}_fact_{i}": {
                "id": str(uuid.uuid4()),
                "content": f"{random.choice(prefixes)} fact {i}: {FuzzyText(length=30).fuzz()}",
                "confidence": random.uniform(0.7, 1.0),
                "created_at": (
                    datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))
                ).isoformat(),
                "last_updated": (
                    datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
                ).isoformat(),
                "source": random.choice(["research", "textbook", "expert", "observation"]),
                "domain": domain,
                "related_concepts": [f"{domain}_concept_{j}" for j in 
                                    random.sample(range(concept_count), min(3, concept_count))]
            }
            for i in range(fact_count)
        }
        
        concepts = {
            f"{domain}_concept_{i}": {
                "id": str(uuid.uuid4()),
                "name": f"{domain.capitalize()} Concept {i}",
                "description": f"{random.choice(prefixes)} concept description {i}",
                "attributes": {
                    f"attr_{j}": f"value_{j}" for j in range(random.randint(2, 5))
                },
                "related_facts": [f"{domain}_fact_{j}" for j in 
                                random.sample(range(fact_count), min(5, fact_count))],
                "related_concepts": [f"{domain}_concept_{j}" for j in 
                                    random.sample(range(concept_count), min(2, concept_count)) if j != i],
                "importance": random.uniform(0.0, 1.0),
                "domain": domain
            }
            for i in range(concept_count)
        }
        
        return cls.create(facts=facts, concepts=concepts)


# Utility functions for creating complex memory test scenarios

def create_memory_system(
    working_memory_capacity: int = 7,
    episodic_memory_capacity: int = 100,
    working_memory_item_count: int = 3,
    episodic_memory_episode_count: int = 10,
    semantic_memory_fact_count: int = 20,
    semantic_memory_concept_count: int = 10
) -> tuple[WorkingMemory, EpisodicMemory, SemanticMemory]:
    """
    Create a complete memory system with all three memory tiers.
    
    This utility function creates a consistent set of working, episodic, and semantic
    memory instances that can be used together in integration tests.
    
    Args:
        working_memory_capacity: Capacity of the working memory
        episodic_memory_capacity: Capacity of the episodic memory
        working_memory_item_count: Number of items in working memory
        episodic_memory_episode_count: Number of episodes in episodic memory
        semantic_memory_fact_count: Number of facts in semantic memory
        semantic_memory_concept_count: Number of concepts in semantic memory
        
    Returns:
        Tuple containing (WorkingMemory, EpisodicMemory, SemanticMemory)
    """
    logger.info("Creating complete memory system for testing")
    
    # Create working memory with specified capacity and item count
    working_memory = WorkingMemoryFactory.create(
        capacity=working_memory_capacity,
        items=MemoryItemFactory.create_batch(
            min(working_memory_capacity, working_memory_item_count)
        )
    )
    
    # Create episodic memory
    episodic_memory = EpisodicMemoryFactory.create(
        capacity=episodic_memory_capacity,
        episodes=[
            {
                "id": str(uuid.uuid4()),
                "timestamp": (
                    datetime.datetime.now() - datetime.timedelta(days=i)
                ).isoformat(),
                "title": f"Test Episode {i}",
                "description": f"This is test episode {i} for integration testing",
                "items": [
                    MemoryItemFactory.create(
                        item_type=MemoryItemType.EXPERIENCE,
                        created_at=datetime.datetime.now() - datetime.timedelta(days=i)
                    ) 
                    for _ in range(random.randint(2, 5))
                ],
                "context": {
                    "location": random.choice(["home", "work", "outside", "travel"]),
                    "participants": random.sample(["user", "friend", "family", "colleague"], 
                                                k=random.randint(1, 3)),
                    "emotional_state": random.choice(["happy", "sad", "neutral", "excited", "anxious"])
                }
            }
            for i in range(episodic_memory_episode_count)
        ]
    )
    
    # Create semantic memory with specified fact and concept counts
    facts = {
        f"fact_{i}": {
            "id": str(uuid.uuid4()),
            "content": f"This is test fact {i} for integration testing",
            "confidence": random.uniform(0.7, 1.0),
            "created_at": (
                datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))
            ).isoformat(),
            "last_updated": (
                datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
            ).isoformat(),
            "source": random.choice(["user", "system", "inference", "external"])
        }
        for i in range(semantic_memory_fact_count)
    }
    
    concepts = {
        f"concept_{i}": {
            "id": str(uuid.uuid4()),
            "name": f"Test Concept {i}",
            "description": f"This is a description of test concept {i} for integration testing",
            "attributes": {
                f"attr_{j}": f"value_{j}" for j in range(random.randint(2, 5))
            },
            "importance": random.uniform(0.0, 1.0)
        }
        for i in range(semantic_memory_concept_count)
    }
    
    # Add relationships between facts and concepts
    for fact_key in facts:
        facts[fact_key]["related_concepts"] = random.sample(
            list(concepts.keys()), k=min(3, len(concepts))
        )
    
    for concept_key in concepts:
        concepts[concept_key]["related_facts"] = random.sample(
            list(facts.keys()), k=min(5, len(facts))
        )
        concepts[concept_key]["related_concepts"] = random.sample(
            [k for k in concepts if k != concept_key], 
            k=min(3, len(concepts) - 1)
        )
    
    semantic_memory = SemanticMemoryFactory.create(
        facts=facts,
        concepts=concepts
    )
    
    return working_memory, episodic_memory, semantic_memory


def create_memory_with_consistent_theme(
    theme: str,
    working_memory_items: int = 3,
    episodic_episodes: int = 5,
    semantic_facts: int = 10,
    semantic_concepts: int = 5
) -> tuple[WorkingMemory, EpisodicMemory, SemanticMemory]:
    """
    Create a memory system with a consistent theme across all memory types.
    
    This function creates memory instances where the content is related to a specific theme,
    useful for testing how the system handles related information across memory tiers.
    
    Args:
        theme: The theme to use for memory content (e.g., "space", "cooking")
        working_memory_items: Number of items in working memory
        episodic_episodes: Number of episodes in episodic memory
        semantic_facts: Number of facts in semantic memory
        semantic_concepts: Number of concepts in semantic memory
        
    Returns:
        Tuple containing (WorkingMemory, EpisodicMemory, SemanticMemory)
    """
    logger.info(f"Creating themed memory system with theme: {theme}")
    
    # Theme-specific content generators
    def themed_content(index: int) -> str:
        themed_templates = [
            f"{theme} is fascinating in aspect {index}",
            f"When exploring {theme}, we discovered {index} important elements",
            f"The relationship between {theme} and factor {index} is significant",
            f"Research on {theme} shows finding {index} has implications",
            f"The history of {theme} reveals pattern {index} consistently"
        ]
        return random.choice(themed_templates)
    
    # Create working memory with themed items
    working_memory = WorkingMemoryFactory.create(
        items=[
            MemoryItemFactory.create(
                content=themed_content(i),
                metadata={"theme": theme}
            )
            for i in range(working_memory_items)
        ]
    )
    
    # Create episodic memory with themed episodes
    themed_episodes = []
    for i in range(episodic_episodes):
        episode_items = [
            MemoryItemFactory.create(
                content=f"{theme} experience {i}.{j}: {FuzzyText(length=20).fuzz()}",
                item_type=MemoryItemType.EXPERIENCE,
                metadata={"theme": theme}
            )
            for j in range(random.randint(2, 4))
        ]
        
        themed_episodes.append({
            "id": str(uuid.uuid4()),
            "timestamp": (
                datetime.datetime.now() - datetime.timedelta(days=i*2)
            ).isoformat(),
            "title": f"{theme.capitalize()} Experience {i}",
            "description": f"An episode related to {theme} with index {i}",
            "items": episode_items,
            "context": {
                "theme": theme,
                "location": random.choice(["home", "work", "outside", "travel"]),
                "emotional_state": random.choice(["interested", "curious", "excited", "focused"])
            }
        })
    
    episodic_memory = EpisodicMemoryFactory.create(episodes=themed_episodes)
    
    # Create semantic memory with themed facts and concepts
    themed_facts = {
        f"{theme}_fact_{i}": {
            "id": str(uuid.uuid4()),
            "content": themed_content(i),
            "confidence": random.uniform(0.7, 1.0),
            "created_at": (
                datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))
            ).isoformat(),
            "theme": theme
        }
        for i in range(semantic_facts)
    }
    
    themed_concepts = {
        f"{theme}_concept_{i}": {
            "id": str(uuid.uuid4()),
            "name": f"{theme.capitalize()} Concept {i}",
            "description": f"A concept related to {theme} with index {i}",
            "attributes": {
                f"{theme}_attr_{j}": f"{theme}_value_{j}" 
                for j in range(random.randint(2, 4))
            },
            "theme": theme
        }
        for i in range(semantic_concepts)
    }
    
    # Add relationships
    for fact_key in themed_facts:
        themed_facts[fact_key]["related_concepts"] = random.sample(
            list(themed_concepts.keys()), k=min(2, len(themed_concepts))
        )
    
    for concept_key in themed_concepts:
        themed_concepts[concept_key]["related_facts"] = random.sample(
            list(themed_facts.keys()), k=min(3, len(themed_facts))
        )
        themed_concepts[concept_key]["related_concepts"] = random.sample(
            [k for k in themed_concepts if k != concept_key], 
            k=min(2, max(0, len(themed_concepts) - 1))
        )
    
    semantic_memory = SemanticMemoryFactory.create(
        facts=themed_facts,
        concepts=themed_concepts
    )
    
    return working_memory, episodic_memory, semantic_memory