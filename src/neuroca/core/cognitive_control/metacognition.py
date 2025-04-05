"""
Metacognition Component for NeuroCognitive Architecture (NCA).

This module implements metacognitive capabilities, allowing the system to
monitor, evaluate, and regulate its own cognitive processes.

Key functionalities:
- Self-monitoring: Tracking performance, errors, and resource usage.
- Confidence Estimation: Assessing the certainty of knowledge or predictions.
- Resource Allocation Optimization: Adjusting cognitive effort based on task demands and internal state.
- Strategy Selection: Choosing appropriate cognitive strategies for tasks.
"""

import logging
import time
from typing import Any, Optional

from neuroca.core.health.dynamics import (  # Example
    HealthState,
)
from neuroca.memory.manager import MemoryItem  # Example

from .goal_manager import GoalStatus  # Example, Import GoalStatus

# Import necessary components for potential integration
from .planner import Plan  # Import Plan for type hinting

# Configure logger
logger = logging.getLogger(__name__)

class MetacognitiveMonitor:
    """
    Monitors the system's internal state and performance.
    """
    def __init__(self, health_manager=None, memory_manager=None, goal_manager=None):
        """
        Initialize the MetacognitiveMonitor.

        Args:
            health_manager: Instance of HealthDynamicsManager.
            memory_manager: Instance of MemoryManager.
            goal_manager: Instance of GoalManager.
        """
        logger.info("MetacognitiveMonitor initialized.")
        self.health_manager = health_manager
        self.memory_manager = memory_manager
        self.goal_manager = goal_manager
        # NOTE: Consider implementing a proper dependency injection framework
        # for managing manager instances instead of direct constructor passing.
        self.last_error_log: list[dict] = [] # Simple error tracking, limited size
        self.performance_metrics: dict[str, Any] = { # Store more performance data
             "total_actions_completed": 0,
             "total_energy_consumed": 0.0,
             "avg_action_cost": 0.0,
        }
        self.max_error_log_size = 20

    def log_error(self, error_details: dict[str, Any]):
         """
         Log an error observed during cognitive processing and store in episodic memory.
         
         Args:
             error_details: Dictionary with error information (type, message, source, etc.)
         """
         # Add timestamp if not present
         error_details['timestamp'] = error_details.get('timestamp', time.time())
         
         # Add to local log buffer
         self.last_error_log.append(error_details)
         if len(self.last_error_log) > self.max_error_log_size:
             self.last_error_log.pop(0)  # Keep log size bounded
         
         # Log to standard logger
         logger.warning(f"Metacognition logged error: {error_details.get('type', 'Unknown')}: {error_details.get('message', '')}")
         
         # Store error in episodic memory for pattern recognition
         if self.memory_manager:
             try:
                 # Create a structured representation for the memory
                 mem_content = {
                     "type": "error",
                     "error_type": error_details.get("type", "Unknown"),
                     "message": error_details.get("message", ""),
                     "details": error_details
                 }
                 
                 # Store with appropriate metadata
                 mem_metadata = {
                     "error_source": error_details.get("source", "unknown_component"),
                     "component": error_details.get("component", "system"),
                     "severity": error_details.get("severity", "warning"),
                     "tags": ["error", error_details.get("type", "unknown_error")]
                 }
                 
                 # If task/action related, add context
                 if "task" in error_details:
                     mem_metadata["task"] = error_details["task"]
                 if "action" in error_details:
                     mem_metadata["action"] = error_details["action"]
                 
                 # Store in episodic memory with high emotional salience (errors are important)
                 self.memory_manager.store(content=mem_content, 
                                           memory_type="episodic", 
                                           metadata=mem_metadata,
                                           emotional_salience=0.8)
                 
                 logger.debug(f"Error stored in episodic memory: {error_details.get('type', 'Unknown')}")
             except Exception as e:
                 logger.error(f"Failed to store error in memory: {e}")

    def log_action_completion(self, action_cost: float):
         """Log the completion of an action to update performance metrics."""
         self.performance_metrics["total_actions_completed"] += 1
         self.performance_metrics["total_energy_consumed"] += action_cost
         total_actions = self.performance_metrics["total_actions_completed"]
         if total_actions > 0:
              self.performance_metrics["avg_action_cost"] = self.performance_metrics["total_energy_consumed"] / total_actions

    def assess_current_state(self) -> dict[str, Any]:
        """
        Assess the overall current state of the cognitive system, including performance.

        Returns:
            A dictionary summarizing the current state (e.g., health, goals, memory, performance).
        """
        logger.debug("Assessing current cognitive state.")
        state_summary = {"assessment_timestamp": time.time()}

        # 1. Health Summary
        if self.health_manager:
            all_component_ids = list(self.health_manager._components.keys()) # Direct access for example
            component_states = []
            total_energy = 0.0
            component_count = 0
            for comp_id in all_component_ids:
                comp_health = self.health_manager.get_component_health(comp_id)
                if comp_health:
                    component_states.append(comp_health.state)
                    energy_param = comp_health.get_parameter("energy")
                    if energy_param:
                        total_energy += energy_param.value
                        component_count += 1
            
            # Determine overall status
            if HealthState.CRITICAL in component_states or HealthState.IMPAIRED in component_states:
                state_summary["overall_health"] = HealthState.CRITICAL.value # Use most severe
            elif HealthState.STRESSED in component_states or HealthState.FATIGUED in component_states:
                state_summary["overall_health"] = HealthState.DEGRADED.value if hasattr(HealthState, 'DEGRADED') else HealthState.STRESSED.value # Use representative degraded state
            else:
                 state_summary["overall_health"] = HealthState.HEALTHY.value if hasattr(HealthState, 'HEALTHY') else HealthState.NORMAL.value # Default healthy state name
            
            state_summary["average_energy"] = round((total_energy / component_count), 3) if component_count > 0 else 0.0
            # Add counts of specific states
            state_summary["health_state_counts"] = {state.value: component_states.count(state) for state in HealthState}

        # 2. Goal Summary
        if self.goal_manager:
            active_goals = self.goal_manager.get_active_goals()
            state_summary["active_goal_count"] = len(active_goals)
            state_summary["highest_priority_goal"] = active_goals[0].description if active_goals else None
            state_summary["suspended_goal_count"] = len([g for g in self.goal_manager.goals.values() if g.status == GoalStatus.SUSPENDED])

        # 3. Memory Load Summary
        if self.memory_manager:
             stats = self.memory_manager.get_stats()
             wm_stats = stats.get("working_memory", {})
             state_summary["working_memory_load"] = round(wm_stats.get("utilization", 0), 3)
             state_summary["working_memory_count"] = wm_stats.get("count", 0)

        # 4. Performance & Error Summary
        state_summary["recent_errors_count"] = len(self.last_error_log)
        state_summary["total_actions_completed"] = self.performance_metrics.get("total_actions_completed", 0)
        state_summary["avg_action_cost"] = round(self.performance_metrics.get("avg_action_cost", 0.0), 3)

        logger.info(f"Current cognitive state assessment: {state_summary}")
        return state_summary

    def estimate_confidence(self, data: Any, source: str) -> float:
        """
        Estimate the confidence level in a piece of data or a prediction.

        Args:
            data: The data item (e.g., retrieved memory, prediction).
            source: The source of the data (e.g., "semantic_memory", "llm_prediction").

        Returns:
            A confidence score (e.g., 0.0 to 1.0).
        """
        # --- Enhanced Placeholder Confidence Estimation Logic ---
        base_confidence = 0.75 # Default

        # 1. Source Reliability
        if source == "semantic_memory":
            base_confidence = 0.85
        elif source == "episodic_memory":
            base_confidence = 0.70
        elif source == "working_memory":
            base_confidence = 0.65
        elif source == "llm_prediction":
            base_confidence = 0.60
        elif source == "direct_input":
             base_confidence = 0.90

        # 2. Data Specifics (if applicable)
        if isinstance(data, MemoryItem):
             # Combine source reliability with memory activation/metadata
             mem_confidence = max(0.1, min(1.0, data.calculate_activation() * 0.8 + 0.1))
             if "confidence" in data.metadata:
                 mem_confidence = (mem_confidence + data.metadata["confidence"]) / 2
             base_confidence = (base_confidence + mem_confidence) / 2 # Average base and memory-specific
        # Could add checks for consistency with other knowledge here using memory_manager

        # 3. Health State Adjustment
        health_state = self.assess_current_state().get("overall_health", "healthy") # Get current assessment
        health_factor = 1.0
        if health_state == "degraded":
            health_factor = 0.9
        elif health_state == "unhealthy":
            health_factor = 0.7
        
        final_confidence = max(0.0, min(1.0, base_confidence * health_factor))

        logger.debug(f"Estimated confidence for data from '{source}': {final_confidence:.2f} (Base: {base_confidence:.2f}, HealthFactor: {health_factor:.2f})")
        return final_confidence
        # --- End Enhanced Placeholder ---

    def select_strategy(self, task_description: str, available_strategies: list[str], context: Optional[dict[str, Any]] = None) -> Optional[str]:
        """
        Select the most appropriate cognitive strategy for a given task.

        Args:
            task_description: Description of the task to be performed.
            available_strategies: List of possible strategies (e.g., "detailed_planning", "heuristic_search", "memory_retrieval").
            context: Current situational information.

        Returns:
            The name of the selected strategy, or None.
        """
        logger.info(f"Selecting strategy for task: {task_description}")
        context = context or {}

        # --- Enhanced Placeholder Strategy Selection Logic ---
        # 1. Assess Current State
        current_state = self.assess_current_state()
        health_status = current_state.get("overall_health", "healthy")
        wm_load = current_state.get("working_memory_load", 0.0)

        # 2. Retrieve Past Performance for Strategy Selection
        past_success = {}
        if self.memory_manager:
            try:
                for strategy in available_strategies:
                    # Query episodic memory for past attempts using this strategy on similar tasks
                    past_attempts = self.memory_manager.retrieve(
                        query=f"strategy {strategy} task {task_description}", 
                        memory_type="episodic", 
                        limit=5
                    )
                    
                    if past_attempts:
                        # Calculate success rate based on outcome metadata
                        success_count = sum(1 for item in past_attempts 
                                         if item.metadata.get("outcome") == "success")
                        success_rate = success_count / len(past_attempts)
                        past_success[strategy] = success_rate
                        logger.debug(f"Strategy '{strategy}' has past success rate: {success_rate:.2f} ({success_count}/{len(past_attempts)})")
                    else:
                        past_success[strategy] = 0.5  # Default when no data
                        logger.debug(f"No past attempts found for strategy '{strategy}'")
            except Exception as e:
                logger.warning(f"Error retrieving past performance: {e}")
                # Fall back to defaults if memory retrieval fails
                past_success = {strategy: 0.5 for strategy in available_strategies}

        # 3. Score Strategies based on Context and Performance
        strategy_scores: dict[str, float] = {}
        for strategy in available_strategies:
            score = 0.5 # Base score

            # Adjust based on health
            if health_status == "healthy":
                 if strategy == "detailed_planning": score += 0.2
                 if strategy == "systematic_search": score += 0.1
            elif health_status == "degraded":
                 if strategy == "heuristic_search": score += 0.1
                 if strategy == "memory_retrieval": score += 0.1
                 if strategy == "detailed_planning": score -= 0.2 # Penalize demanding strategy
            elif health_status == "unhealthy":
                 if strategy == "simple_heuristic": score += 0.3
                 if strategy == "detailed_planning": score -= 0.5

            # Adjust based on WM load
            if wm_load > 0.8 and strategy == "detailed_planning": score -= 0.3 # Penalize if WM is full

            # Adjust based on past success rate
            score += past_success.get(strategy, 0.5) * 0.3  # Weight past success by 30%

            strategy_scores[strategy] = score

        # 4. Select Best Strategy
        if not strategy_scores:
             logger.warning(f"No strategies available or scored for task '{task_description}'.")
             return None

        best_strategy = max(strategy_scores, key=strategy_scores.get)
        logger.info(f"Selected strategy '{best_strategy}' for task '{task_description}' (Score: {strategy_scores[best_strategy]:.2f}, Health: {health_status}, WM Load: {wm_load:.2f}). Scores: {strategy_scores}")

        return best_strategy
        # --- End Enhanced Placeholder ---

    def detect_error_patterns(self, error_type: Optional[str] = None) -> dict[str, Any]:
        """
        Analyze past errors to detect recurring patterns and potential root causes.
        
        Args:
            error_type: Optional filter for specific error type to analyze
            
        Returns:
            Dictionary with error pattern analysis including frequency, common sources, etc.
        """
        if not self.memory_manager:
            logger.warning("Cannot detect error patterns: Memory manager not available")
            return {"patterns_detected": False, "reason": "memory_unavailable"}
            
        try:
            # Query parameters
            query = "type:error"
            if error_type:
                query += f" error_type:{error_type}"
                
            # Retrieve recent errors
            error_memories = self.memory_manager.retrieve(
                query=query,
                memory_type="episodic",
                limit=20,
                sort_by="timestamp",
                sort_order="descending"
            )
            
            if not error_memories:
                return {"patterns_detected": False, "reason": "no_errors_found"}
                
            # Analyze error patterns
            patterns = {
                "total_errors": len(error_memories),
                "by_type": {},
                "by_component": {},
                "by_source": {},
                "common_sequences": [],
                "recent_errors": []
            }
            
            # Count frequencies
            for mem in error_memories:
                # Extract error details
                error_type = mem.content.get("error_type", "unknown")
                component = mem.metadata.get("component", "unknown")
                source = mem.metadata.get("error_source", "unknown")
                
                # Update counts
                patterns["by_type"][error_type] = patterns["by_type"].get(error_type, 0) + 1
                patterns["by_component"][component] = patterns["by_component"].get(component, 0) + 1
                patterns["by_source"][source] = patterns["by_source"].get(source, 0) + 1
                
                # Add to recent errors list (just a few for reference)
                if len(patterns["recent_errors"]) < 5:
                    patterns["recent_errors"].append({
                        "type": error_type,
                        "message": mem.content.get("message", ""),
                        "component": component,
                        "timestamp": mem.metadata.get("timestamp", 0)
                    })
            
            # Determine most common patterns
            most_common_type = max(patterns["by_type"].items(), key=lambda x: x[1])[0] if patterns["by_type"] else None
            most_common_component = max(patterns["by_component"].items(), key=lambda x: x[1])[0] if patterns["by_component"] else None
            
            patterns["most_common_type"] = most_common_type
            patterns["most_common_component"] = most_common_component
            patterns["patterns_detected"] = True
            
            # Look for sequences (errors that tend to happen together or in sequence)
            # This would be more sophisticated in a real implementation
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error during pattern detection: {e}")
            return {"patterns_detected": False, "reason": f"analysis_error: {str(e)}"}

    def optimize_resource_allocation(self, task_complexity: float, current_plan: Optional[Plan] = None, task_type: Optional[str] = None) -> dict[str, float]:
        """
        Suggest adjustments to resource allocation based on task and state.

        Args:
            task_complexity: Estimated complexity of the current task/plan (0.0-1.0).
            current_plan: The plan currently being executed (optional).
            task_type: Type of task being performed (e.g., "planning", "retrieval", "reasoning")

        Returns:
            A dictionary suggesting resource adjustments (e.g., {"energy_budget": 0.8, "focus_level": 0.9}).
        """
        logger.debug(f"Optimizing resource allocation for task complexity: {task_complexity:.2f}")
        
        # 1. Assess current state (health, memory load, active goals)
        state = self.assess_current_state()
        health_status = state.get("overall_health", "healthy")
        state.get("average_energy", 1.0)
        state.get("working_memory_load", 0.5)
        
        # Default allocation
        allocation = {
            "energy_budget_factor": 1.0,  # Proportion of maximum energy to allocate
            "attention_focus_level": 0.8,  # Level of attentional focus (higher = more focused)
            "time_budget_factor": 1.0,     # Proportion of standard time to allocate
            "parallel_processes": 1        # Number of parallel cognitive processes to allow
        }

        # 2. Adjust based on health status and task complexity
        if health_status == "degraded":
            allocation["energy_budget_factor"] = 0.7  # Conserve energy
            allocation["attention_focus_level"] = 0.6
            allocation["parallel_processes"] = 1  # No parallel processing when degraded
        elif health_status == "unhealthy":
            allocation["energy_budget_factor"] = 0.4
            allocation["attention_focus_level"] = 0.5
            allocation["time_budget_factor"] = 1.5  # Allow more time when unhealthy
        
        if task_complexity > 0.7:
            allocation["attention_focus_level"] = min(1.0, allocation["attention_focus_level"] + 0.2)  # Increase focus for complex tasks
            allocation["energy_budget_factor"] = min(1.0, allocation["energy_budget_factor"] + 0.1)    # Allow slightly more energy
            allocation["time_budget_factor"] = 1.2  # More time for complex tasks
        
        # 3. Query memory for similar past tasks if available
        if self.memory_manager and task_type:
            try:
                # Find similar past tasks and their resource usage patterns
                similar_tasks = self.memory_manager.retrieve(
                    query=f"task_type:{task_type} complexity:{int(task_complexity*10)}/10",
                    memory_type="episodic",
                    limit=5
                )
                
                if similar_tasks:
                    logger.debug(f"Found {len(similar_tasks)} similar past tasks to inform resource allocation")
                    
                    # Calculate average resource allocations from past similar tasks
                    past_energy = []
                    past_attention = []
                    past_time = []
                    
                    for task_mem in similar_tasks:
                        if "resources" in task_mem.metadata:
                            resources = task_mem.metadata["resources"]
                            if "energy_used" in resources:
                                past_energy.append(resources["energy_used"])
                            if "attention_level" in resources:
                                past_attention.append(resources["attention_level"])
                            if "time_taken" in resources:
                                past_time.append(resources["time_taken"])
                    
                    # Adjust current allocation based on past performance if we have enough data
                    if len(past_energy) >= 3:
                        avg_energy_used = sum(past_energy) / len(past_energy)
                        allocation["energy_budget_factor"] = (allocation["energy_budget_factor"] + avg_energy_used) / 2
                        
                    if len(past_attention) >= 3:
                        avg_attention = sum(past_attention) / len(past_attention)
                        allocation["attention_focus_level"] = (allocation["attention_focus_level"] + avg_attention) / 2
                        
                    if len(past_time) >= 3:
                        avg_time_factor = sum(past_time) / len(past_time)
                        allocation["time_budget_factor"] = (allocation["time_budget_factor"] + avg_time_factor) / 2
            
            except Exception as e:
                logger.warning(f"Error retrieving past task memory for resource optimization: {e}")
                # Fall back to the default allocations calculated above
        
        # 4. Adjust for specific plan characteristics if available
        if current_plan:
            plan_steps = len(current_plan.steps) if hasattr(current_plan, 'steps') else 0
            if plan_steps > 5:
                # Complex multi-step plans need more attention and possibly parallel processing
                allocation["attention_focus_level"] = min(1.0, allocation["attention_focus_level"] + 0.1)
                if health_status == "healthy":
                    allocation["parallel_processes"] = min(3, max(1, plan_steps // 3))
        
        # Final adjustments and clamping to valid ranges
        for key in allocation:
            if key.endswith("_factor") or key == "attention_focus_level":
                allocation[key] = max(0.1, min(2.0, allocation[key]))  # Clamp between 0.1 and 2.0
        
        # Ensure parallel_processes is an integer
        allocation["parallel_processes"] = int(allocation["parallel_processes"])
        
        logger.info(f"Suggested resource allocation: {allocation} (Health: {health_status}, Task Complexity: {task_complexity:.2f})")
        return allocation
