"""
MTM Lifecycle Management

This module provides the MTMLifecycle class which handles initialization,
shutdown, and related lifecycle operations for the Medium-Term Memory tier.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Set, Callable

from neuroca.memory.backends import BaseStorageBackend


logger = logging.getLogger(__name__)


class MTMLifecycle:
    """
    Manages lifecycle operations for the Medium-Term Memory tier.
    
    This class handles initialization, shutdown, and related tasks like
    loading the priority map and starting background tasks.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the lifecycle manager.
        
        Args:
            tier_name: The name of the tier (always "mtm" for this class)
        """
        self._tier_name = tier_name
        self._consolidation_task = None
        self._priority_map: Dict[str, str] = {}  # memory_id -> priority
        self._backend = None
        self._consolidation_func = None
        self._consolidation_interval = 3600  # Default: 1 hour
    
    async def initialize(self, backend: BaseStorageBackend, consolidation_func: Callable, config: Dict[str, Any]) -> None:
        """
        Initialize the MTM tier.
        
        Args:
            backend: The storage backend to use
            consolidation_func: Function to call for consolidating memories
            config: Configuration options
        """
        logger.info(f"Initializing MTM tier lifecycle with capacity: {config.get('max_capacity', 1000)}")
        
        self._backend = backend
        self._consolidation_func = consolidation_func
        
        # Get configuration options
        self._consolidation_interval = config.get("consolidation_interval", 3600)
        
        # Load existing priority information
        await self._load_priority_map()
        
        # Start consolidation task
        self._start_consolidation_task()
        
        logger.info("MTM lifecycle initialized")
    
    async def shutdown(self) -> None:
        """
        Shutdown the MTM tier lifecycle components.
        """
        logger.info("Shutting down MTM tier lifecycle")
        
        # Stop consolidation task
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass
            self._consolidation_task = None
        
        logger.info("MTM lifecycle shutdown complete")
    
    def _start_consolidation_task(self) -> None:
        """
        Start the background consolidation task.
        """
        if self._consolidation_task is None or self._consolidation_task.done():
            self._consolidation_task = asyncio.create_task(self._consolidation_loop())
            logger.debug("Started MTM consolidation task")
    
    async def _consolidation_loop(self) -> None:
        """
        Background task for periodically consolidating memories.
        """
        logger.info(f"Starting MTM consolidation loop with interval: {self._consolidation_interval} seconds")
        
        try:
            while True:
                # Wait for the next consolidation interval
                await asyncio.sleep(self._consolidation_interval)
                
                # Perform consolidation
                try:
                    if self._consolidation_func:
                        await self._consolidation_func()
                except Exception as e:
                    logger.error(f"Error in MTM consolidation: {str(e)}")
        except asyncio.CancelledError:
            logger.info("MTM consolidation task cancelled")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in MTM consolidation loop: {str(e)}")
    
    async def _load_priority_map(self) -> None:
        """
        Load priority information for all memories in this tier.
        """
        logger.debug("Loading priority map for MTM tier")
        
        # Clear current map
        self._priority_map = {}
        
        try:
            # Query all memories with priority info
            filters = {"metadata.tags.priority": {"$exists": True}}
            memories = await self._backend.query(filters=filters)
            
            # Build priority map
            for memory_data in memories:
                try:
                    memory_id = memory_data.get("id")
                    tags = memory_data.get("metadata", {}).get("tags", {})
                    
                    if "priority" in tags and memory_id:
                        self._priority_map[memory_id] = tags["priority"]
                except Exception as e:
                    logger.error(f"Error loading priority for memory: {str(e)}")
            
            logger.info(f"Loaded priority information for {len(self._priority_map)} memories")
        except Exception as e:
            logger.error(f"Error loading priority map: {str(e)}")
    
    def get_priority_map(self) -> Dict[str, str]:
        """
        Get a copy of the current priority map.
        
        Returns:
            Dictionary mapping memory IDs to priority levels
        """
        return self._priority_map.copy()
    
    def update_priority(self, memory_id: str, priority: str) -> None:
        """
        Update the priority for a memory.
        
        Args:
            memory_id: The ID of the memory
            priority: Priority level ("high", "medium", or "low")
        """
        self._priority_map[memory_id] = priority
    
    def remove_priority(self, memory_id: str) -> None:
        """
        Remove a memory from the priority map.
        
        Args:
            memory_id: The ID of the memory
        """
        if memory_id in self._priority_map:
            del self._priority_map[memory_id]
