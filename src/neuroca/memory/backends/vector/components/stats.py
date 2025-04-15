"""
Vector Stats Component

This module provides the VectorStats class for collecting statistics about vector storage.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.vector.components.index import VectorIndex
from neuroca.memory.backends.vector.components.storage import VectorStorage
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.interfaces import StorageStats

logger = logging.getLogger(__name__)


class VectorStats:
    """
    Collects and reports statistics about vector storage.
    
    This class provides methods for retrieving various metrics about the
    vector storage, such as item count, storage size, and status distributions.
    """
    
    def __init__(
        self,
        index: VectorIndex,
        storage: VectorStorage,
    ):
        """
        Initialize the vector stats component.
        
        Args:
            index: Vector index component
            storage: Vector storage component
        """
        self.index = index
        self.storage = storage
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the vector storage.
        
        Returns:
            StorageStats: Statistics about the storage
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Get counts by status
            status_counts = self._get_status_counts()
            total_count = self.index.count()
            active_count = status_counts.get("active", 0)
            archived_count = status_counts.get("archived", 0)
            
            # Estimate storage size
            size_bytes = self._estimate_storage_size()
            
            # Estimate metadata size
            metadata_size_bytes = self._estimate_metadata_size()
            
            # Get age statistics
            avg_age_seconds, oldest_age_seconds, newest_age_seconds = self._get_age_stats()
            
            # Additional info
            additional_info = {
                "dimension": self.index.dimension,
                "index_path": self.storage.index_path,
                "status_distribution": status_counts,
                "tag_distribution": self._get_tag_counts(),
            }
            
            # Create StorageStats object
            stats = StorageStats(
                backend_type="VectorBackend",
                item_count=total_count,
                storage_size_bytes=size_bytes,
                metadata_size_bytes=metadata_size_bytes,
                average_item_age_seconds=avg_age_seconds,
                oldest_item_age_seconds=oldest_age_seconds,
                newest_item_age_seconds=newest_age_seconds,
                max_capacity=-1,  # Vector database has no fixed capacity
                capacity_used_percent=0.0,
                additional_info=additional_info
            )
            
            logger.debug(f"Retrieved storage stats: {total_count} memories")
            return stats
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    def _get_status_counts(self) -> Dict[str, int]:
        """
        Get counts of memory items by status.
        
        Returns:
            Dict[str, int]: Dictionary mapping status values to counts
        """
        status_counts = {}
        
        for entry in self.index.get_entries():
            status = entry.metadata.get("status", "active")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return status_counts
    
    def _get_tag_counts(self) -> Dict[str, int]:
        """
        Get counts of memory items by tag.
        
        Returns:
            Dict[str, int]: Dictionary mapping tag values to counts
        """
        tag_counts = {}
        
        for entry in self.index.get_entries():
            tags = entry.metadata.get("tags", [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return tag_counts
    
    def _estimate_storage_size(self) -> int:
        """
        Estimate the storage size of the vector database.
        
        Returns:
            int: Estimated size in bytes
        """
        size_bytes = 0
        
        # Estimate vector size (assuming float32)
        for entry in self.index.get_entries():
            # Vector size (assuming float32)
            size_bytes += len(entry.vector) * 4
            # Metadata size (rough estimate)
            size_bytes += len(json.dumps(entry.metadata))
        
        return size_bytes
    
    def _estimate_metadata_size(self) -> int:
        """
        Estimate the size of metadata stored in the storage.
        
        Returns:
            int: Estimated size in bytes
        """
        metadata_dict = self.storage.get_all_memory_metadata()
        return len(json.dumps(metadata_dict))
    
    def _get_age_stats(self) -> tuple[float, float, float]:
        """
        Get age statistics for memory items.
        
        Returns:
            Tuple of (average_age_seconds, oldest_age_seconds, newest_age_seconds)
        """
        now = datetime.now()
        ages = []
        
        for entry in self.index.get_entries():
            created_at = entry.metadata.get("created_at")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at)
                    age_seconds = (now - dt).total_seconds()
                    ages.append(age_seconds)
                except (ValueError, TypeError):
                    continue
        
        if not ages:
            return 0.0, 0.0, 0.0
        
        avg_age = sum(ages) / len(ages)
        oldest_age = max(ages)
        newest_age = min(ages)
        
        return avg_age, oldest_age, newest_age
    
    async def get_access_stats(self) -> Dict[str, Any]:
        """
        Get access statistics for memory items.
        
        Returns:
            Dict: Access statistics
        """
        metadata_dict = self.storage.get_all_memory_metadata()
        
        access_counts = []
        last_access_times = []
        
        for metadata in metadata_dict.values():
            access_count = metadata.get("access_count", 0)
            access_counts.append(access_count)
            
            last_accessed = metadata.get("last_accessed")
            if last_accessed:
                try:
                    dt = datetime.fromisoformat(last_accessed)
                    last_access_times.append(dt)
                except (ValueError, TypeError):
                    continue
        
        if not access_counts:
            return {
                "avg_access_count": 0,
                "max_access_count": 0,
                "min_access_count": 0,
                "seconds_since_last_access": None
            }
        
        now = datetime.now()
        
        avg_access_count = sum(access_counts) / len(access_counts)
        max_access_count = max(access_counts)
        min_access_count = min(access_counts)
        
        seconds_since_last_access = None
        if last_access_times:
            last_access = max(last_access_times)
            seconds_since_last_access = (now - last_access).total_seconds()
        
        return {
            "avg_access_count": avg_access_count,
            "max_access_count": max_access_count,
            "min_access_count": min_access_count,
            "seconds_since_last_access": seconds_since_last_access
        }
