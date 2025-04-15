"""
In-Memory Stats Component

This module provides a class for collecting and reporting statistics about
the in-memory storage backend.
"""

import sys
from datetime import datetime
from typing import Any, Dict, Union

from neuroca.memory.backends.in_memory.components.storage import InMemoryStorage
from neuroca.memory.interfaces import StorageStats


class InMemoryStats:
    """
    Collects and reports statistics about the in-memory storage.
    
    This class provides methods for calculating and retrieving various metrics
    about the storage, such as item count, memory usage, and age statistics.
    """
    
    def __init__(self, storage: InMemoryStorage):
        """
        Initialize the stats component.
        
        Args:
            storage: The storage component to monitor
        """
        self.storage = storage
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the in-memory backend.
        
        Returns:
            StorageStats object with various statistics
        """
        await self.storage.acquire_lock()
        try:
            # Basic stats
            item_count = self.storage.count_items()
            storage_size = self._estimate_storage_size()
            metadata_size = self._estimate_metadata_size()
            average_age = self._calculate_average_age()
            oldest_item_age = self._get_oldest_item_age()
            newest_item_age = self._get_newest_item_age()
            
            # Create StorageStats object
            stats = StorageStats(
                backend_type="InMemoryBackend",
                item_count=item_count,
                storage_size_bytes=storage_size,
                metadata_size_bytes=metadata_size,
                average_item_age_seconds=average_age,
                oldest_item_age_seconds=oldest_item_age,
                newest_item_age_seconds=newest_item_age,
                max_capacity=self.storage.max_items or -1,
                capacity_used_percent=self._calculate_capacity_used_percent(),
                additional_info={
                    "memory_address": hex(id(self.storage)),
                    "python_version": sys.version,
                    "in_memory_backend_version": "1.0.0"  # Example version
                }
            )
            
            return stats
        finally:
            self.storage.release_lock()
    
    def _estimate_storage_size(self) -> int:
        """
        Estimate the amount of memory used by the stored items.
        
        Returns:
            Estimated size in bytes
        """
        # This is a rough approximation
        size_estimate = 0
        for item_id, data in self.storage.get_all_items().items():
            # Add approximate size of item_id
            size_estimate += len(item_id) * 2  # UTF-8 chars are ~2 bytes
            
            # Add approximate size of data
            # This is very rough and doesn't account for Python's object overhead
            size_estimate += len(str(data)) * 2
        
        return size_estimate
    
    def _estimate_metadata_size(self) -> int:
        """
        Estimate the amount of memory used by metadata.
        
        Returns:
            Estimated metadata size in bytes
        """
        metadata_size = 0
        for _item_id, data in self.storage.get_all_items().items():
            if "_meta" in data:
                # Rough estimate
                metadata_size += len(str(data["_meta"])) * 2
        
        return metadata_size
    
    def _calculate_average_age(self) -> float:
        """
        Calculate the average age of items in storage.
        
        Returns:
            Average age in seconds
        """
        created_timestamps = []
        now = datetime.now()
        
        for _item_id, data in self.storage.get_all_items().items():
            if "_meta" in data and "created_at" in data["_meta"]:
                try:
                    created_at = datetime.fromisoformat(data["_meta"]["created_at"])
                    created_timestamps.append(created_at)
                except (ValueError, TypeError):
                    pass
        
        if not created_timestamps:
            return 0.0
            
        total_age = sum((now - created_at).total_seconds() for created_at in created_timestamps)
        return total_age / len(created_timestamps)
    
    def _get_oldest_item_age(self) -> float:
        """
        Get the age of the oldest item in storage.
        
        Returns:
            Age in seconds, or 0.0 if no items or no timestamps
        """
        oldest_timestamp = None
        now = datetime.now()
        
        for _item_id, data in self.storage.get_all_items().items():
            if "_meta" in data and "created_at" in data["_meta"]:
                try:
                    created_at = datetime.fromisoformat(data["_meta"]["created_at"])
                    if oldest_timestamp is None or created_at < oldest_timestamp:
                        oldest_timestamp = created_at
                except (ValueError, TypeError):
                    pass
        
        if oldest_timestamp is None:
            return 0.0
            
        return (now - oldest_timestamp).total_seconds()
    
    def _get_newest_item_age(self) -> float:
        """
        Get the age of the newest item in storage.
        
        Returns:
            Age in seconds, or 0.0 if no items or no timestamps
        """
        newest_timestamp = None
        now = datetime.now()
        
        for _item_id, data in self.storage.get_all_items().items():
            if "_meta" in data and "created_at" in data["_meta"]:
                try:
                    created_at = datetime.fromisoformat(data["_meta"]["created_at"])
                    if newest_timestamp is None or created_at > newest_timestamp:
                        newest_timestamp = created_at
                except (ValueError, TypeError):
                    pass
        
        if newest_timestamp is None:
            return 0.0
            
        return (now - newest_timestamp).total_seconds()
    
    def _calculate_capacity_used_percent(self) -> float:
        """
        Calculate the percentage of capacity used.
        
        Returns:
            Percentage of capacity used (0.0-100.0), or 0.0 if no limit
        """
        if self.storage.max_items is None:
            return 0.0
            
        item_count = self.storage.count_items()
        return (item_count / self.storage.max_items) * 100.0
