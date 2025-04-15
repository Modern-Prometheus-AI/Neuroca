"""
Memory Consolidation Adapter

This module provides adapters for legacy memory consolidation functions
using the new memory system architecture. These adapters delegate to
the Memory Manager and tier-specific consolidation components.

This adapter is provided for backward compatibility during migration
and will be removed in a future version.
"""

import asyncio
import logging
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.exceptions import (
    MemoryNotFoundError,
    TierOperationError,
    InvalidTierError,
)


logger = logging.getLogger(__name__)


async def consolidate_memory(
    memory_manager: MemoryManager,
    memory_id: str,
    source_tier: str,
    target_tier: str,
    **kwargs
) -> Optional[str]:
    """
    Consolidate a memory from one tier to another.
    
    Args:
        memory_manager: Memory manager instance
        memory_id: Memory ID
        source_tier: Source tier
        target_tier: Target tier
        **kwargs: Additional parameters
    
    Returns:
        New memory ID in target tier, or None if consolidation failed
    
    DEPRECATED: Use MemoryManager.consolidate_memory() directly.
    """
    warnings.warn(
        "consolidate_memory() is deprecated. Use MemoryManager.consolidate_memory() directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        # Extract additional metadata from kwargs
        additional_metadata = {}
        if "metadata" in kwargs:
            additional_metadata.update(kwargs["metadata"])
        
        # Add timestamp if not present
        if "consolidation_timestamp" not in additional_metadata:
            import time
            additional_metadata["consolidation_timestamp"] = time.time()
        
        # Mark as consolidated
        additional_metadata["consolidated"] = True
        
        # Execute consolidation
        return await memory_manager.consolidate_memory(
            memory_id=memory_id,
            source_tier=source_tier,
            target_tier=target_tier,
            additional_metadata=additional_metadata
        )
    except (MemoryNotFoundError, InvalidTierError) as e:
        # Re-raise specific errors
        raise e
    except Exception as e:
        logger.error(f"Failed to consolidate memory {memory_id}: {str(e)}")
        return None


async def auto_consolidate_stm_to_mtm(
    memory_manager: MemoryManager,
    limit: int = 10,
    min_importance: float = 0.7,
    min_access_count: int = 3,
    **kwargs
) -> List[str]:
    """
    Automatically consolidate eligible memories from STM to MTM.
    
    Args:
        memory_manager: Memory manager instance
        limit: Maximum number of memories to consolidate
        min_importance: Minimum importance for consolidation
        min_access_count: Minimum access count for consolidation
        **kwargs: Additional parameters
    
    Returns:
        List of consolidated memory IDs
    
    DEPRECATED: Use MemoryManager.run_maintenance() instead.
    """
    warnings.warn(
        "auto_consolidate_stm_to_mtm() is deprecated. Use MemoryManager.run_maintenance() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        # Get eligible STM memories
        stm_memories = await memory_manager._stm.query(
            filters={
                "metadata.importance": {"$gte": min_importance},
                "metadata.access_count": {"$gte": min_access_count},
            },
            limit=limit,
        )
        
        # Consolidate eligible memories
        consolidated_ids = []
        for memory in stm_memories:
            memory_id = memory.get("id")
            if memory_id:
                try:
                    new_id = await consolidate_memory(
                        memory_manager=memory_manager,
                        memory_id=memory_id,
                        source_tier="stm",
                        target_tier="mtm",
                        **kwargs
                    )
                    if new_id:
                        consolidated_ids.append(new_id)
                except Exception as e:
                    logger.error(f"Failed to consolidate memory {memory_id}: {str(e)}")
        
        return consolidated_ids
    except Exception as e:
        logger.error(f"Failed to auto-consolidate memories: {str(e)}")
        return []


async def auto_consolidate_mtm_to_ltm(
    memory_manager: MemoryManager,
    limit: int = 5,
    min_importance: float = 0.8,
    min_strength: float = 0.7,
    **kwargs
) -> List[str]:
    """
    Automatically consolidate eligible memories from MTM to LTM.
    
    Args:
        memory_manager: Memory manager instance
        limit: Maximum number of memories to consolidate
        min_importance: Minimum importance for consolidation
        min_strength: Minimum strength for consolidation
        **kwargs: Additional parameters
    
    Returns:
        List of consolidated memory IDs
    
    DEPRECATED: Use MemoryManager.run_maintenance() instead.
    """
    warnings.warn(
        "auto_consolidate_mtm_to_ltm() is deprecated. Use MemoryManager.run_maintenance() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        # Get eligible MTM memories
        mtm_memories = await memory_manager._mtm.query(
            filters={
                "metadata.importance": {"$gte": min_importance},
                "metadata.strength": {"$gte": min_strength},
            },
            limit=limit,
        )
        
        # Consolidate eligible memories
        consolidated_ids = []
        for memory in mtm_memories:
            memory_id = memory.get("id")
            if memory_id:
                try:
                    new_id = await consolidate_memory(
                        memory_manager=memory_manager,
                        memory_id=memory_id,
                        source_tier="mtm",
                        target_tier="ltm",
                        **kwargs
                    )
                    if new_id:
                        consolidated_ids.append(new_id)
                except Exception as e:
                    logger.error(f"Failed to consolidate memory {memory_id}: {str(e)}")
        
        return consolidated_ids
    except Exception as e:
        logger.error(f"Failed to auto-consolidate memories: {str(e)}")
        return []


async def run_consolidation_cycle(
    memory_manager: MemoryManager,
    stm_to_mtm_limit: int = 10,
    mtm_to_ltm_limit: int = 5,
    **kwargs
) -> Dict[str, List[str]]:
    """
    Run a full consolidation cycle across all tiers.
    
    Args:
        memory_manager: Memory manager instance
        stm_to_mtm_limit: Maximum number of STM to MTM consolidations
        mtm_to_ltm_limit: Maximum number of MTM to LTM consolidations
        **kwargs: Additional parameters
    
    Returns:
        Dictionary with consolidated memory IDs by tier
    
    DEPRECATED: Use MemoryManager.run_maintenance() instead.
    """
    warnings.warn(
        "run_consolidation_cycle() is deprecated. Use MemoryManager.run_maintenance() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    results = {
        "stm_to_mtm": [],
        "mtm_to_ltm": [],
    }
    
    try:
        # Run STM to MTM consolidation
        results["stm_to_mtm"] = await auto_consolidate_stm_to_mtm(
            memory_manager=memory_manager,
            limit=stm_to_mtm_limit,
            **kwargs
        )
        
        # Run MTM to LTM consolidation
        results["mtm_to_ltm"] = await auto_consolidate_mtm_to_ltm(
            memory_manager=memory_manager,
            limit=mtm_to_ltm_limit,
            **kwargs
        )
        
        return results
    except Exception as e:
        logger.error(f"Failed to run consolidation cycle: {str(e)}")
        return results
