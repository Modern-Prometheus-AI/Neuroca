"""
Long-Term Memory (LTM) Tier Package

This package contains the implementation of the Long-Term Memory tier
for the Neuroca memory system. The LTM tier is responsible for storing
permanent memories with semantic relationships and long-term retention.

Key characteristics of LTM:
- Permanent storage with no automatic decay
- Semantic relationships between memories
- Vector embedding support for similarity search
- Categorization and organization of memories
- Focus on retrieval by meaning and context
"""

from neuroca.memory.tiers.ltm.core import LongTermMemoryTier

__all__ = [
    "LongTermMemoryTier",
]
