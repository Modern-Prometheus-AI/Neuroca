"""
SQL Stats Component

This module provides the SQLStats class for collecting statistics about SQL storage.
"""

import logging
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.sql.components.connection import SQLConnection
from neuroca.memory.backends.sql.components.schema import SQLSchema
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.interfaces import StorageStats

logger = logging.getLogger(__name__)


class SQLStats:
    """
    Collects and reports statistics about SQL storage.
    
    This class provides methods for retrieving various metrics about the
    SQL storage, such as item count, storage size, and status distributions.
    """
    
    def __init__(
        self,
        connection: SQLConnection,
        schema: SQLSchema,
    ):
        """
        Initialize the SQL stats component.
        
        Args:
            connection: SQL connection component
            schema: SQL schema component
        """
        self.connection = connection
        self.schema = schema
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the SQL storage.
        
        Returns:
            StorageStats: Statistics about the storage
            
        Raises:
            StorageOperationError: If the get stats operation fails
        """
        try:
            # Get basic counts
            total_memories, active_memories, archived_memories = await self._get_counts()
            
            # Get storage size estimate
            total_size_bytes = await self._estimate_storage_size()
            
            # Get metadata size estimate
            metadata_size_bytes = await self._estimate_metadata_size()
            
            # Get age statistics
            avg_age_seconds, oldest_age_seconds, newest_age_seconds = await self._get_age_stats()
            
            # Get database information
            db_info = await self._get_db_info()
            
            # Create additional info
            additional_info = {
                "pg_database": db_info.get("current_database"),
                "pg_version": db_info.get("server_version"),
                "schema_name": self.schema.schema,
                "table_name": self.schema.table_name,
                "has_indexes": await self._has_indexes(),
            }
            
            # Create StorageStats object
            stats = StorageStats(
                backend_type="SQLBackend",
                item_count=total_memories,
                storage_size_bytes=total_size_bytes,
                metadata_size_bytes=metadata_size_bytes,
                average_item_age_seconds=avg_age_seconds,
                oldest_item_age_seconds=oldest_age_seconds,
                newest_item_age_seconds=newest_age_seconds,
                max_capacity=-1,  # SQL has no fixed capacity
                capacity_used_percent=0.0,
                additional_info=additional_info
            )
            
            logger.debug(f"Retrieved storage stats: {total_memories} memories")
            return stats
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def _get_counts(self) -> tuple[int, int, int]:
        """
        Get memory counts by status.
        
        Returns:
            Tuple of (total_count, active_count, archived_count)
        """
        query = f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE metadata->>'status' = 'active') as active_count,
                COUNT(*) FILTER (WHERE metadata->>'status' = 'archived') as archived_count
            FROM {self.schema.qualified_table_name}
        """
        
        result = await self.connection.execute_query(query)
        
        if not result:
            return 0, 0, 0
            
        row = result[0]
        return row["total"], row["active_count"], row["archived_count"]
    
    async def _estimate_storage_size(self) -> int:
        """
        Estimate the storage size of the memory table.
        
        Returns:
            int: Estimated size in bytes
        """
        query = f"""
            SELECT
                pg_total_relation_size('{self.schema.qualified_table_name}'::regclass) as total_size
        """
        
        result = await self.connection.execute_query(query)
        
        if not result:
            return 0
            
        return result[0]["total_size"]
    
    async def _estimate_metadata_size(self) -> int:
        """
        Estimate the size of metadata stored in the memory table.
        
        Returns:
            int: Estimated size in bytes
        """
        query = f"""
            SELECT
                SUM(pg_column_size(metadata)) as metadata_size
            FROM {self.schema.qualified_table_name}
        """
        
        result = await self.connection.execute_query(query)
        
        if not result or result[0]["metadata_size"] is None:
            return 0
            
        return result[0]["metadata_size"]
    
    async def _get_age_stats(self) -> tuple[float, float, float]:
        """
        Get age statistics for memory items.
        
        Returns:
            Tuple of (average_age_seconds, oldest_age_seconds, newest_age_seconds)
        """
        query = f"""
            SELECT
                EXTRACT(EPOCH FROM (NOW() - AVG(created_at))) as avg_age_seconds,
                EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) as oldest_age_seconds,
                EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) as newest_age_seconds
            FROM {self.schema.qualified_table_name}
        """
        
        result = await self.connection.execute_query(query)
        
        if not result or result[0]["avg_age_seconds"] is None:
            return 0.0, 0.0, 0.0
            
        row = result[0]
        return row["avg_age_seconds"], row["oldest_age_seconds"], row["newest_age_seconds"]
    
    async def _get_db_info(self) -> Dict[str, Any]:
        """
        Get database system information.
        
        Returns:
            Dict: Database information
        """
        queries = [
            "SELECT current_database() AS current_database",
            "SHOW server_version",
        ]
        
        info = {}
        
        for query in queries:
            result = await self.connection.execute_query(query)
            if result:
                for key, value in result[0].items():
                    info[key] = value
        
        return info
    
    async def _has_indexes(self) -> bool:
        """
        Check if the memory table has indexes.
        
        Returns:
            bool: True if indexes exist, False otherwise
        """
        query = f"""
            SELECT COUNT(*) as index_count
            FROM pg_indexes
            WHERE schemaname = '{self.schema.schema}'
            AND tablename = '{self.schema.table_name}'
        """
        
        result = await self.connection.execute_query(query)
        
        if not result:
            return False
            
        return result[0]["index_count"] > 0
    
    async def get_status_distribution(self) -> Dict[str, int]:
        """
        Get distribution of memories by status.
        
        Returns:
            Dict[str, int]: Dictionary mapping status values to counts
        """
        query = f"""
            SELECT
                metadata->>'status' as status,
                COUNT(*) as count
            FROM {self.schema.qualified_table_name}
            GROUP BY metadata->>'status'
        """
        
        result = await self.connection.execute_query(query)
        
        if not result:
            return {}
            
        return {row["status"]: row["count"] for row in result if row["status"]}
    
    async def get_tag_distribution(self) -> Dict[str, int]:
        """
        Get distribution of memories by tags.
        
        Returns:
            Dict[str, int]: Dictionary mapping tag values to counts
        """
        query = f"""
            SELECT
                jsonb_array_elements_text(metadata->'tags') as tag,
                COUNT(*) as count
            FROM {self.schema.qualified_table_name}
            WHERE jsonb_typeof(metadata->'tags') = 'array'
            GROUP BY tag
        """
        
        result = await self.connection.execute_query(query)
        
        if not result:
            return {}
            
        return {row["tag"]: row["count"] for row in result}
    
    async def get_access_stats(self) -> Dict[str, Any]:
        """
        Get access statistics for memory items.
        
        Returns:
            Dict: Access statistics
        """
        query = f"""
            SELECT
                AVG(access_count) as avg_access_count,
                MAX(access_count) as max_access_count,
                MIN(access_count) as min_access_count,
                EXTRACT(EPOCH FROM (NOW() - MAX(last_accessed))) as seconds_since_last_access
            FROM {self.schema.qualified_table_name}
        """
        
        result = await self.connection.execute_query(query)
        
        if not result or result[0]["avg_access_count"] is None:
            return {
                "avg_access_count": 0,
                "max_access_count": 0, 
                "min_access_count": 0,
                "seconds_since_last_access": None
            }
            
        return result[0]
