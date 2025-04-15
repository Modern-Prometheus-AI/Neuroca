"""
Redis Search Component

This module provides the RedisSearch class for searching memory items in Redis.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from neuroca.memory.backends.redis.components.connection import RedisConnection
from neuroca.memory.backends.redis.components.utils import RedisUtils
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.models.search import SearchFilter, SearchResult, SearchResults

logger = logging.getLogger(__name__)


class RedisSearch:
    """
    Handles search operations for memory items in Redis.
    
    This class provides methods for searching and filtering memory items
    based on various criteria such as content text, tags, and status.
    """
    
    def __init__(self, connection: RedisConnection, utils: RedisUtils):
        """
        Initialize the Redis search component.
        
        Args:
            connection: Redis connection component
            utils: Redis utilities
        """
        self.connection = connection
        self.utils = utils
    
    async def search_by_text(
        self, 
        query: str, 
        fields: List[str] = None,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Search for memory items by text content.
        
        Args:
            query: Search query string
            fields: Fields to search in (ignored for this implementation)
            limit: Maximum number of results to return
            
        Returns:
            List[str]: List of memory IDs matching the query
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            if not query:
                # If no query is provided, return all memory IDs
                # This could be optimized for large datasets
                return await self._get_all_memory_ids()
            
            # Tokenize query
            query_words = self.utils.tokenize_content(query)
            
            # Find content matches
            matching_ids: Optional[Set[str]] = None
            
            for word in query_words:
                word_key = self.utils.create_content_index_key(word)
                word_matches = await self.connection.execute("smembers", word_key)
                
                if matching_ids is None:
                    matching_ids = set(word_matches)
                else:
                    # Union results - any word matches
                    matching_ids = matching_ids.union(word_matches)
            
            # If no matches were found, return empty list
            if not matching_ids or len(matching_ids) == 0:
                return []
            
            result_ids = list(matching_ids)
            
            # Apply limit if provided
            if limit is not None and len(result_ids) > limit:
                result_ids = result_ids[:limit]
                
            return result_ids
        except Exception as e:
            error_msg = f"Failed to search by text: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def filter_by_tags(self, memory_ids: List[str], tags: List[str]) -> List[str]:
        """
        Filter memory items by tags.
        
        Args:
            memory_ids: List of memory IDs to filter
            tags: List of tags to filter by
            
        Returns:
            List[str]: Filtered list of memory IDs
            
        Raises:
            StorageOperationError: If the filter operation fails
        """
        try:
            if not tags or not memory_ids:
                return memory_ids
            
            # Get memory IDs for each tag
            filtered_ids = set(memory_ids)
            
            for tag in tags:
                tag_key = self.utils.create_tag_key(tag)
                tag_matches = await self.connection.execute("smembers", tag_key)
                
                # Intersection - must match all tags
                filtered_ids = filtered_ids.intersection(tag_matches)
                
                # If no matches remain, return empty list early
                if not filtered_ids:
                    return []
            
            return list(filtered_ids)
        except Exception as e:
            error_msg = f"Failed to filter by tags: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def filter_by_status(self, memory_ids: List[str], status: str) -> List[str]:
        """
        Filter memory items by status.
        
        Args:
            memory_ids: List of memory IDs to filter
            status: Status to filter by
            
        Returns:
            List[str]: Filtered list of memory IDs
            
        Raises:
            StorageOperationError: If the filter operation fails
        """
        try:
            if not status or not memory_ids:
                return memory_ids
            
            # Get memory IDs with this status
            status_key = self.utils.create_status_key(status)
            status_matches = await self.connection.execute("smembers", status_key)
            
            # Intersection with provided IDs
            filtered_ids = set(memory_ids).intersection(status_matches)
            
            return list(filtered_ids)
        except Exception as e:
            error_msg = f"Failed to filter by status: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def filter_by_importance(
        self, 
        memory_ids: List[str], 
        min_importance: Optional[float] = None,
        max_importance: Optional[float] = None
    ) -> List[str]:
        """
        Filter memory items by importance.
        
        Args:
            memory_ids: List of memory IDs to filter
            min_importance: Minimum importance value (inclusive)
            max_importance: Maximum importance value (inclusive)
            
        Returns:
            List[str]: Filtered list of memory IDs
            
        Raises:
            StorageOperationError: If the filter operation fails
        """
        try:
            if (min_importance is None and max_importance is None) or not memory_ids:
                return memory_ids
            
            # This requires retrieving metadata for each memory
            filtered_ids = []
            
            for memory_id in memory_ids:
                metadata_key = self.utils.create_metadata_key(memory_id)
                metadata_json = await self.connection.execute("get", metadata_key)
                metadata = self.utils.deserialize_metadata(metadata_json)
                
                importance = metadata.get("importance", 0.0)
                
                # Check min importance
                if min_importance is not None and importance < min_importance:
                    continue
                
                # Check max importance
                if max_importance is not None and importance > max_importance:
                    continue
                
                filtered_ids.append(memory_id)
            
            return filtered_ids
        except Exception as e:
            error_msg = f"Failed to filter by importance: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def search_and_filter(
        self,
        query: str,
        filter: Optional[SearchFilter] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[str]:
        """
        Search and filter memory items.
        
        Args:
            query: Search query string
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List[str]: List of filtered memory IDs
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            # First, search by text
            memory_ids = await self.search_by_text(query)
            
            # Apply filters if provided
            if filter:
                # Filter by status
                if filter.status:
                    memory_ids = await self.filter_by_status(memory_ids, filter.status)
                
                # Filter by tags
                if filter.tags:
                    memory_ids = await self.filter_by_tags(memory_ids, filter.tags)
                
                # Filter by importance
                if filter.min_importance is not None or filter.max_importance is not None:
                    memory_ids = await self.filter_by_importance(
                        memory_ids, 
                        filter.min_importance, 
                        filter.max_importance
                    )
            
            # Apply pagination
            total_count = len(memory_ids)
            paginated_ids = memory_ids[offset:offset + limit] if memory_ids else []
            
            return {
                "ids": paginated_ids,
                "total_count": total_count
            }
        except Exception as e:
            error_msg = f"Failed to search and filter: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count_items(self, filter: Optional[SearchFilter] = None) -> int:
        """
        Count memory items matching the filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        try:
            # If no filter, use stats
            if not filter:
                stats_key = self.utils.create_stats_key()
                total = await self.connection.execute("hget", stats_key, "total_memories")
                return int(total) if total else 0
            
            # Search with filters but don't retrieve memory data
            result = await self.search_and_filter("", filter, limit=0)
            return result["total_count"]
        except Exception as e:
            error_msg = f"Failed to count memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _get_all_memory_ids(self) -> List[str]:
        """
        Get all memory IDs.
        
        Returns:
            List[str]: List of all memory IDs
            
        Raises:
            StorageOperationError: If the operation fails
        """
        try:
            # Use pattern matching to find all memory keys
            prefix_pattern = f"{self.utils.prefix}:*"
            memory_pattern = f"{self.utils.prefix}:"
            
            # Use scan to efficiently iterate through keys
            all_memory_ids = []
            cursor = "0"
            
            while True:
                cursor, keys = await self.connection.execute(
                    "scan", 
                    cursor, 
                    match=prefix_pattern, 
                    count=100
                )
                
                # Filter keys to only include memory items
                for key in keys:
                    if ":" not in key[len(memory_pattern):] and key.startswith(memory_pattern):
                        memory_id = key[len(memory_pattern):]
                        all_memory_ids.append(memory_id)
                
                # Stop when scan is complete
                if cursor == "0":
                    break
            
            return all_memory_ids
        except Exception as e:
            error_msg = f"Failed to get all memory IDs: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
