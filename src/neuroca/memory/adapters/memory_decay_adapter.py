"""
Memory Decay Adapter

This module provides adapters for legacy memory decay functions
using the new memory system architecture. These adapters delegate to
the Memory Manager and tier-specific decay components.

This adapter is provided for backward compatibility during migration
and will be removed in a future version.
"""

import asyncio
import logging
import time
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.exceptions import MemoryNotFoundError, TierOperationError


logger = logging.getLogger(__name__)


async def decay_memory(
    memory_manager: MemoryManager,
    memory_id: str,
    tier: Optional[str] = None,
    decay_amount: float = 0.1,
    **kwargs
) -> bool:
    """
    Decay a memory by reducing its strength.
    
    Args:
        memory_manager: Memory manager instance
        memory_id: Memory ID
        tier: Optional tier to decay in (tries all tiers if not specified)
        decay_amount: Amount to decay by (0.0 to 1.0)
        **kwargs: Additional parameters
    
    Returns:
        True if the decay was successful
    
    DEPRECATED: Use MemoryManager.decay_memory() directly.
    """
    warnings.warn(
        "decay_memory() is deprecated. Use MemoryManager.decay_memory() directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        return await memory_manager.decay_memory(
            memory_id=memory_id,
            tier=tier,
            decay_amount=decay_amount
        )
    except MemoryNotFoundError:
        logger.error(f"Memory {memory_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to decay memory {memory_id}: {str(e)}")
        return False


async def decay_memories_by_age(
    memory_manager: MemoryManager,
    tier: str,
    max_age_seconds: int,
    decay_amount: float = 0.1,
    limit: int = 100,
    **kwargs
) -> int:
    """
    Decay memories older than a specified age.
    
    Args:
        memory_manager: Memory manager instance
        tier: Tier to decay in
        max_age_seconds: Maximum age in seconds
        decay_amount: Amount to decay by (0.0 to 1.0)
        limit: Maximum number of memories to decay
        **kwargs: Additional parameters
    
    Returns:
        Number of memories decayed
    
    DEPRECATED: Use MemoryManager.run_maintenance() instead.
    """
    warnings.warn(
        "decay_memories_by_age() is deprecated. Use MemoryManager.run_maintenance() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        # Get tier instance
        tier_instance = None
        if tier == "stm":
            tier_instance = memory_manager._stm
        elif tier == "mtm":
            tier_instance = memory_manager._mtm
        elif tier == "ltm":
            tier_instance = memory_manager._ltm
        else:
            raise ValueError(f"Invalid tier: {tier}")
        
        # Calculate age threshold
        threshold_time = time.time() - max_age_seconds
        
        # Query memories older than threshold
        memories = await tier_instance.query(
            filters={
                "metadata.created_at": {"$lt": threshold_time},
            },
            limit=limit,
        )
        
        # Decay each memory
        decay_count = 0
        for memory in memories:
            memory_id = memory.get("id")
            if memory_id:
                try:
                    success = await memory_manager.decay_memory(
                        memory_id=memory_id,
                        tier=tier,
                        decay_amount=decay_amount
                    )
                    if success:
                        decay_count += 1
                except Exception as e:
                    logger.error(f"Failed to decay memory {memory_id}: {str(e)}")
        
        return decay_count
    except Exception as e:
        logger.error(f"Failed to decay memories by age: {str(e)}")
        return 0


async def decay_memories_by_criteria(
    memory_manager: MemoryManager,
    tier: str,
    criteria: Dict[str, Any],
    decay_amount: float = 0.1,
    limit: int = 100,
    **kwargs
) -> int:
    """
    Decay memories matching specified criteria.
    
    Args:
        memory_manager: Memory manager instance
        tier: Tier to decay in
        criteria: Query criteria
        decay_amount: Amount to decay by (0.0 to 1.0)
        limit: Maximum number of memories to decay
        **kwargs: Additional parameters
    
    Returns:
        Number of memories decayed
    
    DEPRECATED: Use tier-specific query and MemoryManager.decay_memory() instead.
    """
    warnings.warn(
        "decay_memories_by_criteria() is deprecated. Use tier-specific query and MemoryManager.decay_memory() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        # Get tier instance
        tier_instance = None
        if tier == "stm":
            tier_instance = memory_manager._stm
        elif tier == "mtm":
            tier_instance = memory_manager._mtm
        elif tier == "ltm":
            tier_instance = memory_manager._ltm
        else:
            raise ValueError(f"Invalid tier: {tier}")
        
        # Query memories matching criteria
        memories = await tier_instance.query(
            filters=criteria,
            limit=limit,
        )
        
        # Decay each memory
        decay_count = 0
        for memory in memories:
            memory_id = memory.get("id")
            if memory_id:
                try:
                    success = await memory_manager.decay_memory(
                        memory_id=memory_id,
                        tier=tier,
                        decay_amount=decay_amount
                    )
                    if success:
                        decay_count += 1
                except Exception as e:
                    logger.error(f"Failed to decay memory {memory_id}: {str(e)}")
        
        return decay_count
    except Exception as e:
        logger.error(f"Failed to decay memories by criteria: {str(e)}")
        return 0


async def run_decay_cycle(
    memory_manager: MemoryManager,
    stm_decay_amount: float = 0.2,
    stm_max_age_seconds: int = 3600,  # 1 hour
    mtm_decay_amount: float = 0.1,
    mtm_max_age_seconds: int = 86400,  # 24 hours
    limit: int = 100,
    **kwargs
) -> Dict[str, int]:
    """
    Run a full decay cycle across STM and MTM tiers.
    
    Args:
        memory_manager: Memory manager instance
        stm_decay_amount: Amount to decay STM memories by
        stm_max_age_seconds: Maximum age for STM memories
        mtm_decay_amount: Amount to decay MTM memories by
        mtm_max_age_seconds: Maximum age for MTM memories
        limit: Maximum number of memories to decay per tier
        **kwargs: Additional parameters
    
    Returns:
        Dictionary with number of memories decayed by tier
    
    DEPRECATED: Use MemoryManager.run_maintenance() instead.
    """
    warnings.warn(
        "run_decay_cycle() is deprecated. Use MemoryManager.run_maintenance() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    results = {
        "stm": 0,
        "mtm": 0,
    }
    
    try:
        # Run STM decay
        results["stm"] = await decay_memories_by_age(
            memory_manager=memory_manager,
            tier="stm",
            max_age_seconds=stm_max_age_seconds,
            decay_amount=stm_decay_amount,
            limit=limit,
            **kwargs
        )
        
        # Run MTM decay
        results["mtm"] = await decay_memories_by_age(
            memory_manager=memory_manager,
            tier="mtm",
            max_age_seconds=mtm_max_age_seconds,
            decay_amount=mtm_decay_amount,
            limit=limit,
            **kwargs
        )
        
        return results
    except Exception as e:
        logger.error(f"Failed to run decay cycle: {str(e)}")
        return results
