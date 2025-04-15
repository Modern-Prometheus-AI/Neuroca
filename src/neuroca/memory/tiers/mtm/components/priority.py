"""
MTM Priority Management

This module provides the MTMPriority class which handles priority-based
memory management for the Medium-Term Memory (MTM) tier.
"""

import logging
import time
from typing import Any, Dict, Optional, List, Set

from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.exceptions import TierOperationError


logger = logging.getLogger(__name__)


class MTMPriority:
    """
    Manages priority-based memory management for MTM memories.
    
    This class provides methods for setting, getting, and managing priorities
    for MTM memories, which is a key feature of medium-term memory organization.
    """
    
    DEFAULT_PRIORITY_LEVELS = {"high": 3, "medium": 2, "low": 1}
    
    def __init__(self, tier_name: str):
        """
        Initialize the priority manager.
        
        Args:
            tier_name: The name of the tier (always "mtm" for this class)
        """
        self._tier_name = tier_name
        self._priority_levels = self.DEFAULT_PRIORITY_LEVELS.copy()
        self._lifecycle = None
        self._update_func = None  # Function to update a memory
    
    def configure(
        self, 
        lifecycle: Any, 
        update_func: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the priority manager.
        
        Args:
            lifecycle: The lifecycle manager, used to access/update priority map
            update_func: Function to call for updating a memory
            config: Configuration options
        """
        self._lifecycle = lifecycle
        self._update_func = update_func
        
        # Load custom priority levels if configured
        if "priority_levels" in config:
            self._priority_levels = config["priority_levels"]
    
    def process_pre_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item before storage to set priority.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Set default priority for the memory
        priority = "medium"  # Default priority
        
        # Check if a specific priority was provided in metadata
        if memory_item.metadata.tags and "priority" in memory_item.metadata.tags:
            provided_priority = memory_item.metadata.tags["priority"]
            if provided_priority in self._priority_levels:
                priority = provided_priority
            else:
                logger.warning(
                    f"Invalid priority provided in metadata: {provided_priority}, using default"
                )
        
        # Set priority and numeric value
        memory_item.metadata.tags["priority"] = priority
        memory_item.metadata.tags["priority_value"] = self._priority_levels[priority]
    
    def process_post_store(self, memory_item: MemoryItem) -> None:
        """
        Process a memory item after storage to update priority map.
        
        Args:
            memory_item: The stored memory item
        """
        # Update priority map
        if "priority" in memory_item.metadata.tags and self._lifecycle:
            self._lifecycle.update_priority(memory_item.id, memory_item.metadata.tags["priority"])
    
    def process_pre_delete(self, memory_id: str) -> None:
        """
        Process a memory before deletion to update priority map.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Remove from priority map
        if self._lifecycle:
            self._lifecycle.remove_priority(memory_id)
    
    def process_on_access(self, memory_item: MemoryItem, min_access_threshold: int) -> None:
        """
        Process a memory item when accessed to potentially update priority.
        
        Args:
            memory_item: The accessed memory item
            min_access_threshold: Minimum access count for priority upgrade
        """
        # Check if access count is high enough to consider upgrading priority
        if memory_item.metadata.access_count >= min_access_threshold:
            # If priority is not already high, consider upgrading
            current_priority = memory_item.metadata.tags.get("priority", "medium")
            if current_priority != "high":
                # Mark for potential promotion
                memory_item.metadata.tags["promote_to_ltm"] = True
                
                # For now, we'll keep priority as is
                # In a full implementation, we would consider upgrading based on:
                # - Access frequency
                # - Recent accesses
                # - Importance
                # - Memory tags/content
    
    async def set_priority(self, memory_id: str, priority: str) -> bool:
        """
        Set a priority for a MTM memory.
        
        Args:
            memory_id: The ID of the memory
            priority: Priority value ("high", "medium", or "low")
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ValueError: If priority is invalid
            TierOperationError: If the operation fails
        """
        # Validate priority
        if priority not in self._priority_levels:
            raise ValueError(
                f"Invalid priority: {priority}. "
                f"Valid values: {list(self._priority_levels.keys())}"
            )
        
        # Update memory metadata if update function is available
        if self._update_func:
            metadata = {
                "priority": priority,
                "priority_value": self._priority_levels[priority]
            }
            success = await self._update_func(memory_id, metadata=metadata)
            
            # Update priority map if successful
            if success and self._lifecycle:
                self._lifecycle.update_priority(memory_id, priority)
                
            return success
        else:
            # No update function available
            raise TierOperationError(
                operation="set_priority",
                tier_name=self._tier_name,
                message="Update function not configured"
            )
    
    def get_priority_levels(self) -> Dict[str, int]:
        """
        Get all priority levels and their values.
        
        Returns:
            Dictionary mapping priority names to numeric values
        """
        return self._priority_levels.copy()
    
    def get_memories_by_priority(self, priority: str) -> List[str]:
        """
        Get IDs of memories with a specific priority.
        
        Args:
            priority: Priority level to filter by
            
        Returns:
            List of memory IDs with the specified priority
        """
        if not self._lifecycle:
            return []
            
        priority_map = self._lifecycle.get_priority_map()
        
        # Filter for memories with the specified priority
        memory_ids = [
            memory_id 
            for memory_id, mem_priority in priority_map.items() 
            if mem_priority == priority
        ]
        
        return memory_ids
