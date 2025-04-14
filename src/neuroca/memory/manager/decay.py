"""
Memory Manager Decay

This module handles the decay of memory strength over time.
It decreases the strength of memories based on time since last access, access count, and importance.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from neuroca.memory.backends import MemoryTier

# Configure logger
logger = logging.getLogger(__name__)


async def decay_mtm_memories(mtm_storage, config: Dict[str, Any]) -> None:
    """Apply decay to MTM memories based on age and access patterns."""
    logger.debug("Starting MTM memory decay")
    
    try:
        # Get all MTM memories
        mtm_memories = await mtm_storage.list_all()
        
        # Skip if no memories
        if not mtm_memories:
            return
        
        current_time = datetime.now()
        
        # Apply decay to each memory
        for memory in mtm_memories:
            try:
                # Get memory ID
                memory_id = getattr(memory, "id", None)
                if not memory_id:
                    continue
                
                # Get current strength or initialize it
                strength = 1.0  # Default full strength
                if hasattr(memory, "metadata") and memory.metadata:
                    if isinstance(memory.metadata, dict) and "strength" in memory.metadata:
                        strength = memory.metadata.get("strength", 1.0)
                
                # Calculate decay factor based on:
                # - Time since last access
                # - Access count
                # - Importance
                
                # Get last accessed time
                last_accessed = current_time
                if hasattr(memory, "last_accessed") and memory.last_accessed:
                    last_accessed = memory.last_accessed
                
                # Get age in days
                days_since_access = (current_time - last_accessed).days
                
                # Get access count
                access_count = getattr(memory, "access_count", 0)
                
                # Get importance
                importance = 0.5
                if hasattr(memory, "metadata") and memory.metadata:
                    if isinstance(memory.metadata, dict) and "importance" in memory.metadata:
                        importance = memory.metadata.get("importance", 0.5)
                
                # Calculate decay factor
                # High importance and high access count slow decay
                # More time since last access increases decay
                base_decay = 0.01  # Base daily decay rate
                importance_factor = 1.0 - (importance * 0.5)  # Higher importance = slower decay
                access_factor = 1.0 - min(access_count / 20, 0.5)  # Higher access = slower decay
                time_factor = min(days_since_access / 30, 1.0)  # More time = more decay, max out at 30 days
                
                decay_amount = base_decay * importance_factor * access_factor * time_factor
                
                # Apply decay to strength
                new_strength = max(0.0, strength - decay_amount)
                
                # Update memory metadata with new strength
                if hasattr(memory, "metadata") and memory.metadata:
                    if isinstance(memory.metadata, dict):
                        memory.metadata["strength"] = new_strength
                        
                        # Update the memory
                        await mtm_storage.update(memory_id, metadata=memory.metadata)
                
                # If strength is below threshold, mark for forgetting
                if new_strength < 0.1:  # Threshold for forgetting
                    await mtm_storage.forget_memory(memory_id)
                    logger.info(f"Memory {memory_id} strength decayed to {new_strength:.2f}, marked as forgotten")
            
            except Exception as e:
                logger.error(f"Error applying decay to MTM memory {memory_id}: {str(e)}")
                continue
    
    except Exception as e:
        logger.error(f"Error in MTM memory decay: {str(e)}")


async def decay_ltm_memories(ltm_storage, config: Dict[str, Any]) -> None:
    """Apply decay to LTM memories based on age and access patterns."""
    logger.debug("Starting LTM memory decay")
    
    try:
        # For LTM, we'll use a different approach since we can't easily get all memories
        # Instead, we'll focus on memories that haven't been accessed in a long time
        
        # This is a simplified implementation
        # In a real system, you might use a database query to find memories
        # that haven't been accessed in a long time
        
        # For now, we'll just log a message
        logger.debug("LTM decay not fully implemented yet")
    
    except Exception as e:
        logger.error(f"Error in LTM memory decay: {str(e)}")


async def strengthen_memory(
    memory_id: str,
    tier: MemoryTier,
    mtm_storage=None,
    ltm_storage=None,
    strengthen_amount: float = 0.1
) -> None:
    """
    Strengthen a memory by increasing its strength and updating access metrics.
    
    Args:
        memory_id: Memory ID
        tier: Memory tier
        mtm_storage: MTM storage backend (required for MTM memories)
        ltm_storage: LTM storage backend (required for LTM memories)
        strengthen_amount: Amount to increase strength (0.0 to 1.0)
    """
    if not memory_id:
        return
    
    try:
        if tier == MemoryTier.MTM:
            if not mtm_storage:
                logger.error("MTM storage not provided for strengthening MTM memory")
                return
                
            # Get the memory
            memory = await mtm_storage.retrieve(memory_id)
            if not memory:
                return
            
            # Update strength in metadata
            metadata = getattr(memory, "metadata", {}) or {}
            if not isinstance(metadata, dict):
                metadata = {}
            
            # Get current strength or initialize it
            current_strength = metadata.get("strength", 1.0)
            
            # Increase strength, but cap at 1.0
            new_strength = min(1.0, current_strength + strengthen_amount)
            metadata["strength"] = new_strength
            
            # Update the memory
            await mtm_storage.update(memory_id, metadata=metadata)
            logger.debug(f"Strengthened MTM memory {memory_id} to {new_strength:.2f}")
        
        elif tier == MemoryTier.LTM:
            if not ltm_storage:
                logger.error("LTM storage not provided for strengthening LTM memory")
                return
                
            # For LTM, we need to get the memory, modify it, and save it back
            memory = await ltm_storage.get(memory_id)
            if not memory:
                return
            
            # Update strength in metadata
            if memory.metadata:
                # Get current strength or initialize it
                metadata_dict = memory.metadata.dict()
                current_strength = metadata_dict.get("strength", 1.0)
                
                # Increase strength, but cap at 1.0
                new_strength = min(1.0, current_strength + strengthen_amount)
                metadata_dict["strength"] = new_strength
                
                # Create updated metadata
                updated_metadata = memory.metadata.__class__(**metadata_dict)
                memory.metadata = updated_metadata
                
                # Update the memory
                await ltm_storage.update(memory)
                logger.debug(f"Strengthened LTM memory {memory_id} to {new_strength:.2f}")
    
    except Exception as e:
        logger.error(f"Error strengthening memory {memory_id}: {str(e)}")
