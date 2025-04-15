"""
Base Memory Tier Implementation

This module provides the core BaseMemoryTier class that implements the
MemoryTierInterface and serves as the foundation for all memory tier implementations.
"""

import abc
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from neuroca.memory.backends import BaseStorageBackend, BackendType, MemoryTier as BackendTier
from neuroca.memory.backends.factory import StorageBackendFactory
from neuroca.memory.exceptions import (
    TierInitializationError,
    TierOperationError,
    ItemExistsError,
    ItemNotFoundError,
)
from neuroca.memory.interfaces.memory_tier import MemoryTierInterface
from neuroca.memory.models.memory_item import MemoryItem
# Import SearchResults and MemorySearchOptions
from neuroca.memory.models.search import MemorySearchOptions, MemorySearchResults

from neuroca.memory.tiers.base.helpers import MemoryIdGenerator, MemoryItemCreator
from neuroca.memory.tiers.base.search import TierSearcher
from neuroca.memory.tiers.base.stats import TierStatsManager


logger = logging.getLogger(__name__)


class BaseMemoryTier(MemoryTierInterface, abc.ABC):
    """
    Base class for all memory tiers.
    
    This class implements the MemoryTierInterface and provides common
    functionality for all memory tier implementations.
    
    Subclasses must implement the abstract methods for tier-specific behavior.
    """
    
    def __init__(
        self,
        tier_name: str,
        storage_backend: Optional[BaseStorageBackend] = None,
        backend_type: Optional[BackendType] = None,
        backend_config: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the memory tier.
        
        Args:
            tier_name: Name of the tier ("stm", "mtm", or "ltm")
            storage_backend: Optional existing storage backend to use
            backend_type: Type of backend to create if storage_backend not provided
            backend_config: Configuration for the storage backend
            config: Tier-specific configuration options
        """
        self._tier_name = tier_name
        self._backend = storage_backend
        self._backend_type = backend_type
        self._backend_config = backend_config or {}
        self.config = config or {}
        self.initialized = False
        self._stats = TierStatsManager.create_base_stats()
        
        # Helper instances
        self._id_generator = MemoryIdGenerator()
        self._item_creator = MemoryItemCreator()
        self._searcher = TierSearcher()
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the memory tier.
        
        Args:
            config: Optional additional configuration to merge with the existing config
            
        Raises:
            TierInitializationError: If initialization fails
        """
        if config:
            self.config.update(config)
        
        try:
            # Initialize storage backend if not provided
            if self._backend is None:
                # Use the BackendTier enum for tier-based initialization
                backend_tier = None
                if self._tier_name == "stm":
                    backend_tier = BackendTier.STM
                elif self._tier_name == "mtm":
                    backend_tier = BackendTier.MTM
                elif self._tier_name == "ltm":
                    backend_tier = BackendTier.LTM
                
                # Create the storage backend using the factory
                self._backend = StorageBackendFactory.create_storage(
                    tier=backend_tier,
                    backend_type=self._backend_type,
                    config=self._backend_config,
                )
            
            # Initialize the backend if not already initialized
            if not getattr(self._backend, 'initialized', False):
                await self._backend.initialize()
            
            # Initialize tier-specific components
            await self._initialize_tier()
            
            self.initialized = True
            logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize {self.__class__.__name__}")
            raise TierInitializationError(
                tier_name=self._tier_name,
                message=f"Failed to initialize memory tier: {str(e)}"
            ) from e
    
    async def shutdown(self) -> None:
        """
        Shutdown the memory tier.
        
        This method should release all resources and ensure pending operations
        are completed.
        
        Raises:
            TierOperationError: If shutdown fails
        """
        if not self.initialized:
            logger.warning(f"{self.__class__.__name__} shutdown called but not initialized")
            return
        
        try:
            # Shutdown tier-specific components
            await self._shutdown_tier()
            
            # Shutdown the backend if we created it
            if self._backend is not None and getattr(self._backend, 'initialized', False):
                await self._backend.shutdown()
            
            self.initialized = False
            logger.info(f"{self.__class__.__name__} shutdown successfully")
        except Exception as e:
            logger.exception(f"Failed to shutdown {self.__class__.__name__}")
            raise TierOperationError(
                operation="shutdown",
                tier_name=self._tier_name,
                message=f"Failed to shutdown memory tier: {str(e)}"
            ) from e
    
    @property
    def tier_name(self) -> str:
        """
        Get the name of this memory tier.
        
        Returns:
            The tier name ("stm", "mtm", or "ltm")
        """
        return self._tier_name
    
    #-----------------------------------------------------------------------
    # Core Memory Operations
    #-----------------------------------------------------------------------
    
    async def store(
        self, 
        content: Union[Dict[str, Any], MemoryItem],
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        """
        Store a memory in this tier.
        
        Args:
            content: Memory content to store or MemoryItem object
            metadata: Optional metadata for the memory (only used if content is a Dict)
            memory_id: Optional explicit ID (if not provided, one will be generated)
            
        Returns:
            The memory ID
            
        Raises:
            TierOperationError: If the store operation fails
        """
        self._ensure_initialized()
        TierStatsManager.update_operation_stats(self._stats, "store_count")
        
        try:
            # Handle case where content is actually a MemoryItem
            if isinstance(content, MemoryItem):
                memory_item = content
                memory_id = memory_item.id
            else:
                # Generate memory ID if not provided
                if memory_id is None:
                    memory_id = self._id_generator.generate(content)
                
                # Create memory item from content and metadata
                memory_item = self._item_creator.create(memory_id, content, metadata)
            
            # Apply tier-specific behavior before storage
            await self._pre_store(memory_item)
            
            # Store in backend
            data = memory_item.model_dump()
            await self._backend.create(memory_id, data)
            
            # Apply tier-specific behavior after storage
            await self._post_store(memory_item)
            
            self._stats["items_count"] += 1
            return memory_id
        except ItemExistsError:
            # Propagate backend errors
            raise
        except Exception as e:
            logger.exception(f"Failed to store memory in {self._tier_name} tier")
            raise TierOperationError(
                operation="store",
                tier_name=self._tier_name,
                message=f"Failed to store memory: {str(e)}"
            ) from e
    
    async def batch_store(
        self,
        memories: List[Union[Dict[str, Any], MemoryItem]],
        memory_ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Store multiple memories in this tier.
        
        Args:
            memories: List of memory contents or MemoryItem objects to store
            memory_ids: Optional explicit IDs (if not provided, they will be generated)
            
        Returns:
            List of memory IDs in the same order as the input memories
            
        Raises:
            TierOperationError: If the store operation fails
        """
        self._ensure_initialized()
        TierStatsManager.update_operation_stats(self._stats, "batch_store_count")
        
        # Generate memory IDs if not provided
        if memory_ids is None:
            memory_ids = [None] * len(memories)
        elif len(memory_ids) != len(memories):
            raise ValueError("Number of memory_ids must match number of memories")
        
        # Store each memory and collect IDs
        result_ids = []
        try:
            for i, memory in enumerate(memories):
                memory_id = await self._backend.exists(memory_ids[i]) if memory_ids[i] else False
                
                # If memory already exists with this ID, skip
                if memory_id:
                    result_ids.append(memory_ids[i])
                    continue
                
                # Create memory item if not a MemoryItem already
                if not isinstance(memory, MemoryItem):
                    # Generate memory ID if not provided
                    if memory_ids[i] is None:
                        memory_ids[i] = self._id_generator.generate(memory)
                    
                    # Create memory item
                    memory_item = self._item_creator.create(memory_ids[i], memory)
                else:
                    memory_item = memory
                    if memory_ids[i]:
                        memory_item.id = memory_ids[i]
                
                # Apply tier-specific behavior before storage
                await self._pre_store(memory_item)
                
                # Store in backend
                data = memory_item.model_dump()
                await self._backend.create(memory_item.id, data)
                
                # Apply tier-specific behavior after storage
                await self._post_store(memory_item)
                
                # Update stats
                self._stats["items_count"] += 1
                
                # Add ID to result list
                result_ids.append(memory_item.id)
            
            return result_ids
        except Exception as e:
            logger.exception(f"Failed to batch store memories in {self._tier_name} tier")
            raise TierOperationError(
                operation="batch_store",
                tier_name=self._tier_name,
                message=f"Failed to batch store memories: {str(e)}"
            ) from e
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]: # Changed return type hint
        """
        Retrieve a memory by its ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The MemoryItem object if found, None otherwise # Changed docstring
            
        Raises:
            TierOperationError: If the retrieve operation fails
        """
        self._ensure_initialized()
        TierStatsManager.update_operation_stats(self._stats, "retrieve_count")
        
        try:
            # Retrieve from backend
            data = await self._backend.read(memory_id)
            if data is None:
                return None
            
            # Apply tier-specific behavior
            memory_item = MemoryItem.model_validate(data)
            await self._on_retrieve(memory_item)
            
            # Return the MemoryItem object, not the raw dict
            return memory_item 
        except Exception as e:
            logger.exception(f"Failed to retrieve memory {memory_id} from {self._tier_name} tier")
            raise TierOperationError(
                operation="retrieve",
                tier_name=self._tier_name,
                message=f"Failed to retrieve memory: {str(e)}"
            ) from e
    
    async def update(
        self,
        memory_id: str,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update
            content: New content (if None, keeps existing content)
            metadata: New/updated metadata (if None, keeps existing metadata)
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemNotFoundError: If the memory with the given ID does not exist
            TierOperationError: If the update operation fails
        """
        self._ensure_initialized()
        TierStatsManager.update_operation_stats(self._stats, "update_count")
        
        try:
            # Check if memory exists
            if not await self.exists(memory_id):
                raise ItemNotFoundError(item_id=memory_id, tier=self._tier_name)
            
            # Get existing memory
            data = await self._backend.read(memory_id)
            memory_item = MemoryItem.model_validate(data)
            
            # Apply tier-specific behavior before update
            await self._pre_update(memory_item, content, metadata)
            
            # Update content if provided
            if content is not None:
                memory_item.content.data = content
            
            # Update metadata if provided
            if metadata is not None:
                for key, value in metadata.items():
                    memory_item.metadata.tags[key] = value
            
            # Update timestamp
            memory_item.metadata.updated_at = datetime.now()
            
            # Apply tier-specific behavior after update
            await self._post_update(memory_item)
            
            # Save to backend
            data = memory_item.model_dump()
            return await self._backend.update(memory_id, data)
        except ItemNotFoundError:
            # Propagate backend errors
            raise
        except Exception as e:
            logger.exception(f"Failed to update memory {memory_id} in {self._tier_name} tier")
            raise TierOperationError(
                operation="update",
                tier_name=self._tier_name,
                message=f"Failed to update memory: {str(e)}"
            ) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory by its ID.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            TierOperationError: If the delete operation fails
        """
        self._ensure_initialized()
        TierStatsManager.update_operation_stats(self._stats, "delete_count")
        
        try:
            # Apply tier-specific behavior before deletion
            await self._pre_delete(memory_id)
            
            # Delete from backend
            result = await self._backend.delete(memory_id)
            
            # Apply tier-specific behavior after deletion
            await self._post_delete(memory_id)
            
            if result:
                self._stats["items_count"] = max(0, self._stats["items_count"] - 1)
            
            return result
        except Exception as e:
            logger.exception(f"Failed to delete memory {memory_id} from {self._tier_name} tier")
            raise TierOperationError(
                operation="delete",
                tier_name=self._tier_name,
                message=f"Failed to delete memory: {str(e)}"
            ) from e
    
    async def exists(self, memory_id: str) -> bool:
        """
        Check if a memory exists in this tier.
        
        Args:
            memory_id: The ID of the memory to check
            
        Returns:
            bool: True if the memory exists, False otherwise
            
        Raises:
            TierOperationError: If the exists operation fails
        """
        self._ensure_initialized()
        
        try:
            return await self._backend.exists(memory_id)
        except Exception as e:
            logger.exception(f"Failed to check if memory {memory_id} exists in {self._tier_name} tier")
            raise TierOperationError(
                operation="exists",
                tier_name=self._tier_name,
                message=f"Failed to check if memory exists: {str(e)}"
            ) from e
    
    #-----------------------------------------------------------------------
    # Search and Retrieval
    #-----------------------------------------------------------------------
    
    async def search(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None, # Keep filters as dict for now
        embedding: Optional[List[float]] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> MemorySearchResults: # Changed return type hint
        """
        Search for memories in this tier.
        
        Args:
            query: Optional text query
            filters: Optional metadata filters
            embedding: Optional vector embedding for similarity search
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            SearchResults object containing MemoryItems and metadata # Changed docstring
            
        Raises:
            TierOperationError: If the search operation fails
        """
        self._ensure_initialized()
        TierStatsManager.update_operation_stats(self._stats, "search_count")
        
        try:
            # Apply tier-specific filters
            combined_filters = await self._searcher.apply_tier_filters(self._tier_name, filters)
            
            # Convert query to backend query if needed
            backend_query = await self._searcher.convert_query(query, embedding)
            
            # Perform search
            results = await self._searcher.perform_search(
                self._backend, backend_query, combined_filters, limit, offset
            )
            
            # Apply tier-specific post-processing (assuming it returns list of dicts)
            processed_results_dicts = await self._searcher.post_search(results)

            # Convert dicts to MemoryItem objects
            memory_items = [MemoryItem.model_validate(item_dict) for item_dict in processed_results_dicts]

            # Construct and return SearchResults object
            # Note: total_count might be inaccurate if backend applied limit/offset
            total_count = len(memory_items) # Placeholder, ideally get from backend if possible
            
            # Reconstruct MemorySearchOptions if needed, or pass None/defaults
            search_options = MemorySearchOptions(query=query, filters=filters, limit=limit, offset=offset)

            return MemorySearchResults(
                items=memory_items,
                total_count=total_count,
                options=search_options,
                query=query # Keep original query string
            )
        except Exception as e:
            logger.exception(f"Failed to search memories in {self._tier_name} tier")
            raise TierOperationError(
                operation="search",
                tier_name=self._tier_name,
                message=f"Failed to search memories: {str(e)}"
            ) from e
    
    async def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recently stored or accessed memories.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of recent memories
            
        Raises:
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        try:
            # Use search with recent filters
            filters = {"_meta.updated_at": {"$exists": True}}
            sort_by = "_meta.updated_at"
            ascending = False
            
            # Query the backend directly
            results = await self._backend.query(
                filters=filters,
                sort_by=sort_by,
                ascending=ascending,
                limit=limit,
            )
            
            return results
        except Exception as e:
            logger.exception(f"Failed to get recent memories from {self._tier_name} tier")
            raise TierOperationError(
                operation="get_recent",
                tier_name=self._tier_name,
                message=f"Failed to get recent memories: {str(e)}"
            ) from e
    
    async def get_important(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most important memories based on tier-specific criteria.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of important memories
            
        Raises:
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        try:
            # Different tiers define importance differently, so call the tier-specific method
            return await self._get_important_memories(limit)
        except Exception as e:
            logger.exception(f"Failed to get important memories from {self._tier_name} tier")
            raise TierOperationError(
                operation="get_important",
                tier_name=self._tier_name,
                message=f"Failed to get important memories: {str(e)}"
            ) from e
    
    #-----------------------------------------------------------------------
    # Tier-Specific Operations
    #-----------------------------------------------------------------------
    
    async def mark_accessed(self, memory_id: str) -> bool:
        """
        Mark a memory as accessed, updating its access metrics.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        try:
            # Check if memory exists
            if not await self.exists(memory_id):
                raise ItemNotFoundError(item_id=memory_id, tier=self._tier_name)
            
            # Get existing memory
            data = await self._backend.read(memory_id)
            memory_item = MemoryItem.model_validate(data)
            
            # Update access count and timestamp
            memory_item.metadata.access_count += 1
            memory_item.metadata.last_accessed = datetime.now()
            
            # Apply tier-specific behavior
            await self._on_access(memory_item)
            
            # Save to backend
            data = memory_item.model_dump()
            return await self._backend.update(memory_id, data)
        except ItemNotFoundError:
            # Propagate backend errors
            raise
        except Exception as e:
            logger.exception(f"Failed to mark memory {memory_id} as accessed in {self._tier_name} tier")
            raise TierOperationError(
                operation="mark_accessed",
                tier_name=self._tier_name,
                message=f"Failed to mark memory as accessed: {str(e)}"
            ) from e
    
    async def get_memory_strength(self, memory_id: str) -> float:
        """
        Get the current strength value of a memory.
        
        The meaning of strength varies by tier:
        - STM: Freshness (inverse of decay)
        - MTM: Priority and access frequency
        - LTM: Long-term importance and reinforcement
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            Strength value between 0.0 and 1.0
            
        Raises:
            ItemNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        try:
            # Check if memory exists
            if not await self.exists(memory_id):
                raise ItemNotFoundError(item_id=memory_id, tier=self._tier_name)
            
            # Get existing memory
            data = await self._backend.read(memory_id)
            memory_item = MemoryItem.model_validate(data)
            
            # Calculate tier-specific strength
            return await self._calculate_strength(memory_item)
        except ItemNotFoundError:
            # Propagate backend errors
            raise
        except Exception as e:
            logger.exception(f"Failed to get memory strength for {memory_id} in {self._tier_name} tier")
            raise TierOperationError(
                operation="get_memory_strength",
                tier_name=self._tier_name,
                message=f"Failed to get memory strength: {str(e)}"
            ) from e
    
    async def update_memory_strength(self, memory_id: str, delta: float) -> float:
        """
        Update the strength of a memory.
        
        Args:
            memory_id: The ID of the memory
            delta: Amount to adjust strength by (positive or negative)
            
        Returns:
            New strength value
            
        Raises:
            ItemNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        self._ensure_initialized()
        
        try:
            # Check if memory exists
            if not await self.exists(memory_id):
                raise ItemNotFoundError(item_id=memory_id, tier=self._tier_name)
            
            # Get existing memory
            data = await self._backend.read(memory_id)
            memory_item = MemoryItem.model_validate(data)
            
            # Update tier-specific strength
            new_strength = await self._update_strength(memory_item, delta)
            
            # Save to backend
            data = memory_item.model_dump()
            await self._backend.update(memory_id, data)
            
            return new_strength
        except ItemNotFoundError:
            # Propagate backend errors
            raise
        except Exception as e:
            logger.exception(f"Failed to update memory strength for {memory_id} in {self._tier_name} tier")
            raise TierOperationError(
                operation="update_memory_strength",
                tier_name=self._tier_name,
                message=f"Failed to update memory strength: {str(e)}"
            ) from e
    
    #-----------------------------------------------------------------------
    # Maintenance Operations
    #-----------------------------------------------------------------------
    
    async def cleanup(self) -> int:
        """
        Perform tier-specific cleanup operations.
        
        For example:
        - STM: Remove expired memories
        - MTM: Archive low-priority memories
        - LTM: Compress rarely accessed memories
        
        Returns:
            Number of memories affected
            
        Raises:
            TierOperationError: If the cleanup operation fails
        """
        self._ensure_initialized()
        
        try:
            # Perform tier-specific cleanup
            return await self._perform_cleanup()
        except Exception as e:
            logger.exception(f"Failed to perform cleanup in {self._tier_name} tier")
            raise TierOperationError(
                operation="cleanup",
                tier_name=self._tier_name,
                message=f"Failed to perform cleanup: {str(e)}"
            ) from e
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count memories in this tier, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching memories
            
        Raises:
            TierOperationError: If the count operation fails
        """
        self._ensure_initialized()
        
        try:
            # Apply tier-specific filters
            combined_filters = await self._searcher.apply_tier_filters(self._tier_name, filters)
            
            # Count memories
            return await self._backend.count(combined_filters)
        except Exception as e:
            logger.exception(f"Failed to count memories in {self._tier_name} tier")
            raise TierOperationError(
                operation="count",
                tier_name=self._tier_name,
                message=f"Failed to count memories: {str(e)}"
            ) from e
    
    async def clear(self) -> bool:
        """
        Clear all memories from this tier.
        
        Returns:
            bool: True if the operation was successful
            
        Raises:
            TierOperationError: If the clear operation fails
        """
        self._ensure_initialized()
        
        try:
            # Apply tier-specific behavior before clear
            await self._pre_clear()
            
            # Clear all memories
            result = await self._backend.clear()
            
            # Apply tier-specific behavior after clear
            await self._post_clear()
            
            if result:
                self._stats["items_count"] = 0
            
            return result
        except Exception as e:
            logger.exception(f"Failed to clear memories from {self._tier_name} tier")
            raise TierOperationError(
                operation="clear",
                tier_name=self._tier_name,
                message=f"Failed to clear memories: {str(e)}"
            ) from e
    
    async def get_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics about this memory tier.
        
        Returns:
            Dictionary of statistics
            
        Raises:
            TierOperationError: If the get stats operation fails
        """
        self._ensure_initialized()
        
        try:
            # Get backend stats
            backend_stats = await self._backend.get_stats()
            
            # Get tier-specific stats
            tier_stats = await TierStatsManager.get_tier_stats(self._tier_name, self._backend)
            
            # Merge stats
            stats = {
                **self._stats,
                **tier_stats,
                "tier_name": self._tier_name,
                "backend_stats": backend_stats,
            }
            
            return stats
        except Exception as e:
            logger.exception(f"Failed to get stats for {self._tier_name} tier")
            raise TierOperationError(
                operation="get_stats",
                tier_name=self._tier_name,
                message=f"Failed to get stats: {str(e)}"
            ) from e
    
    #-----------------------------------------------------------------------
    # Helper Methods
    #-----------------------------------------------------------------------
    
    def _ensure_initialized(self) -> None:
        """
        Ensure the tier is initialized before operations.
        
        Raises:
            TierOperationError: If the tier is not initialized
        """
        if not self.initialized:
            raise TierOperationError(
                tier_name=self._tier_name,
                message="Memory tier not initialized. Call initialize() first."
            )
    
    #-----------------------------------------------------------------------
    # Abstract methods that subclasses must implement
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def _initialize_tier(self) -> None:
        """Initialize tier-specific components."""
        pass
    
    @abc.abstractmethod
    async def _shutdown_tier(self) -> None:
        """Shutdown tier-specific components."""
        pass
    
    @abc.abstractmethod
    async def _calculate_strength(self, memory_item: MemoryItem) -> float:
        """
        Calculate the strength of a memory based on tier-specific criteria.
        
        Args:
            memory_item: The memory item
            
        Returns:
            Strength value between 0.0 and 1.0
        """
        pass
    
    @abc.abstractmethod
    async def _update_strength(self, memory_item: MemoryItem, delta: float) -> float:
        """
        Update the strength of a memory based on tier-specific criteria.
        
        Args:
            memory_item: The memory item
            delta: Amount to adjust strength by
            
        Returns:
            New strength value
        """
        pass
    
    @abc.abstractmethod
    async def _get_important_memories(self, limit: int) -> List[Dict[str, Any]]:
        """
        Get the most important memories based on tier-specific criteria.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of important memories
        """
        pass
    
    @abc.abstractmethod
    async def _perform_cleanup(self) -> int:
        """
        Perform tier-specific cleanup operations.
        
        Returns:
            Number of memories affected
        """
        pass
    
    #-----------------------------------------------------------------------
    # Methods with default implementations that subclasses may override
    #-----------------------------------------------------------------------
    
    async def _pre_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior before storing a memory.
        
        Args:
            memory_item: The memory item to be stored
        """
        pass
    
    async def _post_store(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior after storing a memory.
        
        Args:
            memory_item: The stored memory item
        """
        pass
    
    async def _on_retrieve(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior when retrieving a memory.
        
        Args:
            memory_item: The retrieved memory item
        """
        pass
    
    async def _pre_update(
        self,
        memory_item: MemoryItem,
        content: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        """
        Apply tier-specific behavior before updating a memory.
        
        Args:
            memory_item: The memory item to be updated
            content: New content (if None, keeps existing content)
            metadata: New/updated metadata (if None, keeps existing metadata)
        """
        pass
    
    async def _post_update(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior after updating a memory.
        
        Args:
            memory_item: The updated memory item
        """
        pass
    
    async def _pre_delete(self, memory_id: str) -> None:
        """
        Apply tier-specific behavior before deleting a memory.
        
        Args:
            memory_id: The ID of the memory to be deleted
        """
        pass
    
    async def _post_delete(self, memory_id: str) -> None:
        """
        Apply tier-specific behavior after deleting a memory.
        
        Args:
            memory_id: The ID of the deleted memory
        """
        pass
    
    async def _on_access(self, memory_item: MemoryItem) -> None:
        """
        Apply tier-specific behavior when accessing a memory.
        
        Args:
            memory_item: The accessed memory item
        """
        pass
    
    async def _pre_clear(self) -> None:
        """
        Apply tier-specific behavior before clearing all memories.
        """
        pass
    
    async def _post_clear(self) -> None:
        """
        Apply tier-specific behavior after clearing all memories.
        """
        pass
