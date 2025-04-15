"""
Integration tests for the memory tier system.

These tests verify the integrated behavior of memory tiers with their storage backends,
focusing on cross-tier operations and proper integration of components.
"""

import pytest
import time
import asyncio
from typing import Dict, List, Any, Generator
from neuroca.memory.manager.consolidation import consolidate_stm_to_mtm

from neuroca.memory.interfaces.memory_tier import MemoryTierInterface
from neuroca.memory.models.memory_item import MemoryItem, MemoryMetadata, MemoryContent
from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory
from neuroca.memory.tiers.stm.core import ShortTermMemoryTier
from neuroca.memory.tiers.mtm.core import MediumTermMemoryTier
from neuroca.memory.tiers.ltm.core import LongTermMemoryTier
from neuroca.memory.manager.core import MemoryManager


@pytest.fixture
def memory_tiers() -> Generator[Dict[str, MemoryTierInterface], None, None]: # Or Iterator[...]
    """Setup memory tiers with in-memory backends for testing."""
    # Initialize tiers with in-memory backends for testing
    stm = ShortTermMemoryTier(
        storage_backend=StorageBackendFactory.create_storage(backend_type=BackendType.MEMORY)
    )
    mtm = MediumTermMemoryTier(
        storage_backend=StorageBackendFactory.create_storage(backend_type=BackendType.MEMORY)
    )
    ltm = LongTermMemoryTier(
        storage_backend=StorageBackendFactory.create_storage(backend_type=BackendType.MEMORY)
    )
    
    # Initialize tiers - these are async methods, so we need to use asyncio.run
    asyncio.run(stm.initialize())
    asyncio.run(mtm.initialize())
    asyncio.run(ltm.initialize())
    
    yield {
        "stm": stm,
        "mtm": mtm,
        "ltm": ltm
    }
    
    # Cleanup - these are async methods too
    asyncio.run(stm.shutdown())
    asyncio.run(mtm.shutdown())
    asyncio.run(ltm.shutdown())


@pytest.fixture
def memory_manager(memory_tiers) -> Generator[MemoryManager, None, None]: # Or Iterator[...]
    """Setup memory manager with test tiers."""
    manager = MemoryManager(
        stm_storage=memory_tiers["stm"],
        # Use the existing storage instances instead of creating new ones
        mtm_storage_type=BackendType.MEMORY,
        ltm_storage_type=BackendType.MEMORY
    )
    asyncio.run(manager.initialize())
    
    yield manager
    
    asyncio.run(manager.shutdown())


@pytest.fixture
def sample_memories() -> List[MemoryItem]:
    """Create sample memories for testing."""
    return [
        MemoryItem(
            content=MemoryContent(text="This is a test memory for integration tests"),
            metadata=MemoryMetadata(
                importance=0.8,
                source="integration_test",
                tags=["test", "integration"]
            )
        ),
        MemoryItem(
            content=MemoryContent(text="Another test memory with different characteristics"),
            metadata=MemoryMetadata(
                importance=0.5,
                source="integration_test",
                tags=["test", "different"]
            )
        ),
        MemoryItem(
            content=MemoryContent(text="Low importance memory that might be forgotten"),
            metadata=MemoryMetadata(
                importance=0.2,
                source="integration_test",
                tags=["test", "low_importance"]
            )
        )
    ]


class TestTierIntegration:
    """Test integration between memory tiers."""
    
    @pytest.mark.asyncio
    async def test_stm_storage_and_retrieval(self, memory_tiers, sample_memories):
        """Test that STM can store and retrieve memories."""
        stm = memory_tiers["stm"]
        
        # Store memories
        memory_ids = []
        for memory in sample_memories:
            memory_id = await stm.store(memory)
            memory_ids.append(memory_id)
            
        # Verify count
        assert await stm.count() == len(sample_memories)
        
        # Retrieve and verify content
        for i, memory_id in enumerate(memory_ids):
            retrieved = await stm.retrieve(memory_id)
            assert retrieved is not None
            assert retrieved.content == sample_memories[i].content
            assert retrieved.metadata.importance == sample_memories[i].metadata.importance
    
    @pytest.mark.asyncio
    async def test_cross_tier_transfer(self, memory_tiers, sample_memories):
        """Test memory transfer between tiers."""
        stm = memory_tiers["stm"]
        mtm = memory_tiers["mtm"]
        
        # Store in STM
        memory_id = await stm.store(sample_memories[0])
        
        # Get from STM
        memory = await stm.retrieve(memory_id)
        assert memory is not None
        
        # Transfer to MTM
        mtm_id = await mtm.store(memory)
        
        # Verify in MTM
        mtm_memory = await mtm.retrieve(mtm_id)
        assert mtm_memory is not None
        assert mtm_memory.content == memory.content
        
        # Remove from STM (simulating consolidation)
        await stm.delete(memory_id)
        
        # Verify removed from STM
        assert await stm.retrieve(memory_id) is None
        
        # But still in MTM
        assert await mtm.retrieve(mtm_id) is not None
    
    @pytest.mark.asyncio
    async def test_vector_search(self, memory_tiers, sample_memories):
        """Test vector search across tiers."""
        ltm = memory_tiers["ltm"]
        
        # Store memories in LTM
        for memory in sample_memories:
            await ltm.store(memory)
        
        # Search by content
        search_results = await ltm.search("test memory")
        
        # Verify results
        assert len(search_results.items) > 0
        assert any("test memory" in item.memory.content for item in search_results.items)


class TestMemoryManagerIntegration:
    """Test memory manager integration with tiers."""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, memory_manager, sample_memories):
        """Test storing and retrieving through manager."""
        # Store through manager
        memory_id = await memory_manager.add_memory(sample_memories[0])
        
        # Retrieve through manager
        memory = await memory_manager.retrieve_memory(memory_id)
        
        # Verify
        assert memory is not None
        assert memory.content == sample_memories[0].content
    
    @pytest.mark.asyncio
    async def test_consolidation(self, memory_manager, sample_memories):
        """Test consolidation process between tiers."""
        # Store several memories
        memory_ids = []
        for memory in sample_memories:
            memory_id = await memory_manager.add_memory(memory)
            memory_ids.append(memory_id)
        
        # Check initial state
        assert await memory_manager.stm_storage.count() == len(sample_memories)
        assert await memory_manager.mtm_storage.count() == 0
        
        # Trigger consolidation (typically this is called by scheduler)
        await asyncio.gather(
            consolidate_stm_to_mtm(
                stm_storage=memory_manager.stm_storage,
                mtm_storage=memory_manager.mtm_storage,
                config=memory_manager.config
            )
        )
        
        # Verify some consolidation occurred - memories moved from STM to MTM
        # Only higher importance memories should be consolidated
        high_importance_count = sum(1 for m in sample_memories if m.metadata.importance >= 0.5)
        
        # Wait a moment for async operations if needed
        time.sleep(0.1)
        
        # Verify MTM has received high importance memories
        assert await memory_manager.mtm_storage.count() > 0
        # The actual count may vary based on consolidation strategy, but should be
        # at least equal to the high importance memories
        assert await memory_manager.mtm_storage.count() >= high_importance_count
    
    @pytest.mark.asyncio
    async def test_search_across_tiers(self, memory_manager, sample_memories):
        """Test searching across all memory tiers."""
        # Store memories in different tiers
        # First in STM
        for memory in sample_memories[:1]:
            await memory_manager.add_memory(memory)
        
        # Store directly in MTM and LTM for testing
        for memory in sample_memories[1:2]:
            await memory_manager.mtm_storage.store(memory)
        
        for memory in sample_memories[2:]:
            await memory_manager.ltm_storage.store(memory)
        
        # Search across all tiers
        search_results = await memory_manager.search_memories("test")
        
        # Should find results from all tiers
        assert len(search_results.items) == len(sample_memories)
        
        # Search with specific content
        specific_results = await memory_manager.search_memories("low importance")
        
        # Should find only the specific memory
        assert len(specific_results.items) == 1
        assert "low importance" in specific_results.items[0].memory.content
    
    @pytest.mark.asyncio
    async def test_memory_context(self, memory_manager, sample_memories):
        """Test retrieving context-relevant memories."""
        # Store memories
        for memory in sample_memories:
            await memory_manager.add_memory(memory)
        
        # Get memory context
        context_memories = await memory_manager.get_prompt_context_memories(max_memories=2)
        
        # Verify context
        assert len(context_memories) <= 2
        assert all("test" in memory.content for memory in context_memories)


class TestBackendIntegration:
    """Test integration with different backend types."""
    
    @pytest.mark.parametrize("backend_type", [
        BackendType.MEMORY,
        BackendType.SQLITE,
        pytest.param(BackendType.REDIS, marks=pytest.mark.skipif(
            True, reason="Redis server might not be available in test environment"
        )),
    ])
    @pytest.mark.asyncio
    async def test_backend_compatibility(self, backend_type, sample_memories):
        """Test compatibility with different backend types."""
        # Skip certain backends if necessary based on environment
        if backend_type == BackendType.REDIS:
            pytest.skip("Redis tests are skipped by default")
        
        # Create backend
        try:
            backend = StorageBackendFactory.create_storage(backend_type=backend_type)
        except Exception as e:
            pytest.skip(f"Backend {backend_type} not available: {str(e)}")
        
        # Create memory tier with this backend
        stm = ShortTermMemoryTier(storage_backend=backend)
        await stm.initialize()
        
        try:
            # Test basic operations
            memory_id = await stm.store(sample_memories[0])
            retrieved = await stm.retrieve(memory_id)
            
            # Verify
            assert retrieved is not None
            assert retrieved.content == sample_memories[0].content
            
            # Test batch operations if supported
            batch_ids = await stm.batch_store(sample_memories[1:])
            assert len(batch_ids) == len(sample_memories[1:])
            
            # Verify count
            assert await stm.count() == len(sample_memories)
            
        finally:
            # Cleanup
            await stm.shutdown()
