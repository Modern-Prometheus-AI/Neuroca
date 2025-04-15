"""
SQL CRUD Operations Component

This module provides the SQLCRUD class for performing CRUD operations on memory items.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from neuroca.memory.backends.sql.components.connection import SQLConnection
from neuroca.memory.backends.sql.components.schema import SQLSchema
from neuroca.memory.exceptions import StorageBackendError, StorageOperationError
from neuroca.memory.models.memory_item import MemoryItem, MemoryMetadata

logger = logging.getLogger(__name__)


class SQLCRUD:
    """
    Handles CRUD operations for memory items in SQL database.
    
    This class provides methods for creating, reading, updating, and
    deleting memory items in a PostgreSQL database.
    """
    
    def __init__(
        self,
        connection: SQLConnection,
        schema: SQLSchema,
    ):
        """
        Initialize the SQL CRUD operations component.
        
        Args:
            connection: SQL connection component
            schema: SQL schema component
        """
        self.connection = connection
        self.schema = schema
    
    async def create(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the database.
        
        Args:
            memory_item: The memory item to store
            
        Returns:
            str: The ID of the stored memory
            
        Raises:
            StorageOperationError: If the memory cannot be stored
        """
        try:
            # Convert memory_item to a dict
            memory_dict = memory_item.model_dump()
            
            # Extract primary fields
            memory_id = memory_dict.get("id")
            content = memory_dict.get("content", {})
            summary = memory_dict.get("summary")
            embedding = memory_dict.get("embedding")
            metadata = memory_dict.get("metadata", {})
            source = memory_dict.get("source")
            associations = memory_dict.get("associations")
            
            # Prepare for insertion
            query = f"""
                INSERT INTO {self.schema.qualified_table_name}
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
            
            # Get created_at timestamp
            created_at = datetime.now()
            if metadata and isinstance(metadata, dict) and "created_at" in metadata:
                created_at_str = metadata["created_at"]
                if isinstance(created_at_str, str):
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                    except ValueError:
                        pass
            
            # Convert to JSON strings for storage
            content_json = json.dumps(content) if content else None
            embedding_json = json.dumps(embedding) if embedding else None
            metadata_json = json.dumps(metadata) if metadata else None
            associations_json = json.dumps(associations) if associations else None
            
            # Execute the query
            params = [
                memory_id,
                content_json,
                summary,
                embedding_json,
                metadata_json,
                created_at,
                source,
                associations_json,
            ]
            
            result = await self.connection.execute_query(query, params, fetch_all=False)
            
            # Return the ID
            return result[0]["id"] if result else memory_id
            
        except Exception as e:
            error_msg = f"Failed to store memory in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def read(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID from the database.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            Optional[MemoryItem]: The memory item if found, None otherwise
            
        Raises:
            StorageOperationError: If there's an error retrieving the memory
        """
        try:
            # Retrieve the memory
            query = f"""
                SELECT *,
                    metadata->>'status' as status
                FROM {self.schema.qualified_table_name}
                WHERE id = $1
            """
            
            result = await self.connection.execute_query(query, [memory_id], fetch_all=False)
            
            if not result:
                logger.debug(f"Memory with ID {memory_id} not found in SQL")
                return None
            
            # Update access stats
            update_query = f"""
                UPDATE {self.schema.qualified_table_name}
                SET last_accessed = NOW(),
                    access_count = access_count + 1
                WHERE id = $1
            """
            await self.connection.execute_query(update_query, [memory_id], fetch_all=False)
            
            # Convert DB row to MemoryItem
            return self._row_to_memory_item(result[0])
                
        except Exception as e:
            error_msg = f"Failed to retrieve memory with ID {memory_id} from SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update(self, memory_item: MemoryItem) -> bool:
        """
        Update an existing memory item in the database.
        
        Args:
            memory_item: The memory item to update
            
        Returns:
            bool: True if the update was successful, False otherwise
            
        Raises:
            StorageOperationError: If there's an error updating the memory
        """
        try:
            # Check if memory exists
            existing = await self.read(memory_item.id)
            if existing is None:
                logger.warning(f"Memory with ID {memory_item.id} not found for update")
                return False
            
            # Convert memory_item to a dict
            memory_dict = memory_item.model_dump()
            
            # Extract primary fields
            memory_id = memory_dict.get("id")
            content = memory_dict.get("content", {})
            summary = memory_dict.get("summary")
            embedding = memory_dict.get("embedding")
            metadata = memory_dict.get("metadata", {})
            source = memory_dict.get("source")
            associations = memory_dict.get("associations")
            
            # Prepare for update
            query = f"""
                UPDATE {self.schema.qualified_table_name}
                SET content = $2,
                    summary = $3,
                    embedding = $4,
                    metadata = $5,
                    source = $6,
                    associations = $7,
                    last_accessed = NOW()
                WHERE id = $1
                RETURNING id
            """
            
            # Convert to JSON strings for storage
            content_json = json.dumps(content) if content else None
            embedding_json = json.dumps(embedding) if embedding else None
            metadata_json = json.dumps(metadata) if metadata else None
            associations_json = json.dumps(associations) if associations else None
            
            # Execute the query
            params = [
                memory_id,
                content_json,
                summary,
                embedding_json,
                metadata_json,
                source,
                associations_json,
            ]
            
            result = await self.connection.execute_query(query, params, fetch_all=False)
            
            success = len(result) > 0
            if success:
                logger.debug(f"Updated memory with ID {memory_id} in SQL")
            else:
                logger.warning(f"Failed to update memory with ID {memory_id} in SQL")
            
            return success
                
        except Exception as e:
            error_msg = f"Failed to update memory with ID {memory_item.id} in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from the database.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            bool: True if the deletion was successful, False otherwise
            
        Raises:
            StorageOperationError: If there's an error deleting the memory
        """
        try:
            # Delete the memory
            query = f"""
                DELETE FROM {self.schema.qualified_table_name}
                WHERE id = $1
                RETURNING id
            """
            
            result = await self.connection.execute_query(query, [memory_id], fetch_all=False)
            
            success = len(result) > 0
            if success:
                logger.debug(f"Deleted memory with ID {memory_id} from SQL")
            else:
                logger.warning(f"Memory with ID {memory_id} not found for deletion")
            
            return success
                
        except Exception as e:
            error_msg = f"Failed to delete memory with ID {memory_id} from SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def exists(self, memory_id: str) -> bool:
        """
        Check if a memory item exists in the database.
        
        Args:
            memory_id: The ID of the memory to check
            
        Returns:
            bool: True if the memory exists, False otherwise
            
        Raises:
            StorageOperationError: If there's an error checking the memory
        """
        try:
            # Check if memory exists
            query = f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self.schema.qualified_table_name}
                    WHERE id = $1
                )
            """
            
            result = await self.connection.execute_query(query, [memory_id], fetch_all=False)
            
            return result[0]["exists"] if result else False
                
        except Exception as e:
            error_msg = f"Failed to check if memory with ID {memory_id} exists in SQL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    def _row_to_memory_item(self, row: Dict[str, Any]) -> MemoryItem:
        """
        Convert a database row to a MemoryItem object.
        
        Args:
            row: Database row
            
        Returns:
            MemoryItem: The memory item
        """
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
        metadata = MemoryMetadata.model_validate(metadata_dict)
        
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
        
        return memory_item
