"""
Medium-Term Memory (MTM) Tier Package

This package contains the implementation of the Medium-Term Memory tier
for the Neuroca memory system. The MTM tier is responsible for storing
memories with medium-term retention and priority-based management.

Key characteristics of MTM:
- Medium retention period (configurable, typically minutes to hours/days)
- Priority-based organization and management
- Balances access speed and storage capacity
- More selective retention based on importance and access frequency
"""

from neuroca.memory.tiers.mtm.core import MediumTermMemoryTier

__all__ = [
    "MediumTermMemoryTier",
]
