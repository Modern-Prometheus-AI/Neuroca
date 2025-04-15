# Memory System Migration Plan

**Date:** April 14, 2025  
**Status:** Ready for Phase 4-5

This document outlines the plan for completing the remaining phases of the memory system refactoring. It provides detailed guidance for migrating existing code, expanding test coverage, implementing additional backends, cleaning up legacy code, and finalizing documentation.

## Table of Contents

- [Migration of Existing Code](#migration-of-existing-code)
- [Comprehensive Test Coverage](#comprehensive-test-coverage)
- [Additional Storage Backends](#additional-storage-backends)
- [Legacy Code Cleanup](#legacy-code-cleanup)
- [Final Validation and Documentation](#final-validation-and-documentation)
- [Timeline and Dependencies](#timeline-and-dependencies)

## Migration of Existing Code

The following existing memory-related code needs to be migrated to use the new architecture:

### 1. Identify Legacy Components

The following legacy components have been identified in the codebase:

- `neuroca/memory/consolidation.py` - Memory consolidation logic
- `neuroca/memory/episodic_memory.py` - Episodic memory implementation
- `neuroca/memory/factory.py` - Old memory factory
- `neuroca/memory/manager.py` - Old memory manager
- `neuroca/memory/memory_consolidation.py` - Memory consolidation logic
- `neuroca/memory/memory_decay.py` - Memory decay logic
- `neuroca/memory/memory_retrieval.py` - Memory retrieval logic
- `neuroca/memory/semantic_memory.py` - Semantic memory implementation
- `neuroca/memory/working_memory.py` - Working memory implementation

### 2. Migration Plan for Each Component

#### Episodic and Semantic Memory

These can be migrated to the LTM tier, with the following mapping:

- `EpisodicMemory` → `LongTermMemoryTier` with specific category "episodic"
- `SemanticMemory` → `LongTermMemoryTier` with specific category "semantic"

**Migration steps:**

1. Create adapter classes in `src/neuroca/memory/adapters/` that implement the legacy interfaces but delegate to the new architecture
2. Update client code to use the new interfaces
3. Add deprecation warnings to the legacy components

Example adapter for Episodic Memory:

```python
# src/neuroca/memory/adapters/episodic_memory_adapter.py
import warnings
from typing import Any, Dict, List, Optional

from neuroca.memory.manager.memory_manager import MemoryManager


class EpisodicMemoryAdapter:
    """
    Adapter for legacy EpisodicMemory that uses the new LTM tier.
    
    This adapter implements the legacy interface but delegates to the new
    Memory Manager and LTM tier.
    
    DEPRECATED: Use MemoryManager directly instead.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        warnings.warn(
            "EpisodicMemoryAdapter is deprecated. Use MemoryManager directly.",
            DeprecationWarning,
            stacklevel=2
        )
        self._memory_manager = memory_manager
        self._ltm = memory_manager._ltm
    
    async def add_memory(self, content, **kwargs):
        """Add a memory to episodic memory."""
        # Add the episodic category
        tags = kwargs.pop("tags", [])
        tags.append("episodic")
        
        # Store in LTM directly
        return await self._memory_manager.add_memory(
            content=content,
            tags=tags,
            initial_tier="ltm",
            **kwargs
        )
        
    # Implement other legacy methods...
```

#### Memory Consolidation and Decay

These functionalities are now handled by the `MemoryManager` and the respective tier components:

- `memory_consolidation.py` → `MemoryManager.consolidate_memory` + tier-specific consolidation
- `memory_decay.py` → `MemoryManager.decay_memory` + tier-specific decay

**Migration steps:**

1. Create adapter functions in a new module `src/neuroca/memory/adapters/legacy_functions.py`
2. Update client code to use the new interfaces
3. Add deprecation warnings to the legacy components

#### Memory Factory

The `factory.py` functionality is replaced by the `MemoryManager` constructor and the backend factory:

**Migration steps:**

1. Create a factory adapter that instantiates the new `MemoryManager` with appropriate configuration
2. Update client code to use the new factory or directly instantiate `MemoryManager`
3. Add deprecation warnings to the legacy factory

### 3. Client Code Updates

Identify all client code that uses the legacy memory components:

1. Search for imports of the legacy components
2. Create a migration guide for each use case
3. Update client code incrementally

## Comprehensive Test Coverage

### 1. Unit Tests for Components

Expand the unit test coverage to include:

- Tests for all STM components
- Tests for all MTM components
- Tests for all LTM components (additional tests beyond the example provided)
- Tests for the Memory Manager

Follow the pattern established in the example test:
- Use pytest fixtures for dependencies
- Mock external dependencies
- Test each method independently
- Include both success and failure cases

### 2. Integration Tests

Create integration tests that verify interactions between components:

- Tests for STM → MTM consolidation
- Tests for MTM → LTM promotion
- Tests for context-aware retrieval
- Tests for working memory management

Example integration test structure:

```python
# tests/integration/memory/test_consolidation.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.backends import BackendType


class TestMemoryConsolidation:
    """
    Integration tests for memory consolidation between tiers.
    """
    
    @pytest.fixture
    async def memory_manager(self):
        """
        Create a MemoryManager with in-memory backends.
        """
        manager = MemoryManager(
            config={
                "stm": {"default_ttl": 3600},
                "mtm": {"max_capacity": 100},
                "ltm": {}
            },
            backend_type=BackendType.IN_MEMORY
        )
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_stm_to_mtm_consolidation(self, memory_manager):
        """
        Test consolidation from STM to MTM.
        """
        # Add a memory to STM
        memory_id = await memory_manager.add_memory(
            content="Test memory for consolidation",
            importance=0.8,
            initial_tier="stm"
        )
        
        # Verify it's in STM
        stm_memory = await memory_manager._stm.retrieve(memory_id)
        assert stm_memory is not None
        
        # Consolidate to MTM
        new_id = await memory_manager.consolidate_memory(
            memory_id=memory_id,
            source_tier="stm",
            target_tier="mtm"
        )
        
        # Verify it's in MTM
        mtm_memory = await memory_manager._mtm.retrieve(new_id)
        assert mtm_memory is not None
        
        # Verify it's not in STM anymore
        stm_memory = await memory_manager._stm.retrieve(memory_id)
        assert stm_memory is None
    
    # Add more integration tests...
```

### 3. Performance Tests

Create performance tests to verify system scalability:

- Tests for large memory counts (1000+ memories)
- Tests for concurrent operations
- Tests for memory usage and efficiency

Example performance test:

```python
# tests/performance/memory/test_memory_performance.py
import pytest
import asyncio
import time

from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.backends import BackendType


class TestMemoryPerformance:
    """
    Performance tests for the memory system.
    """
    
    @pytest.fixture
    async def memory_manager(self):
        """
        Create a MemoryManager with in-memory backends.
        """
        manager = MemoryManager(
            config={
                "stm": {"max_capacity": 10000},
                "mtm": {"max_capacity": 10000},
                "ltm": {}
            },
            backend_type=BackendType.IN_MEMORY
        )
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_bulk_memory_addition(self, memory_manager):
        """
        Test adding a large number of memories.
        """
        memory_count = 1000
        start_time = time.time()
        
        # Add memories
        for i in range(memory_count):
            await memory_manager.add_memory(
                content=f"Test memory {i}",
                importance=0.5,
                initial_tier="stm"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Added {memory_count} memories in {duration:.2f} seconds")
        print(f"Average time per memory: {(duration / memory_count) * 1000:.2f} ms")
        
        # Assert reasonable performance
        assert duration / memory_count < 0.01  # Less than 10ms per memory
    
    # Add more performance tests...
```

## Additional Storage Backends

### 1. SQLite Backend

Implement a SQLite backend for persistent storage:

```python
# src/neuroca/memory/backends/sqlite_backend.py
import os
import json
import sqlite3
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.exceptions import (
    BackendInitializationError,
    MemoryNotFoundError,
    StorageOperationError,
)


class SQLiteBackend(BaseStorageBackend):
    """
    SQLite storage backend for persistent memory storage.
    
    This backend stores memories in a SQLite database, with support for
    all the operations defined in the StorageBackendInterface.
    """
    
    def __init__(self, db_path: str, **kwargs):
        """
        Initialize the SQLite backend.
        
        Args:
            db_path: Path to the SQLite database file
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self._db_path = db_path
        self._connection = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """
        Initialize the SQLite backend.
        
        Creates the database and tables if they don't exist.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            
            # Connect to database
            self._connection = sqlite3.connect(self._db_path)
            
            # Create tables
            cursor = self._connection.cursor()
            
            # Create memories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            ''')
            
            # Create embeddings table (if vector search is supported)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (id) REFERENCES memories (id) ON DELETE CASCADE
                )
            ''')
            
            # Create index on created_at for efficient time-based queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memories_created_at
                ON memories (created_at)
            ''')
            
            self._connection.commit()
            cursor.close()
            
        except Exception as e:
            raise BackendInitializationError(
                f"Failed to initialize SQLite backend: {str(e)}"
            ) from e
    
    async def shutdown(self) -> None:
        """
        Shut down the SQLite backend.
        
        Closes the database connection.
        """
        if self._connection:
            self._connection.close()
            self._connection = None
    
    # Implement all other methods from the interface...
```

### 2. Redis Backend

Implement a Redis backend for high-performance storage:

```python
# src/neuroca/memory/backends/redis_backend.py
import json
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import redis
from redis.asyncio import Redis

from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.exceptions import (
    BackendInitializationError,
    MemoryNotFoundError,
    StorageOperationError,
)


class RedisBackend(BaseStorageBackend):
    """
    Redis storage backend for high-performance memory storage.
    
    This backend stores memories in Redis, with support for all the
    operations defined in the StorageBackendInterface.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "memory:",
        **kwargs
    ):
        """
        Initialize the Redis backend.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            prefix: Key prefix for Redis keys
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self._host = host
        self._port = port
        self._db = db
        self._prefix = prefix
        self._client = None
    
    async def initialize(self) -> None:
        """
        Initialize the Redis backend.
        
        Connects to the Redis server.
        """
        try:
            self._client = Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                decode_responses=True
            )
            
            # Test connection
            await self._client.ping()
            
        except Exception as e:
            raise BackendInitializationError(
                f"Failed to initialize Redis backend: {str(e)}"
            ) from e
    
    async def shutdown(self) -> None:
        """
        Shut down the Redis backend.
        
        Closes the Redis connection.
        """
        if self._client:
            await self._client.close()
            self._client = None
    
    # Implement all other methods from the interface...
```

### 3. Update Backend Factory

Update the backend factory to support the new backends:

```python
# src/neuroca/memory/backends/factory/backend_type.py
from enum import Enum


class BackendType(Enum):
    """
    Enumeration of supported storage backend types.
    """
    IN_MEMORY = "in_memory"
    SQLITE = "sqlite"
    REDIS = "redis"
```

```python
# src/neuroca/memory/backends/factory/storage_factory.py
from typing import Any, Dict, Optional

from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.in_memory_backend import InMemoryBackend
from neuroca.memory.backends.sqlite_backend import SQLiteBackend
from neuroca.memory.backends.redis_backend import RedisBackend
from neuroca.memory.exceptions import BackendInitializationError


class StorageBackendFactory:
    """
    Factory for creating storage backend instances.
    """
    
    @staticmethod
    async def create_backend(
        backend_type: BackendType,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseStorageBackend:
        """
        Create a storage backend instance of the specified type.
        
        Args:
            backend_type: Type of backend to create
            config: Backend configuration
            
        Returns:
            Storage backend instance
            
        Raises:
            BackendInitializationError: If backend creation fails
        """
        config = config or {}
        
        try:
            if backend_type == BackendType.IN_MEMORY:
                backend = InMemoryBackend(**config)
            elif backend_type == BackendType.SQLITE:
                db_path = config.get("db_path", "data/memory.db")
                backend = SQLiteBackend(db_path=db_path, **config)
            elif backend_type == BackendType.REDIS:
                host = config.get("host", "localhost")
                port = config.get("port", 6379)
                db = config.get("db", 0)
                prefix = config.get("prefix", "memory:")
                backend = RedisBackend(
                    host=host,
                    port=port,
                    db=db,
                    prefix=prefix,
                    **config
                )
            else:
                raise BackendInitializationError(
                    f"Unsupported backend type: {backend_type}"
                )
            
            # Initialize the backend
            await backend.initialize()
            
            return backend
        except Exception as e:
            raise BackendInitializationError(
                f"Failed to create backend of type {backend_type}: {str(e)}"
            ) from e
```

## Legacy Code Cleanup

### 1. Deprecation Strategy

1. Mark legacy components with deprecation warnings
2. Add documentation to direct users to the new API
3. Set a timeline for removal (e.g., 3 months)

### 2. Code Removal Plan

After the migration is complete and enough time has passed for users to migrate:

1. Remove old files one by one
2. Update imports in all affected files
3. Remove backward compatibility layers
4. Verify the system still works correctly

## Final Validation and Documentation

### 1. Validation Plan

1. Run comprehensive test suite (unit, integration, performance tests)
2. Perform manual validation of key scenarios
3. Verify compatibility with existing code
4. Test with different backend configurations

### 2. Documentation Updates

1. Update API documentation with the new architecture
2. Create migration guides for each legacy component
3. Create examples for common use cases
4. Update architecture diagrams to reflect the final implementation

### 3. Performance Benchmarks

Document the performance of the new system compared to the legacy system:

- Memory usage
- Operation latency
- Scalability limits

## Timeline and Dependencies

### Phase 4: Cleanup and Removal of Old Code (Weeks 1-3)

1. Week 1: Implement adapters for legacy components
2. Week 2: Update client code to use the new architecture
3. Week 3: Deprecate old code with warnings

### Phase 5: Documentation and Final Validation (Weeks 4-6)

1. Week 4: Implement additional backends
2. Week 5: Expand test coverage
3. Week 6: Update documentation and verify final implementation

### Dependencies

- The SQLite backend requires the `sqlite3` module (standard library)
- The Redis backend requires the `redis` package (`pip install redis`)
- Performance testing requires a test environment with sufficient resources

This migration plan provides a detailed roadmap for completing the memory system refactoring. By following this plan, we can efficiently migrate existing code, expand the capabilities of the new architecture, and ensure a smooth transition for users.
