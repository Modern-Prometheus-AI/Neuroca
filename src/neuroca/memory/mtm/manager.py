"""
Medium-Term Memory (MTM) Manager Module

This module implements the Medium-Term Memory (MTM) manager for the NeuroCognitive Architecture.
The MTM manager is responsible for storing, retrieving, and maintaining medium-term memories,
which typically persist for hours to days. It handles memory consolidation from STM,
decay processes, and provides interfaces for other system components to interact with MTM.

The implementation follows a repository pattern with additional biological-inspired
processes for memory consolidation, association, and decay.

Usage:
    manager = MTMManager()
    
    # Store a new memory
    memory_id = await manager.store_memory(content="Meeting with John", context={"location": "office"})
    
    # Retrieve a memory
    memory = await manager.get_memory(memory_id)
    
    # Search for memories
    memories = await manager.search_memories(query="meeting", limit=5)
    
    # Consolidate memories from STM
    await manager.consolidate_from_stm(stm_memories)
    
    # Run maintenance processes
    await manager.run_maintenance()
"""

import asyncio
import contextlib
import datetime
import logging
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError

from neuroca.config import settings
from neuroca.core.exceptions import (
    MemoryNotFoundError,
    MemoryStorageError,
    MemoryValidationError,
)
from neuroca.db.repositories.mtm_repository import MTMRepository
from neuroca.memory.models import MemoryAssociation, MemoryItem, MemoryPriority, MemoryStatus
from neuroca.memory.utils import calculate_memory_importance, generate_embeddings

# Configure logger
logger = logging.getLogger(__name__)


class MTMMemory(BaseModel):
    """
    Medium-Term Memory item model.
    
    Represents a memory item stored in the Medium-Term Memory system.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    embedding: Optional[list[float]] = None
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    associations: list[MemoryAssociation] = Field(default_factory=list)
    importance: float = 0.5
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_accessed: datetime.datetime = Field(default_factory=datetime.datetime.now)
    access_count: int = 0
    status: MemoryStatus = MemoryStatus.ACTIVE
    priority: MemoryPriority = MemoryPriority.NORMAL
    decay_rate: float = 0.1  # Rate at which memory importance decays
    consolidation_stage: int = 0  # Tracks the consolidation process stage
    
    class Config:
        arbitrary_types_allowed = True


class MTMManager:
    """
    Medium-Term Memory Manager.
    
    Manages the storage, retrieval, and maintenance of medium-term memories.
    Implements biological-inspired processes for memory consolidation, association,
    and decay.
    """
    
    def __init__(self, repository: Optional[MTMRepository] = None):
        """
        Initialize the MTM Manager.
        
        Args:
            repository: Optional repository implementation. If not provided,
                        a default repository will be created.
        """
        self.repository = repository or MTMRepository()
        self.maintenance_interval = settings.memory.mtm.maintenance_interval
        self.consolidation_threshold = settings.memory.mtm.consolidation_threshold
        self.max_memories = settings.memory.mtm.max_memories
        self.maintenance_task = None
        self._is_running = False
        
        # Cache for frequently accessed memories
        self._memory_cache: dict[str, MTMMemory] = {}
        self._cache_size = settings.memory.mtm.cache_size
        
        logger.info("MTM Manager initialized with repository: %s", self.repository.__class__.__name__)
    
    async def start(self) -> None:
        """
        Start the MTM manager and its maintenance processes.
        
        This method initiates background tasks for memory maintenance.
        """
        if self._is_running:
            logger.warning("MTM Manager is already running")
            return
            
        self._is_running = True
        self.maintenance_task = asyncio.create_task(self._maintenance_loop())
        logger.info("MTM Manager started with maintenance interval: %s seconds", 
                   self.maintenance_interval)
    
    async def stop(self) -> None:
        """
        Stop the MTM manager and its maintenance processes.
        
        This method cancels background tasks and performs cleanup.
        """
        if not self._is_running:
            logger.warning("MTM Manager is not running")
            return
            
        self._is_running = False
        if self.maintenance_task:
            self.maintenance_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.maintenance_task

            self.maintenance_task = None
        
        # Flush cache to persistent storage
        await self._flush_cache()
        logger.info("MTM Manager stopped")
    
    async def store_memory(self, content: str, context: Optional[dict[str, Any]] = None, 
                          metadata: Optional[dict[str, Any]] = None,
                          importance: Optional[float] = None,
                          priority: MemoryPriority = MemoryPriority.NORMAL) -> str:
        """
        Store a new memory in the Medium-Term Memory.
        
        Args:
            content: The main content of the memory
            context: Optional contextual information about the memory
            metadata: Optional metadata for the memory
            importance: Optional importance score (0.0-1.0)
            priority: Priority level for the memory
            
        Returns:
            The ID of the stored memory
            
        Raises:
            MemoryValidationError: If the memory data is invalid
            MemoryStorageError: If there's an error storing the memory
        """
        try:
            # Generate embeddings for the content
            embedding = await generate_embeddings(content)
            
            # Calculate importance if not provided
            if importance is None:
                importance = calculate_memory_importance(content, context or {})
            
            # Create memory object
            memory = MTMMemory(
                content=content,
                embedding=embedding,
                context=context or {},
                metadata=metadata or {},
                importance=importance,
                priority=priority
            )
            
            # Store in repository
            await self.repository.add(memory.dict())
            
            # Add to cache if high importance or priority
            if memory.importance > 0.7 or memory.priority in (MemoryPriority.HIGH, MemoryPriority.CRITICAL):
                self._add_to_cache(memory)
            
            logger.debug("Stored new MTM memory: %s", memory.id)
            return memory.id
            
        except ValidationError as e:
            error_msg = f"Invalid memory data: {str(e)}"
            logger.error(error_msg)
            raise MemoryValidationError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MemoryStorageError(error_msg) from e
    
    async def get_memory(self, memory_id: str) -> MTMMemory:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The memory object
            
        Raises:
            MemoryNotFoundError: If the memory is not found
        """
        # Check cache first
        if memory_id in self._memory_cache:
            memory = self._memory_cache[memory_id]
            # Update access metadata
            memory.last_accessed = datetime.datetime.now()
            memory.access_count += 1
            return memory
        
        try:
            # Retrieve from repository
            memory_data = await self.repository.get(memory_id)
            if not memory_data:
                raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
            
            memory = MTMMemory(**memory_data)
            
            # Update access metadata
            memory.last_accessed = datetime.datetime.now()
            memory.access_count += 1
            await self.repository.update(memory_id, {"last_accessed": memory.last_accessed, 
                                                    "access_count": memory.access_count})
            
            # Add to cache
            self._add_to_cache(memory)
            
            logger.debug("Retrieved MTM memory: %s", memory_id)
            return memory
            
        except MemoryNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error retrieving memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MemoryStorageError(error_msg) from e
    
    async def update_memory(self, memory_id: str, 
                           updates: dict[str, Any]) -> MTMMemory:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update
            updates: Dictionary of fields to update
            
        Returns:
            The updated memory object
            
        Raises:
            MemoryNotFoundError: If the memory is not found
            MemoryValidationError: If the update data is invalid
        """
        try:
            # Get current memory
            memory = await self.get_memory(memory_id)
            
            # Apply updates
            memory_dict = memory.dict()
            memory_dict.update(updates)
            
            # Validate updated memory
            updated_memory = MTMMemory(**memory_dict)
            
            # Store updates
            await self.repository.update(memory_id, updates)
            
            # Update cache if present
            if memory_id in self._memory_cache:
                self._memory_cache[memory_id] = updated_memory
            
            logger.debug("Updated MTM memory: %s", memory_id)
            return updated_memory
            
        except ValidationError as e:
            error_msg = f"Invalid update data for memory {memory_id}: {str(e)}"
            logger.error(error_msg)
            raise MemoryValidationError(error_msg) from e
        except MemoryNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error updating memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MemoryStorageError(error_msg) from e
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from MTM.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            True if the memory was deleted, False otherwise
            
        Raises:
            MemoryStorageError: If there's an error deleting the memory
        """
        try:
            # Remove from cache if present
            if memory_id in self._memory_cache:
                del self._memory_cache[memory_id]
            
            # Delete from repository
            result = await self.repository.delete(memory_id)
            
            if result:
                logger.debug("Deleted MTM memory: %s", memory_id)
            else:
                logger.warning("Failed to delete MTM memory: %s (not found)", memory_id)
                
            return result
            
        except Exception as e:
            error_msg = f"Error deleting memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MemoryStorageError(error_msg) from e
    
    async def search_memories(self, query: str, limit: int = 10, 
                             threshold: float = 0.7,
                             context_filter: Optional[dict[str, Any]] = None) -> list[MTMMemory]:
        """
        Search for memories based on semantic similarity to the query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0.0-1.0)
            context_filter: Optional filter for memory context
            
        Returns:
            List of matching memory objects
            
        Raises:
            MemoryStorageError: If there's an error searching memories
        """
        try:
            # Generate embeddings for the query
            query_embedding = await generate_embeddings(query)
            
            # Search in repository
            results = await self.repository.search_by_embedding(
                embedding=query_embedding,
                limit=limit,
                threshold=threshold,
                filters=context_filter
            )
            
            # Convert to memory objects
            memories = [MTMMemory(**item) for item in results]
            
            # Update access metadata for retrieved memories
            current_time = datetime.datetime.now()
            for memory in memories:
                memory.last_accessed = current_time
                memory.access_count += 1
                await self.repository.update(memory.id, {
                    "last_accessed": memory.last_accessed,
                    "access_count": memory.access_count
                })
                
                # Update cache
                self._add_to_cache(memory)
            
            logger.debug("Searched MTM memories with query '%s', found %d results", 
                        query, len(memories))
            return memories
            
        except Exception as e:
            error_msg = f"Error searching memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MemoryStorageError(error_msg) from e
    
    async def consolidate_from_stm(self, stm_memories: list[MemoryItem]) -> list[str]:
        """
        Consolidate memories from Short-Term Memory into Medium-Term Memory.
        
        Args:
            stm_memories: List of STM memory items to consolidate
            
        Returns:
            List of IDs of the consolidated memories
            
        Raises:
            MemoryStorageError: If there's an error during consolidation
        """
        consolidated_ids = []
        
        try:
            for stm_memory in stm_memories:
                # Check if memory meets consolidation threshold
                if stm_memory.importance < self.consolidation_threshold:
                    logger.debug("STM memory %s below consolidation threshold, skipping", 
                               stm_memory.id)
                    continue
                
                # Create MTM memory from STM memory
                memory_id = await self.store_memory(
                    content=stm_memory.content,
                    context=stm_memory.context,
                    metadata={
                        "source": "stm_consolidation",
                        "original_stm_id": stm_memory.id,
                        "consolidation_time": datetime.datetime.now().isoformat()
                    },
                    importance=stm_memory.importance,
                    priority=stm_memory.priority
                )
                
                consolidated_ids.append(memory_id)
                
                # Create associations with existing memories
                await self._create_associations(memory_id)
            
            logger.info("Consolidated %d memories from STM to MTM", len(consolidated_ids))
            return consolidated_ids
            
        except Exception as e:
            error_msg = f"Error during STM to MTM consolidation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MemoryStorageError(error_msg) from e
    
    async def run_maintenance(self) -> dict[str, Any]:
        """
        Run maintenance processes on the Medium-Term Memory.
        
        This includes:
        - Applying decay to memories
        - Pruning low-importance memories
        - Consolidating related memories
        - Preparing memories for LTM transfer
        
        Returns:
            Statistics about the maintenance operation
        """
        stats = {
            "decayed_memories": 0,
            "pruned_memories": 0,
            "consolidated_memories": 0,
            "ltm_candidates": 0,
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": None
        }
        
        try:
            # Apply decay to all memories
            decayed_count = await self._apply_decay()
            stats["decayed_memories"] = decayed_count
            
            # Prune low-importance memories
            pruned_count = await self._prune_memories()
            stats["pruned_memories"] = pruned_count
            
            # Consolidate related memories
            consolidated_count = await self._consolidate_related_memories()
            stats["consolidated_memories"] = consolidated_count
            
            # Identify LTM candidates
            ltm_candidates = await self._identify_ltm_candidates()
            stats["ltm_candidates"] = len(ltm_candidates)
            
            stats["end_time"] = datetime.datetime.now().isoformat()
            logger.info("MTM maintenance completed: decayed=%d, pruned=%d, consolidated=%d, ltm_candidates=%d",
                       decayed_count, pruned_count, consolidated_count, len(ltm_candidates))
            
            return stats
            
        except Exception as e:
            error_msg = f"Error during MTM maintenance: {str(e)}"
            logger.error(error_msg, exc_info=True)
            stats["error"] = str(e)
            stats["end_time"] = datetime.datetime.now().isoformat()
            return stats
    
    async def get_ltm_candidates(self) -> list[MTMMemory]:
        """
        Get memories that are candidates for transfer to Long-Term Memory.
        
        Returns:
            List of memory objects that are candidates for LTM
        """
        try:
            candidates = await self._identify_ltm_candidates()
            logger.debug("Identified %d LTM candidate memories", len(candidates))
            return candidates
        except Exception as e:
            error_msg = f"Error identifying LTM candidates: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MemoryStorageError(error_msg) from e
    
    async def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the Medium-Term Memory.
        
        Returns:
            Dictionary of statistics
        """
        try:
            total_count = await self.repository.count()
            
            # Get counts by priority
            priority_counts = {}
            for priority in MemoryPriority:
                count = await self.repository.count({"priority": priority.value})
                priority_counts[priority.name] = count
            
            # Get counts by status
            status_counts = {}
            for status in MemoryStatus:
                count = await self.repository.count({"status": status.value})
                status_counts[status.name] = count
            
            # Get average importance
            avg_importance = await self.repository.get_average("importance")
            
            # Get age statistics
            now = datetime.datetime.now()
            one_day_ago = now - datetime.timedelta(days=1)
            one_week_ago = now - datetime.timedelta(weeks=1)
            
            new_memories = await self.repository.count({"created_at": {"$gte": one_day_ago.isoformat()}})
            week_old_memories = await self.repository.count({
                "created_at": {
                    "$gte": one_week_ago.isoformat(),
                    "$lt": one_day_ago.isoformat()
                }
            })
            old_memories = await self.repository.count({"created_at": {"$lt": one_week_ago.isoformat()}})
            
            stats = {
                "total_memories": total_count,
                "by_priority": priority_counts,
                "by_status": status_counts,
                "average_importance": avg_importance,
                "age_distribution": {
                    "last_24h": new_memories,
                    "last_week": week_old_memories,
                    "older": old_memories
                },
                "cache_size": len(self._memory_cache),
                "timestamp": now.isoformat()
            }
            
            logger.debug("Generated MTM statistics")
            return stats
            
        except Exception as e:
            error_msg = f"Error generating MTM statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    # Private methods
    
    async def _maintenance_loop(self) -> None:
        """Background task that periodically runs maintenance operations."""
        try:
            while self._is_running:
                logger.debug("Running scheduled MTM maintenance")
                await self.run_maintenance()
                await asyncio.sleep(self.maintenance_interval)
        except asyncio.CancelledError:
            logger.info("MTM maintenance loop cancelled")
            raise
        except Exception as e:
            logger.error("Error in MTM maintenance loop: %s", str(e), exc_info=True)
            if self._is_running:
                # Restart the maintenance loop after a delay
                asyncio.create_task(self._delayed_restart_maintenance())
    
    async def _delayed_restart_maintenance(self) -> None:
        """Restart the maintenance loop after a delay."""
        await asyncio.sleep(60)  # Wait a minute before restarting
        if self._is_running and (self.maintenance_task is None or self.maintenance_task.done()):
            logger.info("Restarting MTM maintenance loop")
            self.maintenance_task = asyncio.create_task(self._maintenance_loop())
    
    async def _apply_decay(self) -> int:
        """
        Apply decay to all memories based on their decay rate and time since last access.
        
        Returns:
            Number of memories that were decayed
        """
        now = datetime.datetime.now()
        all_memories = await self.repository.list_all()
        decayed_count = 0
        
        for memory_data in all_memories:
            memory = MTMMemory(**memory_data)
            
            # Skip high priority memories
            if memory.priority in (MemoryPriority.HIGH, MemoryPriority.CRITICAL):
                continue
                
            # Calculate time since last access
            last_accessed = memory.last_accessed
            time_diff = (now - last_accessed).total_seconds()
            
            # Calculate decay factor based on time difference and decay rate
            # More frequently accessed memories decay slower
            access_factor = max(0.1, min(1.0, 1.0 / (memory.access_count + 1)))
            decay_amount = memory.decay_rate * access_factor * (time_diff / 86400)  # Normalize to days
            
            # Apply decay
            if decay_amount > 0:
                new_importance = max(0.0, memory.importance - decay_amount)
                if new_importance != memory.importance:
                    await self.repository.update(memory.id, {"importance": new_importance})
                    
                    # Update cache if present
                    if memory.id in self._memory_cache:
                        self._memory_cache[memory.id].importance = new_importance
                        
                    decayed_count += 1
        
        return decayed_count
    
    async def _prune_memories(self) -> int:
        """
        Prune low-importance memories to keep MTM size manageable.
        
        Returns:
            Number of memories that were pruned
        """
        # Get current memory count
        total_count = await self.repository.count()
        
        # If we're under the limit, no pruning needed
        if total_count <= self.max_memories:
            return 0
            
        # Calculate how many memories to prune
        to_prune = total_count - self.max_memories
        
        # Get lowest importance memories
        candidates = await self.repository.list_by_field(
            field="importance",
            ascending=True,
            limit=to_prune,
            filters={"priority": {"$nin": [MemoryPriority.HIGH.value, MemoryPriority.CRITICAL.value]}}
        )
        
        # Prune memories
        pruned_count = 0
        for memory_data in candidates:
            memory_id = memory_data["id"]
            
            # Remove from cache if present
            if memory_id in self._memory_cache:
                del self._memory_cache[memory_id]
                
            # Delete from repository
            success = await self.repository.delete(memory_id)
            if success:
                pruned_count += 1
        
        return pruned_count
    
    async def _consolidate_related_memories(self) -> int:
        """
        Consolidate related memories by strengthening associations.
        
        Returns:
            Number of memories that were consolidated
        """
        # Get memories with associations
        memories_with_associations = await self.repository.list_by_field(
            field="associations",
            exists=True,
            limit=100  # Process in batches
        )
        
        consolidated_count = 0
        
        for memory_data in memories_with_associations:
            memory = MTMMemory(**memory_data)
            
            # Skip if no associations
            if not memory.associations:
                continue
                
            # Strengthen important associations
            updated_associations = []
            for assoc in memory.associations:
                # Strengthen association based on access patterns
                try:
                    associated_memory = await self.get_memory(assoc.target_id)
                    
                    # Calculate new strength based on access patterns and importance
                    access_factor = min(associated_memory.access_count, 10) / 10
                    importance_factor = (memory.importance + associated_memory.importance) / 2
                    
                    new_strength = min(1.0, assoc.strength + (0.1 * access_factor * importance_factor))
                    
                    if new_strength != assoc.strength:
                        assoc.strength = new_strength
                        consolidated_count += 1
                        
                    updated_associations.append(assoc)
                except MemoryNotFoundError:
                    # Skip associations to deleted memories
                    continue
                except Exception as e:
                    logger.warning("Error processing association %s -> %s: %s", 
                                  memory.id, assoc.target_id, str(e))
                    updated_associations.append(assoc)
            
            # Update memory with new association strengths
            if updated_associations != memory.associations:
                await self.repository.update(memory.id, {"associations": [a.dict() for a in updated_associations]})
                
                # Update cache if present
                if memory.id in self._memory_cache:
                    self._memory_cache[memory.id].associations = updated_associations
        
        return consolidated_count
    
    async def _identify_ltm_candidates(self) -> list[MTMMemory]:
        """
        Identify memories that are candidates for transfer to Long-Term Memory.
        
        Returns:
            List of memory objects that are candidates for LTM
        """
        # Criteria for LTM candidates:
        # 1. High importance (>0.8)
        # 2. Frequently accessed (>5 times)
        # 3. Older than a certain threshold (1 week)
        # 4. Has strong associations
        
        one_week_ago = datetime.datetime.now() - datetime.timedelta(weeks=1)
        
        candidates_data = await self.repository.list_by_criteria({
            "importance": {"$gt": 0.8},
            "access_count": {"$gt": 5},
            "created_at": {"$lt": one_week_ago.isoformat()},
            "associations": {"$exists": True}
        })
        
        # Filter for memories with strong associations
        candidates = []
        for memory_data in candidates_data:
            memory = MTMMemory(**memory_data)
            
            # Check if it has at least one strong association
            has_strong_association = any(assoc.strength > 0.7 for assoc in memory.associations)
            
            if has_strong_association:
                candidates.append(memory)
        
        return candidates
    
    async def _create_associations(self, memory_id: str) -> None:
        """
        Create associations between a memory and existing related memories.
        
        Args:
            memory_id: The ID of the memory to create associations for
        """
        try:
            # Get the memory
            memory = await self.get_memory(memory_id)
            
            # Find semantically similar memories
            similar_memories = await self.repository.search_by_embedding(
                embedding=memory.embedding,
                limit=5,
                threshold=0.8,
                exclude_ids=[memory_id]
            )
            
            # Create associations
            associations = []
            for similar in similar_memories:
                similarity_score = similar.get("similarity", 0.7)  # Default if not provided
                
                association = MemoryAssociation(
                    target_id=similar["id"],
                    association_type="semantic",
                    strength=similarity_score,
                    created_at=datetime.datetime.now()
                )
                
                associations.append(association)
                
                # Create reciprocal association
                reciprocal = MemoryAssociation(
                    target_id=memory_id,
                    association_type="semantic",
                    strength=similarity_score,
                    created_at=datetime.datetime.now()
                )
                
                # Add to target memory's associations
                target_memory = MTMMemory(**similar)
                target_associations = target_memory.associations
                target_associations.append(reciprocal)
                
                await self.repository.update(similar["id"], {"associations": [a.dict() for a in target_associations]})
                
                # Update cache if present
                if similar["id"] in self._memory_cache:
                    self._memory_cache[similar["id"]].associations = target_associations
            
            # Update memory with new associations
            if associations:
                memory.associations.extend(associations)
                await self.repository.update(memory_id, {"associations": [a.dict() for a in memory.associations]})
                
                # Update cache
                if memory_id in self._memory_cache:
                    self._memory_cache[memory_id].associations = memory.associations
                    
                logger.debug("Created %d associations for memory %s", len(associations), memory_id)
                
        except Exception as e:
            logger.error("Error creating associations for memory %s: %s", memory_id, str(e), exc_info=True)
    
    def _add_to_cache(self, memory: MTMMemory) -> None:
        """
        Add a memory to the cache, managing cache size.
        
        Args:
            memory: The memory to add to the cache
        """
        # If cache is full, remove least important item
        if len(self._memory_cache) >= self._cache_size:
            # Find least important memory in cache
            least_important_id = min(
                self._memory_cache.keys(),
                key=lambda k: (
                    self._memory_cache[k].priority.value,
                    self._memory_cache[k].importance,
                    self._memory_cache[k].last_accessed
                )
            )
            del self._memory_cache[least_important_id]
        
        # Add to cache
        self._memory_cache[memory.id] = memory
    
    async def _flush_cache(self) -> None:
        """Flush the cache to persistent storage."""
        for memory_id, memory in self._memory_cache.items():
            try:
                # Update last accessed time and other dynamic fields
                await self.repository.update(memory_id, memory.dict())
            except Exception as e:
                logger.error("Error flushing cache for memory %s: %s", memory_id, str(e))
        
        # Clear the cache
        self._memory_cache.clear()
        logger.debug("MTM memory cache flushed")