"""
SQLite Schema Management Component

This module provides a class for managing SQLite database schema, including
tables, indices, and constraints for the memory storage system.
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


class SQLiteSchema:
    """
    Manages the SQLite database schema for memory storage.
    
    This class is responsible for creating and maintaining the database
    schema, including tables, indices, and constraints.
    """
    
    def __init__(self, connection_manager):
        """
        Initialize the schema manager.
        
        Args:
            connection_manager: SQLiteConnection instance to manage database connections
        """
        self.connection_manager = connection_manager
    
    def initialize_schema(self) -> None:
        """
        Initialize the database schema with necessary tables and indices.
        
        Creates the following tables if they don't exist:
        - memory_items: Store core memory data
        - memory_metadata: Store associated metadata
        - memory_tags: Store tags for efficient searching
        """
        # Get the connection for the current thread
        conn = self.connection_manager.get_connection()
        
        with conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create the memory_items table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    summary TEXT,
                    embeddings BLOB,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    last_modified TIMESTAMP
                )
            """)
            
            # Create the memory_metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_metadata (
                    memory_id TEXT PRIMARY KEY,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY (memory_id) REFERENCES memory_items(id) ON DELETE CASCADE
                )
            """)
            
            # Create the memory_tags table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY (memory_id) REFERENCES memory_items(id) ON DELETE CASCADE,
                    UNIQUE(memory_id, tag)
                )
            """)
            
            # Create indices for improved search performance
            self._create_indices()
            
            logger.debug("SQLite database schema initialized successfully")
    
    def _create_indices(self) -> None:
        """
        Create indices for improved query performance.
        """
        # Get the connection for the current thread
        conn = self.connection_manager.get_connection()
        
        with conn:
            # Index on content for full-text search
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_content ON memory_items(content)"
            )
            
            # Index on summary for search
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_summary ON memory_items(summary)"
            )
            
            # Index on tags for filtering
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_tags(tag)"
            )
            
            # Index on created_at for sorting
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_items(created_at)"
            )
            
            # Index on last_accessed for filtering
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_accessed ON memory_items(last_accessed)"
            )
            
            logger.debug("SQLite database indices created successfully")
    
    def upgrade_schema(self, current_version: int, target_version: int) -> None:
        """
        Upgrade the database schema from one version to another.
        
        Args:
            current_version: Current schema version
            target_version: Target schema version to upgrade to
        """
        # This is a placeholder for future schema migrations
        # For now, we just initialize the schema
        if current_version == 0:
            self.initialize_schema()
            logger.info(f"Upgraded schema from version {current_version} to {target_version}")
