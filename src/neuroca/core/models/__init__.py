"""
Core Models Package for NeuroCognitive Architecture (NCA)

This package contains the core domain models that represent the fundamental
entities and concepts within the NeuroCognitive Architecture system. These models
form the foundation of the system's domain logic and are used throughout the application.

The models in this package follow domain-driven design principles and are designed
to be persistence-agnostic, focusing on business logic and domain rules rather than
storage concerns.

Usage:
    from neuroca.core.models import BaseModel, ModelRegistry
    from neuroca.core.models.cognitive import CognitiveState
    from neuroca.core.models.memory import MemoryItem

Models are organized into submodules by domain area:
- base: Base model classes and common utilities
- cognitive: Models related to cognitive processes and states
- memory: Models for the three-tiered memory system
- health: Models for system health and monitoring
- agent: Models for agent behavior and characteristics

This module exports commonly used models directly for convenience while
maintaining the ability to import specific models from their respective submodules.
"""

import logging
from typing import Dict, List, Optional, Set, Type, TypeVar, Union

# Configure module-level logger
logger = logging.getLogger(__name__)

# Import and re-export base models and utilities
from neuroca.core.models.base import (  # noqa: E402
    BaseModel,
    ModelRegistry,
    Serializable,
    ValidationError,
    ModelID,
)

# Import and re-export cognitive models
try:
    from neuroca.core.models.cognitive import (  # noqa: E402
        CognitiveState,
        CognitiveProcess,
        Attention,
        WorkingMemoryBuffer,
    )
except ImportError:
    logger.warning("Cognitive models could not be imported. Some functionality may be limited.")
    # Define placeholder classes to prevent import errors elsewhere
    class CognitiveState(BaseModel): pass
    class CognitiveProcess(BaseModel): pass
    class Attention(BaseModel): pass
    class WorkingMemoryBuffer(BaseModel): pass

# Import and re-export memory models
try:
    from neuroca.core.models.memory import (  # noqa: E402
        MemoryItem,
        ShortTermMemory,
        LongTermMemory,
        EpisodicMemory,
        SemanticMemory,
        ProceduralMemory,
        MemoryRetrieval,
        MemoryEncoding,
    )
except ImportError:
    logger.warning("Memory models could not be imported. Memory functionality will be limited.")
    # Define placeholder classes to prevent import errors elsewhere
    class MemoryItem(BaseModel): pass
    class ShortTermMemory(BaseModel): pass
    class LongTermMemory(BaseModel): pass
    class EpisodicMemory(BaseModel): pass
    class SemanticMemory(BaseModel): pass
    class ProceduralMemory(BaseModel): pass
    class MemoryRetrieval(BaseModel): pass
    class MemoryEncoding(BaseModel): pass

# Import and re-export health models
try:
    from neuroca.core.models.health import (  # noqa: E402
        HealthMetrics,
        SystemState,
        ResourceUtilization,
        PerformanceIndicators,
    )
except ImportError:
    logger.warning("Health models could not be imported. Health monitoring may be limited.")
    # Define placeholder classes to prevent import errors elsewhere
    class HealthMetrics(BaseModel): pass
    class SystemState(BaseModel): pass
    class ResourceUtilization(BaseModel): pass
    class PerformanceIndicators(BaseModel): pass

# Import and re-export agent models
try:
    from neuroca.core.models.agent import (  # noqa: E402
        Agent,
        AgentProfile,
        AgentCapability,
        AgentState,
    )
except ImportError:
    logger.warning("Agent models could not be imported. Agent functionality may be limited.")
    # Define placeholder classes to prevent import errors elsewhere
    class Agent(BaseModel): pass
    class AgentProfile(BaseModel): pass
    class AgentCapability(BaseModel): pass
    class AgentState(BaseModel): pass

# Type variable for generic model operations
T = TypeVar('T', bound=BaseModel)

# Define what's available for import from this package
__all__ = [
    # Base models
    'BaseModel',
    'ModelRegistry',
    'Serializable',
    'ValidationError',
    'ModelID',
    
    # Cognitive models
    'CognitiveState',
    'CognitiveProcess',
    'Attention',
    'WorkingMemoryBuffer',
    
    # Memory models
    'MemoryItem',
    'ShortTermMemory',
    'LongTermMemory',
    'EpisodicMemory',
    'SemanticMemory',
    'ProceduralMemory',
    'MemoryRetrieval',
    'MemoryEncoding',
    
    # Health models
    'HealthMetrics',
    'SystemState',
    'ResourceUtilization',
    'PerformanceIndicators',
    
    # Agent models
    'Agent',
    'AgentProfile',
    'AgentCapability',
    'AgentState',
]

# Initialize the model registry
model_registry = ModelRegistry()

# Register all models with the registry
def register_models() -> None:
    """
    Register all model classes with the global model registry.
    This enables model lookup, validation, and other registry-based operations.
    
    This function should be called during application initialization.
    
    Returns:
        None
    
    Raises:
        ImportError: If critical model modules cannot be imported
        RuntimeError: If model registration fails
    """
    try:
        for model_class in [cls for name, cls in globals().items() 
                           if isinstance(cls, type) and issubclass(cls, BaseModel) and cls != BaseModel]:
            model_registry.register(model_class)
        logger.info(f"Successfully registered {len(model_registry)} models")
    except Exception as e:
        logger.error(f"Error registering models: {str(e)}")
        raise RuntimeError(f"Failed to register models: {str(e)}") from e

# Version information
__version__ = '0.1.0'

logger.debug(f"Initialized core models package v{__version__}")