# Memory System Migration Guide

This guide provides instructions for migrating from the legacy memory system components to the new memory system architecture. The new architecture follows the Apex Modular Organization Standard (AMOS) and provides a more modular, maintainable, and flexible approach.

## Table of Contents

- [Overview](#overview)
- [Migration Strategy](#migration-strategy)
- [Code Migration Examples](#code-migration-examples)
- [Deprecation Timeline](#deprecation-timeline)
- [FAQ](#faq)

## Overview

The memory system refactoring introduces several key changes:

1. **Memory Manager**: A central coordinator for all memory operations across tiers
2. **Tiered Architecture**: Three distinct memory tiers (STM, MTM, LTM) with specialized components
3. **Component-Based Design**: Each tier is composed of specialized components for different aspects of memory management
4. **Storage Backends**: Pluggable backends for different storage mechanisms
5. **Models and Interfaces**: Clearly defined data models and interfaces

The legacy memory system components are now deprecated and will be removed in a future version. This guide will help you migrate your code to the new architecture.

## Migration Strategy

We recommend the following migration strategy:

1. **Adapters First**: Use the provided adapters for backward compatibility
2. **Incremental Migration**: Migrate one component at a time
3. **Test Thoroughly**: Ensure that each migration step is thoroughly tested
4. **Final Cleanup**: Remove the adapters once all client code is migrated

## Code Migration Examples

### Example 1: Creating and Using Memory Components

#### Old Code

```python
import asyncio
from neuroca.memory import create_memory_factory
from neuroca.memory.working_memory import WorkingMemory

async def legacy_example():
    # Create factory
    factory = await create_memory_factory()
    
    # Create memory manager
    manager = await factory.create_memory_manager()
    
    # Create episodic and semantic memory
    episodic = await factory.create_episodic_memory()
    semantic = await factory.create_semantic_memory()
    
    # Create working memory
    working = WorkingMemory(capacity=10)
    
    # Add memories
    episodic_id = await episodic.add_memory("This is an episodic memory")
    semantic_id = await semantic.add_memory("This is a semantic memory")
    
    # Work with working memory
    await working.update_context({"current_task": "example"})
    
    # Clean up
    await factory.shutdown()
```

#### New Code

```python
import asyncio
from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.backends import BackendType

async def new_example():
    # Create memory manager
    memory_manager = MemoryManager(
        backend_type=BackendType.IN_MEMORY,
        config={
            "stm": {"default_ttl": 3600},
            "mtm": {"max_capacity": 1000},
            "ltm": {"maintenance_interval": 86400}
        }
    )
    
    # Initialize the memory manager
    await memory_manager.initialize()
    
    try:
        # Add memories directly to specific tiers
        episodic_id = await memory_manager.add_memory(
            content="This is an episodic memory",
            tags=["episodic"],
            initial_tier="ltm"
        )
        
        semantic_id = await memory_manager.add_memory(
            content="This is a semantic memory",
            tags=["semantic"],
            initial_tier="ltm"
        )
        
        # Update context (replaces working memory functionality)
        await memory_manager.update_context({"current_task": "example"})
        
        # Get prompt context memories
        prompt_memories = await memory_manager.get_prompt_context_memories(max_memories=5)
        
    finally:
        # Clean up
        await memory_manager.shutdown()
```

### Example 2: Memory Consolidation

#### Old Code

```python
import asyncio
from neuroca.memory import create_memory_factory
from neuroca.memory.memory_consolidation import run_consolidation_cycle

async def legacy_consolidation_example():
    # Create factory and memory manager
    factory = await create_memory_factory()
    manager = await factory.create_memory_manager()
    
    # Run consolidation cycle
    results = await run_consolidation_cycle(manager)
    
    print(f"Consolidated STM to MTM: {len(results['stm_to_mtm'])} memories")
    print(f"Consolidated MTM to LTM: {len(results['mtm_to_ltm'])} memories")
    
    # Clean up
    await factory.shutdown()
```

#### New Code

```python
import asyncio
from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.backends import BackendType

async def new_consolidation_example():
    # Create and initialize memory manager
    memory_manager = MemoryManager(backend_type=BackendType.IN_MEMORY)
    await memory_manager.initialize()
    
    try:
        # Run maintenance (includes consolidation)
        results = await memory_manager.run_maintenance()
        
        print(f"Consolidated memories: {results['consolidated_memories']}")
        print(f"STM tier results: {results['tiers']['stm']}")
        print(f"MTM tier results: {results['tiers']['mtm']}")
        print(f"LTM tier results: {results['tiers']['ltm']}")
        
    finally:
        # Clean up
        await memory_manager.shutdown()
```

### Example 3: Memory Decay

#### Old Code

```python
import asyncio
from neuroca.memory import create_memory_factory
from neuroca.memory.memory_decay import run_decay_cycle

async def legacy_decay_example():
    # Create factory and memory manager
    factory = await create_memory_factory()
    manager = await factory.create_memory_manager()
    
    # Run decay cycle
    results = await run_decay_cycle(manager)
    
    print(f"Decayed STM memories: {results['stm']}")
    print(f"Decayed MTM memories: {results['mtm']}")
    
    # Clean up
    await factory.shutdown()
```

#### New Code

```python
import asyncio
from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.backends import BackendType

async def new_decay_example():
    # Create and initialize memory manager
    memory_manager = MemoryManager(backend_type=BackendType.IN_MEMORY)
    await memory_manager.initialize()
    
    try:
        # Run maintenance (includes decay)
        results = await memory_manager.run_maintenance()
        
        # Check tier-specific results
        stm_results = results["tiers"]["stm"]
        mtm_results = results["tiers"]["mtm"]
        
        print(f"STM tier results: {stm_results}")
        print(f"MTM tier results: {mtm_results}")
        
    finally:
        # Clean up
        await memory_manager.shutdown()
```

### Example 4: Working Memory and Context

#### Old Code

```python
import asyncio
from neuroca.memory import create_memory_factory
from neuroca.memory.working_memory import WorkingMemory

async def legacy_working_memory_example():
    # Create factory and memory manager
    factory = await create_memory_factory()
    manager = await factory.create_memory_manager()
    
    # Create working memory
    working = WorkingMemory(capacity=10)
    
    # Update context
    await working.update_context({
        "current_task": "example",
        "user_input": "Hello, world!",
    })
    
    # Get context for prompt
    prompt_context = await working.get_prompt_context(max_items=3)
    
    # Clear context
    await working.clear()
    
    # Clean up
    await factory.shutdown()
```

#### New Code

```python
import asyncio
from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.backends import BackendType

async def new_working_memory_example():
    # Create and initialize memory manager
    memory_manager = MemoryManager(backend_type=BackendType.IN_MEMORY)
    await memory_manager.initialize()
    
    try:
        # Update context
        await memory_manager.update_context({
            "current_task": "example",
            "user_input": "Hello, world!",
        })
        
        # Get context for prompt
        prompt_memories = await memory_manager.get_prompt_context_memories(max_memories=3)
        
        # Clear context
        await memory_manager.clear_context()
        
    finally:
        # Clean up
        await memory_manager.shutdown()
```

## Using the Adapters for Incremental Migration

If you're not ready to fully migrate your code, you can use the provided adapters for backward compatibility:

```python
import asyncio
from neuroca.memory.adapters import (
    create_memory_manager,
    EpisodicMemoryAdapter,
    SemanticMemoryAdapter,
    WorkingMemoryAdapter,
)

async def adapter_example():
    # Create memory manager via adapter
    memory_manager = await create_memory_manager()
    
    # Create adapters
    episodic = EpisodicMemoryAdapter(memory_manager)
    semantic = SemanticMemoryAdapter(memory_manager)
    working = WorkingMemoryAdapter(memory_manager)
    
    # Use legacy interfaces via adapters
    episodic_id = await episodic.add_memory("This is an episodic memory")
    semantic_id = await semantic.add_memory("This is a semantic memory")
    
    await working.update_context({"current_task": "example"})
    
    # Clean up
    await memory_manager.shutdown()
```

## Deprecation Timeline

- **Current**: Legacy components are deprecated with warnings
- **In 3 months**: Legacy components will be removed from the codebase

## FAQ

### Q: Do I need to migrate all my code at once?

A: No, you can migrate incrementally using the adapters for backward compatibility.

### Q: Will the new architecture have the same functionality?

A: Yes, the new architecture provides all the functionality of the legacy system, plus additional capabilities and better organization.

### Q: How do I test my migrated code?

A: We recommend writing tests that verify the behavior of your migrated code matches that of the original code. The memory system test plan provides guidance on testing strategies.

### Q: What if I encounter issues during migration?

A: Consult the memory system documentation, particularly the API documentation and the usage guide. If you still have issues, contact the development team for assistance.
