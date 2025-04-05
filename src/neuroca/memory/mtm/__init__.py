"""
Medium-Term Memory (MTM) Module for NeuroCognitive Architecture.

This module implements the Medium-Term Memory component of the three-tiered memory system
in the NeuroCognitive Architecture (NCA). MTM serves as an intermediate storage layer
between Short-Term Memory (STM) and Long-Term Memory (LTM), handling information that
needs to be retained for minutes to hours.

Key characteristics of MTM:
- Retention period: Minutes to hours
- Capacity: Larger than STM but smaller than LTM
- Access speed: Faster than LTM but slower than STM
- Consolidation: Processes information from STM and prepares it for potential LTM storage
- Decay: Information gradually decays unless reinforced

Usage:
    from neuroca.memory.mtm import MTMStore, MTMEntry
    
    # Create a new MTM store
    mtm_store = MTMStore()
    
    # Store information in MTM
    entry_id = mtm_store.store("conversation_123", {
        "content": "User asked about project timeline",
        "importance": 0.75,
        "context": {"project": "NeuroCognitive Architecture"}
    })
    
    # Retrieve information from MTM
    entry = mtm_store.retrieve(entry_id)
    
    # Query MTM based on criteria
    relevant_entries = mtm_store.query(
        filters={"context.project": "NeuroCognitive Architecture"},
        min_importance=0.7
    )
    
    # Update decay parameters
    mtm_store.set_decay_rate(0.05)  # 5% decay per time unit

See Also:
    - neuroca.memory.stm: Short-Term Memory module
    - neuroca.memory.ltm: Long-Term Memory module
    - neuroca.memory.consolidation: Memory consolidation processes
"""

import logging
from typing import Any, Optional

# Configure module logger
logger = logging.getLogger(__name__)

# Import core MTM components
try:
    from .consolidation import MTMConsolidator
    from .decay import DecayFunction, ExponentialDecay, LinearDecay
    from .entry import MTMEntry
    from .exceptions import MTMConsolidationError, MTMError, MTMRetrievalError, MTMStorageError
    from .query import MTMQuery
    from .store import MTMStore
    
    # Make these classes available when importing from the module
    __all__ = [
        'MTMStore',
        'MTMEntry',
        'MTMQuery',
        'MTMConsolidator',
        'DecayFunction',
        'LinearDecay',
        'ExponentialDecay',
        'MTMError',
        'MTMStorageError',
        'MTMRetrievalError',
        'MTMConsolidationError',
        'get_default_mtm_config',
        'create_mtm_store'
    ]
    
except ImportError as e:
    logger.error(f"Failed to import MTM components: {str(e)}")
    # Re-raise with more context to help with debugging
    raise ImportError(f"MTM module initialization failed: {str(e)}. "
                      f"Please ensure all required packages are installed.") from e

# Module version
__version__ = '0.1.0'


def get_default_mtm_config() -> dict[str, Any]:
    """
    Return the default configuration for Medium-Term Memory.
    
    This provides sensible defaults for MTM parameters including capacity,
    decay rates, and consolidation thresholds.
    
    Returns:
        Dict[str, Any]: Default configuration dictionary for MTM
        
    Example:
        config = get_default_mtm_config()
        config['capacity'] = 1000  # Override default capacity
        mtm_store = create_mtm_store(config)
    """
    return {
        'capacity': 500,  # Maximum number of entries
        'default_retention_period': 3600,  # Default retention in seconds (1 hour)
        'decay_function': 'exponential',  # 'linear' or 'exponential'
        'decay_rate': 0.05,  # Base decay rate
        'importance_weight': 0.7,  # How much importance affects decay
        'recency_weight': 0.3,  # How much recency affects decay
        'consolidation_threshold': 0.8,  # Threshold for LTM consolidation
        'retrieval_boost': 0.2,  # Boost to importance when retrieved
        'enable_auto_consolidation': True,  # Automatically consolidate to LTM
    }


def create_mtm_store(config: Optional[dict[str, Any]] = None) -> 'MTMStore':
    """
    Create and configure a new Medium-Term Memory store.
    
    This factory function creates an MTM store with the specified configuration,
    or uses default values if not provided.
    
    Args:
        config (Optional[Dict[str, Any]]): Configuration parameters for the MTM store.
            If None, default configuration is used.
            
    Returns:
        MTMStore: A configured Medium-Term Memory store instance
        
    Raises:
        MTMError: If the store cannot be created with the given configuration
        
    Example:
        # Create with default configuration
        mtm_store = create_mtm_store()
        
        # Create with custom configuration
        mtm_store = create_mtm_store({
            'capacity': 1000,
            'decay_function': 'linear',
            'decay_rate': 0.1
        })
    """
    try:
        # Start with default config
        effective_config = get_default_mtm_config()
        
        # Update with user-provided config if any
        if config:
            effective_config.update(config)
        
        # Create decay function based on configuration
        if effective_config['decay_function'] == 'linear':
            decay_func = LinearDecay(
                rate=effective_config['decay_rate'],
                importance_weight=effective_config['importance_weight'],
                recency_weight=effective_config['recency_weight']
            )
        else:  # exponential decay is the default
            decay_func = ExponentialDecay(
                rate=effective_config['decay_rate'],
                importance_weight=effective_config['importance_weight'],
                recency_weight=effective_config['recency_weight']
            )
        
        # Create and configure the MTM store
        store = MTMStore(
            capacity=effective_config['capacity'],
            default_retention_period=effective_config['default_retention_period'],
            decay_function=decay_func,
            consolidation_threshold=effective_config['consolidation_threshold'],
            retrieval_boost=effective_config['retrieval_boost'],
            enable_auto_consolidation=effective_config['enable_auto_consolidation']
        )
        
        logger.info(f"Created MTM store with capacity {effective_config['capacity']} "
                   f"and {effective_config['decay_function']} decay")
        
        return store
        
    except Exception as e:
        logger.error(f"Failed to create MTM store: {str(e)}")
        raise MTMError(f"Failed to create MTM store: {str(e)}") from e


# Initialize module-level state
logger.debug("Initializing MTM module")