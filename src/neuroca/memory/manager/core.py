"""
Memory Manager Core

This module provides the central MemoryManager class that orchestrates all memory operations
across different tiers (STM, MTM, LTM), implements the working memory buffer,
and handles background tasks for consolidation and decay.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from neuroca.config.settings import get_settings
from neuroca.memory.exceptions import (
    ItemNotFoundError as MemoryNotFoundError,
    StorageBackendError,
    StorageInitializationError,
)
from neuroca.memory.backends import (
    BackendType,
    MemoryTier,
    StorageBackendFactory,
)
# Fixed import path for STMStorage
from neuroca.memory.tiers.stm.core import ShortTermMemoryTier as STMStorage
from neuroca.memory.manager.models import RankedMemory
from neuroca.memory.manager.working_memory import (
    update_working_memory,
    get_prompt_context_memories
)
from neuroca.memory.manager.consolidation import (
    consolidate_stm_to_mtm,
    consolidate_mtm_to_ltm
)
from neuroca.memory.manager.decay import (
    decay_mtm_memories,
    decay_ltm_memories,
    strengthen_memory
)
from neuroca.memory.manager.storage import (
    add_memory,
    retrieve_memory,
    search_memories
)

# Configure logger
logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central memory management system for the NeuroCognitive Agent.
    
    This class orchestrates memory operations across all tiers (STM, MTM, LTM),
    manages memory lifecycle, and provides automatic, context-driven retrieval
    for agent prompts without requiring explicit memory queries.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        stm_storage: Optional[STMStorage] = None,
        mtm_storage_type: BackendType = BackendType.REDIS,
        ltm_storage_type: BackendType = BackendType.SQL,
        vector_storage_type: BackendType = BackendType.VECTOR,
        working_buffer_size: int = 20,
        embedding_dimension: int = 768,
    ):
        """
        Initialize the Memory Manager.
        
        Args:
            config: Configuration for the memory system
            stm_storage: Optional STM storage instance (created if not provided)
            mtm_storage_type: Storage backend type for MTM
            ltm_storage_type: Storage backend type for LTM
            vector_storage_type: Storage backend type for vector search
            working_buffer_size: Size of the working memory buffer
            embedding_dimension: Dimension of embedding vectors
        """
        self.config = config or get_settings().get("memory", {})
        
        # Initialize storage components
        self.stm_storage = stm_storage or StorageBackendFactory.create_storage(
            tier=MemoryTier.STM,
            config=self.config.get("stm", {})
        )
        
        self.mtm_storage = StorageBackendFactory.create_storage(
            tier=MemoryTier.MTM,
            backend_type=mtm_storage_type,
            config=self.config.get("mtm", {})
        )
        
        self.ltm_storage = StorageBackendFactory.create_storage(
            tier=MemoryTier.LTM,
            backend_type=ltm_storage_type,
            config=self.config.get("ltm", {})
        )
        
        self.vector_storage = StorageBackendFactory.create_storage(
            tier=MemoryTier.LTM,
            backend_type=vector_storage_type,
            config=self.config.get("vector", {
                "dimension": embedding_dimension,
                "similarity_threshold": 0.65,
            })
        )
        
        # Working memory settings
        self.working_buffer_size = working_buffer_size
        self.working_memory: List[RankedMemory] = []
        self.working_memory_ids: Set[str] = set()
        
        # Context tracking
        self.current_context: Dict[str, Any] = {}
        self.context_embeddings: List[float] = []
        
        # Background task management
        self._background_tasks = set()
        self._initialized = False
        self._running = False
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the memory manager and all storage backends."""
        try:
            logger.info("Initializing memory manager and storage backends")
            
            # Initialize all storage components
            await self.stm_storage.initialize()
            await self.mtm_storage.initialize()
            await self.ltm_storage.initialize()
            await self.vector_storage.initialize()
            
            # Mark as initialized
            self._initialized = True
            self._running = True
            
            # Start background tasks for memory processes
            self._start_periodic_tasks()
            
            logger.info("Memory manager initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize memory manager: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the memory manager is initialized."""
        if not self._initialized:
            await self.initialize()
    
    def _start_periodic_tasks(self) -> None:
        """Start background tasks for memory management."""
        # Create background tasks for consolidation, decay, etc.
        consolidation_task = asyncio.create_task(self._run_periodic_consolidation())
        self._background_tasks.add(consolidation_task)
        consolidation_task.add_done_callback(self._background_tasks.discard)
        
        decay_task = asyncio.create_task(self._run_periodic_decay())
        self._background_tasks.add(decay_task)
        decay_task.add_done_callback(self._background_tasks.discard)
        
        buffer_update_task = asyncio.create_task(self._run_periodic_buffer_update())
        self._background_tasks.add(buffer_update_task)
        buffer_update_task.add_done_callback(self._background_tasks.discard)
    
    async def shutdown(self) -> None:
        """Gracefully shut down the memory manager."""
        logger.info("Shutting down memory manager")
        
        # Stop background tasks
        self._running = False
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Shut down storage backends
        if hasattr(self.stm_storage, 'shutdown'):
            await self.stm_storage.shutdown()
        
        if hasattr(self.mtm_storage, 'shutdown'):
            await self.mtm_storage.shutdown()
        
        if hasattr(self.ltm_storage, 'shutdown'):
            await self.ltm_storage.shutdown()
        
        if hasattr(self.vector_storage, 'shutdown'):
            await self.vector_storage.shutdown()
        
        logger.info("Memory manager shut down successfully")
    
    #-----------------------------------------------------------------------
    # Storage Operations
    #-----------------------------------------------------------------------
    
    async def add_memory(
        self,
        content: Any,
        summary: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
        initial_tier: MemoryTier = MemoryTier.STM,
    ) -> str:
        """
        Add a new memory to the system. By default, memories start in STM
        and may be consolidated to MTM/LTM based on importance and access patterns.
        
        Args:
            content: Memory content (can be text, dict, or structured data)
            summary: Optional summary of the content
            importance: Importance score (0.0 to 1.0)
            metadata: Additional metadata
            tags: Tags for categorization
            embedding: Optional pre-computed embedding vector
            initial_tier: Initial storage tier (defaults to STM)
            
        Returns:
            Memory ID
        """
        await self._ensure_initialized()
        
        memory_id = await add_memory(
            stm_storage=self.stm_storage,
            mtm_storage=self.mtm_storage,
            ltm_storage=self.ltm_storage,
            vector_storage=self.vector_storage,
            content=content,
            summary=summary,
            importance=importance,
            metadata=metadata,
            tags=tags,
            embedding=embedding,
            initial_tier=initial_tier
        )
        
        # Trigger context update to see if this new memory is relevant to current context
        if memory_id:
            asyncio.create_task(self._update_working_memory())
        
        return memory_id
    
    async def retrieve_memory(
        self,
        memory_id: str,
        tier: Optional[MemoryTier] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: Memory ID
            tier: Optional tier to search in (searches all tiers if not specified)
            
        Returns:
            Memory data as a dictionary
        """
        await self._ensure_initialized()
        
        return await retrieve_memory(
            stm_storage=self.stm_storage,
            mtm_storage=self.mtm_storage,
            ltm_storage=self.ltm_storage,
            vector_storage=self.vector_storage,
            memory_id=memory_id,
            tier=tier
        )
    
    async def search_memories(
        self,
        query: str,
        embedding: Optional[List[float]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_relevance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for memories across all tiers.
        
        Args:
            query: Text query
            embedding: Optional query embedding for vector search
            tags: Optional tags to filter by
            limit: Maximum number of results
            min_relevance: Minimum relevance score (0.0 to 1.0)
            
        Returns:
            List of relevant memories as dictionaries
        """
        await self._ensure_initialized()
        
        return await search_memories(
            stm_storage=self.stm_storage,
            mtm_storage=self.mtm_storage,
            vector_storage=self.vector_storage,
            query=query,
            embedding=embedding,
            tags=tags,
            limit=limit,
            min_relevance=min_relevance
        )
    
    #-----------------------------------------------------------------------
    # Context Monitoring & Working Memory
    #-----------------------------------------------------------------------
    
    async def update_context(
        self,
        context_data: Dict[str, Any],
        embedding: Optional[List[float]] = None,
    ) -> None:
        """
        Update the current context. This triggers background retrieval of relevant memories.
        
        Args:
            context_data: Dictionary with current context information (e.g., current input, goals, etc.)
            embedding: Optional pre-computed embedding of the context
        """
        await self._ensure_initialized()
        
        async with self._lock:
            # Update the current context
            self.current_context.update(context_data)
            
            # Update context embedding if provided
            if embedding:
                self.context_embeddings = embedding
        
        # Trigger a working memory update based on new context
        asyncio.create_task(self._update_working_memory())
    
    async def _update_working_memory(self) -> None:
        """
        Update the working memory buffer based on current context.
        This retrieves relevant memories across all tiers.
        """
        await update_working_memory(
            current_context=self.current_context,
            context_embeddings=self.context_embeddings,
            working_memory=self.working_memory,
            working_memory_ids=self.working_memory_ids,
            working_buffer_size=self.working_buffer_size,
            search_memories_func=self.search_memories,
            lock=self._lock
        )
    
    async def get_prompt_context_memories(
        self,
        max_memories: int = 5,
        max_tokens_per_memory: int = 150,
    ) -> List[Dict[str, Any]]:
        """
        Get the most relevant memories for injection into the agent's prompt.
        
        Args:
            max_memories: Maximum number of memories to include
            max_tokens_per_memory: Maximum tokens per memory
            
        Returns:
            List of formatted memory dictionaries
        """
        await self._ensure_initialized()
        
        # Create a wrapper function for strengthen_memory that includes storage backends
        async def strengthen_memory_wrapper(memory_id, tier, strengthen_amount):
            return await strengthen_memory(
                memory_id=memory_id,
                tier=tier,
                mtm_storage=self.mtm_storage,
                ltm_storage=self.ltm_storage,
                strengthen_amount=strengthen_amount
            )
        
        return await get_prompt_context_memories(
            working_memory=self.working_memory,
            working_memory_ids=self.working_memory_ids,
            max_memories=max_memories,
            max_tokens_per_memory=max_tokens_per_memory,
            strengthen_memory_func=strengthen_memory_wrapper,
            lock=self._lock
        )
    
    #-----------------------------------------------------------------------
    # Background Tasks
    #-----------------------------------------------------------------------
    
    async def _run_periodic_consolidation(self) -> None:
        """
        Background task for periodic memory consolidation.
        Moves memories between tiers based on importance and access patterns.
        """
        while self._running:
            try:
                # Sleep at the beginning to avoid running immediately at startup
                await asyncio.sleep(self.config.get("consolidation_interval_seconds", 300))
                
                await consolidate_stm_to_mtm(
                    stm_storage=self.stm_storage,
                    mtm_storage=self.mtm_storage,
                    config=self.config
                )
                
                await consolidate_mtm_to_ltm(
                    mtm_storage=self.mtm_storage,
                    ltm_storage=self.ltm_storage,
                    config=self.config
                )
                
            except asyncio.CancelledError:
                # Allow clean cancellation
                break
            except Exception as e:
                logger.error(f"Error in periodic consolidation: {str(e)}")
                await asyncio.sleep(60)  # Wait a bit longer on error
    
    async def _run_periodic_decay(self) -> None:
        """
        Background task for periodic memory decay.
        Reduces memory strengths based on access patterns and time.
        """
        while self._running:
            try:
                # Sleep at the beginning to avoid running immediately at startup
                await asyncio.sleep(self.config.get("decay_interval_seconds", 600))
                
                await decay_mtm_memories(
                    mtm_storage=self.mtm_storage,
                    config=self.config
                )
                
                await decay_ltm_memories(
                    ltm_storage=self.ltm_storage,
                    config=self.config
                )
                
            except asyncio.CancelledError:
                # Allow clean cancellation
                break
            except Exception as e:
                logger.error(f"Error in periodic decay: {str(e)}")
                await asyncio.sleep(60)  # Wait a bit longer on error
    
    async def _run_periodic_buffer_update(self) -> None:
        """
        Background task for periodically updating the working memory buffer.
        This ensures the buffer contains the most relevant memories even
        if the context hasn't explicitly changed.
        """
        while self._running:
            try:
                # Sleep at the beginning
                await asyncio.sleep(self.config.get("buffer_update_interval_seconds", 60))
                
                # Only update if there's a current context
                if self.current_context:
                    await self._update_working_memory()
                
            except asyncio.CancelledError:
                # Allow clean cancellation
                break
            except Exception as e:
                logger.error(f"Error in periodic buffer update: {str(e)}")
                await asyncio.sleep(30)  # Wait a bit longer on error
