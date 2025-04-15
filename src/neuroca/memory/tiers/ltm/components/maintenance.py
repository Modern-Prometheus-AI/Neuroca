"""
LTM Maintenance Management

This module provides the LTMMaintenance class which handles maintenance
tasks for the Long-Term Memory (LTM) tier.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Callable

from neuroca.memory.backends import BaseStorageBackend
from neuroca.memory.models.memory_item import MemoryItem, MemoryStatus


logger = logging.getLogger(__name__)


class LTMMaintenance:
    """
    Manages maintenance tasks for the LTM tier.
    
    This class provides functionality for maintaining the LTM tier, including
    tasks like consolidating memory relationships, pruning unused categories,
    and maintaining overall system health.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the maintenance manager.
        
        Args:
            tier_name: The name of the tier (always "ltm" for this class)
        """
        self._tier_name = tier_name
        self._backend = None
        self._lifecycle = None
        self._relationship_manager = None
        self._category_manager = None
        self._auto_prune = True  # Whether to auto-prune empty categories
        self._auto_strengthen = True  # Whether to auto-strengthen frequently accessed memories
    
    def configure(
        self, 
        backend: BaseStorageBackend,
        lifecycle: Any,
        relationship_manager: Any,
        category_manager: Any,
        config: Dict[str, Any]
    ) -> None:
        """
        Configure the maintenance manager.
        
        Args:
            backend: The storage backend to use
            lifecycle: The lifecycle manager
            relationship_manager: The relationship manager
            category_manager: The category manager
            config: Configuration options
        """
        self._backend = backend
        self._lifecycle = lifecycle
        self._relationship_manager = relationship_manager
        self._category_manager = category_manager
        
        # Configuration options
        self._auto_prune = config.get("auto_prune_categories", True)
        self._auto_strengthen = config.get("auto_strengthen_relationships", True)
    
    async def perform_maintenance(self) -> Dict[str, int]:
        """
        Perform maintenance tasks for the LTM tier.
        
        Returns:
            Dictionary with counts of affected items
        """
        logger.info("Performing LTM maintenance")
        
        results = {
            "pruned_categories": 0,
            "strengthened_relationships": 0,
            "updated_memories": 0,
            "errors": 0,
        }
        
        # Check if we have necessary components
        if not self._backend or not self._lifecycle:
            logger.warning("Cannot perform maintenance: missing components")
            return results
        
        try:
            # Prune empty categories
            if self._auto_prune:
                pruned = await self._prune_empty_categories()
                results["pruned_categories"] = pruned
            
            # Strengthen relationships for frequently accessed memories
            if self._auto_strengthen:
                strengthened = await self._strengthen_relationships()
                results["strengthened_relationships"] = strengthened
            
            # Update memory statistics
            updated = await self._update_memory_statistics()
            results["updated_memories"] = updated
            
        except Exception as e:
            logger.error(f"Error during LTM maintenance: {str(e)}")
            results["errors"] += 1
        
        logger.info(f"LTM maintenance completed: {results}")
        return results
    
    async def _prune_empty_categories(self) -> int:
        """
        Prune empty categories from the category map.
        
        Returns:
            Number of categories pruned
        """
        if not self._category_manager:
            return 0
        
        count = 0
        
        try:
            # Get all categories and counts
            categories = await self._category_manager.get_all_categories()
            
            # Identify empty categories
            empty_categories = [
                category for category, count in categories.items()
                if count == 0 and category != "general"  # Don't prune default general category
            ]
            
            # Prune empty categories - we need to modify the category map directly
            if self._lifecycle:
                category_map = self._lifecycle.get_category_map()
                for category in empty_categories:
                    if category in category_map:
                        del category_map[category]
                        count += 1
            
            logger.info(f"Pruned {count} empty categories")
        except Exception as e:
            logger.error(f"Error pruning empty categories: {str(e)}")
        
        return count
    
    async def _strengthen_relationships(self) -> int:
        """
        Strengthen relationships for frequently accessed memories.
        
        Returns:
            Number of relationships strengthened
        """
        if not self._relationship_manager:
            return 0
        
        count = 0
        
        try:
            # Get frequently accessed memories
            # Note: In a real implementation, this would query based on access count or similar metric
            # For the demo, we'll just use a simplified approach with a limit
            
            from neuroca.memory.models.memory_item import MemoryStatus
            
            # Get active memories with high access count
            filters = {
                "metadata.status": MemoryStatus.ACTIVE.value,
                "metadata.access_count": {"$gt": 5},  # Memories accessed more than 5 times
            }
            
            memories = await self._backend.query(
                filters=filters,
                sort_by="metadata.access_count",
                ascending=False,
                limit=20,  # Limit to top 20 frequently accessed
            )
            
            # Check which memories have relationships
            for memory_data in memories:
                try:
                    memory_id = memory_data.get("id")
                    memory_item = MemoryItem.model_validate(memory_data)
                    
                    relationships = memory_item.metadata.tags.get("relationships", {})
                    
                    # Strengthen existing relationships
                    for related_id, rel_data in relationships.items():
                        # Get current strength
                        current_strength = rel_data.get("strength", 0.5)
                        
                        # Only strengthen if below threshold
                        if current_strength < 0.9:
                            # Increase strength by 10%, but cap at 0.9
                            new_strength = min(0.9, current_strength * 1.1)
                            
                            # Update relationship
                            rel_type = rel_data.get("type", "semantic")
                            await self._relationship_manager.add_relationship(
                                memory_id=memory_id,
                                related_id=related_id,
                                relationship_type=rel_type,
                                strength=new_strength,
                                bidirectional=True
                            )
                            
                            count += 1
                except Exception as e:
                    logger.error(f"Error strengthening relationships for {memory_id}: {str(e)}")
            
            logger.info(f"Strengthened {count} relationships")
        except Exception as e:
            logger.error(f"Error strengthening relationships: {str(e)}")
        
        return count
    
    async def _update_memory_statistics(self) -> int:
        """
        Update memory statistics for reporting and analytics.
        
        Returns:
            Number of memories updated
        """
        # In a real implementation, this would update various statistics
        # For the demo, we'll just return a placeholder count
        
        return 0
    
    async def get_maintenance_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the LTM tier for maintenance reporting.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_memories": 0,
            "total_categories": 0,
            "total_relationships": 0,
            "avg_categories_per_memory": 0,
            "avg_relationships_per_memory": 0,
        }
        
        try:
            # Count total memories
            if self._backend:
                stats["total_memories"] = await self._backend.count({})
            
            # Count total categories and relationships
            if self._lifecycle:
                category_map = self._lifecycle.get_category_map()
                relationship_map = self._lifecycle.get_relationship_map()
                
                stats["total_categories"] = len(category_map)
                stats["total_relationships"] = sum(len(relationships) for relationships in relationship_map.values())
                
                # Calculate averages
                if stats["total_memories"] > 0:
                    # Average categories per memory
                    category_counts = [len(memory_ids) for memory_ids in category_map.values()]
                    if category_counts:
                        stats["avg_categories_per_memory"] = sum(category_counts) / stats["total_memories"]
                    
                    # Average relationships per memory
                    relationship_counts = [len(relationships) for relationships in relationship_map.values()]
                    if relationship_counts:
                        stats["avg_relationships_per_memory"] = sum(relationship_counts) / stats["total_memories"]
        except Exception as e:
            logger.error(f"Error getting maintenance stats: {str(e)}")
        
        return stats
