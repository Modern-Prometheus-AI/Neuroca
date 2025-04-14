"""
Memory Manager - Primary Interface to Neuroca Memory System

This module provides the recommended entry point to the Neuroca memory system,
with a unified interface for working with all memory tiers (STM, MTM, LTM).

The MemoryManager class handles:
- Memory storage across tiers
- Automatic memory consolidation
- Memory decay and forgetting
- Context-driven memory retrieval
- Working memory buffer management
- Prompt context generation for LLMs

Example usage:
    ```python
    from neuroca.memory.manager import MemoryManager
    
    manager = MemoryManager()
    await manager.initialize()
    
    # Store a memory
    memory_id = await manager.add_memory(
        content="Important information",
        importance=0.8,
        tags=["important"]
    )
    
    # Retrieve memories for context
    context_memories = await manager.get_prompt_context_memories()
    ```

For detailed usage, see src/neuroca/memory/README.md

Note: This module is a facade that provides backward compatibility with the
previous monolithic implementation while delegating to the new modular structure
in the manager/ directory.
"""

from neuroca.memory.manager.core import MemoryManager
from neuroca.memory.manager.models import RankedMemory

# Re-export main classes for backward compatibility
__all__ = ["MemoryManager", "RankedMemory"]
