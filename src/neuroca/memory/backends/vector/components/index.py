"""
Vector Index Component

This module provides the VectorIndex class for managing vector embeddings,
including storage, retrieval, and similarity-based search operations.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from neuroca.memory.backends.vector.components.models import VectorEntry
from neuroca.memory.exceptions import StorageOperationError

logger = logging.getLogger(__name__)


class VectorIndex:
    """
    Vector index implementation for storage and similarity search.
    
    This class provides:
    - Storage and indexing of vector embeddings
    - Fast similarity search using cosine similarity
    - Support for metadata filtering
    - Efficient batch operations
    
    The implementation uses NumPy for vector operations, making it
    efficient for moderately-sized vector collections. For larger-scale
    production use, this could be replaced with optimized vector
    database backends like FAISS or Milvus.
    """
    
    def __init__(self, dimension: int = 768):
        """
        Initialize the vector index.
        
        Args:
            dimension: Dimensionality of the vectors to store
        """
        self.dimension = dimension
        self.entries: Dict[str, VectorEntry] = {}
        self.vectors: Optional[np.ndarray] = None
        self.ids: List[str] = []
        self._dirty = False
        
        logger.debug(f"Initialized vector index with dimension {dimension}")
    
    def add(self, entry: VectorEntry) -> None:
        """
        Add an entry to the index.
        
        Args:
            entry: Vector entry to add
            
        Raises:
            ValueError: If vector dimension doesn't match the index
        """
        if len(entry.vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(entry.vector)}")
        
        self.entries[entry.id] = entry
        self._dirty = True
        logger.debug(f"Added entry with ID {entry.id} to vector index")
    
    def update(self, entry: VectorEntry) -> None:
        """
        Update an existing entry in the index.
        
        Args:
            entry: Vector entry to update
            
        Raises:
            KeyError: If entry with ID doesn't exist
            ValueError: If vector dimension doesn't match the index
        """
        if entry.id not in self.entries:
            raise KeyError(f"Entry with ID {entry.id} not found")
        
        if len(entry.vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(entry.vector)}")
        
        self.entries[entry.id] = entry
        self._dirty = True
        logger.debug(f"Updated entry with ID {entry.id} in vector index")
    
    def delete(self, entry_id: str) -> bool:
        """
        Delete an entry from the index.
        
        Args:
            entry_id: ID of the entry to delete
            
        Returns:
            bool: True if entry was deleted, False if not found
        """
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._dirty = True
            logger.debug(f"Deleted entry with ID {entry_id} from vector index")
            return True
        return False
    
    def get(self, entry_id: str) -> Optional[VectorEntry]:
        """
        Get an entry by ID.
        
        Args:
            entry_id: ID of the entry to retrieve
            
        Returns:
            The vector entry if found, None otherwise
        """
        return self.entries.get(entry_id)
    
    def _rebuild_index(self) -> None:
        """
        Rebuild the search index.
        
        This creates a NumPy array of all vectors for efficient similarity
        search operations. The index is only rebuilt when needed, as indicated
        by the _dirty flag.
        """
        if not self.entries:
            self.vectors = None
            self.ids = []
            self._dirty = False
            logger.debug("Rebuilt empty vector index")
            return
            
        self.ids = list(self.entries.keys())
        self.vectors = np.array([self.entries[id].vector for id in self.ids])
        self._dirty = False
        logger.debug(f"Rebuilt vector index with {len(self.ids)} entries")
    
    def search(
        self, 
        query_vector: List[float], 
        k: int = 10, 
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
        similarity_threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Vector to search for
            k: Maximum number of results to return
            filter_fn: Optional function to filter results by metadata
            similarity_threshold: Minimum similarity score for results
            
        Returns:
            List of (id, similarity) tuples, sorted by similarity (highest first)
            
        Raises:
            ValueError: If query vector dimension doesn't match the index
        """
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension mismatch: expected {self.dimension}, got {len(query_vector)}")
            
        if self._dirty or self.vectors is None:
            self._rebuild_index()
        
        if not self.entries:
            logger.debug("Search on empty vector index returned no results")
            return []
        
        # Convert query to numpy array
        query_array = np.array(query_vector)
        
        # Compute cosine similarity
        # First normalize vectors for cosine similarity
        norm_query = query_array / np.linalg.norm(query_array)
        norm_vectors = self.vectors / np.linalg.norm(self.vectors, axis=1, keepdims=True)
        similarities = np.dot(norm_vectors, norm_query)
        
        # Sort by similarity
        indices = np.argsort(similarities)[::-1]  # Descending order
        
        # Filter results if filter_fn is provided
        results = []
        for idx in indices:
            similarity = float(similarities[idx])
            
            # Skip results below threshold
            if similarity < similarity_threshold:
                continue
            
            entry_id = self.ids[idx]
            entry = self.entries[entry_id]
            
            if filter_fn is None or filter_fn(entry.metadata):
                results.append((entry_id, similarity))
                if len(results) >= k:
                    break
        
        logger.debug(f"Search returned {len(results)} results")
        return results
    
    def batch_add(self, entries: List[VectorEntry]) -> None:
        """
        Add multiple entries to the index in a batch.
        
        Args:
            entries: List of vector entries to add
            
        Raises:
            ValueError: If any vector dimension doesn't match the index
        """
        for entry in entries:
            if len(entry.vector) != self.dimension:
                raise ValueError(f"Vector dimension mismatch for ID {entry.id}: expected {self.dimension}, got {len(entry.vector)}")
            
            self.entries[entry.id] = entry
        
        self._dirty = True
        logger.debug(f"Added {len(entries)} entries to vector index in batch")
    
    def batch_delete(self, entry_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple entries from the index in a batch.
        
        Args:
            entry_ids: List of entry IDs to delete
            
        Returns:
            Dict mapping entry IDs to deletion success (True if deleted, False if not found)
        """
        results = {}
        for entry_id in entry_ids:
            results[entry_id] = entry_id in self.entries
            if results[entry_id]:
                del self.entries[entry_id]
        
        if any(results.values()):
            self._dirty = True
            
        logger.debug(f"Deleted {sum(1 for success in results.values() if success)} out of {len(entry_ids)} entries from vector index in batch")
        return results
    
    def count(self) -> int:
        """
        Get the number of entries in the index.
        
        Returns:
            Number of entries in the index
        """
        return len(self.entries)
    
    def clear(self) -> None:
        """Clear the index of all entries."""
        self.entries.clear()
        self.vectors = None
        self.ids = []
        self._dirty = False
        logger.debug("Cleared vector index")
    
    def get_entry_ids(self) -> List[str]:
        """
        Get all entry IDs in the index.
        
        Returns:
            List of all entry IDs
        """
        return list(self.entries.keys())
    
    def get_entries(self) -> List[VectorEntry]:
        """
        Get all entries in the index.
        
        Returns:
            List of all vector entries
        """
        return list(self.entries.values())
    
    def get_entries_by_ids(self, entry_ids: List[str]) -> Dict[str, Optional[VectorEntry]]:
        """
        Get multiple entries by their IDs.
        
        Args:
            entry_ids: List of entry IDs to retrieve
            
        Returns:
            Dict mapping entry IDs to their entries (None if not found)
        """
        return {entry_id: self.entries.get(entry_id) for entry_id in entry_ids}
