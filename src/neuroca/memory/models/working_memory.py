"""
Working Memory Models

This module defines data models for the working memory system,
which is responsible for maintaining a buffer of context-relevant memories
for prompt injection and immediate access.
"""

import heapq
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field, field_validator

from neuroca.memory.models.memory_item import MemoryItem


class WorkingMemoryItem(BaseModel):
    """
    A memory item in the working memory buffer.
    
    This model represents a memory item that is currently in the working
    memory buffer, with additional fields for relevance tracking and
    buffer management.
    """
    
    # The memory itself
    memory: MemoryItem
    
    # Working memory specific fields
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)  # Relevance to current context
    last_relevance_update: datetime = Field(default_factory=datetime.now)  # When relevance was last updated
    added_at: datetime = Field(default_factory=datetime.now)  # When the item was added to working memory
    
    # Context info
    context_id: Optional[str] = None  # ID of the context that triggered this memory
    context_relationship: Optional[str] = None  # Relationship to context (e.g., "semantic", "keyword")
    
    # Source info
    source_tier: str  # The tier this memory was retrieved from
    
    @field_validator("memory", mode="before")
    def validate_memory(cls, v):
        """Ensure memory is a MemoryItem object."""
        if isinstance(v, dict):
            return MemoryItem(**v)
        return v
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict() to handle custom fields."""
        result = super().dict(*args, **kwargs)
        
        # Convert MemoryItem to dict
        if "memory" in result and isinstance(result["memory"], MemoryItem):
            result["memory"] = result["memory"].dict()
        
        # Remove None values to save space
        return {k: v for k, v in result.items() if v is not None}
    
    @property
    def memory_id(self) -> str:
        """Get the ID of the memory item."""
        return self.memory.id
    
    @property
    def content(self) -> Dict[str, Any]:
        """Get the content of the memory item."""
        if isinstance(self.memory.content, dict):
            return self.memory.content
        return self.memory.content.dict()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata of the memory item."""
        if isinstance(self.memory.metadata, dict):
            return self.memory.metadata
        return self.memory.metadata.dict()
    
    @property
    def text(self) -> str:
        """Get the text of the memory item."""
        return self.memory.get_text()
    
    def update_relevance(self, new_relevance: float) -> None:
        """
        Update the relevance of this memory.
        
        Args:
            new_relevance: The new relevance score (0.0 to 1.0)
        """
        self.relevance = max(0.0, min(1.0, new_relevance))
        self.last_relevance_update = datetime.now()
    
    def format_for_prompt(
        self,
        max_tokens: int = 150,
        include_metadata: bool = False,
    ) -> Dict[str, Any]:
        """
        Format this memory for inclusion in a prompt.
        
        Args:
            max_tokens: Maximum number of tokens to include
            include_metadata: Whether to include metadata
            
        Returns:
            Formatted memory for prompt inclusion
        """
        # Start with the key information
        result = {
            "id": self.memory_id,
            "relevance": round(self.relevance, 2),
        }
        
        # Add the content
        text = self.text
        if len(text) > max_tokens:
            # Very crude truncation - in a real implementation, this
            # would use a proper tokenizer and truncate at token boundaries
            text = text[:max_tokens - 3] + "..."
        
        result["content"] = text
        
        # Add summary if available and different from content
        if self.memory.summary and self.memory.summary != text:
            summary = self.memory.summary
            if len(summary) > max_tokens // 2:
                summary = summary[:max_tokens // 2 - 3] + "..."
            result["summary"] = summary
        
        # Add metadata if requested
        if include_metadata:
            meta = self.metadata
            
            # Include only the most important metadata fields
            important_fields = ["importance", "tags", "created_at", "source"]
            result["metadata"] = {
                k: v for k, v in meta.items() 
                if k in important_fields and v is not None
            }
        
        return result


class WorkingMemoryBuffer(BaseModel):
    """
    Working memory buffer for the memory system.
    
    This model represents the working memory buffer, which maintains
    a set of context-relevant memories for prompt injection and
    immediate access.
    """
    
    # Buffer settings
    max_size: int = Field(default=100, ge=1)  # Maximum number of items in the buffer
    default_prompt_items: int = Field(default=5, ge=1)  # Default number of items for prompt injection
    
    # The buffer contents
    items: List[WorkingMemoryItem] = Field(default_factory=list)  # Items in the buffer
    item_ids: Set[str] = Field(default_factory=set)  # Set of memory IDs for fast lookup
    
    # Current context
    current_context: Dict[str, Any] = Field(default_factory=dict)  # Current context information
    context_updated_at: Optional[datetime] = None  # When the context was last updated
    
    class Config:
        arbitrary_types_allowed = True
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict() to handle custom fields."""
        result = super().dict(*args, **kwargs)
        
        # Convert items to dict
        if "items" in result:
            result["items"] = [
                item.dict() if hasattr(item, "dict") else item
                for item in result["items"]
            ]
        
        # Convert item_ids set to list
        if "item_ids" in result:
            result["item_ids"] = list(result["item_ids"])
        
        # Remove None values to save space
        return {k: v for k, v in result.items() if v is not None}
    
    def add_item(self, item: WorkingMemoryItem) -> bool:
        """
        Add an item to the buffer.
        
        Args:
            item: The item to add
            
        Returns:
            bool: True if the item was added, False if it was already in the buffer
        """
        memory_id = item.memory_id
        
        # Check if the item is already in the buffer
        if memory_id in self.item_ids:
            # Update the existing item's relevance
            for i, existing_item in enumerate(self.items):
                if existing_item.memory_id == memory_id:
                    existing_item.update_relevance(item.relevance)
                    return False
        
        # Add the new item
        self.items.append(item)
        self.item_ids.add(memory_id)
        
        # If the buffer is full, remove the least relevant item
        if len(self.items) > self.max_size:
            self._remove_least_relevant()
        
        return True
    
    def remove_item(self, memory_id: str) -> bool:
        """
        Remove an item from the buffer.
        
        Args:
            memory_id: The ID of the memory to remove
            
        Returns:
            bool: True if the item was removed, False if it wasn't in the buffer
        """
        if memory_id not in self.item_ids:
            return False
        
        # Remove the item
        self.items = [item for item in self.items if item.memory_id != memory_id]
        self.item_ids.remove(memory_id)
        
        return True
    
    def get_item(self, memory_id: str) -> Optional[WorkingMemoryItem]:
        """
        Get an item from the buffer.
        
        Args:
            memory_id: The ID of the memory to get
            
        Returns:
            The item if found, None otherwise
        """
        if memory_id not in self.item_ids:
            return None
        
        for item in self.items:
            if item.memory_id == memory_id:
                return item
        
        return None
    
    def clear(self) -> None:
        """Clear the buffer."""
        self.items = []
        self.item_ids = set()
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """
        Update the current context.
        
        Args:
            context: The new context information
        """
        self.current_context = context
        self.context_updated_at = datetime.now()
    
    def clear_context(self) -> None:
        """Clear the current context."""
        self.current_context = {}
        self.context_updated_at = None
    
    def get_top_items(
        self,
        max_items: Optional[int] = None,
        min_relevance: float = 0.0,
    ) -> List[WorkingMemoryItem]:
        """
        Get the most relevant items from the buffer.
        
        Args:
            max_items: Maximum number of items to return (defaults to default_prompt_items)
            min_relevance: Minimum relevance score (0.0 to 1.0)
            
        Returns:
            List of the most relevant items
        """
        if max_items is None:
            max_items = self.default_prompt_items
        
        # Filter by minimum relevance
        filtered = [item for item in self.items if item.relevance >= min_relevance]
        
        # Sort by relevance (highest first)
        sorted_items = sorted(filtered, key=lambda x: x.relevance, reverse=True)
        
        # Take the top items
        return sorted_items[:max_items]
    
    def get_items_for_prompt(
        self,
        max_items: Optional[int] = None,
        min_relevance: float = 0.0,
        max_tokens_per_item: int = 150,
        include_metadata: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get formatted items for prompt injection.
        
        Args:
            max_items: Maximum number of items to return
            min_relevance: Minimum relevance score (0.0 to 1.0)
            max_tokens_per_item: Maximum tokens per item
            include_metadata: Whether to include metadata
            
        Returns:
            List of formatted items for prompt injection
        """
        top_items = self.get_top_items(max_items, min_relevance)
        
        return [
            item.format_for_prompt(max_tokens_per_item, include_metadata)
            for item in top_items
        ]
    
    def _remove_least_relevant(self) -> None:
        """Remove the least relevant item from the buffer."""
        if not self.items:
            return
        
        # Find the least relevant item
        least_relevant = min(self.items, key=lambda x: x.relevance)
        
        # Remove it
        self.items.remove(least_relevant)
        self.item_ids.remove(least_relevant.memory_id)
