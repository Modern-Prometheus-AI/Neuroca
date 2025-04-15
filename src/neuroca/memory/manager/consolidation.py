"""
Memory Manager Consolidation

This module handles the consolidation of memories between tiers
(STM -> MTM -> LTM) based on importance, access patterns, and age.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from neuroca.memory.backends import MemoryTier
from neuroca.memory.models.memory_item import MemoryItem, MemoryMetadata, MemoryStatus
# Define priority enum for MTM memories since no longer imported from mtm.storage
from enum import Enum

class MemoryPriority(str, Enum):
    """Priority levels for MTM memories."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Use the same MemoryStatus for MTM
MTMStatus = MemoryStatus

# Configure logger
logger = logging.getLogger(__name__)


class StandardMemoryConsolidator:
    """
    Standard implementation of memory consolidation.
    
    This class handles the consolidation of memories between different tiers
    (STM -> MTM -> LTM) based on importance, access patterns, and age.
    """
    
    def __init__(self):
        """Initialize the memory consolidator."""
        self.config = {}
    
    async def consolidate_stm_to_mtm(self, stm_storage, mtm_storage):
        """
        Consolidate important memories from STM to MTM.
        
        Args:
            stm_storage: STM storage backend
            mtm_storage: MTM storage backend
        """
        await consolidate_stm_to_mtm(stm_storage, mtm_storage, self.config)
    
    async def consolidate_mtm_to_ltm(self, mtm_storage, ltm_storage):
        """
        Consolidate important memories from MTM to LTM.
        
        Args:
            mtm_storage: MTM storage backend
            ltm_storage: LTM storage backend
        """
        await consolidate_mtm_to_ltm(mtm_storage, ltm_storage, self.config)
    
    def configure(self, config):
        """
        Configure the consolidator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
    
    async def consolidate(self, stm_storage, mtm_storage, ltm_storage):
        """
        Perform full consolidation across all tiers.
        
        Args:
            stm_storage: STM storage backend
            mtm_storage: MTM storage backend
            ltm_storage: LTM storage backend
        """
        await self.consolidate_stm_to_mtm(stm_storage, mtm_storage)
        await self.consolidate_mtm_to_ltm(mtm_storage, ltm_storage)


async def consolidate_stm_to_mtm(
    stm_storage,
    mtm_storage,
    config: Dict[str, Any]
) -> None:
    """Consolidate important memories from STM to MTM."""
    logger.debug("Starting STM to MTM consolidation")
    
    # Get items from STM
    try:
        # Get all STM items
        stm_items = await stm_storage.retrieve_all()
        
        # Skip if no items
        if not stm_items:
            return
        
        # Prioritize items for consolidation
        # (This is a simplified approach - a more sophisticated prioritization could be implemented)
        candidates = []
        for item in stm_items:
            if not item:
                continue
                
            # Get importance
            importance = 0.5
            if isinstance(item, dict) and "metadata" in item and isinstance(item["metadata"], dict):
                importance = item["metadata"].get("importance", 0.5)
            
            # Get access count
            access_count = 0
            if isinstance(item, dict) and "access_count" in item:
                access_count = item.get("access_count", 0)
            
            # Calculate priority score
            priority_score = importance * (0.5 + (0.5 * min(access_count, 10) / 10))
            
            # Add to candidates if priority is high enough
            if priority_score >= 0.6:  # Threshold for STM->MTM consolidation
                candidates.append((item, priority_score))
        
        # Sort by priority score (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N candidates (limit batch size)
        batch_size = min(len(candidates), config.get("consolidation_batch_size", 5))
        top_candidates = candidates[:batch_size]
        
        # Consolidate top candidates
        for item, score in top_candidates:
            try:
                # Get the item ID
                item_id = item.get("id")
                if not item_id:
                    continue
                
                # Extract content and metadata
                content = item.get("content", {})
                metadata = item.get("metadata", {})
                tags = metadata.get("tags", [])
                importance = metadata.get("importance", 0.5)
                
                # Determine priority based on importance
                priority = MemoryPriority.MEDIUM
                if importance >= 0.8:
                    priority = MemoryPriority.HIGH
                elif importance >= 0.5:
                    priority = MemoryPriority.MEDIUM
                else:
                    priority = MemoryPriority.LOW
                
                # Store in MTM
                mtm_id = await mtm_storage.store(
                    content=content,
                    tags=tags,
                    priority=priority,
                    metadata=metadata
                )
                
                # If successful, delete from STM
                if mtm_id:
                    await stm_storage.delete(item_id)
                    logger.info(f"Consolidated memory {item_id} from STM to MTM (new ID: {mtm_id})")
            
            except Exception as e:
                logger.error(f"Error consolidating STM memory: {str(e)}")
                continue
    
    except Exception as e:
        logger.error(f"Error in STM to MTM consolidation: {str(e)}")


async def consolidate_mtm_to_ltm(
    mtm_storage,
    ltm_storage,
    config: Dict[str, Any]
) -> None:
    """Consolidate important memories from MTM to LTM."""
    logger.debug("Starting MTM to LTM consolidation")
    
    try:
        # Get candidates from MTM
        # Focus on high priority, frequently accessed, and older memories
        mtm_memories = await mtm_storage.search(
            min_priority=MemoryPriority.HIGH
        )
        
        # Skip if no candidates
        if not mtm_memories:
            return
        
        # Prioritize candidates
        candidates = []
        for memory in mtm_memories:
            if not memory:
                continue
            
            # Get age in days
            age_days = 0
            if hasattr(memory, "created_at") and memory.created_at:
                age_days = (datetime.now() - memory.created_at).days
            
            # Get access count
            access_count = getattr(memory, "access_count", 0)
            
            # Get importance
            importance = 0.5
            if hasattr(memory, "metadata") and memory.metadata:
                if isinstance(memory.metadata, dict) and "importance" in memory.metadata:
                    importance = memory.metadata.get("importance", 0.5)
            
            # Calculate priority score for MTM->LTM consolidation
            # Favor: high importance, high access count, older memories
            priority_score = (
                importance * 0.5 +
                min(access_count, 20) / 20 * 0.3 +
                min(age_days, 30) / 30 * 0.2
            )
            
            # Add to candidates if score is high enough
            if priority_score >= 0.7:  # Threshold for MTM->LTM
                candidates.append((memory, priority_score))
        
        # Sort and limit
        candidates.sort(key=lambda x: x[1], reverse=True)
        batch_size = min(len(candidates), config.get("consolidation_batch_size", 3))
        top_candidates = candidates[:batch_size]
        
        # Consolidate top candidates
        for memory, score in top_candidates:
            try:
                # Get the memory ID
                memory_id = getattr(memory, "id", None)
                if not memory_id:
                    continue
                
                # Extract content and metadata
                content = getattr(memory, "content", {})
                summary = f"Summary of MTM memory: {str(content)[:100]}..."  # Basic summary
                
                # Get tags from MTM memory
                tags = []
                if hasattr(memory, "tags"):
                    tags = memory.tags
                
                # Get importance
                importance = 0.5
                if hasattr(memory, "metadata") and memory.metadata:
                    if isinstance(memory.metadata, dict) and "importance" in memory.metadata:
                        importance = memory.metadata.get("importance", 0.5)
                
                # Store in LTM
                memory_item = MemoryItem(
                    content=content,
                    summary=summary,
                    metadata=MemoryMetadata(
                        status=MemoryStatus.ACTIVE,
                        tags=tags,
                        importance=importance,
                        created_at=datetime.now(),
                        source="mtm_consolidation"
                    )
                )
                
                # Store in LTM
                ltm_id = await ltm_storage.store(memory_item)
                
                if ltm_id:
                    # Mark as consolidated in MTM
                    await mtm_storage.consolidate_memory(memory_id)
                    logger.info(f"Consolidated memory {memory_id} from MTM to LTM (new ID: {ltm_id})")
            
            except Exception as e:
                logger.error(f"Error consolidating MTM memory: {str(e)}")
                continue
    
    except Exception as e:
        logger.error(f"Error in MTM to LTM consolidation: {str(e)}")
