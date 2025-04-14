"""
Integration tests for the tiered memory storage system.

This module contains tests that verify the interaction between different memory tiers
and their respective storage backends. It demonstrates how the tiered memory system
functions as a whole.
"""

import asyncio
import os
import shutil
import tempfile
from datetime import datetime
from typing import Dict, Any, List

import pytest

from neuroca.memory.backends import (
    BackendType,
    MemoryTier,
    StorageBackendFactory,
)
from neuroca.memory.ltm.storage import MemoryItem, MemoryMetadata, MemoryStatus
from neuroca.memory.mtm.storage import MTMMemory, MemoryPriority, MemoryStatus as MTMStatus


@pytest.fixture(scope="module")
def test_dirs():
    """Create temporary directories for test storage."""
    # Create base directory
    base_dir = tempfile.mkdtemp(prefix="neuroca_test_")
    
    # Create subdirectories for each tier
    stm_dir = os.path.join(base_dir, "stm")
    mtm_dir = os.path.join(base_dir, "mtm")
    ltm_dir = os.path.join(base_dir, "ltm")
    vector_dir = os.path.join(base_dir, "vector")
    
    os.makedirs(stm_dir, exist_ok=True)
    os.makedirs(mtm_dir, exist_ok=True)
    os.makedirs(ltm_dir, exist_ok=True)
    os.makedirs(vector_dir, exist_ok=True)
    
    # Return paths
    yield {
        "base_dir": base_dir,
        "stm_dir": stm_dir,
        "mtm_dir": mtm_dir,
        "ltm_dir": ltm_dir,
        "vector_dir": vector_dir,
    }
    
    # Clean up
    shutil.rmtree(base_dir)


@pytest.mark.asyncio
async def test_memory_flow_between_tiers(test_dirs):
    """
    Test the flow of memories between different tiers (STM -> MTM -> LTM).
    
    This test simulates the memory consolidation process where:
    1. Memories are initially created in STM
    2. Important memories are moved to MTM
    3. Valuable long-term memories are consolidated into LTM
    4. Semantic search is performed using the vector backend
    """
    # Configure storage backends for each tier
    stm_config = {
        "base_path": test_dirs["stm_dir"],
        "max_items": 100,
        "default_ttl": 60,  # Short TTL for testing
    }
    
    mtm_config = {
        "storage_dir": test_dirs["mtm_dir"],
    }
    
    ltm_config = {
        "base_path": test_dirs["ltm_dir"],
    }
    
    vector_config = {
        "dimension": 3,  # Small dimension for testing
        "similarity_threshold": 0.7,
        "index_path": os.path.join(test_dirs["vector_dir"], "vector_index.json"),
    }
    
    # Create storage instances
    stm_storage = StorageBackendFactory.create_storage(
        tier=MemoryTier.STM,
        config=stm_config
    )
    
    mtm_storage = StorageBackendFactory.create_storage(
        tier=MemoryTier.MTM,
        backend_type=BackendType.FILE,
        config=mtm_config
    )
    
    ltm_storage = StorageBackendFactory.create_storage(
        tier=MemoryTier.LTM,
        backend_type=BackendType.FILE,
        config=ltm_config
    )
    
    vector_storage = StorageBackendFactory.create_storage(
        tier=MemoryTier.LTM,
        backend_type=BackendType.VECTOR,
        config=vector_config
    )
    
    # Initialize all storage backends
    await stm_storage.initialize()
    await mtm_storage.backend.initialize()
    await ltm_storage.initialize()
    await vector_storage.initialize()
    
    # STEP 1: Create memories in STM
    stm_memories = []
    for i in range(5):
        content = {
            "text": f"STM memory #{i}",
            "created": datetime.now().isoformat(),
            "importance": 0.5 + (i * 0.1),  # Increasing importance
        }
        
        metadata = {
            "source": "test",
            "category": "memory_flow_test",
            "tags": ["test", f"memory_{i}"],
        }
        
        memory_id = await stm_storage.store(content, metadata)
        stm_memories.append({
            "id": memory_id,
            "content": content,
            "metadata": metadata,
        })
    
    # Verify memories are in STM
    for memory in stm_memories:
        result = await stm_storage.retrieve(memory["id"])
        assert result is not None
    
    # STEP 2: Move important memories to MTM
    mtm_memories = []
    for memory in stm_memories:
        # Only move memories with importance > 0.6 to MTM
        if memory["content"]["importance"] > 0.6:
            mtm_memory = MTMMemory(
                content=memory["content"],
                tags=memory["metadata"]["tags"],
                priority=MemoryPriority.MEDIUM if memory["content"]["importance"] < 0.8 else MemoryPriority.HIGH,
                metadata=memory["metadata"]
            )
            
            memory_id = await mtm_storage.store(mtm_memory.content, mtm_memory.tags,
                                               mtm_memory.priority, mtm_memory.metadata)
            mtm_memories.append({
                "id": memory_id,
                "mtm_memory": mtm_memory
            })
            
            # Delete from STM (in a real system, this might be done by a decay process)
            await stm_storage.delete(memory["id"])
    
    # Verify important memories moved to MTM
    assert len(mtm_memories) > 0
    for memory in mtm_memories:
        result = await mtm_storage.retrieve(memory["id"])
        assert result is not None
    
    # STEP 3: Consolidate to LTM
    ltm_memories = []
    for memory in mtm_memories:
        # In a real system, this would happen after a period of time
        # based on importance, access frequency, etc.
        
        # Create a summary
        summary = f"Summary of {memory['mtm_memory'].content['text']}"
        
        # Create LTM memory with embedding (simplified for test)
        ltm_memory = MemoryItem(
            content=memory["mtm_memory"].content,
            summary=summary,
            embedding=[0.1, 0.2, 0.3],  # Simplified embedding for testing
            metadata=MemoryMetadata(
                status=MemoryStatus.ACTIVE,
                tags=memory["mtm_memory"].tags,
                importance=memory["mtm_memory"].content["importance"],
                created_at=datetime.now(),
                source="mtm_consolidation"
            )
        )
        
        # Store in LTM
        memory_id = await ltm_storage.store(ltm_memory)
        ltm_memories.append({
            "id": memory_id,
            "ltm_memory": ltm_memory
        })
        
        # Also store in vector database for semantic search
        await vector_storage.store(ltm_memory)
        
        # Mark as consolidated in MTM
        await mtm_storage.consolidate_memory(memory["id"])
    
    # Verify memories are in LTM
    for memory in ltm_memories:
        result = await ltm_storage.get(memory["id"])
        assert result is not None
        
        # Also check vector store
        result = await vector_storage.get(memory["id"])
        assert result is not None
    
    # STEP 4: Perform semantic search
    # In a real system, this would use actual embeddings
    search_results = await vector_storage.search(
        query="Test search",
        query_embedding=[0.1, 0.2, 0.3],  # Similar to our test embeddings
    )
    
    # Should find all memories we put in the vector store
    assert len(search_results) == len(ltm_memories)
    
    # Verify the search results contain the expected memories
    result_ids = [memory.id for memory in search_results]
    for memory in ltm_memories:
        assert memory["id"] in result_ids


@pytest.mark.asyncio
async def test_memory_retrieval_by_priority(test_dirs):
    """
    Test retrieving memories based on priority across tiers.
    
    This test demonstrates:
    1. Creating memories with different priorities
    2. Retrieving memories based on priority
    3. Cross-tier search capabilities
    """
    # Configure storage backends
    stm_config = {"base_path": test_dirs["stm_dir"]}
    mtm_config = {"storage_dir": test_dirs["mtm_dir"]}
    
    # Create storage instances
    stm_storage = StorageBackendFactory.create_storage(tier=MemoryTier.STM, config=stm_config)
    mtm_storage = StorageBackendFactory.create_storage(
        tier=MemoryTier.MTM, 
        backend_type=BackendType.FILE,
        config=mtm_config
    )
    
    # Initialize storage
    await stm_storage.initialize()
    await mtm_storage.backend.initialize()
    
    # Create memories with different priorities in MTM
    priority_levels = [
        (MemoryPriority.LOW, "Low priority memory"),
        (MemoryPriority.MEDIUM, "Medium priority memory"),
        (MemoryPriority.HIGH, "High priority memory"),
        (MemoryPriority.CRITICAL, "Critical memory")
    ]
    
    for i, (priority, text) in enumerate(priority_levels):
        mtm_memory = MTMMemory(
            content={"text": text, "index": i},
            tags=["test", f"priority_{priority.name.lower()}"],
            priority=priority,
            metadata={"test_id": f"priority_test_{i}"}
        )
        
        await mtm_storage.store(mtm_memory.content, mtm_memory.tags, mtm_memory.priority, mtm_memory.metadata)
    
    # Create memories in STM
    stm_memory_ids = []
    for i in range(3):
        importance = 0.3 + (i * 0.3)  # 0.3, 0.6, 0.9
        memory_id = await stm_storage.store(
            content={"text": f"STM memory with importance {importance}", "importance": importance},
            metadata={"priority_level": "low" if importance < 0.5 else "high" if importance > 0.7 else "medium"}
        )
        stm_memory_ids.append(memory_id)
    
    # Search for high priority memories in MTM
    high_priority_results = await mtm_storage.search(
        min_priority=MemoryPriority.HIGH
    )
    
    # Should find HIGH and CRITICAL memories
    assert len(high_priority_results) == 2
    for memory in high_priority_results:
        assert memory.priority.value >= MemoryPriority.HIGH.value
    
    # Search for memories with specific tags
    tag_results = await mtm_storage.search(tags=["priority_medium"])
    assert len(tag_results) == 1
    assert tag_results[0].priority == MemoryPriority.MEDIUM
    
    # Retrieve STM memories by filter
    stm_high_importance = await stm_storage.retrieve(
        filter_criteria={"metadata.priority_level": "high"}
    )
    assert len(stm_high_importance) == 1
    
    # Test clearing STM
    count = await stm_storage.clear()
    assert count == len(stm_memory_ids)
    
    # Verify STM is empty
    for memory_id in stm_memory_ids:
        result = await stm_storage.retrieve(memory_id)
        assert result is None
