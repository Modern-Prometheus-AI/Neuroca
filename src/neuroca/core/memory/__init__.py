"""
Memory systems for the NeuroCognitive Architecture.

This module implements the three-tiered memory system:
- Working Memory: Limited capacity, short-term storage with 7±2 chunks
- Episodic Memory: Event and experience storage with temporal context
- Semantic Memory: Long-term knowledge representation as a knowledge graph

It also includes memory operations:
- Memory Consolidation: Processes for moving information between memory tiers
- Memory Decay: Biologically-inspired forgetting mechanisms
- Memory Retrieval: Context-based information access
"""

# Import key components for easier access
from neuroca.core.memory.factory import create_memory_system
from neuroca.core.memory.interfaces import MemoryChunk, MemorySystem

__all__ = [
    'MemoryChunk',
    'MemorySystem',
    'create_memory_system',
] 