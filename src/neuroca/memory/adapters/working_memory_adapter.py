"""
Working Memory Adapter

This module provides an adapter that implements the legacy WorkingMemory
interface using the new memory system architecture. It delegates operations
to the Memory Manager's context management and working memory buffer.

This adapter is provided for backward compatibility during migration
and will be removed in a future version.
"""

import asyncio
import logging
import warnings
from typing import Any, Dict, List, Optional, Union

from neuroca.memory.manager.memory_manager import MemoryManager
from neuroca.memory.exceptions import MemoryManagerOperationError


logger = logging.getLogger(__name__)


class WorkingMemoryAdapter:
    """
    Adapter for legacy WorkingMemory that uses the new Memory Manager.
    
    This adapter implements the legacy interface but delegates to the new
    Memory Manager's context management and working memory buffer.
    
    DEPRECATED: Use MemoryManager directly instead.
    """
    
    def __init__(self, memory_manager: MemoryManager, capacity: int = 10):
        """
        Initialize the working memory adapter.
        
        Args:
            memory_manager: Memory manager instance
            capacity: Maximum number of items in working memory
        """
        warnings.warn(
            "WorkingMemoryAdapter is deprecated. Use MemoryManager directly.",
            DeprecationWarning,
            stacklevel=2
        )
        self._memory_manager = memory_manager
        self._capacity = capacity
    
    async def update_context(
        self,
        context_data: Dict[str, Any],
        embedding: Optional[List[float]] = None,
    ) -> None:
        """
        Update the current context.
        
        Args:
            context_data: Dictionary with current context information
            embedding: Optional pre-computed embedding of the context
            
        DEPRECATED: Use MemoryManager.update_context() instead.
        """
        warnings.warn(
            "update_context() is deprecated. Use MemoryManager.update_context() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            await self._memory_manager.update_context(context_data, embedding)
        except Exception as e:
            logger.error(f"Failed to update context: {str(e)}")
            raise
    
    async def clear_context(self) -> None:
        """
        Clear the current context and working memory.
        
        DEPRECATED: Use MemoryManager.clear_context() instead.
        """
        warnings.warn(
            "clear_context() is deprecated. Use MemoryManager.clear_context() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            await self._memory_manager.clear_context()
        except Exception as e:
            logger.error(f"Failed to clear context: {str(e)}")
            raise
    
    async def get_prompt_context(
        self,
        max_items: int = 5,
        max_tokens_per_item: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get relevant memories for the current context.
        
        Args:
            max_items: Maximum number of items to include
            max_tokens_per_item: Maximum tokens per item
            
        Returns:
            List of relevant memories
            
        DEPRECATED: Use MemoryManager.get_prompt_context_memories() instead.
        """
        warnings.warn(
            "get_prompt_context() is deprecated. Use MemoryManager.get_prompt_context_memories() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            return await self._memory_manager.get_prompt_context_memories(
                max_memories=max_items,
                max_tokens_per_memory=max_tokens_per_item,
            )
        except Exception as e:
            logger.error(f"Failed to get prompt context: {str(e)}")
            return []
    
    async def add_item(
        self,
        memory_id: str,
        tier: str,
        relevance: float = 0.5,
    ) -> None:
        """
        Manually add an item to working memory.
        
        Args:
            memory_id: Memory ID
            tier: Tier where the memory is stored
            relevance: Relevance score (0.0 to 1.0)
            
        DEPRECATED: No direct equivalent in new system, use update_context() instead.
        """
        warnings.warn(
            "add_item() is deprecated. No direct equivalent in new system, use update_context() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            # Retrieve the memory
            memory_data = await self._memory_manager.retrieve_memory(
                memory_id=memory_id,
                tier=tier,
            )
            
            if memory_data:
                # Access internal working memory buffer
                # This is not recommended in production code
                item = {
                    "memory_id": memory_id,
                    "tier": tier,
                    "relevance": relevance,
                    "data": memory_data,
                }
                
                # Add to working memory buffer
                self._memory_manager._working_memory.add_item(item)
        except Exception as e:
            logger.error(f"Failed to add item to working memory: {str(e)}")
            raise
    
    async def remove_item(self, memory_id: str) -> None:
        """
        Remove an item from working memory.
        
        Args:
            memory_id: Memory ID
            
        DEPRECATED: No direct equivalent in new system, use update_context() instead.
        """
        warnings.warn(
            "remove_item() is deprecated. No direct equivalent in new system, use update_context() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            # Access internal working memory buffer
            # This is not recommended in production code
            self._memory_manager._working_memory.remove_item(memory_id)
        except Exception as e:
            logger.error(f"Failed to remove item from working memory: {str(e)}")
            raise
    
    async def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Get all items in working memory.
        
        Returns:
            List of working memory items
            
        DEPRECATED: No direct equivalent in new system, use get_prompt_context_memories() instead.
        """
        warnings.warn(
            "get_all_items() is deprecated. No direct equivalent in new system, use get_prompt_context_memories() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            # Access internal working memory buffer
            # This is not recommended in production code
            items = self._memory_manager._working_memory.get_all_items()
            
            # Convert to dictionary format
            return [item.data for item in items]
        except Exception as e:
            logger.error(f"Failed to get working memory items: {str(e)}")
            return []
    
    async def clear(self) -> None:
        """
        Clear working memory.
        
        DEPRECATED: Use MemoryManager.clear_context() instead.
        """
        warnings.warn(
            "clear() is deprecated. Use MemoryManager.clear_context() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        try:
            # Access internal working memory buffer
            # This is not recommended in production code
            self._memory_manager._working_memory.clear()
        except Exception as e:
            logger.error(f"Failed to clear working memory: {str(e)}")
            raise
    
    @property
    def capacity(self) -> int:
        """
        Get working memory capacity.
        
        Returns:
            Maximum number of items in working memory
            
        DEPRECATED: No direct equivalent in new system.
        """
        warnings.warn(
            "capacity property is deprecated. No direct equivalent in new system.",
            DeprecationWarning,
            stacklevel=2
        )
        
        return self._capacity
    
    @capacity.setter
    def capacity(self, value: int) -> None:
        """
        Set working memory capacity.
        
        Args:
            value: Maximum number of items in working memory
            
        DEPRECATED: No direct equivalent in new system.
        """
        warnings.warn(
            "capacity property is deprecated. No direct equivalent in new system.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self._capacity = value
        
        # Also update internal working memory buffer capacity
        try:
            # Access internal working memory buffer
            # This is not recommended in production code
            self._memory_manager._working_memory.capacity = value
        except Exception as e:
            logger.error(f"Failed to set working memory capacity: {str(e)}")
