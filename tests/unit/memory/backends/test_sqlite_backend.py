"""
Unit tests for SQLite storage backend.
"""

import asyncio
import os
import pytest
import pytest_asyncio
import tempfile
import uuid
from typing import Dict, Any

from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory
from neuroca.memory.models.memory_item import MemoryItem, MemoryContent, MemoryMetadata
from neuroca.memory.models.search import MemorySearchOptions


@pytest_asyncio.fixture
async def sqlite_backend():
    """Create a temporary SQLite backend for testing."""
    # Create a temporary directory for the DB
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_memory.db")
    
    # Create and initialize the backend using factory
    backend = StorageBackendFactory.create_storage(
        backend_type=BackendType.SQLITE,
        config={"db_path": db_path}
    )
    await backend.initialize()
    
    yield backend
    
    # Clean up
    await backend.shutdown()
    try:
        os.remove(db_path)
        os.rmdir(temp_dir)
    except (OSError, IOError):
        pass


@pytest.mark.asyncio
async def test_store_and_retrieve(sqlite_backend):
    """Test storing and retrieving a memory item."""
    # Create test memory
    memory_id = str(uuid.uuid4())
    memory = MemoryItem(
        id=memory_id,
        content=MemoryContent(text="Test content"),
        summary="Test summary",
        metadata=MemoryMetadata(importance=0.8, tags=["test", "memory"])
    )
    
    # Store memory
    stored_id = await sqlite_backend.store(memory)
    assert stored_id == memory_id
    
    # Retrieve memory
    retrieved = await sqlite_backend.retrieve(memory_id)
    assert retrieved is not None
    assert retrieved.id == memory_id
    assert retrieved.content == "Test content"
    assert retrieved.summary == "Test summary"
    assert retrieved.metadata.get("importance") == 0.8
    assert "test" in retrieved.metadata.get("tags", [])
    assert "memory" in retrieved.metadata.get("tags", [])


@pytest.mark.asyncio
async def test_update(sqlite_backend):
    """Test updating a memory item."""
    # Create and store test memory
    memory_id = str(uuid.uuid4())
    memory = MemoryItem(
        id=memory_id,
        content=MemoryContent(text="Initial content"),
        summary="Initial summary",
        metadata=MemoryMetadata(importance=0.5)
    )
    await sqlite_backend.store(memory)
    
    # Update memory
    updated_memory = MemoryItem(
        id=memory_id,
        content=MemoryContent(text="Updated content"),
        summary="Updated summary",
        metadata=MemoryMetadata(importance=0.7, tags=["updated"])
    )
    success = await sqlite_backend.update(updated_memory)
    assert success is True
    
    # Retrieve updated memory
    retrieved = await sqlite_backend.retrieve(memory_id)
    assert retrieved.content == "Updated content"
    assert retrieved.summary == "Updated summary"
    assert retrieved.metadata.get("importance") == 0.7
    assert "updated" in retrieved.metadata.get("tags", [])


@pytest.mark.asyncio
async def test_delete(sqlite_backend):
    """Test deleting a memory item."""
    # Create and store test memory
    memory_id = str(uuid.uuid4())
    memory = MemoryItem(
        id=memory_id,
        content=MemoryContent(text="Content to delete"),
        summary="Summary to delete"
    )
    await sqlite_backend.store(memory)
    
    # Verify memory exists
    retrieved = await sqlite_backend.retrieve(memory_id)
    assert retrieved is not None
    
    # Delete memory
    success = await sqlite_backend.delete(memory_id)
    assert success is True
    
    # Verify memory no longer exists
    retrieved = await sqlite_backend.retrieve(memory_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_search(sqlite_backend):
    """Test searching for memory items."""
    # Create and store test memories
    memories = [
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Apple is a fruit"),
            summary="About apples",
            metadata=MemoryMetadata(importance=0.7, tags=["fruit", "apple"])
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Banana is yellow"),
            summary="About bananas",
            metadata=MemoryMetadata(importance=0.5, tags=["fruit", "banana"])
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Car is a vehicle"),
            summary="About cars",
            metadata=MemoryMetadata(importance=0.8, tags=["vehicle", "car"])
        )
    ]
    
    for memory in memories:
        await sqlite_backend.store(memory)
    
    # Test simple search
    results = await sqlite_backend.search("fruit")
    assert len(results.results) == 2
    
    # Test search with filter
    filter = MemorySearchOptions(
        min_importance=0.7,
        tags=["fruit"]
    )
    results = await sqlite_backend.search("", filter=filter)
    assert len(results.results) == 1
    assert results.results[0].memory.content == "Apple is a fruit"


@pytest.mark.asyncio
async def test_batch_operations(sqlite_backend):
    """Test batch store and delete operations."""
    # Create test memories
    memories = [
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text=f"Batch content {i}"),
            summary=f"Batch summary {i}"
        ) for i in range(5)
    ]
    
    # Test batch store
    memory_ids = await sqlite_backend.batch_store(memories)
    assert len(memory_ids) == 5
    
    # Verify all memories were stored
    for memory_id in memory_ids:
        retrieved = await sqlite_backend.retrieve(memory_id)
        assert retrieved is not None
    
    # Test batch delete
    deleted_count = await sqlite_backend.batch_delete(memory_ids[:3])
    assert deleted_count == 3
    
    # Verify memories were deleted
    for memory_id in memory_ids[:3]:
        retrieved = await sqlite_backend.retrieve(memory_id)
        assert retrieved is None
    
    # Verify remaining memories still exist
    for memory_id in memory_ids[3:]:
        retrieved = await sqlite_backend.retrieve(memory_id)
        assert retrieved is not None


@pytest.mark.asyncio
async def test_count(sqlite_backend):
    """Test counting memory items."""
    # Create and store test memories
    memories = [
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Count test 1"),
            metadata=MemoryMetadata(status="active")
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Count test 2"),
            metadata=MemoryMetadata(status="active")
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Count test 3"),
            metadata=MemoryMetadata(status="archived")
        )
    ]
    
    for memory in memories:
        await sqlite_backend.store(memory)
    
    # Test count with no filter
    count = await sqlite_backend.count()
    assert count == 3
    
    # Test count with filter
    filter = MemorySearchOptions(status="active")
    count = await sqlite_backend.count(filter)
    assert count == 2


@pytest.mark.asyncio
async def test_get_stats(sqlite_backend):
    """Test getting storage statistics."""
    # Create and store test memories
    memories = [
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Stats test 1"),
            metadata=MemoryMetadata(status="active")
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Stats test 2"),
            metadata=MemoryMetadata(status="active")
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            content=MemoryContent(text="Stats test 3"),
            metadata=MemoryMetadata(status="archived")
        )
    ]
    
    for memory in memories:
        await sqlite_backend.store(memory)
    
    # Get stats
    stats = await sqlite_backend.get_stats()
    
    # Verify stats
    assert stats.total_memories == 3
    assert stats.active_memories == 2
    assert stats.archived_memories == 1
    assert stats.total_size_bytes > 0
