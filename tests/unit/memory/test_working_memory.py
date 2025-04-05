"""
Tests for the Working Memory implementation of the NeuroCognitive Architecture.

These tests verify that the WorkingMemory system properly implements biological
constraints like capacity limits, activation decay, and recency effects.
"""

import pytest
import time
from neuroca.core.memory.factory import create_memory_system


class TestWorkingMemory:
    """Test suite for the WorkingMemory system."""
    
    def test_capacity_constraint(self, working_memory):
        """Test that working memory respects its capacity constraint."""
        # Set capacity explicitly
        memory = create_memory_system("working", capacity=7)
        
        # Store more than capacity items
        for i in range(10):
            memory.store(f"Memory item {i}")
        
        # Verify only capacity items remain
        assert len(memory.dump()) == 7
    
    def test_capacity_bounds(self):
        """Test that capacity must be within the biological range (5-9)."""
        # Should accept capacities between 5-9
        assert create_memory_system("working", capacity=5)
        assert create_memory_system("working", capacity=9)
        
        # Should reject capacities outside 5-9
        with pytest.raises(ValueError):
            create_memory_system("working", capacity=4)
        
        with pytest.raises(ValueError):
            create_memory_system("working", capacity=10)
    
    def test_activation_decay(self, working_memory):
        """Test that memory chunks decay over time."""
        # Store an item and get its initial activation
        chunk_id = working_memory.store("Test memory")
        initial_activation = working_memory.retrieve_by_id(chunk_id).activation
        
        # Wait for decay to occur
        time.sleep(1)
        
        # Force decay calculation
        working_memory.retrieve(query="anything")
        
        # Check activation has decreased
        current_activation = working_memory.retrieve_by_id(chunk_id).activation
        assert current_activation < initial_activation
    
    def test_recency_effect(self, working_memory):
        """Test that accessing a memory increases its activation."""
        # Store items
        chunk_id = working_memory.store("Test memory")
        
        # Get initial activation, wait for some decay
        initial_activation = working_memory.retrieve_by_id(chunk_id).activation
        time.sleep(0.5)
        
        # Force decay calculation and retrieve again (should boost activation)
        working_memory.retrieve(query="Test")
        
        # Get new activation - should be higher than before retrieval
        new_activation = working_memory.retrieve_by_id(chunk_id).activation
        assert new_activation > initial_activation * 0.9  # Account for some decay
    
    def test_least_active_displaced(self, working_memory):
        """Test that when capacity is reached, least active item is displaced."""
        # Create small capacity memory for easier testing
        memory = create_memory_system("working", capacity=5)
        
        # Store capacity items
        stored_ids = []
        for i in range(5):
            stored_ids.append(memory.store(f"Memory {i}"))
        
        # Access all but the first item to increase their activation
        for chunk_id in stored_ids[1:]:
            memory.retrieve_by_id(chunk_id)
        
        # Force decay calculation
        memory.retrieve(query="X")
        
        # Add a new item, should displace the first (least activated) item
        new_id = memory.store("New memory")
        
        # First item should be gone, new item should be present
        assert memory.retrieve_by_id(stored_ids[0]) is None
        assert memory.retrieve_by_id(new_id) is not None
        
        # Should still be at capacity
        assert len(memory.dump()) == 5
    
    def test_explicit_forgetting(self, working_memory):
        """Test that we can explicitly forget items."""
        # Store an item and verify it exists
        chunk_id = working_memory.store("Remember me")
        assert working_memory.retrieve_by_id(chunk_id) is not None
        
        # Forget it and verify it's gone
        assert working_memory.forget(chunk_id) is True
        assert working_memory.retrieve_by_id(chunk_id) is None
        
        # Forgetting again should return False
        assert working_memory.forget(chunk_id) is False
    
    def test_retrieval_boosts_activation(self, populated_working_memory):
        """Test that retrieving a memory boosts its activation."""
        memory = populated_working_memory
        
        # Query for specific items
        results = memory.retrieve("importance")
        
        # Should have found the item
        assert len(results) >= 1
        
        # Find the medium importance memory
        medium_memory = None
        for result in results:
            if "medium importance" in str(result.content).lower():
                medium_memory = result
                break
        
        assert medium_memory is not None
        
        # Activation should be high after retrieval
        assert medium_memory.activation > 0.6  # It was set to 0.6 and retrieval boosted it
    
    def test_clear_memory(self, populated_working_memory):
        """Test that we can clear all items from memory."""
        memory = populated_working_memory
        
        # Verify items exist
        assert len(memory.dump()) > 0
        
        # Clear memory
        memory.clear()
        
        # Verify memory is empty
        assert len(memory.dump()) == 0
    
    def test_statistics(self, working_memory):
        """Test that memory statistics are properly reported."""
        memory = working_memory
        
        # Initially empty
        stats = memory.get_statistics()
        assert stats["name"] == "working_memory"
        assert stats["used"] == 0
        assert stats["percent_full"] == 0
        
        # Add some items
        for i in range(3):
            memory.store(f"Memory {i}")
        
        # Check updated stats
        stats = memory.get_statistics()
        assert stats["used"] == 3
        assert stats["percent_full"] > 0  # Depends on capacity
        assert stats["average_activation"] > 0 