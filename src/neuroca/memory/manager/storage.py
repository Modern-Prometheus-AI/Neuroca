"""
Memory Manager Storage Operations

This module handles basic storage operations across all memory tiers,
including adding, retrieving, updating, and searching memories.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from neuroca.memory.backends import MemoryTier
from neuroca.memory.ltm.storage import MemoryItem, MemoryMetadata, MemoryStatus
from neuroca.memory.mtm.storage import MemoryPriority
from neuroca.memory.manager.utils import normalize_memory_format, calculate_text_relevance

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
) -> Optional[Dict[str, Any]]:
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
        Memory data as a dictionary
    """
    result = None
    
    try:
        # If tier is specified, only search that tier
        if tier == MemoryTier.STM:
            result = await stm_storage.retrieve(memory_id)
            if result:
                return normalize_memory_format(result, MemoryTier.STM)
        
        elif tier == MemoryTier.MTM:
            result = await mtm_storage.retrieve(memory_id)
            if result:
                return normalize_memory_format(result, MemoryTier.MTM)
        
        elif tier == MemoryTier.LTM:
            result = await ltm_storage.get(memory_id)
            if result:
                return normalize_memory_format(result, MemoryTier.LTM)
        
        else:
            # Search all tiers
            # Start with fastest tier (STM)
            result = await stm_storage.retrieve(memory_id)
            if result:
                return normalize_memory_format(result, MemoryTier.STM)
            
            # Try MTM
            result = await mtm_storage.retrieve(memory_id)
            if result:
                return normalize_memory_format(result, MemoryTier.MTM)
            
            # Try LTM
            result = await ltm_storage.get(memory_id)
            if result:
                return normalize_memory_format(result, MemoryTier.LTM)
            
            # Try vector storage as last resort
            result = await vector_storage.get(memory_id)
            if result:
                return normalize_memory_format(result, MemoryTier.LTM)
    
    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {str(e)}")
    
    return None


async def search_memories(
    stm_storage,
    mtm_storage,
    vector_storage,
    query: str,
    embedding: Optional[List[float]] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10,
    min_relevance: float = 0.0,
) -> List[Dict[str, Any]]:
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
    List of relevant memories as dictionaries
    """
    all_results = []
    
    # Search vector storage if embedding is provided (or if we can generate one)
    if embedding:
        try:
            vector_results = await vector_storage.search(
                query=query,
                query_embedding=embedding,
                limit=limit
            )
            
            for result in vector_results:
                normalized = normalize_memory_format(result, MemoryTier.LTM)
                normalized["relevance"] = 0.8  # Placeholder relevance
                all_results.append(normalized)
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
    
    # Search STM (simple text match for now)
    try:
        # Build filter criteria based on query and tags
        filter_criteria = {}
        if tags:
            filter_criteria["metadata.tags"] = {"$in": tags}
        
        stm_results = await stm_storage.retrieve(filter_criteria=filter_criteria, limit=limit)
        for result in stm_results:
            relevance = calculate_text_relevance(query, result)
            if relevance >= min_relevance:
                normalized = normalize_memory_format(result, MemoryTier.STM)
                normalized["relevance"] = relevance
                all_results.append(normalized)
    except Exception as e:
        logger.error(f"Error in STM search: {str(e)}")
    
    # Search MTM
    try:
        mtm_results = await mtm_storage.search(query=query, tags=tags)
        for result in mtm_results:
            relevance = calculate_text_relevance(query, result)
            if relevance >= min_relevance:
                normalized = normalize_memory_format(result, MemoryTier.MTM)
                normalized["relevance"] = relevance
                all_results.append(normalized)
    except Exception as e:
        logger.error(f"Error in MTM search: {str(e)}")
    
    # Sort by relevance and apply limit
    all_results.sort(key=lambda x: x.get("relevance", 0.0), reverse=True)
    return all_results[:limit]
