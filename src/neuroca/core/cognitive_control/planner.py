"""
Task Planning Component for NeuroCognitive Architecture (NCA).

This module implements the planning capabilities within the executive functions.
It is responsible for generating sequences of actions (plans) to achieve
specified goals, considering the current state, available resources (including
memory and health), and potential obstacles.

Key functionalities:
- Goal decomposition into sub-goals and tasks.
- Action sequence generation.
- Plan adaptation based on execution feedback and changing conditions.
- Resource estimation for planned actions.
"""

import logging
from typing import Any, Optional

from neuroca.core.health.dynamics import HealthState  # Example for context checking

# Import necessary components for potential integration
from neuroca.memory.manager import MemoryItem, MemoryType  # Example

# Configure logger
logger = logging.getLogger(__name__)

class PlanStep:
    """Represents a single step within a larger plan."""
    def __init__(self, action: str, parameters: Optional[dict[str, Any]] = None, estimated_cost: float = 0.1):
        self.action = action
        self.parameters = parameters or {}
        self.estimated_cost = estimated_cost # e.g., estimated energy/time cost
        self.status = "pending" # pending, executing, completed, failed

class Plan:
    """Represents a sequence of actions to achieve a goal."""
    def __init__(self, goal: str, steps: list[PlanStep]):
        self.goal = goal
        self.steps = steps
        self.current_step_index = 0
        self.status = "pending" # pending, executing, completed, failed, aborted

    def get_next_step(self) -> Optional[PlanStep]:
        """Get the next step to execute."""
        if self.status not in ["pending", "executing"]:
            return None
        if self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
            step.status = "executing"
            self.status = "executing"
            return step
        else:
            self.status = "completed"
            return None

    def update_step_status(self, step_index: int, status: str, message: Optional[str] = None):
        """Update the status of a specific step."""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].status = status
            logger.info(f"Plan '{self.goal}': Step {step_index} ('{self.steps[step_index].action}') status updated to {status}. {message or ''}")
            if status == "completed":
                 self.current_step_index += 1
                 if self.current_step_index >= len(self.steps):
                     self.status = "completed"
                     logger.info(f"Plan '{self.goal}' completed successfully.")
            elif status == "failed":
                 self.status = "failed"
                 logger.error(f"Plan '{self.goal}' failed at step {step_index}: {message or 'Unknown reason'}")
        else:
             logger.warning(f"Attempted to update invalid step index {step_index} for plan '{self.goal}'")


class Planner:
    """
    Generates and manages plans for achieving goals.

    Integrates with memory, health, and other cognitive components to create
    realistic and adaptive plans.
    """
    def __init__(self, memory_manager=None, health_manager=None, goal_manager=None):
        """
        Initialize the Planner.

        Args:
            memory_manager: Instance of MemoryManager for memory access.
            health_manager: Instance of HealthDynamicsManager for health status.
            goal_manager: Instance of GoalManager for goal context.
        """
        logger.info("Planner initialized.")
        self.memory_manager = memory_manager
        self.health_manager = health_manager
        self.goal_manager = goal_manager
        # NOTE: Consider implementing a proper dependency injection framework
        # for managing manager instances instead of direct constructor passing.

    def generate_plan(self, goal_description: str, context: Optional[dict[str, Any]] = None) -> Optional[Plan]:
        """
        Generate a plan to achieve the specified goal description given the context.

        Args:
            goal: The objective to achieve.
            context: Current situational information (e.g., state, resources).

        Returns:
            A Plan object, or None if planning fails.
        """
        logger.info(f"Generating plan for goal: {goal_description}")
        context = context or {} # Ensure context is a dict

        # --- Enhanced Placeholder Planning Logic ---

        # 0. Get Goal Details (if GoalManager is available)
        context.get("goal_priority", 5) # Default priority
        # if self.goal_manager:
        #     active_goal = self.goal_manager.get_goal_by_description(goal_description) # Assumes such a method exists
        #     if active_goal:
        #         goal_priority = active_goal.priority
        #     else:
        #         logger.warning(f"Goal '{goal_description}' not found in GoalManager during planning.")

        # 1. Check Health Status (Example)
        # Assume health_manager provides component health, get overall or relevant component state
        health_state = context.get("health_state", HealthState.NORMAL) # Get from context or default
        # if self.health_manager:
        #     planner_health = self.health_manager.get_component_health("planner_component") # Hypothetical ID
        #     if planner_health: health_state = planner_health.state

        if health_state in [HealthState.IMPAIRED, HealthState.CRITICAL]:
            logger.warning(f"Cannot generate complex plan in {health_state.value} state. Aborting planning for '{goal_description}'.")
            return None # Cannot plan in severely impaired state

        # 2. Retrieve Relevant Knowledge
        semantic_knowledge: list[MemoryItem] = []
        episodic_knowledge: list[MemoryItem] = []
        if self.memory_manager:
            try:
                # Search semantic memory for general plans/procedures
                semantic_knowledge = self.memory_manager.retrieve(
                    query=f"procedure for {goal_description}", 
                    memory_type=MemoryType.SEMANTIC,
                    limit=1 # Look for one good procedure first
                )
                # Search episodic memory for specific past attempts (successful or failed)
                episodic_knowledge = self.memory_manager.retrieve(
                    query=f"past plan {goal_description}", 
                    memory_type=MemoryType.EPISODIC,
                    limit=3 # Look at a few recent attempts
                )
                logger.debug(f"Retrieved {len(semantic_knowledge)} semantic, {len(episodic_knowledge)} episodic memories for planning.")
            except Exception as e:
                 logger.error(f"Error retrieving knowledge during planning: {e}")
        else:
            logger.debug("MemoryManager not available for planning knowledge retrieval.")

        # 3. Decompose Goal & Select Actions (using knowledge or falling back)
        plan = None
        
        # --- Try using retrieved knowledge first ---
        if semantic_knowledge:
            item = semantic_knowledge[0] # Use the first relevant procedure found
            # Example expected structure for a procedure stored in memory content:
            # { "type": "procedure", "steps": [ {"action": "...", "parameters": {...}, "cost": 0.1}, ... ] }
            if isinstance(item.content, dict) and item.content.get("type") == "procedure":
                known_procedure = item.content
                logger.info(f"Attempting to use known procedure from semantic memory (ID: {item.id}) for goal '{goal_description}'.")
                try:
                    procedure_steps = known_procedure.get("steps")
                    if isinstance(procedure_steps, list) and procedure_steps:
                         # Validate and create PlanStep objects
                         steps = []
                         valid_procedure = True
                         for i, step_info in enumerate(procedure_steps):
                              if isinstance(step_info, dict) and "action" in step_info:
                                   steps.append(PlanStep(action=step_info["action"], 
                                                         parameters=step_info.get("parameters", {}), 
                                                         estimated_cost=step_info.get("cost", 0.1)))
                              else:
                                   logger.warning(f"Invalid step format in known procedure (step {i}): {step_info}")
                                   valid_procedure = False
                                   break
                         
                         if valid_procedure and steps:
                              plan = Plan(goal=goal_description, steps=steps)
                              logger.info(f"Successfully constructed plan with {len(steps)} steps from semantic knowledge.")
                         elif not steps:
                              logger.warning("Known procedure found but contained no valid steps.")
                    else:
                         logger.warning("Known procedure found but 'steps' list was missing or empty.")
                except Exception as e:
                    logger.error(f"Error constructing plan from known procedure: {e}")
                    plan = None # Failed to use the procedure
            else:
                 logger.warning(f"Retrieved semantic knowledge (ID: {item.id}) was not a valid procedure dictionary.")
        # This block was duplicated and incorrectly indented, removing the duplicate part.
        # The correct block starts below.

        if not plan and episodic_knowledge:
             # Attempt to adapt a plan from a similar past episode (more complex logic needed here)
             # Placeholder: Just log that we found episodic memories
             logger.info(f"Found {len(episodic_knowledge)} related past episodes. Adaptation logic not implemented.")
             # plan = adapt_plan_from_episode(episodic_knowledge[0], context) # Hypothetical function
        # --- End Knowledge Retrieval ---

        # Fallback to generic decomposition if no plan generated from knowledge
        if not plan:
            logger.debug(f"No knowledge-based or rule-based plan found for '{goal_description}'. Attempting generic decomposition.")
            steps = []
            # --- Generic Decomposition Example ---
            # Simple approach: treat words as potential actions/objects
            words = goal_description.lower().split()
            if len(words) > 0:
                 # Assume first word is the primary action
                 action_verb = words[0]
                 action_object = " ".join(words[1:]) if len(words) > 1 else "default_target"
                 
                 # Create steps based on this simple parse
                 steps.append(PlanStep(action=f"prepare_{action_verb}", parameters={"target": action_object}, estimated_cost=0.2))
                 steps.append(PlanStep(action=f"execute_{action_verb}", parameters={"target": action_object}, estimated_cost=0.6))
                 steps.append(PlanStep(action=f"verify_{action_verb}", parameters={"target": action_object}, estimated_cost=0.2))
                 
                 logger.info(f"Created generic 3-step plan based on goal words: {action_verb}, {action_object}")
            else:
                 logger.warning("Cannot decompose empty goal description.")
                 
            # --- Sub-goal Decomposition Placeholder (Could be integrated here) ---
            # if self.goal_manager and len(steps) > 5: # Example: If plan is too long, try sub-goals
            #     logger.info(f"Decomposing complex task '{goal_description}' into sub-goals.")
            #     # ... (sub-goal logic as before) ...
            # --- End Sub-goal Decomposition ---
                 
            # --- Rule-Based Decomposition (Now acts as refinement/alternative) ---
            # Example: If generic decomposition seems too simple, try specific rules
            if len(steps) <= 1: # If generic plan was very basic
                 rule_based_steps = []
                 if "make" in goal_description.lower() and "tea" in goal_description.lower():
                     if health_state == HealthState.FATIGUED:
                         logger.info("Applying simplified 'make tea' rule due to FATIGUED state.")
                         rule_based_steps = [ PlanStep(action="boil_water", estimated_cost=0.4), PlanStep(action="make_tea_simple", estimated_cost=0.2) ]
                     else:
                         logger.info("Applying standard 'make tea' rule.")
                         rule_based_steps = [
                             PlanStep(action="find_kettle", estimated_cost=0.1), PlanStep(action="fill_kettle", parameters={"water_level": "full"}, estimated_cost=0.1),
                             PlanStep(action="boil_water", estimated_cost=0.3), PlanStep(action="find_mug_and_tea_bag", estimated_cost=0.1),
                             PlanStep(action="pour_water", estimated_cost=0.1), PlanStep(action="steep_tea", parameters={"duration_seconds": 180}, estimated_cost=0.05),
                         ]
                 elif "resolve" in goal_description.lower() and ("dependency" in goal_description.lower() or "conflict" in goal_description.lower()):
                      logger.info("Applying 'resolve dependency/conflict' rule.")
                      target = context.get("target_entity", "unknown")
                      rule_based_steps = [
                          PlanStep(action="analyze_situation", parameters={"target": target}, estimated_cost=0.5), PlanStep(action="identify_root_cause", estimated_cost=0.4),
                          PlanStep(action="generate_solutions", estimated_cost=0.3), PlanStep(action="select_best_solution", estimated_cost=0.1),
                          PlanStep(action="implement_solution", estimated_cost=0.4), PlanStep(action="verify_resolution", estimated_cost=0.2),
                      ]
                 # Add more rules...

                 if rule_based_steps:
                      logger.info("Replacing generic plan with rule-based plan.")
                      steps = rule_based_steps
            # --- End Rule-Based Decomposition ---

            if steps:
                 plan = Plan(goal=goal_description, steps=steps)
            else:
                 logger.error(f"Failed to generate any steps for goal: {goal_description}")

        # 4. Final Checks & Return (Resource validation, etc.)
        if plan:
             # NOTE: Implement plan validation before returning.
             # This should check estimated resource costs against available resources
             # reported by the health_manager.
             logger.info(f"Generated plan with {len(plan.steps)} steps for goal: {goal_description} (Health State: {health_state.value})")
             return plan
        else:
             logger.warning(f"No planning strategy found for goal: {goal_description}")
             return None
        # --- End Enhanced Placeholder ---

    def replan(self, failed_plan: Plan, reason: str, context: Optional[dict[str, Any]] = None) -> Optional[Plan]:
        """
        Generate a new plan after a previous plan failed.

        Args:
            failed_plan: The plan that failed.
            reason: The reason for the failure.
            context: Current situational information.

        Returns:
            A new Plan object, or None if replanning fails.
        """
        logger.warning(f"Replanning required for goal '{failed_plan.goal}' due to failure: {reason}")
        # --- Placeholder Replanning Logic ---
        # 1. Analyze the failure reason and context.
        # 2. Identify the problematic step(s).
        # 3. Retrieve alternative strategies or knowledge from memory (placeholder).
        # alternatives = self.memory_manager.retrieve(query=f"alternative for {failed_plan.steps[failed_plan.current_step_index].action}")
        
        # 4. Generate a revised or completely new plan.
        
        # Example: If the failure was resource-related, maybe try a less costly alternative step?
        if "resource" in reason.lower() or "energy" in reason.lower():
             logger.info("Replanning: Attempting less costly alternative due to resource failure.")
             # Try generating a new plan, potentially with constraints or simpler steps
             # This might involve passing modified context to generate_plan
             modified_context = context.copy() if context else {}
             modified_context["planning_constraint"] = "low_resource"
             new_plan = self.generate_plan(failed_plan.goal, modified_context)
             if new_plan:
                 return new_plan
             # Fallback if no low-resource plan generated: skip the step? (Risky)

        # Example: If a specific action failed (e.g., 'find_kettle'), try an alternative action?
        failed_step_index = failed_plan.current_step_index
        if 0 <= failed_step_index < len(failed_plan.steps):
             failed_action = failed_plan.steps[failed_step_index].action
             if failed_action == "find_kettle":
                 logger.info("Replanning: Kettle not found, trying alternative 'use_microwave'.")
                 new_steps = failed_plan.steps[:failed_step_index] # Steps before failure
                 # Replace failed step and potentially subsequent steps
                 new_steps.append(PlanStep(action="use_microwave", estimated_cost=0.2)) 
                 # Need to adjust subsequent steps that depended on the kettle... complex!
                 # For placeholder, just replace and hope subsequent steps still make sense or fail later.
                 new_steps.extend(failed_plan.steps[failed_step_index+1:]) 
                 if new_steps:
                      return Plan(goal=failed_plan.goal, steps=new_steps)

        # Default fallback: Try generating the plan from scratch again (original simplistic retry)
        logger.info("Replanning: Defaulting to generating plan from scratch.")
        return self.generate_plan(failed_plan.goal, context) 
        # --- End Enhanced Placeholder ---
