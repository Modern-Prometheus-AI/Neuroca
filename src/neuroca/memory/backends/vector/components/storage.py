"""
Vector Storage Component

This module provides the VectorStorage class for managing the persistence
of vector data to disk, including loading and saving vector indices.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.vector.components.models import VectorEntry
from neuroca.memory.backends.vector.components.index import VectorIndex
from neuroca.memory.exceptions import StorageBackendError, StorageInitializationError

logger = logging.getLogger(__name__)


class VectorStorage:
    """
    Vector storage component for persistence management.
    
    This class is responsible for:
    - Loading vector indices from disk
    - Saving vector indices to disk
    - Managing metadata associated with stored vectors
    
    It acts as a persistence layer for the vector index, ensuring that
    vector data can be persisted between application restarts.
    """
    
    def __init__(
        self, 
        index: VectorIndex,
        index_path: Optional[str] = None
    ):
        """
        Initialize the vector storage component.
        
        Args:
            index: The vector index to manage
            index_path: Optional path to persist the index
        """
        self.index = index
        self.index_path = index_path
        self._memory_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        logger.debug(f"Initialized vector storage with {'persistence' if index_path else 'no persistence'}")
    
    async def initialize(self) -> None:
        """
        Initialize the vector storage.
        
        This loads the index from disk if a path is provided.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Load index from disk if path is provided
            if self.index_path and os.path.exists(self.index_path):
                await self.load()
            
            logger.info(f"Initialized vector storage with {self.index.count()} entries")
        except Exception as e:
            error_msg = f"Failed to initialize vector storage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def load(self) -> bool:
        """
        Load the index from disk.
        
        Returns:
            bool: True if loaded successfully, False otherwise
            
        Raises:
            StorageBackendError: If loading fails
        """
        if not self.index_path:
            logger.debug("No index path provided, skipping load")
            return False
        
        try:
            if not os.path.exists(self.index_path):
                logger.warning(f"Index file {self.index_path} not found, starting with empty index")
                return False
            
            async with self._lock:
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                
                # Clear existing index
                self.index.clear()
                
                # Load entries
                entries_data = data.get("entries", [])
                entries = []
                for entry_data in entries_data:
                    entry = VectorEntry.from_dict(entry_data)
                    entries.append(entry)
                
                # Add all entries at once
                if entries:
                    self.index.batch_add(entries)
                
                # Load memory metadata
                self._memory_metadata = data.get("memory_metadata", {})
                
                logger.info(f"Loaded vector index from {self.index_path} with {self.index.count()} entries")
                return True
                
        except Exception as e:
            error_msg = f"Failed to load index from {self.index_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def save(self) -> bool:
        """
        Save the index to disk.
        
        Returns:
            bool: True if saved successfully, False otherwise
            
        Raises:
            StorageBackendError: If saving fails
        """
        if not self.index_path:
            logger.debug("No index path provided, skipping save")
            return False
        
        try:
            async with self._lock:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
                
                # Prepare data for serialization
                data = {
                    "entries": [entry.to_dict() for entry in self.index.get_entries()],
                    "memory_metadata": self._memory_metadata
                }
                
                # Write to file
                with open(self.index_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.debug(f"Saved vector index to {self.index_path} with {self.index.count()} entries")
                return True
                
        except Exception as e:
            error_msg = f"Failed to save index to {self.index_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    def get_memory_metadata(self, memory_id: str) -> Dict[str, Any]:
        """
        Get metadata for a memory item.
        
        Args:
            memory_id: The ID of the memory item
            
        Returns:
            Dict containing the metadata for the memory item,
            or an empty dict if not found
        """
        return self._memory_metadata.get(memory_id, {})
    
    def set_memory_metadata(self, memory_id: str, metadata: Dict[str, Any]) -> None:
        """
        Set metadata for a memory item.
        
        Args:
            memory_id: The ID of the memory item
            metadata: The metadata to set
        """
        self._memory_metadata[memory_id] = metadata
    
    def delete_memory_metadata(self, memory_id: str) -> bool:
        """
        Delete metadata for a memory item.
        
        Args:
            memory_id: The ID of the memory item
            
        Returns:
            bool: True if deleted, False if not found
        """
        if memory_id in self._memory_metadata:
            del self._memory_metadata[memory_id]
            return True
        return False
    
    def get_all_memory_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all memory items.
        
        Returns:
            Dict mapping memory IDs to their metadata
        """
        return self._memory_metadata.copy()
