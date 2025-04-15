"""
Short-Term Memory (STM) Tier Implementation

This module provides the implementation of the Short-Term Memory (STM) tier,
which handles temporary memories with automatic decay and expiration. This
implementation uses a modular approach with specialized components to handle
different aspects of the STM functionality.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Callable

from neuroca.memory.backends import BackendType
from neuroca.memory.backends.factory import StorageBackendFactory
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.tiers.base import BaseMemoryTier
from neuroca.memory.tiers.stm.components import (
    STMLifecycle,
    STMExpiry,
    STMCleanup,
    STMStrengthCalculator,
    STMOperations,
)


logger = logging.getLogger(__name__)


class ShortTermMemoryTier(BaseMemoryTier):
    """
    Short-Term Memory (STM) Tier
    
    This tier implements memory storage with automatic decay and expiration.
    Memories in this tier have a limited lifespan and will automatically
    expire after a configurable time period.
    
    Key features:
    - TTL (time-to-live) settings for memories
    - Strength decay over time
    - Automatic cleanup of expired memories
    - Freshness-based importance
    
    The implementation follows the Apex Modular Organization Standard (AMOS)
    by decomposing functionality into specialized component classes:
    - STMLifecycle: Handles initialization, shutdown, and lifecycle processes
    - STMExpiry: Manages TTL and expiry functionality
    - STMCleanup: Handles cleaning up expired memories
    - STMStrengthCalculator: Calculates and updates memory strength
    - STMOperations: Manages core memory operations
    """
    
    DEFAULT_TTL_SECONDS = 3600  # Default: 1 hour
    DEFAULT_CLEANUP_INTERVAL = 300  # Default: 5 minutes
    DEFAULT_DECAY_RATE = 0.05  # Default strength loss per minute
    
    def __init__(
        self,
        storage_backend=None,
        backend_type: Optional[BackendType] = None,
        backend_config: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the STM tier.
        
        Args:
            storage_backend: Optional existing storage backend to use
            backend_type: Type of backend to create if storage_backend not provided
            backend_config: Configuration for the storage backend
            config: Tier-specific configuration options
        """
        super().__init__(
            tier_name="stm",
            storage_backend=storage_backend,
            backend_type=backend_type,
            backend_config=backend_config,
            config=config or {},
        )
        
        # Default configuration
        self.config.setdefault("ttl_seconds", self.DEFAULT_TTL_SECONDS)
        self.config.setdefault("cleanup_interval", self.DEFAULT_CLEANUP_INTERVAL)
        self.config.setdefault("decay_rate", self.DEFAULT_DECAY_RATE)
        
        # Create components
        self._lifecycle = STMLifecycle(self._tier_name)
        self._expiry = STMExpiry(self._tier_name)
        self._cleanup = STMCleanup(self._tier_name)
        self._strength_calculator = STMStrengthCalculator(self._tier_name)
        self._operations = STMOperations(self._tier_name)
    
    async def _initialize_tier(self) -> None:
        """Initialize tier-specific components."""
        logger.info(f"Initializing STM tier with TTL: {self.config['ttl_seconds']} seconds")
        
        # Configure components
        # 1. Configure expiry first (no dependencies)
        self._strength_calculator.configure(
            config=self.config,
        )
        
        # 2. Configure lifecycle with cleanup function
        await self._lifecycle.initialize(
            backend=self._backend,
            cleanup_func=self._cleanup.perform_cleanup,
            config=self.config,
        )
        
        # 3. Configure expiry with lifecycle and update function
        self._expiry.configure(
            lifecycle=self._lifecycle,
            update_func=self.update,
            config=self.config,
        )
        
        # 4. Configure cleanup with backend, expiry, and delete function
        self._cleanup.configure(
            backend=self._backend,
            expiry_manager=self._expiry,
            delete_func=self.delete,
        )
        
        # 5. Configure operations with dependencies
        self._operations.configure(
            expiry_manager=self._expiry,
            strength_calculator=self._strength_calculator,
            config=self.config,
        )
        
        logger.info("STM tier initialization complete")
    
    async def _shutdown_tier(self) -> None:
        """Shutdown tier-specific components."""
        logger.info("Shutting down STM tier")
        
        # Shutdown lifecycle component (manages background tasks)
        await self._lifecycle.shutdown()
        
        logger.info("STM tier shutdown complete")
    
    async def _pre_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior before storing a memory.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Delegate to operations component
        self._operations.process_pre_store(memory_item)
        
        # Delegate to expiry component
        self._expiry.process_pre_store(memory_item)
    
    async def _post_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior after storing a memory.
        
        Args:
            memory_item: The stored memory item
        """
        # Delegate to operations component
        self._operations.process_post_store(memory_item)
        
        # Delegate to expiry component
        self._expiry.process_post_store(memory_item)
    
    async def _pre_delete(self, memory_id: str) -> None:
        """
        Apply tier-specific behavior before deleting a memory.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Delegate to operations component
        self._operations.process_pre_delete(memory_id)
    
    async def _on_retrieve(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior when retrieving a memory.
        
        Args:
            memory_item: The retrieved memory item
        """
        # Delegate to operations component
        self._operations.process_on_retrieve(memory_item)
        
        # Delegate to expiry component
        self._expiry.process_on_retrieve(memory_item)
    
    async def _on_access(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior when accessing a memory.
        
        Args:
            memory_item: The accessed memory item
        """
        # Delegate to operations component
        self._operations.process_on_access(memory_item)
    
    async def _pre_update(
        self,
        memory_item: MemoryItem,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Apply tier-specific behavior before updating a memory.
        
        Args:
            memory_item: The memory item to be updated
            content: New content (if None, keeps existing content)
            metadata: New metadata (if None, keeps existing metadata)
        """
        # Delegate to operations component
        self._operations.process_pre_update(memory_item, content, metadata)
    
    async def _post_update(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior after updating a memory.
        
        Args:
            memory_item: The updated memory item
        """
        # Delegate to operations component
        self._operations.process_post_update(memory_item)
    
    async def _calculate_strength(self, memory_item: MemoryItem) -> float:
        """
        Calculate the strength of a memory based on tier-specific criteria.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Strength value between 0.0 and 1.0
        """
        # Delegate to strength calculator component
        return await self._strength_calculator.calculate_strength(memory_item)
    
    async def _update_strength(self, memory_item: MemoryItem, delta: float) -> float:
        """
        Update the strength of a memory based on tier-specific criteria.
        
        Args:
            memory_item: The memory item
            delta: Amount to adjust strength by
            
        Returns:
            New strength value
        """
        # Delegate to strength calculator component
        return await self._strength_calculator.update_strength(memory_item, delta)
    
    async def _get_important_memories(self, limit: int) -> List[Dict[str, Any]]:
        """
        Get the most important memories based on tier-specific criteria.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of important memories
        """
        # Delegate to operations component
        return await self._operations.get_important_memories(
            query_func=self._backend.query,
            limit=limit,
        )
    
    async def _perform_cleanup(self) -> int:
        """
        Perform tier-specific cleanup operations.
        
        Returns:
            Number of memories affected
        """
        # Delegate to cleanup component
        return await self._cleanup.perform_cleanup()
    
    #-----------------------------------------------------------------------
    # STM-specific methods
    #-----------------------------------------------------------------------
    
    async def set_expiry(self, memory_id: str, ttl_seconds: int) -> bool:
        """
        Set a time-to-live (TTL) for a STM memory.
        
        Args:
            memory_id: The ID of the memory
            ttl_seconds: TTL in seconds
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            ValueError: If TTL is invalid
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to expiry component
        return await self._expiry.set_expiry(memory_id, ttl_seconds)
    
    async def get_expiry(self, memory_id: str) -> Optional[float]:
        """
        Get the expiry time for a memory.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            Expiry time in seconds since epoch, or None if not set
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        # Get memory
        data = await self.retrieve(memory_id)
        if data is None:
            return None
        
        memory_item = MemoryItem.model_validate(data)
        
        # Get expiry time from metadata
        return memory_item.metadata.tags.get("expiry_time")
    
    async def get_ttl(self, memory_id: str) -> Optional[int]:
        """
        Get the TTL for a memory.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            TTL in seconds, or None if not set
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        # Get memory
        data = await self.retrieve(memory_id)
        if data is None:
            return None
        
        memory_item = MemoryItem.model_validate(data)
        
        # Get TTL from metadata
        return memory_item.metadata.tags.get("ttl_seconds")
    
    async def get_time_remaining(self, memory_id: str) -> Optional[float]:
        """
        Get the time remaining before a memory expires.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            Time remaining in seconds, or None if not set
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        # Get memory
        data = await self.retrieve(memory_id)
        if data is None:
            return None
        
        memory_item = MemoryItem.model_validate(data)
        
        # Delegate to expiry component
        return await self._expiry.get_time_remaining(memory_item)
    
    async def get_expiry_count(self) -> int:
        """
        Get the count of memories that have an expiry time set.
        
        Returns:
            Count of memories with expiry
        """
        expiry_map = self._lifecycle.get_expiry_map()
        return len(expiry_map)
    
    async def get_expired_count(self) -> int:
        """
        Get the count of currently expired memories.
        
        Returns:
            Count of expired memories
        """
        return await self._cleanup.get_expired_count()
