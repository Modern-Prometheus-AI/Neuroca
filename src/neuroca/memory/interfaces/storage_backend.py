"""
Storage Backend Interface

This module defines the abstract interface for storage backends in the Neuroca memory system.
Storage backends are responsible for the low-level persistence of memory items,
handling the direct interaction with specific database technologies like Redis, SQL, or vector databases.

These backends know nothing about memory tiers or the memory manager - they simply
provide efficient, reliable storage and retrieval of data with their specific technology.
"""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


class StorageBackendInterface(abc.ABC):
    """
    Abstract Base Class defining the interface for all storage backends.
    
    Implementations of this interface handle direct interaction with specific
    database technologies (Redis, SQL, Vector DB, etc.) for storing, retrieving,
    and querying memory data.
    
    Storage backends are responsible for:
    1. Efficient persistence of data
    2. Reliable retrieval operations
    3. Technology-specific optimizations
    4. Connection management
    
    They are NOT responsible for:
    1. Memory lifecycle management (consolidation, decay)
    2. Business logic around memory behaviors
    3. Cross-tier operations
    """

    @abc.abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the storage backend.
        
        Args:
            config: Configuration options for the backend
            
        Raises:
            StorageInitializationError: If initialization fails
        """
        pass
    
    @abc.abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the storage backend gracefully.
        
        This method should release all resources, close connections,
        and ensure any pending writes are completed.
        
        Raises:
            StorageOperationError: If shutdown operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Core CRUD Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def create(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Create a new item in storage.
        
        Args:
            item_id: Unique identifier for the item
            data: Data to store
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemExistsError: If an item with the same ID already exists
            StorageOperationError: If the create operation fails
        """
        pass
    
    @abc.abstractmethod
    async def read(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item data if found, None otherwise
            
        Raises:
            StorageOperationError: If the read operation fails
        """
        pass
    
    @abc.abstractmethod
    async def update(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing item.
        
        Args:
            item_id: The ID of the item to update
            data: New data for the item
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            ItemNotFoundError: If the item with the given ID does not exist
            StorageOperationError: If the update operation fails
        """
        pass
    
    @abc.abstractmethod
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item by its ID.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            StorageOperationError: If the delete operation fails
        """
        pass
    
    @abc.abstractmethod
    async def exists(self, item_id: str) -> bool:
        """
        Check if an item exists.
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            bool: True if the item exists, False otherwise
            
        Raises:
            StorageOperationError: If the exists operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Batch Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def batch_create(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Create multiple items in a batch operation.
        
        Args:
            items: Dictionary mapping item IDs to their data
            
        Returns:
            Dictionary mapping item IDs to success status
            
        Raises:
            StorageOperationError: If the batch create operation fails
        """
        pass
    
    @abc.abstractmethod
    async def batch_read(self, item_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve multiple items in a batch operation.
        
        Args:
            item_ids: List of item IDs to retrieve
            
        Returns:
            Dictionary mapping item IDs to their data (or None if not found)
            
        Raises:
            StorageOperationError: If the batch read operation fails
        """
        pass
    
    @abc.abstractmethod
    async def batch_update(self, items: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Update multiple items in a batch operation.
        
        Args:
            items: Dictionary mapping item IDs to their new data
            
        Returns:
            Dictionary mapping item IDs to success status
            
        Raises:
            StorageOperationError: If the batch update operation fails
        """
        pass
    
    @abc.abstractmethod
    async def batch_delete(self, item_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items in a batch operation.
        
        Args:
            item_ids: List of item IDs to delete
            
        Returns:
            Dictionary mapping item IDs to success status
            
        Raises:
            StorageOperationError: If the batch delete operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Query Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items based on filter criteria.
        
        Args:
            filters: Dict of field-value pairs to filter by
            sort_by: Field to sort results by
            ascending: Sort order (True for ascending, False for descending)
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of items matching the query criteria
            
        Raises:
            StorageOperationError: If the query operation fails
        """
        pass
    
    #-----------------------------------------------------------------------
    # Vector Operations (optional for vector-capable backends)
    #-----------------------------------------------------------------------
    
    async def vector_search(
        self,
        embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform a vector similarity search.
        
        This method is optional and should be implemented by vector-capable backends.
        By default, it raises NotImplementedError.
        
        Args:
            embedding: The query embedding vector
            filters: Optional metadata filters
            limit: Maximum number of results to return
            min_similarity: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of tuples (item, similarity_score)
            
        Raises:
            NotImplementedError: If the backend does not support vector search
            StorageOperationError: If the vector search operation fails
        """
        raise NotImplementedError("This backend does not support vector search")
    
    async def store_embedding(
        self,
        item_id: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store an embedding vector for an item.
        
        This method is optional and should be implemented by vector-capable backends.
        By default, it raises NotImplementedError.
        
        Args:
            item_id: The ID of the item
            embedding: The embedding vector
            metadata: Optional metadata to store with the embedding
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            NotImplementedError: If the backend does not support embeddings
            StorageOperationError: If the store embedding operation fails
        """
        raise NotImplementedError("This backend does not support embedding storage")
    
    #-----------------------------------------------------------------------
    # Time-based Operations (optional for time-aware backends)
    #-----------------------------------------------------------------------
    
    async def set_expiry(self, item_id: str, expire_at: datetime) -> bool:
        """
        Set an expiration time for an item.
        
        This method is optional and should be implemented by time-aware backends.
        By default, it raises NotImplementedError.
        
        Args:
            item_id: The ID of the item
            expire_at: When the item should expire
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            NotImplementedError: If the backend does not support expiry
            ItemNotFoundError: If the item does not exist
            StorageOperationError: If the set expiry operation fails
        """
        raise NotImplementedError("This backend does not support item expiry")
    
    async def get_expiry(self, item_id: str) -> Optional[datetime]:
        """
        Get the expiration time for an item.
        
        This method is optional and should be implemented by time-aware backends.
        By default, it raises NotImplementedError.
        
        Args:
            item_id: The ID of the item
            
        Returns:
            The expiration time if set, None otherwise
            
        Raises:
            NotImplementedError: If the backend does not support expiry
            ItemNotFoundError: If the item does not exist
            StorageOperationError: If the get expiry operation fails
        """
        raise NotImplementedError("This backend does not support item expiry")
    
    async def clear_expiry(self, item_id: str) -> bool:
        """
        Clear the expiration time for an item.
        
        This method is optional and should be implemented by time-aware backends.
        By default, it raises NotImplementedError.
        
        Args:
            item_id: The ID of the item
            
        Returns:
            bool: True if the operation was successful
            
        Raises:
            NotImplementedError: If the backend does not support expiry
            ItemNotFoundError: If the item does not exist
            StorageOperationError: If the clear expiry operation fails
        """
        raise NotImplementedError("This backend does not support item expiry")
    
    async def list_expired(self, before: datetime = datetime.now()) -> List[str]:
        """
        List IDs of items that have expired.
        
        This method is optional and should be implemented by time-aware backends.
        By default, it raises NotImplementedError.
        
        Args:
            before: Only include items expired before this time
            
        Returns:
            List of expired item IDs
            
        Raises:
            NotImplementedError: If the backend does not support expiry
            StorageOperationError: If the list expired operation fails
        """
        raise NotImplementedError("This backend does not support item expiry")
    
    #-----------------------------------------------------------------------
    # Maintenance Operations
    #-----------------------------------------------------------------------
    
    @abc.abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count items in storage, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        pass
    
    @abc.abstractmethod
    async def clear(self) -> bool:
        """
        Clear all items from storage.
        
        Returns:
            bool: True if the operation was successful
            
        Raises:
            StorageOperationError: If the clear operation fails
        """
        pass
    
    @abc.abstractmethod
    async def get_stats(self) -> Dict[str, Union[int, float, str, datetime]]:
        """
        Get statistics about the storage backend.
        
        Returns:
            Dictionary of statistics (implementation-specific)
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        pass
