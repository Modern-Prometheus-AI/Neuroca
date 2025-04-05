"""
Inhibitory Control Component for NeuroCognitive Architecture (NCA).

This module implements inhibitory control mechanisms within the executive functions.
It is responsible for suppressing prepotent but inappropriate responses, cancelling
planned actions that are no longer relevant or safe, and managing interference
from distracting stimuli or conflicting goals.

Key functionalities:
- Response inhibition (suppressing automatic actions).
- Action cancellation (stopping ongoing or planned actions).
- Interference control (filtering distractions).
- Conflict monitoring (detecting competing responses/goals).
"""

import logging
from typing import Any, Optional, Dict

# Import necessary components for potential integration
from .goal_manager import GoalManager, Goal # Example
from neuroca.core.health.dynamics import HealthState # Example for context checking

# Configure logger
logger = logging.getLogger(__name__)

class InhibitionTarget:
    """Represents an action, plan, or response to be potentially inhibited."""
    def __init__(self, target_type: str, target_id: str, description: str, activation: float = 1.0):
        self.target_type = target_type # e.g., "action", "plan", "stimulus_response"
        self.target_id = target_id
        self.description = description
        self.activation = activation # Current drive/strength of the target

class Inhibitor:
    """
    Manages inhibitory control processes.

    Evaluates whether ongoing or potential actions should be suppressed based
    on current goals, context, rules, and potential negative consequences.
    """
    def __init__(self, goal_manager=None, health_manager=None, memory_manager=None):
        """
        Initialize the Inhibitor.

        Args:
            goal_manager: Instance of GoalManager.
            health_manager: Instance of HealthDynamicsManager.
            memory_manager: Instance of MemoryManager.
        """
        logger.info("Inhibitor initialized.")
        self.goal_manager = goal_manager
        self.health_manager = health_manager
        self.memory_manager = memory_manager
        # TODO: Implement dependency injection properly later

    def should_inhibit(self, target: InhibitionTarget, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine whether a specific target action or response should be inhibited.

        Args:
            target: The InhibitionTarget representing the action/response under consideration.
            context: Current situational information (e.g., active goals, health state, environmental cues).

        Returns:
            True if the target should be inhibited, False otherwise.
        """
        logger.debug(f"Evaluating inhibition for target: {target.description} (Type: {target.target_type}, ID: {target.target_id}, Activation: {target.activation:.2f})")

        # --- Placeholder Inhibition Logic ---
        # In a real implementation, this would involve:
        # 1. Checking against current goals (is the action counter-productive?).
        # 2. Consulting rules or learned constraints from semantic memory.
        # 3. Evaluating potential negative outcomes (risk assessment, possibly from DecisionMaker or memory).
        # 4. Considering current health/resource status (e.g., inhibit costly actions if energy is low).
        # 5. Assessing conflict with other active goals or plans.
        # 6. Comparing the target's activation against an inhibition threshold.

        # Enhanced example: Inhibit based on context signals, goal conflicts, or health state.
        inhibit = False
        reason = "No inhibition criteria met."
        context = context or {} # Ensure context is a dict

        # 1. Check Context Signals
        if context.get("signal") == "stop":
            inhibit = True
            reason = "Stop signal received."
            logger.info(f"Inhibiting target '{target.description}': {reason}")
            return True # Stop signals usually override other checks

        # 2. Check Goal Conflicts (Illustrative - requires Goal.conflicts_with method)
        if self.goal_manager:
            active_goals: List[Goal] = self.goal_manager.get_active_goals()
            for goal in active_goals:
                 # Hypothetical conflict check method on Goal object
                 # if hasattr(goal, 'conflicts_with') and goal.conflicts_with(target):
                 # Simplified check: inhibit if target description matches an active goal's negation or avoidance
                 target_desc_lower = target.description.lower()
                 goal_desc_lower = goal.description.lower()
                 is_negation = f"do not {goal_desc_lower}" in target_desc_lower
                 # Check 'avoid' case explicitly: starts with 'avoid ' and the rest matches the goal
                 avoid_prefix = "avoid "
                 is_avoidance = target_desc_lower.startswith(avoid_prefix) and target_desc_lower[len(avoid_prefix):] == goal_desc_lower
                 
                 if is_negation or is_avoidance:
                     inhibit = True
                     reason = f"Target conflicts with active goal '{goal.description}' (Priority: {goal.priority})."
                     break # Stop checking goals once a conflict is found
        # Fallback simplified check if GoalManager not available or no conflict found yet
        if not inhibit and context.get("high_priority_goal") == "safety" and "risky" in target.description.lower():
             inhibit = True
             reason = "Action conflicts with high-priority safety goal (context flag)."

        # 3. Check Health State (Only if not already inhibited by goals/signals)
        if not inhibit:
            health_state = context.get("health_state", HealthState.NORMAL)
            # Inhibit high-activation/costly actions if health is poor
            if health_state in [HealthState.IMPAIRED, HealthState.CRITICAL] and target.activation > 0.5:
                 inhibit = True
                 reason = f"Health state ({health_state.value}) requires inhibition of non-critical/high-activation actions."
            elif health_state == HealthState.FATIGUED and target.activation > 0.8: # Higher threshold for fatigue
                 inhibit = True
                 reason = f"Health state ({health_state.value}) suggests inhibiting highly demanding actions."

        # 4. Check Learned Constraints (Placeholder - requires Memory integration) (Only if not already inhibited)
        if not inhibit and self.memory_manager:
             # Query semantic memory for rules/constraints related to the target action/type
             # Example query: "constraints action:{target.action_name}" or "rules type:{target.target_type}"
             query = f"constraint related to {target.description}" # Simplified query
             # learned_constraints = self.memory_manager.retrieve(query=query, memory_type=MemoryType.SEMANTIC, limit=3)
             learned_constraints = [] # Placeholder result

             if learned_constraints:
                  # Evaluate if any retrieved constraint mandates inhibition
                  # Example: if any constraint says "never do X" and X matches target
                  # if any("never" in str(constraint.content).lower() and target.description in str(constraint.content).lower() for constraint in learned_constraints):
                  #     inhibit = True
                  #     reason = f"Action violates learned constraint: {learned_constraints[0].content}" # Show first constraint found
                  logger.info(f"Found {len(learned_constraints)} potential constraints related to '{target.description}'. Evaluating...")
                  # Placeholder: Assume a constraint is found for demonstration
                  if "risky" in target.description: # Simple check
                       inhibit = True
                       reason = "Action violates learned constraint (Placeholder: identified as risky)."

        if inhibit:
            logger.info(f"Inhibiting target '{target.description}': {reason}")
        else:
            logger.debug(f"No inhibition required for target '{target.description}'.")

        return inhibit
        # --- End Placeholder ---
