"""
Memory Tier Enumeration

This module defines the enumeration of memory tier types that the factory can create
backends for.
"""

from enum import Enum


class MemoryTier(str, Enum):
    """Memory tier types."""
    
    STM = "stm"  # Short-term memory
    MTM = "mtm"  # Medium-term memory
    LTM = "ltm"  # Long-term memory
