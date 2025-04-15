# Legacy to New Memory System Mapping

**Last Updated:** April 14, 2025

This document provides a comprehensive mapping between the legacy memory system components and their replacements in the new architecture. Use this as a reference to understand how functionality has been migrated to the new system.

## Directory Structure Mapping

| Legacy Path | New Path | Notes |
|-------------|----------|-------|
| `src/neuroca/memory/ltm/` | `src/neuroca/memory/tiers/ltm/` | LTM functionality is now organized into modular components |
| `src/neuroca/memory/mtm/` | `src/neuroca/memory/tiers/mtm/` | MTM functionality is now organized into modular components |
| `src/neuroca/memory/stm/` | `src/neuroca/memory/tiers/stm/` | STM functionality is now organized into modular components |
| N/A | `src/neuroca/memory/tiers/base/` | New shared base functionality across tiers |
| N/A | `src/neuroca/memory/backends/` | New storage backends (previously embedded in tier implementations) |
| N/A | `src/neuroca/memory/interfaces/` | New explicit interface definitions |

## File and Class Mapping

### Core Files

| Legacy File/Class | New File/Class | Notes |
|-------------------|----------------|-------|
| `src/neuroca/memory/manager.py` | `src/neuroca/memory/manager/memory_manager.py` | Centralized memory management |
| `src/neuroca/memory/factory.py` | `src/neuroca/memory/backends/factory/storage_factory.py` | Factory pattern for backends |
| `src/neuroca/memory/episodic_memory.py` | `src/neuroca/memory/tiers/ltm/core.py` + `relationship.py` | Episodic functionality moved to LTM tier |
| `src/neuroca/memory/semantic_memory.py` | `src/neuroca/memory/tiers/ltm/core.py` + `category.py` | Semantic functionality moved to LTM tier |
| `src/neuroca/memory/consolidation.py` | `src/neuroca/memory/tiers/mtm/components/consolidation.py` | Consolidation logic in MTM tier |
| `src/neuroca/memory/memory_consolidation.py` | `src/neuroca/memory/manager/memory_manager.py` (methods) | Cross-tier consolidation in manager |
| `src/neuroca/memory/memory_decay.py` | Tier-specific components: `strength.py` | Decay logic moved to tier-specific strength components |
| `src/neuroca/memory/memory_retrieval.py` | `src/neuroca/memory/manager/memory_manager.py` (retrieval methods) | Retrieval now managed centrally |
| `src/neuroca/memory/working_memory.py` | `src/neuroca/memory/models/working_memory.py` | Working memory model plus manager methods |

### LTM Components

| Legacy File/Class | New File/Class | Notes |
|-------------------|----------------|-------|
| `src/neuroca/memory/ltm/operations.py` | `src/neuroca/memory/tiers/ltm/components/operations.py` | Core LTM operations |
| `src/neuroca/memory/ltm/manager.py` | `src/neuroca/memory/tiers/ltm/core.py` | LTM tier management |
| `src/neuroca/memory/ltm/storage.py` | `src/neuroca/memory/backends/` | Storage functionality extracted to separate backends |
| `src/neuroca/memory/ltm/models.py` | `src/neuroca/memory/models/memory_item.py` | Unified memory models |
| N/A | `src/neuroca/memory/tiers/ltm/components/lifecycle.py` | New component for initialization/shutdown |
| N/A | `src/neuroca/memory/tiers/ltm/components/relationship.py` | New component for memory relationships |
| N/A | `src/neuroca/memory/tiers/ltm/components/category.py` | New component for memory categorization |
| N/A | `src/neuroca/memory/tiers/ltm/components/maintenance.py` | New component for system maintenance |
| N/A | `src/neuroca/memory/tiers/ltm/components/strength.py` | New component for memory strength calculation |

### MTM Components

| Legacy File/Class | New File/Class | Notes |
|-------------------|----------------|-------|
| `src/neuroca/memory/mtm/operations.py` | `src/neuroca/memory/tiers/mtm/components/operations.py` | Core MTM operations |
| `src/neuroca/memory/mtm/manager.py` | `src/neuroca/memory/tiers/mtm/core.py` | MTM tier management |
| `src/neuroca/memory/mtm/storage.py` | `src/neuroca/memory/backends/` | Storage functionality extracted to separate backends |
| N/A | `src/neuroca/memory/tiers/mtm/components/lifecycle.py` | New component for initialization/shutdown |
| N/A | `src/neuroca/memory/tiers/mtm/components/priority.py` | New component for memory prioritization |
| N/A | `src/neuroca/memory/tiers/mtm/components/consolidation.py` | New component for consolidation logic |
| N/A | `src/neuroca/memory/tiers/mtm/components/strength.py` | New component for memory strength calculation |
| N/A | `src/neuroca/memory/tiers/mtm/components/promotion.py` | New component for promoting to LTM |

### STM Components

| Legacy File/Class | New File/Class | Notes |
|-------------------|----------------|-------|
| `src/neuroca/memory/stm/operations.py` | `src/neuroca/memory/tiers/stm/components/operations.py` | Core STM operations |
| `src/neuroca/memory/stm/manager.py` | `src/neuroca/memory/tiers/stm/core.py` | STM tier management |
| `src/neuroca/memory/stm/storage.py` | `src/neuroca/memory/backends/` | Storage functionality extracted to separate backends |
| N/A | `src/neuroca/memory/tiers/stm/components/lifecycle.py` | New component for initialization/shutdown |
| N/A | `src/neuroca/memory/tiers/stm/components/expiry.py` | New component for memory expiration |
| N/A | `src/neuroca/memory/tiers/stm/components/cleanup.py` | New component for cleanup processes |
| N/A | `src/neuroca/memory/tiers/stm/components/strength.py` | New component for memory strength calculation |

## Function Mapping

### Memory Operations

| Legacy Function | New Function/Method | Location |
|-----------------|---------------------|----------|
| `ltm.operations.store_memory()` | `MemoryManager.add_memory_to_ltm()` | `src/neuroca/memory/manager/memory_manager.py` |
| `ltm.operations.retrieve_memory()` | `MemoryManager.get_memory()` | `src/neuroca/memory/manager/memory_manager.py` |
| `ltm.operations.search_memories()` | `MemoryManager.search_memories()` | `src/neuroca/memory/manager/memory_manager.py` |
| `ltm.operations.create_association()` | `LTMTier.create_relationship()` | `src/neuroca/memory/tiers/ltm/components/relationship.py` |
| `ltm.operations.get_associations()` | `LTMTier.get_relationships()` | `src/neuroca/memory/tiers/ltm/components/relationship.py` |
| `mtm.operations.store_memory()` | `MemoryManager.add_memory_to_mtm()` | `src/neuroca/memory/manager/memory_manager.py` |
| `mtm.operations.promote_to_ltm()` | `MTMTier.promote_memory()` | `src/neuroca/memory/tiers/mtm/components/promotion.py` |
| `stm.operations.create_memory()` | `MemoryManager.add_memory_to_stm()` | `src/neuroca/memory/manager/memory_manager.py` |
| `memory_consolidation.consolidate_memory()` | `MemoryManager.consolidate_memory()` | `src/neuroca/memory/manager/memory_manager.py` |
| `memory_decay.decay_memory()` | `Tier-specific.decay_memory()` | `src/neuroca/memory/tiers/*/components/strength.py` |

### Models and Data Structures

| Legacy Model | New Model | Location |
|--------------|-----------|----------|
| `ltm.models.LTMEntry` | `MemoryItem` | `src/neuroca/memory/models/memory_item.py` |
| `mtm.models.MTMEntry` | `MemoryItem` | `src/neuroca/memory/models/memory_item.py` |
| `stm.models.STMEntry` | `MemoryItem` | `src/neuroca/memory/models/memory_item.py` |
| `ltm.models.MemoryMetadata` | `MemoryMetadata` | `src/neuroca/memory/models/memory_item.py` |
| `stm.models.STMCapacityExceededError` | `MemoryTierCapacityError` | `src/neuroca/memory/exceptions.py` |
| `working_memory.WorkingMemoryItem` | `WorkingMemoryItem` | `src/neuroca/memory/models/working_memory.py` |

## Key Architectural Changes

1. **Modular Component Architecture**: Each memory tier is now implemented as a collection of focused, single-responsibility components rather than monolithic classes.
   
2. **Storage Backend Separation**: Storage functionality is extracted into separate backend implementations that can be swapped without changing tier logic.
   
3. **Interface-Driven Design**: Explicit interfaces define contracts between components, improving maintainability.
   
4. **Unified Memory Manager**: A single centralized MemoryManager coordinates operations across memory tiers.
   
5. **Consistent Memory Model**: All tiers now use a unified MemoryItem model with tier-specific behavior implemented in the tier components.
   
6. **Explicit Lifecycle Management**: Components have clear initialization and shutdown processes.
   
7. **Improved Exception Handling**: Comprehensive exception hierarchy for precise error handling.

## Usage Example Comparison

### Legacy Usage

```python
from neuroca.memory.ltm.operations import store_memory, retrieve_memory
from neuroca.memory.mtm.operations import promote_to_ltm
from neuroca.memory.memory_consolidation import consolidate_memory

# Store in LTM
memory_id = store_memory("Important information", importance=0.8)

# Retrieve from LTM
memory = retrieve_memory(memory_id)

# Store in MTM and promote
mtm_id = store_memory("To be consolidated")
consolidated_id = promote_to_ltm(mtm_id)

# Manual consolidation
consolidate_memory(memory_id)
```

### New Usage

```python
from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.models.memory_item import MemoryItem

# Initialize memory manager
memory_manager = MemoryManager()
await memory_manager.initialize()

# Create memory item
memory_item = MemoryItem(
    content="Important information",
    metadata={"importance": 0.8}
)

# Store directly in LTM
ltm_id = await memory_manager.add_memory_to_ltm(memory_item)

# Retrieve from any tier (manager routes to correct tier)
retrieved_memory = await memory_manager.get_memory(ltm_id)

# Add to MTM with auto-promotion option
mtm_id = await memory_manager.add_memory_to_mtm(
    MemoryItem(content="To be consolidated"),
    auto_promote=True
)

# Run consolidation cycle
await memory_manager.consolidate_memories()
