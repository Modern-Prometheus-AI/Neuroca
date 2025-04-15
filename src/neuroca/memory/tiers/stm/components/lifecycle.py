"""
STM Lifecycle Management

This module provides the STMLifecycle class which handles initialization,
shutdown, and related lifecycle operations for the Short-Term Memory tier.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Set, Callable

from neuroca.memory.backends import BaseStorageBackend
from neuroca.memory.models.memory_item import MemoryItem


logger = logging.getLogger(__name__)


class STMLifecycle:
    """
    Manages lifecycle operations for the Short-Term Memory tier.
    
    This class handles initialization, shutdown, and related tasks like
    loading the expiry map and starting background tasks.
    """
    
    def __init__(self, tier_name: str):
        """
        Initialize the lifecycle manager.
        
        Args:
            tier_name: The name of the tier (always "stm" for this class)
        """
        self._tier_name = tier_name
        self._cleanup_task = None
        self._expiry_map: Dict[str, float] = {}  # memory_id -> expiry timestamp
        self._backend = None
        self._cleanup_func = None
        self._cleanup_interval = 300  # Default: 5 minutes
    
    async def initialize(self, backend: BaseStorageBackend, cleanup_func: Callable, config: Dict[str, Any]) -> None:
        """
        Initialize the STM tier.
        
        Args:
            backend: The storage backend to use
            cleanup_func: Function to call for cleaning up expired memories
            config: Configuration options
        """
        logger.info(f"Initializing STM tier lifecycle with {config.get('ttl_seconds', 3600)} TTL")
        
        self._backend = backend
        self._cleanup_func = cleanup_func
        
        # Get configuration options
        self._cleanup_interval = config.get("cleanup_interval", 300)
        
        # Load existing expiry information
        await self._load_expiry_map()
        
        # Start cleanup task
        self._start_cleanup_task()
        
        logger.info("STM lifecycle initialized")
    
    async def shutdown(self) -> None:
        """
        Shutdown the STM tier lifecycle components.
        """
        logger.info("Shutting down STM tier lifecycle")
        
        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("STM lifecycle shutdown complete")
    
    def _start_cleanup_task(self) -> None:
        """
        Start the background cleanup task.
        """
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.debug("Started STM cleanup task")
    
    async def _cleanup_loop(self) -> None:
        """
        Background task for periodically cleaning up expired memories.
        """
        logger.info(f"Starting STM cleanup loop with interval: {self._cleanup_interval} seconds")
        
        try:
            while True:
                # Wait for the next cleanup interval
                await asyncio.sleep(self._cleanup_interval)
                
                # Perform cleanup
                try:
                    if self._cleanup_func:
                        await self._cleanup_func()
                except Exception as e:
                    logger.error(f"Error in STM cleanup: {str(e)}")
        except asyncio.CancelledError:
            logger.info("STM cleanup task cancelled")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in STM cleanup loop: {str(e)}")
    
    async def _load_expiry_map(self) -> None:
        """
        Load expiry information for all memories in this tier.
        """
        logger.debug("Loading expiry map for STM tier")
        
        # Clear current map
        self._expiry_map = {}
        
        try:
            # Query all memories with expiry_time
            filters = {"metadata.tags.expiry_time": {"$exists": True}}
            memories = await self._backend.query(filters=filters)
            
            # Build expiry map
            for memory_data in memories:
                try:
                    memory_item = MemoryItem.model_validate(memory_data)
                    if "expiry_time" in memory_item.metadata.tags:
                        self._expiry_map[memory_item.id] = memory_item.metadata.tags["expiry_time"]
                except Exception as e:
                    logger.error(f"Error loading expiry for memory: {str(e)}")
            
            logger.info(f"Loaded expiry information for {len(self._expiry_map)} memories")
        except Exception as e:
            logger.error(f"Error loading expiry map: {str(e)}")
    
    def get_expiry_map(self) -> Dict[str, float]:
        """
        Get a copy of the current expiry map.
        
        Returns:
            Dictionary mapping memory IDs to expiry timestamps
        """
        return self._expiry_map.copy()
    
    def update_expiry(self, memory_id: str, expiry_time: float) -> None:
        """
        Update the expiry time for a memory.
        
        Args:
            memory_id: The ID of the memory
            expiry_time: Expiry timestamp (seconds since epoch)
        """
        self._expiry_map[memory_id] = expiry_time
    
    def remove_expiry(self, memory_id: str) -> None:
        """
        Remove a memory from the expiry map.
        
        Args:
            memory_id: The ID of the memory
        """
        if memory_id in self._expiry_map:
            del self._expiry_map[memory_id]
