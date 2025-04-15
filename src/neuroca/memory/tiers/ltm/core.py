"""
Long-Term Memory (LTM) Tier Implementation

This module provides the implementation of the Long-Term Memory (LTM) tier,
which handles persistent memories with semantic relationships and structure.
This implementation uses a modular approach with specialized components to
handle different aspects of the LTM functionality.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Callable

from neuroca.memory.backends import BackendType
from neuroca.memory.backends.factory import StorageBackendFactory
from neuroca.memory.models.memory_item import MemoryItem, MemoryStatus
from neuroca.memory.tiers.base import BaseMemoryTier
from neuroca.memory.tiers.ltm.components import (
    LTMLifecycle,
    LTMRelationship,
    LTMCategory,
    LTMMaintenance,
    LTMStrengthCalculator,
    LTMOperations,
)


logger = logging.getLogger(__name__)


class LongTermMemoryTier(BaseMemoryTier):
    """
    Long-Term Memory (LTM) Tier
    
    This tier implements memory storage with permanent retention, semantic
    relationships, and organization. Memories in this tier are stored indefinitely
    and are organized with relationships and categories.
    
    Key features:
    - Permanent storage with no automatic decay
    - Semantic relationships between memories
    - Advanced search capabilities
    - Categories and tagging for organization
    
    The implementation follows the Apex Modular Organization Standard (AMOS)
    by decomposing functionality into specialized component classes:
    - LTMLifecycle: Handles initialization, shutdown, and lifecycle processes
    - LTMRelationship: Manages memory connections and relationship queries
    - LTMCategory: Handles categorization and organization of memories
    - LTMMaintenance: Performs system maintenance and health operations
    - LTMStrengthCalculator: Calculates memory strength based on multiple factors
    - LTMOperations: Manages core memory operations
    """
    
    DEFAULT_RELATIONSHIP_TYPES = {
        "semantic": "Semantic relationship based on content similarity",
        "causal": "One memory caused or led to another",
        "temporal": "Memories occurred close in time",
        "spatial": "Memories occurred in the same location",
        "associative": "Memories are associated through shared context",
        "hierarchical": "One memory is a part or subset of another",
        "contradictory": "Memories contain contradictory information",
    }
    DEFAULT_MAINTENANCE_INTERVAL = 86400  # Default: 24 hours
    DEFAULT_MIN_RELATIONSHIP_STRENGTH = 0.3  # Minimum relationship strength
    
    def __init__(
        self,
        storage_backend=None,
        backend_type: Optional[BackendType] = None,
        backend_config: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the LTM tier.
        
        Args:
            storage_backend: Optional existing storage backend to use
            backend_type: Type of backend to create if storage_backend not provided
            backend_config: Configuration for the storage backend
            config: Tier-specific configuration options
        """
        super().__init__(
            tier_name="ltm",
            storage_backend=storage_backend,
            backend_type=backend_type,
            backend_config=backend_config,
            config=config or {},
        )
        
        # Default configuration
        self.config.setdefault("relationship_types", self.DEFAULT_RELATIONSHIP_TYPES)
        self.config.setdefault("maintenance_interval", self.DEFAULT_MAINTENANCE_INTERVAL)
        self.config.setdefault("min_relationship_strength", self.DEFAULT_MIN_RELATIONSHIP_STRENGTH)
        
        # Create components
        self._lifecycle = LTMLifecycle(self._tier_name)
        self._relationship = LTMRelationship(self._tier_name)
        self._category = LTMCategory(self._tier_name)
        self._maintenance = LTMMaintenance(self._tier_name)
        self._strength_calculator = LTMStrengthCalculator(self._tier_name)
        self._operations = LTMOperations(self._tier_name)
    
    async def _initialize_tier(self) -> None:
        """Initialize tier-specific components."""
        logger.info(f"Initializing LTM tier with {len(self.config['relationship_types'])} relationship types")
        
        # Configure components - order matters due to dependencies
        
        # 1. Configure strength calculator with lifecycle
        self._strength_calculator.configure(
            lifecycle=self._lifecycle,
            config=self.config,
        )
        
        # 2. Configure lifecycle with maintenance function
        await self._lifecycle.initialize(
            backend=self._backend,
            maintenance_func=self._maintenance.perform_maintenance,
            config=self.config,
        )
        
        # 3. Configure relationship manager
        self._relationship.configure(
            lifecycle=self._lifecycle,
            backend=self._backend,
            update_func=self.update,
            config=self.config,
        )
        
        # 4. Configure category manager
        self._category.configure(
            lifecycle=self._lifecycle,
            backend=self._backend,
            update_func=self.update,
            config=self.config,
        )
        
        # 5. Configure maintenance manager with component dependencies
        self._maintenance.configure(
            backend=self._backend,
            lifecycle=self._lifecycle,
            relationship_manager=self._relationship,
            category_manager=self._category,
            config=self.config,
        )
        
        # 6. Configure operations with component dependencies
        self._operations.configure(
            category_manager=self._category,
            relationship_manager=self._relationship,
            strength_calculator=self._strength_calculator,
            config=self.config,
        )
        
        logger.info("LTM tier initialization complete")
    
    async def _shutdown_tier(self) -> None:
        """Shutdown tier-specific components."""
        logger.info("Shutting down LTM tier")
        
        # Shutdown lifecycle component (manages background tasks)
        await self._lifecycle.shutdown()
        
        logger.info("LTM tier shutdown complete")
    
    async def _pre_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior before storing a memory.
        
        Args:
            memory_item: The memory item to be stored
        """
        # Delegate to operations component
        self._operations.process_pre_store(memory_item)
        
        # Delegate to relationship component
        self._relationship.process_on_store(memory_item)
        
        # Delegate to category component
        self._category.process_on_store(memory_item)
    
    async def _post_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior after storing a memory.
        
        Args:
            memory_item: The stored memory item
        """
        # Delegate to operations component
        self._operations.process_post_store(memory_item)
        
        # Delegate to category component
        self._category.process_post_store(memory_item)
    
    async def _pre_delete(self, memory_id: str) -> None:
        """
        Apply tier-specific behavior before deleting a memory.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        # Delegate to operations component
        self._operations.process_pre_delete(memory_id)
        
        # Delegate to relationship component
        self._relationship.process_pre_delete(memory_id)
        
        # Delegate to category component
        self._category.process_pre_delete(memory_id)
    
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
        # Delegate to maintenance component
        results = await self._maintenance.perform_maintenance()
        return results.get("updated_memories", 0)
    
    #-----------------------------------------------------------------------
    # LTM-specific methods for relationship management
    #-----------------------------------------------------------------------
    
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        strength: float = 0.5,
        bidirectional: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a relationship between two LTM memories.
        
        Args:
            source_id: ID of the source memory
            target_id: ID of the target memory
            relationship_type: Type of relationship
            strength: Relationship strength (0-1)
            bidirectional: Whether to create the inverse relationship
            metadata: Optional relationship metadata
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If either memory does not exist
            ValueError: If the relationship type is invalid
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to relationship component
        return await self._relationship.add_relationship(
            memory_id=source_id,
            related_id=target_id,
            relationship_type=relationship_type,
            strength=strength,
            bidirectional=bidirectional
        )
    
    async def remove_relationship(
        self,
        source_id: str,
        target_id: str,
        bidirectional: bool = True,
    ) -> bool:
        """
        Remove a relationship between two memories.
        
        Args:
            source_id: ID of the source memory
            target_id: ID of the target memory
            bidirectional: Whether to remove the inverse relationship
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If either memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to relationship component
        return await self._relationship.remove_relationship(
            memory_id=source_id,
            related_id=target_id,
            bidirectional=bidirectional
        )
    
    async def get_related_memories(
        self,
        memory_id: str,
        relationship_type: Optional[str] = None,
        min_strength: float = 0.0,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get memories related to a specific memory.
        
        Args:
            memory_id: ID of the memory
            relationship_type: Optional specific relationship type
            min_strength: Minimum relationship strength
            limit: Maximum number of results to return
            
        Returns:
            List of related memories
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to relationship component
        return await self._relationship.get_related_memories(
            memory_id=memory_id,
            relationship_type=relationship_type,
            min_strength=min_strength,
            limit=limit
        )
    
    async def get_relationship_types(self) -> Dict[str, str]:
        """
        Get all supported relationship types with descriptions.
        
        Returns:
            Dictionary mapping relationship types to their descriptions
        """
        # Get relationship types from component
        return self._relationship.RELATIONSHIP_TYPES.copy()
    
    #-----------------------------------------------------------------------
    # LTM-specific methods for category management
    #-----------------------------------------------------------------------
    
    async def add_to_category(self, memory_id: str, category: str) -> bool:
        """
        Add a memory to a category.
        
        Args:
            memory_id: ID of the memory
            category: Category name
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to category component
        return await self._category.add_to_category(memory_id, category)
    
    async def remove_from_category(self, memory_id: str, category: str) -> bool:
        """
        Remove a memory from a category.
        
        Args:
            memory_id: ID of the memory
            category: Category name
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to category component
        return await self._category.remove_from_category(memory_id, category)
    
    async def set_categories(self, memory_id: str, categories: List[str]) -> bool:
        """
        Set the categories for a memory.
        
        Args:
            memory_id: ID of the memory
            categories: List of categories
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to category component
        return await self._category.set_categories(memory_id, categories)
    
    async def get_categories(self, memory_id: str) -> List[str]:
        """
        Get the categories for a memory.
        
        Args:
            memory_id: ID of the memory
            
        Returns:
            List of categories
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to category component
        return await self._category.get_categories(memory_id)
    
    async def get_all_categories(self) -> Dict[str, int]:
        """
        Get all categories and the number of memories in each.
        
        Returns:
            Dictionary mapping categories to memory counts
            
        Raises:
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to category component
        return await self._category.get_all_categories()
    
    async def get_memories_by_category(
        self,
        category: str,
        limit: int = 10,
        importance_order: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get memories in a specific category.
        
        Args:
            category: The category to query
            limit: Maximum number of memories to return
            importance_order: Whether to order by importance
            
        Returns:
            List of memories in the category
            
        Raises:
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to category component
        return await self._category.get_memories_by_category(
            category=category,
            limit=limit,
            importance_order=importance_order
        )
    
    #-----------------------------------------------------------------------
    # LTM-specific methods for maintenance
    #-----------------------------------------------------------------------
    
    async def get_maintenance_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the LTM tier for maintenance reporting.
        
        Returns:
            Dictionary with statistics
            
        Raises:
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        # Delegate to maintenance component
        return await self._maintenance.get_maintenance_stats()
