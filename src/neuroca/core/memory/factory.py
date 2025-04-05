"""
Factory functions for creating memory system instances.

This module provides a centralized way to create and initialize memory systems,
abstracting away the details of which implementation classes are used.
"""

import logging
from typing import Optional

from neuroca.core.memory.health import register_memory_system
from neuroca.core.memory.interfaces import MemorySystem

logger = logging.getLogger(__name__)

# Mapping of memory type names to implementation classes
_memory_system_registry: dict[str, type[MemorySystem]] = {}

# Alias mapping for more flexible type names
_memory_type_aliases = {
    "working_memory": "working",
    "stm": "working",
    "short_term": "working",
    "episodic_memory": "episodic",
    "mtm": "episodic",
    "medium_term": "episodic",
    "semantic_memory": "semantic",
    "ltm": "semantic",
    "long_term": "semantic",
}


def register_memory_implementation(memory_type: str, implementation: type[MemorySystem]) -> None:
    """
    Register a memory system implementation class.
    
    Args:
        memory_type: The name to register for this memory type
        implementation: The implementation class
    """
    _memory_system_registry[memory_type.lower()] = implementation
    logger.debug(f"Registered memory implementation for type: {memory_type}")


def create_memory_system(memory_type: str, enable_health_monitoring: bool = True,
                        component_id: Optional[str] = None, **config) -> MemorySystem:
    """
    Create a memory system of the specified type.
    
    Args:
        memory_type: The type of memory system to create
        enable_health_monitoring: Whether to register for health monitoring
        component_id: Optional custom ID for the component (for health monitoring)
        **config: Configuration parameters for the memory system
    
    Returns:
        A memory system instance
    
    Raises:
        ValueError: If the memory type is not recognized
    """
    # Ensure memory implementations are loaded
    _register_default_memory_systems()
    
    # Normalize memory type
    memory_type = _memory_type_aliases.get(memory_type.lower(), memory_type.lower())
    
    # Check if memory type is registered
    if memory_type not in _memory_system_registry:
        valid_types = list(_memory_system_registry.keys()) + list(_memory_type_aliases.keys())
        raise ValueError(f"Unknown memory type: {memory_type}. Valid types: {valid_types}")
    
    # Create the memory system
    implementation_class = _memory_system_registry[memory_type]
    memory_system = implementation_class(**config)
    
    # Register for health monitoring if enabled
    if enable_health_monitoring:
        try:
            health = register_memory_system(memory_system, memory_type, component_id)
            logger.debug(f"Registered {memory_type} memory for health monitoring with ID: {health.component_id}")
        except Exception as e:
            logger.warning(f"Failed to register {memory_type} memory for health monitoring: {e}")
    
    return memory_system


def create_memory_trio(enable_health_monitoring: bool = True, 
                      prefix: str = "") -> dict[str, MemorySystem]:
    """
    Create a complete set of memory systems (working, episodic, semantic).
    
    Args:
        enable_health_monitoring: Whether to register for health monitoring
        prefix: Optional prefix for component IDs (for health monitoring)
    
    Returns:
        Dictionary mapping memory types to memory system instances
    """
    # Create component IDs with prefix if provided
    working_id = f"{prefix}working_memory" if prefix else None
    episodic_id = f"{prefix}episodic_memory" if prefix else None
    semantic_id = f"{prefix}semantic_memory" if prefix else None
    
    # Create memory systems
    working = create_memory_system("working", enable_health_monitoring, working_id)
    episodic = create_memory_system("episodic", enable_health_monitoring, episodic_id)
    semantic = create_memory_system("semantic", enable_health_monitoring, semantic_id)
    
    return {
        "working": working,
        "episodic": episodic,
        "semantic": semantic
    }

# Import and register concrete implementations
# These imports are at the bottom to avoid circular dependencies
def _register_default_memory_systems() -> None:
    """Register the default memory system implementations."""
    # Skip if already registered
    if _memory_system_registry:
        return
        
    try:
        # Import memory implementations
        from neuroca.core.memory.episodic_memory import EpisodicMemory
        from neuroca.core.memory.working_memory import WorkingMemory

        # Import the CONCRETE implementation from the correct location
        from neuroca.memory.semantic_memory import SemanticMemory
        
        # Register implementations
        register_memory_implementation("working", WorkingMemory)
        register_memory_implementation("episodic", EpisodicMemory)
        register_memory_implementation("semantic", SemanticMemory)
        
        # Register aliases
        register_memory_implementation("working_memory", WorkingMemory)
        register_memory_implementation("stm", WorkingMemory)
        register_memory_implementation("episodic_memory", EpisodicMemory)
        register_memory_implementation("semantic_memory", SemanticMemory)
        register_memory_implementation("ltm", SemanticMemory)
        
        logger.debug("Registered default memory system implementations")
    except ImportError as e:
        # During development, some implementations might not exist yet
        logger.warning(f"Could not register all memory implementations: {e}")
