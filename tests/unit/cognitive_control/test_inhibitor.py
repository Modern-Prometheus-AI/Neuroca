"""
Unit tests for the Inhibitor component in cognitive control.
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import MagicMock

from neuroca.core.cognitive_control.inhibitor import Inhibitor, InhibitionTarget
from neuroca.core.health.dynamics import HealthState
# Mock GoalManager and Goal for testing goal conflicts
from neuroca.core.cognitive_control.goal_manager import GoalManager, Goal, GoalStatus

# Mock context for testing
def create_context(health_state: HealthState = HealthState.NORMAL, **kwargs) -> Dict[str, Any]:
    context = {"health_state": health_state}
    context.update(kwargs)
    return context

# Mock GoalManager setup
@pytest.fixture
def mock_goal_manager() -> GoalManager:
    manager = GoalManager()
    # Add some goals for conflict testing
    # Use simpler goal description for easier matching in placeholder logic
    goal1 = manager.add_goal("safety", priority=1) 
    goal2 = manager.add_goal("explore area", priority=5)
    if goal1: manager.activate_goal(goal1.id) # Activate safety goal
    return manager

class TestInhibitor:
    """Tests for the Inhibitor class."""

    @pytest.fixture
    def inhibitor(self, mock_goal_manager: GoalManager) -> Inhibitor:
        """Fixture to create an Inhibitor instance with mocked GoalManager."""
        # Pass the mocked goal manager
        return Inhibitor(goal_manager=mock_goal_manager, health_manager=None, memory_manager=None)

    @pytest.fixture
    def sample_target(self) -> InhibitionTarget:
        """Fixture for a sample inhibition target."""
        return InhibitionTarget(target_type="action", target_id="act_123", description="perform risky maneuver", activation=0.7)

    def test_initialization(self, inhibitor: Inhibitor):
        """Test inhibitor initialization."""
        assert inhibitor.goal_manager is not None # Should have the mock
        assert inhibitor.health_manager is None
        assert inhibitor.memory_manager is None

    def test_should_inhibit_no_criteria_met(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test that inhibition is False when no criteria are met."""
        context = create_context(HealthState.NORMAL)
        # Modify target description so it doesn't trigger default rules
        sample_target.description = "perform standard maneuver" 
        should = inhibitor.should_inhibit(sample_target, context)
        assert should is False

    def test_should_inhibit_stop_signal(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to a 'stop' signal in context."""
        context = create_context(signal="stop")
        should = inhibitor.should_inhibit(sample_target, context)
        assert should is True

    def test_should_inhibit_goal_conflict_safety(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to conflict with active 'safety' goal (via context flag)."""
        # sample_target description is "perform risky maneuver"
        context = create_context(high_priority_goal="safety") 
        should = inhibitor.should_inhibit(sample_target, context)
        assert should is True

    def test_should_inhibit_goal_conflict_negation(self, inhibitor: Inhibitor):
        """Test inhibition due to conflict with active goal (negation)."""
        # Assumes mock_goal_manager has "safety" active (priority 1)
        
        # Test "do not [goal]"
        target_do_not = InhibitionTarget(target_type="action", target_id="act_456", description="do not safety", activation=0.8) 
        context = create_context()
        should_do_not = inhibitor.should_inhibit(target_do_not, context)
        assert should_do_not is True 
        
        # Test "avoid [goal]"
        target_avoid = InhibitionTarget(target_type="action", target_id="act_789", description="avoid safety", activation=0.8)
        should_avoid = inhibitor.should_inhibit(target_avoid, context)
        assert should_avoid is True
        
        # Test case sensitivity (should still match)
        target_case = InhibitionTarget(target_type="action", target_id="act_111", description="Avoid Safety", activation=0.8)
        should_case = inhibitor.should_inhibit(target_case, context)
        assert should_case is True

        # Test non-conflicting
        target_non_conflict = InhibitionTarget(target_type="action", target_id="act_222", description="ensure safety", activation=0.8)
        should_non_conflict = inhibitor.should_inhibit(target_non_conflict, context)
        assert should_non_conflict is False # Assuming no other rules trigger inhibition

    def test_should_inhibit_impaired_health(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to IMPAIRED health state for high activation target."""
        context = create_context(HealthState.IMPAIRED)
        sample_target.activation = 0.6 # Activation > 0.5
        should = inhibitor.should_inhibit(sample_target, context)
        assert should is True

    def test_should_not_inhibit_impaired_health_low_activation(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test no inhibition in IMPAIRED state for low activation target."""
        context = create_context(HealthState.IMPAIRED)
        sample_target.activation = 0.4 # Activation <= 0.5
        should = inhibitor.should_inhibit(sample_target, context)
        assert should is False

    def test_should_inhibit_fatigued_health(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to FATIGUED health state for very high activation target."""
        context = create_context(HealthState.FATIGUED)
        sample_target.activation = 0.9 # Activation > 0.8
        should = inhibitor.should_inhibit(sample_target, context)
        assert should is True

    def test_should_not_inhibit_fatigued_health_medium_activation(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test no inhibition in FATIGUED state for medium activation target."""
        context = create_context(HealthState.FATIGUED)
        sample_target.activation = 0.7 # Activation <= 0.8
        should = inhibitor.should_inhibit(sample_target, context)
        assert should is False

    # Placeholder test for learned constraints (assuming memory manager integration)
    # def test_should_inhibit_learned_constraint(self, inhibitor_with_mock_memory: Inhibitor, sample_target: InhibitionTarget):
    #     """Test inhibition based on a learned constraint from memory."""
    #     # Setup mock memory manager to return a constraint
    #     mock_constraint = MagicMock()
    #     mock_constraint.content = "never perform risky maneuver"
    #     inhibitor_with_mock_memory.memory_manager.retrieve.return_value = [mock_constraint]
        
    #     context = create_context()
    #     should = inhibitor_with_mock_memory.should_inhibit(sample_target, context)
        
    #     inhibitor_with_mock_memory.memory_manager.retrieve.assert_called_once()
    #     assert should is True

class TestInhibitionTarget:
    """Tests for the InhibitionTarget class."""

    def test_inhibition_target_init(self):
        target = InhibitionTarget(target_type="plan", target_id="plan_abc", description="Execute complex plan", activation=0.9)
        assert target.target_type == "plan"
        assert target.target_id == "plan_abc"
        assert target.description == "Execute complex plan"
        assert target.activation == 0.9
