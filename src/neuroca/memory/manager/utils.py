"""
Memory Manager Utilities

This module provides utility functions for the memory manager,
including normalization, relevance calculation, and text truncation.
"""

from typing import Any, Dict

from neuroca.memory.backends import MemoryTier


def normalize_memory_format(
    memory: Any,
    tier: MemoryTier
) -> Dict[str, Any]:
    """
    Normalize memory data from different tiers into a consistent dictionary format.
    
    Args:
        memory: Memory object or dictionary
        tier: Memory tier
        
    Returns:
        Normalized memory dictionary
    """
    result = {
        "tier": tier.value,
    }
    
    # Handle different memory types
    if tier == MemoryTier.STM:
        # STM returns dictionaries
        if isinstance(memory, dict):
            result.update(memory)
            result["id"] = memory.get("id", "")
            return result
    
    elif tier == MemoryTier.MTM:
        # MTM returns MTMMemory objects
        if hasattr(memory, "id"):
            result["id"] = memory.id
        
        if hasattr(memory, "content"):
            result["content"] = memory.content
        
        if hasattr(memory, "created_at"):
            result["created_at"] = memory.created_at
        
        if hasattr(memory, "last_accessed"):
            result["last_accessed"] = memory.last_accessed
        
        if hasattr(memory, "access_count"):
            result["access_count"] = memory.access_count
        
        if hasattr(memory, "priority"):
            result["priority"] = memory.priority.value if hasattr(memory.priority, "value") else memory.priority
        
        if hasattr(memory, "status"):
            result["status"] = memory.status.value if hasattr(memory.status, "value") else memory.status
        
        if hasattr(memory, "tags"):
            result["tags"] = memory.tags
        
        if hasattr(memory, "metadata"):
            result["metadata"] = memory.metadata
            # Extract importance if available
            if isinstance(memory.metadata, dict) and "importance" in memory.metadata:
                result["importance"] = memory.metadata.get("importance", 0.5)
        
        return result
    
    elif tier == MemoryTier.LTM:
        # LTM returns MemoryItem objects
        if hasattr(memory, "id"):
            result["id"] = memory.id
        
        if hasattr(memory, "content"):
            result["content"] = memory.content
        
        if hasattr(memory, "summary"):
            result["summary"] = memory.summary
        
        if hasattr(memory, "embedding"):
            result["embedding"] = memory.embedding
        
        if hasattr(memory, "metadata"):
            # Handle both dictionary and MemoryMetadata object
            if hasattr(memory.metadata, "dict"):
                metadata_dict = memory.metadata.dict()
                result["metadata"] = metadata_dict
                
                # Extract key metadata fields
                result["status"] = metadata_dict.get("status")
                result["tags"] = metadata_dict.get("tags", [])
                result["importance"] = metadata_dict.get("importance", 0.5)
                result["created_at"] = metadata_dict.get("created_at")
            else:
                result["metadata"] = memory.metadata
                
                # Try to extract key fields
                if hasattr(memory.metadata, "status"):
                    result["status"] = memory.metadata.status.value if hasattr(memory.metadata.status, "value") else memory.metadata.status
                
                if hasattr(memory.metadata, "tags"):
                    result["tags"] = memory.metadata.tags
                
                if hasattr(memory.metadata, "importance"):
                    result["importance"] = memory.metadata.importance
                
                if hasattr(memory.metadata, "created_at"):
                    result["created_at"] = memory.metadata.created_at
        
        return result
    
    # Fallback - return as is with tier information
    return result


def calculate_text_relevance(query: str, memory: Any) -> float:
    """
    Calculate simple text relevance between a query and a memory.
    
    Args:
        query: Search query
        memory: Memory object or dictionary
        
    Returns:
        Relevance score (0.0 to 1.0)
    """
    # This is a simplified implementation
    # In a real system, you might use more sophisticated text matching
    
    if not query:
        return 0.0
    
    # Normalize query
    query = query.lower()
    query_words = set(query.split())
    
    # Get memory content
    memory_text = ""
    
    # Handle different memory types
    if isinstance(memory, dict):
        # Extract content from dictionary
        content = memory.get("content", "")
        if isinstance(content, dict):
            if "text" in content:
                memory_text = content["text"]
            else:
                memory_text = str(content)
        else:
            memory_text = str(content)
        
        # Also consider summary if available
        summary = memory.get("summary", "")
        if summary:
            memory_text += " " + summary
    
    elif hasattr(memory, "content"):
        # Extract content from object
        content = getattr(memory, "content", "")
        if isinstance(content, dict):
            if "text" in content:
                memory_text = content["text"]
            else:
                memory_text = str(content)
        else:
            memory_text = str(content)
        
        # Also consider summary if available
        if hasattr(memory, "summary") and getattr(memory, "summary"):
            memory_text += " " + getattr(memory, "summary")
    
    else:
        # Fallback to string representation
        memory_text = str(memory)
    
    # Normalize memory text
    memory_text = memory_text.lower()
    memory_words = set(memory_text.split())
    
    # Calculate word overlap
    if not memory_words:
        return 0.0
        
    common_words = query_words.intersection(memory_words)
    
    # Calculate Jaccard similarity
    if not query_words.union(memory_words):
        return 0.0
        
    jaccard = len(common_words) / len(query_words.union(memory_words))
    
    # Calculate relevance with a bias toward query term matches
    relevance = jaccard * 0.5
    
    # Boost score based on how many query terms are in memory
    query_coverage = len(common_words) / len(query_words) if query_words else 0
    relevance += query_coverage * 0.5
    
    return relevance


def truncate_text(text: str, max_tokens: int) -> str:
    """
    Truncate text to approximately the specified number of tokens.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        
    Returns:
        Truncated text
    """
    # This is a simplified implementation
    # In a real system, you might use a proper tokenizer
    
    # Estimate tokens as words
    words = text.split()
    
    if len(words) <= max_tokens:
        return text
    
    # Truncate with ellipsis
    return " ".join(words[:max_tokens]) + "..."
