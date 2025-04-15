"""
Memory Manager Storage Operations

This module handles basic storage operations across all memory tiers,
including adding, retrieving, updating, and searching memories.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple # Added Tuple import

from neuroca.memory.backends import MemoryTier
from neuroca.memory.models.memory_item import MemoryItem, MemoryMetadata, MemoryStatus
# Import SearchResults and MemorySearchOptions
from neuroca.memory.models.search import MemorySearchResults as SearchResults, MemorySearchOptions, MemorySearchResult # Added MemorySearchResult import
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
        # Create MemoryItem for STM storage
        memory_item = MemoryItem(
            content=content_dict,
            summary=summary,
            embedding=embedding,
            metadata=MemoryMetadata(
                status=MemoryStatus.ACTIVE,
                tags={tag: True for tag in tags_list}, # Convert list to dict
                importance=importance,
                created_at=datetime.now(),
                # Add any other relevant fields from metadata_dict if needed
                **{k: v for k, v in metadata_dict.items() if k not in ['importance', 'tags']}
            )
        )
        # Store in STM using the MemoryItem object
        memory_id = await stm_storage.store(memory_item)
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

        # Create MemoryItem for MTM storage
        memory_item = MemoryItem(
            content=content_dict,
            summary=summary,
            embedding=embedding,
            metadata=MemoryMetadata(
                status=MemoryStatus.ACTIVE,
                tags={tag: True for tag in tags_list}, # Convert list to dict
                importance=importance,
                created_at=datetime.now(),
                priority=mtm_priority, # Add priority for MTM
                **{k: v for k, v in metadata_dict.items() if k not in ['importance', 'tags']}
            )
        )
        # Store in MTM using the MemoryItem object
        memory_id = await mtm_storage.store(memory_item)
        logger.debug(f"Stored memory in MTM with ID: {memory_id}")

    elif initial_tier == MemoryTier.LTM:
        # Store in LTM
        memory_item = MemoryItem(
            content=content_dict,
            summary=summary,
            embedding=embedding,
            metadata=MemoryMetadata(
                status=MemoryStatus.ACTIVE,
                tags={tag: True for tag in tags_list}, # Corrected: Convert list to dict for LTM too
                importance=importance,
                created_at=datetime.now(),
                 **{k: v for k, v in metadata_dict.items() if k not in ['importance', 'tags']} # Added other metadata
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
    # The backend's retrieve method should return a validated MemoryItem or None
    memory_item: Optional[MemoryItem] = None
    try:
        if tier == MemoryTier.STM:
            memory_item = await stm_storage.retrieve(memory_id)
        elif tier == MemoryTier.MTM:
            memory_item = await mtm_storage.retrieve(memory_id)
        elif tier == MemoryTier.LTM:
            # Try standard LTM, then vector
            memory_item = await ltm_storage.retrieve(memory_id)
            if not memory_item:
                memory_item = await vector_storage.retrieve(memory_id)
        else:
            # Search all tiers
            memory_item = await stm_storage.retrieve(memory_id)
            if not memory_item:
                memory_item = await mtm_storage.retrieve(memory_id)
            if not memory_item:
                memory_item = await ltm_storage.retrieve(memory_id)
            if not memory_item:
                memory_item = await vector_storage.retrieve(memory_id)

    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {str(e)}")
        return None

    # Update last accessed time if found (assuming retrieve doesn't do this)
    # Note: This might be redundant if the backend's retrieve already updates it.
    # if memory_item:
    #     memory_item.mark_accessed()
    #     # Persist the access time update if necessary (depends on backend implementation)
    #     # Example: await appropriate_storage.update(memory_item.id, memory_item.model_dump())

    return memory_item


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
        SearchResults object containing MemorySearchResult objects and metadata
    """
    # Store tuples of (MemoryItem, MemoryTier)
    all_result_tuples: List[Tuple[MemoryItem, MemoryTier]] = []
    processed_ids = set() # To avoid duplicates

    # Search vector storage if embedding is provided (or if we can generate one)
    if embedding:
        try: # Ensure try is correctly indented
            # Assuming vector_storage.search returns a list of MemoryItems or dicts
            raw_vector_results = await vector_storage.search( # Correctly indented call
                query=query,
                query_embedding=embedding,
                limit=limit * 2 # Fetch more initially to allow for merging/filtering
            )

            # Process vector results
            for result_data in raw_vector_results: # Adjust iteration based on actual return type
                try: # Added inner try for validation
                    if isinstance(result_data, MemoryItem):
                        item = result_data
                    elif isinstance(result_data, dict):
                        # Ensure normalization happens before validation if needed
                        # Assuming vector search returns data compatible with MemoryItem directly or via normalization
                        item = MemoryItem.model_validate(normalize_memory_format(result_data, MemoryTier.LTM))
                    else:
                        continue # Skip unknown format

                    if item.id not in processed_ids:
                        # Calculate relevance if not provided by backend
                        relevance = getattr(item.metadata, 'relevance', calculate_text_relevance(query, item.model_dump()))
                        if relevance >= min_relevance:
                            item.metadata.relevance = relevance # Store relevance
                            # Append tuple (item, tier)
                            all_result_tuples.append((item, MemoryTier.LTM))
                            processed_ids.add(item.id)

                except Exception as val_err_vector: # Ensure except is aligned with inner try
                    logger.warning(f"Failed to validate vector search result: {val_err_vector}")

        except Exception as e: # Ensure except is aligned with outer try
            logger.error(f"Error in vector search: {str(e)}")

    # Search STM (simple text match for now) # Ensure this is correctly unindented
    try:
        # Build filter criteria based on query and tags
        filter_criteria = {}
        if tags:
            # Note: InMemorySearch text_search doesn't directly support complex filters like this.
            # Tag filtering will be applied manually after retrieval for InMemory.
            pass # filter_criteria["metadata.tags"] = {"$in": tags} # This won't work with text_search

        # Use text_search method on the search attribute (Corrected)
        stm_results_raw = await stm_storage.search.text_search(
            query=query,
            fields=["content.text", "summary"], # Specify fields for text search
            limit=limit * 2 # Fetch more to allow manual filtering
        )

        # Manually filter by tags if needed for InMemory
        stm_results_filtered = []
        if tags:
            for item_dict in stm_results_raw:
                # Check if tags match (assuming tags are stored as dict keys in metadata)
                item_tags = item_dict.get('metadata', {}).get('tags', {})
                if any(tag in item_tags for tag in tags):
                    stm_results_filtered.append(item_dict)
        else:
            stm_results_filtered = stm_results_raw

        for result_dict in stm_results_filtered:
            item_id = result_dict.get('_id') # InMemorySearch uses _id
            if item_id and item_id not in processed_ids:
                try:
                    # Normalize might not be needed if retrieve returns MemoryItem
                    # Assuming normalize handles the dict format from InMemorySearch
                    item = MemoryItem.model_validate(normalize_memory_format(result_dict, MemoryTier.STM))
                    relevance = calculate_text_relevance(query, item.model_dump())
                    if relevance >= min_relevance:
                        item.metadata.relevance = relevance
                        # Append tuple (item, tier)
                        all_result_tuples.append((item, MemoryTier.STM))
                        processed_ids.add(item.id)
                except Exception as val_err:
                    logger.warning(f"Failed to validate STM search result for ID {item_id}: {val_err}")
    except Exception as e:
         logger.error(f"Error in STM search: {str(e)}")

    # Search MTM
    try:
        # Use text_search method on the search attribute (Corrected)
        mtm_results_raw = await mtm_storage.search.text_search(
            query=query,
            fields=["content.text", "summary"], # Specify fields for text search
            limit=limit * 2 # Fetch more for manual filtering
        )

        # Manually filter by tags if needed for InMemory
        mtm_results_filtered = []
        if tags:
            for item_dict in mtm_results_raw:
                item_tags = item_dict.get('metadata', {}).get('tags', {})
                if any(tag in item_tags for tag in tags):
                    mtm_results_filtered.append(item_dict)
        else:
            mtm_results_filtered = mtm_results_raw

        for result_dict in mtm_results_filtered:
             item_id = result_dict.get('_id') # InMemorySearch uses _id
             if item_id and item_id not in processed_ids:
                 try:
                     # Assuming normalize handles the dict format from InMemorySearch
                     item = MemoryItem.model_validate(normalize_memory_format(result_dict, MemoryTier.MTM))
                     relevance = calculate_text_relevance(query, item.model_dump())
                     if relevance >= min_relevance:
                         item.metadata.relevance = relevance
                         # Append tuple (item, tier)
                         all_result_tuples.append((item, MemoryTier.MTM))
                         processed_ids.add(item.id)
                 except Exception as val_err:
                     logger.warning(f"Failed to validate MTM search result for ID {item_id}: {val_err}")
    except Exception as e:
         logger.error(f"Error in MTM search: {str(e)}")

    # Sort tuples by relevance stored in the MemoryItem's metadata
    all_result_tuples.sort(key=lambda item_tuple: getattr(item_tuple[0].metadata, 'relevance', 0.0), reverse=True)

    # Apply limit and construct MemorySearchResult objects
    final_results: List[MemorySearchResult] = []
    rank = 1
    for item, tier in all_result_tuples[:limit]:
        search_result = MemorySearchResult(
            memory=item,
            relevance=getattr(item.metadata, 'relevance', 0.0),
            tier=tier.value, # Use the stored tier value
            rank=rank
            # similarity/distance could be added here if available from vector search
        )
        final_results.append(search_result)
        rank += 1

    total_found_count = len(all_result_tuples) # Total unique items found before limit

    search_options = MemorySearchOptions(
        query=query,
        tags=tags,
        limit=limit,
        offset=0, # Offset was handled by slicing the sorted list
        min_relevance=min_relevance
    )

    # Construct the final SearchResults object
    return SearchResults(
        results=final_results, # Pass the list of MemorySearchResult objects
        total_count=total_found_count,
        options=search_options,
        query=query
        # Removed offset and limit as they are part of options
    )
