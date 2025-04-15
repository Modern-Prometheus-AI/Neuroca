"""
Storage Stats Interface

This module defines data models for storage statistics in the Neuroca memory system.
These models provide structured representations of storage backend statistics for
monitoring, reporting, and analysis purposes.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Union


class StorageStats:
    """
    Data model for storage backend statistics.
    
    This class represents a standardized set of statistics about a storage backend,
    including information about item counts, storage usage, performance metrics,
    and age statistics.
    """
    
    def __init__(
        self,
        backend_type: str,
        item_count: int,
        storage_size_bytes: int,
        metadata_size_bytes: int = 0,
        average_item_age_seconds: float = 0.0,
        oldest_item_age_seconds: float = 0.0,
        newest_item_age_seconds: float = 0.0,
        max_capacity: int = -1,
        capacity_used_percent: float = 0.0,
        created_at: datetime = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize storage statistics.
        
        Args:
            backend_type: The type of storage backend (e.g., "InMemory", "Redis")
            item_count: Number of items in storage
            storage_size_bytes: Estimated size of stored data in bytes
            metadata_size_bytes: Estimated size of metadata in bytes
            average_item_age_seconds: Average age of items in seconds
            oldest_item_age_seconds: Age of the oldest item in seconds
            newest_item_age_seconds: Age of the newest item in seconds
            max_capacity: Maximum capacity of the storage (-1 if unlimited)
            capacity_used_percent: Percentage of capacity used
            created_at: When these statistics were collected
            additional_info: Additional backend-specific information
        """
        self.backend_type = backend_type
        self.item_count = item_count
        self.storage_size_bytes = storage_size_bytes
        self.metadata_size_bytes = metadata_size_bytes
        self.average_item_age_seconds = average_item_age_seconds
        self.oldest_item_age_seconds = oldest_item_age_seconds
        self.newest_item_age_seconds = newest_item_age_seconds
        self.max_capacity = max_capacity
        self.capacity_used_percent = capacity_used_percent
        self.created_at = created_at or datetime.now()
        self.additional_info = additional_info or {}
    
    def to_dict(self) -> Dict[str, Union[str, int, float, Dict[str, Any]]]:
        """
        Convert statistics to a dictionary.
        
        Returns:
            Dictionary representation of the statistics
        """
        return {
            "backend_type": self.backend_type,
            "item_count": self.item_count,
            "storage_size_bytes": self.storage_size_bytes,
            "metadata_size_bytes": self.metadata_size_bytes,
            "average_item_age_seconds": self.average_item_age_seconds,
            "oldest_item_age_seconds": self.oldest_item_age_seconds,
            "newest_item_age_seconds": self.newest_item_age_seconds,
            "max_capacity": self.max_capacity,
            "capacity_used_percent": self.capacity_used_percent,
            "created_at": self.created_at.isoformat(),
            "additional_info": self.additional_info
        }
    
    def __str__(self) -> str:
        """
        Get a string representation of the statistics.
        
        Returns:
            String representation
        """
        return (
            f"StorageStats(backend={self.backend_type}, "
            f"items={self.item_count}, "
            f"size={self.storage_size_bytes / 1024:.1f}KB, "
            f"capacity={self.capacity_used_percent:.1f}%)"
        )
    
    def __repr__(self) -> str:
        """
        Get a detailed string representation of the statistics.
        
        Returns:
            Detailed string representation
        """
        return (
            f"StorageStats("
            f"backend_type='{self.backend_type}', "
            f"item_count={self.item_count}, "
            f"storage_size_bytes={self.storage_size_bytes}, "
            f"metadata_size_bytes={self.metadata_size_bytes}, "
            f"average_item_age_seconds={self.average_item_age_seconds}, "
            f"oldest_item_age_seconds={self.oldest_item_age_seconds}, "
            f"newest_item_age_seconds={self.newest_item_age_seconds}, "
            f"max_capacity={self.max_capacity}, "
            f"capacity_used_percent={self.capacity_used_percent}, "
            f"created_at='{self.created_at.isoformat()}', "
            f"additional_info={self.additional_info}"
            f")"
        )
