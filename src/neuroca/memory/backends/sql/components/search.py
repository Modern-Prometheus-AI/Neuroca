"""
SQL Search Component

This module provides the SQLSearch class for searching memory items in SQL database.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from neuroca.memory.backends.sql.components.connection import SQLConnection
from neuroca.memory.backends.sql.components.crud import SQLCRUD
from neuroca.memory.backends.sql.components.schema import SQLSchema
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import MemorySearchOptions, MemorySearchResults

logger = logging.getLogger(__name__)


class SQLSearch:
    """
    Handles search operations for memory items in SQL database.
    
    This class provides methods for searching and filtering memory items
    based on various criteria such as content text, tags, and status.
    """
    
    def __init__(
        self,
        connection: SQLConnection,
        schema: SQLSchema,
        crud: SQLCRUD,
    ):
        """
        Initialize the SQL search component.
        
        Args:
            connection: SQL connection component
            schema: SQL schema component
            crud: SQL CRUD component for row conversion
        """
        self.connection = connection
        self.schema = schema
        self.crud = crud
    
    async def search(
        self, 
        query: str, 
        filter: Optional[MemorySearchOptions] = None,
        limit: int = 10,
        offset: int = 0
    ) -> MemorySearchResults:
        """
        Search for memory items in the database.
        
        Args:
            query: The search query
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            MemorySearchResults: Search results containing memory items and metadata
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        try:
            # Get search results
            memory_items, total_count = await self._search_and_filter(
                query=query,
                filter=filter,
                limit=limit,
                offset=offset
            )
            
            # Calculate pagination info
            page = offset // limit + 1 if limit > 0 else 1
            total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
            
            # Create search results
            # Pass the original filter options back in the results object
            search_options = filter if filter else MemorySearchOptions(query=query, limit=limit, offset=offset)
            results = MemorySearchResults(
                query=query,
                results=memory_items, 
                total_count=total_count,
                options=search_options 
            )
            
            logger.debug(f"Search for '{query}' returned {len(memory_items)} results out of {total_count} total")
            return results
                
        except Exception as e:
            error_msg = f"Failed to search memories in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def count(self, filter: Optional[MemorySearchOptions] = None) -> int:
        """
        Count memory items in the database matching the filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
            
        Raises:
            StorageOperationError: If the count operation fails
        """
        try:
            count_query, params = self._build_count_query(filter)
            result = await self.connection.execute_query(count_query, params)
            return result[0]["count"] if result else 0
                
        except Exception as e:
            error_msg = f"Failed to count memories in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _search_and_filter(
        self,
        query: str,
        filter: Optional[MemorySearchOptions] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[MemoryItem], int]:
        """
        Search and filter memory items.
        
        Args:
            query: The search query
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            Tuple containing list of memory items and total count
            
        Raises:
            StorageOperationError: If the search operation fails
        """
        # Build the search query
        search_query, count_query, params = self._build_search_query(
            query=query,
            filter=filter,
            limit=limit,
            offset=offset
        )
        
        # Execute search query
        rows = await self.connection.execute_query(search_query, params)
        
        # Execute count query
        count_result = await self.connection.execute_query(count_query, params[:-2])  # exclude limit and offset
        total_count = count_result[0]["count"] if count_result else 0
        
        # Convert rows to memory items
        memory_items = [self.crud._row_to_memory_item(row) for row in rows]
        
        return memory_items, total_count
    
    def _build_search_query(
        self,
        query: str,
        filter: Optional[MemorySearchOptions] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[str, str, List[Any]]:
        """
        Build SQL search query with filters.
        
        Args:
            query: The search query
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            Tuple containing search query, count query, and parameters
        """
        # Prepare base query
        select_clause = f"""
            SELECT *,
                metadata->>'status' as status
            FROM {self.schema.qualified_table_name}
        """
        
        # Build where clauses and params
        where_clauses = []
        params = []
        param_idx = 1
        
        # Add text search if query is provided
        if query and query.strip():
            where_clauses.append(f"(to_tsvector('english', summary) @@ plainto_tsquery('english', ${param_idx}) OR content::text ILIKE ${param_idx+1})")
            params.append(query)
            params.append(f"%{query}%")
            param_idx += 2
        
        # Add filters if provided
        if filter:
            # Filter by status
            if filter.status:
                where_clauses.append(f"metadata->>'status' = ${param_idx}")
                params.append(filter.status.value if hasattr(filter.status, 'value') else filter.status)
                param_idx += 1
            
            # Filter by importance
            if filter.min_importance is not None:
                where_clauses.append(f"(metadata->>'importance')::float >= ${param_idx}")
                params.append(float(filter.min_importance))
                param_idx += 1
                
            if filter.max_importance is not None:
                where_clauses.append(f"(metadata->>'importance')::float <= ${param_idx}")
                params.append(float(filter.max_importance))
                param_idx += 1
            
            # Filter by tags
            if filter.tags:
                # Check if any of the provided tags exist in the metadata tags array
                tag_clauses = []
                for tag in filter.tags:
                    tag_clauses.append(f"metadata->'tags' ? ${param_idx}")
                    params.append(tag)
                    param_idx += 1
                if tag_clauses:
                    where_clauses.append(f"({' AND '.join(tag_clauses)})")
            
            # Filter by created_after
            if filter.created_after:
                where_clauses.append(f"created_at >= ${param_idx}")
                params.append(filter.created_after)
                param_idx += 1
            
            # Filter by created_before
            if filter.created_before:
                where_clauses.append(f"created_at <= ${param_idx}")
                params.append(filter.created_before)
                param_idx += 1
        
        # Build the where clause
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Add order by, limit, and offset
        search_query = f"""
            {select_clause}
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx+1}
        """
        
        # Add limit and offset params
        params.extend([limit, offset])
        
        # Build count query (same as search query but with COUNT(*) and no LIMIT/OFFSET)
        count_query = f"""
            SELECT COUNT(*) as count
            FROM {self.schema.qualified_table_name}
            {where_clause}
        """
        
        return search_query, count_query, params
    
    def _build_count_query(self, filter: Optional[MemorySearchOptions] = None) -> Tuple[str, List[Any]]:
        """
        Build SQL count query with filters.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            Tuple containing count query and parameters
        """
        # Prepare base query
        select_clause = f"""
            SELECT COUNT(*) as count
            FROM {self.schema.qualified_table_name}
        """
        
        # Build where clauses and params
        where_clauses = []
        params = []
        param_idx = 1
        
        # Add filters if provided
        if filter:
            # Filter by status
            if filter.status:
                where_clauses.append(f"metadata->>'status' = ${param_idx}")
                params.append(filter.status.value if hasattr(filter.status, 'value') else filter.status)
                param_idx += 1
            
            # Filter by importance
            if filter.min_importance is not None:
                where_clauses.append(f"(metadata->>'importance')::float >= ${param_idx}")
                params.append(float(filter.min_importance))
                param_idx += 1
                
            if filter.max_importance is not None:
                where_clauses.append(f"(metadata->>'importance')::float <= ${param_idx}")
                params.append(float(filter.max_importance))
                param_idx += 1
            
            # Filter by tags
            if filter.tags:
                # Check if any of the provided tags exist in the metadata tags array
                tag_clauses = []
                for tag in filter.tags:
                    tag_clauses.append(f"metadata->'tags' ? ${param_idx}")
                    params.append(tag)
                    param_idx += 1
                if tag_clauses:
                    where_clauses.append(f"({' AND '.join(tag_clauses)})")
            
            # Filter by created_after
            if filter.created_after:
                where_clauses.append(f"created_at >= ${param_idx}")
                params.append(filter.created_after)
                param_idx += 1
            
            # Filter by created_before
            if filter.created_before:
                where_clauses.append(f"created_at <= ${param_idx}")
                params.append(filter.created_before)
                param_idx += 1
        
        # Build the where clause
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Complete query
        count_query = f"{select_clause}{where_clause}"
        
        return count_query, params
