"""
Goal Management Component for NeuroCognitive Architecture (NCA).

This module manages the system's goals, including their representation,
prioritization, activation status, and relationships to ongoing plans and actions.
It plays a crucial role in directing the system's behavior through goal-oriented
cognitive control.

Key functionalities:
- Representing goals with hierarchical relationships and dependencies
- Prioritizing goals dynamically based on urgency, importance, and context
- Tracking the status of active goals through their lifecycle
- Detecting and resolving conflicts between competing goals
- Managing goal persistence in memory for learning from past experiences
- Adapting goal management strategies based on health state
- Communicating active goals to other cognitive components
"""

import logging
import time
from enum import Enum, auto
from typing import Any, Optional

from neuroca.core.health.dynamics import (  # Example for context checking
    HealthState,
)

# Import necessary components for potential integration

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
    """
    Represents a single goal within the system with biological-inspired properties.
    
    Goals have hierarchical relationships (parent-child), dependencies, activation levels,
    and track their lifecycle with timestamps and metadata.
    """
    def __init__(self, description: str, priority: int = 5, parent_goal: Optional['Goal'] = None):
        self.id = f"goal_{hash(description)}" # Simple ID generation
        self.description = description
        self.priority = priority # Lower number means higher priority (e.g., 1-10)
        self.status = GoalStatus.PENDING
        self.sub_goals: list['Goal'] = []
        self.parent_goal = parent_goal
        self.activation = 0.0 # How strongly the goal is currently driving behavior
        
        # Additional metadata for biological plausibility
        self.created_at = time.time()
        self.last_updated_at = self.created_at
        self.activated_at = None  # When the goal was last activated
        self.completion_rate = 0.0  # Progress towards completion (0.0-1.0)
        self.emotional_salience = 0.5  # How emotionally important this goal is (0.0-1.0)
        self.dependencies: set[str] = set()  # IDs of goals that must be completed before this one
        self.resource_requirements = {
            "attention": 0.2,  # Default attention requirement
            "energy": 0.2,     # Default energy requirement
        }
        self.tags: list[str] = []  # Semantic tags for goal categorization
        
        # Learning-related attributes
        self.success_probability = 0.5  # Initial estimate of success probability
        self.previous_attempts = 0  # Number of times this goal has been attempted
        self.previous_successes = 0  # Number of successful completions
        
        # Conflict detection attributes
        self._incompatible_with: set[str] = set()  # IDs of goals this goal conflicts with
        
    def activate(self, context: Optional[dict[str, Any]] = None):
        """
        Activate the goal, potentially adjusting activation based on context.
        
        Args:
            context: Current situational context that may affect activation.
        """
        self.status = GoalStatus.ACTIVE
        self.activation = 1.0  # Base activation
        self.activated_at = time.time()
        self.last_updated_at = self.activated_at
        
        # Adjust activation based on context if provided
        if context:
            # Example: Emotional state affects activation
            emotional_state = context.get("emotional_state", 0.5)
            if emotional_state > 0.7 and self.emotional_salience > 0.7:
                # Strong emotions + high emotional salience = higher activation
                self.activation = min(1.5, self.activation * 1.3)
            
            # Example: Health state affects activation
            health_state = context.get("health_state", HealthState.NORMAL)
            if health_state == HealthState.FATIGUED:
                # Harder to maintain high activation when fatigued
                self.activation *= 0.8
                
        logger.info(f"Goal activated: '{self.description}' (Priority: {self.priority}, Activation: {self.activation:.2f})")

    def update_status(self, status: GoalStatus, context: Optional[dict[str, Any]] = None):
        """
        Update the goal's status and related properties.
        
        Args:
            status: The new status for the goal.
            context: Current situational context.
        """
        if self.status != status:
            previous_status = self.status
            self.status = status
            self.last_updated_at = time.time()
            
            if status == GoalStatus.COMPLETED:
                self.activation = 0.0
                self.completion_rate = 1.0
                self.previous_attempts += 1
                self.previous_successes += 1
                self.success_probability = self.previous_successes / self.previous_attempts
                logger.info(f"Goal '{self.description}' completed successfully.")
                
            elif status == GoalStatus.FAILED:
                self.activation = 0.0
                self.previous_attempts += 1
                self.success_probability = self.previous_successes / self.previous_attempts
                logger.info(f"Goal '{self.description}' failed.")
                
            elif status == GoalStatus.SUSPENDED:
                # Reduce activation but don't eliminate it completely
                self.activation *= 0.3
                logger.info(f"Goal '{self.description}' suspended. Activation reduced to {self.activation:.2f}.")
            
            else:
                logger.info(f"Goal '{self.description}' status changed from {previous_status.name} to {status.name}.")
    
    def update_completion_rate(self, rate: float):
        """
        Update the goal's completion rate.
        
        Args:
            rate: New completion rate (0.0-1.0).
        """
        if 0.0 <= rate <= 1.0:
            self.completion_rate = rate
            self.last_updated_at = time.time()
            logger.debug(f"Goal '{self.description}' completion rate updated to {rate:.2f}.")
            
            # Adjust activation based on progress
            if self.status == GoalStatus.ACTIVE:
                # As we make more progress, goal becomes more activated
                self.activation = min(1.0, 0.5 + (rate * 0.5))
        else:
            logger.warning(f"Invalid completion rate {rate} for goal '{self.description}'. Must be between 0.0 and 1.0.")
    
    def add_dependency(self, goal_id: str):
        """
        Add a goal dependency.
        
        Args:
            goal_id: ID of the goal that must be completed before this one.
        """
        self.dependencies.add(goal_id)
        logger.debug(f"Added dependency on goal '{goal_id}' for goal '{self.description}'.")
    
    def remove_dependency(self, goal_id: str):
        """
        Remove a goal dependency.
        
        Args:
            goal_id: ID of the goal to remove as a dependency.
        """
        if goal_id in self.dependencies:
            self.dependencies.remove(goal_id)
            logger.debug(f"Removed dependency on goal '{goal_id}' for goal '{self.description}'.")
    
    def mark_incompatible_with(self, goal_id: str):
        """
        Mark this goal as incompatible with another goal.
        
        Args:
            goal_id: ID of the incompatible goal.
        """
        self._incompatible_with.add(goal_id)
        logger.debug(f"Marked goal '{self.description}' as incompatible with goal '{goal_id}'.")
    
    def is_incompatible_with(self, goal_id: str) -> bool:
        """
        Check if this goal is incompatible with another goal.
        
        Args:
            goal_id: ID of the goal to check for compatibility.
            
        Returns:
            True if goals are incompatible, False otherwise.
        """
        return goal_id in self._incompatible_with
    
    def decay_activation(self, decay_rate: float = 0.05):
        """
        Apply natural decay to goal activation over time.
        
        Args:
            decay_rate: The rate at which activation decays (0.0-1.0).
        """
        if self.status == GoalStatus.ACTIVE:
            self.activation = max(0.1, self.activation * (1 - decay_rate))
            logger.debug(f"Goal '{self.description}' activation decayed to {self.activation:.2f}.")
    
    def can_be_activated(self, active_goals: list[str], completed_goals: list[str]) -> bool:
        """
        Check if the goal can be activated based on dependencies.
        
        Args:
            active_goals: List of currently active goal IDs.
            completed_goals: List of completed goal IDs.
            
        Returns:
            True if the goal can be activated, False otherwise.
        """
        # Check if all dependencies are satisfied
        for dep_id in self.dependencies:
            if dep_id not in completed_goals:
                logger.debug(f"Goal '{self.description}' cannot be activated: dependency '{dep_id}' not completed.")
                return False
        
        # Check for incompatibilities with active goals
        for active_id in active_goals:
            if self.is_incompatible_with(active_id):
                logger.debug(f"Goal '{self.description}' cannot be activated: incompatible with active goal '{active_id}'.")
                return False
        
        return True

# Component ID for health monitoring
GOAL_MANAGER_COMPONENT_ID = "cognitive_control.goal_manager"

class GoalManager:
    """
    Manages the system's goals with biologically-inspired properties.
    
    The GoalManager maintains a hierarchical structure of goals, tracks their statuses,
    manages their activations, detects and resolves conflicts, and integrates with
    memory systems for learning from past goal achievements.
    
    This component is responsible for the system's goal-oriented behavior, which
    is a key aspect of executive function in cognitive architectures.
    """
    def __init__(self, health_manager=None, memory_manager=None):
        """
        Initialize the GoalManager.

        Args:
            health_manager: Optional instance of HealthDynamicsManager.
            memory_manager: Optional instance of MemoryManager.
        """
        self.goals: dict[str, Goal] = {} # Store all goals by ID
        self.active_goals: set[str] = set() # IDs of currently active goals
        self.completed_goals: set[str] = set() # IDs of completed goals
        self.failed_goals: set[str] = set() # IDs of failed goals
        
        # Track goal status history for learning
        self.goal_history: dict[str, list[dict[str, Any]]] = {}
        
        # Dependencies and resources
        self.health_manager = health_manager
        self.memory_manager = memory_manager
        
        # Biological constraints
        self.max_concurrent_goals = 5  # Miller's 7±2
        self.min_activation_threshold = 0.2  # Goals below this are automatically suspended
        self.activation_decay_rate = 0.05  # Natural decay rate for goal activation
        
        # Resource tracking
        self.available_resources = {
            "attention": 1.0,
            "energy": 1.0
        }
        
        # Register with health system if available
        if self.health_manager:
            try:
                self.health_manager.register_component(
                    component_id=GOAL_MANAGER_COMPONENT_ID,
                    component_type="cognitive_control",
                    description="Goal management system",
                    initial_health=1.0  # Start with perfect health
                )
                logger.info(f"GoalManager registered with health system as {GOAL_MANAGER_COMPONENT_ID}")
            except Exception as e:
                logger.warning(f"Failed to register GoalManager with health system: {e}")
        
        logger.info("GoalManager initialized.")

    def add_goal(self, description: str, priority: int = 5, parent_goal_id: Optional[str] = None, context: Optional[dict[str, Any]] = None) -> Optional[Goal]:
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

    def activate_goal(self, goal_id: str, context: Optional[dict[str, Any]] = None):
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

    def get_active_goals(self, sorted_by_priority: bool = True) -> list[Goal]:
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

    def update_goal_status(self, goal_id: str, status: GoalStatus, context: Optional[dict[str, Any]] = None):
        """
        Update the status of a specific goal with context awareness.

        Args:
            goal_id: The ID of the goal to update.
            status: The new status for the goal.
            context: Current situational context.
        """
        goal = self.goals.get(goal_id)
        if not goal:
            logger.warning(f"Cannot update status for goal: ID '{goal_id}' not found.")
            return
            
        context = context or {}
        previous_status = goal.status
        goal.update_status(status, context)
        
        # Update active/completed/failed sets
        if status == GoalStatus.ACTIVE and goal_id not in self.active_goals:
            self.active_goals.add(goal_id)
        elif status != GoalStatus.ACTIVE and goal_id in self.active_goals:
            self.active_goals.remove(goal_id)
            
        if status == GoalStatus.COMPLETED:
            self.completed_goals.add(goal_id)
            if goal_id in self.failed_goals:
                self.failed_goals.remove(goal_id)
        elif status == GoalStatus.FAILED:
            self.failed_goals.add(goal_id)
            if goal_id in self.completed_goals:
                self.completed_goals.remove(goal_id)
        
        # Record goal status history for learning
        if goal_id not in self.goal_history:
            self.goal_history[goal_id] = []
            
        self.goal_history[goal_id].append({
            "from_status": previous_status.name if previous_status else None,
            "to_status": status.name,
            "timestamp": time.time(),
            "context": context.copy() if context else {},
        })
        
        # If completed or failed, store in memory if available
        if status in [GoalStatus.COMPLETED, GoalStatus.FAILED] and self.memory_manager:
            self._store_goal_in_memory(goal, status)
            
        # Check effect on dependent goals
        self._update_dependent_goals(goal_id, status)
        
        # If health manager is available, report cognitive operation
        if self.health_manager:
            operation_type = f"goal_{status.name.lower()}"
            self.health_manager.record_cognitive_operation(
                component_id=GOAL_MANAGER_COMPONENT_ID,
                operation_type=operation_type,
                complexity=goal.priority * 0.1,  # Higher priority goals are more cognitively demanding
                duration=0.1  # Placeholder duration
            )
        
        # Resolve conflicts if active goals changed
        if previous_status != GoalStatus.ACTIVE and status == GoalStatus.ACTIVE:
            self.resolve_conflicts()
            
    def _update_dependent_goals(self, goal_id: str, status: GoalStatus):
        """
        Update goals that depend on the specified goal.
        
        Args:
            goal_id: ID of the goal whose status changed.
            status: New status of the goal.
        """
        if status != GoalStatus.COMPLETED:
            return  # Only completed goals affect dependencies
            
        # Find all goals that have this goal as a dependency
        for _dependent_id, dependent_goal in self.goals.items():
            if goal_id in dependent_goal.dependencies:
                logger.debug(f"Goal '{dependent_goal.description}' dependency '{goal_id}' completed")
                
                # Check if all dependencies are now satisfied
                all_dependencies_met = True
                for dep_id in dependent_goal.dependencies:
                    if dep_id not in self.completed_goals:
                        all_dependencies_met = False
                        break
                        
                if all_dependencies_met and dependent_goal.status == GoalStatus.PENDING:
                    logger.info(f"All dependencies for goal '{dependent_goal.description}' are met, eligible for activation")
                    # Could auto-activate here, or just mark as eligible
                    # For now, we'll leave it pending but could be modified based on system design
    
    def activate_goal(self, goal_id: str, context: Optional[dict[str, Any]] = None):
        """
        Activate a specific goal with comprehensive context checking.

        Args:
            goal_id: The ID of the goal to activate.
            context: Current situational information.
        """
        context = context or {}
        goal = self.goals.get(goal_id)
        if not goal:
            logger.warning(f"Cannot activate goal: ID '{goal_id}' not found.")
            return

        # Check if max concurrent goals reached
        if len(self.active_goals) >= self.max_concurrent_goals:
            logger.warning(f"Cannot activate goal '{goal.description}': Maximum concurrent goals ({self.max_concurrent_goals}) reached.")
            
            # Try to make room by suspending lowest priority goal if this goal is higher priority
            lowest_priority_goal = self._get_lowest_priority_active_goal()
            if lowest_priority_goal and lowest_priority_goal.priority > goal.priority:
                logger.info(f"Suspending lowest priority goal '{lowest_priority_goal.description}' to make room for '{goal.description}'")
                self.update_goal_status(lowest_priority_goal.id, GoalStatus.SUSPENDED, context)
            else:
                return
        
        # Check health state constraints
        health_state = self._get_current_health_state(context)
        if health_state in [HealthState.IMPAIRED, HealthState.CRITICAL] and goal.priority > 3:
            logger.warning(f"Cannot activate goal '{goal.description}' (Priority: {goal.priority}) in {health_state.value} state.")
            return
            
        # Check resource availability
        required_resources = goal.resource_requirements
        for resource, amount in required_resources.items():
            if resource in self.available_resources and self.available_resources[resource] < amount:
                logger.warning(f"Cannot activate goal '{goal.description}': Insufficient {resource} resource ({self.available_resources[resource]:.2f} available, {amount:.2f} required)")
                return
                
        # Check dependencies and incompatibilities
        if not goal.can_be_activated(list(self.active_goals), list(self.completed_goals)):
            logger.warning(f"Cannot activate goal '{goal.description}': Dependencies not met or incompatible with active goals")
            return
            
        # Activate the goal with context
        goal.activate(context)
        self.active_goals.add(goal_id)
        
        # Allocate resources
        for resource, amount in required_resources.items():
            if resource in self.available_resources:
                self.available_resources[resource] -= amount
                logger.debug(f"Allocated {amount:.2f} {resource} to goal '{goal.description}', {self.available_resources[resource]:.2f} remaining")
        
        # Record in memory if available
        if self.memory_manager:
            self._record_goal_activation(goal, context)
            
        # Record cognitive operation
        if self.health_manager:
            self.health_manager.record_cognitive_operation(
                component_id=GOAL_MANAGER_COMPONENT_ID,
                operation_type="goal_activation",
                complexity=goal.priority * 0.1,  # Higher priority goals are more cognitively demanding
                duration=0.1  # Placeholder duration
            )
            
        # Resolve conflicts after activation
        self.resolve_conflicts()
    
    def _get_lowest_priority_active_goal(self) -> Optional[Goal]:
        """
        Find the active goal with the lowest priority (highest number).
        
        Returns:
            The lowest priority active Goal object, or None if no goals are active.
        """
        active = self.get_active_goals(sorted_by_priority=False)  # Don't sort, we'll find lowest
        if not active:
            return None
            
        lowest = active[0]
        for goal in active[1:]:
            if goal.priority > lowest.priority:  # Remember, higher number = lower priority
                lowest = goal
                
        return lowest
    
    def _get_current_health_state(self, context: Optional[dict[str, Any]] = None) -> HealthState:
        """
        Get the current health state from either context or health manager.
        
        Args:
            context: Optional context that may contain health state.
            
        Returns:
            Current health state.
        """
        # First check context
        if context and "health_state" in context:
            return context["health_state"]
            
        # Then check health manager
        if self.health_manager:
            manager_health = self.health_manager.get_component_health(GOAL_MANAGER_COMPONENT_ID)
            if manager_health:
                return manager_health.state
                
        # Default
        return HealthState.NORMAL
    
    def _record_goal_activation(self, goal: Goal, context: dict[str, Any]):
        """
        Record goal activation in memory for learning.
        
        Args:
            goal: The goal being activated.
            context: Current context.
        """
        if not self.memory_manager:
            return
            
        # Record in episodic memory
        try:
            content = {
                "type": "goal_activation",
                "goal_id": goal.id,
                "goal_description": goal.description,
                "priority": goal.priority,
                "activation": goal.activation,
                "timestamp": time.time(),
                "context": context
            }
            
            self.memory_manager.store(
                content=content,
                memory_type="episodic",
                metadata={
                    "type": "goal_event",
                    "goal_id": goal.id,
                    "event_type": "activation",
                    "priority": goal.priority
                },
                emotional_salience=min(0.8, 0.3 + (1.0 / goal.priority))  # Higher salience for higher priority (lower number)
            )
            
            logger.debug(f"Recorded goal activation in episodic memory: '{goal.description}'")
        except Exception as e:
            logger.error(f"Failed to record goal activation in memory: {e}")
    
    def _store_goal_in_memory(self, goal: Goal, status: GoalStatus):
        """
        Store goal completion or failure in memory for learning.
        
        Args:
            goal: The completed/failed goal.
            status: COMPLETED or FAILED.
        """
        if not self.memory_manager:
            return
            
        try:
            # Record in episodic memory
            content = {
                "type": "goal_completion" if status == GoalStatus.COMPLETED else "goal_failure",
                "goal_id": goal.id,
                "goal_description": goal.description,
                "priority": goal.priority,
                "timestamp": time.time(),
                "time_active": time.time() - (goal.activated_at or goal.created_at),
                "success_probability": goal.success_probability,
                "previous_attempts": goal.previous_attempts,
                "resource_requirements": goal.resource_requirements
            }
            
            emotional_salience = 0.5  # Base salience
            if status == GoalStatus.COMPLETED:
                # Higher priority completions are more salient
                emotional_salience = min(0.9, 0.5 + (1.0 / goal.priority))
            else:  # FAILED
                # Higher priority failures are more salient
                emotional_salience = min(0.9, 0.6 + (1.0 / goal.priority))
            
            self.memory_manager.store(
                content=content,
                memory_type="episodic",
                metadata={
                    "type": "goal_event",
                    "goal_id": goal.id,
                    "event_type": status.name.lower(),
                    "priority": goal.priority,
                    "success": status == GoalStatus.COMPLETED
                },
                emotional_salience=emotional_salience
            )
            
            # If we've had multiple goals of similar type, maybe consolidate into semantic memory
            self._consolidate_goal_patterns(goal, status)
            
            logger.debug(f"Recorded goal {status.name.lower()} in memory: '{goal.description}'")
        except Exception as e:
            logger.error(f"Failed to record goal in memory: {e}")
    
    def _consolidate_goal_patterns(self, goal: Goal, status: GoalStatus):
        """
        Check for patterns in similar goals that should be consolidated into semantic memory.
        
        Args:
            goal: The goal that was just completed or failed.
            status: COMPLETED or FAILED.
        """
        if not self.memory_manager:
            return
            
        # Look for similar goals in episodic memory
        try:
            # Construct a query for similar goals
            # This is a simplified example - in a real system, you might use more sophisticated
            # semantic matching to find similar goals
            query = f"type:goal_{status.name.lower()} description:{goal.description}"
            results = self.memory_manager.retrieve(
                query=query,
                memory_type="episodic",
                limit=5
            )
            
            # If we found multiple similar goals, consolidate a pattern
            if len(results) >= 3:
                # Calculate average success rate
                completions = sum(1 for r in results if r.content.get("success", False))
                success_rate = completions / len(results)
                
                # Create a semantic memory entry for this goal pattern
                pattern = {
                    "type": "goal_pattern",
                    "goal_description_pattern": goal.description,
                    "success_rate": success_rate,
                    "typical_priority": goal.priority,
                    "resource_requirements": goal.resource_requirements,
                    "recommendations": {
                        "should_attempt": success_rate > 0.5,
                        "optimal_health_state": "NORMAL" if success_rate > 0.7 else "OPTIMAL",
                        "resource_allocation": goal.resource_requirements
                    },
                    "supporting_evidence": len(results),
                    "derived_from": "pattern_recognition",
                    "created_at": time.time()
                }
                
                self.memory_manager.store(
                    content=pattern,
                    memory_type="semantic",
                    metadata={
                        "type": "goal_pattern",
                        "description_pattern": goal.description,
                        "success_rate": success_rate
                    }
                )
                
                logger.info(f"Consolidated goal pattern into semantic memory: '{goal.description}' (Success Rate: {success_rate:.2f})")
        except Exception as e:
            logger.error(f"Failed to consolidate goal patterns: {e}")
    
    def resolve_conflicts(self):
        """
        Identify and resolve conflicts between active goals using intelligent strategies.
        
        This implementation considers:
        1. Explicit incompatibilities between goals
        2. Resource constraints across all active goals
        3. Current health state of the system
        4. Goal priorities and activation levels
        """
        logger.debug("Resolving goal conflicts...")
        
        # Short-circuit if no conflicts possible
        if len(self.active_goals) <= 1:
            return
            
        # Get current health state to inform conflict resolution strategy
        health_state = self._get_current_health_state(None)
        
        # 1. Check for explicit incompatibilities
        active_goals = self.get_active_goals(sorted_by_priority=True)
        incompatibilities_found = False
        
        for i, goal1 in enumerate(active_goals):
            for goal2 in active_goals[i+1:]:  # Only check each pair once
                if goal1.is_incompatible_with(goal2.id) or goal2.is_incompatible_with(goal1.id):
                    incompatibilities_found = True
                    logger.info(f"Conflict detected: Goals '{goal1.description}' and '{goal2.description}' are incompatible")
                    
                    # Keep the higher priority goal (lower number)
                    if goal1.priority <= goal2.priority:
                        logger.info(f"Suspending lower priority goal '{goal2.description}' due to incompatibility")
                        self.update_goal_status(goal2.id, GoalStatus.SUSPENDED)
                    else:
                        logger.info(f"Suspending lower priority goal '{goal1.description}' due to incompatibility")
                        self.update_goal_status(goal1.id, GoalStatus.SUSPENDED)
                    
                    # After suspending a goal, we need to rerun conflict resolution
                    # But we'll do that after checking all pairs to avoid repeated calls
        
        # 2. Check resource constraints - more restrictive when health is poor
        total_resources_required = {
            "attention": 0.0,
            "energy": 0.0
        }
        
        # Recalculate active goals if incompatibilities were resolved
        if incompatibilities_found:
            active_goals = self.get_active_goals(sorted_by_priority=True)
        
        # Sum required resources
        for goal in active_goals:
            for resource, amount in goal.resource_requirements.items():
                if resource in total_resources_required:
                    total_resources_required[resource] += amount
        
        # Adjust available resources based on health state
        resource_limits = {
            "attention": 1.0,
            "energy": 1.0
        }
        
        if health_state in [HealthState.FATIGUED, HealthState.STRESSED]:
            resource_limits["attention"] = 0.8
            resource_limits["energy"] = 0.8
        elif health_state == HealthState.IMPAIRED:
            resource_limits["attention"] = 0.6
            resource_limits["energy"] = 0.6
        elif health_state == HealthState.CRITICAL:
            resource_limits["attention"] = 0.4
            resource_limits["energy"] = 0.4
        
        # Check for resource overallocation
        for resource, total in total_resources_required.items():
            if total > resource_limits[resource]:
                logger.info(f"Resource overallocation detected: {resource.capitalize()} required {total:.2f}, limit {resource_limits[resource]:.2f}")
                
                # Suspend lowest priority goals until resources are within limits
                for goal in reversed(active_goals):  # Start with lowest priority (end of list)
                    if total <= resource_limits[resource]:
                        break
                        
                    goal_usage = goal.resource_requirements.get(resource, 0.0)
                    if goal_usage > 0:
                        logger.info(f"Suspending goal '{goal.description}' due to {resource} constraints")
                        self.update_goal_status(goal.id, GoalStatus.SUSPENDED)
                        total -= goal_usage
                        
        # 3. Special rules for different health states
        if health_state == HealthState.CRITICAL:
            # In critical health, keep only the highest priority goal active
            active_goals = self.get_active_goals(sorted_by_priority=True)
            if len(active_goals) > 1:
                active_goals[0]
                for goal in active_goals[1:]:
                    logger.info(f"Suspending goal '{goal.description}' due to CRITICAL health state (keeping only highest priority)")
                    self.update_goal_status(goal.id, GoalStatus.SUSPENDED)
        
        # 4. Check activation thresholds - suspend goals with low activation
        # This simulates the biological tendency to lose focus on goals over time
        active_goals = self.get_active_goals(sorted_by_priority=True)
        for goal in active_goals:
            if goal.activation < self.min_activation_threshold:
                logger.info(f"Suspending goal '{goal.description}' due to low activation ({goal.activation:.2f})")
                self.update_goal_status(goal.id, GoalStatus.SUSPENDED)
    
    def process_decay(self):
        """
        Apply natural decay to all active goals.
        
        This simulates the biological tendency for goals to lose activation over time
        if not actively renewed or making progress.
        """
        for goal_id in self.active_goals.copy():  # Copy to allow modification during iteration
            goal = self.goals.get(goal_id)
            if goal:
                goal.decay_activation(self.activation_decay_rate)
                logger.debug(f"Goal '{goal.description}' activation decayed to {goal.activation:.2f}")
                
                # If activation falls below threshold, suspend the goal
                if goal.activation < self.min_activation_threshold:
                    logger.info(f"Goal '{goal.description}' activation fell below threshold, suspending")
                    self.update_goal_status(goal_id, GoalStatus.SUSPENDED)
    
    def suggest_next_goal(self, context: Optional[dict[str, Any]] = None) -> Optional[Goal]:
        """
        Suggest the next goal to activate based on priorities, dependencies, and context.
        
        Args:
            context: Current situation context.
            
        Returns:
            The suggested Goal to activate next, or None if no suitable goals.
        """
        context = context or {}
        
        # Get all pending goals sorted by priority
        pending_goals = [g for g in self.goals.values() if g.status == GoalStatus.PENDING]
        pending_goals.sort(key=lambda g: g.priority)  # Sort by priority (low to high number = high to low priority)
        
        # Filter goals that can be activated (dependencies satisfied, no incompatibilities)
        activatable_goals = []
        for goal in pending_goals:
            if goal.can_be_activated(list(self.active_goals), list(self.completed_goals)):
                activatable_goals.append(goal)
        
        if not activatable_goals:
            return None
            
        # Check if health state allows for new goals
        health_state = self._get_current_health_state(context)
        max_priority_allowed = 10
        
        if health_state == HealthState.STRESSED:
            max_priority_allowed = 7  # Restrict to priority 1-7
        elif health_state == HealthState.FATIGUED:
            max_priority_allowed = 5  # Restrict to priority 1-5
        elif health_state == HealthState.IMPAIRED:
            max_priority_allowed = 3  # Restrict to priority 1-3
        elif health_state == HealthState.CRITICAL:
            max_priority_allowed = 2  # Restrict to priority 1-2
        
        # Further filter by health state
        filtered_goals = [g for g in activatable_goals if g.priority <= max_priority_allowed]
        
        if not filtered_goals:
            return None
            
        # Sort by priority, then by prev_successes/prev_attempts (prefer goals with higher success rate)
        filtered_goals.sort(key=lambda g: (
            g.priority,  # First by priority (lower is better)
            -g.success_probability if g.previous_attempts > 0 else -0.5  # Then by success probability (higher is better)
        ))
        
        return filtered_goals[0]
