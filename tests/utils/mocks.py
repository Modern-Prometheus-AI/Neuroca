"""
Mock objects and utilities for testing the NeuroCognitive Architecture (NCA) system.

This module provides a comprehensive set of mock objects, fixtures, and utilities
to facilitate testing across the NeuroCognitive Architecture project. It includes
mocks for memory systems, LLM integrations, health dynamics, and other core components.

Usage:
    from neuroca.tests.utils.mocks import MockMemoryStore, MockLLMProvider
    
    # Use in tests
    memory_store = MockMemoryStore()
    llm_provider = MockLLMProvider(response_template="Test response")
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from unittest.mock import MagicMock, patch

import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class MockMemoryStore:
    """
    Mock implementation of the memory store for testing.
    
    This class simulates the behavior of different memory tiers (working, episodic, semantic)
    without requiring actual database connections or external services.
    
    Attributes:
        working_memory (Dict): Simulated working memory storage
        episodic_memory (Dict): Simulated episodic memory storage
        semantic_memory (Dict): Simulated semantic memory storage
        decay_rate (float): Simulated memory decay rate
    """
    
    def __init__(self, decay_rate: float = 0.1):
        """
        Initialize a mock memory store with empty memory tiers.
        
        Args:
            decay_rate: Simulated rate at which memories decay (0.0-1.0)
        """
        self.working_memory = {}
        self.episodic_memory = {}
        self.semantic_memory = {}
        self.decay_rate = decay_rate
        logger.debug("Initialized MockMemoryStore with decay_rate=%f", decay_rate)
    
    def store_working_memory(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Store an item in working memory with a time-to-live.
        
        Args:
            key: Unique identifier for the memory item
            value: The data to store
            ttl: Time-to-live in seconds (default: 300)
            
        Returns:
            bool: True if storage was successful
        """
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.working_memory[key] = {
            "value": value,
            "expiry": expiry,
            "created_at": datetime.now()
        }
        logger.debug("Stored item in working memory: %s (TTL: %d seconds)", key, ttl)
        return True
    
    def retrieve_working_memory(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from working memory if it exists and hasn't expired.
        
        Args:
            key: The identifier to retrieve
            
        Returns:
            The stored value or None if not found or expired
        """
        if key not in self.working_memory:
            logger.debug("Item not found in working memory: %s", key)
            return None
            
        item = self.working_memory[key]
        if item["expiry"] < datetime.now():
            logger.debug("Item expired in working memory: %s", key)
            del self.working_memory[key]
            return None
            
        logger.debug("Retrieved item from working memory: %s", key)
        return item["value"]
    
    def store_episodic_memory(self, memory: dict[str, Any]) -> str:
        """
        Store an episodic memory.
        
        Args:
            memory: Dictionary containing the episodic memory data
            
        Returns:
            str: Unique ID for the stored memory
        """
        if "id" not in memory:
            memory["id"] = str(uuid.uuid4())
        
        memory["created_at"] = datetime.now()
        memory["salience"] = memory.get("salience", 0.5)  # Default salience
        
        self.episodic_memory[memory["id"]] = memory
        logger.debug("Stored episodic memory with ID: %s", memory["id"])
        return memory["id"]
    
    def retrieve_episodic_memory(self, memory_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve an episodic memory by ID.
        
        Args:
            memory_id: The unique identifier of the memory
            
        Returns:
            Dict or None: The memory if found, None otherwise
        """
        memory = self.episodic_memory.get(memory_id)
        if memory:
            logger.debug("Retrieved episodic memory: %s", memory_id)
            return memory
        
        logger.debug("Episodic memory not found: %s", memory_id)
        return None
    
    def query_episodic_memory(self, query: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        """
        Query episodic memories based on criteria.
        
        Args:
            query: Dictionary of query parameters
            limit: Maximum number of results to return
            
        Returns:
            List of matching memories
        """
        results = []
        
        for memory in self.episodic_memory.values():
            match = True
            for key, value in query.items():
                if key not in memory or memory[key] != value:
                    match = False
                    break
            
            if match:
                results.append(memory)
                if len(results) >= limit:
                    break
        
        logger.debug("Query returned %d episodic memories", len(results))
        return results
    
    def store_semantic_memory(self, concept: str, data: dict[str, Any]) -> bool:
        """
        Store semantic memory for a concept.
        
        Args:
            concept: The concept identifier
            data: The semantic data to store
            
        Returns:
            bool: True if storage was successful
        """
        if concept in self.semantic_memory:
            # Update existing concept
            self.semantic_memory[concept].update(data)
        else:
            # Create new concept
            self.semantic_memory[concept] = data
            
        self.semantic_memory[concept]["updated_at"] = datetime.now()
        logger.debug("Stored semantic memory for concept: %s", concept)
        return True
    
    def retrieve_semantic_memory(self, concept: str) -> Optional[dict[str, Any]]:
        """
        Retrieve semantic memory for a concept.
        
        Args:
            concept: The concept identifier
            
        Returns:
            Dict or None: The semantic data if found, None otherwise
        """
        if concept in self.semantic_memory:
            logger.debug("Retrieved semantic memory for concept: %s", concept)
            return self.semantic_memory[concept]
        
        logger.debug("Semantic memory not found for concept: %s", concept)
        return None
    
    def clear_all(self) -> None:
        """Clear all mock memory stores for testing reset."""
        self.working_memory.clear()
        self.episodic_memory.clear()
        self.semantic_memory.clear()
        logger.debug("Cleared all memory stores")


class MockLLMProvider:
    """
    Mock implementation of an LLM provider for testing.
    
    This class simulates responses from language models without requiring
    actual API calls to external LLM providers.
    
    Attributes:
        response_template (str): Template for generating responses
        delay (float): Simulated response delay in seconds
        failure_rate (float): Probability of simulated failure (0.0-1.0)
        token_usage (Dict): Simulated token usage statistics
    """
    
    def __init__(
        self, 
        response_template: str = "This is a mock response to: {prompt}",
        delay: float = 0.0,
        failure_rate: float = 0.0
    ):
        """
        Initialize a mock LLM provider.
        
        Args:
            response_template: Template string for responses with {prompt} placeholder
            delay: Simulated response delay in seconds
            failure_rate: Probability of simulated failure (0.0-1.0)
        """
        self.response_template = response_template
        self.delay = delay
        self.failure_rate = failure_rate
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.call_history = []
        logger.debug("Initialized MockLLMProvider with failure_rate=%f, delay=%f", 
                    failure_rate, delay)
    
    def generate_response(self, prompt: str, **kwargs) -> dict[str, Any]:
        """
        Generate a mock response to the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters that would be passed to a real LLM
            
        Returns:
            Dict containing the response and metadata
            
        Raises:
            RuntimeError: If the simulated call fails based on failure_rate
        """
        import random
        import time
        
        # Record the call
        self.call_history.append({
            "prompt": prompt,
            "kwargs": kwargs,
            "timestamp": datetime.now()
        })
        
        # Simulate delay
        if self.delay > 0:
            time.sleep(self.delay)
        
        # Simulate failure
        if random.random() < self.failure_rate:
            logger.warning("Simulated LLM API failure")
            raise RuntimeError("Simulated LLM API failure")
        
        # Calculate token usage (simplified estimation)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(self.response_template.format(prompt=prompt).split())
        
        self.token_usage["prompt_tokens"] += prompt_tokens
        self.token_usage["completion_tokens"] += completion_tokens
        self.token_usage["total_tokens"] += prompt_tokens + completion_tokens
        
        response = {
            "text": self.response_template.format(prompt=prompt),
            "model": kwargs.get("model", "mock-model"),
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            },
            "finish_reason": "stop"
        }
        
        logger.debug("Generated mock LLM response for prompt: %s...", prompt[:50])
        return response
    
    def get_embedding(self, text: str) -> list[float]:
        """
        Generate a mock embedding vector for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            List[float]: A mock embedding vector
        """
        # Generate a deterministic but seemingly random embedding based on the text
        seed = sum(ord(c) for c in text)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, 384).tolist()  # 384-dimensional embedding
        
        logger.debug("Generated mock embedding for text: %s...", text[:50])
        return embedding


class MockHealthSystem:
    """
    Mock implementation of the health dynamics system for testing.
    
    This class simulates the biological-inspired health system without requiring
    the full implementation of health dynamics.
    
    Attributes:
        vitals (Dict): Current vital signs
        homeostasis_targets (Dict): Target values for vitals
        history (List): History of vital changes
    """
    
    def __init__(self):
        """Initialize a mock health system with default values."""
        self.vitals = {
            "energy": 100.0,
            "stress": 0.0,
            "fatigue": 0.0,
            "curiosity": 50.0,
            "focus": 100.0
        }
        
        self.homeostasis_targets = {
            "energy": 100.0,
            "stress": 0.0,
            "fatigue": 0.0,
            "curiosity": 50.0,
            "focus": 100.0
        }
        
        self.history = []
        logger.debug("Initialized MockHealthSystem with default vitals")
    
    def update_vital(self, vital: str, value: float) -> bool:
        """
        Update a specific vital sign.
        
        Args:
            vital: The name of the vital to update
            value: The new value
            
        Returns:
            bool: True if update was successful
            
        Raises:
            ValueError: If the vital name is invalid
        """
        if vital not in self.vitals:
            logger.error("Invalid vital name: %s", vital)
            raise ValueError(f"Invalid vital name: {vital}")
        
        old_value = self.vitals[vital]
        self.vitals[vital] = max(0.0, min(100.0, value))  # Clamp between 0-100
        
        self.history.append({
            "vital": vital,
            "old_value": old_value,
            "new_value": self.vitals[vital],
            "timestamp": datetime.now()
        })
        
        logger.debug("Updated vital %s: %.2f -> %.2f", vital, old_value, self.vitals[vital])
        return True
    
    def get_vital(self, vital: str) -> float:
        """
        Get the current value of a vital sign.
        
        Args:
            vital: The name of the vital to retrieve
            
        Returns:
            float: The current value
            
        Raises:
            ValueError: If the vital name is invalid
        """
        if vital not in self.vitals:
            logger.error("Invalid vital name: %s", vital)
            raise ValueError(f"Invalid vital name: {vital}")
        
        return self.vitals[vital]
    
    def simulate_time_passage(self, minutes: int) -> None:
        """
        Simulate the passage of time and its effects on vitals.
        
        Args:
            minutes: Number of minutes to simulate
        """
        # Simple simulation of how vitals change over time
        energy_decay = 0.5 * minutes / 60.0  # Lose 0.5 per hour
        fatigue_increase = 1.0 * minutes / 60.0  # Gain 1.0 per hour
        
        self.update_vital("energy", self.vitals["energy"] - energy_decay)
        self.update_vital("fatigue", self.vitals["fatigue"] + fatigue_increase)
        
        # Simulate homeostasis for other vitals
        for vital in ["stress", "curiosity", "focus"]:
            current = self.vitals[vital]
            target = self.homeostasis_targets[vital]
            adjustment = (target - current) * 0.1 * minutes / 60.0
            self.update_vital(vital, current + adjustment)
        
        logger.debug("Simulated passage of %d minutes", minutes)


class MockEventBus:
    """
    Mock implementation of an event bus for testing.
    
    This class simulates the event publishing and subscription system
    without requiring actual message broker integration.
    
    Attributes:
        subscribers (Dict): Mapping of event types to subscriber callbacks
        published_events (List): History of published events
    """
    
    def __init__(self):
        """Initialize a mock event bus with empty subscribers."""
        self.subscribers = {}
        self.published_events = []
        logger.debug("Initialized MockEventBus")
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        logger.debug("Added subscriber to event type: %s", event_type)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
            
        Returns:
            bool: True if unsubscribed successfully, False otherwise
        """
        if event_type not in self.subscribers:
            logger.warning("Cannot unsubscribe: event type %s has no subscribers", event_type)
            return False
        
        if callback not in self.subscribers[event_type]:
            logger.warning("Cannot unsubscribe: callback not found for event type %s", event_type)
            return False
        
        self.subscribers[event_type].remove(callback)
        logger.debug("Removed subscriber from event type: %s", event_type)
        return True
    
    def publish(self, event_type: str, data: Any = None) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: The type of event to publish
            data: The event data
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now()
        }
        
        self.published_events.append(event)
        
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error("Error in event subscriber callback: %s", str(e))
        
        logger.debug("Published event of type: %s", event_type)
    
    def get_published_events(self, event_type: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Get history of published events, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by
            
        Returns:
            List of published events
        """
        if event_type is None:
            return self.published_events
        
        return [e for e in self.published_events if e["type"] == event_type]


# Utility functions for creating mock objects

def create_mock_context(
    memory_store: Optional[MockMemoryStore] = None,
    llm_provider: Optional[MockLLMProvider] = None,
    health_system: Optional[MockHealthSystem] = None,
    event_bus: Optional[MockEventBus] = None
) -> dict[str, Any]:
    """
    Create a complete mock context for testing components.
    
    Args:
        memory_store: Optional custom memory store mock
        llm_provider: Optional custom LLM provider mock
        health_system: Optional custom health system mock
        event_bus: Optional custom event bus mock
        
    Returns:
        Dict containing all mock components
    """
    context = {
        "memory_store": memory_store or MockMemoryStore(),
        "llm_provider": llm_provider or MockLLMProvider(),
        "health_system": health_system or MockHealthSystem(),
        "event_bus": event_bus or MockEventBus(),
        "created_at": datetime.now()
    }
    
    logger.debug("Created mock context with %d components", len(context))
    return context


def patch_dependencies(target_module: str) -> dict[str, MagicMock]:
    """
    Create and apply patches for common dependencies in a module.
    
    Args:
        target_module: The module path to patch
        
    Returns:
        Dict of patchers that can be used in a with statement or as decorators
    """
    patchers = {
        "memory_store": patch(f"{target_module}.MemoryStore", MockMemoryStore),
        "llm_provider": patch(f"{target_module}.LLMProvider", MockLLMProvider),
        "health_system": patch(f"{target_module}.HealthSystem", MockHealthSystem),
        "event_bus": patch(f"{target_module}.EventBus", MockEventBus),
    }
    
    logger.debug("Created dependency patchers for module: %s", target_module)
    return patchers