"""
Memory Tier Statistics

This module provides functionality for collecting and managing
statistics about memory tiers.
"""

from datetime import datetime
from typing import Any, Dict, Union

from neuroca.memory.models.memory_item import MemoryItem


class TierStatsManager:
    """
    Manages the collection and reporting of memory tier statistics.
    
    This class provides methods for updating operation statistics and
    generating tier-specific statistics reports.
    """
    
    @staticmethod
    def create_base_stats() -> Dict[str, Union[int, float, str, datetime]]:
        """
        Create a base statistics dictionary with default values.
        
        Returns:
            Base statistics dictionary
        """
        return {
            "created_at": datetime.now(),
            "last_operation_at": None,
            "operations_count": 0,
            "items_count": 0,
            "store_count": 0,
            "retrieve_count": 0,
            "update_count": 0,
            "delete_count": 0,
            "search_count": 0,
        }
    
    @staticmethod
    def update_operation_stats(
        stats: Dict[str, Union[int, float, str, datetime]],
        operation_name: str,
        count: int = 1
    ) -> None:
        """
        Update the operation statistics.
        
        Args:
            stats: Statistics dictionary to update
            operation_name: Name of the operation
            count: Number of operations performed
        """
        stats["last_operation_at"] = datetime.now()
        stats["operations_count"] += count
        stats[operation_name] += count
    
    @staticmethod
    async def get_tier_stats(
        tier_name: str,
        backend
    ) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get tier-specific statistics.
        
        Args:
            tier_name: Name of the tier
            backend: Storage backend
            
        Returns:
            Tier-specific statistics
        """
        # Calculate tier-specific statistics based on the tier name
        if tier_name == "stm":
            return await TierStatsManager._get_stm_stats(backend)
        elif tier_name == "mtm":
            return await TierStatsManager._get_mtm_stats(backend)
        elif tier_name == "ltm":
            return await TierStatsManager._get_ltm_stats(backend)
        else:
            return {}
    
    @staticmethod
    async def _get_stm_stats(backend) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics specific to STM tier.
        
        Args:
            backend: Storage backend
            
        Returns:
            STM-specific statistics
        """
        # Get STM-specific statistics
        stats = {}
        
        # Count items by status
        active_count = await backend.count({"metadata.status": "active"})
        expired_count = await backend.count({"metadata.status": "expired"})
        
        stats["active_count"] = active_count
        stats["expired_count"] = expired_count
        stats["average_lifespan_seconds"] = await TierStatsManager._calculate_average_lifespan(backend)
        
        return stats
    
    @staticmethod
    async def _get_mtm_stats(backend) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics specific to MTM tier.
        
        Args:
            backend: Storage backend
            
        Returns:
            MTM-specific statistics
        """
        # Get MTM-specific statistics
        stats = {}
        
        # Count items by priority
        high_priority_count = await backend.count({"metadata.priority": "high"})
        medium_priority_count = await backend.count({"metadata.priority": "medium"})
        low_priority_count = await backend.count({"metadata.priority": "low"})
        
        stats["high_priority_count"] = high_priority_count
        stats["medium_priority_count"] = medium_priority_count
        stats["low_priority_count"] = low_priority_count
        stats["average_access_count"] = await TierStatsManager._calculate_average_access_count(backend)
        
        return stats
    
    @staticmethod
    async def _get_ltm_stats(backend) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics specific to LTM tier.
        
        Args:
            backend: Storage backend
            
        Returns:
            LTM-specific statistics
        """
        # Get LTM-specific statistics
        stats = {}
        
        # Count relationships if supported
        relationship_count = 0
        if hasattr(backend, "count_relationships"):
            relationship_count = await backend.count_relationships()
        
        stats["relationship_count"] = relationship_count
        stats["average_importance"] = await TierStatsManager._calculate_average_importance(backend)
        
        return stats
    
    @staticmethod
    async def _calculate_average_lifespan(backend) -> float:
        """
        Calculate the average lifespan of memories in seconds.
        
        Args:
            backend: Storage backend
            
        Returns:
            Average lifespan in seconds
        """
        # Simplified implementation, in a real system this would be more complex
        return 0.0
    
    @staticmethod
    async def _calculate_average_access_count(backend) -> float:
        """
        Calculate the average number of times memories have been accessed.
        
        Args:
            backend: Storage backend
            
        Returns:
            Average access count
        """
        # Simplified implementation, in a real system this would be more complex
        return 0.0
    
    @staticmethod
    async def _calculate_average_importance(backend) -> float:
        """
        Calculate the average importance of memories.
        
        Args:
            backend: Storage backend
            
        Returns:
            Average importance
        """
        # Simplified implementation, in a real system this would be more complex
        return 0.5
