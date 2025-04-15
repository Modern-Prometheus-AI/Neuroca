"""
SQLite CRUD Operations Component

This module provides a class for handling CRUD (Create, Read, Update, Delete)
operations on memory items in the SQLite database.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from neuroca.memory.models.memory_item import MemoryItem

logger = logging.getLogger(__name__)


class SQLiteCRUD:
    """
    Handles CRUD operations for memory items in SQLite database.
    
    This class provides methods for storing, retrieving, updating, and
    deleting memory items in the SQLite database.
    """
    
    def __init__(self, connection: sqlite3.Connection):
        """
        Initialize the CRUD operations handler.
        
        Args:
            connection: SQLite database connection
        """
        self.conn = connection
    
    def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
        """
        memory_id = memory_item.id or self._generate_id()
        
        # Ensure the memory item has an ID
        if not memory_item.id:
            memory_item.id = memory_id
        
        with self.conn:
            # Begin transaction
            self.conn.execute("BEGIN")
            
            try:
                # Store the memory item using the helper method
                self._store_memory_without_transaction(memory_item)
                
                # Commit the transaction
                self.conn.execute("COMMIT")
                
                logger.debug(f"Stored memory with ID: {memory_id}")
                return memory_id
            except Exception as e:
                # Rollback the transaction on error
                self.conn.execute("ROLLBACK")
                logger.error(f"Failed to store memory: {str(e)}")
                raise
    
    def _store_memory_without_transaction(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item without transaction handling.
        
        This method is used by both store() and batch_store() to avoid
        duplicating the core storage logic.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
        """
        memory_id = memory_item.id
        
        # Store the memory item
        self.conn.execute(
            """
            INSERT INTO memory_items (id, content, summary, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                memory_id,
                memory_item.content,
                memory_item.summary,
                datetime.now()
            )
        )
        
        # Store metadata if it exists
        if memory_item.metadata:
            self._store_metadata(memory_id, memory_item.metadata)
        
        return memory_id
    
    def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from the database by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
        """
        # Get the memory item
        memory_row = self.conn.execute(
            """
            SELECT id, content, summary, created_at, last_accessed, last_modified
            FROM memory_items
            WHERE id = ?
            """,
            (memory_id,)
        ).fetchone()
        
        if not memory_row:
            logger.debug(f"Memory with ID {memory_id} not found")
            return None
        
        # Update access time
        self.conn.execute(
            """
            UPDATE memory_items
            SET last_accessed = ?
            WHERE id = ?
            """,
            (datetime.now(), memory_id)
        )
        
        # Get metadata
        metadata = self._retrieve_metadata(memory_id)
        
        # Create the memory item
        memory_item = MemoryItem(
            id=memory_row[0],
            content=memory_row[1],
            summary=memory_row[2],
            metadata=metadata
        )
        
        logger.debug(f"Retrieved memory with ID: {memory_id}")
        return memory_item
    
    def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the database.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            bool: True if update was successful, False if memory not found
        """
        memory_id = memory_item.id
        
        if not memory_id:
            logger.error("Cannot update memory without ID")
            return False
        
        with self.conn:
            # Begin transaction
            self.conn.execute("BEGIN")
            
            try:
                # Check if memory exists
                exists = self.conn.execute(
                    "SELECT 1 FROM memory_items WHERE id = ?",
                    (memory_id,)
                ).fetchone()
                
                if not exists:
                    self.conn.execute("ROLLBACK")
                    logger.warning(f"Memory with ID {memory_id} not found for update")
                    return False
                
                # Update the memory item using the helper method
                success = self._update_memory_without_transaction(memory_item)
                
                # Commit the transaction
                self.conn.execute("COMMIT")
                
                logger.debug(f"Updated memory with ID: {memory_id}")
                return success
            except Exception as e:
                # Rollback the transaction on error
                self.conn.execute("ROLLBACK")
                logger.error(f"Failed to update memory {memory_id}: {str(e)}")
                raise
    
    def _update_memory_without_transaction(self, memory_item: MemoryItem) -> bool:
        """
        Update a memory item without transaction handling.
        
        This method is used by both update() and batch_update() to avoid
        duplicating the core update logic.
        
        Args:
            memory_item: Memory item to update
            
        Returns:
            bool: True if update was successful
        """
        memory_id = memory_item.id
        
        # Update the memory item
        self.conn.execute(
            """
            UPDATE memory_items
            SET content = ?, summary = ?, last_modified = ?
            WHERE id = ?
            """,
            (
                memory_item.content,
                memory_item.summary,
                datetime.now(),
                memory_id
            )
        )
        
        # Update metadata if it exists
        if memory_item.metadata:
            self._update_metadata(memory_id, memory_item.metadata)
        
        return True
    
    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the database.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            bool: True if deletion was successful, False if memory not found
        """
        with self.conn:
            # Check if memory exists
            exists = self.conn.execute(
                "SELECT 1 FROM memory_items WHERE id = ?",
                (memory_id,)
            ).fetchone()
            
            if not exists:
                logger.warning(f"Memory with ID {memory_id} not found for deletion")
                return False
            
            # Delete the memory item
            # Foreign key constraints will handle related deletions
            self.conn.execute(
                "DELETE FROM memory_items WHERE id = ?",
                (memory_id,)
            )
            
            logger.debug(f"Deleted memory with ID: {memory_id}")
            return True
    
    def _store_metadata(self, memory_id: str, metadata: Dict) -> None:
        """
        Store metadata for a memory item.
        
        Args:
            memory_id: ID of the memory item
            metadata: Metadata to store
        """
        metadata_json = json.dumps(metadata)
        
        self.conn.execute(
            """
            INSERT INTO memory_metadata (memory_id, metadata_json)
            VALUES (?, ?)
            """,
            (memory_id, metadata_json)
        )
        
        # Store tags if they exist
        if metadata.get("tags"):
            for tag in metadata["tags"]:
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO memory_tags (memory_id, tag)
                    VALUES (?, ?)
                    """,
                    (memory_id, tag)
                )
    
    def _update_metadata(self, memory_id: str, metadata: Dict) -> None:
        """
        Update metadata for a memory item.
        
        Args:
            memory_id: ID of the memory item
            metadata: Updated metadata
        """
        metadata_json = json.dumps(metadata)
        
        # Check if metadata exists
        metadata_exists = self.conn.execute(
            "SELECT 1 FROM memory_metadata WHERE memory_id = ?",
            (memory_id,)
        ).fetchone()
        
        if metadata_exists:
            self.conn.execute(
                """
                UPDATE memory_metadata
                SET metadata_json = ?
                WHERE memory_id = ?
                """,
                (metadata_json, memory_id)
            )
        else:
            self.conn.execute(
                """
                INSERT INTO memory_metadata (memory_id, metadata_json)
                VALUES (?, ?)
                """,
                (memory_id, metadata_json)
            )
        
        # Update tags
        if metadata.get("tags"):
            # Delete existing tags
            self.conn.execute(
                "DELETE FROM memory_tags WHERE memory_id = ?",
                (memory_id,)
            )
            
            # Add new tags
            for tag in metadata["tags"]:
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO memory_tags (memory_id, tag)
                    VALUES (?, ?)
                    """,
                    (memory_id, tag)
                )
    
    def _retrieve_metadata(self, memory_id: str) -> Dict:
        """
        Retrieve metadata for a memory item.
        
        Args:
            memory_id: ID of the memory item
            
        Returns:
            Dict: Memory metadata or empty dict if not found
        """
        metadata_row = self.conn.execute(
            """
            SELECT metadata_json
            FROM memory_metadata
            WHERE memory_id = ?
            """,
            (memory_id,)
        ).fetchone()
        
        if metadata_row:
            return json.loads(metadata_row[0])
        
        return {}
    
    def _generate_id(self) -> str:
        """
        Generate a unique ID for a memory item.
        
        Returns:
            str: A unique UUID
        """
        return str(uuid.uuid4())
