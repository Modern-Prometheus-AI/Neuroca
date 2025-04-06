"""
Unit tests for the MetacognitiveMonitor component in cognitive control.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Import GoalStatus needed for assess_current_state
from neuroca.core.cognitive_control.goal_manager import Goal, GoalStatus
from neuroca.core.cognitive_control.metacognition import MetacognitiveMonitor
from neuroca.core.health.dynamics import (
    ComponentHealth,
    HealthParameter,
    HealthParameterType,
    HealthState,
)
from neuroca.memory.manager import MemoryItem  # Assuming MemoryItem is available


# Mock context for testing
def create_context(health_state: HealthState = HealthState.NORMAL, **kwargs) -> dict[str, Any]:
    context = {"health_state": health_state}
    context.update(kwargs)
    return context

# Mock HealthDynamicsManager
@pytest.fixture()
def mock_health_manager() -> MagicMock:
    manager = MagicMock()
    # Setup mock components and their health
    comp1_health = ComponentHealth("comp1", state=HealthState.NORMAL)
    comp1_health.add_parameter(HealthParameter(name="energy", type=HealthParameterType.ENERGY, value=0.8, min_value=0.0, max_value=1.0))
    comp2_health = ComponentHealth("comp2", state=HealthState.FATIGUED)
    comp2_health.add_parameter(HealthParameter(name="energy", type=HealthParameterType.ENERGY, value=0.4, min_value=0.0, max_value=1.0))
    
    manager._components = {"comp1": comp1_health, "comp2": comp2_health} # Simulate internal dict
    manager.get_component_health.side_effect = lambda cid: manager._components.get(cid)
    return manager

# Mock MemoryManager
@pytest.fixture()
def mock_memory_manager() -> MagicMock:
    manager = MagicMock()
    manager.get_stats.return_value = {
        "working_memory": {"count": 5, "capacity": 7, "utilization": 5/7},
        # Add other stats if needed by tests
    }
    # Setup retrieve for strategy selection tests if needed later
    # manager.retrieve.return_value = [] 
    return manager

# Mock GoalManager
@pytest.fixture()
def mock_goal_manager() -> MagicMock:
    manager = MagicMock()
    mock_goal = MagicMock()
    mock_goal.description = "High Priority Goal"
    manager.get_active_goals.return_value = [mock_goal] # Simulate one active goal
    # Simulate the goals dictionary for assess_current_state
    mock_goal_instance = Goal(description="High Priority Goal") 
    mock_goal_instance.status = GoalStatus.ACTIVE # Assume it's active
    manager.goals = {"goal_1": mock_goal_instance} 
    return manager


class TestMetacognitiveMonitor:
    """Tests for the MetacognitiveMonitor class."""

    @pytest.fixture()
    def monitor(self, mock_health_manager, mock_memory_manager, mock_goal_manager) -> MetacognitiveMonitor:
        """Fixture to create a MetacognitiveMonitor instance with mocks."""
        return MetacognitiveMonitor(
            health_manager=mock_health_manager, 
            memory_manager=mock_memory_manager, 
            goal_manager=mock_goal_manager
        )

    def test_initialization(self, monitor: MetacognitiveMonitor):
        """Test monitor initialization."""
        assert monitor.health_manager is not None
        assert monitor.memory_manager is not None
        assert monitor.goal_manager is not None
        assert not monitor.last_error_log
        assert monitor.performance_metrics["total_actions_completed"] == 0

    def test_log_error(self, monitor: MetacognitiveMonitor):
        """Test logging errors to local buffer."""
        monitor.log_error({"type": "PlanningError", "message": "Failed"})
        assert len(monitor.last_error_log) == 1
        assert monitor.last_error_log[0]["type"] == "PlanningError"
        
        # Test log trimming
        monitor.max_error_log_size = 1
        monitor.log_error({"type": "MemoryError", "message": "Not found"})
        assert len(monitor.last_error_log) == 1
        assert monitor.last_error_log[0]["type"] == "MemoryError"  # Old error should be gone
        
    def test_log_error_memory_storage(self, monitor: MetacognitiveMonitor):
        """Test error logging to episodic memory."""
        # Setup memory_manager mock for this specific test
        error_details = {
            "type": "PlanningError", 
            "message": "Failed to generate plan", 
            "component": "planner",
            "source": "planning_subsystem",
            "severity": "error",
            "task": "daily_schedule"
        }
        
        # Call the method
        monitor.log_error(error_details)
        
        # Verify memory_manager.store was called with correct arguments
        monitor.memory_manager.store.assert_called_once()
        
        # Extract the call arguments
        call_args = monitor.memory_manager.store.call_args[1]
        
        # Validate stored content structure
        assert call_args["memory_type"] == "episodic"
        assert call_args["emotional_salience"] == 0.8  # Errors have high emotional salience
        
        # Validate content
        content = call_args["content"]
        assert content["type"] == "error"
        assert content["error_type"] == "PlanningError"
        assert content["message"] == "Failed to generate plan"
        
        # Validate metadata
        metadata = call_args["metadata"]
        assert metadata["component"] == "planner"
        assert metadata["error_source"] == "planning_subsystem"
        assert metadata["severity"] == "error"
        assert metadata["task"] == "daily_schedule"
        assert "tags" in metadata
        assert "error" in metadata["tags"]

    def test_log_action_completion(self, monitor: MetacognitiveMonitor):
        """Test logging action completion and updating metrics."""
        monitor.log_action_completion(action_cost=0.5)
        assert monitor.performance_metrics["total_actions_completed"] == 1
        assert monitor.performance_metrics["total_energy_consumed"] == 0.5
        assert monitor.performance_metrics["avg_action_cost"] == 0.5

        monitor.log_action_completion(action_cost=0.3)
        assert monitor.performance_metrics["total_actions_completed"] == 2
        assert monitor.performance_metrics["total_energy_consumed"] == 0.8
        assert monitor.performance_metrics["avg_action_cost"] == 0.4

    def test_assess_current_state(self, monitor: MetacognitiveMonitor):
        """Test assessing the current cognitive state."""
        state = monitor.assess_current_state()
        
        assert "assessment_timestamp" in state
        # Based on mock_health_manager (NORMAL, FATIGUED) -> degraded
        assert state.get("overall_health") == HealthState.STRESSED.value # Placeholder uses STRESSED for degraded
        assert state.get("average_energy") == pytest.approx((0.8 + 0.4) / 2)
        assert state.get("health_state_counts", {}).get(HealthState.NORMAL.value) == 1
        assert state.get("health_state_counts", {}).get(HealthState.FATIGUED.value) == 1
        
        # Based on mock_goal_manager
        assert state.get("active_goal_count") == 1
        assert state.get("highest_priority_goal") == "High Priority Goal"
        assert state.get("suspended_goal_count") == 0 # Mock doesn't have suspended goals
 
        # Based on mock_memory_manager
        # The code rounds utilization to 3 decimal places
        assert state.get("working_memory_load") == pytest.approx(0.714)
        assert state.get("working_memory_count") == 5 # Ensure this aligns with the previous assert
 
        # Based on performance/error logs (initially empty)
        assert state.get("recent_errors_count") == 0
        assert state.get("total_actions_completed") == 0
        assert state.get("avg_action_cost") == 0.0

    def test_estimate_confidence_memory_item(self, monitor: MetacognitiveMonitor):
        """Test confidence estimation for a MemoryItem."""
        # Mock MemoryItem with specific activation and metadata
        mem_item = MagicMock(spec=MemoryItem)
        mem_item.calculate_activation.return_value = 0.8
        mem_item.metadata = {"confidence": 0.9} # Explicit confidence
        
        confidence = monitor.estimate_confidence(mem_item, source="semantic_memory")
        
        # Expected:
        # Source base = 0.85
        # Mem confidence = max(0.1, min(1.0, 0.8 * 0.8 + 0.1)) = 0.74
        # Mem confidence avg with metadata = (0.74 + 0.9) / 2 = 0.82
        # Base avg with mem = (0.85 + 0.82) / 2 = 0.835
        # Health factor (assuming NORMAL/healthy) = 1.0
        # Final = 0.835 * 1.0 = 0.835
        assert confidence == pytest.approx(0.835)
 
    def test_estimate_confidence_llm(self, monitor: MetacognitiveMonitor):
        """Test confidence estimation for an LLM prediction."""
        # Mock assess_current_state to ensure "healthy" state for this test
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "healthy"}):
            confidence = monitor.estimate_confidence("Some prediction", source="llm_prediction")
        # Expected: Base=0.6, HealthFactor=1.0 -> 0.6
        assert confidence == pytest.approx(0.6) # Ensure this aligns with the 'with' block start
 
    def test_estimate_confidence_degraded_health(self, monitor: MetacognitiveMonitor):
        """Test confidence reduction in degraded health state."""
        # Force degraded state in assessment via mock
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "degraded"}):
            confidence = monitor.estimate_confidence("Some prediction", source="llm_prediction")
        # Expected: Base=0.6, HealthFactor=0.9 -> 0.54
        assert confidence == pytest.approx(0.54) # Ensure this aligns with the 'with' block start
 
    def test_select_strategy_normal_health(self, monitor: MetacognitiveMonitor):
        """Test strategy selection in NORMAL health."""
        strategies = ["heuristic_search", "detailed_planning", "memory_retrieval"]
        # Mock assess_current_state to ensure "healthy" state for this test
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "healthy", "working_memory_load": 0.5}):
            context = create_context() # Context health state won't be used due to patch
            choice = monitor.select_strategy("complex task", strategies, context)
        # Expect detailed_planning as it gets bonus in healthy state
        assert choice == "detailed_planning" # Ensure this aligns with the 'with' block start

    def test_select_strategy_fatigued_health(self, monitor: MetacognitiveMonitor):
        """Test strategy selection in FATIGUED health."""
        strategies = ["heuristic_search", "detailed_planning", "memory_retrieval"]
        context = create_context(HealthState.FATIGUED)
        choice = monitor.select_strategy("complex task", strategies, context)
        # Expect heuristic or memory retrieval due to penalty on detailed_planning
        assert choice in ["heuristic_search", "memory_retrieval"]

    def test_select_strategy_unhealthy_state(self, monitor: MetacognitiveMonitor):
        """Test strategy selection in unhealthy (IMPAIRED/CRITICAL) state."""
        strategies = ["heuristic_search", "detailed_planning", "simple_heuristic"]
        # Force unhealthy state in assessment
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "unhealthy"}):
            context = create_context() # Context health doesn't matter due to patch
            choice = monitor.select_strategy("simple task", strategies, context)
            # Expect simple_heuristic due to bonus in unhealthy state
            assert choice == "simple_heuristic"

    def test_select_strategy_high_wm_load(self, monitor: MetacognitiveMonitor):
        """Test strategy selection penalizes demanding strategies with high WM load."""
        strategies = ["heuristic_search", "detailed_planning", "memory_retrieval"]
        # Force high WM load in assessment
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "healthy", "working_memory_load": 0.9}):
             context = create_context()
             choice = monitor.select_strategy("complex task", strategies, context)
             # detailed_planning gets bonus for healthy, but penalty for high WM load
             # heuristic_search or memory_retrieval might win
             assert choice != "detailed_planning"
             assert choice in ["heuristic_search", "memory_retrieval"]

    def test_detect_error_patterns_no_memory_manager(self, monitor: MetacognitiveMonitor):
        """Test error pattern detection when memory manager is not available."""
        # Force memory_manager to None for this test
        monitor.memory_manager = None
        result = monitor.detect_error_patterns()
        
        assert result["patterns_detected"] is False
        assert result["reason"] == "memory_unavailable"
    
    def test_detect_error_patterns_no_errors(self, monitor: MetacognitiveMonitor):
        """Test error pattern detection when no errors are found."""
        # Setup memory_manager to return empty list
        monitor.memory_manager.retrieve.return_value = []
        
        result = monitor.detect_error_patterns()
        
        assert result["patterns_detected"] is False
        assert result["reason"] == "no_errors_found"
        monitor.memory_manager.retrieve.assert_called_once()
    
    def test_detect_error_patterns_with_errors(self, monitor: MetacognitiveMonitor):
        """Test error pattern detection with multiple errors."""
        # Create mock memory items with error data
        mock_mem1 = MagicMock()
        mock_mem1.content = {"error_type": "MemoryError", "message": "Not found"}
        mock_mem1.metadata = {"component": "memory", "error_source": "retrieval", "timestamp": 12345}
        
        mock_mem2 = MagicMock()
        mock_mem2.content = {"error_type": "MemoryError", "message": "Index error"}
        mock_mem2.metadata = {"component": "memory", "error_source": "storage", "timestamp": 12346}
        
        mock_mem3 = MagicMock()
        mock_mem3.content = {"error_type": "PlanningError", "message": "Invalid plan"}
        mock_mem3.metadata = {"component": "planner", "error_source": "validation", "timestamp": 12347}
        
        # Setup memory_manager to return these items
        monitor.memory_manager.retrieve.return_value = [mock_mem1, mock_mem2, mock_mem3]
        
        result = monitor.detect_error_patterns()
        
        # Check overall results
        assert result["patterns_detected"] is True
        assert result["total_errors"] == 3
        
        # Check frequency counts
        assert result["by_type"]["MemoryError"] == 2
        assert result["by_type"]["PlanningError"] == 1
        assert result["by_component"]["memory"] == 2
        assert result["by_component"]["planner"] == 1
        
        # Check most common patterns
        assert result["most_common_type"] == "MemoryError"
        assert result["most_common_component"] == "memory"
        
        # Check recent errors list
        assert len(result["recent_errors"]) == 3
    
    def test_optimize_resource_allocation_normal(self, monitor: MetacognitiveMonitor):
        """Test resource allocation optimization in NORMAL state."""
        allocation = monitor.optimize_resource_allocation(task_complexity=0.5)
        assert allocation["energy_budget_factor"] == 1.0
        assert allocation["attention_focus_level"] == 0.8  # Default
        assert allocation["time_budget_factor"] == 1.0
        assert allocation["parallel_processes"] == 1

    def test_optimize_resource_allocation_degraded_complex(self, monitor: MetacognitiveMonitor):
        """Test resource allocation optimization in DEGRADED state for complex task."""
         # Force degraded state in assessment
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "degraded"}):
            allocation = monitor.optimize_resource_allocation(task_complexity=0.8)
            # Degraded defaults: energy=0.7, attention=0.6
            # Complex task bonus: energy=min(1.0, 0.7+0.1)=0.8, attention=min(1.0, 0.6+0.2)=0.8
            assert allocation["energy_budget_factor"] == pytest.approx(0.8)
            assert allocation["attention_focus_level"] == pytest.approx(0.8)
            assert allocation["time_budget_factor"] == pytest.approx(1.2)  # More time for complex tasks
            assert allocation["parallel_processes"] == 1  # No parallel in degraded state

    def test_optimize_resource_allocation_unhealthy_simple(self, monitor: MetacognitiveMonitor):
        """Test resource allocation optimization in UNHEALTHY state for simple task."""
         # Force unhealthy state in assessment
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "unhealthy"}):
            allocation = monitor.optimize_resource_allocation(task_complexity=0.3)
            # Unhealthy defaults: energy=0.4, attention=0.5
            # Simple task bonus doesn't apply
            assert allocation["energy_budget_factor"] == pytest.approx(0.4)
            assert allocation["attention_focus_level"] == pytest.approx(0.5)
            assert allocation["time_budget_factor"] == pytest.approx(1.5)  # More time when unhealthy
            assert allocation["parallel_processes"] == 1
    
    def test_optimize_resource_allocation_with_plan(self, monitor: MetacognitiveMonitor):
        """Test resource allocation with plan information."""
        # Create a mock plan with multiple steps
        mock_plan = MagicMock()
        mock_plan.steps = [1, 2, 3, 4, 5, 6]  # 6 steps
        
        # Force healthy state for parallel processing
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "healthy"}):
            allocation = monitor.optimize_resource_allocation(task_complexity=0.6, current_plan=mock_plan)
            
            # Check that plan characteristics influenced allocation
            assert allocation["attention_focus_level"] > 0.8  # Baseline is 0.8, should be higher
            assert allocation["parallel_processes"] == 2  # Should allow some parallelism (plan_steps // 3)
    
    def test_optimize_resource_allocation_with_memory(self, monitor: MetacognitiveMonitor):
        """Test resource allocation using past task memory."""
        # Create mock memory items for past similar tasks
        mock_mem1 = MagicMock()
        mock_mem1.metadata = {
            "resources": {
                "energy_used": 0.6,
                "attention_level": 0.7,
                "time_taken": 1.3
            }
        }
        
        mock_mem2 = MagicMock()
        mock_mem2.metadata = {
            "resources": {
                "energy_used": 0.8,
                "attention_level": 0.9,
                "time_taken": 1.1
            }
        }
        
        mock_mem3 = MagicMock()
        mock_mem3.metadata = {
            "resources": {
                "energy_used": 0.7,
                "attention_level": 0.8,
                "time_taken": 1.2
            }
        }
        
        # Setup memory_manager to return these items
        monitor.memory_manager.retrieve.return_value = [mock_mem1, mock_mem2, mock_mem3]
        
        # Force normal health state for baseline
        with patch.object(monitor, 'assess_current_state', return_value={"overall_health": "healthy"}):
            allocation = monitor.optimize_resource_allocation(
                task_complexity=0.5, 
                task_type="planning"
            )
            
            # Expected values based on averaging baseline with past performance
            # Avg past energy: (0.6 + 0.8 + 0.7) / 3 = 0.7
            # energy_budget_factor = (1.0 + 0.7) / 2 = 0.85
            assert allocation["energy_budget_factor"] == pytest.approx(0.85)
            
            # Avg past attention: (0.7 + 0.9 + 0.8) / 3 = 0.8
            # attention_focus_level = (0.8 + 0.8) / 2 = 0.8 (unchanged)
            assert allocation["attention_focus_level"] == pytest.approx(0.8)
            
            # Avg past time: (1.3 + 1.1 + 1.2) / 3 = 1.2
            # time_budget_factor = (1.0 + 1.2) / 2 = 1.1
            assert allocation["time_budget_factor"] == pytest.approx(1.1)
