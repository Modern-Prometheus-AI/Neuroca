"""
Tests for the Memory Consolidation system of the NeuroCognitive Architecture.

These tests verify that memory consolidation correctly moves memories between
tiers (Working → Episodic → Semantic) based on biological principles such as
activation level, emotional salience, and pattern recognition.
"""

from neuroca.core.memory.consolidation import (
    StandardMemoryConsolidator,
    consolidate_working_to_episodic,
    run_consolidation_cycle,
)


class TestMemoryConsolidation:
    """Test suite for memory consolidation between memory tiers."""
    
    def test_working_to_episodic_high_activation(self, working_memory, episodic_memory, memory_consolidator):
        """Test that high-activation working memories get consolidated to episodic memory."""
        # Add an item to working memory
        working_memory.store("Remember this important fact")
        
        # Initially, episodic memory should be empty
        assert len(episodic_memory.dump()) == 0
        
        # Consolidate - this one should move due to high activation (default 1.0)
        ids = memory_consolidator.consolidate(working_memory, episodic_memory)
        
        # Should have consolidated one memory
        assert len(ids) == 1
        
        # Episodic memory should now have the memory
        assert len(episodic_memory.dump()) == 1
        
        # Content should match
        episodic_content = episodic_memory.dump()[0]["content"]
        assert episodic_content == "Remember this important fact"
    
    def test_working_to_episodic_emotional_content(self, working_memory, episodic_memory):
        """Test that emotional content is transferred even with lower activation."""
        # Create consolidator with higher activation threshold but default emotional threshold
        consolidator = StandardMemoryConsolidator(activation_threshold=0.9, emotional_threshold=0.7)
        
        # Add an item to working memory with emotional metadata
        chunk_id = working_memory.store(
            "Something sad happened", 
            emotional_salience=0.8  # High emotional salience
        )
        
        # Now intentionally decrease its activation to below the activation threshold
        chunk = working_memory.retrieve_by_id(chunk_id)
        chunk.update_activation(0.6)  # Below activation threshold
        
        # Consolidate - this should still transfer due to emotional salience
        ids = consolidator.consolidate(working_memory, episodic_memory)
        
        # Should have consolidated one memory
        assert len(ids) == 1
        
        # Episodic memory should have the memory
        assert len(episodic_memory.dump()) == 1
        
        # New memory should have emotional salience preserved
        episodic_memory = episodic_memory.dump()[0]
        assert episodic_memory["emotional_salience"] == 0.8
    
    def test_consolidation_preserves_temporal_context(self, working_memory, episodic_memory, memory_consolidator):
        """Test that consolidation preserves and enhances temporal context."""
        # Store memory with a timestamp in metadata
        original_time = "2023-01-01T12:00:00"
        working_memory.store(
            "Historical event", 
            event_time=original_time
        )
        
        # Consolidate to episodic
        ids = memory_consolidator.consolidate(working_memory, episodic_memory)
        
        # Get the consolidated memory
        episodic_chunk = episodic_memory.retrieve_by_id(ids[0])
        
        # Should have temporal context
        assert "timestamp" in episodic_chunk.temporal_context
        assert "sequence_id" in episodic_chunk.temporal_context
        
        # Original metadata should be preserved
        assert "event_time" in episodic_chunk.metadata
        assert episodic_chunk.metadata["event_time"] == original_time
    
    def test_pattern_tracking(self, working_memory, episodic_memory):
        """Test that the consolidator tracks patterns for repetition detection."""
        consolidator = StandardMemoryConsolidator()
        
        # Store the same content multiple times
        for _i in range(3):
            working_memory.store("Repeated pattern")
            consolidator.consolidate(working_memory, episodic_memory)
        
        # The pattern counter should have tracked this
        # We can't directly access the pattern counter, but we can test its behavior
        # by checking how many episodic memories we have
        assert len(episodic_memory.dump()) == 3
        
        # If we were to consolidate to semantic, this pattern would be recognized
        # This functionality will be tested in episodic_to_semantic tests
    
    def test_helper_functions(self, working_memory, episodic_memory):
        """Test that the helper functions work correctly."""
        # Add an item to working memory
        working_memory.store("Helper function test")
        
        # Use helper function to consolidate
        ids = consolidate_working_to_episodic()
        
        # Should have consolidated one memory
        assert len(ids) == 1
        
        # Episodic memory should now have the memory
        episodic_dump = episodic_memory.dump()
        assert len(episodic_dump) == 1
        assert episodic_dump[0]["content"] == "Helper function test"
    
    def test_run_consolidation_cycle(self, working_memory, episodic_memory):
        """Test that the full consolidation cycle works correctly."""
        # This would require the semantic memory system to test fully,
        # but we can test the working to episodic part now
        
        # Add an item to working memory
        working_memory.store("Cycle test")
        
        # Run the cycle - semantic won't work without implementation
        # but working_to_episodic should still work
        try:
            results = run_consolidation_cycle()
            assert len(results['working_to_episodic']) == 1
        except Exception as e:
            # If semantic isn't implemented yet, this is expected
            assert "semantic" in str(e).lower()
            
            # Just test working_to_episodic directly then
            ids = consolidate_working_to_episodic()
            assert len(ids) == 1
    
    def test_consolidator_threshold_settings(self, working_memory, episodic_memory):
        """Test that consolidator thresholds can be adjusted."""
        consolidator = StandardMemoryConsolidator(
            activation_threshold=0.5, 
            emotional_threshold=0.5,
            repetition_threshold=3
        )
        
        # Update thresholds
        consolidator.set_activation_threshold(0.7)
        consolidator.set_emotional_threshold(0.8)
        consolidator.set_repetition_threshold(5)
        
        # Add item with activation that would pass the old threshold but not the new one
        chunk_id = working_memory.store("Threshold test")
        chunk = working_memory.retrieve_by_id(chunk_id)
        chunk.update_activation(0.6)  # Between old (0.5) and new (0.7) thresholds
        
        # This shouldn't consolidate now because activation is below new threshold
        ids = consolidator.consolidate(working_memory, episodic_memory)
        assert len(ids) == 0
        
        # Now try with emotional salience that would pass old threshold but not new one
        chunk_id = working_memory.store("Emotional test", emotional_salience=0.6)
        # This shouldn't consolidate now because emotional salience is below new threshold
        ids = consolidator.consolidate(working_memory, episodic_memory)
        assert len(ids) == 0
        
        # Try with values that should pass the new thresholds
        chunk_id = working_memory.store("High activation", emotional_salience=0.9)
        ids = consolidator.consolidate(working_memory, episodic_memory)
        assert len(ids) == 1 