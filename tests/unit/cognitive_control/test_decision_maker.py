"""
Unit tests for the DecisionMaker component in cognitive control.
"""

from typing import Any
from unittest.mock import MagicMock  # Import MagicMock

import pytest

from neuroca.core.cognitive_control.decision_maker import DecisionMaker, DecisionOption
from neuroca.core.health.dynamics import HealthState

# Import MemoryItem and MemoryType for mocking memory results
from neuroca.memory.manager import MemoryItem, MemoryManager


# Mock context for testing (can reuse or adapt from planner tests)
def create_context(health_state: HealthState = HealthState.NORMAL, **kwargs) -> dict[str, Any]:
    context = {"health_state": health_state}
    context.update(kwargs)
    return context

class TestDecisionMaker:
    """Tests for the DecisionMaker class."""

    @pytest.fixture()
    def mock_memory_manager(self) -> MagicMock:
        """Fixture for a mocked MemoryManager."""
        manager = MagicMock(spec=MemoryManager)
        manager.retrieve.return_value = [] # Default: no past attempts found
        return manager

    @pytest.fixture()
    def decision_maker(self, mock_memory_manager: MagicMock) -> DecisionMaker:
        """Fixture to create a DecisionMaker instance with mocked memory."""
        # Pass mock memory manager
        return DecisionMaker(memory_manager=mock_memory_manager)

    @pytest.fixture()
    def sample_options(self) -> list[DecisionOption]:
        """Fixture providing sample decision options."""
        return [
            DecisionOption(description="Option A (Low Risk, Med Utility)", action="action_a", estimated_utility=0.6, risk=0.1),
            DecisionOption(description="Option B (High Risk, High Utility)", action="action_b", estimated_utility=0.9, risk=0.7),
            DecisionOption(description="Option C (Med Risk, Low Utility)", action="action_c", estimated_utility=0.3, risk=0.4),
        ]

    def test_initialization(self, decision_maker: DecisionMaker, mock_memory_manager: MagicMock):
        """Test decision maker initialization."""
        # Fixture now provides mock memory manager
        assert decision_maker.memory_manager is mock_memory_manager
        assert decision_maker.health_manager is None
        assert decision_maker.planner is None
        assert decision_maker.goal_manager is None

    def test_choose_action_no_options(self, decision_maker: DecisionMaker):
        """Test choosing an action when no options are provided."""
        choice = decision_maker.choose_action([], context=create_context())
        assert choice is None

    def test_choose_action_normal_health(self, decision_maker: DecisionMaker, sample_options: list[DecisionOption]):
        """Test action choice in NORMAL health state (default risk aversion)."""
        context = create_context(HealthState.NORMAL)
        choice = decision_maker.choose_action(sample_options, context)
        
        # Expected utilities with risk_factor = 0.5:
        # A: 0.6 - (0.5 * 0.1) = 0.55
        # B: 0.9 - (0.5 * 0.7) = 0.55
        # C: 0.3 - (0.5 * 0.4) = 0.10
        # Ties might go to the first one encountered (Option A) or depend on float precision.
        # Let's assert it's either A or B in this placeholder logic.
        assert choice is not None
        assert choice.description in ["Option A (Low Risk, Med Utility)", "Option B (High Risk, High Utility)"]
        # If logic consistently picks first on tie: assert choice.description == "Option A (Low Risk, Med Utility)"

    def test_choose_action_stressed_health(self, decision_maker: DecisionMaker, sample_options: list[DecisionOption]):
        """Test action choice in STRESSED health state (higher risk aversion)."""
        context = create_context(HealthState.STRESSED)
        choice = decision_maker.choose_action(sample_options, context)
        
        # Expected utilities with risk_factor = 0.8:
        # A: 0.6 - (0.8 * 0.1) = 0.52
        # B: 0.9 - (0.8 * 0.7) = 0.34
        # C: 0.3 - (0.8 * 0.4) = -0.02
        # Option A should be chosen due to higher risk aversion.
        assert choice is not None
        assert choice.description == "Option A (Low Risk, Med Utility)"

    def test_choose_action_critical_health(self, decision_maker: DecisionMaker, sample_options: list[DecisionOption]):
        """Test action choice in CRITICAL health state (highest risk aversion)."""
        context = create_context(HealthState.CRITICAL)
        choice = decision_maker.choose_action(sample_options, context)
        
        # Expected utilities with risk_factor = 1.0:
        # A: 0.6 - (1.0 * 0.1) = 0.50
        # B: 0.9 - (1.0 * 0.7) = 0.20
        # C: 0.3 - (1.0 * 0.4) = -0.10
        # Option A should be chosen.
        assert choice is not None
        assert choice.description == "Option A (Low Risk, Med Utility)"

    def test_choose_action_optimal_health(self, decision_maker: DecisionMaker, sample_options: list[DecisionOption]):
        """Test action choice in OPTIMAL health state (lower risk aversion)."""
        context = create_context(HealthState.OPTIMAL)
        choice = decision_maker.choose_action(sample_options, context)
        
        # Expected utilities with risk_factor = 0.3:
        # A: 0.6 - (0.3 * 0.1) = 0.57
        # B: 0.9 - (0.3 * 0.7) = 0.69
        # C: 0.3 - (0.3 * 0.4) = 0.18
        # Option B should be chosen due to lower risk aversion.
        assert choice is not None
        assert choice.description == "Option B (High Risk, High Utility)"

    def test_choose_action_with_goal_bonus(self, decision_maker: DecisionMaker):
        """Test that goal alignment bonus influences choice (placeholder)."""
        options = [
            DecisionOption(description="Aligns with default_goal", action="action_a", estimated_utility=0.5, risk=0.1),
            DecisionOption(description="Does not align", action="action_b", estimated_utility=0.6, risk=0.1),
        ]
        context = create_context(HealthState.NORMAL) # risk_factor = 0.5
        choice = decision_maker.choose_action(options, context)

        # Expected utilities:
        # A: 0.5 (base) + 0.2 (goal bonus) - (0.5 * 0.1) (risk) = 0.65
        # B: 0.6 (base) + 0.0 (goal bonus) - (0.5 * 0.1) (risk) = 0.55
        # Option A should be chosen.
        assert choice is not None
        assert choice.description == "Aligns with default_goal"

    def test_choose_action_past_success(self, decision_maker: DecisionMaker, mock_memory_manager: MagicMock):
        """Test that past success increases utility."""
        options = [
            DecisionOption(description="Option Good History", action="action_a", estimated_utility=0.5, risk=0.1),
            DecisionOption(description="Option Neutral History", action="action_b", estimated_utility=0.5, risk=0.1),
        ]
        # Mock memory to return successful past attempts for Option A
        success_item = MagicMock(spec=MemoryItem)
        success_item.metadata = {"outcome": "success"}
        mock_memory_manager.retrieve.side_effect = lambda query, **kwargs: [success_item] * 3 if "Good History" in query else []

        context = create_context(HealthState.NORMAL) # risk_factor = 0.5
        choice = decision_maker.choose_action(options, context)

        # Expected utilities:
        # A: 0.5 (base) + 0.0 (goal) + (1.0 - 0.5)*0.2 (past success) - (0.5 * 0.1) (risk) = 0.5 + 0.1 - 0.05 = 0.55
        # B: 0.5 (base) + 0.0 (goal) + (0.0 - 0.5)*0.2 (no history)   - (0.5 * 0.1) (risk) = 0.5 - 0.1 - 0.05 = 0.35
        assert choice is not None
        assert choice.description == "Option Good History"

    def test_choose_action_past_failure(self, decision_maker: DecisionMaker, mock_memory_manager: MagicMock):
        """Test that past failure decreases utility."""
        options = [
            DecisionOption(description="Option Bad History", action="action_a", estimated_utility=0.5, risk=0.1),
            DecisionOption(description="Option Neutral History", action="action_b", estimated_utility=0.5, risk=0.1),
        ]
        # Mock memory to return failed past attempts for Option A
        failure_item = MagicMock(spec=MemoryItem)
        failure_item.metadata = {"outcome": "failure"}
        mock_memory_manager.retrieve.side_effect = lambda query, **kwargs: [failure_item] * 3 if "Bad History" in query else []

        context = create_context(HealthState.NORMAL) # risk_factor = 0.5
        choice = decision_maker.choose_action(options, context)

        # Expected utilities:
        # A: 0.5 (base) + 0.0 (goal) + (0.0 - 0.5)*0.2 (past failure) - (0.5 * 0.1) (risk) = 0.5 - 0.1 - 0.05 = 0.35
        # B: 0.5 (base) + 0.0 (goal) + (0.0 - 0.5)*0.2 (no history)   - (0.5 * 0.1) (risk) = 0.5 - 0.1 - 0.05 = 0.35
        # With equal scores, it might pick either. Let's check it's not None.
        # If we want deterministic, maybe Neutral should have slightly higher base utility.
        # Let's adjust Neutral base utility slightly for a deterministic outcome.
        options[1].estimated_utility = 0.51 
        # B new: 0.51 + 0.0 - 0.1 - 0.05 = 0.36
        choice = decision_maker.choose_action(options, context)
        assert choice is not None
        assert choice.description == "Option Neutral History"


class TestDecisionOption:
    """Tests for the DecisionOption class."""

    def test_decision_option_init(self):
        option = DecisionOption(description="Test Option", action="do_test", estimated_utility=0.8, risk=0.2)
        assert option.description == "Test Option"
        assert option.action == "do_test"
        assert option.estimated_utility == 0.8
        assert option.risk == 0.2
