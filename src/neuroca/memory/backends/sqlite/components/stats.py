"""
SQLite Statistics Component

This module provides a class for gathering statistics about the SQLite database,
such as memory counts, database size, and access/modification times.
"""

import logging
import os
import sqlite3
from typing import Optional

from neuroca.memory.interfaces import StorageStats

logger = logging.getLogger(__name__)


class SQLiteStats:
    """
    Handles statistics gathering for the SQLite database.
    
    This class provides methods for collecting statistics about memory items
    in the SQLite database, such as counts, sizes, and timestamps.
    """
    
    def __init__(self, connection: sqlite3.Connection, db_path: str):
        """
        Initialize the statistics handler.
        
        Args:
            connection: SQLite database connection
            db_path: Path to the SQLite database file
        """
        self.conn = connection
        self.db_path = db_path
    
    def get_stats(self) -> StorageStats:
        """
        Get statistics about the SQLite storage.
        
        Returns:
            StorageStats: Storage statistics including counts, size, and timestamps
        """
        # Get total memory count
        total_memories = self._get_total_count()
        
        # Get counts by status
        active_memories = self._get_active_count()
        archived_memories = self._get_archived_count()
        
        # Get database size
        db_size = self._get_database_size()
        
        # Get last access and write times
        last_access_time = self._get_last_access_time()
        last_write_time = self._get_last_write_time()
        
        # Create stats object
        stats = StorageStats(
            total_memories=total_memories,
            active_memories=active_memories,
            archived_memories=archived_memories,
            total_size_bytes=db_size,
            last_access_time=last_access_time,
            last_write_time=last_write_time
        )
        
        logger.debug(f"Retrieved storage stats: {stats.total_memories} memories")
        return stats
    
    def _get_total_count(self) -> int:
        """
        Get the total count of memory items.
        
        Returns:
            int: Total count of memory items
        """
        result = self.conn.execute(
            "SELECT COUNT(*) FROM memory_items"
        ).fetchone()
        
        return result[0] if result else 0
    
    def _get_active_count(self) -> int:
        """
        Get the count of active memory items.
        
        Returns:
            int: Count of active memory items
        """
        result = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM memory_items m
            JOIN memory_metadata mm ON m.id = mm.memory_id
            WHERE json_extract(mm.metadata_json, '$.status') = 'active'
            """
        ).fetchone()
        
        return result[0] if result else 0
    
    def _get_archived_count(self) -> int:
        """
        Get the count of archived memory items.
        
        Returns:
            int: Count of archived memory items
        """
        result = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM memory_items m
            JOIN memory_metadata mm ON m.id = mm.memory_id
            WHERE json_extract(mm.metadata_json, '$.status') = 'archived'
            """
        ).fetchone()
        
        return result[0] if result else 0
    
    def _get_database_size(self) -> int:
        """
        Get the size of the SQLite database file.
        
        Returns:
            int: Size of the database file in bytes
        """
        return os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
    
    def _get_last_access_time(self) -> Optional[float]:
        """
        Get the timestamp of the last accessed memory item.
        
        Returns:
            Optional[float]: Timestamp of last access or None if no access
        """
        result = self.conn.execute(
            """
            SELECT MAX(last_accessed)
            FROM memory_items
            WHERE last_accessed IS NOT NULL
            """
        ).fetchone()
        
        return result[0] if result and result[0] else None
    
    def _get_last_write_time(self) -> Optional[float]:
        """
        Get the timestamp of the last modified memory item.
        
        Returns:
            Optional[float]: Timestamp of last modification or None if no modification
        """
        result = self.conn.execute(
            """
            SELECT MAX(last_modified)
            FROM memory_items
            WHERE last_modified IS NOT NULL
            """
        ).fetchone()
        
        return result[0] if result and result[0] else None
    
    def get_memory_type_distribution(self) -> dict:
        """
        Get the distribution of memory items by type.
        
        Returns:
            dict: Distribution of memory items by type
        """
        results = self.conn.execute(
            """
            SELECT json_extract(mm.metadata_json, '$.type') as type, COUNT(*) as count
            FROM memory_items m
            JOIN memory_metadata mm ON m.id = mm.memory_id
            WHERE json_extract(mm.metadata_json, '$.type') IS NOT NULL
            GROUP BY type
            """
        ).fetchall()
        
        distribution = {}
        for row in results:
            distribution[row[0]] = row[1]
        
        return distribution
    
    def get_tag_distribution(self) -> dict:
        """
        Get the distribution of tags across memory items.
        
        Returns:
            dict: Distribution of tags
        """
        results = self.conn.execute(
            """
            SELECT tag, COUNT(*) as count
            FROM memory_tags
            GROUP BY tag
            ORDER BY count DESC
            """
        ).fetchall()
        
        distribution = {}
        for row in results:
            distribution[row[0]] = row[1]
        
        return distribution
