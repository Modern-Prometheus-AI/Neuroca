"""
Backend Statistics Component

This module provides the BackendStats class for tracking and managing
storage backend statistics such as operation counts and item counts.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


class BackendStats:
    """
    Statistics tracking for storage backends.
    
    This class provides methods for tracking and updating statistics
    for storage backend operations, such as operation counts and timing.
    """
    
    def __init__(self):
        """Initialize statistics tracking."""
        self._stats = {
            "created_at": datetime.now(),
            "last_operation_at": None,
            "operations_count": 0,
            "items_count": 0,
            "create_count": 0,
            "read_count": 0,
            "update_count": 0,
            "delete_count": 0,
            "query_count": 0,
        }
    
    def update_stat(self, operation_name: str, count: int = 1) -> None:
        """
        Update operation statistics.
        
        Args:
            operation_name: The name of the operation to update
            count: The number of operations performed
        """
        self._stats["last_operation_at"] = datetime.now()
        self._stats["operations_count"] += count
        
        if operation_name in self._stats:
            self._stats[operation_name] += count
    
    def increment_items_count(self, count: int = 1) -> None:
        """
        Increment the items count.
        
        Args:
            count: The number of items to add
        """
        self._stats["items_count"] += count
    
    def decrement_items_count(self, count: int = 1) -> None:
        """
        Decrement the items count.
        
        Args:
            count: The number of items to remove
        """
        self._stats["items_count"] = max(0, self._stats["items_count"] - count)
    
    def set_items_count(self, count: int) -> None:
        """
        Set the items count to a specific value.
        
        Args:
            count: The new item count value
        """
        self._stats["items_count"] = max(0, count)
    
    def get_all_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get all statistics.
        
        Returns:
            Dictionary of all statistics
        """
        return self._stats.copy()
    
    def get_stat(self, stat_name: str) -> Optional[Union[int, float, str, datetime]]:
        """
        Get a specific statistic.
        
        Args:
            stat_name: The name of the statistic to retrieve
            
        Returns:
            The statistic value, or None if not found
        """
        return self._stats.get(stat_name)
    
    def merge_stats(self, backend_stats: Dict[str, Union[int, float, str, datetime]]) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Merge backend-specific stats with base stats.
        
        Args:
            backend_stats: Backend-specific statistics
            
        Returns:
            Merged statistics dictionary
        """
        return {
            **self._stats,
            **backend_stats,
        }
