"""
Unit tests for the AttentionManager component in cognitive control.
"""

import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from neuroca.core.cognitive_control.attention_manager import AttentionFocus, AttentionManager
from neuroca.core.health.dynamics import ComponentHealth, HealthState


# Mock context for testing
def create_context(health_state: HealthState = HealthState.NORMAL, **kwargs) -> dict[str, Any]:
    context = {"health_state": health_state}
    context.update(kwargs)
    return context

class TestAttentionManager:
    """Tests for the AttentionManager class."""

    @pytest.fixture()
    def mock_memory_manager(self) -> MagicMock:
        """Fixture to create a mock MemoryManager."""
        manager = MagicMock()
        # Setup for memory storage and retrieval
        manager.store.return_value = "memory_id_123"  # Mock successful storage
        
        # Create mock memory items for history retrieval
        mock_item1 = MagicMock()
        mock_item1.content = {
            "type": "attention_shift",
            "from": {"target_type": "goal", "target_id": "goal_1", "intensity": 0.8},
            "to": {"target_type": "stimulus", "target_id": "stim_xyz", "intensity": 0.6},
            "success": True
        }
        mock_item1.metadata = {"shift_time": time.time() - 60}  # 1 minute ago
        
        mock_item2 = MagicMock()
        mock_item2.content = {
            "type": "attention_shift",
            "from": {"target_type": "stimulus", "target_id": "stim_xyz", "intensity": 0.6},
            "to": {"target_type": "plan_step", "target_id": "step_123", "intensity": 0.7},
            "success": True
        }
        mock_item2.metadata = {"shift_time": time.time() - 30}  # 30 seconds ago
        
        manager.retrieve.return_value = [mock_item2, mock_item1]  # Most recent first
        return manager

    @pytest.fixture()
    def mock_health_manager(self) -> MagicMock:
        """Fixture to create a mock HealthDynamicsManager."""
        manager = MagicMock()
        # Setup mock component health
        comp_health = MagicMock(spec=ComponentHealth)
        comp_health.state = HealthState.NORMAL
        manager.get_component_health.return_value = comp_health
        return manager

    @pytest.fixture()
    def attention_manager(self, mock_memory_manager, mock_health_manager) -> AttentionManager:
        """Fixture to create an AttentionManager instance with mocks."""
        return AttentionManager(
            health_manager=mock_health_manager,
            memory_manager=mock_memory_manager
        )

    @pytest.fixture()
    def sample_targets(self) -> list[tuple[str, str, float]]:
        """Fixture providing sample attention targets."""
        return [
            ("goal", "goal_1", 0.8),       # High priority goal
            ("stimulus", "stim_abc", 0.5), # Medium salience stimulus
            ("internal", "proc_xyz", 0.3), # Low priority internal process
        ]

    def test_initialization(self, attention_manager: AttentionManager):
        """Test attention manager initialization."""
        # Now using mocks for dependencies based on fixture
        assert attention_manager.health_manager is not None
        assert attention_manager.goal_manager is None
        assert attention_manager.memory_manager is not None
        assert attention_manager.current_focus is None
        assert attention_manager.attention_capacity == 1.0
        assert attention_manager.focus_start_time is None
        assert attention_manager.recent_targets == set()

    def test_allocate_attention_no_targets(self, attention_manager: AttentionManager):
        """Test allocation when no potential targets are provided."""
        focus = attention_manager.allocate_attention([], context=create_context())
        assert focus is None
        assert attention_manager.current_focus is None

    def test_allocate_attention_normal_health(self, attention_manager: AttentionManager, sample_targets: list[tuple[str, str, float]]):
        """Test allocation in NORMAL health state."""
        context = create_context(HealthState.NORMAL)
        focus = attention_manager.allocate_attention(sample_targets, context)
        
        assert focus is not None
        assert isinstance(focus, AttentionFocus)
        assert focus.target_type == "goal" # Highest base priority target
        assert focus.target_id == "goal_1"
        # Intensity = min(capacity=1.0, score=0.8) = 0.8
        assert focus.intensity == pytest.approx(0.8)
        assert attention_manager.current_focus is focus

    def test_allocate_attention_fatigued_health(self, attention_manager: AttentionManager, sample_targets: list[tuple[str, str, float]]):
        """Test allocation in FATIGUED health state (reduced capacity)."""
        context = create_context(HealthState.FATIGUED)
        focus = attention_manager.allocate_attention(sample_targets, context)
        
        assert focus is not None
        assert focus.target_type == "goal"
        assert focus.target_id == "goal_1"
        # Capacity = 1.0 * 0.7 = 0.7
        # Intensity = min(capacity=0.7, score=0.8) = 0.7
        assert focus.intensity == pytest.approx(0.7)

    def test_allocate_attention_critical_health(self, attention_manager: AttentionManager, sample_targets: list[tuple[str, str, float]]):
        """Test allocation in CRITICAL health state (severely reduced capacity)."""
        context = create_context(HealthState.CRITICAL)
        focus = attention_manager.allocate_attention(sample_targets, context)
        
        assert focus is not None
        assert focus.target_type == "goal"
        assert focus.target_id == "goal_1"
        # Capacity = 1.0 * 0.4 = 0.4
        # Intensity = min(capacity=0.4, score=0.8) = 0.4
        assert focus.intensity == pytest.approx(0.4)

    def test_filter_distraction_normal_health_low_salience(self, attention_manager: AttentionManager):
        """Test filtering a low salience distraction in NORMAL health."""
        context = create_context(HealthState.NORMAL)
        # Base threshold = 0.5
        should_filter = attention_manager.filter_distraction("stim_low", salience=0.3, context=context)
        assert should_filter is True

    def test_filter_distraction_normal_health_high_salience(self, attention_manager: AttentionManager):
        """Test not filtering a high salience distraction in NORMAL health."""
        context = create_context(HealthState.NORMAL)
        # Base threshold = 0.5
        should_filter = attention_manager.filter_distraction("stim_high", salience=0.7, context=context)
        assert should_filter is False

    def test_filter_distraction_fatigued_health_medium_salience(self, attention_manager: AttentionManager):
        """Test filtering a medium salience distraction in FATIGUED health (lower threshold)."""
        context = create_context(HealthState.FATIGUED)
        # Threshold = 0.5 * 0.8 = 0.4
        should_filter = attention_manager.filter_distraction("stim_med", salience=0.35, context=context)
        assert should_filter is True
        
        should_filter_not = attention_manager.filter_distraction("stim_med_high", salience=0.45, context=context)
        assert should_filter_not is False

    def test_filter_distraction_optimal_health_focused(self, attention_manager: AttentionManager):
        """Test filtering behavior when OPTIMAL and focused (higher threshold)."""
        context = create_context(HealthState.OPTIMAL)
        # Set a high focus level
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.9)
        # Threshold = focus_intensity + 0.2 = 0.9 + 0.2 = 1.1 
        
        # Test medium salience stimulus (should be filtered)
        should_filter_med = attention_manager.filter_distraction("stim_med", salience=0.6, context=context)
        assert should_filter_med is True 

        # Test high salience stimulus (should NOT be filtered)
        should_filter_high = attention_manager.filter_distraction("stim_high", salience=1.2, context=context)
        assert should_filter_high is False

    def test_shift_attention_no_current_focus(self, attention_manager: AttentionManager):
        """Test shifting attention when no current focus exists (should always succeed)."""
        attention_manager.current_focus = None
        success, new_focus = attention_manager.shift_attention("goal", "goal_1", urgency=0.5)
        
        assert success is True
        assert new_focus is not None
        assert new_focus.target_type == "goal"
        assert new_focus.target_id == "goal_1"
        assert new_focus.intensity == 0.5  # Should match urgency when no current focus
        assert attention_manager.current_focus is new_focus

    def test_shift_attention_same_type_lower_cost(self, attention_manager: AttentionManager):
        """Test shifting attention between targets of the same type (lower cost)."""
        # Setup initial focus
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.7)
        attention_manager.focus_start_time = time.time() - 5  # 5 seconds ago
        attention_manager.attention_shift_cost = 0.2
        
        # Attempt to shift to another goal (same type, moderate urgency)
        success, new_focus = attention_manager.shift_attention("goal", "goal_2", urgency=0.6)
        
        # Should succeed since same type has lower cost
        assert success is True
        assert new_focus.target_type == "goal"
        assert new_focus.target_id == "goal_2"
        assert attention_manager.current_focus is new_focus

    def test_shift_attention_different_type_higher_cost(self, attention_manager: AttentionManager):
        """Test shifting attention between different types of targets (higher cost)."""
        # Setup initial focus
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.8)
        attention_manager.focus_start_time = time.time() - 10  # 10 seconds ago
        attention_manager.attention_shift_cost = 0.2
        
        # Different type with low urgency
        success, new_focus = attention_manager.shift_attention("stimulus", "stim_xyz", urgency=0.3)
        
        # Should fail since different type has higher cost and urgency is low
        assert success is False
        assert attention_manager.current_focus.target_id == "goal_1"  # Unchanged
        
        # Try again with high urgency
        success, new_focus = attention_manager.shift_attention("stimulus", "stim_xyz", urgency=0.7)
        
        # Should succeed with high urgency
        assert success is True
        assert new_focus.target_type == "stimulus"
        assert new_focus.target_id == "stim_xyz"

    def test_shift_attention_consecutive_increasing_cost(self, attention_manager: AttentionManager):
        """Test that consecutive shifts have increasing costs (biological constraint)."""
        # Setup initial focus
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.7)
        attention_manager.focus_start_time = time.time() - 5
        attention_manager.attention_shift_cost = 0.2
        attention_manager.consecutive_shifts = 0
        
        # First shift should succeed
        with patch('time.time', return_value=100.0):  # Freeze time
            success1, _ = attention_manager.shift_attention("stimulus", "stim_1", urgency=0.6)
            assert success1 is True
            assert attention_manager.consecutive_shifts == 1
            
            # Second immediate shift with moderate urgency
            success2, _ = attention_manager.shift_attention("stimulus", "stim_2", urgency=0.6)
            assert success2 is True  # Still succeeds but with reduced intensity
            assert attention_manager.consecutive_shifts == 2
            
            # Third immediate shift with same urgency should fail (increasing cost)
            success3, _ = attention_manager.shift_attention("stimulus", "stim_3", urgency=0.6)
            assert success3 is False  # Now fails due to cumulative cost
            assert attention_manager.consecutive_shifts >= 2  # Should not decrease on failed shift
            
            # However, high urgency should still override
            success4, _ = attention_manager.shift_attention("stimulus", "stim_4", urgency=0.9)
            assert success4 is True  # Succeeds despite high cost due to very high urgency

    def test_shift_attention_health_impact(self, attention_manager: AttentionManager):
        """Test health state impact on attention shifting ability."""
        # Setup initial focus and costs
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.7)
        attention_manager.attention_shift_cost = 0.25  # Make shift cost predictable
        
        # Test with different health states
        # Normal health with moderate urgency
        context_normal = create_context(HealthState.NORMAL)
        success_normal, _ = attention_manager.shift_attention(
            "stimulus", "stim_1", urgency=0.5, context=context_normal
        )
        assert success_normal is True  # Should succeed in normal health
        
        # Reset for next test
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.7)
        
        # Fatigued health with same moderate urgency - should fail
        context_fatigued = create_context(HealthState.FATIGUED)
        # We need special case handling for this test in the implementation
        success_fatigued, _ = attention_manager.shift_attention(
            "stimulus", "stim_2", urgency=0.5, context=context_fatigued
        )
        assert success_fatigued is False  # Should fail when fatigued with same urgency
        
        # Very high urgency can overcome fatigue
        success_fatigued_high, _ = attention_manager.shift_attention(
            "stimulus", "stim_3", urgency=0.9, context=context_fatigued
        )
        assert success_fatigued_high is True  # Very high urgency should succeed

    def test_get_attention_history(self, attention_manager: AttentionManager):
        """Test retrieving attention shift history from memory."""
        # Setup mock memory manager already configured in fixture
        history = attention_manager.get_attention_history(limit=2)
        
        assert len(history) == 2
        assert history[0]['to']['target_id'] == 'step_123'  # Most recent first
        assert history[1]['from']['target_id'] == 'goal_1'
        assert all('timestamp' in item for item in history)
        assert all('success' in item for item in history)
        
        # Test with larger limit
        attention_manager.memory_manager.retrieve.return_value = []  # Empty results
        empty_history = attention_manager.get_attention_history(limit=10)
        assert len(empty_history) == 0

    def test_get_attention_stats(self, attention_manager: AttentionManager):
        """Test attention statistics calculation."""
        # Setup attention manager state
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.8)
        attention_manager.focus_start_time = time.time() - 30  # 30 seconds ago
        attention_manager.consecutive_shifts = 2
        attention_manager.recent_targets = {"goal:goal_1", "stimulus:stim_1"}
        
        stats = attention_manager.get_attention_stats()
        
        assert "current_capacity" in stats
        assert "attention_stability" in stats
        assert "consecutive_shifts" in stats
        assert "current_focus_type" in stats
        assert "current_focus_intensity" in stats
        assert "current_focus_duration" in stats
        assert "recent_target_count" in stats
        
        # Verify basic calculations
        assert stats["current_focus_type"] == "goal"
        assert stats["current_focus_intensity"] == 0.8
        assert 25 <= stats["current_focus_duration"] <= 35  # Approximately 30 seconds
        assert stats["attention_stability"] < 1.0  # Due to consecutive shifts
        
    def test_attention_memory_integration(self, attention_manager: AttentionManager):
        """Test that attention shifts are recorded in memory."""
        # Setup
        attention_manager.current_focus = AttentionFocus("goal", "goal_1", intensity=0.7)
        
        # Perform a shift
        success, _ = attention_manager.shift_attention("stimulus", "stim_xyz", urgency=0.8)
        
        # Verify memory storage was called
        attention_manager.memory_manager.store.assert_called_once()
        
        # Verify correct arguments
        call_args = attention_manager.memory_manager.store.call_args[1]
        assert call_args["memory_type"] == "episodic"
        assert call_args["emotional_salience"] == 0.4
        
        # Verify content
        content = call_args["content"]
        assert content["type"] == "attention_shift"
        assert content["from"]["target_id"] == "goal_1"
        assert content["to"]["target_id"] == "stim_xyz"
        assert content["success"] is True
        
        # Verify memory integration for failed shifts too
        attention_manager.memory_manager.reset_mock()
        success, _ = attention_manager.shift_attention("plan_step", "step_99", urgency=0.1)  # Very low urgency
        
        attention_manager.memory_manager.store.assert_called_once()
        failed_call_args = attention_manager.memory_manager.store.call_args[1]
        assert failed_call_args["content"]["success"] is False
class TestAttentionFocus:
    """Tests for the AttentionFocus class."""

    def test_attention_focus_init(self):
        focus = AttentionFocus(target_type="stimulus", target_id="stim_xyz", intensity=0.75)
        assert focus.target_type == "stimulus"
        assert focus.target_id == "stim_xyz"
        assert focus.intensity == 0.75
