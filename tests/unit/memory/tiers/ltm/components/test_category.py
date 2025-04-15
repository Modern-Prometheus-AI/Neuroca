"""
Unit Tests for LTM Category Component

This module contains unit tests for the LTMCategory class which handles
categorization of memories in the LTM tier.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from neuroca.memory.tiers.ltm.components.category import LTMCategory
from neuroca.memory.models.memory_item import MemoryItem, MemoryMetadata, MemoryContent, MemoryStatus
from neuroca.memory.exceptions import TierOperationError


class TestLTMCategory:
    """
    Test suite for LTMCategory class.
    """
    
    @pytest.fixture
    def category_manager(self):
        """
        Create and return an LTMCategory instance with mocked dependencies.
        """
        category_manager = LTMCategory("ltm")
        
        # Create mocks for dependencies
        category_manager._lifecycle = MagicMock()
        category_manager._backend = AsyncMock()
        category_manager._update_func = AsyncMock()
        
        # Configure with default values
        category_manager.configure(
            lifecycle=category_manager._lifecycle,
            backend=category_manager._backend, 
            update_func=category_manager._update_func,
            config={"default_categories": ["general", "test"]}
        )
        
        return category_manager
    
    @pytest.fixture
    def sample_memory_item(self):
        """
        Create a sample memory item for testing.
        """
        return MemoryItem(
            id="test-memory-id",
            content=MemoryContent(
                text="Test memory content",
                summary="Test summary"
            ),
            metadata=MemoryMetadata(
                importance=0.7,
                tags={"test": True}
            )
        )
    
    @pytest.fixture
    def sample_memory_data(self):
        """
        Create sample memory data dictionary for testing.
        """
        return {
            "id": "test-memory-id",
            "content": {
                "text": "Test memory content",
                "summary": "Test summary"
            },
            "metadata": {
                "importance": 0.7,
                "tags": {"test": True},
                "status": MemoryStatus.ACTIVE.value
            }
        }
    
    def test_init(self):
        """
        Test initialization of LTMCategory.
        """
        category_manager = LTMCategory("ltm")
        
        assert category_manager._tier_name == "ltm"
        assert category_manager._lifecycle is None
        assert category_manager._backend is None
        assert category_manager._update_func is None
        assert category_manager._default_categories == ["general"]
    
    def test_configure(self, category_manager):
        """
        Test configuration of LTMCategory.
        """
        # Already configured in fixture, test the results
        assert category_manager._lifecycle is not None
        assert category_manager._backend is not None
        assert category_manager._update_func is not None
        assert category_manager._default_categories == ["general", "test"]
    
    def test_process_on_store(self, category_manager, sample_memory_item):
        """
        Test processing a memory item during storage.
        """
        # Memory has no categories yet
        assert "categories" not in sample_memory_item.metadata.tags
        
        # Process on store
        category_manager.process_on_store(sample_memory_item)
        
        # Should add default categories
        assert "categories" in sample_memory_item.metadata.tags
        assert sample_memory_item.metadata.tags["categories"] == ["general", "test"]
    
    def test_process_on_store_with_existing_categories(self, category_manager, sample_memory_item):
        """
        Test processing a memory item with existing categories during storage.
        """
        # Add existing categories
        sample_memory_item.metadata.tags["categories"] = ["existing"]
        
        # Process on store
        category_manager.process_on_store(sample_memory_item)
        
        # Should not modify existing categories
        assert sample_memory_item.metadata.tags["categories"] == ["existing"]
    
    def test_process_post_store(self, category_manager, sample_memory_item):
        """
        Test processing a memory item after storage.
        """
        # Add categories
        sample_memory_item.metadata.tags["categories"] = ["cat1", "cat2"]
        
        # Process post store
        category_manager.process_post_store(sample_memory_item)
        
        # Should update lifecycle's category map
        category_manager._lifecycle.update_category.assert_called_once_with(
            sample_memory_item.id, ["cat1", "cat2"]
        )
    
    def test_process_pre_delete(self, category_manager):
        """
        Test processing a memory before deletion.
        """
        memory_id = "test-memory-id"
        
        # Process pre delete
        category_manager.process_pre_delete(memory_id)
        
        # Should update lifecycle to remove memory
        category_manager._lifecycle.remove_memory.assert_called_once_with(memory_id)
    
    @pytest.mark.asyncio
    async def test_add_to_category(self, category_manager, sample_memory_data):
        """
        Test adding a memory to a category.
        """
        memory_id = "test-memory-id"
        category = "new-category"
        
        # Configure backend to return the memory
        category_manager._backend.retrieve.return_value = sample_memory_data
        
        # Configure update_func to return True (success)
        category_manager._update_func.return_value = True
        
        # Add to category
        result = await category_manager.add_to_category(memory_id, category)
        
        # Verify result
        assert result is True
        
        # Verify backend was called to retrieve memory
        category_manager._backend.retrieve.assert_called_once_with(memory_id)
        
        # Verify update_func was called with updated metadata
        expected_metadata = {
            "importance": 0.7,
            "tags": {"test": True},
            "status": MemoryStatus.ACTIVE.value,
            "categories": ["new-category"]
        }
        category_manager._update_func.assert_called_once()
        call_args = category_manager._update_func.call_args[0]
        assert call_args[0] == memory_id
        assert "categories" in call_args[1]
        assert "new-category" in call_args[1]["categories"]
        
        # Verify lifecycle was updated
        category_manager._lifecycle.update_category.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_to_category_already_exists(self, category_manager, sample_memory_data):
        """
        Test adding a memory to a category it's already in.
        """
        memory_id = "test-memory-id"
        category = "existing-category"
        
        # Add existing category
        sample_memory_data["metadata"]["categories"] = ["existing-category"]
        
        # Configure backend to return the memory
        category_manager._backend.retrieve.return_value = sample_memory_data
        
        # Add to category
        result = await category_manager.add_to_category(memory_id, category)
        
        # Verify result
        assert result is True
        
        # Verify backend was called to retrieve memory
        category_manager._backend.retrieve.assert_called_once_with(memory_id)
        
        # Verify update_func was NOT called since category already exists
        category_manager._update_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_memories_by_category(self, category_manager, sample_memory_data):
        """
        Test getting memories by category.
        """
        category = "test-category"
        
        # Configure lifecycle to return a category map
        category_manager._lifecycle.get_category_map.return_value = {
            category: {"memory1", "memory2", "memory3"}
        }
        
        # Configure backend to return sample memory data
        category_manager._backend.retrieve.return_value = sample_memory_data
        
        # Get memories by category
        memories = await category_manager.get_memories_by_category(category, limit=2)
        
        # Verify results
        assert len(memories) == 2
        
        # Verify backend was called for retrievals
        assert category_manager._backend.retrieve.call_count == 3
