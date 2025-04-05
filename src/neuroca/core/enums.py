"""
Enumerations for the NeuroCognitive Architecture (NCA) system.

This module defines all the enumeration types used throughout the NCA system,
providing standardized constants for various aspects of the cognitive architecture
including memory types, cognitive states, health indicators, and processing modes.

These enumerations help maintain consistency across the codebase and provide
type safety for critical system parameters.

Usage:
    from neuroca.core.enums import MemoryTier, CognitiveState
    
    # Check memory tier
    if memory.tier == MemoryTier.WORKING:
        # Process working memory
        
    # Set cognitive state
    agent.set_state(CognitiveState.FOCUSED)
"""

import logging
from enum import Enum, auto, unique

logger = logging.getLogger(__name__)

@unique
class MemoryTier(Enum):
    """
    Represents the three-tiered memory system in the NCA.
    
    Attributes:
        WORKING: Short-term, limited capacity, high-access speed memory
        EPISODIC: Medium-term memory for experiences and events
        SEMANTIC: Long-term memory for facts, concepts, and knowledge
    """
    WORKING = auto()
    EPISODIC = auto()
    SEMANTIC = auto()
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, tier_name: str) -> 'MemoryTier':
        """
        Convert a string to a MemoryTier enum value.
        
        Args:
            tier_name: String representation of the memory tier
            
        Returns:
            Corresponding MemoryTier enum value
            
        Raises:
            ValueError: If the string doesn't match any memory tier
        """
        try:
            return cls[tier_name.upper()]
        except KeyError:
            valid_tiers = [t.name.lower() for t in cls]
            logger.error(f"Invalid memory tier: '{tier_name}'. Valid tiers are: {', '.join(valid_tiers)}")
            raise ValueError(f"Invalid memory tier: '{tier_name}'. Valid tiers are: {', '.join(valid_tiers)}")


@unique
class CognitiveState(Enum):
    """
    Represents the possible cognitive states of the NCA.
    
    These states influence processing priorities, attention mechanisms,
    and resource allocation within the architecture.
    """
    IDLE = auto()        # Default state, minimal processing
    FOCUSED = auto()     # Concentrated on specific task
    LEARNING = auto()    # Prioritizing knowledge acquisition
    CREATIVE = auto()    # Emphasizing novel connections
    ANALYTICAL = auto()  # Detailed logical processing
    REFLECTIVE = auto()  # Internal state assessment
    EXPLORATORY = auto() # Seeking new information
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, state_name: str) -> 'CognitiveState':
        """
        Convert a string to a CognitiveState enum value.
        
        Args:
            state_name: String representation of the cognitive state
            
        Returns:
            Corresponding CognitiveState enum value
            
        Raises:
            ValueError: If the string doesn't match any cognitive state
        """
        try:
            return cls[state_name.upper()]
        except KeyError:
            valid_states = [s.name.lower() for s in cls]
            logger.error(f"Invalid cognitive state: '{state_name}'. Valid states are: {', '.join(valid_states)}")
            raise ValueError(f"Invalid cognitive state: '{state_name}'. Valid states are: {', '.join(valid_states)}")


@unique
class HealthIndicator(Enum):
    """
    Health indicators for the NCA system's biological-inspired dynamics.
    
    These indicators represent various aspects of the system's operational health,
    which can influence performance, decision-making, and resource allocation.
    """
    ENERGY = auto()       # Available computational resources
    COHERENCE = auto()    # Internal consistency of knowledge
    STABILITY = auto()    # Resistance to rapid state changes
    ADAPTABILITY = auto() # Ability to adjust to new information
    EFFICIENCY = auto()   # Resource utilization optimization
    RESILIENCE = auto()   # Recovery from errors or contradictions
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, indicator_name: str) -> 'HealthIndicator':
        """
        Convert a string to a HealthIndicator enum value.
        
        Args:
            indicator_name: String representation of the health indicator
            
        Returns:
            Corresponding HealthIndicator enum value
            
        Raises:
            ValueError: If the string doesn't match any health indicator
        """
        try:
            return cls[indicator_name.upper()]
        except KeyError:
            valid_indicators = [i.name.lower() for i in cls]
            logger.error(f"Invalid health indicator: '{indicator_name}'. Valid indicators are: {', '.join(valid_indicators)}")
            raise ValueError(f"Invalid health indicator: '{indicator_name}'. Valid indicators are: {', '.join(valid_indicators)}")


@unique
class ProcessingMode(Enum):
    """
    Processing modes for the NCA system.
    
    These modes determine how information is processed, affecting
    the balance between speed, depth, and resource utilization.
    """
    FAST = auto()      # Quick, heuristic-based processing
    DEEP = auto()      # Thorough, resource-intensive processing
    BALANCED = auto()  # Moderate balance of speed and depth
    ADAPTIVE = auto()  # Dynamically adjusts based on context
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, mode_name: str) -> 'ProcessingMode':
        """
        Convert a string to a ProcessingMode enum value.
        
        Args:
            mode_name: String representation of the processing mode
            
        Returns:
            Corresponding ProcessingMode enum value
            
        Raises:
            ValueError: If the string doesn't match any processing mode
        """
        try:
            return cls[mode_name.upper()]
        except KeyError:
            valid_modes = [m.name.lower() for m in cls]
            logger.error(f"Invalid processing mode: '{mode_name}'. Valid modes are: {', '.join(valid_modes)}")
            raise ValueError(f"Invalid processing mode: '{mode_name}'. Valid modes are: {', '.join(valid_modes)}")


@unique
class MemoryOperation(Enum):
    """
    Operations that can be performed on memory.
    
    These operations represent the fundamental actions that can be
    taken with memory items across the different memory tiers.
    """
    STORE = auto()    # Add new information to memory
    RETRIEVE = auto() # Access existing information
    UPDATE = auto()   # Modify existing information
    FORGET = auto()   # Remove or decay information
    CONSOLIDATE = auto() # Move between memory tiers
    ASSOCIATE = auto()   # Create links between memory items
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, operation_name: str) -> 'MemoryOperation':
        """
        Convert a string to a MemoryOperation enum value.
        
        Args:
            operation_name: String representation of the memory operation
            
        Returns:
            Corresponding MemoryOperation enum value
            
        Raises:
            ValueError: If the string doesn't match any memory operation
        """
        try:
            return cls[operation_name.upper()]
        except KeyError:
            valid_operations = [o.name.lower() for o in cls]
            logger.error(f"Invalid memory operation: '{operation_name}'. Valid operations are: {', '.join(valid_operations)}")
            raise ValueError(f"Invalid memory operation: '{operation_name}'. Valid operations are: {', '.join(valid_operations)}")


@unique
class Priority(Enum):
    """
    Priority levels for tasks, memories, and processes.
    
    These priorities help the system allocate resources and
    determine processing order for competing demands.
    """
    CRITICAL = 5   # Highest priority, immediate attention required
    HIGH = 4       # Important, should be processed soon
    MEDIUM = 3     # Standard priority
    LOW = 2        # Process when resources available
    BACKGROUND = 1 # Lowest priority, process during idle time
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, priority_name: str) -> 'Priority':
        """
        Convert a string to a Priority enum value.
        
        Args:
            priority_name: String representation of the priority
            
        Returns:
            Corresponding Priority enum value
            
        Raises:
            ValueError: If the string doesn't match any priority
        """
        try:
            return cls[priority_name.upper()]
        except KeyError:
            valid_priorities = [p.name.lower() for p in cls]
            logger.error(f"Invalid priority: '{priority_name}'. Valid priorities are: {', '.join(valid_priorities)}")
            raise ValueError(f"Invalid priority: '{priority_name}'. Valid priorities are: {', '.join(valid_priorities)}")
    
    @classmethod
    def from_int(cls, value: int) -> 'Priority':
        """
        Convert an integer to a Priority enum value.
        
        Args:
            value: Integer value of the priority (1-5)
            
        Returns:
            Corresponding Priority enum value
            
        Raises:
            ValueError: If the integer doesn't match any priority
        """
        for priority in cls:
            if priority.value == value:
                return priority
        
        valid_values = [str(p.value) for p in cls]
        logger.error(f"Invalid priority value: {value}. Valid values are: {', '.join(valid_values)}")
        raise ValueError(f"Invalid priority value: {value}. Valid values are: {', '.join(valid_values)}")


@unique
class IntegrationMode(Enum):
    """
    Modes for integrating with external LLM systems.
    
    These modes determine how the NCA system interacts with
    and utilizes external language models.
    """
    STANDALONE = auto()  # NCA operates independently
    AUGMENTED = auto()   # NCA enhances LLM capabilities
    EMBEDDED = auto()    # NCA runs within LLM context
    COLLABORATIVE = auto() # NCA and LLM work as peers
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, mode_name: str) -> 'IntegrationMode':
        """
        Convert a string to an IntegrationMode enum value.
        
        Args:
            mode_name: String representation of the integration mode
            
        Returns:
            Corresponding IntegrationMode enum value
            
        Raises:
            ValueError: If the string doesn't match any integration mode
        """
        try:
            return cls[mode_name.upper()]
        except KeyError:
            valid_modes = [m.name.lower() for m in cls]
            logger.error(f"Invalid integration mode: '{mode_name}'. Valid modes are: {', '.join(valid_modes)}")
            raise ValueError(f"Invalid integration mode: '{mode_name}'. Valid modes are: {', '.join(valid_modes)}")


@unique
class LogLevel(Enum):
    """
    Log levels for the NCA system.
    
    These levels correspond to standard logging levels but are
    exposed as an enum for type safety and consistency.
    """
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    
    def __str__(self) -> str:
        return self.name.lower()
    
    @classmethod
    def from_string(cls, level_name: str) -> 'LogLevel':
        """
        Convert a string to a LogLevel enum value.
        
        Args:
            level_name: String representation of the log level
            
        Returns:
            Corresponding LogLevel enum value
            
        Raises:
            ValueError: If the string doesn't match any log level
        """
        try:
            return cls[level_name.upper()]
        except KeyError:
            valid_levels = [l.name.lower() for l in cls]
            logger.error(f"Invalid log level: '{level_name}'. Valid levels are: {', '.join(valid_levels)}")
            raise ValueError(f"Invalid log level: '{level_name}'. Valid levels are: {', '.join(valid_levels)}")
    
    def to_logging_level(self) -> int:
        """
        Convert the enum value to a standard logging module level.
        
        Returns:
            Integer value corresponding to logging module levels
        """
        return self.value