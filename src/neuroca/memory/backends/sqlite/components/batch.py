"""
SQLite Batch Operations Component

This module provides a class for handling batch operations on memory items
in the SQLite database, such as batch storing, retrieving, and deleting.
"""

import logging
import sqlite3
from typing import List

from neuroca.memory.models.memory_item import MemoryItem

logger = logging.getLogger(__name__)


class SQLiteBatch:
    """
    Handles batch operations for memory items in SQLite database.
    
    This class provides methods for performing operations on multiple
    memory items in a single transaction for improved performance.
    """
    
    def __init__(self, connection: sqlite3.Connection, crud):
        """
        Initialize the batch operations handler.
        
        Args:
            connection: SQLite database connection
            crud: SQLiteCRUD instance for single-item operations
        """
        self.conn = connection
        self.crud = crud
    
    def batch_store(self, memory_items: List[MemoryItem]) -> List[str]:
        """
        Store multiple memory items in a single transaction.
        
        Args:
            memory_items: List of memory items to store
            
        Returns:
            List[str]: List of stored memory IDs
        """
        # Generate IDs for memories that don't have them
        for memory_item in memory_items:
            if not memory_item.id:
                memory_item.id = self.crud._generate_id()
        
        memory_ids = [item.id for item in memory_items]
        
        with self.conn:
            # Begin transaction
            self.conn.execute("BEGIN")
            
            try:
                for memory_item in memory_items:
                    # Store the memory item
                    self.crud._store_memory_without_transaction(memory_item)
                
                # Commit the transaction
                self.conn.execute("COMMIT")
                
                logger.debug(f"Batch stored {len(memory_ids)} memories")
                return memory_ids
            except Exception as e:
                # Rollback the transaction on error
                self.conn.execute("ROLLBACK")
                logger.error(f"Failed to batch store memories: {str(e)}")
                raise
    
    def batch_retrieve(self, memory_ids: List[str]) -> List[MemoryItem]:
        """
        Retrieve multiple memory items in an efficient manner.
        
        Args:
            memory_ids: List of memory IDs to retrieve
            
        Returns:
            List[MemoryItem]: List of retrieved memory items
        """
        if not memory_ids:
            return []
        
        memory_items = []
        
        for memory_id in memory_ids:
            memory_item = self.crud.retrieve(memory_id)
            if memory_item:
                memory_items.append(memory_item)
        
        logger.debug(f"Batch retrieved {len(memory_items)} of {len(memory_ids)} memories")
        return memory_items
    
    def batch_delete(self, memory_ids: List[str]) -> int:
        """
        Delete multiple memory items in a single transaction.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            int: Number of memories actually deleted
        """
        if not memory_ids:
            return 0
        
        with self.conn:
            # Begin transaction
            self.conn.execute("BEGIN")
            
            try:
                deleted_count = 0
                
                for memory_id in memory_ids:
                    # Delete the memory item
                    cursor = self.conn.execute(
                        "DELETE FROM memory_items WHERE id = ?",
                        (memory_id,)
                    )
                    
                    deleted_count += cursor.rowcount
                
                # Commit the transaction
                self.conn.execute("COMMIT")
                
                logger.debug(f"Batch deleted {deleted_count} memories")
                return deleted_count
            except Exception as e:
                # Rollback the transaction on error
                self.conn.execute("ROLLBACK")
                logger.error(f"Failed to batch delete memories: {str(e)}")
                raise
    
    def batch_update(self, memory_items: List[MemoryItem]) -> int:
        """
        Update multiple memory items in a single transaction.
        
        Args:
            memory_items: List of memory items to update
            
        Returns:
            int: Number of memories actually updated
        """
        if not memory_items:
            return 0
        
        with self.conn:
            # Begin transaction
            self.conn.execute("BEGIN")
            
            try:
                updated_count = 0
                
                for memory_item in memory_items:
                    if not memory_item.id:
                        logger.warning("Skipping update for memory without ID")
                        continue
                    
                    # Check if memory exists
                    exists = self.conn.execute(
                        "SELECT 1 FROM memory_items WHERE id = ?",
                        (memory_item.id,)
                    ).fetchone()
                    
                    if not exists:
                        logger.warning(f"Memory with ID {memory_item.id} not found for update")
                        continue
                    
                    # Update using the single-item method (without transactions)
                    if self.crud._update_memory_without_transaction(memory_item):
                        updated_count += 1
                
                # Commit the transaction
                self.conn.execute("COMMIT")
                
                logger.debug(f"Batch updated {updated_count} memories")
                return updated_count
            except Exception as e:
                # Rollback the transaction on error
                self.conn.execute("ROLLBACK")
                logger.error(f"Failed to batch update memories: {str(e)}")
                raise
