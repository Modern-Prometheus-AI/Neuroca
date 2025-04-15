"""
Memory System Adapters

This package provides adapters for legacy memory components to use the new
memory system architecture. These adapters delegate to the Memory Manager and
tier-specific components.

These adapters are provided for backward compatibility during migration
and will be removed in a future version.
"""

import warnings

# Import adapters for easy access
from neuroca.memory.adapters.episodic_memory_adapter import EpisodicMemoryAdapter
from neuroca.memory.adapters.semantic_memory_adapter import SemanticMemoryAdapter
from neuroca.memory.adapters.working_memory_adapter import WorkingMemoryAdapter
from neuroca.memory.adapters.memory_factory_adapter import (
    MemoryFactoryAdapter,
    create_memory_factory,
    create_memory_manager,
)

# Import legacy functions
from neuroca.memory.adapters.memory_consolidation_adapter import (
    consolidate_memory,
    auto_consolidate_stm_to_mtm,
    auto_consolidate_mtm_to_ltm,
    run_consolidation_cycle,
)
from neuroca.memory.adapters.memory_decay_adapter import (
    decay_memory,
    decay_memories_by_age,
    decay_memories_by_criteria,
    run_decay_cycle,
)

# Import storage adapters
from neuroca.memory.adapters.storage_adapters import (
    LegacyLTMStorageAdapter,
    LegacySTMStorageAdapter,
    LegacyMTMStorageAdapter,
    store_memory,
    retrieve_memory,
    update_memory,
    delete_memory,
    search_memories,
)

# Show global deprecation warning
warnings.warn(
    "The neuroca.memory.adapters module is deprecated and will be removed in a future version. "
    "Use the new memory system components directly instead.",
    DeprecationWarning,
    stacklevel=2
)
