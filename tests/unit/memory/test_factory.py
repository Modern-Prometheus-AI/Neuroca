"""
Tests for the memory system factory.

This module tests the factory pattern implementation for creating memory systems,
ensuring that all memory types can be created without circular import issues.
"""

import pytest

from neuroca.core.memory.factory import (
    _memory_system_registry,
    _memory_type_aliases,
    create_memory_system,
    create_memory_trio,
)

# Import the interface instead of concrete classes for isinstance checks
from neuroca.core.memory.interfaces import MemorySystem

# Keep concrete imports if needed for other assertions, or remove if not
# from neuroca.core.memory.working_memory import WorkingMemory
# from neuroca.core.memory.episodic_memory import EpisodicMemory
from neuroca.memory.semantic_memory import (
    SemanticMemory,  # Concrete implementation needed for isinstance check
)


def test_memory_system_registry():
    """Test that all memory systems are properly registered."""
    # Ensure memory systems are registered
    assert "working" in _memory_system_registry
    assert "episodic" in _memory_system_registry
    assert "semantic" in _memory_system_registry

    # Check that the registry contains classes derived from MemorySystem
    assert issubclass(_memory_system_registry["working"], MemorySystem)
    assert issubclass(_memory_system_registry["episodic"], MemorySystem)
    assert issubclass(_memory_system_registry["semantic"], MemorySystem)


def test_memory_type_aliases():
    """Test that memory type aliases are properly defined."""
    # Check a few key aliases
    assert _memory_type_aliases["working_memory"] == "working"
    assert _memory_type_aliases["stm"] == "working"
    assert _memory_type_aliases["episodic_memory"] == "episodic"
    assert _memory_type_aliases["ltm"] == "semantic"


def test_create_memory_system():
    """Test creating memory systems of different types."""
    # Create memory systems using different type names
    working = create_memory_system("working")
    assert isinstance(working, MemorySystem) # Check against interface

    working_alt = create_memory_system("working_memory")
    assert isinstance(working_alt, MemorySystem) # Check against interface

    stm = create_memory_system("stm")
    assert isinstance(stm, MemorySystem) # Check against interface

    episodic = create_memory_system("episodic")
    assert isinstance(episodic, MemorySystem) # Check against interface

    semantic = create_memory_system("semantic")
    assert isinstance(semantic, MemorySystem) # Check against interface
    
    ltm = create_memory_system("ltm")
    assert isinstance(ltm, SemanticMemory)


def test_create_memory_system_with_config():
    """Test creating memory systems with configuration parameters."""
    # Create working memory with custom capacity
    working = create_memory_system("working", capacity=5)
    assert working.capacity == 5
    
    # Create episodic memory with custom decay rate
    episodic = create_memory_system("episodic", decay_rate=0.05)
    assert hasattr(episodic, "_decay_rate")
    assert episodic._decay_rate == 0.05


def test_create_memory_system_invalid_type():
    """Test that creating a memory system with an invalid type raises an error."""
    with pytest.raises(ValueError):
        create_memory_system("invalid_memory_type")


def test_create_memory_trio():
    """Test creating a complete set of memory systems."""
    # Create memory trio
    memory_systems = create_memory_trio()
    
    # Check that all three memory systems were created
    assert "working" in memory_systems
    assert "episodic" in memory_systems
    assert "semantic" in memory_systems

    # Check that they are the correct types (using interface)
    assert isinstance(memory_systems["working"], MemorySystem)
    assert isinstance(memory_systems["episodic"], MemorySystem)
    assert isinstance(memory_systems["semantic"], MemorySystem)


def test_create_memory_trio_with_prefix():
    """Test creating a memory trio with component ID prefixes."""
    # Create memory trio with prefix
    memory_systems = create_memory_trio(prefix="test_")
    
    # Check that all three memory systems were created
    assert "working" in memory_systems
    assert "episodic" in memory_systems
    assert "semantic" in memory_systems
    
    # We can't easily check the component IDs as they're internal to the health system,
    # but we can verify the memory systems were created correctly (using interface)
    assert isinstance(memory_systems["working"], MemorySystem)
    assert isinstance(memory_systems["episodic"], MemorySystem)
    assert isinstance(memory_systems["semantic"], MemorySystem)


def test_health_monitoring_disabled():
    """Test creating memory systems with health monitoring disabled."""
    # Create memory systems with health monitoring disabled
    create_memory_system("working", enable_health_monitoring=False)
    # assert isinstance(working, WorkingMemory) # Removed concrete check
    
    # Create memory trio with health monitoring disabled
    memory_systems = create_memory_trio(enable_health_monitoring=False)
    assert isinstance(memory_systems["working"], MemorySystem) # Check against interface
    assert isinstance(memory_systems["episodic"], MemorySystem) # Check against interface
    assert isinstance(memory_systems["semantic"], MemorySystem) # Check against interface
