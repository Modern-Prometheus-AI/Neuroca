"""
Unit tests for memory health monitoring.

This module tests the health monitoring integration with memory systems,
including health checks, metrics tracking, and cognitive operation recording.
"""


import pytest

from neuroca.core.health import (
    ComponentStatus,
    HealthCheckStatus,
    get_health_dynamics,
    get_health_monitor,
    run_health_check,
)
from neuroca.core.memory.episodic_memory import EpisodicMemory
from neuroca.core.memory.factory import create_memory_system
from neuroca.core.memory.health import (
    EpisodicMemoryHealthCheck,
    SemanticMemoryHealthCheck,
    WorkingMemoryHealthCheck,
    get_memory_health_monitor,
    record_memory_operation,
    register_memory_system,
)
from neuroca.core.memory.working_memory import WorkingMemory

# Import the concrete implementation from the correct location
from neuroca.memory.semantic_memory import SemanticMemory


@pytest.fixture()
def memory_systems():
    """Provide memory systems for testing without health monitoring."""
    working = WorkingMemory()
    episodic = EpisodicMemory()
    semantic = SemanticMemory()
    
    # Clean up after tests
    yield working, episodic, semantic
    
    working.clear()
    episodic.clear()
    semantic.clear()


@pytest.fixture()
def monitored_memory_systems():
    """Provide memory systems registered for health monitoring."""
    # Create memory systems with health monitoring
    working = create_memory_system("working", enable_health_monitoring=True, component_id="test_working")
    episodic = create_memory_system("episodic", enable_health_monitoring=True, component_id="test_episodic")
    semantic = create_memory_system("semantic", enable_health_monitoring=True, component_id="test_semantic")
    
    # Clean up after tests
    yield working, episodic, semantic
    
    working.clear()
    episodic.clear()
    semantic.clear()


def test_register_memory_system():
    """Test registering a memory system for health monitoring."""
    # Create memory systems
    working = WorkingMemory()
    
    # Register for health monitoring
    health = register_memory_system(working, "working", "test_register")
    
    # Verify registration
    assert health.component_id == "test_register"
    
    # Check that a health check was registered
    health_monitor = get_health_monitor()
    health_check = health_monitor.get_result("test_register.health")
    
    # Should not have results until checks are run
    assert health_check is None
    
    # Run the health check
    result = run_health_check("test_register.health")
    
    # Verify result
    assert result.status == HealthCheckStatus.PASSED
    assert result.component_id == "test_register"
    assert "Working memory is operating normally" in result.message


def test_memory_health_checks(memory_systems):
    """Test memory-specific health checks."""
    working, episodic, semantic = memory_systems
    
    # Create health checks
    working_check = WorkingMemoryHealthCheck("test_working", working)
    episodic_check = EpisodicMemoryHealthCheck("test_episodic", episodic)
    semantic_check = SemanticMemoryHealthCheck("test_semantic", semantic)
    
    # Run health checks
    working_result = working_check.execute()
    episodic_result = episodic_check.execute()
    semantic_result = semantic_check.execute()
    
    # Verify results
    assert working_result.status == HealthCheckStatus.PASSED
    assert episodic_result.status == HealthCheckStatus.PASSED
    assert semantic_result.status == HealthCheckStatus.PASSED
    
    # Check metrics in results
    assert "total_items" in working_result.details
    assert "operations_successful" in working_result.details
    
    assert "timestamp_ratio" in episodic_result.details
    assert "metadata_preserved" in episodic_result.details
    
    assert "total_concepts" in semantic_result.details
    assert "total_relationships" in semantic_result.details


def test_working_memory_health_warning():
    """Test working memory health check producing warnings."""
    # Create memory with small capacity
    working = WorkingMemory(capacity=5)
    
    # Create health check
    check = WorkingMemoryHealthCheck("test_wm_warning", working)
    
    # Fill memory near capacity
    for i in range(4):
        working.store(f"Item {i}")
    
    # Run health check
    result = check.execute()
    
    # Verify results (should be warning due to near capacity)
    assert result.status == HealthCheckStatus.WARNING
    assert "nearing capacity" in result.message
    assert result.details["capacity_ratio"] >= 0.8
    
    # Create memory with low activation items
    working_low = WorkingMemory()
    check_low = WorkingMemoryHealthCheck("test_wm_low", working_low)
    
    # Add items with low activation
    for i in range(10):
        working_low.store(f"Low activation item {i}", activation=0.2)
    
    # Run health check
    result_low = check_low.execute()
    
    # Verify results (should be warning due to low activation)
    assert result_low.status == HealthCheckStatus.WARNING
    assert "low activation" in result_low.message


def test_episodic_memory_health_warning():
    """Test episodic memory health check producing warnings."""
    # Create memory
    episodic = EpisodicMemory()
    
    # Create health check
    check = EpisodicMemoryHealthCheck("test_em_warning", episodic)
    
    # Add memories without timestamps
    for i in range(10):
        episodic.store(f"Memory without timestamp {i}")
    
    # Run health check
    result = check.execute()
    
    # Verify results (should be warning due to missing timestamps)
    assert result.status == HealthCheckStatus.WARNING
    assert "temporal context" in result.message
    assert result.details["timestamp_ratio"] < 0.8


def test_semantic_memory_health_warning():
    """Test semantic memory health check producing warnings."""
    # Create memory
    semantic = SemanticMemory()
    
    # Create health check
    check = SemanticMemoryHealthCheck("test_sm_warning", semantic)
    
    # Add disconnected concepts
    for i in range(10):
        concept = Concept(id=f"concept_{i}", name=f"Concept {i}")
        semantic.store(concept)
    
    # Run health check
    result = check.execute()
    
    # Verify results (should be warning due to low connectivity)
    assert result.status == HealthCheckStatus.WARNING
    assert "connectivity" in result.message
    assert result.details["connectivity_ratio"] < 0.5


def test_health_dynamics_integration(monitored_memory_systems):
    """Test integration with health dynamics system."""
    working, episodic, semantic = monitored_memory_systems
    
    # Get the health dynamics manager
    dynamics = get_health_dynamics()
    
    # Get component health objects
    working_health = dynamics.get_component_health("test_working")
    episodic_health = dynamics.get_component_health("test_episodic")
    semantic_health = dynamics.get_component_health("test_semantic")
    
    # Verify that components were registered with health dynamics
    assert working_health is not None
    assert episodic_health is not None
    assert semantic_health is not None
    
    # Verify initial parameters
    assert "energy" in working_health.parameters
    assert "cognitive_load" in working_health.parameters
    assert "attention" in working_health.parameters
    
    # Record operations
    record_memory_operation("test_working", "store", 5)
    record_memory_operation("test_episodic", "retrieve", 10)
    record_memory_operation("test_semantic", "update", 1)
    
    # Force update to process events
    dynamics.update_all_components()
    
    # Check that energy was consumed
    assert working_health.parameters["energy"].value < 1.0
    assert episodic_health.parameters["energy"].value < 1.0
    assert semantic_health.parameters["energy"].value < 1.0
    
    # Check that cognitive load increased
    assert working_health.parameters["cognitive_load"].value > 0.2
    
    # Record many operations to simulate intensive use
    for _i in range(20):
        record_memory_operation("test_working", "store", 1)
        dynamics.update_all_components()
    
    # Energy should be significantly reduced
    assert working_health.parameters["energy"].value < 0.7
    
    # Fatigue should have increased
    assert working_health.parameters["fatigue"].value > 0.1


def test_factory_integration():
    """Test memory factory integration with health monitoring."""
    # Create memory with health monitoring enabled
    create_memory_system("working", enable_health_monitoring=True)
    
    # Get component ID from memory type
    component_id = "working_memory"
    
    # Verify that health check was registered
    health_monitor = get_health_monitor()
    
    # Run all checks to generate results
    health_monitor.run_all_checks()
    
    # Get component status
    component_status = health_monitor.get_component_status(component_id)
    
    # Verify component status
    assert component_status is not None
    
    # Component should be in a healthy state
    assert component_status.status in [ComponentStatus.OPTIMAL, ComponentStatus.FUNCTIONAL]
    
    # Create memory with health monitoring disabled
    create_memory_system("episodic", enable_health_monitoring=False)
    
    # Record operation (should not raise errors even though not monitored)
    record_memory_operation("episodic_memory", "store", 1)


def test_memory_health_monitor_singleton():
    """Test that the memory health monitor is a singleton."""
    # Get the memory health monitor twice
    monitor1 = get_memory_health_monitor()
    monitor2 = get_memory_health_monitor()
    
    # Should be the same object
    assert monitor1 is monitor2
    
    # Register a memory system
    working = WorkingMemory()
    register_memory_system(working, "working", "singleton_test")
    
    # Monitor should have the registered system
    assert "singleton_test" in monitor1._memory_systems
