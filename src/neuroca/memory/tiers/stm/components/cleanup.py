"""
STM Cleanup Management

This module provides the STMCleanup class which handles the cleanup
of expired memories in the Short-Term Memory (STM) tier.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from neuroca.memory.backends import BaseStorageBackend


logger = logging.getLogger(__name__)


class STMCleanup:
    """
    Manages the cleanup of expired memories in the STM tier.
    
    This class provides functionality for identifying and removing
    expired memories, which is a key aspect of STM's automatic decay.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the cleanup manager.
        
        Args:
            tier_name: The name of the tier (always "stm" for this class)
        """
        self._tier_name = tier_name
        self._backend = None
        self._expiry_manager = None
        self._delete_func = None  # Function to delete a memory
    
    def configure(
        self, 
        backend: BaseStorageBackend,
        expiry_manager: Any,
        delete_func: Callable[[str], Any]
    ) -> None:
        """
        Configure the cleanup manager.
        
        Args:
            backend: The storage backend to use
            expiry_manager: The expiry manager, used to get expired memory IDs
            delete_func: Function to call for deleting a memory
        """
        self._backend = backend
        self._expiry_manager = expiry_manager
        self._delete_func = delete_func
    
    async def perform_cleanup(self) -> int:
        """
        Perform cleanup by removing expired memories.
        
        Returns:
            Number of memories cleaned up
        """
        logger.debug("Performing STM cleanup")
        
        # Check if we have necessary components
        if not self._expiry_manager or not self._delete_func:
            logger.warning("Cannot perform cleanup: missing components")
            return 0
        
        # Get expired memories from expiry manager
        expired_memories = self._expiry_manager.get_expired_memory_ids()
        
        # Delete expired memories
        count = 0
        for memory_id in expired_memories:
            try:
                # Delete memory
                success = await self._delete_func(memory_id)
                if success:
                    count += 1
            except Exception as e:
                logger.error(f"Error deleting expired memory {memory_id}: {str(e)}")
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired memories from STM")
        
        return count
    
    async def get_expired_count(self) -> int:
        """
        Get the count of currently expired memories.
        
        Returns:
            Count of expired memories
        """
        if not self._expiry_manager:
            return 0
            
        expired_memories = self._expiry_manager.get_expired_memory_ids()
        return len(expired_memories)
    
    async def get_expiring_soon_count(self, seconds: int = 60) -> int:
        """
        Get the count of memories that will expire soon.
        
        Args:
            seconds: Number of seconds to consider as "soon"
            
        Returns:
            Count of memories expiring soon
        """
        if not self._backend:
            return 0
            
        # This would require querying all memories with expiry times and filtering
        # In a real implementation, this would be optimized with a database query
        # For now, we'll return 0 as a placeholder
        return 0
