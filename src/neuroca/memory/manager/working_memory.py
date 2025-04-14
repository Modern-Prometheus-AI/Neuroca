"""
Memory Manager Working Memory

This module handles the working memory buffer, which maintains
a collection of context-relevant memories for immediate use.
It provides automatic retrieval, ranking, and selection of memories
based on the current context.
"""

import asyncio
import logging
from datetime import datetime
from heapq import heappush, heappop
from typing import Any, Dict, List, Optional, Set

from neuroca.memory.manager.models import RankedMemory
from neuroca.memory.manager.utils import calculate_text_relevance, truncate_text
from neuroca.memory.manager.decay import strengthen_memory

# Configure logger
logger = logging.getLogger(__name__)


async def update_working_memory(
    current_context: Dict[str, Any],
    context_embeddings: List[float],
    working_memory: List[RankedMemory],
    working_memory_ids: Set[str],
    working_buffer_size: int,
    search_memories_func,
    lock,
) -> None:
    """
    Update the working memory buffer based on current context.
    This retrieves relevant memories across all tiers.
    
    Args:
        current_context: Current context information
        context_embeddings: Embeddings of the current context
        working_memory: Working memory buffer
        working_memory_ids: Set of IDs in the working memory
        working_buffer_size: Maximum size of the working memory buffer
        search_memories_func: Function to search memories
        lock: Asyncio lock for the working memory
    """
    if not current_context:
        return  # No context to work with
    
    # Extract key elements from context for search
    query_text = ""
    if "input" in current_context:
        query_text += str(current_context["input"]) + " "
    if "goal" in current_context:
        query_text += str(current_context["goal"]) + " "
    if "focus" in current_context:
        query_text += str(current_context["focus"]) + " "
    
    query_text = query_text.strip()
    if not query_text:
        return  # No meaningful query can be constructed
    
    # Search using current context
    results = await search_memories_func(
        query=query_text,
        embedding=context_embeddings,
        limit=working_buffer_size * 2  # Get more than needed to ensure quality
    )
    
    # Convert to RankedMemory objects
    ranked_memories = []
    for result in results:
        # Skip if already in working memory
        if result.get("id") in working_memory_ids:
            continue
        
        memory = RankedMemory(
            relevance_score=result.get("relevance", 0.5),
            memory_id=result.get("id", ""),
            memory_tier=result.get("tier", None),
            memory_data=result,
            summary=result.get("summary", ""),
            tags=result.get("tags", []),
            importance=result.get("importance", 0.5),
            strength=result.get("strength", 1.0)
        )
        ranked_memories.append(memory)
    
    # Update the working memory buffer
    async with lock:
        # Add new memories to the buffer
        for memory in ranked_memories:
            if len(working_memory) < working_buffer_size or memory.relevance_score > working_memory[0].relevance_score:
                if memory.memory_id not in working_memory_ids:
                    if len(working_memory) >= working_buffer_size:
                        # Remove least relevant memory to make space
                        least_relevant = heappop(working_memory)
                        working_memory_ids.remove(least_relevant.memory_id)
                    
                    # Add the new memory
                    heappush(working_memory, memory)
                    working_memory_ids.add(memory.memory_id)
    
    logger.debug(f"Updated working memory with {len(ranked_memories)} new memories")


async def get_prompt_context_memories(
    working_memory: List[RankedMemory],
    working_memory_ids: Set[str],
    max_memories: int = 5,
    max_tokens_per_memory: int = 150,
    strengthen_memory_func=None,
    lock=None,
) -> List[Dict[str, Any]]:
    """
    Get the most relevant memories for injection into the agent's prompt.
    
    Args:
        working_memory: Working memory buffer
        working_memory_ids: Set of IDs in the working memory
        max_memories: Maximum number of memories to include
        max_tokens_per_memory: Maximum tokens per memory
        strengthen_memory_func: Function to strengthen a memory
        lock: Asyncio lock for the working memory
        
    Returns:
        List of formatted memory dictionaries
    """
    # Start with an empty list
    prompt_memories = []
    
    if lock:
        async with lock:
            # Create a copy of the heap to avoid modifying it
            working_copy = working_memory.copy()
            
            # Extract the top N memories by relevance
            top_memories = []
            while working_copy and len(top_memories) < max_memories:
                top_memories.append(heappop(working_copy))
    else:
        # Create a copy of the heap to avoid modifying it
        working_copy = working_memory.copy()
        
        # Extract the top N memories by relevance
        top_memories = []
        while working_copy and len(top_memories) < max_memories:
            top_memories.append(heappop(working_copy))
    
    # Format each memory for inclusion in the prompt
    for ranked_memory in top_memories:
        memory_data = ranked_memory.memory_data
        tier = ranked_memory.memory_tier
        
        # Format memory based on tier-specific considerations
        formatted_memory = {
            "id": ranked_memory.memory_id,
            "tier": tier.value if hasattr(tier, "value") else str(tier),
            "relevance": ranked_memory.relevance_score,
            "created_at": memory_data.get("created_at", ""),
            "last_accessed": memory_data.get("last_accessed", ""),
        }
        
        # Add content based on tier (different tiers might have different formats)
        if tier and hasattr(tier, "STM") and tier == tier.STM:
            content = memory_data.get("content", {})
            if isinstance(content, dict) and "text" in content:
                formatted_memory["content"] = truncate_text(content["text"], max_tokens_per_memory)
            else:
                formatted_memory["content"] = truncate_text(str(content), max_tokens_per_memory)
        
        elif tier and hasattr(tier, "MTM") and tier == tier.MTM:
            content = memory_data.get("content", {})
            if ranked_memory.summary:
                formatted_memory["content"] = truncate_text(ranked_memory.summary, max_tokens_per_memory)
            elif isinstance(content, dict) and "text" in content:
                formatted_memory["content"] = truncate_text(content["text"], max_tokens_per_memory)
            else:
                formatted_memory["content"] = truncate_text(str(content), max_tokens_per_memory)
        
        elif tier and hasattr(tier, "LTM") and tier == tier.LTM:
            # LTM should have a summary field
            if ranked_memory.summary:
                formatted_memory["content"] = truncate_text(ranked_memory.summary, max_tokens_per_memory)
            else:
                content = memory_data.get("content", {})
                if isinstance(content, dict) and "text" in content:
                    formatted_memory["content"] = truncate_text(content["text"], max_tokens_per_memory)
                else:
                    formatted_memory["content"] = truncate_text(str(content), max_tokens_per_memory)
        else:
            # Fallback if tier is not recognized
            content = memory_data.get("content", {})
            if isinstance(content, dict) and "text" in content:
                formatted_memory["content"] = truncate_text(content["text"], max_tokens_per_memory)
            else:
                formatted_memory["content"] = truncate_text(str(content), max_tokens_per_memory)
        
        # Add tags if available
        if ranked_memory.tags:
            formatted_memory["tags"] = ranked_memory.tags
        
        prompt_memories.append(formatted_memory)
        
        # Update memory strength since it's being used in a prompt
        if strengthen_memory_func:
            asyncio.create_task(strengthen_memory_func(
                ranked_memory.memory_id,
                ranked_memory.memory_tier,
                0.2  # Strengthen by a fixed amount for prompt use
            ))
    
    return prompt_memories
