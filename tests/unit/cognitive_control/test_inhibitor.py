"""
Unit tests for the Inhibitor component in cognitive control.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Mock GoalManager and Goal for testing goal conflicts
from neuroca.core.cognitive_control.goal_manager import Goal, GoalManager, GoalStatus
from neuroca.core.cognitive_control.inhibitor import InhibitionDecision, InhibitionTarget, Inhibitor
from neuroca.core.health.dynamics import ComponentHealth, HealthState
from neuroca.memory.manager import MemoryManager


# Mock context for testing
def create_context(health_state: HealthState = HealthState.NORMAL, **kwargs) -> dict[str, Any]:
    context = {"health_state": health_state}
    context.update(kwargs)
    return context

# Mock fixtures
@pytest.fixture()
def mock_memory_manager() -> MagicMock:
    """Create a mocked MemoryManager."""
    manager = MagicMock(spec=MemoryManager)
    
    # Setup for successful store operations
    manager.store.return_value = "memory_id_123"
    
    # Setup for retrieve operations - constraints
    constraint = MagicMock()
    constraint.content = {
        "type": "constraint",
        "applies_to": "dangerous action",
        "action": "prohibit",
        "confidence": 0.8,
        "description": "Never perform dangerous actions"
    }
    
    # Setup for retrieve operations - experiences
    experience1 = MagicMock()
    experience1.content = {
        "type": "memory", 
        "action": "risky test",
        "outcome": "negative"
    }
    experience2 = MagicMock()
    experience2.content = {
        "type": "memory",
        "action": "risky test",
        "outcome": "negative"
    }
    experience3 = MagicMock()
    experience3.content = {
        "type": "memory",
        "action": "risky test",
        "outcome": "negative"
    }
    
    # Make retrieve return different results based on the query
    def mock_retrieve(query, memory_type, **kwargs):
        if "constraint" in query and "dangerous action" in query:
            return [constraint]
        elif "outcome:negative" in query and "risky test" in query:
            return [experience1, experience2, experience3]
        else:
            return []
            
    manager.retrieve.side_effect = mock_retrieve
    
    return manager

@pytest.fixture()
def mock_health_manager() -> MagicMock:
    """Create a mocked HealthDynamicsManager."""
    manager = MagicMock()
    
    # Default component health
    comp_health = MagicMock(spec=ComponentHealth)
    comp_health.state = HealthState.NORMAL
    
    # Make get_component_health return the mock health
    manager.get_component_health.return_value = comp_health
    
    return manager

# Mock GoalManager setup
@pytest.fixture()
def mock_goal_manager() -> MagicMock:
    """Create a mocked GoalManager with test goals."""
    manager = MagicMock(spec=GoalManager)
    
    # Create mock goals
    safety_goal = MagicMock(spec=Goal)
    safety_goal.id = "goal1"
    safety_goal.description = "safety"
    safety_goal.priority = 1.0
    safety_goal.status = GoalStatus.ACTIVE
    
    explore_goal = MagicMock(spec=Goal)
    explore_goal.id = "goal2"
    explore_goal.description = "explore area"
    explore_goal.priority = 0.5
    explore_goal.status = GoalStatus.ACTIVE
    
    # Make get_active_goals return the safety goal
    manager.get_active_goals.return_value = [safety_goal, explore_goal]
    
    # Give safety_goal a conflicts_with method - but only for certain tests
    def mock_conflicts_with(target):
        # Skip semantic conflict check for specific test cases
        if hasattr(target, 'for_health_test') and target.for_health_test:
            return False
        if hasattr(target, 'context_hint') and target.description == "perform risky maneuver" and "high_priority_goal" in target.context_hint:
            # For test_should_inhibit_goal_conflict_safety
            return False
        return "risky" in target.description.lower()
    safety_goal.conflicts_with = mock_conflicts_with
    
    return manager

class TestInhibitor:
    """Tests for the Inhibitor class."""

    @pytest.fixture()
    def inhibitor(self, mock_goal_manager, mock_health_manager, mock_memory_manager) -> Inhibitor:
        """Fixture to create an Inhibitor instance with mocked dependencies."""
        return Inhibitor(
            goal_manager=mock_goal_manager, 
            health_manager=mock_health_manager, 
            memory_manager=mock_memory_manager
        )

    @pytest.fixture()
    def sample_target(self) -> InhibitionTarget:
        """Fixture for a sample inhibition target."""
        return InhibitionTarget(target_type="action", target_id="act_123", description="perform risky maneuver", activation=0.7)

    def test_initialization(self, inhibitor: Inhibitor):
        """Test inhibitor initialization."""
        assert inhibitor.goal_manager is not None # Should have the mock
        assert inhibitor.health_manager is not None
        assert inhibitor.memory_manager is not None
        assert inhibitor.base_inhibition_threshold == 0.5
        assert inhibitor.recent_decisions == []
        assert inhibitor.active_inhibitions == set()
        assert "total_evaluations" in inhibitor.inhibition_metrics

    def test_should_inhibit_no_criteria_met(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test that inhibition is False when no criteria are met."""
        context = create_context(HealthState.NORMAL)
        # Modify target description so it doesn't trigger default rules
        sample_target.description = "perform standard maneuver" 
        sample_target.activation = 0.6  # Above the threshold
        
        # New API returns (bool, confidence, reason)
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is False
        assert confidence >= 0.5  # Should have at least moderate confidence
        assert reasoning == "Target passes all inhibition checks"
        assert len(inhibitor.recent_decisions) == 1

    def test_should_inhibit_stop_signal(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to a 'stop' signal in context."""
        context = create_context(signal="stop")
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is True
        assert confidence > 0.9  # Very high confidence for stop signals
        assert reasoning == "Stop signal received"
        assert sample_target.target_id in inhibitor.active_inhibitions

    def test_should_inhibit_goal_conflict_safety(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to conflict with active 'safety' goal (via context flag)."""
        # sample_target description is "perform risky maneuver"
        context = create_context(high_priority_goal="safety") 
        
        # Set a hint for the conflicts_with method
        sample_target.context_hint = "high_priority_goal"
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is True
        assert confidence >= 0.7  # Should have high confidence
        assert "Conflicts with high-priority safety goal" in reasoning
        assert sample_target.target_id in inhibitor.active_inhibitions

    def test_should_inhibit_goal_conflict_negation(self, inhibitor: Inhibitor):
        """Test inhibition due to conflict with active goal (negation)."""
        # Assumes mock_goal_manager has "safety" active (priority 1)
        
        # Test "do not [goal]"
        target_do_not = InhibitionTarget(target_type="action", target_id="act_456", description="do not safety", activation=0.8) 
        context = create_context()
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(target_do_not, context)
        assert inhibit_decision is True 
        assert confidence >= 0.7
        assert "Conflicts with active goal" in reasoning
        
        # Test "avoid [goal]"
        target_avoid = InhibitionTarget(target_type="action", target_id="act_789", description="avoid safety", activation=0.8)
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(target_avoid, context)
        assert inhibit_decision is True
        assert confidence >= 0.7
        assert "Conflicts with active goal" in reasoning
        
        # Test case sensitivity (should still match)
        target_case = InhibitionTarget(target_type="action", target_id="act_111", description="Avoid Safety", activation=0.8)
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(target_case, context)
        assert inhibit_decision is True
        assert confidence >= 0.7
        assert "Conflicts with active goal" in reasoning

        # Test non-conflicting
        target_non_conflict = InhibitionTarget(target_type="action", target_id="act_222", description="ensure safety", activation=0.8)
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(target_non_conflict, context)
        assert inhibit_decision is False  # Assuming no other rules trigger inhibition

    def test_should_inhibit_impaired_health(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to IMPAIRED health state for high activation target."""
        context = create_context(HealthState.IMPAIRED)
        sample_target.activation = 0.6  # Activation > 0.5
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is True
        assert confidence >= 0.7
        assert "Health state" in reasoning
        assert "high-activation" in reasoning.lower()

    def test_should_not_inhibit_impaired_health_low_activation(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test no inhibition in IMPAIRED state for low activation target."""
        context = create_context(HealthState.IMPAIRED)
        sample_target.activation = 0.4  # Activation <= 0.5
        
        # Bypass goal checks for this health-specific test
        sample_target.for_health_test = True
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is False

    def test_should_inhibit_fatigued_health(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to FATIGUED health state for very high activation target."""
        context = create_context(HealthState.FATIGUED)
        sample_target.activation = 0.9  # Activation > 0.8
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is True
        assert confidence >= 0.6
        assert "Health state" in reasoning
        assert "demanding actions" in reasoning

    def test_should_not_inhibit_fatigued_health_medium_activation(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test no inhibition in FATIGUED state for medium activation target."""
        context = create_context(HealthState.FATIGUED)
        sample_target.activation = 0.7  # Activation <= 0.8
        
        # Bypass goal checks for this health-specific test
        sample_target.for_health_test = True
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is False

    def test_should_inhibit_learned_constraint(self, inhibitor: Inhibitor):
        """Test inhibition based on a learned constraint from memory."""
        # Create a target that matches our mocked constraint
        target = InhibitionTarget(
            target_type="action", 
            target_id="act_dangerous", 
            description="dangerous action", 
            activation=0.7
        )
        
        context = create_context()
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(target, context)
        
        # Should match the mocked constraint
        assert inhibit_decision is True
        assert confidence >= 0.7  # Should have high confidence for constraints
        assert "Violates learned constraint" in reasoning
        
    def test_should_inhibit_based_on_past_negative_experiences(self, inhibitor: Inhibitor):
        """Test inhibition based on multiple past negative experiences."""
        # Create a target that matches our mocked negative experiences
        target = InhibitionTarget(
            target_type="action", 
            target_id="act_risky_test", 
            description="risky test", 
            activation=0.7
        )
        
        context = create_context()
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(target, context)
        
        # Should match the mocked negative experiences
        assert inhibit_decision is True
        assert confidence >= 0.6  # Should have moderate confidence for experience-based decisions
        assert "negative outcomes" in reasoning
        assert "3 times" in reasoning  # Should mention the number of past negative outcomes
        
    def test_should_inhibit_below_threshold(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test inhibition due to activation below threshold."""
        context = create_context(HealthState.NORMAL)
        # Make sure no other inhibition criteria apply
        sample_target.description = "standard safe action"
        # Set activation low enough to be below threshold
        sample_target.activation = 0.3  # Below default threshold of 0.5
        
        inhibit_decision, confidence, reasoning = inhibitor.should_inhibit(sample_target, context)
        
        assert inhibit_decision is True
        assert confidence >= 0.5
        assert "below inhibition threshold" in reasoning
        
    def test_inhibition_metrics_update(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test that inhibition metrics are updated after evaluations."""
        # Initial state
        initial_evaluations = inhibitor.inhibition_metrics["total_evaluations"]
        initial_inhibitions = inhibitor.inhibition_metrics["total_inhibitions"]
        
        # Make a call that should result in inhibition
        context = create_context(signal="stop")  # Using stop signal for guaranteed inhibition
        inhibit_decision, _, _ = inhibitor.should_inhibit(sample_target, context)
        
        # Verify metrics update
        assert inhibitor.inhibition_metrics["total_evaluations"] == initial_evaluations + 1
        assert inhibitor.inhibition_metrics["total_inhibitions"] == initial_inhibitions + 1
        assert inhibitor.inhibition_metrics["average_confidence"] > 0
        assert inhibitor.inhibition_metrics["average_response_time"] >= 0  # Can be very fast in tests
        
    def test_adaptive_inhibition_threshold(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test that inhibition threshold adapts based on factors like health state."""
        # Calculate threshold in NORMAL state
        context_normal = create_context(HealthState.NORMAL)
        threshold_normal = inhibitor._calculate_inhibition_threshold(sample_target, context_normal)
        
        # Calculate threshold in CRITICAL state
        context_critical = create_context(HealthState.CRITICAL)
        threshold_critical = inhibitor._calculate_inhibition_threshold(sample_target, context_critical)
        
        # Threshold should be higher (more likely to inhibit) in CRITICAL state
        assert threshold_critical > threshold_normal
        
        # Test with emergency
        context_emergency = create_context(HealthState.NORMAL, emergency=True)
        threshold_emergency = inhibitor._calculate_inhibition_threshold(sample_target, context_emergency)
        
        # Threshold should be lower (less likely to inhibit) in emergency situations
        assert threshold_emergency < threshold_normal
        
    def test_report_outcome_updates_metrics(self, inhibitor: Inhibitor, sample_target: InhibitionTarget):
        """Test that reporting outcomes updates the performance metrics."""
        # Make an inhibition decision
        context = create_context(signal="stop")
        inhibitor.should_inhibit(sample_target, context)
        
        # Report incorrect outcome (we inhibited something we shouldn't have)
        inhibitor.report_outcome(sample_target.target_id, "Action was actually safe", success=False)
        
        # Verify false_inhibitions metric increased
        assert inhibitor.inhibition_metrics["false_inhibitions"] == 1
        
        # Verify memory storage was called
        inhibitor.memory_manager.store.assert_called()
        
    def test_consolidate_inhibition_patterns(self, inhibitor: Inhibitor):
        """Test that consistent patterns are consolidated into semantic memory."""
        # Create multiple consistent decisions
        target = InhibitionTarget("action", "act_123", "dangerous test", activation=0.7)
        
        # Create mock decisions (all with inhibit=True)
        decision1 = InhibitionDecision(target, True, "Test reason 1", 0.8, {})
        decision2 = InhibitionDecision(target, True, "Test reason 2", 0.7, {})
        decision3 = InhibitionDecision(target, True, "Test reason 3", 0.9, {})
        
        # Add to recent decisions
        inhibitor.recent_decisions = [decision1, decision2, decision3]
        
        # We'll mock _pattern_exists_in_memory to return False (pattern doesn't exist yet)
        with patch.object(inhibitor, '_pattern_exists_in_memory', return_value=False):
            # This should create a new constraint
            inhibitor._consolidate_inhibition_patterns()
            
            # Verify memory storage was called for a new constraint
            inhibitor.memory_manager.store.assert_called()
            
            # Verify the last call was to store a constraint
            last_call_args = inhibitor.memory_manager.store.call_args[1]
            assert last_call_args["memory_type"] == "semantic"
            assert last_call_args["content"]["type"] == "constraint"
            assert last_call_args["content"]["action"] == "prohibit"  # Should be prohibit with ratio of 1.0

class TestInhibitionTarget:
    """Tests for the InhibitionTarget class."""

    def test_inhibition_target_init(self):
        target = InhibitionTarget(target_type="plan", target_id="plan_abc", description="Execute complex plan", activation=0.9)
        assert target.target_type == "plan"
        assert target.target_id == "plan_abc"
        assert target.description == "Execute complex plan"
        assert target.activation == 0.9
