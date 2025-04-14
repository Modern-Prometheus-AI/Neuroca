"""
Memory Manager Models

This module defines the data models used by the memory manager.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List

from neuroca.memory.backends import MemoryTier


@dataclass(order=True)
class RankedMemory:
    """A memory with a relevance score for prioritization."""
    
    relevance_score: float
    memory_id: str = field(compare=False)
    memory_tier: MemoryTier = field(compare=False)
    memory_data: Any = field(compare=False)  # Either MemoryItem or dict, depending on tier
    summary: str = field(compare=False, default="")
    tags: List[str] = field(compare=False, default_factory=list)
    last_accessed: datetime = field(compare=False, default_factory=datetime.now)
    strength: float = field(compare=False, default=1.0)
    importance: float = field(compare=False, default=0.5)
