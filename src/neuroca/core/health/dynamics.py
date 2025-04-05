"""
Health dynamics for the NeuroCognitive Architecture.

This module provides biologically-inspired health dynamics including energy 
management, attention allocation, and homeostatic mechanisms.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class HealthParameterType(Enum):
    """
    Types of health parameters that can be tracked.
    
    These parameter types are inspired by biological systems and are
    used to model the health and energy dynamics of cognitive components.
    """
    ENERGY = "energy"                 # Available energy for operations
    ATTENTION = "attention"           # Focus and concentration levels
    COGNITIVE_LOAD = "cognitive_load" # Current mental workload
    STRESS = "stress"                 # Strain on the system
    FATIGUE = "fatigue"               # Accumulated weariness from operations
    RECOVERY = "recovery"             # Ability to restore energy and function
    ADAPTATION = "adaptation"         # Adjustment to changing conditions
    CUSTOM = "custom"                 # User-defined parameter type


class HealthState(Enum):
    """
    Overall health states for cognitive components.
    
    These states represent a simplified model of health conditions and
    their impact on cognitive function.
    """
    OPTIMAL = "optimal"         # Peak performance
    NORMAL = "normal"           # Standard operation
    FATIGUED = "fatigued"       # Showing signs of exhaustion
    STRESSED = "stressed"       # Under significant pressure
    IMPAIRED = "impaired"       # Function significantly diminished
    CRITICAL = "critical"       # Severely compromised function


class HealthEventType(Enum):
    """
    Types of health-related events that can occur.
    
    These events represent significant changes in health parameters
    that might trigger adaptive responses.
    """
    PARAMETER_CHANGE = "parameter_change"  # A health parameter changed
    STATE_CHANGE = "state_change"          # Overall health state changed
    THRESHOLD_CROSSED = "threshold_crossed" # A parameter crossed a threshold
    RECOVERY_STARTED = "recovery_started"   # Starting to recover
    RECOVERY_COMPLETED = "recovery_completed" # Recovery finished
    CUSTOM = "custom"                      # User-defined event type


@dataclass
class HealthParameter:
    """
    Tracks a specific health parameter with its current value and limits.
    
    This class models individual health metrics, tracking their current value,
    normal ranges, and related metadata.
    
    Attributes:
        name: Name of the parameter
        type: Type of health parameter
        value: Current value
        min_value: Minimum healthy value
        max_value: Maximum healthy value
        optimal_value: Ideal value for peak performance
        decay_rate: How quickly the parameter degrades over time
        recover_rate: How quickly the parameter recovers
        last_updated: When the parameter was last changed
    """
    name: str
    type: HealthParameterType
    value: float
    min_value: float
    max_value: float
    optimal_value: float = field(default=None)
    decay_rate: float = 0.01
    recovery_rate: float = 0.02
    last_updated: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize default values if needed."""
        if self.optimal_value is None:
            # Default optimal is halfway between min and max
            self.optimal_value = (self.min_value + self.max_value) / 2
    
    def update(self, new_value: float) -> float:
        """
        Update the parameter value and record the change time.
        
        Args:
            new_value: The new value to set
        
        Returns:
            The delta change in value
        """
        old_value = self.value
        # Clamp value to min/max range
        self.value = max(self.min_value, min(self.max_value, new_value))
        self.last_updated = time.time()
        return self.value - old_value
    
    def is_optimal(self, tolerance: float = 0.1) -> bool:
        """
        Check if the parameter is within optimal range.
        
        Args:
            tolerance: Allowed deviation from optimal value as a fraction
        
        Returns:
            True if the parameter is within optimal range
        """
        range_size = self.max_value - self.min_value
        allowed_deviation = range_size * tolerance
        return abs(self.value - self.optimal_value) <= allowed_deviation


@dataclass
class HealthEvent:
    """
    Represents a significant health-related event.
    
    These events track important changes in health parameters that may
    require adaptive responses from the system.
    
    Attributes:
        event_type: The type of health event
        component_id: The affected component
        parameter_name: The parameter that changed (if applicable)
        old_value: Previous value (if applicable)
        new_value: New value (if applicable)
        timestamp: When the event occurred
        details: Additional event details
    """
    event_type: HealthEventType
    component_id: str
    parameter_name: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    timestamp: float = field(default_factory=time.time)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """
    Manages the health state and parameters for a cognitive component.
    
    This class tracks all health-related aspects of a specific component,
    including energy, attention, and other biological factors.
    
    Attributes:
        component_id: Unique identifier for the component
        state: Current overall health state
        parameters: Health parameters being tracked
        events: Recent health events
        last_state_change: When the health state last changed
    """
    component_id: str
    state: HealthState = HealthState.NORMAL
    parameters: dict[str, HealthParameter] = field(default_factory=dict)
    events: list[HealthEvent] = field(default_factory=list)
    last_state_change: float = field(default_factory=time.time)
    max_events: int = 100
    
    def add_parameter(self, param: HealthParameter) -> None:
        """
        Add a health parameter to track.
        
        Args:
            param: The parameter to add
        """
        self.parameters[param.name] = param
    
    def update_parameter(self, name: str, value: float) -> Optional[HealthEvent]:
        """
        Update a health parameter's value and generate events if needed.
        
        Args:
            name: The parameter name
            value: The new value
        
        Returns:
            A HealthEvent if a significant change occurred, None otherwise
        
        Raises:
            KeyError: If the parameter doesn't exist
        """
        if name not in self.parameters:
            raise KeyError(f"Parameter '{name}' not found")
        
        param = self.parameters[name]
        old_value = param.value
        delta = param.update(value)
        
        # Generate event if significant change
        if abs(delta) >= 0.1 * (param.max_value - param.min_value):
            event = HealthEvent(
                event_type=HealthEventType.PARAMETER_CHANGE,
                component_id=self.component_id,
                parameter_name=name,
                old_value=old_value,
                new_value=param.value
            )
            self._add_event(event)
            return event
        
        return None
    
    def get_parameter(self, name: str) -> Optional[HealthParameter]:
        """
        Get a specific health parameter.
        
        Args:
            name: The parameter name
        
        Returns:
            The parameter or None if not found
        """
        return self.parameters.get(name)
    
    def update_state(self, new_state: HealthState) -> HealthEvent:
        """
        Update the overall health state and generate an event.
        
        Args:
            new_state: The new health state
        
        Returns:
            The state change event
        """
        if new_state != self.state:
            old_state = self.state
            self.state = new_state
            self.last_state_change = time.time()
            
            event = HealthEvent(
                event_type=HealthEventType.STATE_CHANGE,
                component_id=self.component_id,
                old_value=old_state.value,
                new_value=new_state.value
            )
            self._add_event(event)
            return event
        return None
    
    def _add_event(self, event: HealthEvent) -> None:
        """
        Add an event to the history, maintaining size limit.
        
        Args:
            event: The event to add
        """
        self.events.append(event)
        
        # Trim if needed
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

    def _apply_coping_strategy(self) -> None:
        """Apply coping strategies based on the current health state."""
        # Example strategies:
        if self.state == HealthState.FATIGUED:
            # Increase recovery rate when fatigued
            fatigue_param = self.get_parameter("fatigue")
            if fatigue_param:
                # Temporarily boost recovery rate (e.g., double it)
                # Note: This is a simple example; real strategies could be more complex
                # and might need state tracking (e.g., 'is_recovering')
                pass # Actual modification might happen in apply_natural_processes
            logger.debug(f"Component {self.component_id} applying FATIGUED coping strategy.")

        elif self.state == HealthState.STRESSED:
            # Reduce cognitive load or prioritize essential tasks
            # This might involve signaling other parts of the system
            logger.debug(f"Component {self.component_id} applying STRESSED coping strategy.")

        elif self.state == HealthState.IMPAIRED:
            # Drastically reduce activity, focus on recovery
            logger.debug(f"Component {self.component_id} applying IMPAIRED coping strategy.")
            # Example: Reduce energy decay, increase recovery significantly

        elif self.state == HealthState.CRITICAL:
            # Minimal function, maximum recovery focus
            logger.debug(f"Component {self.component_id} applying CRITICAL coping strategy.")
            # Example: Halt non-essential operations, maximize recovery rates

    def apply_natural_processes(self, elapsed_seconds: float) -> list[HealthEvent]:
        """
        Apply natural biological processes like decay and recovery, potentially
        modified by coping strategies.
        
        This method simulates natural biological processes over time,
        such as energy decay, attention fatigue, and recovery.
        
        Args:
            elapsed_seconds: Time elapsed since last update
        
        Returns:
            List of events generated during the process
        """
        events = []
        
        for param in self.parameters.values():
            old_value = param.value
            
            # Get current rates, potentially modified by coping strategies
            current_decay_rate = param.decay_rate
            current_recovery_rate = param.recovery_rate

            # --- Apply Coping Strategy Effects ---
            if self.state == HealthState.FATIGUED:
                # Boost recovery when fatigued
                current_recovery_rate *= 1.5 # Example: 50% boost
            elif self.state == HealthState.STRESSED:
                # Stress might increase decay rates
                current_decay_rate *= 1.2 # Example: 20% increase
            elif self.state == HealthState.IMPAIRED:
                # Impaired state focuses on recovery
                current_decay_rate *= 0.5 # Reduce decay
                current_recovery_rate *= 2.0 # Double recovery
            elif self.state == HealthState.CRITICAL:
                # Critical state maximizes recovery, minimizes decay
                current_decay_rate *= 0.1 # Drastically reduce decay
                current_recovery_rate *= 3.0 # Triple recovery
            # --- End Coping Strategy Effects ---

            # Apply appropriate process based on parameter type
            if param.type == HealthParameterType.ENERGY:
                # Energy decays naturally, recovers based on state/strategy
                new_value = param.value - (current_decay_rate * elapsed_seconds)
                # Recovery happens more effectively in non-optimal states (if not critical)
                if self.state in [HealthState.FATIGUED, HealthState.STRESSED, HealthState.IMPAIRED]:
                     new_value += current_recovery_rate * elapsed_seconds
            
            elif param.type == HealthParameterType.ATTENTION:
                # Attention decays, recovery depends on state/strategy
                attention_decay = current_decay_rate * elapsed_seconds
                new_value = param.value - attention_decay
                # Attention recovers better in normal/optimal states
                if self.state in [HealthState.NORMAL, HealthState.OPTIMAL]:
                    new_value += current_recovery_rate * elapsed_seconds
            
            elif param.type == HealthParameterType.FATIGUE:
                # Fatigue increases via decay, reduces via recovery (especially during rest)
                fatigue_increase = current_decay_rate * elapsed_seconds
                new_value = param.value + fatigue_increase
                
                # Recovery reduces fatigue, enhanced by coping strategies
                recovery = current_recovery_rate * elapsed_seconds
                new_value -= recovery
            
            else: # Default handling for custom or other types
                # Apply decay unless in a recovery-focused state
                if self.state not in [HealthState.OPTIMAL, HealthState.IMPAIRED, HealthState.CRITICAL]:
                    new_value = param.value - (current_decay_rate * elapsed_seconds)
                else: # Apply recovery in optimal or forced recovery states
                    new_value = param.value + (current_recovery_rate * elapsed_seconds)
            
            # Update the parameter
            param.update(new_value)
            
            # Generate event if significant change
            if abs(new_value - old_value) >= 0.1 * (param.max_value - param.min_value):
                event = HealthEvent(
                    event_type=HealthEventType.PARAMETER_CHANGE,
                    component_id=self.component_id,
                    parameter_name=param.name,
                    old_value=old_value,
                    new_value=param.value
                )
                self._add_event(event)
                events.append(event)
        
        # Assess overall state and potentially trigger state change event
        state_change_event = self._reassess_state()
        if state_change_event:
            events.append(state_change_event)
            # Apply coping strategy immediately after state change
            self._apply_coping_strategy() 
            
        return events
    
    def _reassess_state(self) -> Optional[HealthEvent]:
        """
        Reassess the overall health state based on parameters.
        
        Returns:
            A state change event if the state changed, None otherwise
        """
        # Calculate number of parameters in each condition
        optimal_count = sum(1 for p in self.parameters.values() if p.is_optimal())
        
        # Get energy and other critical parameters
        energy = self.get_parameter("energy")
        fatigue = self.get_parameter("fatigue")
        stress = self.get_parameter("stress")
        
        # Determine new state based on parameters (prioritize more severe states)
        new_state = HealthState.NORMAL # Default assumption

        # Critical state check (most severe)
        if energy and energy.value <= 0.1:
            new_state = HealthState.CRITICAL
        # Impaired state check
        elif energy and energy.value <= 0.3:
             new_state = HealthState.IMPAIRED
        # Stressed state check
        elif stress and stress.value >= 0.8: # Increased threshold for stress state
             new_state = HealthState.STRESSED
        # Fatigued state check
        elif fatigue and fatigue.value >= 0.7: # Increased threshold for fatigue state
             new_state = HealthState.FATIGUED
        # Optimal state check (least severe positive state)
        elif optimal_count >= len(self.parameters) * 0.8: # Higher requirement for optimal
             new_state = HealthState.OPTIMAL
        # If none of the above, it remains NORMAL
        
        # Update state if changed
        if new_state != self.state:
            return self.update_state(new_state)
        
        return None


class HealthDynamicsManager:
    """
    Manages health dynamics for all components in the system.
    
    This class provides methods to initialize, update, and monitor the health
    states of cognitive components, applying biologically-inspired processes.
    """
    def __init__(self):
        """Initialize the health dynamics manager."""
        self._components: dict[str, ComponentHealth] = {}
        self._listeners: list[Callable[[HealthEvent], None]] = []
        self._lock = threading.RLock()
        self._last_update = time.time()
        self._update_interval = 5.0  # Update every 5 seconds
        self._scheduler_thread = None
        self._stop_scheduler = threading.Event()
    
    def register_component(self, component_id: str) -> ComponentHealth:
        """
        Register a component for health tracking.
        
        Args:
            component_id: Unique identifier for the component
        
        Returns:
            The ComponentHealth object for the component
        """
        with self._lock:
            if component_id not in self._components:
                health = ComponentHealth(component_id)
                
                # Add default parameters
                health.add_parameter(HealthParameter(
                    name="energy",
                    type=HealthParameterType.ENERGY,
                    value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    decay_rate=0.01,
                    recovery_rate=0.02
                ))
                
                health.add_parameter(HealthParameter(
                    name="attention",
                    type=HealthParameterType.ATTENTION,
                    value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    decay_rate=0.02,
                    recovery_rate=0.05
                ))
                
                health.add_parameter(HealthParameter(
                    name="cognitive_load",
                    type=HealthParameterType.COGNITIVE_LOAD,
                    value=0.2,
                    min_value=0.0,
                    max_value=1.0,
                    optimal_value=0.4  # Some load is good for performance
                ))
                
                health.add_parameter(HealthParameter(
                    name="fatigue",
                    type=HealthParameterType.FATIGUE,
                    value=0.0,
                    min_value=0.0,
                    max_value=1.0,
                    decay_rate=0.005,  # Fatigue builds slowly
                    recovery_rate=0.01
                ))
                
                self._components[component_id] = health
                logger.info(f"Registered component for health tracking: {component_id}")
            
            return self._components[component_id]
    
    def unregister_component(self, component_id: str) -> None:
        """
        Remove a component from health tracking.
        
        Args:
            component_id: The ID of the component to remove
        """
        with self._lock:
            if component_id in self._components:
                del self._components[component_id]
                logger.info(f"Unregistered component from health tracking: {component_id}")
    
    def get_component_health(self, component_id: str) -> Optional[ComponentHealth]:
        """
        Get the health state for a specific component.
        
        Args:
            component_id: The ID of the component
        
        Returns:
            The component's health state or None if not registered
        """
        with self._lock:
            return self._components.get(component_id)
    
    def update_parameter(self, component_id: str, param_name: str, 
                         value: float) -> Optional[HealthEvent]:
        """
        Update a health parameter for a component.
        
        Args:
            component_id: The ID of the component
            param_name: The parameter name
            value: The new value
        
        Returns:
            A HealthEvent if a significant change occurred, None otherwise
        
        Raises:
            KeyError: If the component isn't registered
        """
        with self._lock:
            if component_id not in self._components:
                raise KeyError(f"Component '{component_id}' not registered for health tracking")
            
            health = self._components[component_id]
            event = health.update_parameter(param_name, value)
            
            # Notify listeners if event generated
            if event:
                self._notify_listeners(event)
            
            return event
    
    def record_operation(self, component_id: str, operation_type: str, 
                        complexity: float = 0.5) -> list[HealthEvent]:
        """
        Record a cognitive operation and update health parameters accordingly.
        
        Args:
            component_id: The ID of the component performing the operation
            operation_type: Type of cognitive operation
            complexity: Complexity of the operation (0.0-1.0)
        
        Returns:
            List of health events generated
        
        Raises:
            KeyError: If the component isn't registered
        """
        with self._lock:
            if component_id not in self._components:
                raise KeyError(f"Component '{component_id}' not registered for health tracking")
            
            health = self._components[component_id]
            events = []
            
            # Update energy - decreases based on operation complexity
            energy = health.get_parameter("energy")
            if energy:
                energy_cost = 0.01 * complexity
                event = health.update_parameter("energy", energy.value - energy_cost)
                if event:
                    events.append(event)
            
            # Update cognitive load - increases during operation
            cog_load = health.get_parameter("cognitive_load")
            if cog_load:
                load_increase = 0.1 * complexity
                event = health.update_parameter("cognitive_load", 
                                               cog_load.value + load_increase)
                if event:
                    events.append(event)
                    
                # Load will decrease naturally over time
            
            # Update fatigue - increases with operations
            fatigue = health.get_parameter("fatigue")
            if fatigue:
                fatigue_increase = 0.01 * complexity
                event = health.update_parameter("fatigue", 
                                               fatigue.value + fatigue_increase)
                if event:
                    events.append(event)
            
            # Notify listeners for all events
            for event in events:
                self._notify_listeners(event)
            
            return events
    
    def add_listener(self, listener: Callable[[HealthEvent], None]) -> None:
        """
        Add a listener for health events.
        
        Args:
            listener: Callback function that receives health events
        """
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[HealthEvent], None]) -> None:
        """
        Remove a health event listener.
        
        Args:
            listener: The listener to remove
        """
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def _notify_listeners(self, event: HealthEvent) -> None:
        """
        Notify all listeners about a health event.
        
        Args:
            event: The event to broadcast
        """
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in health event listener: {e}")
    
    def update_all_components(self) -> list[HealthEvent]:
        """
        Update health dynamics for all components.
        
        This method applies natural biological processes like energy decay
        and recovery to all registered components.
        
        Returns:
            List of events generated during updates
        """
        now = time.time()
        elapsed = now - self._last_update
        self._last_update = now
        
        all_events = []
        
        with self._lock:
            component_ids = list(self._components.keys())
        
        for component_id in component_ids:
            try:
                with self._lock:
                    health = self._components.get(component_id)
                    if not health:
                        continue
                
                # Apply natural processes
                events = health.apply_natural_processes(elapsed)
                all_events.extend(events)
                
                # Notify listeners
                for event in events:
                    self._notify_listeners(event)
                
            except Exception as e:
                logger.error(f"Error updating health for component {component_id}: {e}")
        
        return all_events
    
    def start_scheduled_updates(self, interval_seconds: float = 5.0) -> None:
        """
        Start a background thread to update health dynamics at regular intervals.
        
        Args:
            interval_seconds: How often to update (in seconds)
        """
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logger.warning("Health dynamics scheduler already running")
            return
        
        self._update_interval = interval_seconds
        self._stop_scheduler.clear()
        
        def scheduler_loop():
            while not self._stop_scheduler.is_set():
                try:
                    self.update_all_components()
                except Exception as e:
                    logger.error(f"Error in health dynamics scheduler: {e}")
                
                # Wait for the next interval or until stopped
                self._stop_scheduler.wait(self._update_interval)
        
        self._scheduler_thread = threading.Thread(
            target=scheduler_loop,
            name="HealthDynamicsScheduler",
            daemon=True
        )
        self._scheduler_thread.start()
        logger.info(f"Health dynamics scheduler started with {interval_seconds}s interval")
    
    def stop_scheduled_updates(self) -> None:
        """Stop the background health dynamics scheduler."""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._stop_scheduler.set()
            self._scheduler_thread.join(timeout=1.0)
            logger.info("Health dynamics scheduler stopped")


# Global instance for singleton access
_health_dynamics = HealthDynamicsManager()

def get_health_dynamics() -> HealthDynamicsManager:
    """Get the global health dynamics manager instance."""
    return _health_dynamics

def register_component_for_health_tracking(component_id: str) -> ComponentHealth:
    """Register a component with the global health dynamics manager."""
    return get_health_dynamics().register_component(component_id)

def record_cognitive_operation(component_id: str, operation_type: str, 
                              complexity: float = 0.5) -> list[HealthEvent]:
    """Record a cognitive operation with the global health dynamics manager."""
    return get_health_dynamics().record_operation(
        component_id, operation_type, complexity
    )
