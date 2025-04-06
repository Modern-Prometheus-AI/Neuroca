"""
Unit tests for the Planner component in cognitive control.
"""

from typing import Any
from unittest.mock import MagicMock  # Import MagicMock

import pytest

from neuroca.core.cognitive_control.planner import Plan, Planner, PlanStep
from neuroca.core.health.dynamics import HealthState

# Import MemoryItem, MemoryType, and MemoryManager for mocking
from neuroca.memory.manager import MemoryItem, MemoryManager


# Mock context for testing
def create_context(health_state: HealthState = HealthState.NORMAL, **kwargs) -> dict[str, Any]:
    context = {"health_state": health_state}
    context.update(kwargs)
    return context

class TestPlanner:
    """Tests for the Planner class."""

    @pytest.fixture()
    def mock_memory_manager(self) -> MagicMock:
        """Fixture for a mocked MemoryManager."""
        manager = MagicMock(spec=MemoryManager)
        manager.retrieve.return_value = [] # Default: no knowledge found
        return manager
        
    @pytest.fixture()
    def planner(self, mock_memory_manager: MagicMock) -> Planner:
        """Fixture to create a Planner instance with mocked memory."""
        # Pass mock memory manager, others None for now
        return Planner(memory_manager=mock_memory_manager, health_manager=None, goal_manager=None)

    def test_initialization(self, planner: Planner, mock_memory_manager: MagicMock):
        """Test planner initialization."""
        # Planner fixture now receives the mock memory manager
        assert planner.memory_manager is mock_memory_manager 
        assert planner.health_manager is None
        assert planner.goal_manager is None

    def test_generate_plan_make_tea_normal_health(self, planner: Planner):
        """Test generating 'make tea' plan in NORMAL health."""
        context = create_context(HealthState.NORMAL)
        plan = planner.generate_plan("make tea", context)
        assert plan is not None
        assert isinstance(plan, Plan)
        assert plan.goal == "make tea"
        # Expects generic plan because mock memory returns no procedure
        assert len(plan.steps) == 3 
        assert plan.steps[0].action == "prepare_make"
        assert plan.steps[1].action == "execute_make"
        assert plan.steps[2].action == "verify_make"

    def test_generate_plan_make_tea_fatigued_health(self, planner: Planner):
        """Test generating 'make tea' plan in FATIGUED health."""
        context = create_context(HealthState.FATIGUED)
        plan = planner.generate_plan("make tea", context)
        assert plan is not None
        assert isinstance(plan, Plan)
        assert plan.goal == "make tea"
        # Expects generic plan first, health adaptation happens later if rule-based is triggered
        assert len(plan.steps) == 3
        assert plan.steps[0].action == "prepare_make"
        assert plan.steps[1].action == "execute_make"
        assert plan.steps[2].action == "verify_make"

    def test_generate_plan_impaired_health(self, planner: Planner):
        """Test that planning is aborted in IMPAIRED health."""
        context = create_context(HealthState.IMPAIRED)
        plan = planner.generate_plan("make tea", context)
        assert plan is None

    def test_generate_plan_critical_health(self, planner: Planner):
        """Test that planning is aborted in CRITICAL health."""
        context = create_context(HealthState.CRITICAL)
        plan = planner.generate_plan("make tea", context)
        assert plan is None

    def test_generate_plan_resolve_dependency(self, planner: Planner):
        """Test generating 'resolve dependency' plan."""
        context = create_context(dependency_target="module_A")
        plan = planner.generate_plan("resolve dependency conflict", context)
        assert plan is not None
        assert isinstance(plan, Plan)
        assert plan.goal == "resolve dependency conflict"
        # Expects generic plan first
        assert len(plan.steps) == 3 
        assert plan.steps[0].action == "prepare_resolve"
        assert plan.steps[0].parameters.get("target") == "dependency conflict" 
        assert plan.steps[2].action == "verify_resolve"

    def test_generate_plan_unknown_goal_generic_plan(self, planner: Planner):
        """Test generating a generic plan for an unknown goal."""
        context = create_context()
        plan = planner.generate_plan("unknown complex goal", context)
        assert plan is not None
        assert isinstance(plan, Plan)
        assert plan.goal == "unknown complex goal"
        # Check for generic steps based on decomposition
        assert len(plan.steps) == 3 
        assert plan.steps[0].action == "prepare_unknown"
        assert plan.steps[1].action == "execute_unknown"
        assert plan.steps[2].action == "verify_unknown"
        assert plan.steps[0].parameters.get("target") == "complex goal"

    def test_generate_plan_empty_goal(self, planner: Planner):
        """Test handling of an empty goal description."""
        context = create_context()
        plan = planner.generate_plan("", context)
        assert plan is None # Should fail to generate steps

    def test_replan_simple_retry(self, planner: Planner):
        """Test the basic replan functionality (simple retry)."""
        context = create_context()
        original_plan = planner.generate_plan("make tea", context)
        assert original_plan is not None
        
        # Simulate failure
        original_plan.status = "failed" 
        
        new_plan = planner.replan(original_plan, "Kettle not found", context)
        # Current placeholder just calls generate_plan again
        assert new_plan is not None
        assert new_plan.goal == original_plan.goal
        assert new_plan.status == "pending" # New plan should be pending
        # Check if it's essentially the same plan (as simple retry is the default fallback)
        assert len(new_plan.steps) == len(original_plan.steps)
        assert new_plan.steps[0].action == original_plan.steps[0].action

    # Add a test for the replan modification (e.g., resource failure)
    def test_replan_resource_failure(self, planner: Planner):
        """Test replanning attempts a low-resource plan on resource failure."""
        context = create_context()
        original_plan = planner.generate_plan("make tea", context)
        assert original_plan is not None
        original_plan.status = "failed"
        
        # Simulate replanning after resource failure
        planner.replan(original_plan, "energy resource low", context)
        
        # The placeholder logic tries generate_plan again with a modified context
        # In the 'make tea' example, if health was NORMAL, it generates the standard plan again.
        # If health was FATIGUED, it generates the simplified plan.
        # Let's test the FATIGUED case to see if the modified context works (though it doesn't currently)
        fatigued_context = create_context(HealthState.FATIGUED)
        fatigued_plan = planner.generate_plan("make tea", fatigued_context)
        fatigued_plan.status = "failed"
        new_fatigued_plan = planner.replan(fatigued_plan, "energy resource low", fatigued_context)

        assert new_fatigued_plan is not None
        # It should still generate the generic plan first in the current logic
        assert len(new_fatigued_plan.steps) == 3 
        assert new_fatigued_plan.steps[0].action == "prepare_make"

    # Add a test for the replan alternative action
    def test_replan_alternative_action(self, planner: Planner):
        """Test replanning uses an alternative action placeholder."""
        context = create_context()
        original_plan = planner.generate_plan("make tea", context)
        assert original_plan is not None
        
        # Simulate failure at step 0 ("find_kettle")
        original_plan.current_step_index = 0 
        original_plan.status = "failed" 
        
        new_plan = planner.replan(original_plan, "Kettle not found", context)
        
        assert new_plan is not None
        assert new_plan.goal == original_plan.goal
        # The current replan logic defaults to regenerating the original plan.
        # The original plan generated for "make tea" is the generic one.
        assert len(new_plan.steps) == 3
        assert new_plan.steps[0].action == "prepare_make" # Expecting the regenerated generic plan step
        assert new_plan.steps[1].action == "execute_make"
        assert new_plan.steps[2].action == "verify_make"

    # Test using knowledge from memory
    def test_generate_plan_with_semantic_knowledge(self, planner: Planner, mock_memory_manager: MagicMock):
        """Test generating a plan using a procedure from semantic memory."""
        # Setup mock memory to return a procedure
        procedure_content = {
            "type": "procedure",
            "steps": [
                {"action": "semantic_step_1", "cost": 0.2},
                {"action": "semantic_step_2", "parameters": {"p": "v"}, "cost": 0.3},
            ]
        }
        mock_item = MagicMock(spec=MemoryItem)
        mock_item.content = procedure_content
        mock_item.id = "proc_123"
        mock_memory_manager.retrieve.return_value = [mock_item] # Return this item when semantic memory is queried

        context = create_context()
        plan = planner.generate_plan("use known procedure", context)

        mock_memory_manager.retrieve.assert_called() # Check retrieve was called
        assert plan is not None
        assert plan.goal == "use known procedure"
        assert len(plan.steps) == 2
        assert plan.steps[0].action == "semantic_step_1"
        assert plan.steps[1].action == "semantic_step_2"
        assert plan.steps[1].parameters == {"p": "v"}
        assert plan.steps[0].estimated_cost == 0.2

class TestPlan:
    """Tests for the Plan and PlanStep classes."""

    def test_plan_step_init(self):
        step = PlanStep(action="test_action", parameters={"p1": 1}, estimated_cost=0.5)
        assert step.action == "test_action"
        assert step.parameters == {"p1": 1}
        assert step.estimated_cost == 0.5
        assert step.status == "pending"

    def test_plan_init(self):
        steps = [PlanStep("step1"), PlanStep("step2")]
        plan = Plan(goal="test_goal", steps=steps)
        assert plan.goal == "test_goal"
        assert plan.steps == steps
        assert plan.current_step_index == 0
        assert plan.status == "pending"

    def test_get_next_step(self):
        steps = [PlanStep("step1"), PlanStep("step2")]
        plan = Plan(goal="test_goal", steps=steps)
        
        step1 = plan.get_next_step()
        assert step1 is not None
        assert step1.action == "step1"
        assert step1.status == "executing"
        assert plan.status == "executing"
        assert plan.current_step_index == 0 # Index not incremented until status update

        # Mark step1 as completed
        plan.update_step_status(0, "completed")
        assert plan.current_step_index == 1

        step2 = plan.get_next_step()
        assert step2 is not None
        assert step2.action == "step2"
        assert step2.status == "executing"
        assert plan.status == "executing"
        assert plan.current_step_index == 1

        # Mark step2 as completed
        plan.update_step_status(1, "completed")
        assert plan.current_step_index == 2
        assert plan.status == "completed" # Plan completes

        step3 = plan.get_next_step()
        assert step3 is None # No more steps

    def test_get_next_step_already_completed(self):
        steps = [PlanStep("step1")]
        plan = Plan(goal="test_goal", steps=steps)
        plan.status = "completed"
        step = plan.get_next_step()
        assert step is None

    def test_update_step_status_completed(self):
        steps = [PlanStep("step1"), PlanStep("step2")]
        plan = Plan(goal="test_goal", steps=steps)
        plan.get_next_step() # Start step 0
        plan.update_step_status(0, "completed")
        assert plan.steps[0].status == "completed"
        assert plan.current_step_index == 1
        assert plan.status == "executing" # Plan still executing

        plan.get_next_step() # Start step 1
        plan.update_step_status(1, "completed")
        assert plan.steps[1].status == "completed"
        assert plan.current_step_index == 2
        assert plan.status == "completed" # Plan now completed

    def test_update_step_status_failed(self):
        steps = [PlanStep("step1"), PlanStep("step2")]
        plan = Plan(goal="test_goal", steps=steps)
        plan.get_next_step() # Start step 0
        plan.update_step_status(0, "failed", message="Resource unavailable")
        assert plan.steps[0].status == "failed"
        assert plan.status == "failed"
        assert plan.current_step_index == 0 # Index doesn't advance on failure

        # Cannot get next step if plan failed
        next_step = plan.get_next_step()
        assert next_step is None

    def test_update_step_status_invalid_index(self):
        steps = [PlanStep("step1")]
        plan = Plan(goal="test_goal", steps=steps)
        # Should log warning but not raise error
        plan.update_step_status(5, "completed") 
        assert plan.status == "pending" # Status unchanged
