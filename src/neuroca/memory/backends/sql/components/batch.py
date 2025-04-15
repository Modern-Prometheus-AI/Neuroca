"""
SQL Batch Operations Component

This module provides the SQLBatch class for handling batch operations on memory items.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from neuroca.memory.backends.sql.components.connection import SQLConnection
from neuroca.memory.backends.sql.components.crud import SQLCRUD
from neuroca.memory.backends.sql.components.schema import SQLSchema
from neuroca.memory.exceptions import StorageOperationError
from neuroca.memory.models.memory_item import MemoryItem

logger = logging.getLogger(__name__)


class SQLBatch:
    """
    Handles batch operations for memory items in SQL database.
    
    This class provides methods for performing operations on multiple memory
    items at once with optimized performance.
    """
    
    def __init__(
        self,
        connection: SQLConnection,
        schema: SQLSchema,
        crud: SQLCRUD,
    ):
        """
        Initialize the SQL batch operations component.
        
        Args:
            connection: SQL connection component
            schema: SQL schema component
            crud: SQL CRUD component
        """
        self.connection = connection
        self.schema = schema
        self.crud = crud
    
    async def batch_create(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Create multiple memory items in a batch.
        
        Args:
            memory_items: List of memory items to create
            
        Returns:
            List[str]: List of created memory IDs
            
        Raises:
            StorageOperationError: If the batch create operation fails
        """
        try:
            if not memory_items:
                return []
            
            created_ids = []
            
            # Use a transaction to ensure atomicity
            async with self.connection.connection.transaction():
                for memory_item in memory_items:
                    memory_id = await self.crud.create(memory_item)
                    created_ids.append(memory_id)
            
            logger.debug(f"Batch created {len(created_ids)} memories")
            return created_ids
        except Exception as e:
            error_msg = f"Failed to batch create memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_read(self, memory_ids: List[str]) -> Dict[str, Optional[MemoryItem]]:
        """
        Read multiple memory items in a batch.
        
        Args:
            memory_ids: List of memory IDs to read
            
        Returns:
            Dict[str, Optional[MemoryItem]]: Dictionary mapping memory IDs to their items
            
        Raises:
            StorageOperationError: If the batch read operation fails
        """
        try:
            if not memory_ids:
                return {}
            
            # Prepare placeholders for the IN clause
            placeholders = []
            for i in range(len(memory_ids)):
                placeholders.append(f"${i+1}")
            
            # Build query
            query = f"""
                SELECT *,
                    metadata->>'status' as status
                FROM {self.schema.qualified_table_name}
                WHERE id IN ({", ".join(placeholders)})
            """
            
            # Execute query
            rows = await self.connection.execute_query(query, memory_ids)
            
            # Build result dictionary
            result = {memory_id: None for memory_id in memory_ids}
            row_by_id = {row["id"]: row for row in rows}
            
            # Update access times in a separate query
            if rows:
                access_ids = [row["id"] for row in rows]
                update_query = f"""
                    UPDATE {self.schema.qualified_table_name}
                    SET last_accessed = NOW(),
                        access_count = access_count + 1
                    WHERE id IN ({", ".join(f"${i+1}" for i in range(len(access_ids)))})
                """
                await self.connection.execute_query(update_query, access_ids, fetch_all=False)
            
            # Convert rows to memory items
            for memory_id in memory_ids:
                if memory_id in row_by_id:
                    result[memory_id] = self.crud._row_to_memory_item(row_by_id[memory_id])
            
            logger.debug(f"Batch read {len(rows)} out of {len(memory_ids)} memories")
            return result
        except Exception as e:
            error_msg = f"Failed to batch read memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_update(self, memory_items: List[MemoryItem]) -> Dict[str, bool]:
        """
        Update multiple memory items in a batch.
        
        Args:
            memory_items: List of memory items to update
            
        Returns:
            Dict[str, bool]: Dictionary mapping memory IDs to update success
            
        Raises:
            StorageOperationError: If the batch update operation fails
        """
        try:
            if not memory_items:
                return {}
            
            result = {}
            
            # Use a transaction to ensure atomicity
            async with self.connection.connection.transaction():
                for memory_item in memory_items:
                    success = await self.crud.update(memory_item)
                    result[memory_item.id] = success
            
            logger.debug(f"Batch updated {sum(1 for v in result.values() if v)} out of {len(memory_items)} memories")
            return result
        except Exception as e:
            error_msg = f"Failed to batch update memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_delete(self, memory_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple memory items in a batch.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            Dict[str, bool]: Dictionary mapping memory IDs to deletion success
            
        Raises:
            StorageOperationError: If the batch delete operation fails
        """
        try:
            if not memory_ids:
                return {}
            
            # Prepare placeholders for the IN clause
            placeholders = []
            for i in range(len(memory_ids)):
                placeholders.append(f"${i+1}")
            
            # Build query
            query = f"""
                DELETE FROM {self.schema.qualified_table_name}
                WHERE id IN ({", ".join(placeholders)})
                RETURNING id
            """
            
            # Execute query
            rows = await self.connection.execute_query(query, memory_ids)
            
            # Build result dictionary
            deleted_ids = [row["id"] for row in rows]
            result = {memory_id: memory_id in deleted_ids for memory_id in memory_ids}
            
            logger.debug(f"Batch deleted {len(deleted_ids)} out of {len(memory_ids)} memories")
            return result
        except Exception as e:
            error_msg = f"Failed to batch delete memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def batch_exists(self, memory_ids: List[str]) -> Dict[str, bool]:
        """
        Check if multiple memory items exist in a batch.
        
        Args:
            memory_ids: List of memory IDs to check
            
        Returns:
            Dict[str, bool]: Dictionary mapping memory IDs to existence
            
        Raises:
            StorageOperationError: If the batch exists operation fails
        """
        try:
            if not memory_ids:
                return {}
            
            # Prepare placeholders for the IN clause
            placeholders = []
            for i in range(len(memory_ids)):
                placeholders.append(f"${i+1}")
            
            # Build query
            query = f"""
                SELECT id FROM {self.schema.qualified_table_name}
                WHERE id IN ({", ".join(placeholders)})
            """
            
            # Execute query
            rows = await self.connection.execute_query(query, memory_ids)
            
            # Build result dictionary
            existing_ids = [row["id"] for row in rows]
            result = {memory_id: memory_id in existing_ids for memory_id in memory_ids}
            
            return result
        except Exception as e:
            error_msg = f"Failed to batch check existence of memories: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
