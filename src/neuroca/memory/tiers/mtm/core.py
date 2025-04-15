"""
Medium-Term Memory (MTM) Tier Implementation

This module provides the implementation of the Medium-Term Memory (MTM) tier,
which handles memories with priority-based management and selective retention.
This implementation uses a modular approach with specialized components to
handle different aspects of the MTM functionality.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Callable

from neuroca.memory.backends import BackendType
from neuroca.memory.backends.factory import StorageBackendFactory
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.tiers.base import BaseMemoryTier
from neuroca.memory.tiers.mtm.components import (
    MTMLifecycle,
    MTMPriority,
    MTMConsolidation,
    MTMStrengthCalculator,
    MTMOperations,
    MTMPromotion,
)


logger = logging.getLogger(__name__)


class MediumTermMemoryTier(BaseMemoryTier):
    """
    Medium-Term Memory (MTM) Tier
    
    This tier implements memory storage with priority-based management and
    selective retention. Memories in this tier are managed based on their
    importance, access frequency, and explicit priority settings.
    
    Key features:
    - Priority-based memory management
    - Access frequency and recency tracking
    - Selective retention based on memory importance
    - Periodic consolidation of memories
    - Promotion of important memories to LTM
    
    The implementation follows the Apex Modular Organization Standard (AMOS)
    by decomposing functionality into specialized component classes:
    - MTMLifecycle: Handles initialization, shutdown, and lifecycle processes
    - MTMPriority: Manages priority-based memory organization
    - MTMConsolidation: Handles capacity management and memory cleanup
    - MTMStrengthCalculator: Calculates and updates memory strength
    - MTMOperations: Manages core memory operations
    - MTMPromotion: Handles promotion of memories to LTM
    """
    
    DEFAULT_MAX_CAPACITY = 1000  # Default maximum number of memories
    DEFAULT_PRIORITY_LEVELS = {"high": 3, "medium": 2, "low": 1}
    DEFAULT_CONSOLIDATION_INTERVAL = 3600  # Default: 1 hour
    DEFAULT_MIN_ACCESS_THRESHOLD = 3  # Minimum access count for high priority
    
    # Priority score weights
    DEFAULT_PRIORITY_WEIGHT = 0.4
    DEFAULT_RECENCY_WEIGHT = 0.3
    DEFAULT_FREQUENCY_WEIGHT = 0.3
    
    def __init__(
        self,
        storage_backend=None,
        backend_type: Optional[BackendType] = None,
        backend_config: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the MTM tier.
        
        Args:
            storage_backend: Optional existing storage backend to use
            backend_type: Type of backend to create if storage_backend not provided
            backend_config: Configuration for the storage backend
            config: Tier-specific configuration options
        """
        super().__init__(
            tier_name="mtm",
            storage_backend=storage_backend,
            backend_type=backend_type,
            backend_config=backend_config,
            config=config or {},
        )
        
        # Default configuration
        self.config.setdefault("max_capacity", self.DEFAULT_MAX_CAPACITY)
        self.config.setdefault("priority_levels", self.DEFAULT_PRIORITY_LEVELS.copy())
        self.config.setdefault("consolidation_interval", self.DEFAULT_CONSOLIDATION_INTERVAL)
        self.config.setdefault("min_access_threshold", self.DEFAULT_MIN_ACCESS_THRESHOLD)
        
        # Priority weights
        self.config.setdefault("priority_weight", self.DEFAULT_PRIORITY_WEIGHT)
        self.config.setdefault("recency_weight", self.DEFAULT_RECENCY_WEIGHT)
        self.config.setdefault("frequency_weight", self.DEFAULT_FREQUENCY_WEIGHT)
        
        # Create components
        self._lifecycle = MTMLifecycle(self._tier_name)
        self._priority = MTMPriority(self._tier_name)
        self._consolidation = MTMConsolidation(self._tier_name)
        self._strength_calculator = MTMStrengthCalculator(self._tier_name)
        self._promotion = MTMPromotion(self._tier_name)
        self._operations = MTMOperations(self._tier_name)
    
    async def _initialize_tier(self) -> None:
        """Initialize tier-specific components."""
        logger.info(f"Initializing MTM tier with capacity: {self.config['max_capacity']}")
        
        # Configure components
        # 1. Configure strength calculator (no dependencies)
        self._strength_calculator.configure(
            config=self.config,
        )
        
        # 2. Configure lifecycle with consolidation function
        await self._lifecycle.initialize(
            backend=self._backend,
            consolidation_func=self._consolidation.perform_consolidation,
            config=self.config,
        )
        
        # 3. Configure priority with lifecycle and update function
        self._priority.configure(
            lifecycle=self._lifecycle,
            update_func=self.update,
            config=self.config,
        )
        
        # 4. Configure consolidation with backend, priority manager, and delete function
        self._consolidation.configure(
            backend=self._backend,
            priority_manager=self._priority,
            delete_func=self.delete,
            config=self.config,
        )
        
        # 5. Configure promotion manager
        self._promotion.configure(
            backend=self._backend,
            config=self.config,
        )
        
        # 6. Configure operations with dependencies
        self._operations.configure(
            priority_manager=self._priority,
            strength_calculator=self._strength_calculator,
            promotion_manager=self._promotion,
            config=self.config,
        )
        
        logger.info("MTM tier initialization complete")
    
    async def _shutdown_tier(self) -> None:
        """Shutdown tier-specific components."""
        logger.info("Shutting down MTM tier")
        
        # Shutdown lifecycle component (manages background tasks)
        await self._lifecycle.shutdown()
        
        logger.info("MTM tier shutdown complete")
    
    async def _pre_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior before storing a memory.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Delegate to operations component
        self._operations.process_pre_store(memory_item)
        
        # Delegate to priority component
        self._priority.process_pre_store(memory_item)
    
    async def _post_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior after storing a memory.
        
        Args:
            memory_item: The stored memory item
        """
        # Delegate to operations component
        self._operations.process_post_store(memory_item)
        
        # Delegate to priority component
        self._priority.process_post_store(memory_item)
    
    async def _pre_delete(self, memory_id: str) -> None:
        """
        Apply tier-specific behavior before deleting a memory.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Delegate to operations component
        self._operations.process_pre_delete(memory_id)
        
        # Delegate to priority component
        self._priority.process_pre_delete(memory_id)
    
    async def _post_delete(self, memory_id: str) -> None:
        """
        Apply tier-specific behavior after deleting a memory.
        
        Args:
            memory_id: The ID of the deleted memory
        """
        # Delegate to operations component
        self._operations.process_post_delete(memory_id)
    
    async def _on_retrieve(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior when retrieving a memory.
        
        Args:
            memory_item: The retrieved memory item
        """
        # Delegate to operations component
        self._operations.process_on_retrieve(memory_item)
    
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
        # Delegate to consolidation component
        return await self._consolidation.perform_consolidation()
    
    #-----------------------------------------------------------------------
    # MTM-specific methods
    #-----------------------------------------------------------------------
    
    async def set_priority(self, memory_id: str, priority: str) -> bool:
        """
        Set the priority of a MTM memory.
        
        Args:
            memory_id: The ID of the memory
            priority: Priority value ("high", "medium", or "low")
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            ValueError: If the priority is invalid
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to priority component
        return await self._priority.set_priority(memory_id, priority)
    
    async def get_priority(self, memory_id: str) -> Optional[str]:
        """
        Get the priority of a memory.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            Priority value or None if not set
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        # Get memory
        data = await self.retrieve(memory_id)
        if data is None:
            return None
        
        memory_item = MemoryItem.model_validate(data)
        
        # Get priority
        return memory_item.metadata.tags.get("priority")
    
    async def get_promotion_candidates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memories that are candidates for promotion to LTM.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of memory candidates for promotion
            
        Raises:
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to promotion component
        return await self._promotion.get_promotion_candidates(limit)
