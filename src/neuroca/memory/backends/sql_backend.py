"""
SQL Backend for Memory Storage

This module provides a SQL-based backend implementation for the Long-Term Memory (LTM)
storage system. It is designed to provide robust, scalable storage for long-term retention
of memories with comprehensive querying capabilities.

Features:
- Persistent storage in PostgreSQL database
- Support for complex queries with filtering
- JSONB storage for flexible schema
- Efficient indexing for fast retrieval
- Transactional operations for data integrity
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import (
    ConnectionError,
    DatabaseError,
    LTMStorageError,
    MemoryNotFoundError,
    StorageBackendError,
    StorageInitializationError,
)
from neuroca.db.connections.postgres import (
    AsyncPostgresConnection,
    PostgresConfig,
    get_postgres_connection,
)
from neuroca.memory.ltm.storage import (
    MemoryItem,
    MemoryMetadata,
    MemoryStatus,
    StorageBackend,
    StorageStats,
)

# Configure logger
logger = logging.getLogger(__name__)


class SQLStorageBackend(StorageBackend):
    """
    SQL implementation of the storage backend for LTM.
    
    This implementation uses PostgreSQL for storing long-term memories with:
    - Persistent, reliable storage
    - Advanced querying capabilities
    - Efficient indexing
    - ACID compliance for data integrity
    """
    
    def __init__(
        self,
        schema: str = "memory",
        table_name: str = "ltm_items",
        connection: Optional[AsyncPostgresConnection] = None,
        **config: Any,
    ):
        """
        Initialize the SQL storage backend.
        
        Args:
            schema: Database schema to use
            table_name: Table name for storing memory items
            connection: Optional database connection to use
            **config: Additional configuration for database connection
        """
        self.schema = schema
        self.table_name = table_name
        self._connection = connection
        self._config = config
        self._initialized = False
        self._lock = asyncio.Lock()
    
    @property
    def qualified_table_name(self) -> str:
        """Get the fully qualified table name."""
        return f'"{self.schema}"."{self.table_name}"'
    
    async def initialize(self) -> None:
        """
        Initialize the SQL storage backend.
        
        This creates the necessary schema and tables if they don't exist.
        
        Raises:
            StorageInitializationError: If initialization fails
        """
        try:
            # Create connection if not provided
            if self._connection is None:
                pg_config = PostgresConfig.from_env()
                # Override with any provided config
                for key, value in self._config.items():
                    setattr(pg_config, key, value)
                # Use async mode for better performance
                pg_config.connection_mode = "async"
                self._connection = get_postgres_connection(pg_config, async_mode=True)
            
            # Create schema if it doesn't exist
            async with self._connection as conn:
                await conn.execute_query(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"')
                
                # Create memory items table if it doesn't exist
                await conn.execute_query(f"""
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
                """)
                
                # Create indexes
                # Index on metadata status for faster filtering by status
                await conn.execute_query(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_status
                    ON {self.qualified_table_name} ((metadata->>'status'))
                """)
                
                # Index on tags for faster tag-based search
                await conn.execute_query(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_tags
                    ON {self.qualified_table_name} USING GIN ((metadata->'tags'))
                """)
                
                # Index on creation time for time-based queries
                await conn.execute_query(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created_at
                    ON {self.qualified_table_name} (created_at)
                """)
                
                # Text search index for content-based search
                await conn.execute_query(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_content_search
                    ON {self.qualified_table_name} USING GIN (to_tsvector('english', summary))
                """)
                
                logger.info(f"Initialized SQL storage backend with table {self.qualified_table_name}")
                self._initialized = True
                
        except Exception as e:
            error_msg = f"Failed to initialize SQL storage backend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageInitializationError(error_msg) from e
    
    async def _ensure_initialized(self) -> None:
        """Ensure the backend is initialized before use."""
        if not self._initialized:
            await self.initialize()
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            The ID of the stored memory
            
        Raises:
            StorageBackendError: If the memory cannot be stored
        """
        try:
            await self._ensure_initialized()
            
            # Convert memory_item to a dict
            memory_dict = memory_item.model_dump()
            
            # Extract primary fields
            memory_id = memory_dict.pop("id")
            content = memory_dict.pop("content", {})
            summary = memory_dict.pop("summary", None)
            embedding = memory_dict.pop("embedding", None)
            metadata = memory_dict.pop("metadata", None)
            source = memory_dict.pop("source", None)
            associations = memory_dict.pop("associations", None)
            
            # Convert Pydantic models to dicts
            if metadata is not None and isinstance(metadata, dict) and "status" in metadata:
                if isinstance(metadata["status"], MemoryStatus):
                    metadata["status"] = metadata["status"].value
            
            # Prepare for insertion
            async with self._connection as conn:
                query = f"""
                    INSERT INTO {self.qualified_table_name}
                    (id, content, summary, embedding, metadata, created_at, source, associations)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE
                    SET content = $2,
                        summary = $3,
                        embedding = $4,
                        metadata = $5,
                        source = $7,
                        associations = $8
                    RETURNING id
                """
                
                created_at = datetime.now()
                if metadata and "created_at" in metadata:
                    created_at = metadata["created_at"]
                
                result = await conn.execute_query(
                    query,
                    [
                        memory_id,
                        json.dumps(content),
                        summary,
                        json.dumps(embedding) if embedding else None,
                        json.dumps(metadata) if metadata else None,
                        created_at,
                        source,
                        json.dumps(associations) if associations else None,
                    ],
                    fetch_all=False,
                )
                
                # Return the ID
                return result[0]["id"] if result else memory_id
            
        except Exception as e:
            error_msg = f"Failed to store memory in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID from the database.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The memory item if found, None otherwise
            
        Raises:
            StorageBackendError: If there's an error retrieving the memory
        """
        try:
            await self._ensure_initialized()
            
            async with self._connection as conn:
                # Retrieve the memory
                query = f"""
                    SELECT *,
                        metadata->>'status' as status
                    FROM {self.qualified_table_name}
                    WHERE id = $1
                """
                result = await conn.execute_query(query, [memory_id], fetch_all=False)
                
                if not result:
                    logger.debug(f"Memory with ID {memory_id} not found in SQL")
                    return None
                
                # Update access stats
                update_query = f"""
                    UPDATE {self.qualified_table_name}
                    SET last_accessed = NOW(),
                        access_count = access_count + 1
                    WHERE id = $1
                """
                await conn.execute_query(update_query, [memory_id], fetch_all=False)
                
                # Convert DB row to MemoryItem
                row = result[0]
                
                # Parse JSON fields
                content = json.loads(row["content"]) if row["content"] else {}
                embedding = json.loads(row["embedding"]) if row["embedding"] else None
                metadata_dict = json.loads(row["metadata"]) if row["metadata"] else {}
                associations = json.loads(row["associations"]) if row["associations"] else None
                
                # Add access metrics to metadata
                metadata_dict.update({
                    "last_accessed": row["last_accessed"].isoformat() if row["last_accessed"] else None,
                    "access_count": row["access_count"]
                })
                
                # Create metadata object
                metadata = MemoryMetadata(**metadata_dict)
                
                # Create and return memory item
                memory_item = MemoryItem(
                    id=row["id"],
                    content=content,
                    summary=row["summary"],
                    embedding=embedding,
                    metadata=metadata,
                    source=row["source"],
                    associations=associations,
                )
                
                logger.debug(f"Retrieved memory with ID {memory_id} from SQL")
                return memory_item
                
        except Exception as e:
            error_msg = f"Failed to retrieve memory with ID {memory_id} from SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the database.
        
        Args:
            memory_item: The memory item to update
            
        Returns:
            True if the update was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error updating the memory
        """
        try:
            await self._ensure_initialized()
            
            # Check if memory exists
            existing_memory = await self.get(memory_item.id)
            if existing_memory is None:
                logger.warning(f"Memory with ID {memory_item.id} not found for update")
                return False
            
            # Store the updated memory (using store for simplicity, as it handles UPSERT)
            await self.store(memory_item)
            logger.debug(f"Updated memory with ID {memory_item.id} in SQL")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update memory with ID {memory_item.id} in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the database.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            True if the deletion was successful, False otherwise
            
        Raises:
            StorageBackendError: If there's an error deleting the memory
        """
        try:
            await self._ensure_initialized()
            
            async with self._connection as conn:
                # Delete the memory
                query = f"""
                    DELETE FROM {self.qualified_table_name}
                    WHERE id = $1
                    RETURNING id
                """
                result = await conn.execute_query(query, [memory_id], fetch_all=False)
                
                success = len(result) > 0
                if success:
                    logger.debug(f"Deleted memory with ID {memory_id} from SQL")
                else:
                    logger.warning(f"Memory with ID {memory_id} not found for deletion")
                
                return success
                
        except Exception as e:
            error_msg = f"Failed to delete memory with ID {memory_id} from SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: int = 10,
        offset: int = 0
    ) -> List[MemoryItem]:
        """
        Search for memory items in the database.
        
        Args:
            query: The search query
            filters: Optional filters to apply to the search
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of memory items matching the search criteria
            
        Raises:
            StorageBackendError: If there's an error during search
        """
        try:
            await self._ensure_initialized()
            
            # Prepare base query
            select_clause = f"""
                SELECT *,
                    metadata->>'status' as status
                FROM {self.qualified_table_name}
            """
            
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
            if filters:
                for key, value in filters.items():
                    if key == "status" and value:
                        where_clauses.append(f"metadata->>'status' = ${param_idx}")
                        params.append(value if isinstance(value, str) else value.value)
                        param_idx += 1
                    elif key == "importance" and value is not None:
                        where_clauses.append(f"(metadata->>'importance')::float >= ${param_idx}")
                        params.append(float(value))
                        param_idx += 1
                    elif key == "tags" and value:
                        # Check if any of the provided tags exist in the metadata tags array
                        tag_clauses = []
                        for tag in value:
                            tag_clauses.append(f"metadata->'tags' ? ${param_idx}")
                            params.append(tag)
                            param_idx += 1
                        if tag_clauses:
                            where_clauses.append(f"({' OR '.join(tag_clauses)})")
                    elif key == "created_after" and value:
                        where_clauses.append(f"created_at >= ${param_idx}")
                        params.append(value)
                        param_idx += 1
                    elif key == "created_before" and value:
                        where_clauses.append(f"created_at <= ${param_idx}")
                        params.append(value)
                        param_idx += 1
            
            # Build the where clause
            where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Add order by, limit, and offset
            query_string = f"""
                {select_clause}
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx+1}
            """
            params.extend([limit, offset])
            
            # Execute the query
            async with self._connection as conn:
                result = await conn.execute_query(query_string, params)
                
                # Convert DB rows to MemoryItems
                memories = []
                for row in result:
                    # Parse JSON fields
                    content = json.loads(row["content"]) if row["content"] else {}
                    embedding = json.loads(row["embedding"]) if row["embedding"] else None
                    metadata_dict = json.loads(row["metadata"]) if row["metadata"] else {}
                    associations = json.loads(row["associations"]) if row["associations"] else None
                    
                    # Add access metrics to metadata
                    metadata_dict.update({
                        "last_accessed": row["last_accessed"].isoformat() if row["last_accessed"] else None,
                        "access_count": row["access_count"]
                    })
                    
                    # Create metadata object
                    metadata = MemoryMetadata(**metadata_dict)
                    
                    # Create memory item
                    memory_item = MemoryItem(
                        id=row["id"],
                        content=content,
                        summary=row["summary"],
                        embedding=embedding,
                        metadata=metadata,
                        source=row["source"],
                        associations=associations,
                    )
                    memories.append(memory_item)
                
                logger.debug(f"Search for '{query}' returned {len(memories)} results from SQL")
                return memories
                
        except Exception as e:
            error_msg = f"Failed to search memories in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
    
    async def get_stats(self) -> StorageStats:
        """
        Get statistics about the database storage.
        
        Returns:
            Statistics about the storage
            
        Raises:
            StorageBackendError: If there's an error retrieving statistics
        """
        try:
            await self._ensure_initialized()
            
            async with self._connection as conn:
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM {self.qualified_table_name}
                """
                count_result = await conn.execute_query(count_query)
                total_count = count_result[0]["total"] if count_result else 0
                
                # Get counts by status
                status_query = f"""
                    SELECT
                        COUNT(*) FILTER (WHERE metadata->>'status' = 'active') as active_count,
                        COUNT(*) FILTER (WHERE metadata->>'status' = 'archived') as archived_count
                    FROM {self.qualified_table_name}
                """
                status_result = await conn.execute_query(status_query)
                active_count = status_result[0]["active_count"] if status_result else 0
                archived_count = status_result[0]["archived_count"] if status_result else 0
                
                # Estimate total size
                size_query = f"""
                    SELECT
                        pg_total_relation_size('{self.qualified_table_name}'::regclass) as total_size
                """
                size_result = await conn.execute_query(size_query)
                total_size_bytes = size_result[0]["total_size"] if size_result else 0
                
                # Get last access and write times
                time_query = f"""
                    SELECT
                        MAX(last_accessed) as last_access,
                        MAX(created_at) as last_write
                    FROM {self.qualified_table_name}
                """
                time_result = await conn.execute_query(time_query)
                last_access = time_result[0]["last_access"] if time_result and time_result[0]["last_access"] else None
                last_write = time_result[0]["last_write"] if time_result and time_result[0]["last_write"] else None
                
                # Create and return stats
                stats = StorageStats(
                    total_memories=total_count,
                    active_memories=active_count,
                    archived_memories=archived_count,
                    total_size_bytes=total_size_bytes,
                    last_access_time=last_access,
                    last_write_time=last_write
                )
                
                logger.debug(f"Retrieved storage statistics from SQL: {stats}")
                return stats
                
        except Exception as e:
            error_msg = f"Failed to get storage statistics from SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageBackendError(error_msg) from e
