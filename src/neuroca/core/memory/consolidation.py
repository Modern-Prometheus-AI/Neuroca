"""
Memory Consolidation module for the NeuroCognitive Architecture.

This module implements the biological process of memory consolidation - transferring
information between memory systems with various transformations. Key processes include:

1. Working to Episodic: Preserving temporal context and emotional significance 
2. Episodic to Semantic: Abstracting repeated experiences into general knowledge
"""

import time

from neuroca.core.memory.factory import create_memory_system
from neuroca.core.memory.interfaces import MemoryConsolidator, MemorySystem


class StandardMemoryConsolidator(MemoryConsolidator):
    """
    Implements memory consolidation from working to episodic memory and from episodic to semantic memory.
    
    Consolidation is the biological process of moving important memories from short-term
    to long-term storage, with various transformations along the way.
    """
    
    def __init__(
        self,
        activation_threshold: float = 0.6,
        repetition_threshold: int = 3,
        emotional_threshold: float = 0.7
    ):
        """
        Initialize the memory consolidator.
        
        Args:
            activation_threshold: Minimum activation for a memory to be consolidated
            repetition_threshold: Number of repetitions before consolidation to semantic
            emotional_threshold: Emotional salience threshold for direct consolidation
        """
        self._activation_threshold = activation_threshold
        self._repetition_threshold = repetition_threshold
        self._emotional_threshold = emotional_threshold
        self._pattern_counter: dict[str, int] = {}  # Track repeated patterns for abstraction
    
    def consolidate(
        self,
        source: MemorySystem,
        target: MemorySystem,
        **parameters
    ) -> list[str]:
        """
        Consolidate memories from source system to target system.
        
        Args:
            source: Source memory system (e.g., working memory)
            target: Target memory system (e.g., episodic memory)
        
        Returns:
            List of IDs for the newly consolidated memories in the target system
        """
        # Get configuration from parameters or use defaults
        activation_threshold = parameters.get('activation_threshold', self._activation_threshold)
        emotional_threshold = parameters.get('emotional_threshold', self._emotional_threshold)
        
        # Get all memories from the source system
        all_chunks = source.dump()
        
        # Filter based on activation threshold
        consolidation_candidates = []
        for chunk_data in all_chunks:
            # High activation or high emotional salience can trigger consolidation
            if (chunk_data["activation"] >= activation_threshold or 
                chunk_data.get("metadata", {}).get("emotional_salience", 0) >= emotional_threshold):
                consolidation_candidates.append(chunk_data)
        
        # Skip if no candidates
        if not consolidation_candidates:
            return []
        
        # Perform the consolidation
        consolidated_ids = []
        
        # For each candidate, store in target memory
        for chunk_data in consolidation_candidates:
            # Extract content and relevant metadata
            content = chunk_data["content"]
            # Make a copy of metadata to avoid modifying the original dict
            metadata = chunk_data.get("metadata", {}).copy() 
            # Extract emotional_salience and remove it from metadata to avoid duplicate keyword arg
            emotional_salience = metadata.pop("emotional_salience", 0.5) 
            
            # For working to episodic: preserve temporal context
            if source.name in ["working_memory", "working", "stm"]:
                # Create temporal context
                temporal_context = {
                    "timestamp": time.time(),
                    "sequence_id": int(time.time() * 1000),  # Millisecond precision
                    "original_created": chunk_data["created_at"],
                }
                
                # Store in episodic memory
                target_id = target.store(
                    content=content,
                    emotional_salience=emotional_salience,
                    temporal_context=temporal_context,
                    **metadata
                )
                consolidated_ids.append(target_id)
                
                # Track patterns for potential abstraction
                content_hash = str(content)
                self._pattern_counter[content_hash] = self._pattern_counter.get(content_hash, 0) + 1
            
            # For episodic to semantic: abstract and generalize
            elif source.name in ["episodic_memory", "episodic", "mtm"]:
                if hasattr(target, "store_concept"):
                    # Only consolidate to semantic if seen multiple times
                    content_hash = str(content)
                    if self._pattern_counter.get(content_hash, 0) >= self._repetition_threshold:
                        # Add abstraction metadata if moving to semantic memory
                        abstraction_metadata = {
                            "abstracted_from": chunk_data["id"],
                            "confidence": min(1.0, 0.3 + (0.1 * self._pattern_counter[content_hash])),
                            "observed_count": self._pattern_counter[content_hash],
                        }
                        
                        # Store as a concept in semantic memory
                        target_id = target.store_concept(
                            concept=content,
                            confidence=abstraction_metadata["confidence"],
                            **{**metadata, **abstraction_metadata}
                        )
                        consolidated_ids.append(target_id)
                else:
                    # Fallback for target without store_concept
                    target_id = target.store(
                        content=content,
                        **metadata
                    )
                    consolidated_ids.append(target_id)
        
        return consolidated_ids
    
    def set_activation_threshold(self, threshold: float) -> None:
        """Update the activation threshold for consolidation."""
        self._activation_threshold = max(0.0, min(1.0, threshold))
    
    def set_emotional_threshold(self, threshold: float) -> None:
        """Update the emotional threshold for consolidation."""
        self._emotional_threshold = max(0.0, min(1.0, threshold))
    
    def set_repetition_threshold(self, threshold: int) -> None:
        """Update the repetition threshold for abstraction."""
        self._repetition_threshold = max(1, threshold)
    
    def clear_pattern_tracking(self) -> None:
        """Clear the tracked patterns."""
        self._pattern_counter.clear()


# Helper function to consolidate working memory to episodic memory
def consolidate_working_to_episodic(**parameters) -> list[str]:
    """Consolidate items from working memory to episodic memory."""
    working = create_memory_system("working")
    episodic = create_memory_system("episodic")
    consolidator = StandardMemoryConsolidator()
    return consolidator.consolidate(working, episodic, **parameters)


# Helper function to consolidate episodic memory to semantic memory
def consolidate_episodic_to_semantic(**parameters) -> list[str]:
    """Consolidate items from episodic memory to semantic memory."""
    episodic = create_memory_system("episodic")
    semantic = create_memory_system("semantic")
    consolidator = StandardMemoryConsolidator()
    return consolidator.consolidate(episodic, semantic, **parameters)


# Function to run a complete consolidation cycle (both steps)
def run_consolidation_cycle(**parameters) -> dict[str, list[str]]:
    """
    Run a complete consolidation cycle, similar to what might occur during sleep.
    
    This consolidates from working → episodic → semantic memory.
    
    Returns:
        Dictionary with keys 'working_to_episodic' and 'episodic_to_semantic'
        containing lists of IDs for the newly consolidated memories.
    """
    # First consolidate working to episodic
    working_to_episodic_ids = consolidate_working_to_episodic(**parameters)
    
    # Then consolidate episodic to semantic
    episodic_to_semantic_ids = consolidate_episodic_to_semantic(**parameters)
    
    return {
        'working_to_episodic': working_to_episodic_ids,
        'episodic_to_semantic': episodic_to_semantic_ids
    }
