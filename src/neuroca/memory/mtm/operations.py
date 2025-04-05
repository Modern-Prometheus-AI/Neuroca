"""
Medium-Term Memory (MTM) Operations Module.

This module provides the core operations for managing medium-term memories in the
NeuroCognitive Architecture. It handles creation, retrieval, updating, and decay
of medium-term memories, implementing the biological-inspired memory dynamics.

The MTM layer serves as an intermediate storage between Working Memory (WM) and
Long-Term Memory (LTM), with memories that persist longer than WM but may eventually
decay or be consolidated to LTM based on importance, relevance, and usage patterns.

Usage:
    from neuroca.memory.mtm.operations import (
        store_memory, retrieve_memory, update_memory, 
        consolidate_to_ltm, decay_memories
    )
    
    # Store a new memory in MTM
    memory_id = store_memory(content="Important meeting details", 
                            metadata={"source": "meeting", "importance": 0.8})
    
    # Retrieve a memory
    memory = retrieve_memory(memory_id)
    
    # Update memory with new information
    update_memory(memory_id, content="Updated meeting details", 
                 metadata={"importance": 0.9})
                 
    # Trigger decay process for all MTM memories
    decay_memories()
"""

import datetime
import json
import logging
import uuid
from typing import Any, Optional

from neuroca.config import settings
from neuroca.core.exceptions import (
    InvalidMemoryDataError,
    MemoryNotFoundError,
    MemoryOperationError,
    MemoryStorageError,
)
from neuroca.db.connections import get_database_connection
from neuroca.memory.ltm.operations import store_ltm_memory
from neuroca.memory.models import MemoryItem, MemoryState
from neuroca.monitoring.metrics import track_memory_operation

# Configure logger
logger = logging.getLogger(__name__)

# Constants for MTM operations
DEFAULT_MEMORY_LIFESPAN = settings.MTM_DEFAULT_LIFESPAN  # Default lifespan in seconds
DEFAULT_DECAY_RATE = settings.MTM_DEFAULT_DECAY_RATE  # Default decay rate per cycle
CONSOLIDATION_THRESHOLD = settings.MTM_CONSOLIDATION_THRESHOLD  # Importance threshold for LTM consolidation
MAX_MTM_CAPACITY = settings.MTM_MAX_CAPACITY  # Maximum number of items in MTM


def store_memory(
    content: str,
    metadata: Optional[dict[str, Any]] = None,
    importance: float = 0.5,
    lifespan: Optional[int] = None,
    tags: Optional[list[str]] = None,
    linked_memories: Optional[list[str]] = None
) -> str:
    """
    Store a new memory in the Medium-Term Memory (MTM) system.
    
    Args:
        content: The main content of the memory to store
        metadata: Additional structured data associated with the memory
        importance: A value between 0 and 1 indicating the memory's importance
                   (affects decay rate and consolidation likelihood)
        lifespan: Custom lifespan in seconds (overrides default)
        tags: List of tags for categorizing and retrieving the memory
        linked_memories: List of memory IDs that are related to this memory
        
    Returns:
        str: The unique identifier (UUID) of the stored memory
        
    Raises:
        InvalidMemoryDataError: If the provided data is invalid
        MemoryStorageError: If there's an error storing the memory
    """
    try:
        # Input validation
        if not content or not isinstance(content, str):
            raise InvalidMemoryDataError("Memory content must be a non-empty string")
        
        if importance < 0 or importance > 1:
            raise InvalidMemoryDataError("Importance must be between 0 and 1")
            
        # Generate a unique ID for the memory
        memory_id = str(uuid.uuid4())
        
        # Set default values if not provided
        metadata = metadata or {}
        tags = tags or []
        linked_memories = linked_memories or []
        memory_lifespan = lifespan or DEFAULT_MEMORY_LIFESPAN
        
        # Calculate expiration time based on lifespan and importance
        # More important memories live longer
        adjusted_lifespan = memory_lifespan * (1 + importance)
        creation_time = datetime.datetime.utcnow()
        expiration_time = creation_time + datetime.timedelta(seconds=adjusted_lifespan)
        
        # Create memory object
        memory = MemoryItem(
            id=memory_id,
            content=content,
            metadata=metadata,
            importance=importance,
            state=MemoryState.ACTIVE,
            creation_time=creation_time,
            last_accessed=creation_time,
            expiration_time=expiration_time,
            access_count=0,
            tags=tags,
            linked_memories=linked_memories,
            decay_factor=DEFAULT_DECAY_RATE * (1 - importance * 0.5)  # Important memories decay slower
        )
        
        # Store memory in database
        db = get_database_connection()
        db.mtm_collection.insert_one(memory.to_dict())
        
        # Check if we're exceeding capacity and need to decay some memories
        current_count = db.mtm_collection.count_documents({"state": MemoryState.ACTIVE.value})
        if current_count > MAX_MTM_CAPACITY:
            logger.info(f"MTM capacity exceeded ({current_count}/{MAX_MTM_CAPACITY}). Triggering decay.")
            _decay_least_important_memories(MAX_MTM_CAPACITY * 0.2)  # Decay 20% of capacity
        
        # Track metrics
        track_memory_operation("mtm_store", 1, {"importance": importance})
        
        logger.debug(f"Stored new MTM memory with ID: {memory_id}, importance: {importance}")
        return memory_id
        
    except Exception as e:
        logger.error(f"Error storing MTM memory: {str(e)}", exc_info=True)
        if isinstance(e, (InvalidMemoryDataError, MemoryStorageError)):
            raise
        raise MemoryStorageError(f"Failed to store memory in MTM: {str(e)}") from e


def retrieve_memory(
    memory_id: str,
    update_access_stats: bool = True
) -> dict[str, Any]:
    """
    Retrieve a memory from Medium-Term Memory by its ID.
    
    Args:
        memory_id: The unique identifier of the memory to retrieve
        update_access_stats: Whether to update last_accessed time and access_count
        
    Returns:
        Dict[str, Any]: The memory data as a dictionary
        
    Raises:
        MemoryNotFoundError: If no memory with the given ID exists
        MemoryOperationError: If there's an error during retrieval
    """
    try:
        db = get_database_connection()
        memory = db.mtm_collection.find_one({"id": memory_id})
        
        if not memory:
            logger.warning(f"Memory with ID {memory_id} not found in MTM")
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found in MTM")
            
        # If memory is marked as decayed or consolidated, log but still return
        if memory.get("state") != MemoryState.ACTIVE.value:
            logger.info(f"Retrieved non-active memory {memory_id} with state: {memory.get('state')}")
        
        # Update access statistics if requested
        if update_access_stats:
            now = datetime.datetime.utcnow()
            
            # Convert string timestamps to datetime objects if needed
            if isinstance(memory.get("last_accessed"), str):
                last_accessed = datetime.datetime.fromisoformat(memory["last_accessed"].replace('Z', '+00:00'))
            else:
                last_accessed = memory.get("last_accessed")
                
            # Calculate time since last access
            time_since_access = (now - last_accessed).total_seconds() if last_accessed else 0
            
            # Update memory with new access information
            update_data = {
                "last_accessed": now,
                "access_count": memory.get("access_count", 0) + 1,
            }
            
            # Potentially extend expiration time based on access (memory reinforcement)
            if time_since_access > 0 and memory.get("state") == MemoryState.ACTIVE.value:
                importance = memory.get("importance", 0.5)
                extension_factor = min(1.0, importance * 0.5 + 0.1)  # More important memories get bigger extensions
                
                # Calculate new expiration time
                if isinstance(memory.get("expiration_time"), str):
                    expiration_time = datetime.datetime.fromisoformat(memory["expiration_time"].replace('Z', '+00:00'))
                else:
                    expiration_time = memory.get("expiration_time")
                    
                # Extend expiration time
                if expiration_time:
                    remaining_time = (expiration_time - now).total_seconds()
                    if remaining_time > 0:
                        extension = remaining_time * extension_factor
                        new_expiration = now + datetime.timedelta(seconds=remaining_time + extension)
                        update_data["expiration_time"] = new_expiration
            
            # Apply updates to the database
            db.mtm_collection.update_one(
                {"id": memory_id},
                {"$set": update_data}
            )
            
            # Update the returned memory with the new values
            memory.update(update_data)
            
            # Track metrics
            track_memory_operation("mtm_retrieve", 1, {"state": memory.get("state")})
            
        logger.debug(f"Retrieved MTM memory with ID: {memory_id}")
        return memory
        
    except Exception as e:
        if isinstance(e, MemoryNotFoundError):
            raise
        logger.error(f"Error retrieving MTM memory {memory_id}: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to retrieve memory from MTM: {str(e)}") from e


def update_memory(
    memory_id: str,
    content: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    importance: Optional[float] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None,
    add_linked_memories: Optional[list[str]] = None,
    remove_linked_memories: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Update an existing memory in Medium-Term Memory.
    
    Args:
        memory_id: The unique identifier of the memory to update
        content: New content to replace the existing content (if provided)
        metadata: Metadata to update (will be merged with existing metadata)
        importance: New importance value between 0 and 1
        add_tags: Tags to add to the memory
        remove_tags: Tags to remove from the memory
        add_linked_memories: Memory IDs to add as linked memories
        remove_linked_memories: Memory IDs to remove from linked memories
        
    Returns:
        Dict[str, Any]: The updated memory data
        
    Raises:
        MemoryNotFoundError: If no memory with the given ID exists
        InvalidMemoryDataError: If the provided update data is invalid
        MemoryOperationError: If there's an error during the update
    """
    try:
        # Input validation
        if importance is not None and (importance < 0 or importance > 1):
            raise InvalidMemoryDataError("Importance must be between 0 and 1")
            
        # Retrieve the current memory
        db = get_database_connection()
        memory = db.mtm_collection.find_one({"id": memory_id})
        
        if not memory:
            logger.warning(f"Cannot update memory {memory_id}: not found in MTM")
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found in MTM")
            
        # Check if memory is active
        if memory.get("state") != MemoryState.ACTIVE.value:
            logger.warning(f"Attempting to update non-active memory {memory_id} with state: {memory.get('state')}")
            
        # Prepare update data
        update_data = {}
        if content is not None:
            if not isinstance(content, str) or not content:
                raise InvalidMemoryDataError("Memory content must be a non-empty string")
            update_data["content"] = content
            
        # Update metadata (merge with existing)
        if metadata is not None:
            existing_metadata = memory.get("metadata", {})
            if isinstance(existing_metadata, str):
                try:
                    existing_metadata = json.loads(existing_metadata)
                except json.JSONDecodeError:
                    existing_metadata = {}
                    
            merged_metadata = {**existing_metadata, **metadata}
            update_data["metadata"] = merged_metadata
            
        # Update importance and adjust decay factor if needed
        if importance is not None:
            update_data["importance"] = importance
            update_data["decay_factor"] = DEFAULT_DECAY_RATE * (1 - importance * 0.5)
            
            # Adjust expiration time based on new importance
            now = datetime.datetime.utcnow()
            if isinstance(memory.get("expiration_time"), str):
                expiration_time = datetime.datetime.fromisoformat(memory["expiration_time"].replace('Z', '+00:00'))
            else:
                expiration_time = memory.get("expiration_time")
                
            if expiration_time:
                remaining_time = (expiration_time - now).total_seconds()
                if remaining_time > 0:
                    # Adjust remaining time based on importance change
                    old_importance = memory.get("importance", 0.5)
                    importance_factor = (1 + importance) / (1 + old_importance)
                    new_expiration = now + datetime.timedelta(seconds=remaining_time * importance_factor)
                    update_data["expiration_time"] = new_expiration
        
        # Handle tags updates
        if add_tags or remove_tags:
            current_tags = set(memory.get("tags", []))
            
            if add_tags:
                current_tags.update(add_tags)
                
            if remove_tags:
                current_tags = current_tags - set(remove_tags)
                
            update_data["tags"] = list(current_tags)
            
        # Handle linked memories updates
        if add_linked_memories or remove_linked_memories:
            current_linked = set(memory.get("linked_memories", []))
            
            if add_linked_memories:
                current_linked.update(add_linked_memories)
                
            if remove_linked_memories:
                current_linked = current_linked - set(remove_linked_memories)
                
            update_data["linked_memories"] = list(current_linked)
            
        # Record update time
        update_data["last_modified"] = datetime.datetime.utcnow()
        
        # Apply updates to the database
        if update_data:
            db.mtm_collection.update_one(
                {"id": memory_id},
                {"$set": update_data}
            )
            
            # Track metrics
            track_memory_operation("mtm_update", 1, {})
            
            # Get the updated memory
            updated_memory = db.mtm_collection.find_one({"id": memory_id})
            logger.debug(f"Updated MTM memory with ID: {memory_id}")
            return updated_memory
        else:
            logger.debug(f"No updates provided for MTM memory {memory_id}")
            return memory
            
    except Exception as e:
        if isinstance(e, (MemoryNotFoundError, InvalidMemoryDataError)):
            raise
        logger.error(f"Error updating MTM memory {memory_id}: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to update memory in MTM: {str(e)}") from e


def search_memories(
    query: Optional[str] = None,
    metadata_filters: Optional[dict[str, Any]] = None,
    tags: Optional[list[str]] = None,
    importance_min: float = 0.0,
    importance_max: float = 1.0,
    include_decayed: bool = False,
    limit: int = 10,
    offset: int = 0
) -> list[dict[str, Any]]:
    """
    Search for memories in Medium-Term Memory based on various criteria.
    
    Args:
        query: Text query to search in memory content
        metadata_filters: Filters to apply on metadata fields
        tags: List of tags to filter by (memories must have at least one)
        importance_min: Minimum importance value (inclusive)
        importance_max: Maximum importance value (inclusive)
        include_decayed: Whether to include memories in DECAYED state
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        
    Returns:
        List[Dict[str, Any]]: List of matching memories
        
    Raises:
        InvalidMemoryDataError: If the search parameters are invalid
        MemoryOperationError: If there's an error during the search
    """
    try:
        # Input validation
        if importance_min < 0 or importance_min > 1:
            raise InvalidMemoryDataError("importance_min must be between 0 and 1")
        if importance_max < 0 or importance_max > 1:
            raise InvalidMemoryDataError("importance_max must be between 0 and 1")
        if importance_min > importance_max:
            raise InvalidMemoryDataError("importance_min cannot be greater than importance_max")
            
        # Build the search filter
        search_filter = {
            "importance": {"$gte": importance_min, "$lte": importance_max}
        }
        
        # Add state filter
        if include_decayed:
            search_filter["state"] = {"$in": [MemoryState.ACTIVE.value, MemoryState.DECAYED.value]}
        else:
            search_filter["state"] = MemoryState.ACTIVE.value
            
        # Add text search if query provided
        if query:
            search_filter["$text"] = {"$search": query}
            
        # Add metadata filters
        if metadata_filters:
            for key, value in metadata_filters.items():
                search_filter[f"metadata.{key}"] = value
                
        # Add tags filter
        if tags:
            search_filter["tags"] = {"$in": tags}
            
        # Execute search
        db = get_database_connection()
        cursor = db.mtm_collection.find(search_filter).sort("importance", -1).skip(offset).limit(limit)
        results = list(cursor)
        
        # Track metrics
        track_memory_operation("mtm_search", 1, {"results_count": len(results)})
        
        logger.debug(f"MTM search returned {len(results)} results")
        return results
        
    except Exception as e:
        if isinstance(e, InvalidMemoryDataError):
            raise
        logger.error(f"Error searching MTM memories: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to search memories in MTM: {str(e)}") from e


def decay_memories(decay_cycle_id: Optional[str] = None) -> tuple[int, int]:
    """
    Process memory decay for all active memories in MTM.
    
    This function applies the decay algorithm to all active memories,
    potentially marking some as DECAYED if they've expired or reached
    decay threshold.
    
    Args:
        decay_cycle_id: Optional identifier for the decay cycle (for tracking)
        
    Returns:
        Tuple[int, int]: (number of memories processed, number of memories decayed)
        
    Raises:
        MemoryOperationError: If there's an error during the decay process
    """
    try:
        cycle_id = decay_cycle_id or str(uuid.uuid4())
        logger.info(f"Starting MTM decay cycle {cycle_id}")
        
        db = get_database_connection()
        now = datetime.datetime.utcnow()
        
        # Find all active memories
        active_memories = list(db.mtm_collection.find({"state": MemoryState.ACTIVE.value}))
        
        decayed_count = 0
        consolidated_count = 0
        
        for memory in active_memories:
            memory_id = memory.get("id")
            
            # Check if memory has expired
            if isinstance(memory.get("expiration_time"), str):
                expiration_time = datetime.datetime.fromisoformat(memory["expiration_time"].replace('Z', '+00:00'))
            else:
                expiration_time = memory.get("expiration_time")
                
            # Process expired memories
            if expiration_time and now > expiration_time:
                importance = memory.get("importance", 0)
                
                # Decide whether to consolidate to LTM or decay
                if importance >= CONSOLIDATION_THRESHOLD:
                    # Consolidate to LTM
                    try:
                        ltm_id = _consolidate_memory_to_ltm(memory)
                        db.mtm_collection.update_one(
                            {"id": memory_id},
                            {
                                "$set": {
                                    "state": MemoryState.CONSOLIDATED.value,
                                    "ltm_reference": ltm_id,
                                    "consolidation_time": now
                                }
                            }
                        )
                        consolidated_count += 1
                        logger.debug(f"Consolidated MTM memory {memory_id} to LTM as {ltm_id}")
                    except Exception as e:
                        logger.error(f"Failed to consolidate memory {memory_id} to LTM: {str(e)}", exc_info=True)
                else:
                    # Decay the memory
                    db.mtm_collection.update_one(
                        {"id": memory_id},
                        {
                            "$set": {
                                "state": MemoryState.DECAYED.value,
                                "decay_time": now
                            }
                        }
                    )
                    decayed_count += 1
                    logger.debug(f"Decayed MTM memory {memory_id} due to expiration")
        
        # Track metrics
        track_memory_operation("mtm_decay_cycle", 1, {
            "processed": len(active_memories),
            "decayed": decayed_count,
            "consolidated": consolidated_count
        })
        
        logger.info(f"Completed MTM decay cycle {cycle_id}: processed {len(active_memories)}, "
                   f"decayed {decayed_count}, consolidated {consolidated_count}")
        
        return len(active_memories), decayed_count
        
    except Exception as e:
        logger.error(f"Error during MTM decay cycle: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to process memory decay in MTM: {str(e)}") from e


def consolidate_to_ltm(memory_id: str, force: bool = False) -> str:
    """
    Explicitly consolidate a memory from MTM to LTM.
    
    Args:
        memory_id: The ID of the memory to consolidate
        force: Whether to force consolidation regardless of importance
        
    Returns:
        str: The ID of the newly created LTM memory
        
    Raises:
        MemoryNotFoundError: If the memory doesn't exist
        MemoryOperationError: If consolidation fails
    """
    try:
        db = get_database_connection()
        memory = db.mtm_collection.find_one({"id": memory_id})
        
        if not memory:
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found in MTM")
            
        # Check if already consolidated
        if memory.get("state") == MemoryState.CONSOLIDATED.value:
            logger.info(f"Memory {memory_id} already consolidated to LTM as {memory.get('ltm_reference')}")
            return memory.get("ltm_reference")
            
        # Check importance threshold unless forced
        if not force and memory.get("importance", 0) < CONSOLIDATION_THRESHOLD:
            logger.warning(f"Memory {memory_id} importance ({memory.get('importance')}) "
                          f"below threshold ({CONSOLIDATION_THRESHOLD}) for consolidation")
            raise MemoryOperationError(
                f"Memory importance ({memory.get('importance')}) below consolidation threshold "
                f"({CONSOLIDATION_THRESHOLD}). Use force=True to override."
            )
            
        # Perform consolidation
        ltm_id = _consolidate_memory_to_ltm(memory)
        
        # Update MTM memory state
        now = datetime.datetime.utcnow()
        db.mtm_collection.update_one(
            {"id": memory_id},
            {
                "$set": {
                    "state": MemoryState.CONSOLIDATED.value,
                    "ltm_reference": ltm_id,
                    "consolidation_time": now
                }
            }
        )
        
        # Track metrics
        track_memory_operation("mtm_explicit_consolidation", 1, {"forced": force})
        
        logger.info(f"Explicitly consolidated MTM memory {memory_id} to LTM as {ltm_id}")
        return ltm_id
        
    except Exception as e:
        if isinstance(e, (MemoryNotFoundError, MemoryOperationError)):
            raise
        logger.error(f"Error consolidating MTM memory {memory_id} to LTM: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to consolidate memory to LTM: {str(e)}") from e


def delete_memory(memory_id: str) -> bool:
    """
    Delete a memory from Medium-Term Memory.
    
    Args:
        memory_id: The ID of the memory to delete
        
    Returns:
        bool: True if the memory was deleted, False if it wasn't found
        
    Raises:
        MemoryOperationError: If there's an error during deletion
    """
    try:
        db = get_database_connection()
        result = db.mtm_collection.delete_one({"id": memory_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted MTM memory with ID: {memory_id}")
            track_memory_operation("mtm_delete", 1, {})
            return True
        else:
            logger.warning(f"Attempted to delete non-existent MTM memory: {memory_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting MTM memory {memory_id}: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to delete memory from MTM: {str(e)}") from e


def clear_all_memories(confirm: bool = False) -> int:
    """
    Clear all memories from Medium-Term Memory.
    
    CAUTION: This is a destructive operation that will remove all MTM memories.
    
    Args:
        confirm: Must be set to True to confirm the operation
        
    Returns:
        int: Number of memories deleted
        
    Raises:
        MemoryOperationError: If confirmation is not provided or there's an error
    """
    if not confirm:
        raise MemoryOperationError("Must set confirm=True to clear all MTM memories")
        
    try:
        db = get_database_connection()
        result = db.mtm_collection.delete_many({})
        deleted_count = result.deleted_count
        
        logger.warning(f"Cleared all MTM memories: {deleted_count} memories deleted")
        track_memory_operation("mtm_clear_all", 1, {"count": deleted_count})
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error clearing all MTM memories: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to clear all memories from MTM: {str(e)}") from e


# Helper functions

def _consolidate_memory_to_ltm(memory: dict[str, Any]) -> str:
    """
    Helper function to consolidate a memory to LTM.
    
    Args:
        memory: The memory object to consolidate
        
    Returns:
        str: The ID of the newly created LTM memory
        
    Raises:
        MemoryOperationError: If consolidation fails
    """
    try:
        # Prepare memory for LTM storage
        ltm_data = {
            "content": memory.get("content"),
            "metadata": memory.get("metadata", {}),
            "importance": memory.get("importance", 0.5),
            "source_memory_id": memory.get("id"),
            "source_memory_type": "mtm",
            "tags": memory.get("tags", []),
            "linked_memories": memory.get("linked_memories", []),
            "creation_time": memory.get("creation_time"),
            "mtm_access_count": memory.get("access_count", 0)
        }
        
        # Store in LTM
        ltm_id = store_ltm_memory(**ltm_data)
        return ltm_id
        
    except Exception as e:
        logger.error(f"Error in _consolidate_memory_to_ltm: {str(e)}", exc_info=True)
        raise MemoryOperationError(f"Failed to consolidate memory to LTM: {str(e)}") from e


def _decay_least_important_memories(count: int) -> int:
    """
    Decay the least important memories to free up space in MTM.
    
    Args:
        count: Number of memories to decay
        
    Returns:
        int: Number of memories actually decayed
    """
    try:
        db = get_database_connection()
        now = datetime.datetime.utcnow()
        
        # Find the least important active memories
        memories_to_decay = list(
            db.mtm_collection.find(
                {"state": MemoryState.ACTIVE.value}
            ).sort([
                ("importance", 1),  # Sort by importance ascending
                ("last_accessed", 1)  # Then by last accessed time
            ]).limit(int(count))
        )
        
        if not memories_to_decay:
            return 0
            
        # Decay these memories
        memory_ids = [m.get("id") for m in memories_to_decay]
        db.mtm_collection.update_many(
            {"id": {"$in": memory_ids}},
            {
                "$set": {
                    "state": MemoryState.DECAYED.value,
                    "decay_time": now,
                    "decay_reason": "capacity_management"
                }
            }
        )
        
        logger.info(f"Decayed {len(memory_ids)} least important memories to manage MTM capacity")
        return len(memory_ids)
        
    except Exception as e:
        logger.error(f"Error in _decay_least_important_memories: {str(e)}", exc_info=True)
        return 0