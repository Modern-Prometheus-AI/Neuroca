"""
Memory Tier Helper Classes

This module provides utility classes for the base memory tier implementation,
handling memory item creation and identifier generation.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from neuroca.memory.models.memory_item import MemoryItem, MemoryStatus


class MemoryIdGenerator:
    """
    Utility class for generating unique memory identifiers.
    
    This class provides methods for generating memory IDs based on
    different strategies.
    """
    
    @staticmethod
    def generate(content: Dict[str, Any], **kwargs) -> str:
        """
        Generate a unique ID for a memory.
        
        Args:
            content: Memory content
            **kwargs: Additional parameters for ID generation
            
        Returns:
            A unique ID string
        """
        # Default implementation uses UUID4
        return str(uuid.uuid4())


class MemoryItemCreator:
    """
    Utility class for creating memory items.
    
    This class provides methods for creating memory items with
    standardized metadata and formatting.
    """
    
    @staticmethod
    def create(
        memory_id: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> MemoryItem:
        """
        Create a memory item from content and metadata.
        
        Args:
            memory_id: The ID for the memory
            content: Memory content
            metadata: Optional metadata
            **kwargs: Additional parameters for memory creation
            
        Returns:
            A MemoryItem instance
        """
        # Create base memory item
        now = datetime.now()
        importance = kwargs.get("importance", 0.5)
        strength = kwargs.get("strength", 1.0)
        
        item = MemoryItem(
            id=memory_id,
            content={
                "data": content,
                "created_at": now,
                "updated_at": now,
            },
            metadata={
                "importance": importance,
                "strength": strength,
                "tags": metadata or {},
                "status": MemoryStatus.ACTIVE,
                "created_at": now,
                "updated_at": now,
                "access_count": 0,
            },
        )
        
        return item
