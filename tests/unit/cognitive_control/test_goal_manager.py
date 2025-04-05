"""
Unit tests for the GoalManager component in cognitive control.
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import MagicMock # Import MagicMock

from neuroca.core.cognitive_control.goal_manager import GoalManager, Goal, GoalStatus
from neuroca.core.health.dynamics import HealthState

# Mock context for testing
def create_context(health_state: HealthState = HealthState.NORMAL, **kwargs) -> Dict[str, Any]:
    context = {"health_state": health_state}
    context.update(kwargs)
    return context

class TestGoalManager:
    """Tests for the GoalManager class."""

    @pytest.fixture
    def goal_manager(self) -> GoalManager:
        """Fixture to create a GoalManager instance."""
        return GoalManager()

    def test_initialization(self, goal_manager: GoalManager):
        """Test goal manager initialization."""
        assert not goal_manager.goals
        assert not goal_manager.active_goals
        assert goal_manager.health_manager is None
        assert goal_manager.memory_manager is None

    def test_add_goal_simple(self, goal_manager: GoalManager):
        """Test adding a simple top-level goal."""
        goal = goal_manager.add_goal("Test Goal 1", priority=3)
        assert goal is not None
        assert goal.id in goal_manager.goals
        assert goal_manager.goals[goal.id] is goal
        assert goal.description == "Test Goal 1"
        assert goal.priority == 3
        assert goal.status == GoalStatus.PENDING
        assert goal.parent_goal is None
        assert not goal.sub_goals

    def test_add_sub_goal(self, goal_manager: GoalManager):
        """Test adding a sub-goal to a parent goal."""
        parent_goal = goal_manager.add_goal("Parent Goal", priority=2)
        assert parent_goal is not None
        
        sub_goal = goal_manager.add_goal("Sub Goal", priority=4, parent_goal_id=parent_goal.id)
        assert sub_goal is not None
        assert sub_goal.id in goal_manager.goals
        assert sub_goal.parent_goal is parent_goal
        assert sub_goal in parent_goal.sub_goals

    def test_add_sub_goal_invalid_parent(self, goal_manager: GoalManager):
        """Test adding a sub-goal with an invalid parent ID returns None."""
        sub_goal = goal_manager.add_goal("Sub Goal", parent_goal_id="invalid_parent_id")
        assert sub_goal is None

    def test_add_goal_priority_adjustment_critical(self, goal_manager: GoalManager):
        """Test priority adjustment when adding a non-survival goal in CRITICAL state."""
        context = create_context(HealthState.CRITICAL)
        goal = goal_manager.add_goal("Normal Goal", priority=5, context=context)
        assert goal is not None
        assert goal.priority == 8 # 5 + 3

    def test_add_goal_priority_adjustment_stressed_urgent(self, goal_manager: GoalManager):
        """Test priority adjustment when adding an urgent goal in STRESSED state."""
        context = create_context(HealthState.STRESSED)
        goal = goal_manager.add_goal("Urgent Task", priority=4, context=context)
        assert goal is not None
        assert goal.priority == 3 # 4 - 1

    def test_add_goal_priority_clamping(self, goal_manager: GoalManager):
        """Test that adjusted priority is clamped between 1 and 10."""
        context_critical = create_context(HealthState.CRITICAL)
        goal_low = goal_manager.add_goal("Low Prio Goal", priority=9, context=context_critical)
        assert goal_low is not None
        assert goal_low.priority == 10 # 9 + 3 clamped to 10

        context_stressed = create_context(HealthState.STRESSED)
        goal_high = goal_manager.add_goal("Urgent High Prio", priority=1, context=context_stressed)
        assert goal_high is not None
        assert goal_high.priority == 1 # 1 - 1 clamped to 1

    def test_add_goal_collision_handling(self, goal_manager: GoalManager):
        """Test that adding a goal with the same description generates a unique ID."""
        goal1 = goal_manager.add_goal("Duplicate Goal")
        goal2 = goal_manager.add_goal("Duplicate Goal") # Should trigger collision logic
        
        assert goal1 is not None
        assert goal2 is not None
        assert goal1.id != goal2.id # IDs should be different
        assert goal1.description == "Duplicate Goal"
        assert goal2.description == "Duplicate Goal_1" # Description modified for unique hash
        assert goal2.id in goal_manager.goals
        assert goal_manager.goals[goal2.id] is goal2

    def test_activate_goal(self, goal_manager: GoalManager):
        """Test activating a goal."""
        goal = goal_manager.add_goal("Activate Me")
        assert goal is not None
        goal_manager.activate_goal(goal.id)
        assert goal.status == GoalStatus.ACTIVE
        assert goal.id in goal_manager.active_goals

    def test_activate_goal_not_found(self, goal_manager: GoalManager):
        """Test activating a non-existent goal."""
        # Should log warning but not raise error
        goal_manager.activate_goal("invalid_id")
        assert not goal_manager.active_goals

    def test_activate_goal_impaired_health_low_prio(self, goal_manager: GoalManager):
        """Test that activating a low priority goal fails in IMPAIRED state."""
        goal = goal_manager.add_goal("Low Prio", priority=5)
        assert goal is not None
        context = create_context(HealthState.IMPAIRED)
        goal_manager.activate_goal(goal.id, context)
        assert goal.status == GoalStatus.PENDING # Should remain pending
        assert goal.id not in goal_manager.active_goals

    def test_activate_goal_impaired_health_high_prio(self, goal_manager: GoalManager):
        """Test activating a high priority goal succeeds in IMPAIRED state."""
        goal = goal_manager.add_goal("High Prio", priority=2)
        assert goal is not None
        context = create_context(HealthState.IMPAIRED)
        goal_manager.activate_goal(goal.id, context)
        assert goal.status == GoalStatus.ACTIVE
        assert goal.id in goal_manager.active_goals

    def test_update_goal_status(self, goal_manager: GoalManager):
        """Test updating goal status."""
        goal = goal_manager.add_goal("Update Status")
        assert goal is not None
        goal_manager.activate_goal(goal.id)
        assert goal.status == GoalStatus.ACTIVE
        assert goal.id in goal_manager.active_goals

        goal_manager.update_goal_status(goal.id, GoalStatus.COMPLETED)
        assert goal.status == GoalStatus.COMPLETED
        assert goal.id not in goal_manager.active_goals # Should be removed from active set

        goal_manager.update_goal_status(goal.id, GoalStatus.ACTIVE) # Reactivate (though usually via activate_goal)
        assert goal.status == GoalStatus.ACTIVE
        assert goal.id in goal_manager.active_goals

        goal_manager.update_goal_status(goal.id, GoalStatus.SUSPENDED)
        assert goal.status == GoalStatus.SUSPENDED
        assert goal.id not in goal_manager.active_goals

    def test_get_active_goals(self, goal_manager: GoalManager):
        """Test retrieving active goals, sorted by priority."""
        g1 = goal_manager.add_goal("Goal 1", priority=5)
        g2 = goal_manager.add_goal("Goal 2", priority=2)
        g3 = goal_manager.add_goal("Goal 3", priority=8)
        g4 = goal_manager.add_goal("Goal 4", priority=2) # Same priority as g2
        
        goal_manager.activate_goal(g1.id)
        goal_manager.activate_goal(g2.id)
        # g3 is not activated
        goal_manager.activate_goal(g4.id)

        active_goals = goal_manager.get_active_goals(sorted_by_priority=True)
        
        assert len(active_goals) == 3
        assert active_goals[0].priority == 2 # g2 or g4
        assert active_goals[1].priority == 2 # g2 or g4
        assert active_goals[2].priority == 5 # g1
        assert active_goals[0].id in [g2.id, g4.id]
        assert active_goals[1].id in [g2.id, g4.id]
        assert active_goals[2].id == g1.id

    def test_get_highest_priority_active_goal(self, goal_manager: GoalManager):
        """Test retrieving the highest priority active goal."""
        g1 = goal_manager.add_goal("Goal 1", priority=5)
        g2 = goal_manager.add_goal("Goal 2", priority=2)
        g3 = goal_manager.add_goal("Goal 3", priority=8)
        
        highest = goal_manager.get_highest_priority_active_goal()
        assert highest is None # No active goals yet

        goal_manager.activate_goal(g1.id)
        goal_manager.activate_goal(g3.id)
        highest = goal_manager.get_highest_priority_active_goal()
        assert highest is not None
        assert highest.id == g1.id # Priority 5 is higher than 8

        goal_manager.activate_goal(g2.id)
        highest = goal_manager.get_highest_priority_active_goal()
        assert highest is not None
        assert highest.id == g2.id # Priority 2 is highest

    def test_resolve_conflicts_suspends_low_prio_when_stressed(self, goal_manager: GoalManager):
        """Test conflict resolution suspends low priority goals when stressed."""
        g1 = goal_manager.add_goal("High Prio", priority=2)
        g2 = goal_manager.add_goal("Medium Prio", priority=5) # Difference > 2
        g3 = goal_manager.add_goal("Low Prio", priority=8)    # Difference > 2
        
        # Mock health state via context (though resolve_conflicts doesn't take context directly yet)
        # We rely on the placeholder logic inside resolve_conflicts for now
        # To properly test, we'd mock the health_manager dependency
        goal_manager.health_manager = MagicMock()
        mock_health = MagicMock()
        mock_health.state = HealthState.STRESSED
        goal_manager.health_manager.get_component_health.return_value = mock_health

        goal_manager.activate_goal(g1.id)
        goal_manager.activate_goal(g2.id)
        goal_manager.activate_goal(g3.id)
        
        # activate_goal calls resolve_conflicts, let's call it again just in case
        goal_manager.resolve_conflicts() 

        assert g1.status == GoalStatus.ACTIVE
        assert g2.status == GoalStatus.SUSPENDED # Priority 5 > 2 + 2
        assert g3.status == GoalStatus.SUSPENDED # Priority 8 > 2 + 2

class TestGoal:
    """Tests for the Goal class."""

    def test_goal_init(self):
        goal = Goal(description="Test Goal", priority=7)
        assert goal.description == "Test Goal"
        assert goal.priority == 7
        assert goal.status == GoalStatus.PENDING
        assert goal.activation == 0.0
        assert goal.id.startswith("goal_")

    def test_goal_activate(self):
        goal = Goal("Test")
        goal.activate()
        assert goal.status == GoalStatus.ACTIVE
        assert goal.activation == 1.0

    def test_goal_update_status(self):
        goal = Goal("Test")
        goal.activate()
        goal.update_status(GoalStatus.COMPLETED)
        assert goal.status == GoalStatus.COMPLETED
        assert goal.activation == 0.0

        goal.update_status(GoalStatus.FAILED)
        assert goal.status == GoalStatus.FAILED
        assert goal.activation == 0.0

        goal.update_status(GoalStatus.SUSPENDED)
        assert goal.status == GoalStatus.SUSPENDED
        # Activation might not necessarily go to 0 when suspended, depends on design
        # Current implementation doesn't reset activation on suspend, only complete/fail
        assert goal.activation == 0.0 # Test current behavior
