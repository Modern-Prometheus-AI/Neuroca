# Neuroca Memory System

This directory contains all components related to the NeuroCognitive Architecture's memory system. This is a cornerstone of NCA, providing the mechanisms for storing, retrieving, and managing information across different time scales and levels of abstraction, inspired by human cognitive memory.

## Structure

- **`manager/`**: Contains the central `MemoryManager` which orchestrates operations across different memory tiers and backends. It handles tasks like adding memories, searching, and triggering maintenance processes (consolidation, decay).
- **`tiers/`**: Defines the different memory tiers (STM, MTM, LTM). Each tier has its own logic for managing memories based on its specific characteristics (e.g., TTL for STM, capacity for MTM).
    - `base/`: Abstract base classes or shared components for memory tiers.
    - `stm/`, `mtm/`, `ltm/`: Implementations for Short-Term, Medium-Term, and Long-Term Memory tiers.
- **`backends/`**: Implements the concrete storage solutions used by the memory tiers. This allows for flexibility in choosing storage technologies (e.g., in-memory dictionaries, SQLite databases, vector databases).
    - `base/`: Abstract base classes for storage backends.
    - `in_memory/`, `sqlite/`, `vector/` (example): Specific backend implementations. Each backend typically provides components for CRUD operations, search, schema management, etc.
    - `factory/`: Responsible for creating instances of the appropriate storage backends based on configuration.
- **`models/`**: Defines the data structures specific to the memory system, such as `MemoryItem`, `MemorySearchResult`, and configuration models for tiers/backends.
- **`utils/`**: Shared utility functions or constants used within the memory system.

## Usage

The `MemoryManager` is the primary entry point for interacting with the memory system. Other parts of the application (e.g., core processing services) use the manager to:
- Add new memories resulting from interactions or internal processing.
- Search for relevant memories to provide context for ongoing tasks.
- Retrieve specific memories by ID.
- Potentially trigger manual maintenance or status checks.

The internal workings, such as moving memories between tiers (consolidation) or removing old memories (decay), are typically handled automatically by background processes managed or triggered by the `MemoryManager` and the individual tiers based on their configured rules.

## Maintenance

- When adding a new storage backend, implement the required interfaces defined in `backends/base/` and register it in the `backends/factory/`.
- Modifications to memory consolidation or decay logic should be made within the relevant `tiers/` implementations or the `manager/` if it orchestrates these processes.
- Ensure `MemoryItem` and other core memory models accurately represent the necessary information.
- Update backend-specific components (like schema or connection handling) when underlying database requirements change.
