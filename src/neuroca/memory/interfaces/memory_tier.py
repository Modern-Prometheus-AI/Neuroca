"""
Memory Tier Interface

This module defines the abstract interface for memory tiers in the Neuroca memory system.
Memory tiers represent the different layers of storage with specific behaviors:

- Short-Term Memory (STM): Temporary storage with automatic decay
- Medium-Term Memory (MTM): Intermediate storage with prioritization
- Long-Term Memory (LTM): Permanent storage with semantic relationships

Each tier implementation uses one or more storage backends, while adding
tier-specific behaviors, policies, and constraints.
"""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


class MemoryTierInterface(abc.ABC):
    """
    Abstract Base Class defining the interface for all memory tiers.
    
    Implementations of this interface provide tier-specific behavior for
    different memory types (STM, MTM, LTM). They use storage backends for
    persistence but add tier-specific behaviors, policies, and constraints.
    
    Memory tiers are responsible for:
    1. Tier-specific storage policies
    2. Tier-appropriate retrieval behavior
    3. Tier-specific metadata management
    4. Tier-level access patterns
    
    They are NOT responsible for:
    1. Cross-tier operations (consolidation, promotion)
    2. Global memory operations
    3. Direct database/storage interactions
    """

    @abc.abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the memory tier.
        
        Args:
            config: Configuration options for the tier
            
        Raises:
            TierInitializationError: If initialization fails
        """
        pass
    
    @abc.abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the memory tier gracefully.
        
        This method should release all resources and ensure
        any pending operations are completed.
        
        Raises:
            TierOperationError: If shutdown operation fails
        """
        pass
    
    @property
    @abc.abstractmethod
    def tier_name(self) -> str:
        """
        Get the name of this memory tier.
        
        Returns:
            The tier name ("stm", "mtm", or "ltm")
        """
        pass
    
    #-----------------------------------------------------------------------
    # Core Memory Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def store(
        self, 
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        """
        Store a memory in this tier.
        
        Args:
            content: Memory content to store
            metadata: Optional metadata for the memory
            memory_id: Optional explicit ID (if not provided, one will be generated)
            
        Returns:
            The memory ID
            
        Raises:
            TierOperationError: If the store operation fails
        """
        pass
    
    @abc.abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory by its ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The memory data if found, None otherwise
            
        Raises:
            TierOperationError: If the retrieve operation fails
        """
        pass
    
    @abc.abstractmethod
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
            MemoryNotFoundError: If the memory with the given ID does not exist
            TierOperationError: If the update operation fails
        """
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    #-----------------------------------------------------------------------
    # Search and Retrieval
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search for memories in this tier.
        
        Args:
            query: Optional text query
            filters: Optional metadata filters
            embedding: Optional vector embedding for similarity search
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of memories matching the search criteria
            
        Raises:
            TierOperationError: If the search operation fails
        """
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    #-----------------------------------------------------------------------
    # Tier-Specific Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def mark_accessed(self, memory_id: str) -> bool:
        """
        Mark a memory as accessed, updating its access metrics.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        pass
    
    @abc.abstractmethod
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
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        pass
    
    @abc.abstractmethod
    async def update_memory_strength(self, memory_id: str, delta: float) -> float:
        """
        Update the strength of a memory.
        
        Args:
            memory_id: The ID of the memory
            delta: Amount to adjust strength by (positive or negative)
            
        Returns:
            New strength value
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Maintenance Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    async def clear(self) -> bool:
        """
        Clear all memories from this tier.
        
        Returns:
            bool: True if the operation was successful
            
        Raises:
            TierOperationError: If the clear operation fails
        """
        pass
    
    @abc.abstractmethod
    async def get_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics about this memory tier.
        
        Returns:
            Dictionary of statistics
            
        Raises:
            TierOperationError: If the get stats operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Tier-Specific Methods
    #-----------------------------------------------------------------------
    
    # STM-specific methods (implemented by STM tier)
    async def set_expiry(self, memory_id: str, ttl_seconds: int) -> bool:
        """
        Set a time-to-live (TTL) for a STM memory.
        
        Args:
            memory_id: The ID of the memory
            ttl_seconds: TTL in seconds
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            NotImplementedError: If not implemented by this tier
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        raise NotImplementedError("This tier does not support expiry")
    
    # MTM-specific methods (implemented by MTM tier)
    async def set_priority(self, memory_id: str, priority: Union[int, str]) -> bool:
        """
        Set the priority of a MTM memory.
        
        Args:
            memory_id: The ID of the memory
            priority: Priority value (tier-specific)
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            NotImplementedError: If not implemented by this tier
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        raise NotImplementedError("This tier does not support priority")
    
    # LTM-specific methods (implemented by LTM tier)
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a relationship between two LTM memories.
        
        Args:
            source_id: ID of the source memory
            target_id: ID of the target memory
            relationship_type: Type of relationship
            metadata: Optional relationship metadata
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            NotImplementedError: If not implemented by this tier
            MemoryNotFoundError: If either memory does not exist
            TierOperationError: If the operation fails
        """
        raise NotImplementedError("This tier does not support relationships")
    
    async def get_related(
        self,
        memory_id: str,
        relationship_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get memories related to a specific memory.
        
        Args:
            memory_id: ID of the memory
            relationship_type: Optional specific relationship type
            limit: Maximum number of results to return
            
        Returns:
            List of related memories
            
        Raises:
            NotImplementedError: If not implemented by this tier
            MemoryNotFoundError: If the memory does not exist
            TierOperationError: If the operation fails
        """
        raise NotImplementedError("This tier does not support relationships")
