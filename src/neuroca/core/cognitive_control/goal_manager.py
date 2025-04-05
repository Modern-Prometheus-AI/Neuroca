"""
Goal Management Component for NeuroCognitive Architecture (NCA).

This module manages the system's goals, including their representation,
prioritization, activation status, and relationship to ongoing plans and actions.
It plays a crucial role in directing the system's behavior.

Key functionalities:
- Representing goals (short-term, long-term, hierarchical).
- Prioritizing goals based on urgency, importance, and context.
- Tracking the status of active goals (pending, active, completed, failed).
- Resolving conflicts between competing goals.
- Communicating active goals to other cognitive components (Planner, DecisionMaker).
"""

import logging
from typing import List, Dict, Any, Optional, Set
from enum import Enum, auto
import time

# Import necessary components for potential integration
from neuroca.memory.manager import MEMORY_MANAGER_COMPONENT_ID # Import the constant
from neuroca.core.health.dynamics import HealthState, HealthDynamicsManager # Example for context checking

# Configure logger
logger = logging.getLogger(__name__)

class GoalStatus(Enum):
    """Status of a goal."""
    PENDING = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    FAILED = auto()
    SUSPENDED = auto()

class Goal:
    """Represents a single goal within the system."""
    def __init__(self, description: str, priority: int = 5, parent_goal: Optional['Goal'] = None):
        self.id = f"goal_{hash(description)}" # Simple ID generation
        self.description = description
        self.priority = priority # Lower number means higher priority (e.g., 1-10)
        self.status = GoalStatus.PENDING
        self.sub_goals: List['Goal'] = []
        self.parent_goal = parent_goal
        self.activation = 0.0 # How strongly the goal is currently driving behavior

    def activate(self):
        """Activate the goal."""
        self.status = GoalStatus.ACTIVE
        self.activation = 1.0 # Or calculate based on priority/context
        logger.info(f"Goal activated: '{self.description}' (Priority: {self.priority})")

    def update_status(self, status: GoalStatus):
        """Update the goal's status."""
        if self.status != status:
            self.status = status
            logger.info(f"Goal '{self.description}' status updated to {status.name}")
            if status in [GoalStatus.COMPLETED, GoalStatus.FAILED]:
                self.activation = 0.0

class GoalManager:
    """
    Manages the hierarchy and status of the system's goals.
    """
    def __init__(self, health_manager=None, memory_manager=None):
        """
        Initialize the GoalManager.

        Args:
            health_manager: Instance of HealthDynamicsManager.
            memory_manager: Instance of MemoryManager.
        """
        self.goals: Dict[str, Goal] = {} # Store all goals by ID
        self.active_goals: Set[str] = set() # IDs of currently active goals
        self.health_manager = health_manager
        self.memory_manager = memory_manager
        logger.info("GoalManager initialized.")
        # TODO: Implement dependency injection properly later

    def add_goal(self, description: str, priority: int = 5, parent_goal_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Optional[Goal]:
        """
        Add a new goal to the system, potentially adjusting priority based on context.

        Args:
            description: Description of the goal.
            priority: Priority level (lower is higher).
            parent_goal_id: ID of the parent goal, if this is a sub-goal.

        Returns:
            The created Goal object, or None if parent ID is invalid.
        """
        context = context or {}
        parent = self.goals.get(parent_goal_id) if parent_goal_id else None
        if parent_goal_id and not parent:
            logger.error(f"Cannot add goal '{description}': Parent goal ID '{parent_goal_id}' not found.")
            return None

        # --- Context-Based Priority Adjustment (Example) ---
        adjusted_priority = priority
        health_state = context.get("health_state", HealthState.NORMAL)
        if health_state == HealthState.CRITICAL and "survival" not in description.lower():
             adjusted_priority += 3 # Deprioritize non-survival goals in critical state
        elif health_state == HealthState.STRESSED and "urgent" in description.lower():
             adjusted_priority -= 1 # Prioritize urgent goals when stressed
        adjusted_priority = max(1, min(10, adjusted_priority)) # Clamp priority 1-10
        if adjusted_priority != priority:
             logger.info(f"Adjusted priority for goal '{description}' from {priority} to {adjusted_priority} based on context (Health: {health_state.value}).")
        # --- End Adjustment ---

        # Handle potential hash collisions for ID generation
        original_description = description
        collision_count = 0
        while True:
             current_description = f"{original_description}" + (f"_{collision_count}" if collision_count > 0 else "")
             goal = Goal(description=current_description, priority=adjusted_priority, parent_goal=parent)
             if goal.id not in self.goals:
                 if collision_count > 0:
                      logger.warning(f"Goal ID collision for '{original_description}'. Generated unique ID {goal.id} using description '{current_description}'.")
                 break # Unique ID found
             
             collision_count += 1
             if collision_count > 5: # Limit attempts to prevent infinite loop
                  logger.error(f"Could not generate unique ID for goal '{original_description}' after {collision_count} attempts.")
                  return None # Failed to add goal

        self.goals[goal.id] = goal
        if parent:
            parent.sub_goals.append(goal)

        logger.info(f"Added goal: '{description}' (ID: {goal.id}, Priority: {adjusted_priority})")
        # Potentially activate based on priority/context immediately?
        # For now, activation is separate.
        return goal

    def activate_goal(self, goal_id: str, context: Optional[Dict[str, Any]] = None):
        """
        Activate a specific goal, checking context first.

        Args:
            goal_id: The ID of the goal to activate.
            context: Current situational information.
        """
        context = context or {}
        goal = self.goals.get(goal_id)
        if not goal:
            logger.warning(f"Cannot activate goal: ID '{goal_id}' not found.")
            return

        # --- Context Check Before Activation (Example) ---
        health_state = context.get("health_state", HealthState.NORMAL)
        if health_state in [HealthState.IMPAIRED, HealthState.CRITICAL] and goal.priority > 3: # Don't activate low-priority goals if impaired
             logger.warning(f"Cannot activate goal '{goal.description}' (Priority: {goal.priority}) in {health_state.value} state.")
             return
        # --- End Context Check ---

        goal.activate()
        self.active_goals.add(goal_id)
        # Potentially suspend lower-priority conflicting goals?
        self.resolve_conflicts() # Check conflicts upon activation

    def update_goal_status(self, goal_id: str, status: GoalStatus):
        """
        Update the status of a specific goal.

        Args:
            goal_id: The ID of the goal to update.
            status: The new status for the goal.
        """
        goal = self.goals.get(goal_id)
        if goal:
            goal.update_status(status)
            if status != GoalStatus.ACTIVE and goal_id in self.active_goals:
                self.active_goals.remove(goal_id)
            elif status == GoalStatus.ACTIVE and goal_id not in self.active_goals:
                 self.active_goals.add(goal_id) # Should usually go through activate_goal
        else:
            logger.warning(f"Cannot update status for goal: ID '{goal_id}' not found.")

    def get_active_goals(self, sorted_by_priority: bool = True) -> List[Goal]:
        """
        Get a list of currently active goals.

        Args:
            sorted_by_priority: If True, sort goals by priority (highest first).

        Returns:
            A list of active Goal objects.
        """
        active_goal_objects = [self.goals[gid] for gid in self.active_goals if gid in self.goals]
        if sorted_by_priority:
            active_goal_objects.sort(key=lambda g: g.priority)
        return active_goal_objects

    def get_highest_priority_active_goal(self) -> Optional[Goal]:
        """
        Get the currently active goal with the highest priority.

        Returns:
            The highest priority active Goal object, or None if no goals are active.
        """
        active = self.get_active_goals(sorted_by_priority=True)
        return active[0] if active else None

    # --- Placeholder Methods for Future Integration ---
    def resolve_conflicts(self):
        """Identify and resolve conflicts between active goals."""
        # Logic to detect conflicting goals (e.g., mutually exclusive outcomes)
        # and decide which to prioritize or suspend.
        logger.debug("Checking for goal conflicts...")
        # Placeholder: Simple conflict check - suspend lower priority goals if health is poor
        health_state = HealthState.NORMAL # Default
        if self.health_manager:
            # Get overall health or relevant component health
            # Simplified: Check the health of the GoalManager component itself, if registered
            # Using MEMORY_MANAGER_COMPONENT_ID as placeholder, adjust if GoalManager has its own ID
            manager_health = self.health_manager.get_component_health(MEMORY_MANAGER_COMPONENT_ID) 
            if manager_health: 
                health_state = manager_health.state
                logger.debug(f"Resolve conflicts using health state: {health_state.value}")
            else:
                 logger.warning(f"Could not get health state for component '{MEMORY_MANAGER_COMPONENT_ID}' during conflict resolution.")
        else:
             logger.debug("Health manager not available for conflict resolution context.")


        if health_state in [HealthState.STRESSED, HealthState.FATIGUED, HealthState.IMPAIRED, HealthState.CRITICAL]:
            active = self.get_active_goals(sorted_by_priority=True)
            if len(active) > 1:
                 highest_priority = active[0].priority
                 for goal in active[1:]:
                     if goal.priority > highest_priority + 2: # Suspend much lower priority goals
                          logger.info(f"Suspending goal '{goal.description}' (Priority: {goal.priority}) due to conflict/resource constraints (Health: {health_state.value}).")
                          self.update_goal_status(goal.id, GoalStatus.SUSPENDED)

        # More complex logic would involve checking resource needs vs. availability,
        # checking for mutually exclusive goal outcomes, etc.
