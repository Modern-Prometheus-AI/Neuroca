# Memory System Directory Structure

**Last Updated:** April 14, 2025

This document defines the directory structure for the Neuroca memory system as part of the refactoring effort. This structure ensures clean separation of concerns, logical organization, and adherence to the AMOS guidelines.

## Overview

The memory system code will be organized into the following primary directories:

```
src/neuroca/memory/
├── interfaces/       # Interfaces for all components
├── models/           # Data models shared across components
├── backends/         # Storage backend implementations
├── tiers/            # Memory tier implementations
├── manager/          # Memory manager implementation
├── utils/            # Utility functions and helpers
├── exceptions.py     # Exception hierarchy
├── constants.py      # Shared constants and enums
├── config.py         # Configuration management
└── README.md         # System documentation
```

## Detailed Structure

### Interfaces (`interfaces/`)

Defines the contracts for all components of the memory system.

```
interfaces/
├── __init__.py                # Exports all interfaces
├── storage_backend.py         # StorageBackendInterface
├── memory_tier.py             # MemoryTierInterface
└── memory_manager.py          # MemoryManagerInterface
```

### Models (`models/`)

Contains data models used throughout the memory system.

```
models/
├── __init__.py                # Exports all models
├── memory_item.py             # Core memory item models
├── search.py                  # Search-related models
└── working_memory.py          # Working memory models
```

### Backends (`backends/`)

Implements specific storage technologies.

```
backends/
├── __init__.py                # Exports backend classes
├── factory.py                 # StorageBackendFactory
├── base.py                    # Base implementation
├── in_memory_backend.py       # Simple in-memory implementation
├── redis_backend.py           # Redis implementation
├── sql_backend.py             # SQL database implementation
└── vector_backend.py          # Vector database implementation
```

### Tiers (`tiers/`)

Implements the memory tiers with tier-specific behaviors.

```
tiers/
├── __init__.py                # Exports tier classes
├── factory.py                 # MemoryTierFactory
├── base.py                    # Base tier implementation
├── stm.py                     # Short-term memory implementation
├── mtm.py                     # Medium-term memory implementation
└── ltm.py                     # Long-term memory implementation
```

### Manager (`manager/`)

Implements the memory manager as the central coordination component.

```
manager/
├── __init__.py                # Exports manager classes
├── core.py                    # Main MemoryManager implementation
├── consolidation.py           # Memory consolidation logic
├── decay.py                   # Memory decay logic
├── working_memory.py          # Working memory management
└── utils.py                   # Manager-specific utilities
```

### Utils (`utils/`)

Contains utility functions and helpers.

```
utils/
├── __init__.py                # Exports utility functions
├── embedding.py               # Text embedding utilities
├── text_processing.py         # Text processing functions
├── relevance.py               # Relevance calculation functions
└── serialization.py           # Serialization utilities
```

## File Naming and Organization Conventions

1. **Interfaces** should be named with the suffix `Interface` (e.g., `StorageBackendInterface`).
2. **Implementations** should be named after what they implement (e.g., `RedisBackend`).
3. **Factory classes** should be named with the suffix `Factory` (e.g., `StorageBackendFactory`).
4. **Utility functions** should be grouped by functionality in appropriately named modules.
5. **Test files** should mirror the structure of the implementation files with a `test_` prefix.

## Test Structure

Tests will mirror the implementation structure under the `tests/` directory:

```
tests/unit/memory/
├── interfaces/             # Tests for interface contracts
├── models/                 # Tests for data models
├── backends/               # Tests for storage backends
├── tiers/                  # Tests for memory tiers
├── manager/                # Tests for memory manager
└── utils/                  # Tests for utilities

tests/integration/memory/
├── backends/               # Integration tests for backends
├── tiers/                  # Integration tests for tiers
└── manager/                # Integration tests for manager
```

## Implementation Approach

1. **Interfaces First**: Implement and stabilize all interfaces before implementation
2. **Bottom-Up**: Implement in this order:
   - Storage backends
   - Memory tiers
   - Memory manager
3. **Test-Driven**: Write tests before implementation

## Notes

- Keep files under 500 lines per AMOS guidelines (AMOS-ORG-2)
- Follow modular design principles (AMOS-MOD-1)
- Ensure clear separation of concerns (AMOS-STRUCT-1)
- Define clean interfaces between components (AMOS-EXT-1)
- Place configuration in appropriate location (AMOS-CONF-1)
- Avoid hardcoding configuration values (AMOS-CONF-2)
