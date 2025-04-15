"""
Memory Manager Storage Operations

This module handles basic storage operations across all memory tiers,
including adding, retrieving, updating, and searching memories.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from neuroca.memory.backends import MemoryTier
from neuroca.memory.models.memory_item import MemoryItem, MemoryMetadata, MemoryStatus
# Import SearchResults and MemorySearchOptions
from neuroca.memory.models.search import MemorySearchResults as SearchResults, MemorySearchOptions
from enum import Enum
from neuroca.memory.manager.utils import normalize_memory_format, calculate_text_relevance

class MemoryPriority(str, Enum):
    """Priority levels for MTM memories."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Configure logger
logger = logging.getLogger(__name__)


async def add_memory(
    stm_storage,
    mtm_storage,
    ltm_storage,
    vector_storage,
    content: Any,
    summary: Optional[str] = None,
    importance: float = 0.5,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    embedding: Optional[List[float]] = None,
    initial_tier: MemoryTier = MemoryTier.STM,
) -> str:
    """
    Add a new memory to the system. By default, memories start in STM
    and may be consolidated to MTM/LTM based on importance and access patterns.
    
    Args:
        stm_storage: STM storage backend
        mtm_storage: MTM storage backend
        ltm_storage: LTM storage backend
        vector_storage: Vector storage backend
        content: Memory content (can be text, dict, or structured data)
        summary: Optional summary of the content
        importance: Importance score (0.0 to 1.0)
        metadata: Additional metadata
        tags: Tags for categorization
        embedding: Optional pre-computed embedding vector
        initial_tier: Initial storage tier (defaults to STM)
        
    Returns:
        Memory ID
    """
    # Normalize content
    if isinstance(content, str):
        content_dict = {"text": content}
    elif isinstance(content, dict):
        content_dict = content
    else:
        content_dict = {"data": str(content)}
    
    # Prepare metadata
    metadata_dict = metadata or {}
    if importance is not None:
        metadata_dict["importance"] = importance
    
    tags_list = tags or []
    
    # Store in appropriate tier
    memory_id = None
    if initial_tier == MemoryTier.STM:
        # Store in STM
        memory_id = await stm_storage.store(
            content=content_dict,
            metadata=metadata_dict
        )
        logger.debug(f"Stored memory in STM with ID: {memory_id}")
        
    elif initial_tier == MemoryTier.MTM:
        # Store in MTM
        mtm_priority = MemoryPriority.MEDIUM
        if importance >= 0.8:
            mtm_priority = MemoryPriority.HIGH
        elif importance >= 0.5:
            mtm_priority = MemoryPriority.MEDIUM
        else:
            mtm_priority = MemoryPriority.LOW
            
        memory_id = await mtm_storage.store(
            content=content_dict,
            tags=tags_list,
            priority=mtm_priority,
            metadata=metadata_dict
        )
        logger.debug(f"Stored memory in MTM with ID: {memory_id}")
        
    elif initial_tier == MemoryTier.LTM:
        # Store in LTM
        memory_item = MemoryItem(
            content=content_dict,
            summary=summary,
            embedding=embedding,
            metadata=MemoryMetadata(
                status=MemoryStatus.ACTIVE,
                tags=tags_list,
                importance=importance,
                created_at=datetime.now(),
            )
        )
        
        memory_id = await ltm_storage.store(memory_item)
        logger.debug(f"Stored memory in LTM with ID: {memory_id}")
        
        # If embedding is provided, also store in vector storage
        if embedding:
            await vector_storage.store(memory_item)
            logger.debug(f"Stored memory in vector storage with ID: {memory_id}")
    
    return memory_id


async def retrieve_memory(
    stm_storage,
    mtm_storage,
    ltm_storage,
    vector_storage,
    memory_id: str,
        tier: Optional[MemoryTier] = None
) -> Optional[MemoryItem]: # Changed return type hint
    """
    Retrieve a specific memory by ID.
    
    Args:
        stm_storage: STM storage backend
        mtm_storage: MTM storage backend
        ltm_storage: LTM storage backend
        vector_storage: Vector storage backend
        memory_id: Memory ID
        tier: Optional tier to search in (searches all tiers if not specified)
    
    Returns:
        MemoryItem object if found, otherwise None
    """
    result_dict = None
    result_tier = None
    try:
        # If tier is specified, only search that tier
        if tier == MemoryTier.STM:
            result_dict = await stm_storage.retrieve(memory_id)
            if result_dict: result_tier = MemoryTier.STM
        
        elif tier == MemoryTier.MTM:
            result_dict = await mtm_storage.retrieve(memory_id)
            if result_dict: result_tier = MemoryTier.MTM
        
        elif tier == MemoryTier.LTM:
            # Try LTM standard storage first
            result_dict = await ltm_storage.retrieve(memory_id) # Assuming retrieve exists, might need get
            if result_dict:
                result_tier = MemoryTier.LTM
            else:
                # Try vector storage if not found in standard LTM
                # Assuming vector_storage.retrieve exists and returns dict or MemoryItem
                vector_result = await vector_storage.retrieve(memory_id)
                if vector_result:
                    # Ensure it's a dict before normalization
                    result_dict = vector_result if isinstance(vector_result, dict) else vector_result.model_dump()
                    result_tier = MemoryTier.LTM # Treat vector as part of LTM conceptually
        
        else:
            # Search all tiers if no specific tier is given
            # Start with fastest tier (STM)
            result_dict = await stm_storage.retrieve(memory_id)
            if result_dict:
                result_tier = MemoryTier.STM
            else:
                # Try MTM
                result_dict = await mtm_storage.retrieve(memory_id)
                if result_dict:
                    result_tier = MemoryTier.MTM
                else:
                    # Try LTM standard storage
                    result_dict = await ltm_storage.retrieve(memory_id) # Assuming retrieve exists
                    if result_dict:
                        result_tier = MemoryTier.LTM
                    else:
                         # Try vector storage as last resort
                        vector_result = await vector_storage.retrieve(memory_id)
                        if vector_result:
                            result_dict = vector_result if isinstance(vector_result, dict) else vector_result.model_dump()
                            result_tier = MemoryTier.LTM

    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {str(e)}")
        return None # Return None on error

    # If found, normalize and validate into MemoryItem
    if result_dict and result_tier:
        try:
            normalized_dict = normalize_memory_format(result_dict, result_tier)
            return MemoryItem.model_validate(normalized_dict)
        except Exception as val_err:
            logger.error(f"Failed to validate retrieved memory {memory_id} into MemoryItem: {val_err}")
            return None # Return None if validation fails

    return None # Return None if not found in any tier


async def search_memories(
    stm_storage,
    mtm_storage,
    vector_storage,
    query: str,
    embedding: Optional[List[float]] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10,
    min_relevance: float = 0.0,
) -> SearchResults: # Changed return type hint
    """
    Search for memories across all tiers.
    
    Args:
        stm_storage: STM storage backend
        mtm_storage: MTM storage backend
        vector_storage: Vector storage backend
        query: Text query
        embedding: Optional query embedding for vector search
        tags: Optional tags to filter by
        limit: Maximum number of results
        min_relevance: Minimum relevance score (0.0 to 1.0)
            
    Returns:
        SearchResults object containing MemoryItems and metadata
    """
    all_result_items: List[MemoryItem] = []
    processed_ids = set() # To avoid duplicates
    # Search vector storage if embedding is provided (or if we can generate one)
    if embedding:
        try:
            vector_results = await vector_storage.search(
                query=query,
                query_embedding=embedding,
                limit=limit
            )
            # Assuming vector_results is already a SearchResults object or similar
            # Need to adapt based on actual vector_storage.search return type
            # For now, assume it returns a list of dicts or MemoryItems
            raw_vector_results = await vector_storage.search(
                query=query,
                query_embedding=embedding,
                limit=limit * 2 # Fetch more initially to allow for merging/filtering
            )

            # Process vector results (assuming list of dicts/MemoryItems)
            for result_data in raw_vector_results: # Adjust iteration based on actual return type
                 if isinstance(result_data, MemoryItem):
                     item = result_data
                 elif isinstance(result_data, dict):
                     item = MemoryItem.model_validate(normalize_memory_format(result_data, MemoryTier.LTM))
                 else:
                     continue # Skip unknown format

                 if item.id not in processed_ids:
                     # Calculate relevance if not provided by backend
                     relevance = getattr(item, 'relevance', calculate_text_relevance(query, item.model_dump()))
                     if relevance >= min_relevance:
                         item.metadata.relevance = relevance # Store relevance if possible
                         all_result_items.append(item)
                         processed_ids.add(item.id)

        except Exception as e:
             logger.error(f"Error in vector search: {str(e)}")
    
    # Search STM (simple text match for now)
    try:
        # Build filter criteria based on query and tags
        filter_criteria = {}
        if tags:
            filter_criteria["metadata.tags"] = {"$in": tags}
        # Assuming stm_storage.search exists and returns list of dicts
        stm_results = await stm_storage.search(query=query, filters=filter_criteria, limit=limit * 2)
        for result_dict in stm_results:
            if result_dict and result_dict.get('id') not in processed_ids:
                 try:
                     item = MemoryItem.model_validate(normalize_memory_format(result_dict, MemoryTier.STM))
                     relevance = calculate_text_relevance(query, item.model_dump())
                     if relevance >= min_relevance:
                         item.metadata.relevance = relevance
                         all_result_items.append(item)
                         processed_ids.add(item.id)
                 except Exception as val_err:
                     logger.warning(f"Failed to validate STM search result: {val_err}")
    except Exception as e:
         logger.error(f"Error in STM search: {str(e)}")

    # Search MTM
    try:
        # Assuming mtm_storage.search exists and returns list of dicts
        mtm_results = await mtm_storage.search(query=query, filters={"tags": tags} if tags else None, limit=limit * 2)
        for result_dict in mtm_results:
             if result_dict and result_dict.get('id') not in processed_ids:
                 try:
                     item = MemoryItem.model_validate(normalize_memory_format(result_dict, MemoryTier.MTM))
                     relevance = calculate_text_relevance(query, item.model_dump())
                     if relevance >= min_relevance:
                         item.metadata.relevance = relevance
                         all_result_items.append(item)
                         processed_ids.add(item.id)
                 except Exception as val_err:
                     logger.warning(f"Failed to validate MTM search result: {val_err}")
    except Exception as e:
         logger.error(f"Error in MTM search: {str(e)}")

    # Sort by relevance (assuming relevance is stored in metadata)
    all_result_items.sort(key=lambda item: getattr(item.metadata, 'relevance', 0.0), reverse=True)

    # Apply limit and construct SearchResults object
    final_items = all_result_items[:limit]
    
    # Note: total_count might be inaccurate if limits were applied during backend searches
    # A more accurate count would require counting in each backend without limit first.
    # For now, use the count of unique items found before the final limit.
    total_found_count = len(all_result_items)
    
    # Create search options object for the results
    search_options = MemorySearchOptions(
        query=query,
        tags=tags,
        limit=limit,
        offset=0, # Using 0 as offset was handled by slicing
        min_relevance=min_relevance
    )

    return SearchResults(
        items=final_items,
        total_count=total_found_count, # This might not be the true total across all tiers
        options=search_options, # Add the required options field
        offset=0, # Offset was handled implicitly by slicing
        limit=limit,
        query=query
    )
