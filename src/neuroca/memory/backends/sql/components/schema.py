"""
SQL Schema Component

This module provides the SQLSchema class for creating and managing database schema.
"""

import logging
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.sql.components.connection import SQLConnection
from neuroca.memory.exceptions import StorageInitializationError

logger = logging.getLogger(__name__)


class SQLSchema:
    """
    Manages database schema for the SQL backend.
    
    This class is responsible for creating and maintaining the necessary
    database schema objects (tables, indexes, etc.) for the memory storage.
    """
    
    def __init__(
        self,
        connection: SQLConnection,
        schema: str = "memory",
        table_name: str = "memory_items",
    ):
        """
        Initialize the SQL schema component.
        
        Args:
            connection: SQL connection component
            schema: Database schema to use
            table_name: Table name for storing memory items
        """
        self.connection = connection
        self.schema = schema
        self.table_name = table_name
    
    @property
    def qualified_table_name(self) -> str:
        """Get the fully qualified table name."""
        return f'"{self.schema}"."{self.table_name}"'
    
    async def create_schema(self) -> None:
        """
        Create the database schema if it doesn't exist.
        
        Raises:
            StorageInitializationError: If schema creation fails
        """
        try:
            # Create schema if it doesn't exist
            create_schema_query = f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'
            await self.connection.execute_query(create_schema_query)
            logger.debug(f"Created schema {self.schema} (if it didn't exist)")
        except Exception as e:
            error_msg = f"Failed to create schema {self.schema}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def create_tables(self) -> None:
        """
        Create the necessary tables if they don't exist.
        
        Raises:
            StorageInitializationError: If table creation fails
        """
        try:
            # Create memory items table if it doesn't exist
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.qualified_table_name} (
                    id TEXT PRIMARY KEY,
                    content JSONB NOT NULL,
                    summary TEXT,
                    embedding JSONB,
                    metadata JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_accessed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    access_count INTEGER NOT NULL DEFAULT 0,
                    decay_factor FLOAT DEFAULT 1.0,
                    source TEXT,
                    associations JSONB
                )
            """
            await self.connection.execute_query(create_table_query)
            logger.debug(f"Created table {self.qualified_table_name} (if it didn't exist)")
        except Exception as e:
            error_msg = f"Failed to create table {self.qualified_table_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def create_indexes(self) -> None:
        """
        Create the necessary indexes if they don't exist.
        
        Raises:
            StorageInitializationError: If index creation fails
        """
        try:
            # Create indexes for efficient querying
            index_queries = [
                # Index on metadata status for faster filtering by status
                f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_status
                    ON {self.qualified_table_name} ((metadata->>'status'))
                """,
                
                # Index on tags for faster tag-based search
                f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_tags
                    ON {self.qualified_table_name} USING GIN ((metadata->'tags'))
                """,
                
                # Index on creation time for time-based queries
                f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created_at
                    ON {self.qualified_table_name} (created_at)
                """,
                
                # Text search index for content-based search
                f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_content_search
                    ON {self.qualified_table_name} USING GIN (to_tsvector('english', summary))
                """
            ]
            
            # Execute all index creation queries
            for query in index_queries:
                await self.connection.execute_query(query)
                
            logger.debug(f"Created indexes for table {self.qualified_table_name}")
        except Exception as e:
            error_msg = f"Failed to create indexes for {self.qualified_table_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def initialize(self) -> None:
        """
        Initialize the database schema.
        
        This creates the necessary schema, tables, and indexes if they don't exist.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Create schema
            await self.create_schema()
            
            # Create tables
            await self.create_tables()
            
            # Create indexes
            await self.create_indexes()
            
            logger.info(f"Initialized SQL schema with table {self.qualified_table_name}")
        except Exception as e:
            error_msg = f"Failed to initialize SQL schema: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def drop_schema(self, cascade: bool = False) -> None:
        """
        Drop the database schema and all its objects.
        
        Args:
            cascade: Whether to drop all objects in the schema
            
        Raises:
            StorageInitializationError: If schema drop fails
        """
        try:
            # Drop schema
            drop_schema_query = f'DROP SCHEMA IF EXISTS "{self.schema}"'
            if cascade:
                drop_schema_query += " CASCADE"
                
            await self.connection.execute_query(drop_schema_query)
            logger.info(f"Dropped schema {self.schema}" + (" CASCADE" if cascade else ""))
        except Exception as e:
            error_msg = f"Failed to drop schema {self.schema}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def drop_table(self) -> None:
        """
        Drop the memory items table.
        
        Raises:
            StorageInitializationError: If table drop fails
        """
        try:
            # Drop table
            drop_table_query = f'DROP TABLE IF EXISTS {self.qualified_table_name}'
            await self.connection.execute_query(drop_table_query)
            logger.info(f"Dropped table {self.qualified_table_name}")
        except Exception as e:
            error_msg = f"Failed to drop table {self.qualified_table_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def check_schema_exists(self) -> bool:
        """
        Check if the schema exists.
        
        Returns:
            bool: True if schema exists, False otherwise
        """
        try:
            # Check if schema exists
            check_schema_query = """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = $1
                )
            """
            result = await self.connection.execute_query(check_schema_query, [self.schema])
            return result[0]["exists"] if result else False
        except Exception as e:
            error_msg = f"Failed to check if schema {self.schema} exists: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False
    
    async def check_table_exists(self) -> bool:
        """
        Check if the table exists.
        
        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            # Check if table exists
            check_table_query = """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = $1 AND table_name = $2
                )
            """
            result = await self.connection.execute_query(
                check_table_query, [self.schema, self.table_name]
            )
            return result[0]["exists"] if result else False
        except Exception as e:
            error_msg = f"Failed to check if table {self.qualified_table_name} exists: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False
