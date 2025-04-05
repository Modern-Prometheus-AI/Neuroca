"""
Long-Term Memory (LTM) Manager Module

This module implements the Long-Term Memory manager for the NeuroCognitive Architecture.
It provides functionality for storing, retrieving, updating, and managing long-term memories
within the system. The LTM manager handles persistence, retrieval optimization, and 
memory consolidation processes.

The LTM manager serves as the interface between the memory orchestrator and the actual
storage backends, providing a unified API for memory operations regardless of the 
underlying storage technology.

Usage:
    ltm_manager = LTMManager(config)
    
    # Store a new memory
    memory_id = await ltm_manager.store(memory_content)
    
    # Retrieve a memory
    memory = await ltm_manager.retrieve(memory_id)
    
    # Search for memories
    memories = await ltm_manager.search(query, limit=10)
    
    # Update a memory
    await ltm_manager.update(memory_id, updated_content)
    
    # Delete a memory
    await ltm_manager.delete(memory_id)
"""

import asyncio
import datetime
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Union

import aiofiles
from pydantic import BaseModel, Field, ValidationError

from neuroca.core.exceptions import (
    LTMConfigError,
    LTMConnectionError,
    LTMMemoryNotFoundError,
    LTMOperationError,
    LTMValidationError,
)
from neuroca.core.models.memory import (
    MemoryContent,
    MemoryImportance,
    MemoryMetadata,
    MemoryRecord,
    MemoryStatus,
)
from neuroca.memory.ltm.backends.factory import create_ltm_backend
from neuroca.memory.ltm.indexing import MemoryIndexer
from neuroca.memory.ltm.policies import ConsolidationPolicy, RetentionPolicy
from neuroca.monitoring.metrics import ltm_metrics

# Configure logger
logger = logging.getLogger(__name__)


class LTMManagerConfig(BaseModel):
    """Configuration for the LTM Manager."""
    
    backend_type: str = Field(
        default="vector_db",
        description="Type of backend storage to use (vector_db, relational, file, hybrid)"
    )
    consolidation_interval: int = Field(
        default=3600,
        description="Interval in seconds between memory consolidation runs"
    )
    max_batch_size: int = Field(
        default=100,
        description="Maximum number of memories to process in a single batch operation"
    )
    retention_policy: str = Field(
        default="importance_based",
        description="Policy for memory retention (time_based, importance_based, hybrid)"
    )
    indexing_enabled: bool = Field(
        default=True,
        description="Whether to enable memory indexing for faster retrieval"
    )
    backup_enabled: bool = Field(
        default=True,
        description="Whether to enable periodic backups of the memory store"
    )
    backup_interval: int = Field(
        default=86400,  # 24 hours
        description="Interval in seconds between memory backups"
    )
    backup_path: str = Field(
        default="./backups/ltm",
        description="Path where memory backups should be stored"
    )


class LTMManager:
    """
    Long-Term Memory (LTM) Manager
    
    Manages the storage, retrieval, and maintenance of long-term memories in the
    NeuroCognitive Architecture. Provides a unified interface to the underlying
    storage backend and implements memory management policies.
    
    The LTM Manager handles:
    - Memory storage and retrieval
    - Memory search and querying
    - Memory consolidation and optimization
    - Memory retention policies
    - Memory indexing for fast retrieval
    - Backup and recovery
    """
    
    def __init__(self, config: Optional[Union[dict[str, Any], LTMManagerConfig]] = None):
        """
        Initialize the LTM Manager with the provided configuration.
        
        Args:
            config: Configuration for the LTM Manager. Can be a dictionary or LTMManagerConfig object.
                   If None, default configuration will be used.
        
        Raises:
            LTMConfigError: If the configuration is invalid or the backend cannot be initialized.
        """
        try:
            # Initialize configuration
            if config is None:
                self.config = LTMManagerConfig()
            elif isinstance(config, dict):
                self.config = LTMManagerConfig(**config)
            elif isinstance(config, LTMManagerConfig):
                self.config = config
            else:
                raise LTMConfigError(f"Invalid configuration type: {type(config)}")
            
            logger.info(f"Initializing LTM Manager with backend: {self.config.backend_type}")
            
            # Initialize backend
            self.backend = create_ltm_backend(self.config.backend_type)
            if not self.backend:
                raise LTMConfigError(f"Failed to create backend of type: {self.config.backend_type}")
            
            # Initialize indexer if enabled
            self.indexer = MemoryIndexer() if self.config.indexing_enabled else None
            
            # Initialize policies
            self.retention_policy = RetentionPolicy(policy_type=self.config.retention_policy)
            self.consolidation_policy = ConsolidationPolicy()
            
            # Initialize state
            self._running = False
            self._background_tasks = set()
            self._last_consolidation = time.time()
            self._last_backup = time.time()
            
            # Ensure backup directory exists if backups are enabled
            if self.config.backup_enabled:
                os.makedirs(Path(self.config.backup_path), exist_ok=True)
                
            logger.info("LTM Manager initialized successfully")
            
        except ValidationError as e:
            logger.error(f"Invalid LTM Manager configuration: {e}")
            raise LTMConfigError(f"Invalid configuration: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize LTM Manager: {e}", exc_info=True)
            raise LTMConfigError(f"Initialization error: {e}")
    
    async def start(self) -> None:
        """
        Start the LTM Manager and its background tasks.
        
        This method initializes the backend connection and starts background tasks
        for memory consolidation and backups.
        
        Raises:
            LTMConnectionError: If the backend connection cannot be established.
        """
        try:
            logger.info("Starting LTM Manager")
            
            # Connect to the backend
            await self.backend.connect()
            
            # Start background tasks
            self._running = True
            self._start_background_task(self._consolidation_loop())
            
            if self.config.backup_enabled:
                self._start_background_task(self._backup_loop())
            
            logger.info("LTM Manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start LTM Manager: {e}", exc_info=True)
            self._running = False
            raise LTMConnectionError(f"Failed to start LTM Manager: {e}")
    
    async def stop(self) -> None:
        """
        Stop the LTM Manager and clean up resources.
        
        This method stops all background tasks and closes the backend connection.
        """
        logger.info("Stopping LTM Manager")
        self._running = False
        
        # Wait for background tasks to complete
        if self._background_tasks:
            logger.debug(f"Waiting for {len(self._background_tasks)} background tasks to complete")
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()
        
        # Disconnect from backend
        try:
            await self.backend.disconnect()
            logger.info("LTM Manager stopped successfully")
        except Exception as e:
            logger.error(f"Error disconnecting from backend: {e}", exc_info=True)
    
    async def store(self, content: Union[dict[str, Any], MemoryContent], 
                   metadata: Optional[Union[dict[str, Any], MemoryMetadata]] = None) -> str:
        """
        Store a new memory in the long-term memory store.
        
        Args:
            content: The content of the memory to store. Can be a dictionary or MemoryContent object.
            metadata: Optional metadata for the memory. Can be a dictionary or MemoryMetadata object.
                     If None, default metadata will be created.
        
        Returns:
            str: The ID of the stored memory.
        
        Raises:
            LTMValidationError: If the memory content or metadata is invalid.
            LTMOperationError: If the memory cannot be stored.
        """
        start_time = time.time()
        try:
            # Validate and prepare content
            if isinstance(content, dict):
                content = MemoryContent(**content)
            elif not isinstance(content, MemoryContent):
                raise LTMValidationError(f"Invalid content type: {type(content)}")
            
            # Create or validate metadata
            if metadata is None:
                metadata = MemoryMetadata(
                    created_at=datetime.datetime.now(),
                    importance=MemoryImportance.NORMAL,
                    status=MemoryStatus.ACTIVE
                )
            elif isinstance(metadata, dict):
                metadata = MemoryMetadata(**metadata)
            elif not isinstance(metadata, MemoryMetadata):
                raise LTMValidationError(f"Invalid metadata type: {type(metadata)}")
            
            # Generate a unique ID for the memory
            memory_id = str(uuid.uuid4())
            
            # Create the memory record
            memory = MemoryRecord(
                id=memory_id,
                content=content,
                metadata=metadata
            )
            
            # Store the memory in the backend
            logger.debug(f"Storing memory with ID: {memory_id}")
            await self.backend.store(memory)
            
            # Index the memory if indexing is enabled
            if self.indexer:
                await self.indexer.index_memory(memory)
            
            # Update metrics
            ltm_metrics.memory_store_count.inc()
            ltm_metrics.memory_store_latency.observe(time.time() - start_time)
            
            logger.info(f"Successfully stored memory with ID: {memory_id}")
            return memory_id
            
        except ValidationError as e:
            logger.error(f"Validation error when storing memory: {e}")
            raise LTMValidationError(f"Invalid memory data: {e}")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}", exc_info=True)
            ltm_metrics.memory_store_errors.inc()
            raise LTMOperationError(f"Failed to store memory: {e}")
    
    async def retrieve(self, memory_id: str) -> MemoryRecord:
        """
        Retrieve a memory by its ID.
        
        Args:
            memory_id: The ID of the memory to retrieve.
        
        Returns:
            MemoryRecord: The retrieved memory record.
        
        Raises:
            LTMMemoryNotFoundError: If the memory with the given ID does not exist.
            LTMOperationError: If the memory cannot be retrieved.
        """
        start_time = time.time()
        try:
            logger.debug(f"Retrieving memory with ID: {memory_id}")
            
            # Retrieve the memory from the backend
            memory = await self.backend.retrieve(memory_id)
            
            if not memory:
                logger.warning(f"Memory with ID {memory_id} not found")
                raise LTMMemoryNotFoundError(f"Memory with ID {memory_id} not found")
            
            # Update access timestamp in metadata
            memory.metadata.last_accessed = datetime.datetime.now()
            memory.metadata.access_count += 1
            
            # Update the memory in the backend to reflect the access
            await self.backend.update(memory)
            
            # Update metrics
            ltm_metrics.memory_retrieve_count.inc()
            ltm_metrics.memory_retrieve_latency.observe(time.time() - start_time)
            
            logger.debug(f"Successfully retrieved memory with ID: {memory_id}")
            return memory
            
        except LTMMemoryNotFoundError:
            # Re-raise the not found error
            ltm_metrics.memory_not_found_count.inc()
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve memory with ID {memory_id}: {e}", exc_info=True)
            ltm_metrics.memory_retrieve_errors.inc()
            raise LTMOperationError(f"Failed to retrieve memory: {e}")
    
    async def search(self, query: str, limit: int = 10, 
                    filters: Optional[dict[str, Any]] = None) -> list[MemoryRecord]:
        """
        Search for memories matching the given query.
        
        Args:
            query: The search query string.
            limit: Maximum number of results to return.
            filters: Optional filters to apply to the search results.
        
        Returns:
            List[MemoryRecord]: A list of memory records matching the query.
        
        Raises:
            LTMOperationError: If the search operation fails.
        """
        start_time = time.time()
        try:
            logger.debug(f"Searching memories with query: '{query}', limit: {limit}")
            
            # Use the indexer for search if available, otherwise fall back to backend
            if self.indexer and query:
                memory_ids = await self.indexer.search(query, limit, filters)
                memories = []
                for memory_id in memory_ids:
                    try:
                        memory = await self.backend.retrieve(memory_id)
                        if memory:
                            memories.append(memory)
                    except Exception as e:
                        logger.warning(f"Failed to retrieve indexed memory {memory_id}: {e}")
            else:
                # Fall back to backend search
                memories = await self.backend.search(query, limit, filters)
            
            # Update access timestamps for retrieved memories
            now = datetime.datetime.now()
            for memory in memories:
                memory.metadata.last_accessed = now
                memory.metadata.access_count += 1
            
            # Batch update the memories in the backend
            if memories:
                await self._batch_update_memories(memories)
            
            # Update metrics
            ltm_metrics.memory_search_count.inc()
            ltm_metrics.memory_search_latency.observe(time.time() - start_time)
            ltm_metrics.memory_search_results.observe(len(memories))
            
            logger.info(f"Search for '{query}' returned {len(memories)} results")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories with query '{query}': {e}", exc_info=True)
            ltm_metrics.memory_search_errors.inc()
            raise LTMOperationError(f"Failed to search memories: {e}")
    
    async def update(self, memory_id: str, 
                    content: Optional[Union[dict[str, Any], MemoryContent]] = None,
                    metadata: Optional[Union[dict[str, Any], MemoryMetadata]] = None) -> None:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update.
            content: Optional new content for the memory. If None, content will not be updated.
            metadata: Optional new metadata for the memory. If None, metadata will not be updated.
        
        Raises:
            LTMMemoryNotFoundError: If the memory with the given ID does not exist.
            LTMValidationError: If the updated content or metadata is invalid.
            LTMOperationError: If the memory cannot be updated.
        """
        start_time = time.time()
        try:
            logger.debug(f"Updating memory with ID: {memory_id}")
            
            # Retrieve the existing memory
            memory = await self.backend.retrieve(memory_id)
            
            if not memory:
                logger.warning(f"Memory with ID {memory_id} not found for update")
                raise LTMMemoryNotFoundError(f"Memory with ID {memory_id} not found")
            
            # Update content if provided
            if content:
                if isinstance(content, dict):
                    content = MemoryContent(**content)
                elif not isinstance(content, MemoryContent):
                    raise LTMValidationError(f"Invalid content type: {type(content)}")
                memory.content = content
            
            # Update metadata if provided
            if metadata:
                if isinstance(metadata, dict):
                    # Preserve existing fields not in the update
                    updated_metadata = memory.metadata.dict()
                    updated_metadata.update(metadata)
                    metadata = MemoryMetadata(**updated_metadata)
                elif not isinstance(metadata, MemoryMetadata):
                    raise LTMValidationError(f"Invalid metadata type: {type(metadata)}")
                memory.metadata = metadata
            
            # Always update the modified timestamp
            memory.metadata.modified_at = datetime.datetime.now()
            
            # Update the memory in the backend
            await self.backend.update(memory)
            
            # Update the index if indexing is enabled
            if self.indexer:
                await self.indexer.update_index(memory)
            
            # Update metrics
            ltm_metrics.memory_update_count.inc()
            ltm_metrics.memory_update_latency.observe(time.time() - start_time)
            
            logger.info(f"Successfully updated memory with ID: {memory_id}")
            
        except ValidationError as e:
            logger.error(f"Validation error when updating memory {memory_id}: {e}")
            raise LTMValidationError(f"Invalid memory data: {e}")
        except LTMMemoryNotFoundError:
            # Re-raise the not found error
            raise
        except Exception as e:
            logger.error(f"Failed to update memory with ID {memory_id}: {e}", exc_info=True)
            ltm_metrics.memory_update_errors.inc()
            raise LTMOperationError(f"Failed to update memory: {e}")
    
    async def delete(self, memory_id: str, permanent: bool = False) -> None:
        """
        Delete a memory from the long-term memory store.
        
        Args:
            memory_id: The ID of the memory to delete.
            permanent: If True, permanently delete the memory. If False, mark it as deleted.
        
        Raises:
            LTMMemoryNotFoundError: If the memory with the given ID does not exist.
            LTMOperationError: If the memory cannot be deleted.
        """
        start_time = time.time()
        try:
            logger.debug(f"Deleting memory with ID: {memory_id}, permanent: {permanent}")
            
            if not permanent:
                # Soft delete - mark the memory as deleted
                memory = await self.backend.retrieve(memory_id)
                
                if not memory:
                    logger.warning(f"Memory with ID {memory_id} not found for deletion")
                    raise LTMMemoryNotFoundError(f"Memory with ID {memory_id} not found")
                
                memory.metadata.status = MemoryStatus.DELETED
                memory.metadata.modified_at = datetime.datetime.now()
                
                await self.backend.update(memory)
                
                # Update the index if indexing is enabled
                if self.indexer:
                    await self.indexer.update_index(memory)
            else:
                # Hard delete - remove the memory completely
                result = await self.backend.delete(memory_id)
                
                if not result:
                    logger.warning(f"Memory with ID {memory_id} not found for permanent deletion")
                    raise LTMMemoryNotFoundError(f"Memory with ID {memory_id} not found")
                
                # Remove from index if indexing is enabled
                if self.indexer:
                    await self.indexer.remove_from_index(memory_id)
            
            # Update metrics
            ltm_metrics.memory_delete_count.inc()
            ltm_metrics.memory_delete_latency.observe(time.time() - start_time)
            
            logger.info(f"Successfully {'permanently ' if permanent else ''}deleted memory with ID: {memory_id}")
            
        except LTMMemoryNotFoundError:
            # Re-raise the not found error
            raise
        except Exception as e:
            logger.error(f"Failed to delete memory with ID {memory_id}: {e}", exc_info=True)
            ltm_metrics.memory_delete_errors.inc()
            raise LTMOperationError(f"Failed to delete memory: {e}")
    
    async def consolidate(self) -> int:
        """
        Manually trigger memory consolidation.
        
        This process applies retention policies, optimizes storage, and
        performs other maintenance tasks on the long-term memory store.
        
        Returns:
            int: The number of memories processed during consolidation.
        
        Raises:
            LTMOperationError: If the consolidation process fails.
        """
        start_time = time.time()
        try:
            logger.info("Starting manual memory consolidation")
            
            # Get memories that need consolidation
            memories_to_process = await self._get_memories_for_consolidation()
            
            if not memories_to_process:
                logger.info("No memories require consolidation")
                return 0
            
            # Apply retention policy
            memories_to_keep, memories_to_archive = await self._apply_retention_policy(memories_to_process)
            
            # Update kept memories
            if memories_to_keep:
                await self._batch_update_memories(memories_to_keep)
            
            # Archive memories
            if memories_to_archive:
                for memory in memories_to_archive:
                    memory.metadata.status = MemoryStatus.ARCHIVED
                    memory.metadata.modified_at = datetime.datetime.now()
                
                await self._batch_update_memories(memories_to_archive)
            
            # Update metrics
            ltm_metrics.memory_consolidation_count.inc()
            ltm_metrics.memory_consolidation_latency.observe(time.time() - start_time)
            ltm_metrics.memories_archived.inc(len(memories_to_archive))
            
            total_processed = len(memories_to_keep) + len(memories_to_archive)
            logger.info(f"Consolidation complete. Processed {total_processed} memories, archived {len(memories_to_archive)}")
            
            return total_processed
            
        except Exception as e:
            logger.error(f"Failed to consolidate memories: {e}", exc_info=True)
            ltm_metrics.memory_consolidation_errors.inc()
            raise LTMOperationError(f"Failed to consolidate memories: {e}")
    
    async def backup(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the long-term memory store.
        
        Args:
            backup_path: Optional path where the backup should be stored.
                        If None, the default path from configuration will be used.
        
        Returns:
            str: The path to the created backup file.
        
        Raises:
            LTMOperationError: If the backup process fails.
        """
        start_time = time.time()
        try:
            # Use provided path or default from config
            path = backup_path or self.config.backup_path
            os.makedirs(Path(path), exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(path, f"ltm_backup_{timestamp}.json")
            
            logger.info(f"Starting backup to {backup_file}")
            
            # Get all memories from the backend
            memories = await self.backend.get_all()
            
            # Serialize memories to JSON
            serialized_memories = [memory.dict() for memory in memories]
            
            # Write to backup file
            async with aiofiles.open(backup_file, 'w') as f:
                await f.write(json.dumps(serialized_memories, default=str, indent=2))
            
            # Update metrics
            ltm_metrics.memory_backup_count.inc()
            ltm_metrics.memory_backup_latency.observe(time.time() - start_time)
            ltm_metrics.memories_backed_up.set(len(memories))
            
            logger.info(f"Backup complete. {len(memories)} memories backed up to {backup_file}")
            
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}", exc_info=True)
            ltm_metrics.memory_backup_errors.inc()
            raise LTMOperationError(f"Failed to create backup: {e}")
    
    async def restore(self, backup_file: str) -> int:
        """
        Restore the long-term memory store from a backup.
        
        Args:
            backup_file: Path to the backup file to restore from.
        
        Returns:
            int: The number of memories restored.
        
        Raises:
            LTMOperationError: If the restore process fails.
        """
        start_time = time.time()
        try:
            logger.info(f"Starting restore from {backup_file}")
            
            # Read backup file
            async with aiofiles.open(backup_file, 'r') as f:
                content = await f.read()
            
            serialized_memories = json.loads(content)
            
            # Deserialize memories
            memories = []
            for mem_dict in serialized_memories:
                try:
                    memory = MemoryRecord(**mem_dict)
                    memories.append(memory)
                except ValidationError as e:
                    logger.warning(f"Skipping invalid memory during restore: {e}")
            
            # Clear existing memories if needed
            # This is commented out for safety - uncomment if full replacement is desired
            # await self.backend.clear()
            
            # Restore memories in batches
            restored_count = 0
            batch_size = self.config.max_batch_size
            
            for i in range(0, len(memories), batch_size):
                batch = memories[i:i+batch_size]
                for memory in batch:
                    await self.backend.store(memory)
                    restored_count += 1
                
                logger.debug(f"Restored batch of {len(batch)} memories")
            
            # Rebuild index if indexing is enabled
            if self.indexer:
                logger.info("Rebuilding memory index")
                await self.indexer.rebuild_index(memories)
            
            # Update metrics
            ltm_metrics.memory_restore_count.inc()
            ltm_metrics.memory_restore_latency.observe(time.time() - start_time)
            ltm_metrics.memories_restored.inc(restored_count)
            
            logger.info(f"Restore complete. {restored_count} memories restored from {backup_file}")
            
            return restored_count
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}", exc_info=True)
            ltm_metrics.memory_restore_errors.inc()
            raise LTMOperationError(f"Failed to restore from backup: {e}")
    
    async def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the long-term memory store.
        
        Returns:
            Dict[str, Any]: Statistics about the memory store.
        
        Raises:
            LTMOperationError: If the statistics cannot be retrieved.
        """
        try:
            logger.debug("Retrieving LTM statistics")
            
            # Get basic stats from backend
            total_count = await self.backend.count()
            
            # Get counts by status
            active_count = await self.backend.count({"metadata.status": MemoryStatus.ACTIVE})
            archived_count = await self.backend.count({"metadata.status": MemoryStatus.ARCHIVED})
            deleted_count = await self.backend.count({"metadata.status": MemoryStatus.DELETED})
            
            # Get counts by importance
            high_importance = await self.backend.count({"metadata.importance": MemoryImportance.HIGH})
            normal_importance = await self.backend.count({"metadata.importance": MemoryImportance.NORMAL})
            low_importance = await self.backend.count({"metadata.importance": MemoryImportance.LOW})
            
            # Get time-based stats
            now = datetime.datetime.now()
            one_day_ago = now - datetime.timedelta(days=1)
            one_week_ago = now - datetime.timedelta(weeks=1)
            
            created_last_day = await self.backend.count({"metadata.created_at": {"$gte": one_day_ago}})
            created_last_week = await self.backend.count({"metadata.created_at": {"$gte": one_week_ago}})
            
            accessed_last_day = await self.backend.count({"metadata.last_accessed": {"$gte": one_day_ago}})
            accessed_last_week = await self.backend.count({"metadata.last_accessed": {"$gte": one_week_ago}})
            
            # Compile stats
            stats = {
                "total_memories": total_count,
                "status": {
                    "active": active_count,
                    "archived": archived_count,
                    "deleted": deleted_count
                },
                "importance": {
                    "high": high_importance,
                    "normal": normal_importance,
                    "low": low_importance
                },
                "activity": {
                    "created_last_day": created_last_day,
                    "created_last_week": created_last_week,
                    "accessed_last_day": accessed_last_day,
                    "accessed_last_week": accessed_last_week
                },
                "backend_type": self.config.backend_type,
                "indexing_enabled": self.config.indexing_enabled,
                "last_consolidation": datetime.datetime.fromtimestamp(self._last_consolidation),
                "last_backup": datetime.datetime.fromtimestamp(self._last_backup) if self.config.backup_enabled else None
            }
            
            logger.debug("Successfully retrieved LTM statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to retrieve LTM statistics: {e}", exc_info=True)
            raise LTMOperationError(f"Failed to retrieve statistics: {e}")
    
    def _start_background_task(self, coro):
        """
        Start a background task and add it to the set of tracked tasks.
        
        Args:
            coro: The coroutine to run as a background task.
        """
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    
    async def _consolidation_loop(self):
        """
        Background task that periodically consolidates memories.
        """
        logger.info("Starting memory consolidation background task")
        while self._running:
            try:
                current_time = time.time()
                if current_time - self._last_consolidation >= self.config.consolidation_interval:
                    logger.info("Running scheduled memory consolidation")
                    await self.consolidate()
                    self._last_consolidation = current_time
                
                # Sleep for a while before checking again
                await asyncio.sleep(min(60, self.config.consolidation_interval / 10))
                
            except asyncio.CancelledError:
                logger.info("Memory consolidation task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in memory consolidation task: {e}", exc_info=True)
                # Sleep before retrying to avoid tight error loops
                await asyncio.sleep(60)
    
    async def _backup_loop(self):
        """
        Background task that periodically backs up the memory store.
        """
        logger.info("Starting memory backup background task")
        while self._running and self.config.backup_enabled:
            try:
                current_time = time.time()
                if current_time - self._last_backup >= self.config.backup_interval:
                    logger.info("Running scheduled memory backup")
                    await self.backup()
                    self._last_backup = current_time
                
                # Sleep for a while before checking again
                await asyncio.sleep(min(300, self.config.backup_interval / 10))
                
            except asyncio.CancelledError:
                logger.info("Memory backup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in memory backup task: {e}", exc_info=True)
                # Sleep before retrying to avoid tight error loops
                await asyncio.sleep(300)
    
    async def _get_memories_for_consolidation(self) -> list[MemoryRecord]:
        """
        Get memories that need consolidation based on the consolidation policy.
        
        Returns:
            List[MemoryRecord]: List of memories that need consolidation.
        """
        # Get active memories that haven't been consolidated recently
        # The specific criteria can be adjusted based on the consolidation policy
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=7)
        
        filters = {
            "metadata.status": MemoryStatus.ACTIVE,
            "$or": [
                {"metadata.last_consolidated": None},
                {"metadata.last_consolidated": {"$lt": cutoff_time}}
            ]
        }
        
        memories = await self.backend.search("", limit=self.config.max_batch_size, filters=filters)
        return memories
    
    async def _apply_retention_policy(self, memories: list[MemoryRecord]) -> tuple[list[MemoryRecord], list[MemoryRecord]]:
        """
        Apply the retention policy to determine which memories to keep and which to archive.
        
        Args:
            memories: List of memories to evaluate.
            
        Returns:
            Tuple[List[MemoryRecord], List[MemoryRecord]]: Memories to keep and memories to archive.
        """
        memories_to_keep = []
        memories_to_archive = []
        
        now = datetime.datetime.now()
        
        for memory in memories:
            # Apply retention policy based on importance, age, and access patterns
            should_retain = await self.retention_policy.should_retain(memory)
            
            if should_retain:
                # Update consolidation timestamp
                memory.metadata.last_consolidated = now
                memories_to_keep.append(memory)
            else:
                memories_to_archive.append(memory)
        
        return memories_to_keep, memories_to_archive
    
    async def _batch_update_memories(self, memories: list[MemoryRecord]) -> None:
        """
        Update multiple memories in batches.
        
        Args:
            memories: List of memories to update.
        """
        batch_size = self.config.max_batch_size
        
        for i in range(0, len(memories), batch_size):
            batch = memories[i:i+batch_size]
            update_tasks = [self.backend.update(memory) for memory in batch]
            await asyncio.gather(*update_tasks)
            
            # Update indices if indexing is enabled
            if self.indexer:
                index_tasks = [self.indexer.update_index(memory) for memory in batch]
                await asyncio.gather(*index_tasks)