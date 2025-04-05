"""
Lymphatic Memory Subsystem for NeuroCognitive Architecture (NCA)

This module implements the lymphatic memory tier of the NCA's three-tiered memory system.
The lymphatic memory serves as an intermediate memory system between working memory and
long-term storage, responsible for memory consolidation, filtering, and prioritization.

Similar to the biological lymphatic system that filters and processes waste from tissues,
the lymphatic memory subsystem processes and filters information from working memory,
determining what should be retained in long-term storage and what can be discarded.

Key responsibilities:
- Memory consolidation from working memory
- Information filtering based on relevance and importance
- Prioritization of memories for long-term storage
- Temporary storage of intermediate-term memories
- Cleanup of obsolete or low-priority information

Usage:
    from neuroca.memory.lymphatic import LymphaticMemory
    
    # Initialize the lymphatic memory system
    lymphatic_mem = LymphaticMemory(config=config)
    
    # Store information in lymphatic memory
    lymphatic_mem.store(memory_item)
    
    # Retrieve information from lymphatic memory
    result = lymphatic_mem.retrieve(query)
    
    # Consolidate memories to long-term storage
    lymphatic_mem.consolidate()
    
    # Clean up obsolete memories
    lymphatic_mem.cleanup()
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional, Union

from neuroca.config import LymphaticMemoryConfig
from neuroca.core.exceptions import (
    InvalidMemoryItemError,
    MemoryConsolidationError,
    MemoryRetrievalError,
    MemoryStorageError,
)
from neuroca.memory.base import BaseMemory, MemoryItem, MemoryPriority, MemoryQuery

# Configure logger for the lymphatic memory subsystem
logger = logging.getLogger(__name__)

class LymphaticMemory(BaseMemory):
    """
    Lymphatic Memory implementation for the NCA system.
    
    This class provides the intermediate memory tier that sits between working memory
    and long-term storage. It handles memory consolidation, filtering, and prioritization
    based on configurable parameters.
    
    Attributes:
        retention_period (timedelta): How long memories are retained before cleanup
        consolidation_threshold (float): Importance threshold for consolidation to long-term
        capacity (int): Maximum number of memory items to store
        memory_store (Dict): Internal storage for memory items
        last_consolidation (datetime): Timestamp of the last consolidation operation
        last_cleanup (datetime): Timestamp of the last cleanup operation
    """
    
    def __init__(self, config: Optional[LymphaticMemoryConfig] = None):
        """
        Initialize the lymphatic memory system.
        
        Args:
            config (LymphaticMemoryConfig, optional): Configuration for the lymphatic memory.
                If not provided, default configuration will be used.
        """
        super().__init__()
        
        # Use provided config or create default
        self.config = config or LymphaticMemoryConfig()
        
        # Initialize memory parameters
        self.retention_period = self.config.retention_period
        self.consolidation_threshold = self.config.consolidation_threshold
        self.capacity = self.config.capacity
        
        # Initialize internal storage
        self.memory_store: dict[str, MemoryItem] = {}
        
        # Tracking timestamps for maintenance operations
        self.last_consolidation = datetime.now()
        self.last_cleanup = datetime.now()
        
        logger.info("Lymphatic memory system initialized with capacity %d and retention period %s",
                   self.capacity, self.retention_period)
    
    def store(self, item: Union[MemoryItem, dict[str, Any]]) -> str:
        """
        Store a memory item in the lymphatic memory system.
        
        Args:
            item (Union[MemoryItem, Dict]): The memory item to store. Can be a MemoryItem
                object or a dictionary with the required fields.
                
        Returns:
            str: The ID of the stored memory item.
            
        Raises:
            InvalidMemoryItemError: If the item format is invalid.
            MemoryStorageError: If there's an error storing the item.
        """
        try:
            # Convert dict to MemoryItem if necessary
            if isinstance(item, dict):
                memory_item = MemoryItem.from_dict(item)
            elif isinstance(item, MemoryItem):
                memory_item = item
            else:
                raise InvalidMemoryItemError(f"Expected MemoryItem or dict, got {type(item)}")
            
            # Generate ID if not present
            if not memory_item.id:
                memory_item.id = str(uuid.uuid4())
            
            # Set creation time if not present
            if not memory_item.created_at:
                memory_item.created_at = datetime.now()
            
            # Set last accessed time
            memory_item.last_accessed = datetime.now()
            
            # Check if we're at capacity and need to make room
            if len(self.memory_store) >= self.capacity:
                self._make_room()
            
            # Store the memory item
            self.memory_store[memory_item.id] = memory_item
            
            logger.debug("Stored memory item with ID %s and priority %s", 
                        memory_item.id, memory_item.priority)
            
            return memory_item.id
            
        except Exception as e:
            logger.error("Failed to store memory item: %s", str(e), exc_info=True)
            raise MemoryStorageError(f"Failed to store memory item: {str(e)}") from e
    
    def retrieve(self, query: MemoryQuery) -> list[MemoryItem]:
        """
        Retrieve memory items matching the given query.
        
        Args:
            query (MemoryQuery): The query parameters for retrieval.
            
        Returns:
            List[MemoryItem]: A list of memory items matching the query.
            
        Raises:
            MemoryRetrievalError: If there's an error retrieving items.
        """
        try:
            results = []
            
            # Direct ID lookup if provided
            if query.id and query.id in self.memory_store:
                item = self.memory_store[query.id]
                item.last_accessed = datetime.now()
                item.access_count += 1
                results.append(item)
                return results
            
            # Filter by other criteria
            for item in self.memory_store.values():
                if self._matches_query(item, query):
                    # Update access metadata
                    item.last_accessed = datetime.now()
                    item.access_count += 1
                    results.append(item)
            
            # Sort results by relevance if specified
            if query.sort_by_relevance and results:
                results.sort(key=lambda x: x.importance, reverse=True)
            
            # Limit results if specified
            if query.limit and query.limit > 0:
                results = results[:query.limit]
            
            logger.debug("Retrieved %d memory items matching query", len(results))
            return results
            
        except Exception as e:
            logger.error("Failed to retrieve memory items: %s", str(e), exc_info=True)
            raise MemoryRetrievalError(f"Failed to retrieve memory items: {str(e)}") from e
    
    def consolidate(self) -> tuple[int, int]:
        """
        Consolidate important memories to long-term storage.
        
        This method identifies memory items that exceed the consolidation threshold
        and marks them for transfer to long-term storage.
        
        Returns:
            Tuple[int, int]: A tuple containing (consolidated_count, remaining_count)
            
        Raises:
            MemoryConsolidationError: If there's an error during consolidation.
        """
        try:
            consolidated_count = 0
            remaining_count = 0
            
            # Update consolidation timestamp
            self.last_consolidation = datetime.now()
            
            for item_id, item in list(self.memory_store.items()):
                # Check if item exceeds consolidation threshold
                if item.importance >= self.consolidation_threshold:
                    # Mark for consolidation (in a full implementation, this would
                    # trigger transfer to long-term storage)
                    item.consolidated = True
                    consolidated_count += 1
                    
                    # In a complete implementation, we would call the long-term storage here
                    # long_term_memory.store(item)
                    
                    logger.debug("Marked item %s for consolidation to long-term storage", item_id)
                else:
                    remaining_count += 1
            
            logger.info("Consolidation complete: %d items consolidated, %d items retained",
                       consolidated_count, remaining_count)
            
            return consolidated_count, remaining_count
            
        except Exception as e:
            logger.error("Failed to consolidate memories: %s", str(e), exc_info=True)
            raise MemoryConsolidationError(f"Failed to consolidate memories: {str(e)}") from e
    
    def cleanup(self) -> int:
        """
        Clean up obsolete or low-priority memories.
        
        This method removes memory items that have exceeded their retention period
        or have low importance and haven't been accessed recently.
        
        Returns:
            int: The number of items removed during cleanup.
            
        Raises:
            MemoryStorageError: If there's an error during cleanup.
        """
        try:
            removed_count = 0
            current_time = datetime.now()
            self.last_cleanup = current_time
            
            for item_id, item in list(self.memory_store.items()):
                # Skip consolidated items
                if item.consolidated:
                    continue
                
                # Check if item has exceeded retention period
                age = current_time - item.created_at
                if age > self.retention_period:
                    del self.memory_store[item_id]
                    removed_count += 1
                    logger.debug("Removed item %s due to age (%s)", item_id, age)
                    continue
                
                # Check if item has low importance and hasn't been accessed recently
                if (item.importance < self.config.low_importance_threshold and 
                    current_time - item.last_accessed > self.config.inactive_threshold):
                    del self.memory_store[item_id]
                    removed_count += 1
                    logger.debug("Removed item %s due to low importance and inactivity", item_id)
            
            logger.info("Cleanup complete: %d items removed, %d items remaining",
                       removed_count, len(self.memory_store))
            
            return removed_count
            
        except Exception as e:
            logger.error("Failed to clean up memories: %s", str(e), exc_info=True)
            raise MemoryStorageError(f"Failed to clean up memories: {str(e)}") from e
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the current state of the lymphatic memory.
        
        Returns:
            Dict[str, Any]: A dictionary containing memory statistics.
        """
        current_time = datetime.now()
        
        # Count items by priority
        priority_counts = {
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for item in self.memory_store.values():
            if item.priority == MemoryPriority.HIGH:
                priority_counts["high"] += 1
            elif item.priority == MemoryPriority.MEDIUM:
                priority_counts["medium"] += 1
            else:
                priority_counts["low"] += 1
        
        return {
            "total_items": len(self.memory_store),
            "capacity": self.capacity,
            "usage_percent": (len(self.memory_store) / self.capacity) * 100 if self.capacity > 0 else 0,
            "priority_distribution": priority_counts,
            "consolidated_items": sum(1 for item in self.memory_store.values() if item.consolidated),
            "time_since_last_consolidation": (current_time - self.last_consolidation).total_seconds(),
            "time_since_last_cleanup": (current_time - self.last_cleanup).total_seconds(),
        }
    
    def _make_room(self) -> None:
        """
        Make room in the memory store when capacity is reached.
        
        This internal method removes the least important items to make room for new ones.
        """
        if len(self.memory_store) < self.capacity:
            return
        
        # Sort items by importance (ascending)
        sorted_items = sorted(
            self.memory_store.items(),
            key=lambda x: (x[1].importance, x[1].last_accessed)
        )
        
        # Remove least important items to get below capacity
        items_to_remove = max(1, int(self.capacity * self.config.cleanup_percentage))
        for i in range(min(items_to_remove, len(sorted_items))):
            item_id, _ = sorted_items[i]
            del self.memory_store[item_id]
            logger.debug("Removed item %s to make room for new items", item_id)
    
    def _matches_query(self, item: MemoryItem, query: MemoryQuery) -> bool:
        """
        Check if a memory item matches the given query.
        
        Args:
            item (MemoryItem): The memory item to check.
            query (MemoryQuery): The query to match against.
            
        Returns:
            bool: True if the item matches the query, False otherwise.
        """
        # Check each query parameter
        if query.content and query.content.lower() not in item.content.lower():
            return False
        
        if query.tags and not all(tag in item.tags for tag in query.tags):
            return False
        
        if query.category and query.category != item.category:
            return False
        
        if query.min_importance is not None and item.importance < query.min_importance:
            return False
        
        if query.max_importance is not None and item.importance > query.max_importance:
            return False
        
        if query.created_after and item.created_at < query.created_after:
            return False
        
        if query.created_before and item.created_at > query.created_before:
            return False
        
        if query.priority and item.priority != query.priority:
            return False
        
        return True

# Export public classes and functions
__all__ = ['LymphaticMemory']