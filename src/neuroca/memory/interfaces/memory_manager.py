"""
Memory Manager Interface

This module defines the abstract interface for the Memory Manager component,
which serves as the central orchestration layer for the entire memory system.

The Memory Manager is responsible for:
1. Coordinating operations across memory tiers (STM, MTM, LTM)
2. Managing the memory lifecycle (addition, retrieval, consolidation, decay)
3. Providing context-aware memory retrieval
4. Maintaining a working memory buffer for prompt injection
5. Offering a clean, unified public API for the entire memory system

Client code should interact with the memory system exclusively through
this interface, without direct access to the underlying tiers or backends.
"""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


class MemoryManagerInterface(abc.ABC):
    """
    Abstract Base Class defining the interface for the Memory Manager.
    
    The Memory Manager serves as the central orchestration layer for the
    memory system, coordinating operations across memory tiers and providing
    a unified public API for the entire system.
    
    Memory Manager is responsible for:
    1. Cross-tier memory operations
    2. Memory lifecycle management
    3. Context-aware memory retrieval
    4. Working memory management
    5. System configuration and initialization
    
    Client code should interact with the memory system exclusively 
    through this interface.
    """
    
    @abc.abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the memory manager and all storage components.
        
        This method must be called before any other method.
        
        Raises:
            MemoryManagerInitializationError: If initialization fails
        """
        pass
    
    @abc.abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shut down the memory manager and all storage components.
        
        This method should be called when the memory system is no longer needed
        to ensure all resources are released and pending operations are completed.
        
        Raises:
            MemoryManagerOperationError: If shutdown fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Core Memory Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def add_memory(
        self,
        content: Any,
        summary: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
        initial_tier: Optional[str] = None,
    ) -> str:
        """
        Add a new memory to the system.
        
        By default, memories start in STM and may be consolidated to MTM/LTM
        based on importance and access patterns.
        
        Args:
            content: Memory content (can be text, dict, or structured data)
            summary: Optional summary of the content
            importance: Importance score (0.0 to 1.0)
            metadata: Additional metadata
            tags: Tags for categorization
            embedding: Optional pre-computed embedding vector
            initial_tier: Initial storage tier (default determined by implementation)
            
        Returns:
            Memory ID
            
        Raises:
            MemoryManagerOperationError: If the add operation fails
        """
        pass
    
    @abc.abstractmethod
    async def retrieve_memory(
        self,
        memory_id: str,
        tier: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: Memory ID
            tier: Optional tier to search in (searches all tiers if not specified)
            
        Returns:
            Memory data as a dictionary, or None if not found
            
        Raises:
            MemoryManagerOperationError: If the retrieve operation fails
        """
        pass
    
    @abc.abstractmethod
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[Any] = None,
        summary: Optional[str] = None,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory ID
            content: New content (if None, keeps existing content)
            summary: New summary (if None, keeps existing summary)
            importance: New importance (if None, keeps existing importance)
            metadata: New metadata (if None, keeps existing metadata)
            tags: New tags (if None, keeps existing tags)
            
        Returns:
            bool: True if the update was successful
            
        Raises:
            MemoryNotFoundError: If memory with the given ID is not found
            MemoryManagerOperationError: If the update operation fails
        """
        pass
    
    @abc.abstractmethod
    async def delete_memory(
        self,
        memory_id: str,
        tier: Optional[str] = None,
    ) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: Memory ID
            tier: Optional tier to delete from (tries all tiers if not specified)
            
        Returns:
            bool: True if the deletion was successful
            
        Raises:
            MemoryManagerOperationError: If the delete operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Search and Retrieval
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def search_memories(
        self,
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        tags: Optional[List[str]] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        min_relevance: float = 0.0,
        tiers: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for memories across all tiers.
        
        Args:
            query: Text query
            embedding: Optional query embedding for vector search
            tags: Optional tags to filter by
            metadata_filters: Optional metadata field filters
            limit: Maximum number of results
            min_relevance: Minimum relevance score (0.0 to 1.0)
            tiers: Optional list of tiers to search in
            
        Returns:
            List of relevant memories
            
        Raises:
            MemoryManagerOperationError: If the search operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Context Management
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def update_context(
        self,
        context_data: Dict[str, Any],
        embedding: Optional[List[float]] = None,
    ) -> None:
        """
        Update the current context to trigger relevant memory retrieval.
        
        This method updates the system's understanding of the current context,
        such as the current conversation, user input, goals, etc. It triggers
        background retrieval of relevant memories for the working memory buffer.
        
        Args:
            context_data: Dictionary with current context information
            embedding: Optional pre-computed embedding of the context
            
        Raises:
            MemoryManagerOperationError: If the context update fails
        """
        pass
    
    @abc.abstractmethod
    async def get_prompt_context_memories(
        self,
        max_memories: int = 5,
        max_tokens_per_memory: int = 150,
    ) -> List[Dict[str, Any]]:
        """
        Get the most relevant memories for injection into the agent's prompt.
        
        This method is used by the prompt builder to inject relevant context
        from the memory system into the agent's prompt.
        
        Args:
            max_memories: Maximum number of memories to include
            max_tokens_per_memory: Maximum tokens per memory
            
        Returns:
            List of formatted memory dictionaries
            
        Raises:
            MemoryManagerOperationError: If the prompt context retrieval fails
        """
        pass
    
    @abc.abstractmethod
    async def clear_context(self) -> None:
        """
        Clear the current context and working memory buffer.
        
        This method is typically called at the end of a conversation or
        when switching to a completely different task.
        
        Raises:
            MemoryManagerOperationError: If the clear context operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Memory Lifecycle Management
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def consolidate_memory(
        self,
        memory_id: str,
        source_tier: str,
        target_tier: str,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Explicitly consolidate a memory from one tier to another.
        
        This method allows for manual consolidation of a memory, 
        in addition to the automatic consolidation done by the system.
        
        Args:
            memory_id: Memory ID
            source_tier: Source tier ("stm", "mtm", "ltm")
            target_tier: Target tier ("stm", "mtm", "ltm")
            additional_metadata: Optional additional metadata to add during consolidation
            
        Returns:
            The ID of the consolidated memory in the target tier (may be the same or different)
            
        Raises:
            MemoryNotFoundError: If memory with the given ID is not found
            InvalidTierError: If source or target tier is invalid
            MemoryManagerOperationError: If the consolidation fails
        """
        pass
    
    @abc.abstractmethod
    async def strengthen_memory(
        self,
        memory_id: str,
        tier: Optional[str] = None,
        strengthen_amount: float = 0.1,
    ) -> bool:
        """
        Strengthen a memory to make it less likely to be forgotten.
        
        Args:
            memory_id: Memory ID
            tier: Optional tier to strengthen in (tries all tiers if not specified)
            strengthen_amount: Amount to strengthen by (0.0 to 1.0)
            
        Returns:
            bool: True if the strengthening was successful
            
        Raises:
            MemoryNotFoundError: If memory with the given ID is not found
            MemoryManagerOperationError: If the strengthen operation fails
        """
        pass
    
    @abc.abstractmethod
    async def decay_memory(
        self,
        memory_id: str,
        tier: Optional[str] = None,
        decay_amount: float = 0.1,
    ) -> bool:
        """
        Explicitly decay a memory to make it more likely to be forgotten.
        
        Args:
            memory_id: Memory ID
            tier: Optional tier to decay in (tries all tiers if not specified)
            decay_amount: Amount to decay by (0.0 to 1.0)
            
        Returns:
            bool: True if the decay was successful
            
        Raises:
            MemoryNotFoundError: If memory with the given ID is not found
            MemoryManagerOperationError: If the decay operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # System Management
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.
        
        Returns:
            Dictionary of statistics
            
        Raises:
            MemoryManagerOperationError: If the stats retrieval fails
        """
        pass
    
    @abc.abstractmethod
    async def run_maintenance(self) -> Dict[str, Any]:
        """
        Run maintenance tasks on the memory system.
        
        This includes tasks like:
        - Consolidating memories between tiers
        - Decaying memories
        - Cleaning up expired memories
        - Optimizing storage
        
        Returns:
            Dictionary of maintenance results
            
        Raises:
            MemoryManagerOperationError: If the maintenance fails
        """
        pass
