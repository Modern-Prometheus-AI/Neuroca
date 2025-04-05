# Circular Dependency Resolution in NeuroCognitive Architecture

## Problem Statement

The NeuroCognitive Architecture (NCA) initially suffered from circular dependencies between the memory system factory and the concrete memory implementations. Specifically:

1. `factory.py` needed to import concrete memory implementations (`WorkingMemory`, `EpisodicMemory`, `SemanticMemory`) to register them.
2. The memory implementation files (e.g., `working_memory.py`) needed to import `register_memory_system` from `factory.py` to register themselves.

This circular dependency caused import errors and made the codebase difficult to maintain.

## Solution Architecture

We implemented a solution based on the following architectural patterns:

### 1. Lazy Loading Pattern

Instead of importing and registering memory implementations at module load time, we now use lazy loading to defer imports until they are actually needed:

```python
def _register_default_memory_systems() -> None:
    """Register the default memory system implementations."""
    # Skip if already registered
    if _memory_system_registry:
        return
        
    try:
        # Import memory implementations
        from neuroca.core.memory.working_memory import WorkingMemory
        from neuroca.core.memory.episodic_memory import EpisodicMemory
        from neuroca.core.memory.semantic_memory import SemanticMemory
        
        # Register implementations
        register_memory_implementation("working", WorkingMemory)
        register_memory_implementation("episodic", EpisodicMemory)
        register_memory_implementation("semantic", SemanticMemory)
        
        # Register aliases
        register_memory_implementation("working_memory", WorkingMemory)
        register_memory_implementation("stm", WorkingMemory)
        register_memory_implementation("episodic_memory", EpisodicMemory)
        register_memory_implementation("semantic_memory", SemanticMemory)
        register_memory_implementation("ltm", SemanticMemory)
        
        logger.debug("Registered default memory system implementations")
    except ImportError as e:
        # During development, some implementations might not exist yet
        logger.warning(f"Could not register all memory implementations: {e}")
```

### 2. Centralized Registration

We moved all registration logic to the factory module, eliminating the need for memory implementations to import from the factory:

```python
# Before (in working_memory.py):
from neuroca.core.memory.factory import register_memory_system
# ...
register_memory_system("working_memory", WorkingMemory)
register_memory_system("working", WorkingMemory)
register_memory_system("stm", WorkingMemory)

# After (in factory.py):
def _register_default_memory_systems() -> None:
    # ...
    register_memory_implementation("working", WorkingMemory)
    register_memory_implementation("working_memory", WorkingMemory)
    register_memory_implementation("stm", WorkingMemory)
```

### 3. Just-in-Time Registration

Memory systems are now registered only when they are first requested, ensuring that the registration happens after all modules are fully loaded:

```python
def create_memory_system(memory_type: str, enable_health_monitoring: bool = True,
                        component_id: Optional[str] = None, **config) -> MemorySystem:
    """Create a memory system of the specified type."""
    # Ensure memory implementations are loaded
    _register_default_memory_systems()
    
    # Rest of the function...
```

## Benefits of the Solution

This architectural approach provides several key benefits:

1. **Elimination of Circular Dependencies**: The memory implementation modules no longer need to import from the factory.

2. **Improved Maintainability**: Registration logic is centralized in one place, making it easier to add new memory types.

3. **Lazy Loading**: Memory implementations are only imported when needed, reducing startup time and memory usage.

4. **Graceful Error Handling**: The system can handle missing implementations gracefully, which is useful during development.

5. **Testability**: The architecture is easier to test because components have clearer boundaries.

## Implementation Details

### Factory Module Changes

The factory module now:
- Maintains a registry of memory system implementations
- Provides a function to register implementations
- Lazily loads implementations when needed
- Handles aliases for memory types

### Memory Implementation Changes

The memory implementation modules now:
- Focus solely on implementing the `MemorySystem` interface
- Do not import from the factory module
- Do not register themselves with the factory

## Testing the Solution

We've created comprehensive tests to verify that the new architecture works correctly:

1. **Registry Tests**: Verify that all memory systems are properly registered
2. **Creation Tests**: Ensure that memory systems can be created with different type names
3. **Configuration Tests**: Check that configuration parameters are properly passed to memory systems
4. **Error Handling Tests**: Verify that appropriate errors are raised for invalid memory types

## Conclusion

This architectural solution effectively resolves the circular dependency issue while maintaining the flexibility and extensibility of the factory pattern. The centralized registration approach makes the codebase more maintainable and easier to extend with new memory system implementations in the future. 