"""
LTM Lifecycle Management

This module provides the LTMLifecycle class which handles initialization,
shutdown, and related lifecycle operations for the Long-Term Memory tier.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Set, Callable, List

from neuroca.memory.backends import BaseStorageBackend


logger = logging.getLogger(__name__)


class LTMLifecycle:
    """
    Manages lifecycle operations for the Long-Term Memory tier.
    
    This class handles initialization, shutdown, and related tasks like
    starting background maintenance tasks and managing category mappings.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the lifecycle manager.
        
        Args:
            tier_name: The name of the tier (always "ltm" for this class)
        """
        self._tier_name = tier_name
        self._maintenance_task = None
        self._category_map: Dict[str, Set[str]] = {}  # category -> set of memory_ids
        self._relationship_map: Dict[str, Dict[str, float]] = {}  # memory_id -> {related_id: strength}
        self._backend = None
        self._maintenance_func = None
        self._maintenance_interval = 86400  # Default: 24 hours
    
    async def initialize(self, backend: BaseStorageBackend, maintenance_func: Callable, config: Dict[str, Any]) -> None:
        """
        Initialize the LTM tier.
        
        Args:
            backend: The storage backend to use
            maintenance_func: Function to call for performing maintenance
            config: Configuration options
        """
        logger.info(f"Initializing LTM tier lifecycle")
        
        self._backend = backend
        self._maintenance_func = maintenance_func
        
        # Get configuration options
        self._maintenance_interval = config.get("maintenance_interval", 86400)
        
        # Load existing category and relationship information
        await self._load_category_map()
        await self._load_relationship_map()
        
        # Start maintenance task
        self._start_maintenance_task()
        
        logger.info("LTM lifecycle initialized")
    
    async def shutdown(self) -> None:
        """
        Shutdown the LTM tier lifecycle components.
        """
        logger.info("Shutting down LTM tier lifecycle")
        
        # Stop maintenance task
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
            self._maintenance_task = None
        
        logger.info("LTM lifecycle shutdown complete")
    
    def _start_maintenance_task(self) -> None:
        """
        Start the background maintenance task.
        """
        if self._maintenance_task is None or self._maintenance_task.done():
            self._maintenance_task = asyncio.create_task(self._maintenance_loop())
            logger.debug("Started LTM maintenance task")
    
    async def _maintenance_loop(self) -> None:
        """
        Background task for periodically performing maintenance on LTM memories.
        """
        logger.info(f"Starting LTM maintenance loop with interval: {self._maintenance_interval} seconds")
        
        try:
            while True:
                # Wait for the next maintenance interval
                await asyncio.sleep(self._maintenance_interval)
                
                # Perform maintenance
                try:
                    if self._maintenance_func:
                        await self._maintenance_func()
                except Exception as e:
                    logger.error(f"Error in LTM maintenance: {str(e)}")
        except asyncio.CancelledError:
            logger.info("LTM maintenance task cancelled")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in LTM maintenance loop: {str(e)}")
    
    async def _load_category_map(self) -> None:
        """
        Load category information for all memories in this tier.
        """
        logger.debug("Loading category map for LTM tier")
        
        # Clear current map
        self._category_map = {}
        
        try:
            # Query all memories with categories
            filters = {"metadata.tags.categories": {"$exists": True}}
            memories = await self._backend.query(filters=filters)
            
            # Build category map
            for memory_data in memories:
                try:
                    memory_id = memory_data.get("id")
                    tags = memory_data.get("metadata", {}).get("tags", {})
                    
                    if "categories" in tags and memory_id:
                        categories = tags["categories"]
                        if isinstance(categories, list):
                            for category in categories:
                                if category not in self._category_map:
                                    self._category_map[category] = set()
                                self._category_map[category].add(memory_id)
                except Exception as e:
                    logger.error(f"Error loading category for memory: {str(e)}")
            
            logger.info(f"Loaded category information for {sum(len(m) for m in self._category_map.values())} memories across {len(self._category_map)} categories")
        except Exception as e:
            logger.error(f"Error loading category map: {str(e)}")
    
    async def _load_relationship_map(self) -> None:
        """
        Load relationship information for all memories in this tier.
        """
        logger.debug("Loading relationship map for LTM tier")
        
        # Clear current map
        self._relationship_map = {}
        
        try:
            # Query all memories with relationships
            filters = {"metadata.tags.relationships": {"$exists": True}}
            memories = await self._backend.query(filters=filters)
            
            # Build relationship map
            for memory_data in memories:
                try:
                    memory_id = memory_data.get("id")
                    tags = memory_data.get("metadata", {}).get("tags", {})
                    
                    if "relationships" in tags and memory_id:
                        relationships = tags["relationships"]
                        if isinstance(relationships, dict):
                            self._relationship_map[memory_id] = relationships
                except Exception as e:
                    logger.error(f"Error loading relationships for memory: {str(e)}")
            
            logger.info(f"Loaded relationship information for {len(self._relationship_map)} memories")
        except Exception as e:
            logger.error(f"Error loading relationship map: {str(e)}")
    
    def get_category_map(self) -> Dict[str, Set[str]]:
        """
        Get a copy of the current category map.
        
        Returns:
            Dictionary mapping categories to sets of memory IDs
        """
        # Create a deep copy to prevent external modification
        return {category: set(memory_ids) for category, memory_ids in self._category_map.items()}
    
    def get_relationship_map(self) -> Dict[str, Dict[str, float]]:
        """
        Get a copy of the current relationship map.
        
        Returns:
            Dictionary mapping memory IDs to dictionaries of related memory IDs with strengths
        """
        # Create a deep copy to prevent external modification
        return {memory_id: dict(relationships) for memory_id, relationships in self._relationship_map.items()}
    
    def update_category(self, memory_id: str, categories: List[str]) -> None:
        """
        Update the categories for a memory.
        
        Args:
            memory_id: The ID of the memory
            categories: List of categories
        """
        # Remove memory from any existing categories
        for category, memory_ids in self._category_map.items():
            if memory_id in memory_ids:
                memory_ids.remove(memory_id)
        
        # Add memory to new categories
        for category in categories:
            if category not in self._category_map:
                self._category_map[category] = set()
            self._category_map[category].add(memory_id)
    
    def update_relationship(self, memory_id: str, related_id: str, strength: float) -> None:
        """
        Update the relationship between two memories.
        
        Args:
            memory_id: The ID of the memory
            related_id: The ID of the related memory
            strength: Relationship strength (0.0 to 1.0)
        """
        if memory_id not in self._relationship_map:
            self._relationship_map[memory_id] = {}
        
        self._relationship_map[memory_id][related_id] = strength
    
    def remove_memory(self, memory_id: str) -> None:
        """
        Remove a memory from all category and relationship maps.
        
        Args:
            memory_id: The ID of the memory
        """
        # Remove from categories
        for category, memory_ids in self._category_map.items():
            if memory_id in memory_ids:
                memory_ids.remove(memory_id)
        
        # Remove from relationships
        if memory_id in self._relationship_map:
            del self._relationship_map[memory_id]
        
        # Remove from related memories
        for related_id, relationships in self._relationship_map.items():
            if memory_id in relationships:
                del relationships[memory_id]
