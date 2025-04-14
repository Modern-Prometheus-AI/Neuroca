# Neuroca Memory System

## Overview

The Neuroca Memory System implements a multi-tiered, human-inspired memory architecture that supports:
- Short-term memory (STM) for temporary storage
- Medium-term memory (MTM) for intermediate retention
- Long-term memory (LTM) for permanent storage
- Context-aware working memory for prompt/context injection

## Architecture

![Memory System Architecture](../../docs/architecture/diagrams/memory_architecture.png)

The memory system is composed of:

1. **Memory Manager** - Central orchestration of all memory operations (`memory/manager/`)
2. **Storage Backends** - Database implementations for different tiers (`memory/backends/`)
3. **Memory Tiers** - Tier-specific storage implementations (`memory/stm/`, `memory/mtm/`, `memory/ltm/`)
4. **Memory Types** - Semantic, episodic, working memory implementations

## Recommended Usage

### Preferred Interface: MemoryManager

The `MemoryManager` class is the **preferred entry point** and provides a unified interface to the memory system:

```python
from neuroca.memory.manager import MemoryManager

# Initialize the manager
memory_manager = MemoryManager()
await memory_manager.initialize()

# Add a memory
memory_id = await memory_manager.add_memory(
    content="Important information to remember",
    importance=0.8,
    tags=["example", "important"]
)

# Retrieve memory by ID
memory = await memory_manager.retrieve_memory(memory_id)

# Update context to trigger relevant memories
await memory_manager.update_context({
    "current_input": "What was that important information?",
    "current_goal": "Recall important facts"
})

# Get memories for prompt injection
prompt_memories = await memory_manager.get_prompt_context_memories(
    max_memories=3,
    max_tokens_per_memory=100
)

# Search memories
search_results = await memory_manager.search_memories(
    query="important information",
    tags=["important"],
    limit=5
)

# Clean shutdown
await memory_manager.shutdown()
```

### Advanced Usage

For advanced use cases requiring direct access to specific storage tiers:

```python
from neuroca.memory.backends import StorageBackendFactory, MemoryTier, BackendType

# Create specific storage backends
ltm_storage = StorageBackendFactory.create_storage(MemoryTier.LTM, BackendType.SQL)
vector_storage = StorageBackendFactory.create_storage(
    tier=MemoryTier.LTM, 
    backend_type=BackendType.VECTOR, 
    config={"dimension": 768}
)

await ltm_storage.initialize()
await vector_storage.initialize()

# Use the storage directly
memory_id = await ltm_storage.store(memory_item)
```

## Implementation Status

This memory system is under active refactoring to improve modularity, performance, and maintainability. Please refer to [Memory System Refactoring Plan](../../docs/architecture/memory_system_refactoring.md) for details.

### Deprecation Notices

> ⚠️ **Warning**: The following components are considered legacy and will be deprecated in future releases. Please migrate to the MemoryManager interface.

- `memory_consolidation.py`
- `memory_decay.py`
- `memory_retrieval.py`
- Direct usage of tier-specific storage classes

## Best Practices

1. **Use MemoryManager** - Always interact with the memory system through the MemoryManager class
2. **Provide rich metadata** - Include tags, importance scores, and structured content for better retrieval
3. **Update context frequently** - Keep the context updated for relevant memory retrieval
4. **Handle async properly** - The memory system is fully asynchronous
5. **Proper cleanup** - Always call `shutdown()` to clean up resources

## Configuration

Memory system behavior can be configured through the application settings:

```python
# In config.py or similar
SETTINGS = {
    "memory": {
        "stm": {
            "max_items": 1000,
            "default_ttl": 3600,  # seconds
        },
        "mtm": {
            "backend": "redis",
            "cleanup_interval": 3600,  # seconds
        },
        "ltm": {
            "backend": "sql",
            "connection_string": "postgresql://user:pass@localhost/neuroca"
        },
        "vector": {
            "dimension": 768,
            "similarity_threshold": 0.65,
        },
        "consolidation_interval_seconds": 300,
        "decay_interval_seconds": 600,
        "buffer_update_interval_seconds": 60,
    }
}
```

## See Also

- [API Reference](../../docs/api/memory.md)
- [Memory System Architecture](../../docs/architecture/memory_system.md)
- [Memory System Refactoring Plan](../../docs/architecture/memory_system_refactoring.md)
