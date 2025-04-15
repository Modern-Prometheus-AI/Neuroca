"""
SQLite Search Operations Component

This module provides a class for handling search operations on memory items
in the SQLite database, including filtering, sorting, and pagination.
"""

import json
import logging
import sqlite3
from typing import List, Optional, Tuple

from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.models.search import MemorySearchOptions as SearchFilter, MemorySearchResult as SearchResult, MemorySearchResults as SearchResults

logger = logging.getLogger(__name__)


class SQLiteSearch:
    """
    Handles search operations for memory items in SQLite database.
    
    This class provides methods for searching memory items in the SQLite database
    based on content, tags, metadata, and other criteria.
    """
    
    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize the search operations handler.
        
        Args:
            connection: SQLite database connection
        """
        self.conn = connection
    
    def search(
        self,
        query: str,
        filter: Optional[SearchFilter] = None,
        limit: int = 10,
        offset: int = 0
    ) -> SearchResults:
        """
        Search for memory items based on query and filter criteria.
        
        Args:
            query: Search query string
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            SearchResults: Search results containing memory items and metadata
        """
        # Build the query
        sql_query, params = self._build_search_query(query, filter, limit, offset)
        
        # Execute the query
        rows = self.conn.execute(sql_query, params).fetchall()
        
        # Count total results (without pagination)
        count_query, count_params = self._build_count_query(query, filter)
        total_count = self.conn.execute(count_query, count_params).fetchone()[0]
        
        # Convert rows to memory items
        results = self._convert_rows_to_results(rows)
        
        # Create search results
        search_results = SearchResults(
            query=query,
            results=results,
            total_results=total_count,
            page=offset // limit + 1 if limit > 0 else 1,
            page_size=limit,
            total_pages=(total_count + limit - 1) // limit if limit > 0 else 1
        )
        
        logger.debug(f"Search for '{query}' returned {len(results)} results")
        return search_results
    
    def count(self, filter: Optional[SearchFilter] = None) -> int:
        """
        Count memory items matching the given filter.
        
        Args:
            filter: Optional filter conditions
            
        Returns:
            int: Count of matching memory items
        """
        # Build the count query
        count_query, count_params = self._build_count_query("", filter)
        
        # Execute the query
        count = self.conn.execute(count_query, count_params).fetchone()[0]
        
        logger.debug(f"Count returned {count} memories")
        return count
    
    def _build_search_query(
        self,
        query: str,
        filter: Optional[SearchFilter],
        limit: int,
        offset: int
    ) -> Tuple[str, List]:
        """
        Build SQL query for searching memory items.
        
        Args:
            query: Search query string
            filter: Optional filter conditions
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            Tuple[str, List]: SQL query string and parameters
        """
        # Base query
        sql_query = """
            SELECT DISTINCT m.id, m.content, m.summary, m.created_at,
                   m.last_accessed, m.last_modified, mm.metadata_json
            FROM memory_items m
            LEFT JOIN memory_metadata mm ON m.id = mm.memory_id
            LEFT JOIN memory_tags mt ON m.id = mt.memory_id
        """
        
        # Add WHERE clause if needed
        where_clauses = []
        params = []
        
        # Add search query if provided
        if query:
            where_clauses.append("""
                (m.content LIKE ? OR m.summary LIKE ? OR mt.tag LIKE ?)
            """)
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term])
        
        # Add filters if provided
        if filter:
            self._add_filter_clauses(filter, where_clauses, params)
        
        # Add WHERE clause if any conditions are present
        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)
        
        # Add order by
        sql_query += " ORDER BY m.created_at DESC"
        
        # Add pagination
        sql_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return sql_query, params
    
    def _build_count_query(
        self,
        query: str,
        filter: Optional[SearchFilter]
    ) -> Tuple[str, List]:
        """
        Build SQL query for counting memory items.
        
        Args:
            query: Search query string
            filter: Optional filter conditions
            
        Returns:
            Tuple[str, List]: SQL query string and parameters
        """
        # Base query
        count_query = """
            SELECT COUNT(DISTINCT m.id)
            FROM memory_items m
            LEFT JOIN memory_metadata mm ON m.id = mm.memory_id
            LEFT JOIN memory_tags mt ON m.id = mt.memory_id
        """
        
        # Add WHERE clause if needed
        where_clauses = []
        params = []
        
        # Add search query if provided
        if query:
            where_clauses.append("""
                (m.content LIKE ? OR m.summary LIKE ? OR mt.tag LIKE ?)
            """)
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term])
        
        # Add filters if provided
        if filter:
            self._add_filter_clauses(filter, where_clauses, params)
        
        # Add WHERE clause if any conditions are present
        if where_clauses:
            count_query += " WHERE " + " AND ".join(where_clauses)
        
        return count_query, params
    
    def _add_filter_clauses(
        self,
        filter: SearchFilter,
        where_clauses: List[str],
        params: List
    ) -> None:
        """
        Add filter clauses to the WHERE clause.
        
        Args:
            filter: Filter conditions
            where_clauses: List of WHERE clause conditions
            params: List of query parameters
        """
        if filter.min_importance is not None:
            where_clauses.append("""
                (json_extract(mm.metadata_json, '$.importance') >= ?)
            """)
            params.append(filter.min_importance)
        
        if filter.max_importance is not None:
            where_clauses.append("""
                (json_extract(mm.metadata_json, '$.importance') <= ?)
            """)
            params.append(filter.max_importance)
        
        if filter.status:
            where_clauses.append("""
                (json_extract(mm.metadata_json, '$.status') = ?)
            """)
            params.append(filter.status)
        
        if filter.tags:
            placeholders = ", ".join(["?"] * len(filter.tags))
            where_clauses.append(f"""
                m.id IN (
                    SELECT memory_id FROM memory_tags
                    WHERE tag IN ({placeholders})
                    GROUP BY memory_id
                    HAVING COUNT(DISTINCT tag) = ?
                )
            """)
            params.extend(filter.tags)
            params.append(len(filter.tags))
        
        if filter.created_after:
            where_clauses.append("m.created_at >= ?")
            params.append(filter.created_after)
        
        if filter.created_before:
            where_clauses.append("m.created_at <= ?")
            params.append(filter.created_before)
        
        if filter.accessed_after:
            where_clauses.append("m.last_accessed >= ?")
            params.append(filter.accessed_after)
        
        if filter.accessed_before:
            where_clauses.append("m.last_accessed <= ?")
            params.append(filter.accessed_before)
    
    def _convert_rows_to_results(self, rows: List[sqlite3.Row]) -> List[SearchResult]:
        """
        Convert SQL rows to search results.
        
        Args:
            rows: SQL result rows
            
        Returns:
            List[SearchResult]: List of search results
        """
        results = []
        
        for row in rows:
            metadata = {}
            if row[6]:  # metadata_json
                metadata = json.loads(row[6])
            
            memory_item = MemoryItem(
                id=row[0],
                content=row[1],
                summary=row[2],
                metadata=metadata
            )
            
            # For simplicity, use a constant score
            # In a real implementation, you might want to calculate relevance scores
            score = 1.0
            
            results.append(SearchResult(memory=memory_item, score=score))
        
        return results
