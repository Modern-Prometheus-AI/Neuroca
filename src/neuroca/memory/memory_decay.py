"""
Memory decay functionality for the NCA system.

This module handles the decay of memories over time to simulate
the natural forgetting process of human memory.
"""

import math
from datetime import datetime, timedelta
from typing import Any, Optional


def calculate_decay(memory: dict[str, Any], current_time: Optional[datetime] = None) -> float:
    """
    Calculate the decay value for a memory based on its age and access patterns.
    
    Args:
        memory: The memory object to calculate decay for
        current_time: Current time reference (defaults to now)
        
    Returns:
        Decay factor between 0.0 (completely decayed) and 1.0 (no decay)
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Use a simple exponential decay model
    # This is a stub implementation
    memory_age = timedelta(days=1)  # Placeholder - would be calculated from memory creation time
    decay_factor = math.exp(-0.1 * memory_age.days)
    
    return max(0.0, min(1.0, decay_factor))


def apply_decay_to_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Apply decay to a list of memories.
    
    Args:
        memories: List of memory objects
        
    Returns:
        List of memories with decay applied
    """
    # This is a stub implementation
    for memory in memories:
        memory['strength'] = memory.get('strength', 1.0) * calculate_decay(memory)
    
    return memories 