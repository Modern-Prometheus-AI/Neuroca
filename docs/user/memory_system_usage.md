# Memory System Usage Guide

This guide provides examples of how to use the Neuroca memory system. The memory system is designed with a tiered architecture, following a cognitive model that includes Short-Term Memory (STM), Medium-Term Memory (MTM), and Long-Term Memory (LTM) tiers.

## Table of Contents

- [System Overview](#system-overview)
- [Getting Started](#getting-started)
- [Basic Operations](#basic-operations)
- [Memory Lifecycle](#memory-lifecycle)
- [Context-Aware Memory Retrieval](#context-aware-memory-retrieval)
- [Advanced Features](#advanced-features)
- [Configuration Options](#configuration-options)

## System Overview

The Neuroca memory system implements a cognitively-inspired memory architecture with three tiers:

1. **Short-Term Memory (STM)**: Temporary storage with a limited lifespan. Memories in STM automatically expire after a configurable time-to-live (TTL).

2. **Medium-Term Memory (MTM)**: Intermediate storage with priority-based management. Memories are organized by priority and importance, with automatic consolidation.

3. **Long-Term Memory (LTM)**: Permanent storage with semantic relationships and organization. Memories in LTM can be categorized and connected through relationships.

These tiers are coordinated by the **Memory Manager**, which provides a unified API for the entire system. The Memory Manager handles cross-tier operations, context-aware memory retrieval, and memory lifecycle management.

## Getting Started

### Installation

The memory system is part of the Neuroca package. No separate installation is needed.

### Initialization

To use the memory system, you need to create and initialize a Memory Manager instance:

```python
import asyncio
from neuroca.memory.backends import BackendType
from neuroca.memory.manager.memory_manager import MemoryManager

async def init_memory_system():
    # Create a Memory Manager with in-memory backend
    memory_manager = MemoryManager(
        config={
            "stm": {
                "default_ttl": 3600,  # 1 hour TTL for STM memories
                "max_capacity": 100,
            },
            "mtm": {
                "max_capacity": 1000,
                "consolidation_interval": 7200,  # 2 hours
            },
            "ltm": {
                "maintenance_interval": 86400,  # 24 hours
            }
        },
        backend_type=BackendType.IN_MEMORY
    )
    
    # Initialize the memory system
    await memory_manager.initialize()
    
    return memory_manager

# Create and initialize memory manager
memory_manager = asyncio.run(init_memory_system())
```

### Shutdown

When you're done using the memory system, it's important to properly shut it down:

```python
async def shutdown_memory_system(memory_manager):
    await memory_manager.shutdown()

# Shutdown memory manager
asyncio.run(shutdown_memory_system(memory_manager))
```

## Basic Operations

### Adding Memories

You can add memories to the system using the `add_memory` method:

```python
async def add_memory_example(memory_manager):
    # Add a simple text memory to STM
    memory_id = await memory_manager.add_memory(
        content="This is a test memory",
        summary="Test memory",
        importance=0.7,
        tags=["test", "example"],
        initial_tier="stm"  # Optional, defaults to STM
    )
    
    print(f"Added memory with ID: {memory_id}")
    
    # Add a structured data memory
    structured_memory_id = await memory_manager.add_memory(
        content={
            "name": "John Doe",
            "email": "john@example.com",
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        },
        summary="User profile",
        importance=0.9,
        tags=["user", "profile"],
        initial_tier="ltm"  # Store directly in LTM
    )
    
    print(f"Added structured memory with ID: {structured_memory_id}")
```

### Retrieving Memories

You can retrieve memories by ID:

```python
async def retrieve_memory_example(memory_manager, memory_id):
    # Retrieve a memory
    memory = await memory_manager.retrieve_memory(memory_id)
    
    if memory:
        print(f"Memory content: {memory['content']['text'] or memory['content']['data']}")
        print(f"Memory importance: {memory['metadata']['importance']}")
    else:
        print(f"Memory {memory_id} not found")
```

### Updating Memories

You can update existing memories:

```python
async def update_memory_example(memory_manager, memory_id):
    # Update a memory
    success = await memory_manager.update_memory(
        memory_id=memory_id,
        content="Updated content",
        importance=0.8,
        tags=["updated", "example"]
    )
    
    if success:
        print(f"Memory {memory_id} updated successfully")
    else:
        print(f"Failed to update memory {memory_id}")
```

### Deleting Memories

You can delete memories by ID:

```python
async def delete_memory_example(memory_manager, memory_id):
    # Delete a memory
    success = await memory_manager.delete_memory(memory_id)
    
    if success:
        print(f"Memory {memory_id} deleted successfully")
    else:
        print(f"Failed to delete memory {memory_id}")
```

### Searching Memories

You can search for memories based on various criteria:

```python
async def search_memories_example(memory_manager):
    # Search memories by text query
    text_results = await memory_manager.search_memories(
        query="test memory",
        limit=5,
        min_relevance=0.3
    )
    
    print(f"Found {len(text_results)} memories by text search")
    
    # Search memories by tags
    tag_results = await memory_manager.search_memories(
        tags=["example"],
        limit=10
    )
    
    print(f"Found {len(tag_results)} memories with tag 'example'")
    
    # Search with metadata filters
    metadata_results = await memory_manager.search_memories(
        metadata_filters={
            "metadata.importance": {"$gt": 0.7}  # Memories with importance > 0.7
        },
        limit=10
    )
    
    print(f"Found {len(metadata_results)} important memories")
    
    # Search in specific tiers
    ltm_results = await memory_manager.search_memories(
        query="user profile",
        tiers=["ltm"],
        limit=5
    )
    
    print(f"Found {len(ltm_results)} memories in LTM")
```

## Memory Lifecycle

### Strengthening Memories

You can strengthen memories to make them less likely to be forgotten:

```python
async def strengthen_memory_example(memory_manager, memory_id):
    # Strengthen a memory
    success = await memory_manager.strengthen_memory(
        memory_id=memory_id,
        strengthen_amount=0.2
    )
    
    if success:
        print(f"Memory {memory_id} strengthened successfully")
    else:
        print(f"Failed to strengthen memory {memory_id}")
```

### Decaying Memories

You can explicitly decay memories:

```python
async def decay_memory_example(memory_manager, memory_id):
    # Decay a memory
    success = await memory_manager.decay_memory(
        memory_id=memory_id,
        decay_amount=0.1
    )
    
    if success:
        print(f"Memory {memory_id} decayed successfully")
    else:
        print(f"Failed to decay memory {memory_id}")
```

### Consolidating Memories

You can explicitly consolidate memories between tiers:

```python
async def consolidate_memory_example(memory_manager, memory_id):
    # Consolidate a memory from STM to MTM
    new_id = await memory_manager.consolidate_memory(
        memory_id=memory_id,
        source_tier="stm",
        target_tier="mtm",
        additional_metadata={
            "consolidated": True,
            "consolidation_timestamp": time.time()
        }
    )
    
    if new_id:
        print(f"Memory consolidated to MTM with new ID: {new_id}")
    else:
        print(f"Failed to consolidate memory {memory_id}")
```

## Context-Aware Memory Retrieval

### Updating Context

You can update the current context to trigger relevant memory retrieval:

```python
async def update_context_example(memory_manager):
    # Update context with current conversation
    await memory_manager.update_context({
        "text": "Let's discuss the project timeline for the new feature.",
        "topic": "project planning",
        "participants": ["user", "assistant"]
    })
    
    print("Context updated")
```

### Getting Memories for Prompt Context

You can get the most relevant memories for inclusion in the agent's prompt:

```python
async def get_prompt_memories_example(memory_manager):
    # Get memories for prompt context
    prompt_memories = await memory_manager.get_prompt_context_memories(
        max_memories=3,
        max_tokens_per_memory=100
    )
    
    print(f"Retrieved {len(prompt_memories)} memories for prompt context")
    
    for i, memory in enumerate(prompt_memories):
        print(f"Memory {i+1}:")
        print(f"  Content: {memory['content']}")
        print(f"  Relevance: {memory['relevance']}")
        print(f"  Tier: {memory['tier']}")
```

### Clearing Context

You can clear the current context:

```python
async def clear_context_example(memory_manager):
    # Clear context
    await memory_manager.clear_context()
    
    print("Context cleared")
```

## Advanced Features

### LTM-Specific Features

#### Categories

LTM memories can be organized into categories:

```python
async def ltm_category_example(memory_manager, memory_id):
    # Get the LTM tier directly (for tier-specific operations)
    ltm_tier = memory_manager._ltm
    
    # Add a memory to a category
    success = await ltm_tier.add_to_category(memory_id, "important")
    
    if success:
        print(f"Memory {memory_id} added to category 'important'")
    
    # Get memories in a category
    category_memories = await ltm_tier.get_memories_by_category("important", limit=5)
    
    print(f"Found {len(category_memories)} memories in category 'important'")
    
    # Get all categories
    categories = await ltm_tier.get_all_categories()
    
    print(f"Available categories: {list(categories.keys())}")
```

#### Relationships

LTM memories can be connected through relationships:

```python
async def ltm_relationship_example(memory_manager, source_id, target_id):
    # Get the LTM tier directly (for tier-specific operations)
    ltm_tier = memory_manager._ltm
    
    # Add a relationship between two memories
    success = await ltm_tier.add_relationship(
        source_id=source_id,
        target_id=target_id,
        relationship_type="causal",
        strength=0.8,
        bidirectional=True
    )
    
    if success:
        print(f"Relationship added between {source_id} and {target_id}")
    
    # Get related memories
    related_memories = await ltm_tier.get_related_memories(
        memory_id=source_id,
        relationship_type="causal",
        min_strength=0.5,
        limit=5
    )
    
    print(f"Found {len(related_memories)} related memories")
    
    # Get relationship types
    relationship_types = await ltm_tier.get_relationship_types()
    
    print(f"Available relationship types: {list(relationship_types.keys())}")
```

### System Maintenance

You can run maintenance tasks on the memory system:

```python
async def run_maintenance_example(memory_manager):
    # Run maintenance
    results = await memory_manager.run_maintenance()
    
    print(f"Maintenance completed:")
    print(f"  Consolidated memories: {results['consolidated_memories']}")
    
    for tier, tier_results in results["tiers"].items():
        print(f"  {tier.upper()} tier:")
        for key, value in tier_results.items():
            print(f"    {key}: {value}")
```

### System Statistics

You can get statistics about the memory system:

```python
async def get_system_stats_example(memory_manager):
    # Get system stats
    stats = await memory_manager.get_system_stats()
    
    print(f"Memory system statistics:")
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  Working memory size: {stats['working_memory']['size']}")
    
    for tier, tier_stats in stats["tiers"].items():
        print(f"  {tier.upper()} tier:")
        for key, value in tier_stats.items():
            print(f"    {key}: {value}")
```

## Configuration Options

### General Configuration

```python
config = {
    "maintenance_interval": 3600,  # 1 hour global maintenance interval
}
```

### STM Configuration

```python
stm_config = {
    "default_ttl": 3600,  # 1 hour TTL for STM memories
    "max_capacity": 100,  # Maximum number of memories in STM
    "cleanup_interval": 300,  # Clean up expired memories every 5 minutes
}
```

### MTM Configuration

```python
mtm_config = {
    "max_capacity": 1000,  # Maximum number of memories in MTM
    "consolidation_interval": 7200,  # Consolidate memories every 2 hours
    "priority_levels": {"high": 3, "medium": 2, "low": 1},  # Priority levels
    "min_access_threshold": 3,  # Minimum access count for priority upgrade
}
```

### LTM Configuration

```python
ltm_config = {
    "maintenance_interval": 86400,  # Run maintenance every 24 hours
    "relationship_types": {
        "semantic": "Semantic relationship based on content similarity",
        "causal": "One memory caused or led to another",
        "temporal": "Memories occurred close in time",
        "spatial": "Memories occurred in the same location",
        "associative": "Memories are associated through shared context",
    }
}
```

## Complete Example

Here's a complete example that demonstrates using the memory system:

```python
import asyncio
import time
from neuroca.memory.backends import BackendType
from neuroca.memory.manager.memory_manager import MemoryManager

async def memory_system_example():
    # Create and initialize memory manager
    memory_manager = MemoryManager(
        config={
            "stm": {"default_ttl": 3600},
            "mtm": {"max_capacity": 1000},
            "ltm": {"maintenance_interval": 86400}
        },
        backend_type=BackendType.IN_MEMORY
    )
    
    await memory_manager.initialize()
    
    try:
        # Add memories
        stm_memory_id = await memory_manager.add_memory(
            content="Short-term information that will expire soon",
            summary="STM test",
            importance=0.5,
            tags=["test", "stm"],
            initial_tier="stm"
        )
        
        mtm_memory_id = await memory_manager.add_memory(
            content="Medium-term information that's somewhat important",
            summary="MTM test",
            importance=0.7,
            tags=["test", "mtm"],
            initial_tier="mtm"
        )
        
        ltm_memory_id = await memory_manager.add_memory(
            content="Long-term information that's very important",
            summary="LTM test",
            importance=0.9,
            tags=["test", "ltm"],
            initial_tier="ltm"
        )
        
        # Set up a relationship between MTM and LTM memories
        ltm_tier = memory_manager._ltm
        await ltm_tier.add_relationship(
            source_id=ltm_memory_id,
            target_id=mtm_memory_id,
            relationship_type="associative",
            strength=0.8
        )
        
        # Update context
        await memory_manager.update_context({
            "text": "Testing the memory system with various tiers",
            "topic": "memory testing"
        })
        
        # Get memories for prompt context
        prompt_memories = await memory_manager.get_prompt_context_memories(
            max_memories=3,
            max_tokens_per_memory=100
        )
        
        print(f"Memories for prompt context:")
        for memory in prompt_memories:
            print(f"  {memory['id']} - {memory['content'][:30]}... (relevance: {memory['relevance']:.2f})")
        
        # Run maintenance
        await memory_manager.run_maintenance()
        
        # Get system stats
        stats = await memory_manager.get_system_stats()
        print(f"Memory system statistics:")
        print(f"  Total memories: {stats['total_memories']}")
    
    finally:
        # Always shutdown properly
        await memory_manager.shutdown()

# Run the example
asyncio.run(memory_system_example())
```

This usage guide provides a starting point for working with the Neuroca memory system. For more details, refer to the API documentation and other guides in the documentation.
