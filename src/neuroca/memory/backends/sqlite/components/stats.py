"""
SQLite Statistics Component

This module provides a class for gathering statistics about the SQLite database,
such as memory counts, database size, and access/modification times.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Union

from neuroca.memory.interfaces import StorageStats

logger = logging.getLogger(__name__)


class SQLiteStats:
    """
    Handles statistics gathering for the SQLite database.
    
    This class provides methods for collecting statistics about memory items
    in the SQLite database, such as counts, sizes, and timestamps.
    """
    
    def __init__(self, connection_manager, db_path: str):
        """
        Initialize the statistics handler.
        
        Args:
            connection_manager: SQLiteConnection instance to manage database connections
            db_path: Path to the SQLite database file
        """
        self.connection_manager = connection_manager
        self.db_path = db_path
        # Initialize stats dictionary
        self._stats = {
            "create_count": 0,
            "read_count": 0,
            "update_count": 0,
            "delete_count": 0,
            "query_count": 0,
            "items_count": 0,
            "last_access_time": datetime.now(),
            "last_write_time": datetime.now()
        }
    
    def update_stat(self, stat_name: str, value: Any = 1) -> None:
        """
        Update a statistics value.
        
        Args:
            stat_name: Name of the statistic to update
            value: Value to add to the statistic (default is 1)
        """
        if stat_name in self._stats:
            if isinstance(self._stats[stat_name], (int, float)):
                self._stats[stat_name] += value
            else:
                self._stats[stat_name] = value
        else:
            self._stats[stat_name] = value
            
        # Update timestamps for certain operations
        if stat_name == "read_count":
            self._stats["last_access_time"] = datetime.now()
        elif stat_name in ["create_count", "update_count", "delete_count"]:
            self._stats["last_write_time"] = datetime.now()
            
        # Update items count for certain operations
        if stat_name == "create_count":
            self._stats["items_count"] += 1
        elif stat_name == "delete_count":
            self._stats["items_count"] = max(0, self._stats["items_count"] - 1)
    
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
        last_access_time = self._stats.get("last_access_time") or self._get_last_access_time()
        last_write_time = self._stats.get("last_write_time") or self._get_last_write_time()
        
        # Create stats object
        stats = StorageStats(
            total_memories=total_memories,
            active_memories=active_memories,
            archived_memories=archived_memories,
            total_size_bytes=db_size,
            last_access_time=last_access_time,
            last_write_time=last_write_time,
            # Include operation counts
            create_count=self._stats.get("create_count", 0),
            read_count=self._stats.get("read_count", 0),
            update_count=self._stats.get("update_count", 0),
            delete_count=self._stats.get("delete_count", 0),
            query_count=self._stats.get("query_count", 0)
        )
        
        logger.debug(f"Retrieved storage stats: {stats.total_memories} memories")
        return stats
    
    def _get_total_count(self) -> int:
        """
        Get the total count of memory items.
        
        Returns:
            int: Total count of memory items
        """
        # Get a connection for the current thread
        conn = self.connection_manager.get_connection()
        
        result = conn.execute(
            "SELECT COUNT(*) FROM memory_items"
        ).fetchone()
        
        return result[0] if result else 0
    
    def _get_active_count(self) -> int:
        """
        Get the count of active memory items.
        
        Returns:
            int: Count of active memory items
        """
        # Get a connection for the current thread
        conn = self.connection_manager.get_connection()
        
        result = conn.execute(
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
        # Get a connection for the current thread
        conn = self.connection_manager.get_connection()
        
        result = conn.execute(
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
        # For in-memory databases, return 0
        if self.db_path == ":memory:":
            return 0
            
        return os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
    
    def _get_last_access_time(self) -> Optional[Union[float, datetime]]:
        """
        Get the timestamp of the last accessed memory item.
        
        Returns:
            Optional[Union[float, datetime]]: Timestamp of last access or None if no access
        """
        # Get a connection for the current thread
        conn = self.connection_manager.get_connection()
        
        result = conn.execute(
            """
            SELECT MAX(last_accessed)
            FROM memory_items
            WHERE last_accessed IS NOT NULL
            """
        ).fetchone()
        
        return result[0] if result and result[0] else None
    
    def _get_last_write_time(self) -> Optional[Union[float, datetime]]:
        """
        Get the timestamp of the last modified memory item.
        
        Returns:
            Optional[Union[float, datetime]]: Timestamp of last modification or None if no modification
        """
        # Get a connection for the current thread
        conn = self.connection_manager.get_connection()
        
        result = conn.execute(
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
        # Get a connection for the current thread
        conn = self.connection_manager.get_connection()
        
        results = conn.execute(
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
        # Get a connection for the current thread
        conn = self.connection_manager.get_connection()
        
        results = conn.execute(
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
