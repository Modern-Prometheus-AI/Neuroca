"""
Short-Term Memory (STM) Operations Module.

This module provides the core operations for managing short-term memory entries in the
NeuroCognitive Architecture (NCA). It implements CRUD operations for STM entries,
along with specialized operations like memory decay, prioritization, and consolidation
to long-term memory.

The STM is a temporary, capacity-limited storage system that holds information for
active processing. It follows cognitive science principles including:
- Limited capacity (typically 5-9 items)
- Temporal decay (items fade over time)
- Interference effects (similar items compete for retention)
- Prioritization based on relevance and recency

Usage:
    from neuroca.memory.stm.operations import (
        create_memory, retrieve_memory, update_memory, delete_memory,
        apply_decay, consolidate_to_ltm, get_all_memories, clear_expired
    )

    # Create a new STM entry
    memory_id = create_memory(content="Important fact", priority=0.8)

    # Retrieve a memory by ID
    memory = retrieve_memory(memory_id)

    # Update memory attributes
    update_memory(memory_id, priority=0.9, content="Updated important fact")

    # Apply decay to all memories based on elapsed time
    apply_decay(decay_rate=0.05)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from neuroca.config.settings import get_settings
from neuroca.core.utils.validation import sanitize_input
from neuroca.memory.ltm.operations import store_in_ltm
from neuroca.memory.stm.exceptions import (
    STMCapacityExceededError,
    STMEntryNotFoundError,
    STMStorageError,
)
from neuroca.memory.stm.models import STMEntry

# Configure logger
logger = logging.getLogger(__name__)

# Get configuration settings
settings = get_settings()
STM_MAX_CAPACITY = settings.memory.stm.max_capacity
STM_DEFAULT_TTL = settings.memory.stm.default_ttl_seconds
STM_MIN_PRIORITY_FOR_LTM = settings.memory.stm.min_priority_for_ltm
STM_DECAY_INTERVAL = settings.memory.stm.decay_interval_seconds

# In-memory storage for STM entries (in production, this might be Redis or another fast storage)
_stm_store: dict[str, STMEntry] = {}


def create_memory(
    content: str,
    priority: float = 0.5,
    metadata: Optional[dict[str, Any]] = None,
    ttl_seconds: Optional[int] = None,
    tags: Optional[list[str]] = None
) -> str:
    """
    Create a new short-term memory entry.
    
    Args:
        content: The content of the memory entry
        priority: Importance score between 0.0 and 1.0 (default: 0.5)
        metadata: Additional structured data associated with this memory
        ttl_seconds: Time-to-live in seconds before automatic decay (None = use default)
        tags: List of tags for categorizing the memory
        
    Returns:
        str: The unique ID of the created memory entry
        
    Raises:
        STMCapacityExceededError: If the STM is at maximum capacity
        ValueError: If input parameters are invalid
        STMStorageError: If there's an error storing the memory
    """
    # Validate inputs
    content = sanitize_input(content)
    if not content:
        raise ValueError("Memory content cannot be empty")
    
    if not 0.0 <= priority <= 1.0:
        raise ValueError("Priority must be between 0.0 and 1.0")
    
    # Check capacity before adding new entry
    if len(_stm_store) >= STM_MAX_CAPACITY:
        logger.warning(f"STM capacity exceeded ({STM_MAX_CAPACITY} items). Attempting to make room.")
        _make_room_for_new_entry(priority)
    
    # Generate unique ID
    memory_id = str(uuid.uuid4())
    
    # Set default values
    if metadata is None:
        metadata = {}
    
    if tags is None:
        tags = []
    
    if ttl_seconds is None:
        ttl_seconds = STM_DEFAULT_TTL
    
    # Create timestamp
    current_time = datetime.now()
    
    # Create the memory entry
    try:
        memory_entry = STMEntry(
            id=memory_id,
            content=content,
            priority=priority,
            created_at=current_time,
            last_accessed=current_time,
            access_count=0,
            metadata=metadata,
            expiry=current_time + timedelta(seconds=ttl_seconds),
            tags=tags,
            decay_factor=1.0  # Start with no decay
        )
        
        # Store the entry
        _stm_store[memory_id] = memory_entry
        
        logger.debug(f"Created STM entry: {memory_id} with priority {priority}")
        return memory_id
    
    except Exception as e:
        logger.error(f"Failed to create STM entry: {str(e)}")
        raise STMStorageError(f"Failed to store memory: {str(e)}") from e


def retrieve_memory(memory_id: str, update_access: bool = True) -> STMEntry:
    """
    Retrieve a memory entry by its ID.
    
    Args:
        memory_id: The unique ID of the memory to retrieve
        update_access: Whether to update last_accessed time and access_count (default: True)
        
    Returns:
        STMEntry: The retrieved memory entry
        
    Raises:
        STMEntryNotFoundError: If no memory with the given ID exists
    """
    try:
        if memory_id not in _stm_store:
            logger.warning(f"Attempted to retrieve non-existent STM entry: {memory_id}")
            raise STMEntryNotFoundError(f"No memory found with ID: {memory_id}")
        
        memory = _stm_store[memory_id]
        
        # Check if memory has expired
        if datetime.now() > memory.expiry:
            logger.info(f"Retrieved expired STM entry: {memory_id}. Entry will be removed.")
            delete_memory(memory_id)
            raise STMEntryNotFoundError(f"Memory with ID {memory_id} has expired")
        
        # Update access metadata if requested
        if update_access:
            memory.last_accessed = datetime.now()
            memory.access_count += 1
            _stm_store[memory_id] = memory
            logger.debug(f"Updated access for STM entry: {memory_id}, count: {memory.access_count}")
        
        return memory
    
    except STMEntryNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving STM entry {memory_id}: {str(e)}")
        raise STMStorageError(f"Failed to retrieve memory: {str(e)}") from e


def update_memory(
    memory_id: str,
    content: Optional[str] = None,
    priority: Optional[float] = None,
    metadata: Optional[dict[str, Any]] = None,
    ttl_seconds: Optional[int] = None,
    tags: Optional[list[str]] = None,
    decay_factor: Optional[float] = None
) -> STMEntry:
    """
    Update an existing memory entry.
    
    Args:
        memory_id: The unique ID of the memory to update
        content: New content (if None, keeps existing)
        priority: New priority (if None, keeps existing)
        metadata: New metadata (if None, keeps existing)
        ttl_seconds: New TTL in seconds (if None, keeps existing)
        tags: New tags (if None, keeps existing)
        decay_factor: New decay factor (if None, keeps existing)
        
    Returns:
        STMEntry: The updated memory entry
        
    Raises:
        STMEntryNotFoundError: If no memory with the given ID exists
        ValueError: If input parameters are invalid
    """
    # First retrieve the memory to ensure it exists and is not expired
    memory = retrieve_memory(memory_id, update_access=False)
    
    # Update fields if provided
    if content is not None:
        content = sanitize_input(content)
        if not content:
            raise ValueError("Memory content cannot be empty")
        memory.content = content
    
    if priority is not None:
        if not 0.0 <= priority <= 1.0:
            raise ValueError("Priority must be between 0.0 and 1.0")
        memory.priority = priority
    
    if metadata is not None:
        # Merge with existing metadata rather than replacing
        memory.metadata.update(metadata)
    
    if ttl_seconds is not None:
        if ttl_seconds <= 0:
            raise ValueError("TTL must be positive")
        memory.expiry = datetime.now() + timedelta(seconds=ttl_seconds)
    
    if tags is not None:
        memory.tags = tags
    
    if decay_factor is not None:
        if not 0.0 <= decay_factor <= 1.0:
            raise ValueError("Decay factor must be between 0.0 and 1.0")
        memory.decay_factor = decay_factor
    
    # Update last modified time
    memory.last_accessed = datetime.now()
    
    # Store updated memory
    try:
        _stm_store[memory_id] = memory
        logger.debug(f"Updated STM entry: {memory_id}")
        return memory
    except Exception as e:
        logger.error(f"Failed to update STM entry {memory_id}: {str(e)}")
        raise STMStorageError(f"Failed to update memory: {str(e)}") from e


def delete_memory(memory_id: str) -> bool:
    """
    Delete a memory entry by its ID.
    
    Args:
        memory_id: The unique ID of the memory to delete
        
    Returns:
        bool: True if the memory was deleted, False if it didn't exist
        
    Raises:
        STMStorageError: If there's an error deleting the memory
    """
    try:
        if memory_id in _stm_store:
            del _stm_store[memory_id]
            logger.debug(f"Deleted STM entry: {memory_id}")
            return True
        else:
            logger.warning(f"Attempted to delete non-existent STM entry: {memory_id}")
            return False
    except Exception as e:
        logger.error(f"Error deleting STM entry {memory_id}: {str(e)}")
        raise STMStorageError(f"Failed to delete memory: {str(e)}") from e


def get_all_memories(
    tag_filter: Optional[list[str]] = None,
    min_priority: float = 0.0,
    include_expired: bool = False
) -> list[STMEntry]:
    """
    Retrieve all memory entries, optionally filtered.
    
    Args:
        tag_filter: If provided, only return memories with these tags
        min_priority: Minimum priority threshold for returned memories
        include_expired: Whether to include expired memories
        
    Returns:
        List[STMEntry]: List of memory entries matching the criteria
    """
    result = []
    current_time = datetime.now()
    
    try:
        for memory in _stm_store.values():
            # Skip expired memories unless explicitly requested
            if not include_expired and current_time > memory.expiry:
                continue
                
            # Apply priority filter
            if memory.priority < min_priority:
                continue
                
            # Apply tag filter if provided
            if tag_filter and not any(tag in memory.tags for tag in tag_filter):
                continue
                
            result.append(memory)
            
        logger.debug(f"Retrieved {len(result)} STM entries matching criteria")
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving STM entries: {str(e)}")
        raise STMStorageError(f"Failed to retrieve memories: {str(e)}") from e


def apply_decay(decay_rate: float = 0.1) -> int:
    """
    Apply decay to all memories based on time elapsed and decay rate.
    
    This simulates the natural forgetting process in human memory.
    
    Args:
        decay_rate: Rate at which memories decay (0.0 to 1.0)
        
    Returns:
        int: Number of memories that were removed due to decay
        
    Raises:
        ValueError: If decay_rate is invalid
    """
    if not 0.0 <= decay_rate <= 1.0:
        raise ValueError("Decay rate must be between 0.0 and 1.0")
    
    current_time = datetime.now()
    removed_count = 0
    memories_to_remove = []
    
    try:
        # First pass: apply decay and identify memories to remove
        for memory_id, memory in _stm_store.items():
            # Skip already expired memories (they'll be cleaned up separately)
            if current_time > memory.expiry:
                continue
                
            # Calculate time-based decay
            time_since_access = (current_time - memory.last_accessed).total_seconds()
            time_factor = min(1.0, time_since_access / STM_DECAY_INTERVAL)
            
            # Apply decay to the decay_factor
            memory.decay_factor *= (1.0 - (decay_rate * time_factor))
            
            # If decay factor drops below threshold, mark for removal
            if memory.decay_factor < 0.1:  # 10% threshold for removal
                memories_to_remove.append(memory_id)
                
                # If memory is important enough, consolidate to LTM before removing
                if memory.priority >= STM_MIN_PRIORITY_FOR_LTM:
                    try:
                        consolidate_to_ltm(memory_id)
                    except Exception as e:
                        logger.warning(f"Failed to consolidate decayed memory {memory_id} to LTM: {str(e)}")
            else:
                # Update the memory with new decay factor
                _stm_store[memory_id] = memory
        
        # Second pass: remove identified memories
        for memory_id in memories_to_remove:
            delete_memory(memory_id)
            removed_count += 1
            
        logger.info(f"Applied decay (rate={decay_rate}): removed {removed_count} memories")
        return removed_count
        
    except Exception as e:
        logger.error(f"Error applying decay to STM entries: {str(e)}")
        raise STMStorageError(f"Failed to apply memory decay: {str(e)}") from e


def clear_expired() -> int:
    """
    Remove all expired memory entries.
    
    Returns:
        int: Number of expired memories that were removed
    """
    current_time = datetime.now()
    expired_ids = []
    
    try:
        # Identify expired memories
        for memory_id, memory in _stm_store.items():
            if current_time > memory.expiry:
                expired_ids.append(memory_id)
        
        # Remove expired memories
        for memory_id in expired_ids:
            delete_memory(memory_id)
            
        logger.info(f"Cleared {len(expired_ids)} expired STM entries")
        return len(expired_ids)
        
    except Exception as e:
        logger.error(f"Error clearing expired STM entries: {str(e)}")
        raise STMStorageError(f"Failed to clear expired memories: {str(e)}") from e


def consolidate_to_ltm(memory_id: str) -> bool:
    """
    Consolidate a short-term memory to long-term memory.
    
    This simulates the biological process of memory consolidation.
    
    Args:
        memory_id: The unique ID of the memory to consolidate
        
    Returns:
        bool: True if consolidation was successful
        
    Raises:
        STMEntryNotFoundError: If no memory with the given ID exists
    """
    try:
        # Retrieve the memory (this will raise STMEntryNotFoundError if not found)
        memory = retrieve_memory(memory_id, update_access=False)
        
        # Only consolidate memories that meet the priority threshold
        if memory.priority < STM_MIN_PRIORITY_FOR_LTM:
            logger.debug(f"Memory {memory_id} priority too low for LTM consolidation")
            return False
        
        # Prepare memory for LTM storage
        ltm_data = {
            "content": memory.content,
            "original_id": memory.id,
            "created_at": memory.created_at.isoformat(),
            "last_accessed": memory.last_accessed.isoformat(),
            "access_count": memory.access_count,
            "priority": memory.priority,
            "metadata": memory.metadata,
            "tags": memory.tags,
            "consolidated_at": datetime.now().isoformat()
        }
        
        # Store in LTM
        store_in_ltm(ltm_data)
        logger.info(f"Consolidated STM entry {memory_id} to LTM")
        return True
        
    except STMEntryNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to consolidate memory {memory_id} to LTM: {str(e)}")
        return False


def search_memories(
    query: str,
    tag_filter: Optional[list[str]] = None,
    min_priority: float = 0.0
) -> list[STMEntry]:
    """
    Search for memories matching the query string.
    
    Args:
        query: Search string to match against memory content
        tag_filter: If provided, only search memories with these tags
        min_priority: Minimum priority threshold for returned memories
        
    Returns:
        List[STMEntry]: List of memory entries matching the search criteria
    """
    query = query.lower()
    results = []
    
    try:
        # Get all memories that match the basic criteria
        candidates = get_all_memories(tag_filter, min_priority, include_expired=False)
        
        # Filter by query string
        for memory in candidates:
            if query in memory.content.lower():
                results.append(memory)
                
        logger.debug(f"Search for '{query}' returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error searching STM entries: {str(e)}")
        raise STMStorageError(f"Failed to search memories: {str(e)}") from e


def _make_room_for_new_entry(new_priority: float) -> None:
    """
    Make room for a new memory entry when at capacity.
    
    This function implements the forgetting strategy when STM is full.
    It will either:
    1. Remove the lowest priority item if the new item has higher priority
    2. Consolidate important memories to LTM before removing them
    3. Raise an exception if the new item has lower priority than all existing items
    
    Args:
        new_priority: The priority of the new memory to be added
        
    Raises:
        STMCapacityExceededError: If cannot make room for the new entry
    """
    # First, clear any expired memories
    cleared = clear_expired()
    if cleared > 0:
        # We made room by clearing expired memories
        return
    
    # Find the lowest priority memory
    lowest_priority = 1.1  # Start higher than max possible priority
    lowest_id = None
    
    for memory_id, memory in _stm_store.items():
        if memory.priority < lowest_priority:
            lowest_priority = memory.priority
            lowest_id = memory_id
    
    # If the new memory has higher priority than the lowest existing one
    if lowest_id is not None and new_priority > lowest_priority:
        # Try to consolidate to LTM if important enough
        if lowest_priority >= STM_MIN_PRIORITY_FOR_LTM:
            try:
                consolidate_to_ltm(lowest_id)
                logger.info(f"Consolidated memory {lowest_id} to LTM to make room")
            except Exception as e:
                logger.warning(f"Failed to consolidate memory {lowest_id} to LTM: {str(e)}")
        
        # Remove the lowest priority memory
        delete_memory(lowest_id)
        logger.info(f"Removed lowest priority memory {lowest_id} to make room")
    else:
        # The new memory has lower priority than all existing ones
        raise STMCapacityExceededError(
            f"STM at capacity ({STM_MAX_CAPACITY} items) and new memory priority "
            f"({new_priority}) is too low to replace existing memories"
        )


def get_memory_stats() -> dict[str, Any]:
    """
    Get statistics about the current state of short-term memory.
    
    Returns:
        Dict[str, Any]: Dictionary containing STM statistics
    """
    current_time = datetime.now()
    total_memories = len(_stm_store)
    expired_count = 0
    avg_priority = 0.0
    avg_age_seconds = 0.0
    tag_counts = {}
    
    if total_memories > 0:
        priorities_sum = 0.0
        age_sum = 0.0
        
        for memory in _stm_store.values():
            # Count expired memories
            if current_time > memory.expiry:
                expired_count += 1
                
            # Sum priorities
            priorities_sum += memory.priority
            
            # Sum ages
            age = (current_time - memory.created_at).total_seconds()
            age_sum += age
            
            # Count tags
            for tag in memory.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        avg_priority = priorities_sum / total_memories
        avg_age_seconds = age_sum / total_memories
    
    return {
        "total_memories": total_memories,
        "expired_count": expired_count,
        "active_count": total_memories - expired_count,
        "capacity": STM_MAX_CAPACITY,
        "utilization_percent": (total_memories / STM_MAX_CAPACITY) * 100 if STM_MAX_CAPACITY > 0 else 0,
        "avg_priority": avg_priority,
        "avg_age_seconds": avg_age_seconds,
        "tag_distribution": tag_counts
    }