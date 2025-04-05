"""
Memory Factory Module for NeuroCognitive Architecture (NCA)

This module provides a factory pattern implementation for creating and managing
different types of memory components within the NCA's three-tiered memory system.
It abstracts the creation logic and provides a unified interface for instantiating
memory components based on configuration and runtime requirements.

The factory supports creating:
- Working memory components
- Episodic memory components 
- Semantic memory components
- Procedural memory components
- And other specialized memory types

Usage:
    from neuroca.memory.factory import MemoryFactory
    
    # Create a memory factory with default configuration
    factory = MemoryFactory()
    
    # Create a specific memory component
    working_memory = factory.create_memory("working", capacity=10)
    
    # Create a memory component with custom parameters
    episodic_memory = factory.create_memory(
        "episodic", 
        storage_backend="vector_db",
        embedding_model="text-embedding-ada-002"
    )
"""

import importlib
import logging
from typing import Any, Optional

# Import memory base classes and exceptions
from neuroca.core.memory.interfaces import MemorySystem  # Corrected import path
from neuroca.memory.exceptions import (
    MemoryConfigurationError,
    MemoryCreationError,
    MemoryInitializationError,
    MemoryTypeNotFoundError,
)

# Import specific memory implementations
# These will be dynamically loaded, but we include them here for type checking
try:
    from neuroca.memory.episodic import EpisodicMemory
    from neuroca.memory.procedural import ProceduralMemory
    from neuroca.memory.semantic import SemanticMemory
    from neuroca.memory.working import WorkingMemory
    HAS_ALL_MEMORY_TYPES = True
except ImportError:
    HAS_ALL_MEMORY_TYPES = False

# Setup logging
logger = logging.getLogger(__name__)


class MemoryFactory:
    """
    Factory class for creating memory components in the NCA system.
    
    This factory implements the Factory Method pattern to create different types
    of memory components based on the specified memory type and configuration.
    It handles the dynamic loading of memory implementations and manages their
    lifecycle.
    
    Attributes:
        _registry (Dict[str, Type[MemorySystem]]): Registry mapping memory type names to their classes
        _config (Dict[str, Any]): Configuration for memory components
        _default_params (Dict[str, Dict[str, Any]]): Default parameters for each memory type
    """
    
    # Memory type mapping from user-friendly names to module paths
    _MEMORY_TYPE_MAPPING = {
        "working": "neuroca.memory.working.WorkingMemory",
        "episodic": "neuroca.memory.episodic.EpisodicMemory",
        "semantic": "neuroca.memory.semantic.SemanticMemory",
        "procedural": "neuroca.memory.procedural.ProceduralMemory",
        "associative": "neuroca.memory.associative.AssociativeMemory",
        "sensory": "neuroca.memory.sensory.SensoryMemory",
    }
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize the memory factory with optional configuration.
        
        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary for memory components.
                If None, default configuration will be used.
                
        Raises:
            MemoryConfigurationError: If the provided configuration is invalid.
        """
        self._registry: dict[str, type[MemorySystem]] = {}
        self._config = config or {}
        self._default_params = self._initialize_default_params()
        
        # Pre-register known memory types if available
        if HAS_ALL_MEMORY_TYPES:
            self._preregister_memory_types()
            
        logger.debug("MemoryFactory initialized with config: %s", self._config)
    
    def _initialize_default_params(self) -> dict[str, dict[str, Any]]:
        """
        Initialize default parameters for each memory type.
        
        Returns:
            Dict[str, Dict[str, Any]]: Default parameters for each memory type.
        """
        return {
            "working": {
                "capacity": 7,  # Miller's Law - 7±2 items
                "decay_rate": 0.1,
                "priority_based": True,
            },
            "episodic": {
                "storage_backend": "in_memory",
                "max_episodes": 1000,
                "embedding_model": "default",
                "retrieval_strategy": "recency_and_relevance",
            },
            "semantic": {
                "storage_backend": "in_memory",
                "indexing_strategy": "hierarchical",
                "compression_enabled": True,
            },
            "procedural": {
                "max_procedures": 500,
                "learning_rate": 0.05,
                "reinforcement_enabled": True,
            },
            "associative": {
                "connection_strength_decay": 0.01,
                "hebbian_learning_enabled": True,
            },
            "sensory": {
                "buffer_size": 5,
                "modalities": ["visual", "textual"],
            }
        }
    
    def _preregister_memory_types(self) -> None:
        """
        Pre-register known memory types if their modules are available.
        This avoids dynamic imports for common memory types.
        """
        try:
            self._registry["working"] = WorkingMemory
            self._registry["episodic"] = EpisodicMemory
            self._registry["semantic"] = SemanticMemory
            self._registry["procedural"] = ProceduralMemory
            logger.debug("Pre-registered standard memory types")
        except NameError:
            logger.debug("Some memory types not available for pre-registration")
    
    def register_memory_type(self, memory_type: str, memory_class: type[MemorySystem]) -> None:
        """
        Register a new memory type with the factory.
        
        Args:
            memory_type (str): The name/identifier for the memory type
            memory_class (Type[MemorySystem]): The memory class to register
            
        Raises:
            ValueError: If memory_type is None or empty
            TypeError: If memory_class is not a subclass of MemorySystem
        """
        if not memory_type:
            raise ValueError("Memory type cannot be None or empty")
        
        if not isinstance(memory_class, type) or not issubclass(memory_class, MemorySystem):
            raise TypeError(f"Memory class must be a subclass of MemorySystem, got {type(memory_class)}")
        
        self._registry[memory_type] = memory_class
        logger.debug("Registered memory type: %s", memory_type)
    
    def _load_memory_class(self, memory_type: str) -> type[MemorySystem]:
        """
        Dynamically load a memory class based on its type.
        
        Args:
            memory_type (str): The type of memory to load
            
        Returns:
            Type[MemorySystem]: The memory class
            
        Raises:
            MemoryTypeNotFoundError: If the memory type is not supported
            MemoryInitializationError: If there's an error loading the memory class
        """
        # Check if already registered
        if memory_type in self._registry:
            return self._registry[memory_type]
        
        # Check if it's a known type
        if memory_type not in self._MEMORY_TYPE_MAPPING:
            raise MemoryTypeNotFoundError(f"Unsupported memory type: {memory_type}")
        
        # Dynamically import the memory class
        class_path = self._MEMORY_TYPE_MAPPING[memory_type]
        module_path, class_name = class_path.rsplit(".", 1)
        
        try:
            module = importlib.import_module(module_path)
            memory_class = getattr(module, class_name)
            
            # Validate that it's a proper memory class
            if not issubclass(memory_class, MemorySystem):
                raise MemoryInitializationError(
                    f"Class {class_name} is not a subclass of MemorySystem"
                )
            
            # Register for future use
            self._registry[memory_type] = memory_class
            return memory_class
            
        except ImportError as e:
            logger.error("Failed to import memory module %s: %s", module_path, str(e))
            raise MemoryInitializationError(f"Failed to import memory module: {str(e)}")
        except AttributeError as e:
            logger.error("Failed to find memory class %s in module %s: %s", 
                          class_name, module_path, str(e))
            raise MemoryInitializationError(f"Failed to find memory class: {str(e)}") # Corrected indentation here
    
    def create_memory(self, memory_type: str, **kwargs) -> MemorySystem:
        """
        Create a memory component of the specified type with the given parameters.
        
        Args:
            memory_type (str): The type of memory to create
            **kwargs: Additional parameters to pass to the memory constructor
            
        Returns:
            MemorySystem: An instance of the requested memory type
            
        Raises:
            MemoryTypeNotFoundError: If the memory type is not supported
            MemoryCreationError: If there's an error creating the memory instance
        """
        try:
            # Get default parameters for this memory type
            default_params = self._default_params.get(memory_type, {}).copy()
            
            # Override with global config if available
            if memory_type in self._config:
                default_params.update(self._config[memory_type])
            
            # Override with provided kwargs
            default_params.update(kwargs)
            
            # Load the memory class
            memory_class = self._load_memory_class(memory_type)
            
            # Create and return the memory instance
            logger.debug("Creating %s memory with params: %s", memory_type, default_params)
            return memory_class(**default_params)
            
        except (MemoryTypeNotFoundError, MemoryInitializationError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.exception("Error creating memory of type %s: %s", memory_type, str(e))
            raise MemoryCreationError(f"Failed to create {memory_type} memory: {str(e)}")
    
    def create_memory_system(self, config: dict[str, dict[str, Any]]) -> dict[str, MemorySystem]:
        """
        Create a complete memory system with multiple memory components.
        
        Args:
            config (Dict[str, Dict[str, Any]]): Configuration for each memory component.
                The keys are memory types and the values are parameter dictionaries.
                
        Returns:
            Dict[str, MemorySystem]: Dictionary mapping memory types to their instances
            
        Raises:
            MemoryConfigurationError: If the configuration is invalid
            MemoryCreationError: If there's an error creating any memory component
        """
        if not isinstance(config, dict):
            raise MemoryConfigurationError("Memory system configuration must be a dictionary")
        
        memory_system = {}
        creation_errors = []
        
        for memory_type, params in config.items():
            try:
                memory_system[memory_type] = self.create_memory(memory_type, **params)
            except Exception as e:
                error_msg = f"Failed to create {memory_type} memory: {str(e)}"
                creation_errors.append(error_msg)
                logger.error(error_msg)
        
        if creation_errors:
            raise MemoryCreationError(
                f"Failed to create memory system. Errors: {'; '.join(creation_errors)}"
            )
        
        logger.info("Created memory system with components: %s", list(memory_system.keys()))
        return memory_system
    
    def get_available_memory_types(self) -> list[str]:
        """
        Get a list of all available memory types.
        
        Returns:
            list[str]: List of available memory type names
        """
        return list(self._MEMORY_TYPE_MAPPING.keys())
    
    def get_memory_type_info(self, memory_type: str) -> dict[str, Any]:
        """
        Get information about a specific memory type, including its default parameters.
        
        Args:
            memory_type (str): The memory type to get information for
            
        Returns:
            Dict[str, Any]: Information about the memory type
            
        Raises:
            MemoryTypeNotFoundError: If the memory type is not supported
        """
        if memory_type not in self._MEMORY_TYPE_MAPPING:
            raise MemoryTypeNotFoundError(f"Unsupported memory type: {memory_type}")
        
        # Get the memory class to access its docstring and other attributes
        memory_class = self._load_memory_class(memory_type)
        
        return {
            "name": memory_type,
            "class": self._MEMORY_TYPE_MAPPING[memory_type],
            "description": memory_class.__doc__,
            "default_params": self._default_params.get(memory_type, {}),
        }
