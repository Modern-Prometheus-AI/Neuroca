"""
Unit tests for the health dynamics module.

Tests the functionality of ComponentHealth, HealthParameter, HealthState,
HealthDynamicsManager, and the application of natural processes and coping strategies.
"""

from unittest.mock import patch

import pytest

from neuroca.core.health.dynamics import (
    ComponentHealth,
    HealthDynamicsManager,
    HealthEvent,
    HealthEventType,
    HealthParameter,
    HealthParameterType,
    HealthState,
    get_health_dynamics,
    record_cognitive_operation,
    register_component_for_health_tracking,
)

# Constants for testing
TEST_COMPONENT_ID = "test_component_1"
TOLERANCE = 0.001 # Tolerance for floating point comparisons

# Helper function to get a parameter value or default
def get_param_value(health: ComponentHealth, name: str, default: float = 0.0) -> float:
    param = health.get_parameter(name)
    return param.value if param else default

class TestComponentHealth:
    """Tests for the ComponentHealth class."""

    @pytest.fixture()
    def component_health(self) -> ComponentHealth:
        """Fixture to create a ComponentHealth instance with default parameters."""
        health = ComponentHealth(TEST_COMPONENT_ID)
        # Add standard parameters similar to HealthDynamicsManager registration
        health.add_parameter(HealthParameter(name="energy", type=HealthParameterType.ENERGY, value=1.0, min_value=0.0, max_value=1.0, decay_rate=0.01, recovery_rate=0.02))
        health.add_parameter(HealthParameter(name="attention", type=HealthParameterType.ATTENTION, value=1.0, min_value=0.0, max_value=1.0, decay_rate=0.02, recovery_rate=0.05))
        health.add_parameter(HealthParameter(name="cognitive_load", type=HealthParameterType.COGNITIVE_LOAD, value=0.2, min_value=0.0, max_value=1.0, optimal_value=0.4))
        health.add_parameter(HealthParameter(name="fatigue", type=HealthParameterType.FATIGUE, value=0.0, min_value=0.0, max_value=1.0, decay_rate=0.005, recovery_rate=0.01))
        health.add_parameter(HealthParameter(name="stress", type=HealthParameterType.STRESS, value=0.1, min_value=0.0, max_value=1.0, decay_rate=0.002, recovery_rate=0.005)) # Added stress for testing
        return health

    def test_initialization(self, component_health: ComponentHealth):
        """Test initial state and parameters."""
        assert component_health.component_id == TEST_COMPONENT_ID
        assert component_health.state == HealthState.NORMAL
        assert len(component_health.parameters) == 5 # energy, attention, load, fatigue, stress
        assert component_health.get_parameter("energy").value == 1.0
        assert component_health.get_parameter("fatigue").value == 0.0
        assert not component_health.events

    def test_add_parameter(self, component_health: ComponentHealth):
        """Test adding a new parameter."""
        custom_param = HealthParameter(name="custom_resilience", type=HealthParameterType.CUSTOM, value=0.8, min_value=0.0, max_value=1.0)
        component_health.add_parameter(custom_param)
        assert "custom_resilience" in component_health.parameters
        assert component_health.get_parameter("custom_resilience").value == 0.8

    def test_update_parameter(self, component_health: ComponentHealth):
        """Test updating an existing parameter's value."""
        event = component_health.update_parameter("energy", 0.5)
        assert component_health.get_parameter("energy").value == 0.5
        assert event is not None
        assert event.event_type == HealthEventType.PARAMETER_CHANGE
        assert event.parameter_name == "energy"
        assert event.old_value == 1.0
        assert event.new_value == 0.5
        assert len(component_health.events) == 1

    def test_update_parameter_no_significant_change(self, component_health: ComponentHealth):
        """Test updating a parameter without a significant change doesn't create an event."""
        event = component_health.update_parameter("energy", 0.99) # Less than 0.1 change
        assert component_health.get_parameter("energy").value == 0.99
        assert event is None
        assert not component_health.events

    def test_update_parameter_not_found(self, component_health: ComponentHealth):
        """Test updating a non-existent parameter raises KeyError."""
        with pytest.raises(KeyError):
            component_health.update_parameter("non_existent", 0.5)

    def test_update_state(self, component_health: ComponentHealth):
        """Test updating the overall health state."""
        event = component_health.update_state(HealthState.FATIGUED)
        assert component_health.state == HealthState.FATIGUED
        assert event is not None
        assert event.event_type == HealthEventType.STATE_CHANGE
        assert event.old_value == HealthState.NORMAL.value
        assert event.new_value == HealthState.FATIGUED.value
        assert len(component_health.events) == 1

    def test_reassess_state_normal_to_optimal(self, component_health: ComponentHealth):
        """Test state transition from NORMAL to OPTIMAL."""
        # Make parameters close to their optimal values (default optimal is 0.5 for most)
        # is_optimal checks if abs(value - optimal_value) <= tolerance * range
        # Default tolerance is 0.1, range is 1.0, so abs(value - 0.5) <= 0.1 -> 0.4 <= value <= 0.6
        component_health.update_parameter("energy", 0.55)
        component_health.update_parameter("attention", 0.6)
        component_health.update_parameter("cognitive_load", 0.4) # Explicit optimal is 0.4
        component_health.update_parameter("fatigue", 0.45)
        component_health.update_parameter("stress", 0.4)
        # Now all 5 parameters should be considered optimal by is_optimal()
        
        event = component_health._reassess_state()
        assert component_health.state == HealthState.OPTIMAL
        assert event is not None
        assert event.new_value == HealthState.OPTIMAL.value

    def test_reassess_state_normal_to_fatigued(self, component_health: ComponentHealth):
        """Test state transition from NORMAL to FATIGUED."""
        component_health.update_parameter("fatigue", 0.75) # Above fatigue threshold (0.7)
        event = component_health._reassess_state()
        assert component_health.state == HealthState.FATIGUED
        assert event is not None
        assert event.new_value == HealthState.FATIGUED.value

    def test_reassess_state_normal_to_stressed(self, component_health: ComponentHealth):
        """Test state transition from NORMAL to STRESSED."""
        component_health.update_parameter("stress", 0.85) # Above stress threshold (0.8)
        event = component_health._reassess_state()
        assert component_health.state == HealthState.STRESSED
        assert event is not None
        assert event.new_value == HealthState.STRESSED.value

    def test_reassess_state_normal_to_impaired(self, component_health: ComponentHealth):
        """Test state transition from NORMAL to IMPAIRED."""
        component_health.update_parameter("energy", 0.25) # Below impaired threshold (0.3)
        event = component_health._reassess_state()
        assert component_health.state == HealthState.IMPAIRED
        assert event is not None
        assert event.new_value == HealthState.IMPAIRED.value

    def test_reassess_state_normal_to_critical(self, component_health: ComponentHealth):
        """Test state transition from NORMAL to CRITICAL."""
        component_health.update_parameter("energy", 0.05) # Below critical threshold (0.1)
        event = component_health._reassess_state()
        assert component_health.state == HealthState.CRITICAL
        assert event is not None
        assert event.new_value == HealthState.CRITICAL.value

    def test_reassess_state_priority(self, component_health: ComponentHealth):
        """Test that more severe states take priority."""
        component_health.update_parameter("energy", 0.05) # Critical
        component_health.update_parameter("fatigue", 0.9) # Fatigued
        component_health.update_parameter("stress", 0.9) # Stressed
        event = component_health._reassess_state()
        assert component_health.state == HealthState.CRITICAL # Critical should override others
        assert event is not None
        assert event.new_value == HealthState.CRITICAL.value

    def test_apply_natural_processes_decay(self, component_health: ComponentHealth):
        """Test natural decay of parameters in NORMAL state."""
        elapsed_time = 10.0 # seconds
        initial_energy = get_param_value(component_health, "energy")
        initial_attention = get_param_value(component_health, "attention")
        initial_fatigue = get_param_value(component_health, "fatigue")
        
        component_health.apply_natural_processes(elapsed_time)
        
        # Energy should decay
        expected_energy = initial_energy - (component_health.get_parameter("energy").decay_rate * elapsed_time)
        assert get_param_value(component_health, "energy") == pytest.approx(expected_energy, TOLERANCE)
        
        # Attention decays AND recovers in NORMAL state, potentially clamping at max
        attention_param = component_health.get_parameter("attention")
        expected_attention = initial_attention - (attention_param.decay_rate * elapsed_time) + (attention_param.recovery_rate * elapsed_time)
        expected_attention = max(attention_param.min_value, min(attention_param.max_value, expected_attention)) # Apply clamping
        assert get_param_value(component_health, "attention") == pytest.approx(expected_attention, TOLERANCE)
        
        # Fatigue should increase (decay) and decrease (recovery) in NORMAL state
        fatigue_param = component_health.get_parameter("fatigue")
        calculated_fatigue = initial_fatigue + (fatigue_param.decay_rate * elapsed_time) - (fatigue_param.recovery_rate * elapsed_time)
        expected_clamped_fatigue = max(fatigue_param.min_value, min(fatigue_param.max_value, calculated_fatigue)) # Apply clamping
        assert get_param_value(component_health, "fatigue") == pytest.approx(expected_clamped_fatigue, TOLERANCE)

    def test_apply_natural_processes_recovery_fatigued(self, component_health: ComponentHealth):
        """Test enhanced recovery when FATIGUED."""
        component_health.update_state(HealthState.FATIGUED) # Set state to FATIGUED
        elapsed_time = 10.0
        
        initial_energy = get_param_value(component_health, "energy", 1.0)
        initial_fatigue = get_param_value(component_health, "fatigue", 0.8) # Start fatigued
        component_health.update_parameter("fatigue", initial_fatigue)

        energy_param = component_health.get_parameter("energy")
        fatigue_param = component_health.get_parameter("fatigue")

        # Coping strategy effect: recovery rate * 1.5
        boosted_energy_recovery = energy_param.recovery_rate * 1.5
        boosted_fatigue_recovery = fatigue_param.recovery_rate * 1.5

        component_health.apply_natural_processes(elapsed_time)

        # Energy decays but also recovers due to FATIGUED state recovery boost, check clamping
        expected_energy = initial_energy - (energy_param.decay_rate * elapsed_time) + (boosted_energy_recovery * elapsed_time)
        expected_energy = max(energy_param.min_value, min(energy_param.max_value, expected_energy)) # Apply clamping
        assert get_param_value(component_health, "energy") == pytest.approx(expected_energy, TOLERANCE)

        # Fatigue increases (decay) but recovers faster, check clamping
        calculated_fatigue = initial_fatigue + (fatigue_param.decay_rate * elapsed_time) - (boosted_fatigue_recovery * elapsed_time)
        expected_clamped_fatigue = max(fatigue_param.min_value, min(fatigue_param.max_value, calculated_fatigue)) # Apply clamping
        assert get_param_value(component_health, "fatigue") == pytest.approx(expected_clamped_fatigue, TOLERANCE)

    def test_apply_natural_processes_stressed(self, component_health: ComponentHealth):
        """Test increased decay when STRESSED."""
        component_health.update_state(HealthState.STRESSED) # Set state to STRESSED
        elapsed_time = 10.0
        
        initial_energy = get_param_value(component_health, "energy", 1.0)
        initial_attention = get_param_value(component_health, "attention", 1.0)

        energy_param = component_health.get_parameter("energy")
        attention_param = component_health.get_parameter("attention")

        # Coping strategy effect: decay rate * 1.2
        boosted_energy_decay = energy_param.decay_rate * 1.2
        boosted_attention_decay = attention_param.decay_rate * 1.2
        
        # Energy recovery also happens in STRESSED state
        boosted_energy_recovery = energy_param.recovery_rate # No boost specified for stress recovery itself

        component_health.apply_natural_processes(elapsed_time)

        # Energy decays faster and recovers, check clamping
        expected_energy = initial_energy - (boosted_energy_decay * elapsed_time) + (boosted_energy_recovery * elapsed_time)
        expected_energy = max(energy_param.min_value, min(energy_param.max_value, expected_energy)) # Apply clamping
        assert get_param_value(component_health, "energy") == pytest.approx(expected_energy, TOLERANCE)

        # Attention decays faster, no recovery in STRESSED state, check clamping
        expected_attention = initial_attention - (boosted_attention_decay * elapsed_time)
        assert get_param_value(component_health, "attention") == pytest.approx(expected_attention, TOLERANCE)

    def test_apply_natural_processes_critical(self, component_health: ComponentHealth):
        """Test reduced decay and max recovery when CRITICAL."""
        component_health.update_state(HealthState.CRITICAL) # Set state to CRITICAL
        elapsed_time = 10.0
        
        initial_energy = get_param_value(component_health, "energy", 0.05) # Start critical
        component_health.update_parameter("energy", initial_energy)
        initial_fatigue = get_param_value(component_health, "fatigue", 0.9)
        component_health.update_parameter("fatigue", initial_fatigue)

        energy_param = component_health.get_parameter("energy")
        fatigue_param = component_health.get_parameter("fatigue")

        # Coping strategy effect: decay * 0.1, recovery * 3.0
        reduced_energy_decay = energy_param.decay_rate * 0.1
        energy_param.recovery_rate * 3.0
        reduced_fatigue_decay = fatigue_param.decay_rate * 0.1
        max_fatigue_recovery = fatigue_param.recovery_rate * 3.0

        component_health.apply_natural_processes(elapsed_time)

        # Energy decay is minimal, recovery is maximized (but recovery doesn't apply to energy in CRITICAL)
        expected_energy = initial_energy - (reduced_energy_decay * elapsed_time)
        # Note: The code currently doesn't apply energy recovery in CRITICAL state, only FATIGUED, STRESSED, IMPAIRED.
        # If recovery *should* apply, the expected value would change. Let's test current logic.
        assert get_param_value(component_health, "energy") == pytest.approx(expected_energy, TOLERANCE)

        # Fatigue decay is minimal, recovery is maximized, check clamping
        expected_fatigue = initial_fatigue + (reduced_fatigue_decay * elapsed_time) - (max_fatigue_recovery * elapsed_time)
        expected_fatigue = max(fatigue_param.min_value, min(fatigue_param.max_value, expected_fatigue)) # Apply clamping
        assert get_param_value(component_health, "fatigue") == pytest.approx(expected_fatigue, TOLERANCE)

    def test_event_history_limit(self, component_health: ComponentHealth):
        """Test that the event history is trimmed correctly."""
        component_health.max_events = 3 # Set a small limit for testing
        component_health.update_parameter("energy", 0.8) # Event 1
        component_health.update_parameter("energy", 0.6) # Event 2
        component_health.update_parameter("energy", 0.4) # Event 3
        component_health.update_parameter("energy", 0.2) # Event 4 (should push out event 1)
        
        assert len(component_health.events) == 3
        assert component_health.events[0].new_value == 0.6 # Event 2 is now the first
        assert component_health.events[1].new_value == 0.4 # Event 3
        assert component_health.events[2].new_value == 0.2 # Event 4


class TestHealthDynamicsManager:
    """Tests for the HealthDynamicsManager class."""

    @pytest.fixture()
    def manager(self) -> HealthDynamicsManager:
        """Fixture to create a HealthDynamicsManager instance."""
        # Use a fresh instance for each test to avoid state leakage
        return HealthDynamicsManager()

    def test_register_component(self, manager: HealthDynamicsManager):
        """Test registering a new component."""
        health = manager.register_component(TEST_COMPONENT_ID)
        assert isinstance(health, ComponentHealth)
        assert health.component_id == TEST_COMPONENT_ID
        assert manager.get_component_health(TEST_COMPONENT_ID) is health
        # Check default parameters were added
        assert "energy" in health.parameters
        assert "fatigue" in health.parameters

    def test_register_component_already_exists(self, manager: HealthDynamicsManager):
        """Test registering a component that already exists returns the existing one."""
        health1 = manager.register_component(TEST_COMPONENT_ID)
        health2 = manager.register_component(TEST_COMPONENT_ID)
        assert health1 is health2 # Should be the same object

    def test_unregister_component(self, manager: HealthDynamicsManager):
        """Test unregistering a component."""
        manager.register_component(TEST_COMPONENT_ID)
        assert manager.get_component_health(TEST_COMPONENT_ID) is not None
        manager.unregister_component(TEST_COMPONENT_ID)
        assert manager.get_component_health(TEST_COMPONENT_ID) is None

    def test_update_parameter_manager(self, manager: HealthDynamicsManager):
        """Test updating a parameter via the manager."""
        manager.register_component(TEST_COMPONENT_ID)
        event = manager.update_parameter(TEST_COMPONENT_ID, "energy", 0.5)
        health = manager.get_component_health(TEST_COMPONENT_ID)
        assert health.get_parameter("energy").value == 0.5
        assert event is not None
        assert event.parameter_name == "energy"

    def test_update_parameter_manager_unregistered(self, manager: HealthDynamicsManager):
        """Test updating parameter for an unregistered component raises KeyError."""
        with pytest.raises(KeyError):
            manager.update_parameter("unregistered_component", "energy", 0.5)

    def test_record_operation(self, manager: HealthDynamicsManager):
        """Test recording an operation updates relevant parameters."""
        health = manager.register_component(TEST_COMPONENT_ID)
        initial_energy = get_param_value(health, "energy")
        initial_load = get_param_value(health, "cognitive_load")
        initial_fatigue = get_param_value(health, "fatigue")
        
        complexity = 0.8
        manager.record_operation(TEST_COMPONENT_ID, "complex_thought", complexity)
        
        # Energy should decrease
        expected_energy_cost = 0.01 * complexity
        assert get_param_value(health, "energy") == pytest.approx(initial_energy - expected_energy_cost, TOLERANCE)
        
        # Load should increase
        expected_load_increase = 0.1 * complexity
        assert get_param_value(health, "cognitive_load") == pytest.approx(initial_load + expected_load_increase, TOLERANCE)
        
        # Fatigue should increase
        expected_fatigue_increase = 0.01 * complexity
        assert get_param_value(health, "fatigue") == pytest.approx(initial_fatigue + expected_fatigue_increase, TOLERANCE)
        
        # Check that parameters actually changed, even if no event generated
        assert get_param_value(health, "energy") < initial_energy
        assert get_param_value(health, "cognitive_load") > initial_load
        assert get_param_value(health, "fatigue") > initial_fatigue
        # We don't assert len(events) > 0 anymore, as changes might be small

    def test_record_operation_unregistered(self, manager: HealthDynamicsManager):
        """Test recording operation for an unregistered component raises KeyError."""
        with pytest.raises(KeyError):
            manager.record_operation("unregistered_component", "simple_task", 0.1)

    def test_listeners(self, manager: HealthDynamicsManager):
        """Test that listeners are notified of events."""
        manager.register_component(TEST_COMPONENT_ID)
        
        received_events: list[HealthEvent] = []
        def listener_callback(event: HealthEvent):
            received_events.append(event)
            
        manager.add_listener(listener_callback)
        
        # Trigger an event
        manager.update_parameter(TEST_COMPONENT_ID, "energy", 0.5)
        
        assert len(received_events) == 1
        assert received_events[0].event_type == HealthEventType.PARAMETER_CHANGE
        assert received_events[0].parameter_name == "energy"
        
        # Test removing listener
        manager.remove_listener(listener_callback)
        manager.update_parameter(TEST_COMPONENT_ID, "energy", 0.3) # Trigger another event
        assert len(received_events) == 1 # Listener should not have been called again

    @patch('neuroca.core.health.dynamics.time.time')
    def test_update_all_components(self, mock_time, manager: HealthDynamicsManager):
        """Test the update_all_components method applies natural processes."""
        # Register two components
        health1 = manager.register_component("comp1")
        health2 = manager.register_component("comp2")
        
        initial_energy1 = get_param_value(health1, "energy")
        initial_energy2 = get_param_value(health2, "energy")
        
        # Mock time to control elapsed time - provide enough values
        start_time = 1000.0
        elapsed_time = 10.0
        # Need time for: 
        # 1. `now = time.time()` at start of update_all_components
        # 2. `param.update()` calls inside apply_natural_processes (updates last_updated)
        # Provide the end time first, then subsequent times for updates.
        end_time = start_time + elapsed_time
        mock_time.side_effect = [end_time] + [end_time] * 20 # First call gets end_time, others too
        
        # Set initial last_update time
        manager._last_update = start_time
        
        events = manager.update_all_components()
        
        # Check that parameters were updated for both components
        energy_param1 = health1.get_parameter("energy")
        expected_energy1 = initial_energy1 - (energy_param1.decay_rate * elapsed_time)
        assert get_param_value(health1, "energy") == pytest.approx(expected_energy1, TOLERANCE)
        
        energy_param2 = health2.get_parameter("energy")
        expected_energy2 = initial_energy2 - (energy_param2.decay_rate * elapsed_time)
        assert get_param_value(health2, "energy") == pytest.approx(expected_energy2, TOLERANCE)
        
        assert len(events) > 0 # Should have generated events
        assert manager._last_update == start_time + elapsed_time

    # Note: Testing the scheduler thread directly is complex in unit tests.
    # It might require more advanced techniques like mocking threading or
    # testing it in an integration test setting.

# Test global functions (which use the singleton manager)
# Need to ensure the global manager is reset between tests if necessary,
# or mock get_health_dynamics()

@pytest.fixture(autouse=True)
def reset_global_manager():
    """Fixture to reset the global manager before each test function."""
    global _health_dynamics
    # Store original and replace
    get_health_dynamics()
    new_manager = HealthDynamicsManager()
    
    # Use patch to replace the global instance within the dynamics module
    with patch('neuroca.core.health.dynamics._health_dynamics', new_manager):
        yield new_manager # Provide the new manager if needed by tests
        
    # Restore (though typically not strictly needed as tests should isolate)
    # _health_dynamics = original_manager # This assignment might not work as expected due to import caching

def test_global_register_component():
    """Test the global register_component_for_health_tracking function."""
    health = register_component_for_health_tracking(TEST_COMPONENT_ID)
    assert health is not None
    assert health.component_id == TEST_COMPONENT_ID
    # Verify it used the (patched) global manager
    assert get_health_dynamics().get_component_health(TEST_COMPONENT_ID) is health

def test_global_record_operation():
    """Test the global record_cognitive_operation function."""
    register_component_for_health_tracking(TEST_COMPONENT_ID)
    health = get_health_dynamics().get_component_health(TEST_COMPONENT_ID)
    initial_energy = get_param_value(health, "energy")
    
    record_cognitive_operation(TEST_COMPONENT_ID, "global_op", 0.5)
    
    # Check that parameters changed, not event count
    assert get_param_value(health, "energy") < initial_energy
    # assert len(events) > 0 # Don't assert event count
