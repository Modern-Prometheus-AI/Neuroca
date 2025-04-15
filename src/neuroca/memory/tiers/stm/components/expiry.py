"""
STM Expiry Management

This module provides the STMExpiry class which handles expiry and
time-to-live (TTL) functionality for the Short-Term Memory (STM) tier.
"""

import logging
import time
from typing import Any, Dict, Optional

from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.exceptions import TierOperationError


logger = logging.getLogger(__name__)


class STMExpiry:
    """
    Manages expiry and time-to-live (TTL) functionality for STM memories.
    
    This class provides methods for setting, getting, and managing expiry
    times for STM memories, which is a key feature of short-term memory.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the expiry manager.
        
        Args:
            tier_name: The name of the tier (always "stm" for this class)
        """
        self._tier_name = tier_name
        self._default_ttl = 3600  # Default: 1 hour
        self._lifecycle = None
        self._update_func = None  # Function to update a memory
    
    def configure(
        self, 
        lifecycle: Any, 
        update_func: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the expiry manager.
        
        Args:
            lifecycle: The lifecycle manager, used to access/update expiry map
            update_func: Function to call for updating a memory
            config: Configuration options
        """
        self._lifecycle = lifecycle
        self._update_func = update_func
        self._default_ttl = config.get("ttl_seconds", 3600)
    
    def process_pre_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item before storage to set expiry time.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Set default TTL for the memory
        ttl = self._default_ttl
        
        # Check if a specific TTL was provided in metadata
        if memory_item.metadata.tags and "ttl_seconds" in memory_item.metadata.tags:
            try:
                ttl = int(memory_item.metadata.tags["ttl_seconds"])
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid TTL provided in metadata: {memory_item.metadata.tags['ttl_seconds']}, using default"
                )
        
        # Set expiry time
        expiry_time = time.time() + ttl
        memory_item.metadata.tags["expiry_time"] = expiry_time
    
    def process_post_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after storage to update expiry map.
        
        Args:
            memory_item: The stored memory item
        """
        # Update expiry map
        if "expiry_time" in memory_item.metadata.tags and self._lifecycle:
            self._lifecycle.update_expiry(memory_item.id, memory_item.metadata.tags["expiry_time"])
    
    def process_on_retrieve(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item when retrieved to check expiry.
        
        Args:
            memory_item: The retrieved memory item
        """
        # Check if memory has expired
        if "expiry_time" in memory_item.metadata.tags:
            expiry_time = memory_item.metadata.tags["expiry_time"]
            if time.time() > expiry_time:
                # Mark as expired
                from neuroca.memory.models.memory_item import MemoryStatus
                memory_item.metadata.status = MemoryStatus.EXPIRED
    
    def process_on_access(self, memory_item: MemoryItem, extend_ttl_on_access: bool) -> None:
        """
        Process a memory item when accessed to potentially extend expiry.
        
        Args:
            memory_item: The accessed memory item
            extend_ttl_on_access: Whether to extend TTL on access
        """
        # Optionally extend expiry time on access
        if extend_ttl_on_access:
            ttl = self._default_ttl
            
            # Get custom TTL if specified
            if "ttl_seconds" in memory_item.metadata.tags:
                try:
                    ttl = int(memory_item.metadata.tags["ttl_seconds"])
                except (ValueError, TypeError):
                    pass
            
            # Set new expiry time
            new_expiry = time.time() + ttl
            memory_item.metadata.tags["expiry_time"] = new_expiry
            
            # Update expiry map
            if self._lifecycle:
                self._lifecycle.update_expiry(memory_item.id, new_expiry)
    
    def process_pre_delete(self, memory_id: str) -> None:
        """
        Process a memory before deletion to update expiry map.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Remove from expiry map
        if self._lifecycle:
            self._lifecycle.remove_expiry(memory_id)
    
    async def set_expiry(self, memory_id: str, ttl_seconds: int) -> bool:
        """
        Set a time-to-live (TTL) for a STM memory.
        
        Args:
            memory_id: The ID of the memory
            ttl_seconds: TTL in seconds
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ValueError: If TTL is invalid
            TierOperationError: If the operation fails
        """
        # Validate TTL
        if ttl_seconds <= 0:
            raise ValueError("TTL must be greater than 0")
        
        # Calculate expiry time
        expiry_time = time.time() + ttl_seconds
        
        # Update memory metadata if update function is available
        if self._update_func:
            metadata = {
                "expiry_time": expiry_time,
                "ttl_seconds": ttl_seconds
            }
            success = await self._update_func(memory_id, metadata=metadata)
            
            # Update expiry map if successful
            if success and self._lifecycle:
                self._lifecycle.update_expiry(memory_id, expiry_time)
                
            return success
        else:
            # No update function available
            raise TierOperationError(
                operation="set_expiry",
                tier_name=self._tier_name,
                message="Update function not configured"
            )
    
    async def get_time_remaining(self, memory_item: MemoryItem) -> Optional[float]:
        """
        Get the time remaining before a memory expires.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Time remaining in seconds, or None if not set
        """
        # Get expiry time from memory item
        expiry_time = memory_item.metadata.tags.get("expiry_time")
        if expiry_time is None:
            return None
        
        # Calculate remaining time
        remaining = expiry_time - time.time()
        
        # If expired, return 0
        if remaining < 0:
            return 0.0
        
        return remaining
    
    def get_expired_memory_ids(self) -> Dict[str, float]:
        """
        Get IDs of expired memories from the expiry map.
        
        Returns:
            Dictionary mapping expired memory IDs to expiry timestamps
        """
        if not self._lifecycle:
            return {}
            
        current_time = time.time()
        expiry_map = self._lifecycle.get_expiry_map()
        
        # Filter for expired memories
        expired = {
            memory_id: expiry_time 
            for memory_id, expiry_time in expiry_map.items() 
            if current_time > expiry_time
        }
        
        return expired
