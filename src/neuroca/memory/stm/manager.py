"""
Short-Term Memory (STM) Manager for the NeuroCognitive Architecture.

This module implements the Short-Term Memory component of the three-tiered memory system.
STM serves as a temporary storage for recent information with limited capacity and
duration, mimicking human cognitive processes. The STM Manager handles operations such as:
- Adding new memory items to STM
- Retrieving items from STM
- Managing memory decay and capacity constraints
- Transferring items between STM and other memory tiers
- Prioritizing items based on relevance and recency

Usage:
    stm_manager = STMManager()
    
    # Add a new memory item
    item_id = stm_manager.add_item(content="Important fact", metadata={"source": "conversation"})
    
    # Retrieve an item
    item = stm_manager.get_item(item_id)
    
    # Get all items matching a query
    relevant_items = stm_manager.search_items(query="important")
    
    # Update STM state (should be called periodically)
    stm_manager.update()
"""

import heapq
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class STMItem:
    """
    Represents a single item in Short-Term Memory.
    
    Attributes:
        id: Unique identifier for the memory item
        content: The actual content/information stored in memory
        creation_time: When the item was first added to STM
        last_accessed: When the item was last retrieved or modified
        access_count: Number of times this item has been accessed
        activation: Current activation level (determines retention)
        metadata: Additional information about the memory item
        priority: Item's priority in STM (higher = more important)
        tags: Set of tags for categorization and retrieval
    """
    id: str
    content: Any
    creation_time: float
    last_accessed: float
    access_count: int = 0
    activation: float = 1.0  # Starts at maximum activation
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: float = 0.0
    tags: set[str] = field(default_factory=set)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the STM item to a dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "creation_time": self.creation_time,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "activation": self.activation,
            "metadata": self.metadata,
            "priority": self.priority,
            "tags": list(self.tags)
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'STMItem':
        """Create an STM item from a dictionary."""
        # Convert tags back to a set if it exists
        if "tags" in data:
            data["tags"] = set(data["tags"])
        return cls(**data)
    
    def update_access(self) -> None:
        """Update the item's access statistics and activation."""
        self.last_accessed = time.time()
        self.access_count += 1
        self.activation = min(1.0, self.activation + 0.2)  # Boost activation, capped at 1.0


class STMManager:
    """
    Manager for Short-Term Memory operations in the NeuroCognitive Architecture.
    
    This class handles all operations related to the Short-Term Memory tier, including
    adding, retrieving, and maintaining memory items according to cognitive-inspired
    principles of decay, capacity limitations, and priority.
    """
    
    def __init__(
        self,
        capacity: int = 50,
        decay_rate: float = 0.05,
        decay_interval: float = 5.0,
        activation_threshold: float = 0.2,
        auto_update: bool = True
    ):
        """
        Initialize the STM Manager with configurable parameters.
        
        Args:
            capacity: Maximum number of items that can be stored in STM
            decay_rate: Rate at which memory activation decays over time
            decay_interval: Time interval (seconds) between decay updates
            activation_threshold: Minimum activation level for items to remain in STM
            auto_update: Whether to automatically update STM in background thread
        """
        self.capacity = capacity
        self.decay_rate = decay_rate
        self.decay_interval = decay_interval
        self.activation_threshold = activation_threshold
        
        # Main storage for STM items
        self._items: dict[str, STMItem] = {}
        
        # Index for faster searching
        self._content_index: dict[str, set[str]] = {}
        self._tag_index: dict[str, set[str]] = {}
        
        # Priority queue for managing capacity
        self._priority_queue: list[tuple[float, str]] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "items_added": 0,
            "items_removed": 0,
            "items_transferred": 0,
            "searches_performed": 0,
            "last_update_time": time.time()
        }
        
        # Set up automatic updating if enabled
        self._stop_update_thread = threading.Event()
        self._update_thread = None
        if auto_update:
            self._start_auto_update()
    
    def _start_auto_update(self) -> None:
        """Start the background thread for automatic STM updates."""
        if self._update_thread is not None and self._update_thread.is_alive():
            return
        
        self._stop_update_thread.clear()
        self._update_thread = threading.Thread(
            target=self._auto_update_loop,
            daemon=True,
            name="STM-Update-Thread"
        )
        self._update_thread.start()
        logger.debug("Started STM auto-update thread")
    
    def _auto_update_loop(self) -> None:
        """Background loop that periodically updates STM state."""
        while not self._stop_update_thread.is_set():
            try:
                self.update()
                time.sleep(self.decay_interval)
            except Exception as e:
                logger.error(f"Error in STM auto-update loop: {e}", exc_info=True)
                # Sleep briefly to avoid tight error loops
                time.sleep(1.0)
    
    def stop_auto_update(self) -> None:
        """Stop the automatic update thread."""
        if self._update_thread and self._update_thread.is_alive():
            self._stop_update_thread.set()
            self._update_thread.join(timeout=2.0)
            logger.debug("Stopped STM auto-update thread")
    
    def add_item(
        self,
        content: Any,
        metadata: Optional[dict[str, Any]] = None,
        priority: float = 0.0,
        tags: Optional[set[str]] = None,
        item_id: Optional[str] = None
    ) -> str:
        """
        Add a new item to Short-Term Memory.
        
        Args:
            content: The content to store in memory
            metadata: Additional information about the item
            priority: Item's importance (higher values = higher priority)
            tags: Set of tags for categorization
            item_id: Optional custom ID (if not provided, a UUID will be generated)
            
        Returns:
            The ID of the added item
            
        Raises:
            ValueError: If the content is None or empty
        """
        if content is None or (isinstance(content, str) and not content.strip()):
            raise ValueError("Cannot add empty content to STM")
        
        current_time = time.time()
        item_id = item_id or str(uuid.uuid4())
        metadata = metadata or {}
        tags = tags or set()
        
        # Create the new STM item
        item = STMItem(
            id=item_id,
            content=content,
            creation_time=current_time,
            last_accessed=current_time,
            activation=1.0,  # Start with full activation
            metadata=metadata,
            priority=priority,
            tags=tags
        )
        
        with self._lock:
            # Check if we need to make room
            if len(self._items) >= self.capacity:
                self._enforce_capacity()
            
            # Add the item
            self._items[item_id] = item
            
            # Update indexes
            self._update_indexes(item)
            
            # Update priority queue
            effective_priority = self._calculate_effective_priority(item)
            heapq.heappush(self._priority_queue, (effective_priority, item_id))
            
            # Update stats
            self.stats["items_added"] += 1
            
            logger.debug(f"Added item to STM: {item_id}")
            
        return item_id
    
    def get_item(self, item_id: str) -> Optional[STMItem]:
        """
        Retrieve an item from STM by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The STM item if found, None otherwise
        """
        with self._lock:
            item = self._items.get(item_id)
            if item:
                # Update access statistics
                item.update_access()
                
                # Re-evaluate priority in the queue
                self._update_item_priority(item)
                
                logger.debug(f"Retrieved item from STM: {item_id}")
            else:
                logger.debug(f"Item not found in STM: {item_id}")
                
        return item
    
    def update_item(
        self,
        item_id: str,
        content: Optional[Any] = None,
        metadata: Optional[dict[str, Any]] = None,
        priority: Optional[float] = None,
        tags: Optional[set[str]] = None
    ) -> bool:
        """
        Update an existing item in STM.
        
        Args:
            item_id: The ID of the item to update
            content: New content (if None, keeps existing)
            metadata: New metadata (if None, keeps existing)
            priority: New priority (if None, keeps existing)
            tags: New tags (if None, keeps existing)
            
        Returns:
            True if the item was updated, False if not found
            
        Raises:
            ValueError: If trying to update to empty content
        """
        if content is not None and (content is None or (isinstance(content, str) and not content.strip())):
            raise ValueError("Cannot update to empty content")
            
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                logger.debug(f"Cannot update item, not found in STM: {item_id}")
                return False
            
            # Remove from indexes before updating
            self._remove_from_indexes(item)
            
            # Update fields
            if content is not None:
                item.content = content
            if metadata is not None:
                item.metadata = metadata
            if priority is not None:
                item.priority = priority
            if tags is not None:
                item.tags = tags
                
            # Update access time and count
            item.update_access()
            
            # Re-index the item
            self._update_indexes(item)
            
            # Update priority in queue
            self._update_item_priority(item)
            
            logger.debug(f"Updated item in STM: {item_id}")
            return True
    
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from STM.
        
        Args:
            item_id: The ID of the item to remove
            
        Returns:
            True if the item was removed, False if not found
        """
        with self._lock:
            item = self._items.pop(item_id, None)
            if not item:
                logger.debug(f"Cannot remove item, not found in STM: {item_id}")
                return False
            
            # Remove from indexes
            self._remove_from_indexes(item)
            
            # Mark for removal from priority queue (will be cleaned up in next update)
            # We don't remove directly from the heap as it would be O(n)
            
            self.stats["items_removed"] += 1
            logger.debug(f"Removed item from STM: {item_id}")
            return True
    
    def search_items(
        self,
        query: Optional[str] = None,
        tags: Optional[set[str]] = None,
        metadata_filters: Optional[dict[str, Any]] = None,
        min_activation: float = 0.0,
        limit: Optional[int] = None
    ) -> list[STMItem]:
        """
        Search for items in STM based on various criteria.
        
        Args:
            query: Text to search for in content
            tags: Tags that items must have (all of them)
            metadata_filters: Metadata key-value pairs to match
            min_activation: Minimum activation level
            limit: Maximum number of results to return
            
        Returns:
            List of matching STM items, sorted by relevance
        """
        with self._lock:
            self.stats["searches_performed"] += 1
            
            # Start with all items
            candidate_ids = set(self._items.keys())
            
            # Apply tag filters if specified
            if tags:
                tag_matches = set()
                for tag in tags:
                    tag_matches.update(self._tag_index.get(tag, set()))
                candidate_ids &= tag_matches
            
            # Apply content query if specified
            if query and query.strip():
                query_terms = query.lower().split()
                content_matches = set()
                for term in query_terms:
                    content_matches.update(self._content_index.get(term, set()))
                candidate_ids &= content_matches
            
            # Filter results
            results = []
            for item_id in candidate_ids:
                item = self._items.get(item_id)
                if not item:
                    continue
                
                # Check activation threshold
                if item.activation < min_activation:
                    continue
                
                # Check metadata filters
                if metadata_filters:
                    match = True
                    for key, value in metadata_filters.items():
                        if key not in item.metadata or item.metadata[key] != value:
                            match = False
                            break
                    if not match:
                        continue
                
                results.append(item)
            
            # Sort by relevance (combination of activation, priority, and recency)
            results.sort(
                key=lambda x: (x.activation * 0.4 + x.priority * 0.4 + 
                              (1.0 / (time.time() - x.last_accessed + 1)) * 0.2),
                reverse=True
            )
            
            # Apply limit if specified
            if limit is not None and limit > 0:
                results = results[:limit]
            
            logger.debug(f"Search returned {len(results)} results")
            return results
    
    def update(self) -> None:
        """
        Update the state of STM, applying decay and enforcing constraints.
        
        This method should be called periodically to simulate the natural
        decay of short-term memory over time.
        """
        current_time = time.time()
        time_elapsed = current_time - self.stats["last_update_time"]
        
        with self._lock:
            # Apply decay to all items
            items_to_remove = []
            for item_id, item in list(self._items.items()):
                # Calculate decay based on time elapsed
                decay_amount = self.decay_rate * time_elapsed
                item.activation = max(0.0, item.activation - decay_amount)
                
                # Check if item should be removed due to low activation
                if item.activation < self.activation_threshold:
                    items_to_remove.append(item_id)
            
            # Remove items with low activation
            for item_id in items_to_remove:
                self.remove_item(item_id)
            
            # Clean up priority queue (remove any items that no longer exist)
            self._rebuild_priority_queue()
            
            # Enforce capacity constraints
            if len(self._items) > self.capacity:
                self._enforce_capacity()
            
            # Update statistics
            self.stats["last_update_time"] = current_time
            
            logger.debug(f"Updated STM state, removed {len(items_to_remove)} items due to decay")
    
    def get_all_items(self) -> list[STMItem]:
        """
        Get all items currently in STM.
        
        Returns:
            List of all STM items
        """
        with self._lock:
            return list(self._items.values())
    
    def clear(self) -> None:
        """Clear all items from STM."""
        with self._lock:
            self._items.clear()
            self._content_index.clear()
            self._tag_index.clear()
            self._priority_queue.clear()
            logger.debug("Cleared all items from STM")
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the current state of STM to a file.
        
        Args:
            filepath: Path to the file where STM state will be saved
            
        Raises:
            IOError: If the file cannot be written
        """
        with self._lock:
            try:
                items_data = {
                    item_id: item.to_dict() 
                    for item_id, item in self._items.items()
                }
                
                data = {
                    "items": items_data,
                    "stats": self.stats,
                    "config": {
                        "capacity": self.capacity,
                        "decay_rate": self.decay_rate,
                        "decay_interval": self.decay_interval,
                        "activation_threshold": self.activation_threshold
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"Saved STM state to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save STM state: {e}", exc_info=True)
                raise OSError(f"Failed to save STM state: {str(e)}")
    
    def load_from_file(self, filepath: str) -> None:
        """
        Load STM state from a file.
        
        Args:
            filepath: Path to the file containing saved STM state
            
        Raises:
            IOError: If the file cannot be read
            ValueError: If the file contains invalid data
        """
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            with self._lock:
                # Clear current state
                self.clear()
                
                # Load configuration
                config = data.get("config", {})
                self.capacity = config.get("capacity", self.capacity)
                self.decay_rate = config.get("decay_rate", self.decay_rate)
                self.decay_interval = config.get("decay_interval", self.decay_interval)
                self.activation_threshold = config.get("activation_threshold", self.activation_threshold)
                
                # Load statistics
                self.stats = data.get("stats", self.stats)
                
                # Load items
                items_data = data.get("items", {})
                for item_id, item_dict in items_data.items():
                    item = STMItem.from_dict(item_dict)
                    self._items[item_id] = item
                    self._update_indexes(item)
                
                # Rebuild priority queue
                self._rebuild_priority_queue()
                
                logger.info(f"Loaded STM state from {filepath} with {len(self._items)} items")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse STM state file: {e}", exc_info=True)
            raise ValueError(f"Invalid STM state file format: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load STM state: {e}", exc_info=True)
            raise OSError(f"Failed to load STM state: {str(e)}")
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the STM.
        
        Returns:
            Dictionary containing STM statistics
        """
        with self._lock:
            stats = self.stats.copy()
            stats.update({
                "current_size": len(self._items),
                "capacity": self.capacity,
                "capacity_utilization": len(self._items) / self.capacity if self.capacity > 0 else 0,
                "average_activation": sum(item.activation for item in self._items.values()) / len(self._items) if self._items else 0,
                "average_priority": sum(item.priority for item in self._items.values()) / len(self._items) if self._items else 0,
            })
            return stats
    
    def _enforce_capacity(self) -> None:
        """
        Enforce capacity constraints by removing lowest priority items.
        
        This method is called internally when STM reaches capacity.
        """
        # Rebuild priority queue to ensure it's accurate
        self._rebuild_priority_queue()
        
        # Remove items until we're under capacity
        items_removed = 0
        while len(self._items) > self.capacity and self._priority_queue:
            # Get the lowest priority item
            _, item_id = heapq.heappop(self._priority_queue)
            
            # Skip if item no longer exists
            if item_id not in self._items:
                continue
            
            # Remove the item
            item = self._items.pop(item_id)
            self._remove_from_indexes(item)
            items_removed += 1
            self.stats["items_removed"] += 1
        
        if items_removed > 0:
            logger.debug(f"Enforced STM capacity by removing {items_removed} items")
    
    def _update_indexes(self, item: STMItem) -> None:
        """
        Update search indexes for an item.
        
        Args:
            item: The STM item to index
        """
        # Index content words for text search
        if isinstance(item.content, str):
            words = item.content.lower().split()
            for word in words:
                if word not in self._content_index:
                    self._content_index[word] = set()
                self._content_index[word].add(item.id)
        
        # Index tags
        for tag in item.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(item.id)
    
    def _remove_from_indexes(self, item: STMItem) -> None:
        """
        Remove an item from all search indexes.
        
        Args:
            item: The STM item to remove from indexes
        """
        # Remove from content index
        if isinstance(item.content, str):
            words = item.content.lower().split()
            for word in words:
                if word in self._content_index:
                    self._content_index[word].discard(item.id)
                    # Clean up empty sets
                    if not self._content_index[word]:
                        del self._content_index[word]
        
        # Remove from tag index
        for tag in item.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(item.id)
                # Clean up empty sets
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
    
    def _calculate_effective_priority(self, item: STMItem) -> float:
        """
        Calculate the effective priority of an item for the priority queue.
        
        This combines explicit priority with activation and recency.
        
        Args:
            item: The STM item
            
        Returns:
            Effective priority value (lower values = lower priority)
        """
        # Combine factors: explicit priority, activation level, and recency
        recency_factor = 1.0 / (time.time() - item.last_accessed + 1)
        
        # Weighted combination (can be tuned)
        return item.priority * 0.5 + item.activation * 0.3 + recency_factor * 0.2
    
    def _update_item_priority(self, item: STMItem) -> None:
        """
        Update an item's position in the priority queue.
        
        Args:
            item: The STM item whose priority needs updating
        """
        # Since heapq doesn't support efficient updates, we'll mark the old entry
        # as invalid and add a new one. The invalid entries will be cleaned up
        # during the next rebuild.
        effective_priority = self._calculate_effective_priority(item)
        heapq.heappush(self._priority_queue, (effective_priority, item.id))
    
    def _rebuild_priority_queue(self) -> None:
        """Rebuild the priority queue from scratch to remove stale entries."""
        valid_entries = []
        for item_id, item in self._items.items():
            priority = self._calculate_effective_priority(item)
            valid_entries.append((priority, item_id))
        
        self._priority_queue = valid_entries
        heapq.heapify(self._priority_queue)
    
    def __len__(self) -> int:
        """Return the number of items in STM."""
        return len(self._items)
    
    def __contains__(self, item_id: str) -> bool:
        """Check if an item exists in STM."""
        return item_id in self._items
    
    def __del__(self) -> None:
        """Clean up resources when the STM manager is destroyed."""
        self.stop_auto_update()