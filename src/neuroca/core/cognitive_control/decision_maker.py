"""
Decision Making Component for NeuroCognitive Architecture (NCA).

This module implements decision-making processes within the executive functions.
It evaluates potential actions or plans based on current goals, context,
predicted outcomes, resource availability (health/memory), and learned heuristics.

Key functionalities:
- Evaluating options against goals and constraints.
- Selecting the most appropriate action or plan.
- Incorporating uncertainty and risk assessment.
- Learning from past decision outcomes.
"""

import logging
from typing import Any, Optional

from neuroca.core.enums import MemoryTier  # Import the correct enum

# Import necessary components for potential integration
# from neuroca.memory.manager import MemoryManager # Example
from neuroca.core.health.dynamics import HealthState  # Example for context checking
from neuroca.core.models import MemoryItem  # Import MemoryItem

# Assuming Plan and PlanStep might be used or adapted for decision options

# from .goal_manager import GoalManager, Goal # Example

# Configure logger
logger = logging.getLogger(__name__)

class DecisionOption:
    """Represents a potential choice or action to be evaluated."""
    def __init__(self, description: str, action: Any, estimated_utility: float = 0.0, risk: float = 0.0):
        self.description = description
        self.action = action # Could be a PlanStep, a full Plan, or another representation
        self.estimated_utility = estimated_utility # Expected value/benefit
        self.risk = risk # Potential negative outcome probability/severity

class DecisionMaker:
    """
    Evaluates options and selects actions based on goals and context.

    Integrates with memory, health, and planning components to make informed
    and adaptive decisions.
    """
    def __init__(self, memory_manager=None, health_manager=None, planner=None, goal_manager=None):
        """
        Initialize the DecisionMaker.

        Args:
            memory_manager: Instance of MemoryManager.
            health_manager: Instance of HealthDynamicsManager.
            planner: Instance of Planner.
            goal_manager: Instance of GoalManager.
        """
        logger.info("DecisionMaker initialized.")
        self.memory_manager = memory_manager
        self.health_manager = health_manager
        self.planner = planner
        self.goal_manager = goal_manager
        # NOTE: Consider implementing a proper dependency injection framework
        # for managing manager instances instead of direct constructor passing.

    def choose_action(self, options: list[DecisionOption], context: Optional[dict[str, Any]] = None) -> Optional[DecisionOption]:
        """
        Selects the best action from a list of options based on utility and risk.

        Args:
            options: A list of DecisionOption objects representing possible choices.
            context: Current situational information (e.g., health state, active goals).

        Returns:
            The selected DecisionOption, or None if no suitable option is found.
        """
        if not options:
            logger.warning("No options provided for decision making.")
            return None

        logger.info(f"Evaluating {len(options)} options.")

        # --- Enhanced Placeholder Decision Logic ---
        context = context or {} # Ensure context is a dict
        best_option = None
        max_adjusted_utility = -float('inf')

        # 1. Get Current Goal Context (Placeholder)
        current_goal_description = "default_goal"
        # if self.goal_manager:
        #     highest_goal = self.goal_manager.get_highest_priority_active_goal()
        #     if highest_goal:
        #         current_goal_description = highest_goal.description
        #         logger.debug(f"Considering highest priority goal: {current_goal_description}")

        # 2. Get Health Context
        health_state = context.get("health_state", HealthState.NORMAL)
        # Determine risk aversion based on health state
        if health_state == HealthState.STRESSED:
            risk_aversion_factor = 0.8
        elif health_state in [HealthState.IMPAIRED, HealthState.CRITICAL]:
            risk_aversion_factor = 1.0
        elif health_state == HealthState.OPTIMAL:
            risk_aversion_factor = 0.3
        else: # NORMAL or FATIGUED
            risk_aversion_factor = 0.5
        logger.debug(f"Decision context: Health={health_state.value}, RiskFactor={risk_aversion_factor:.2f}, Goal='{current_goal_description}'")

        # 3. Evaluate Options
        for option in options:
            # Base utility calculation
            base_utility = option.estimated_utility

            # --- Retrieve Past Outcomes ---
            past_outcome_adjustment = 0.0
            if self.memory_manager:
                try:
                    # Query episodic memory for past outcomes of this action/description
                    # Assuming MemoryItem metadata stores outcome like: {"outcome": "success" | "failure", "details": "..."}
                    past_attempts = self.memory_manager.retrieve(
                        query=f"outcome related to {option.description}", # More general query
                        memory_type=MemoryTier.EPISODIC, # Use MemoryTier instead of MemoryType
                        limit=5 # Look at recent attempts
                    )
                    if past_attempts:
                        logger.debug(f"Retrieved {len(past_attempts)} past attempts related to '{option.description}'.")
                        # Simple average of past success/failure 
                        success_count = sum(1 for item in past_attempts if isinstance(item, MemoryItem) and item.metadata.get("outcome") == "success")
                        len(past_attempts) - success_count
                        if len(past_attempts) > 0:
                             success_rate = success_count / len(past_attempts)
                             # Adjust utility: +0.1 for >50% success, -0.1 for <50% success
                             past_outcome_adjustment = (success_rate - 0.5) * 0.2
                             logger.debug(f"Option '{option.description}': Past success rate {success_rate:.2f}, Utility Adjustment={past_outcome_adjustment:.2f}")
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Error retrieving past outcomes for decision making: {e}")
            # --- End Past Outcome ---

            # Adjust utility based on goal alignment (placeholder)
            goal_alignment_bonus = 0.0
            if current_goal_description in option.description.lower(): # Very simple check
                 goal_alignment_bonus = 0.2
            
            # Adjust utility based on risk aversion and past outcomes
            adjusted_utility = base_utility + goal_alignment_bonus + past_outcome_adjustment - (risk_aversion_factor * option.risk)
            
            logger.debug(f"Option '{option.description}': BaseUtil={base_utility:.2f}, GoalBonus={goal_alignment_bonus:.2f}, PastAdj={past_outcome_adjustment:.2f}, Risk={option.risk:.2f}, FinalUtil={adjusted_utility:.2f}")

            if adjusted_utility > max_adjusted_utility:
                max_adjusted_utility = adjusted_utility
                best_option = option

        if best_option:
            logger.info(f"Selected option: '{best_option.description}' with adjusted utility {max_adjusted_utility:.2f}")
        else:
            logger.warning("Could not select a suitable option.")

        # 4. Post-Decision Actions / Plan Triggering (Placeholder)
        if best_option:
             # Example: If the chosen action itself represents a sub-goal or complex task, trigger planning.
             # This requires a way to identify such actions (e.g., based on type, description, or metadata).
             action_requires_plan = False
             if isinstance(best_option.action, str) and best_option.action.startswith("goal:"):
                 action_requires_plan = True
                 goal_desc_for_plan = best_option.action.split(":", 1)[1].strip()
             elif isinstance(best_option.action, dict) and best_option.action.get("type") == "complex_action":
                  action_requires_plan = True
                  goal_desc_for_plan = best_option.description # Use option description as goal

             if action_requires_plan:
                 logger.info(f"Chosen action '{best_option.description}' requires further planning.")
                 if self.planner:
                     # Generate a sub-plan for the chosen complex action/sub-goal
                     sub_plan = self.planner.generate_plan(goal_description=goal_desc_for_plan, context=context)
                     if sub_plan:
                          logger.info(f"Generated sub-plan for action '{best_option.description}'.")
                          # The system's execution loop would now likely focus on this sub_plan.
                          # We might replace the 'action' in the DecisionOption with the generated Plan.
                          best_option.action = sub_plan 
                     else:
                          logger.error(f"Failed to generate sub-plan for chosen action '{best_option.description}'. Decision might need reconsideration.")
                          # NOTE: Implement handling for sub-plan generation failure.
                          # This could involve selecting an alternative option or raising an error.
                 else:
                     logger.warning("Planner not available to create sub-plan for complex action.")

        return best_option
        # --- End Enhanced Placeholder ---
