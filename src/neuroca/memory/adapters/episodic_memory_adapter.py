"""
Episodic Memory Adapter

This module provides an adapter that implements the legacy EpisodicMemory
interface using the new memory system architecture. It delegates operations
to the Memory Manager and LTM tier.

This adapter is provided for backward compatibility during migration
and will be removed in a future version.
"""

import asyncio
import logging
import warnings
from typing import Any, Dict, List, Optional, Union

from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.exceptions import MemoryNotFoundError, TierOperationError


logger = logging.getLogger(__name__)


class EpisodicMemoryAdapter:
    """
    Adapter for legacy EpisodicMemory that uses the new LTM tier.
    
    This adapter implements the legacy interface but delegates to the new
    Memory Manager and LTM tier.
    
    DEPRECATED: Use MemoryManager directly instead.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the episodic memory adapter.
        
        Args:
            memory_manager: Memory manager instance
        """
        warnings.warn(
            "EpisodicMemoryAdapter is deprecated. Use MemoryManager directly.",
            DeprecationWarning,
            stacklevel=2
        )
        self._memory_manager = memory_manager
        self._ltm = memory_manager._ltm
    
    async def add_memory(
        self,
        content: Any,
        summary: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Add a memory to episodic memory.
        
        Args:
            content: Memory content
            summary: Optional summary
            importance: Importance score (0.0 to 1.0)
            metadata: Additional metadata
            tags: Tags for categorization
            **kwargs: Additional arguments
            
        Returns:
            Memory ID
            
        DEPRECATED: Use MemoryManager.add_memory() instead.
        """
        warnings.warn(
            "add_memory() is deprecated. Use MemoryManager.add_memory() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Add the "episodic" category
        tags = tags or []
        tags.append("episodic")
        
        # Store in LTM directly
        try:
            return await self._memory_manager.add_memory(
                content=content,
                summary=summary,
                importance=importance,
                metadata=metadata,
                tags=tags,
                initial_tier="ltm",
                **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to add episodic memory: {str(e)}")
            raise
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an episodic memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory data, or None if not found
            
        DEPRECATED: Use MemoryManager.retrieve_memory() instead.
        """
        warnings.warn(
            "get_memory() is deprecated. Use MemoryManager.retrieve_memory() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            return await self._memory_manager.retrieve_memory(
                memory_id=memory_id,
                tier="ltm"
            )
        except Exception as e:
            logger.error(f"Failed to get episodic memory {memory_id}: {str(e)}")
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[Any] = None,
        summary: Optional[str] = None,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an episodic memory.
        
        Args:
            memory_id: Memory ID
            content: New content (if None, keeps existing content)
            summary: New summary (if None, keeps existing summary)
            importance: New importance (if None, keeps existing importance)
            metadata: New metadata (if None, keeps existing metadata)
            tags: New tags (if None, keeps existing tags)
            
        Returns:
            bool: True if the update was successful
            
        DEPRECATED: Use MemoryManager.update_memory() instead.
        """
        warnings.warn(
            "update_memory() is deprecated. Use MemoryManager.update_memory() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Make sure to keep the "episodic" tag
        if tags is not None and "episodic" not in tags:
            tags.append("episodic")
        
        try:
            return await self._memory_manager.update_memory(
                memory_id=memory_id,
                content=content,
                summary=summary,
                importance=importance,
                metadata=metadata,
                tags=tags
            )
        except MemoryNotFoundError:
            logger.error(f"Episodic memory {memory_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to update episodic memory {memory_id}: {str(e)}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete an episodic memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            bool: True if the deletion was successful
            
        DEPRECATED: Use MemoryManager.delete_memory() instead.
        """
        warnings.warn(
            "delete_memory() is deprecated. Use MemoryManager.delete_memory() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            return await self._memory_manager.delete_memory(
                memory_id=memory_id,
                tier="ltm"
            )
        except Exception as e:
            logger.error(f"Failed to delete episodic memory {memory_id}: {str(e)}")
            return False
    
    async def search_memories(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search episodic memories.
        
        Args:
            query: Text query
            tags: Tags to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching memories
            
        DEPRECATED: Use MemoryManager.search_memories() instead.
        """
        warnings.warn(
            "search_memories() is deprecated. Use MemoryManager.search_memories() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Make sure to include the "episodic" tag
        search_tags = tags or []
        if "episodic" not in search_tags:
            search_tags.append("episodic")
        
        try:
            return await self._memory_manager.search_memories(
                query=query,
                tags=search_tags,
                limit=limit,
                tiers=["ltm"]
            )
        except Exception as e:
            logger.error(f"Failed to search episodic memories: {str(e)}")
            return []
    
    async def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all episodic memories.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of memories
            
        DEPRECATED: Use MemoryManager.search_memories() with "episodic" tag instead.
        """
        warnings.warn(
            "get_all_memories() is deprecated. Use MemoryManager.search_memories() with 'episodic' tag instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            return await self._memory_manager.search_memories(
                tags=["episodic"],
                limit=limit,
                tiers=["ltm"]
            )
        except Exception as e:
            logger.error(f"Failed to get all episodic memories: {str(e)}")
            return []
