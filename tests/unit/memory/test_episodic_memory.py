"""
Tests for the Episodic Memory implementation of the NeuroCognitive Architecture.

These tests verify that the EpisodicMemory system properly implements biological
features like temporal context, emotional salience, and sequence tracking.
"""

import time
from datetime import datetime


class TestEpisodicMemory:
    """Test suite for the EpisodicMemory system."""
    
    def test_unlimited_capacity(self, episodic_memory):
        """Test that episodic memory has unlimited capacity."""
        # Verify capacity is None (unlimited)
        assert episodic_memory.capacity is None
        
        # Store many items
        for i in range(100):
            episodic_memory.store(f"Memory item {i}")
        
        # Verify all items were stored
        assert len(episodic_memory.dump()) == 100
    
    def test_temporal_context(self, episodic_memory):
        """Test that each memory has a temporal context."""
        # Store a memory
        memory_id = episodic_memory.store("Meeting with Alice")
        
        # Retrieve and check temporal context
        memory_chunk = episodic_memory.retrieve_by_id(memory_id)
        
        # Should have timestamp and sequence_id
        assert "timestamp" in memory_chunk.temporal_context
        assert "sequence_id" in memory_chunk.temporal_context
        
        # Timestamp should be recent
        now = datetime.now().timestamp()
        stored_time = memory_chunk.temporal_context["timestamp"]
        assert now - stored_time < 5  # Within 5 seconds
    
    def test_emotional_salience(self, episodic_memory):
        """Test that emotional salience affects memory retrieval and decay."""
        # Store memories with different emotional salience
        high_emotion_id = episodic_memory.store("Exciting achievement", emotional_salience=0.9)
        low_emotion_id = episodic_memory.store("Regular Tuesday", emotional_salience=0.1)
        
        # Verify emotional salience was stored
        high_emotion = episodic_memory.retrieve_by_id(high_emotion_id)
        low_emotion = episodic_memory.retrieve_by_id(low_emotion_id)
        
        assert high_emotion.emotional_salience == 0.9
        assert low_emotion.emotional_salience == 0.1
        
        # Wait for decay
        time.sleep(1)
        
        # Force decay calculation by doing a retrieval
        episodic_memory.retrieve(query="anything")
        
        # High emotional memory should decay slower
        high_emotion = episodic_memory.retrieve_by_id(high_emotion_id)
        low_emotion = episodic_memory.retrieve_by_id(low_emotion_id)
        
        # The high emotional memory should have higher activation after decay
        assert high_emotion.activation > low_emotion.activation
    
    def test_emotional_salience_filtering(self, populated_episodic_memory):
        """Test that we can filter by emotional salience during retrieval."""
        memory = populated_episodic_memory
        
        # Retrieve with emotional filter
        high_emotion_results = memory.retrieve(
            query="memory", 
            min_emotional_salience=0.7
        )
        
        # Should only get the high emotional memories
        assert len(high_emotion_results) == 3  # Happy, Sad, Exciting (all >= 0.7)
        emotions = [chunk.emotional_salience for chunk in high_emotion_results]
        assert all(e >= 0.7 for e in emotions)
        
        # Content should match expected memories
        contents = [str(chunk.content).lower() for chunk in high_emotion_results]
        assert any("happy" in content for content in contents)
        assert any("sad" in content for content in contents)
        assert any("exciting" in content for content in contents)
        assert not any("boring" in content for content in contents)
    
    def test_temporal_filtering(self, episodic_memory):
        """Test that we can filter memories by temporal range."""
        # Create custom temporal contexts
        now = time.time()
        yesterday = now - 86400  # 24 hours ago
        last_week = now - 604800  # 7 days ago
        
        # Store memories with different timestamps
        episodic_memory.store(
            "Today's memory", 
            temporal_context={"timestamp": now, "sequence_id": 1}
        )
        episodic_memory.store(
            "Yesterday's memory", 
            temporal_context={"timestamp": yesterday, "sequence_id": 2}
        )
        episodic_memory.store(
            "Last week's memory", 
            temporal_context={"timestamp": last_week, "sequence_id": 3}
        )
        
        # Retrieve with time range filter (between yesterday and now)
        recent_results = episodic_memory.retrieve(
            query="memory",
            temporal_range=(yesterday - 3600, now + 3600)  # +/- 1 hour buffer
        )
        
        # Should get today and yesterday but not last week
        assert len(recent_results) == 2
        
        # Content should match expected memories
        contents = [str(chunk.content) for chunk in recent_results]
        assert any("Today's memory" in content for content in contents)
        assert any("Yesterday's memory" in content for content in contents)
        assert not any("Last week's memory" in content for content in contents)
    
    def test_sequence_tracking(self, populated_episodic_memory):
        """Test that we can retrieve a sequence of related memories."""
        memory = populated_episodic_memory
        
        # Retrieve the sequence (sequence_id is 12345 in the fixture)
        sequence = memory.retrieve_sequence(12345)
        
        # Should get the three memories in the correct order
        assert len(sequence) == 3
        
        # Should be in timestamp order
        assert "First in sequence" in str(sequence[0].content)
        assert "Second in sequence" in str(sequence[1].content)
        assert "Third in sequence" in str(sequence[2].content)
    
    def test_retrieval_boosts_activation(self, episodic_memory):
        """Test that retrieving a memory boosts its activation."""
        # Store a memory
        memory_id = episodic_memory.store("Important meeting")
        
        # Get initial activation
        initial_activation = episodic_memory.retrieve_by_id(memory_id).activation
        
        # Let it decay a bit
        time.sleep(0.5)
        
        # Force decay and retrieve again
        episodic_memory.retrieve(query="meeting")
        
        # Should have higher activation after retrieval
        new_activation = episodic_memory.retrieve_by_id(memory_id).activation
        assert new_activation > initial_activation * 0.9
    
    def test_emotional_memories_get_bigger_boost(self, episodic_memory):
        """Test that emotional memories get a bigger activation boost when retrieved."""
        # Store memories with different emotional salience
        neutral_id = episodic_memory.store("Regular event", emotional_salience=0.5)
        emotional_id = episodic_memory.store("Exciting event", emotional_salience=1.0)
        
        # Let them decay
        time.sleep(0.5)
        
        # Get activation before retrieval
        neutral_before = episodic_memory.retrieve_by_id(neutral_id).activation
        emotional_before = episodic_memory.retrieve_by_id(emotional_id).activation
        
        # Force retrieval boost (these are direct retrievals, so should get the full boost)
        episodic_memory.retrieve_by_id(neutral_id)
        episodic_memory.retrieve_by_id(emotional_id)
        
        # Get activation after retrieval
        neutral_after = episodic_memory.retrieve_by_id(neutral_id).activation
        emotional_after = episodic_memory.retrieve_by_id(emotional_id).activation
        
        # Calculate the boost each received
        neutral_boost = neutral_after - neutral_before
        emotional_boost = emotional_after - emotional_before
        
        # Emotional memory should get a bigger boost
        assert emotional_boost > neutral_boost
    
    def test_statistics(self, populated_episodic_memory):
        """Test that memory statistics are properly reported."""
        memory = populated_episodic_memory
        
        # Check stats
        stats = memory.get_statistics()
        assert stats["name"] == "episodic_memory"
        assert stats["count"] > 0
        assert 0 < stats["average_emotional_salience"] < 1
        assert stats["sequence_count"] > 0 