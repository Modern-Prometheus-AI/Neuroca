"""
Short-Term Memory (STM) Tier Package

This package contains the implementation of the Short-Term Memory tier
for the Neuroca memory system. The STM tier is responsible for storing
temporary memories with automatic decay and expiration.

Key characteristics of STM:
- Short retention period (configurable, typically seconds to minutes)
- Automatic decay/expiration of memories
- High access speed
- Priority based on recency
"""

from neuroca.memory.tiers.stm.core import ShortTermMemoryTier

__all__ = [
    "ShortTermMemoryTier",
]
