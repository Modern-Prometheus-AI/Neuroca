"""
Vector Search Component

This module provides the VectorSearch class for implementing semantic search
functionality over vector embeddings, including filtering and similarity-based retrieval.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from neuroca.memory.backends.vector.components.crud import VectorCRUD
from neuroca.memory.backends.vector.components.index import VectorIndex
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import MemorySearchOptions, MemorySearchResults

logger = logging.getLogger(__name__)


class VectorSearch:
    """
    Implements semantic search functionality for the vector database.
    
    This class provides methods for searching memory items in the vector database
    based on semantic similarity of vector embeddings, with support for filtering
    by metadata such as tags, status, importance, and creation time.
    """
    
    def __init__(
        self,
        index: VectorIndex,
        crud: VectorCRUD,
        similarity_threshold: float = 0.0,
    ):
        """
        Initialize the vector search component.
        
        Args:
            index: Vector index component
            crud: Vector CRUD component
            similarity_threshold: Minimum similarity score for search results
        """
        self.index = index
        self.crud = crud
        self.similarity_threshold = similarity_threshold
    
    async def search(
        self,
        query: str,
        query_embedding: List[float],
        filter: Optional[MemorySearchOptions] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> MemorySearchResults:
        """
        Search for memory items in the vector database.
        
        Args:
            query: The search query (used for logging and result info)
            query_embedding: The embedding vector to search for
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            SearchResults: Search results with memory items and metadata
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            # Create filter function for the vector index
            filter_fn = self._create_filter_function(filter)
            
            # Search for similar vectors
            fetch_limit = limit + offset + 20  # Fetch extra for filtering
            search_results = self.index.search(
                query_vector=query_embedding,
                k=fetch_limit,
                filter_fn=filter_fn,
                similarity_threshold=self.similarity_threshold,
            )
            
            # No results case
            if not search_results:
                # Use MemorySearchResults and pass options
                search_options = filter if filter else MemorySearchOptions(query=query, limit=limit, offset=offset)
                return MemorySearchResults(
                    query=query,
                    results=[],
                    total_results=0,
                    page=1,
                    page_size=limit,
                    total_pages=0
                )
            
            # Apply offset
            search_results = search_results[offset:offset + limit]
            
            # Get memory items for results
            memory_ids = [memory_id for memory_id, _ in search_results]
            memory_items_dict = await self.crud.batch_read(memory_ids)
            
            # Filter out None values and preserve order
            memory_items = []
            scores = {}
            
            for memory_id, similarity in search_results:
                memory_item = memory_items_dict.get(memory_id)
                if memory_item:
                    memory_items.append(memory_item)
                    scores[memory_id] = similarity
            
            # Calculate pagination info
            total_count = await self.count(filter)
            page = offset // limit + 1 if limit > 0 else 1
            total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
            
            # Create search results
            # Use MemorySearchResults and pass options
            search_options = filter if filter else MemorySearchOptions(query=query, limit=limit, offset=offset)
            results = MemorySearchResults(
                query=query,
                results=memory_items,
                total_results=total_count,
                page=page,
                page_size=limit,
                total_pages=total_pages,
                scores=scores
            )
            
            logger.debug(f"Search for '{query}' returned {len(memory_items)} results")
            return results
                
        except Exception as e:
            error_msg = f"Failed to search memories in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count(self, filter: Optional[MemorySearchOptions] = None) -> int:
        """
        Count memory items in the vector database matching the filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        try:
            # Create filter function
            filter_fn = self._create_filter_function(filter)
            
            # Count entries that match the filter
            if filter_fn is None:
                # If no filter, just return total count
                count = self.index.count()
            else:
                # Apply filter to each entry
                count = 0
                for entry in self.index.get_entries():
                    if filter_fn(entry.metadata):
                        count += 1
            
            return count
                
        except Exception as e:
            error_msg = f"Failed to count memories in vector database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    def _create_filter_function(
        self, 
        filter: Optional[MemorySearchOptions]
    ) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """
        Create a filter function based on provided filters.
        
        Args:
            filter: Filter conditions
            
        Returns:
            Optional[Callable]: Filter function or None if no filter
        """
        if not filter:
            return None
            
        def filter_fn(metadata: Dict[str, Any]) -> bool:
            # Filter by status
            if filter.status:
                status_val = filter.status.value if hasattr(filter.status, 'value') else filter.status
                if metadata.get("status") != status_val:
                    return False
            
            # Filter by importance
            if filter.min_importance is not None:
                if metadata.get("importance", 0) < float(filter.min_importance):
                    return False
                    
            if filter.max_importance is not None:
                if metadata.get("importance", 0) > float(filter.max_importance):
                    return False
            
            # Filter by tags
            if filter.tags:
                metadata_tags = metadata.get("tags", [])
                if not any(tag in metadata_tags for tag in filter.tags):
                    return False
            
            # Filter by created_after
            if filter.created_after:
                created_at = metadata.get("created_at")
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at)
                        if created_dt < filter.created_after:
                            return False
                    except (ValueError, TypeError):
                        return False
            
            # Filter by created_before
            if filter.created_before:
                created_at = metadata.get("created_at")
                if created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at)
                        if created_dt > filter.created_before:
                            return False
                    except (ValueError, TypeError):
                        return False
            
            return True
            
        return filter_fn
