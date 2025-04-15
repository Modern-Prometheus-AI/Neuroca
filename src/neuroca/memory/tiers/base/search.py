"""
Memory Tier Search Functionality

This module provides classes for handling search-related operations
in memory tiers.
"""

from typing import Any, Dict, List, Optional

from neuroca.memory.models.memory_item import MemoryItem


class TierSearcher:
    """
    Handles search operations for memory tiers.
    
    This class provides methods for applying tier-specific filters,
    converting queries, and processing search results.
    """
    
    @staticmethod
    async def apply_tier_filters(
        tier_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply tier-specific filters to search criteria.
        
        Args:
            tier_name: The name of the tier
            filters: Optional filters provided by the client
            
        Returns:
            Combined filters with tier-specific constraints
        """
        combined_filters = {}
        
        # Add tier-specific filters
        tier_filter = {"metadata.tier": tier_name}
        
        # Only include active memories by default
        status_filter = {"metadata.status": "active"}
        
        # Combine with provided filters
        if filters:
            combined_filters.update(filters)
        
        combined_filters.update(tier_filter)
        combined_filters.update(status_filter)
        
        return combined_filters
    
    @staticmethod
    async def convert_query(
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Convert a text query and/or embedding to a backend query format.
        
        Args:
            query: Optional text query
            embedding: Optional vector embedding
            
        Returns:
            Backend query specification
        """
        backend_query = {}
        
        if query:
            # Simple text search by default
            backend_query["text"] = query
        
        if embedding:
            # Vector similarity search
            backend_query["embedding"] = embedding
            
        return backend_query
    
    @staticmethod
    async def perform_search(
        backend,
        backend_query: Dict[str, Any],
        combined_filters: Dict[str, Any],
        limit: int,
        offset: int,
    ) -> List[Dict[str, Any]]:
        """
        Perform the actual search operation using the backend.
        
        Args:
            backend: The storage backend
            backend_query: Query specification
            combined_filters: Combined filters
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            Search results
        """
        # Check if a vector search is requested
        if "embedding" in backend_query and hasattr(backend, "similarity_search"):
            # Use vector search if available
            embedding = backend_query["embedding"]
            return await backend.similarity_search(
                embedding=embedding,
                filters=combined_filters,
                limit=limit,
                offset=offset,
            )
        elif "text" in backend_query and hasattr(backend, "text_search"):
            # Use text search if available
            text = backend_query["text"]
            return await backend.text_search(
                text=text,
                filters=combined_filters,
                limit=limit,
                offset=offset,
            )
        else:
            # Fall back to regular query
            return await backend.query(
                filters=combined_filters,
                limit=limit,
                offset=offset,
            )
    
    @staticmethod
    async def post_search(
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process search results before returning them.
        
        Args:
            results: Raw search results
            
        Returns:
            Processed search results
        """
        # Default implementation just returns the results
        # Subclasses can override to add tier-specific post-processing
        return results
