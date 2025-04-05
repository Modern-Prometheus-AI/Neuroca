"""
Memory consolidation functionality for the NCA system.

This module handles the process of memory consolidation, which moves information
from short-term memory to long-term memory with appropriate transformations.
"""

from datetime import datetime
from typing import Any


def consolidate_memory(memory_data: dict[str, Any], memory_type: str = "episodic") -> dict[str, Any]:
    """
    Consolidate a memory from short-term to long-term storage.
    
    Args:
        memory_data: The memory data to consolidate
        memory_type: Type of memory ('episodic' or 'semantic')
        
    Returns:
        The consolidated memory with additional metadata
    """
    # Add consolidation metadata
    consolidated = memory_data.copy()
    consolidated["consolidated_at"] = datetime.now().isoformat()
    consolidated["consolidation_version"] = "1.0"
    consolidated["memory_type"] = memory_type
    
    # In a real implementation, this would perform more complex transformations
    # such as extracting key information, linking related concepts, etc.
    
    return consolidated


def batch_consolidate_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Consolidate a batch of memories.
    
    Args:
        memories: List of memories to consolidate
        
    Returns:
        List of consolidated memories
    """
    return [consolidate_memory(memory) for memory in memories]


def extract_semantic_knowledge(episodic_memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extract semantic knowledge from a collection of episodic memories.
    
    Args:
        episodic_memories: List of episodic memories to analyze
        
    Returns:
        List of extracted semantic knowledge
    """
    # This is a stub implementation
    # In a real system, this would use more sophisticated NLP techniques
    semantic_knowledge = []
    
    # Group memories by themes or entities
    # For demonstration, we'll just create one semantic entry per episodic memory
    for i, memory in enumerate(episodic_memories):
        if i < 3:  # Limit for demonstration
            semantic_knowledge.append({
                "concept": f"Concept from memory {i}",
                "facts": {"source": f"Extracted from episodic memory {i}"},
                "confidence": 0.7,
                "source_memories": [memory.get("id", f"unknown_{i}")]
            })
    
    return semantic_knowledge


def prioritize_memories_for_consolidation(memories: list[dict[str, Any]], 
                                          limit: int = 10) -> list[dict[str, Any]]:
    """
    Prioritize memories for consolidation based on importance, recency, etc.
    
    Args:
        memories: List of memories to prioritize
        limit: Maximum number of memories to return
        
    Returns:
        Prioritized list of memories
    """
    # This is a simplified implementation - a real system would use more factors
    
    # Sort by importance and recency (using access count as a proxy)
    def priority_score(memory: dict[str, Any]) -> float:
        importance = memory.get("importance", 0.5)
        access_count = memory.get("access_count", 0)
        # Memories with high importance and low access count get higher priority
        return importance * (1.0 / (access_count + 1))
        
    sorted_memories = sorted(memories, key=priority_score, reverse=True)
    return sorted_memories[:limit] 