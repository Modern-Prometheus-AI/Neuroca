"""
Long-Term Memory (LTM) Repository Module.

This module provides database access and operations for the Long-Term Memory component
of the NeuroCognitive Architecture. It handles CRUD operations, search functionality,
and memory consolidation processes for long-term memories.

The LTM repository is responsible for:
1. Storing and retrieving semantic knowledge
2. Managing episodic memories
3. Supporting memory consolidation from STM/WM
4. Implementing forgetting mechanisms based on relevance and time
5. Providing efficient search and retrieval based on embeddings and metadata

Usage:
    repo = LTMRepository()
    
    # Store a new memory
    memory_id = await repo.store_memory(memory_data)
    
    # Retrieve a memory
    memory = await repo.get_memory(memory_id)
    
    # Search for relevant memories
    memories = await repo.search_memories(query_embedding, limit=5)
"""

import datetime
import logging
import uuid
from typing import Any, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import (
    DatabaseConnectionError,
    MemoryNotFoundError,
    MemoryStorageError,
    RepositoryError,
)
from neuroca.core.models.memory import (
    LTMMemory,
    MemoryImportance,
    MemoryRetrievalMetadata,
    MemoryType,
)
from neuroca.core.utils.embedding import cosine_similarity, normalize_embedding
from neuroca.core.utils.time import get_current_timestamp

# Configure logger
logger = logging.getLogger(__name__)


class LTMRepository:
    """
    Repository for managing Long-Term Memory (LTM) storage and retrieval operations.
    
    This class provides methods to store, retrieve, update, and search memories in the
    long-term memory database. It handles vector similarity search, memory consolidation,
    and implements forgetting mechanisms based on memory importance and recency.
    """

    def __init__(self, connection_string: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize the LTM Repository with database connection parameters.
        
        Args:
            connection_string: MongoDB connection string. If None, uses the value from settings.
            db_name: Database name. If None, uses the value from settings.
            
        Raises:
            DatabaseConnectionError: If the database connection cannot be established.
        """
        settings = get_settings()
        self._connection_string = connection_string or settings.mongodb_uri
        self._db_name = db_name or settings.mongodb_db_name
        self._collection_name = "ltm_memories"
        self._client = None
        self._db = None
        self._collection = None
        self._connected = False
        
        # Index fields for efficient querying
        self._indexes = [
            [("memory_id", 1)],  # Unique ID index
            [("created_at", -1)],  # Timestamp index for recency queries
            [("memory_type", 1)],  # Memory type index
            [("importance", -1)],  # Importance index
            [("tags", 1)],  # Tags index for categorical searches
            [("last_accessed", -1)]  # Last accessed index for forgetting mechanisms
        ]

    async def connect(self) -> None:
        """
        Establish connection to the MongoDB database.
        
        Creates necessary indexes if they don't exist.
        
        Raises:
            DatabaseConnectionError: If connection to the database fails.
        """
        if self._connected:
            return
            
        try:
            logger.debug(f"Connecting to MongoDB at {self._connection_string}")
            self._client = AsyncIOMotorClient(self._connection_string)
            self._db = self._client[self._db_name]
            self._collection = self._db[self._collection_name]
            
            # Create indexes
            for index in self._indexes:
                await self._collection.create_index(index)
                
            # Create unique index on memory_id
            await self._collection.create_index([("memory_id", 1)], unique=True)
            
            # Create text index for content search
            await self._collection.create_index([
                ("content", "text"), 
                ("title", "text"),
                ("summary", "text")
            ])
            
            self._connected = True
            logger.info(f"Connected to LTM database: {self._db_name}.{self._collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise DatabaseConnectionError(f"Failed to connect to LTM database: {str(e)}")

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Disconnected from LTM database")

    async def _ensure_connection(self) -> None:
        """Ensure database connection is established before operations."""
        if not self._connected:
            await self.connect()

    async def store_memory(self, memory: Union[LTMMemory, dict[str, Any]]) -> str:
        """
        Store a new memory in the long-term memory database.
        
        Args:
            memory: The memory to store, either as a LTMMemory object or a dictionary.
            
        Returns:
            str: The ID of the stored memory.
            
        Raises:
            MemoryStorageError: If the memory cannot be stored.
            ValidationError: If the memory data is invalid.
        """
        await self._ensure_connection()
        
        try:
            # Convert to LTMMemory if dict provided
            if isinstance(memory, dict):
                memory = LTMMemory(**memory)
            
            # Generate memory_id if not provided
            if not memory.memory_id:
                memory.memory_id = str(uuid.uuid4())
                
            # Set timestamps if not provided
            current_time = get_current_timestamp()
            if not memory.created_at:
                memory.created_at = current_time
            if not memory.last_accessed:
                memory.last_accessed = current_time
                
            # Normalize embedding vector if present
            if memory.embedding:
                memory.embedding = normalize_embedding(memory.embedding)
                
            # Convert to dictionary for storage
            memory_dict = memory.model_dump()
            
            # Store in database
            await self._collection.insert_one(memory_dict)
            logger.info(f"Stored memory with ID: {memory.memory_id}")
            return memory.memory_id
            
        except DuplicateKeyError:
            logger.warning(f"Memory with ID {memory.memory_id} already exists")
            raise MemoryStorageError(f"Memory with ID {memory.memory_id} already exists")
        except ValidationError as e:
            logger.error(f"Invalid memory data: {str(e)}")
            raise ValidationError(f"Invalid memory data: {str(e)}", model=LTMMemory)
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            raise MemoryStorageError(f"Failed to store memory: {str(e)}")

    async def get_memory(self, memory_id: str, update_access_time: bool = True) -> LTMMemory:
        """
        Retrieve a memory by its ID.
        
        Args:
            memory_id: The ID of the memory to retrieve.
            update_access_time: Whether to update the last_accessed timestamp.
            
        Returns:
            LTMMemory: The retrieved memory.
            
        Raises:
            MemoryNotFoundError: If the memory is not found.
        """
        await self._ensure_connection()
        
        try:
            memory_dict = await self._collection.find_one({"memory_id": memory_id})
            
            if not memory_dict:
                logger.warning(f"Memory with ID {memory_id} not found")
                raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                
            # Update last accessed time if requested
            if update_access_time:
                await self._collection.update_one(
                    {"memory_id": memory_id},
                    {"$set": {"last_accessed": get_current_timestamp()}}
                )
                
            # Convert to LTMMemory object
            memory = LTMMemory(**memory_dict)
            logger.debug(f"Retrieved memory with ID: {memory_id}")
            return memory
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving memory {memory_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve memory {memory_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {str(e)}")
            raise RepositoryError(f"Error retrieving memory {memory_id}: {str(e)}")

    async def update_memory(self, memory_id: str, updates: dict[str, Any]) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update.
            updates: Dictionary of fields to update.
            
        Returns:
            bool: True if the update was successful.
            
        Raises:
            MemoryNotFoundError: If the memory is not found.
            MemoryStorageError: If the update fails.
        """
        await self._ensure_connection()
        
        try:
            # Check if memory exists
            exists = await self._collection.find_one({"memory_id": memory_id})
            if not exists:
                logger.warning(f"Memory with ID {memory_id} not found for update")
                raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
                
            # Normalize embedding if present in updates
            if "embedding" in updates and updates["embedding"]:
                updates["embedding"] = normalize_embedding(updates["embedding"])
                
            # Add last_modified timestamp
            updates["last_modified"] = get_current_timestamp()
            
            # Update the memory
            result = await self._collection.update_one(
                {"memory_id": memory_id},
                {"$set": updates}
            )
            
            if result.modified_count == 0:
                logger.warning(f"No changes made to memory {memory_id}")
                
            logger.info(f"Updated memory with ID: {memory_id}")
            return True
            
        except PyMongoError as e:
            logger.error(f"Database error updating memory {memory_id}: {str(e)}")
            raise MemoryStorageError(f"Failed to update memory {memory_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {str(e)}")
            raise MemoryStorageError(f"Error updating memory {memory_id}: {str(e)}")

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from the database.
        
        Args:
            memory_id: The ID of the memory to delete.
            
        Returns:
            bool: True if the memory was deleted, False if it didn't exist.
            
        Raises:
            RepositoryError: If the deletion fails.
        """
        await self._ensure_connection()
        
        try:
            result = await self._collection.delete_one({"memory_id": memory_id})
            
            if result.deleted_count == 0:
                logger.warning(f"Memory with ID {memory_id} not found for deletion")
                return False
                
            logger.info(f"Deleted memory with ID: {memory_id}")
            return True
            
        except PyMongoError as e:
            logger.error(f"Database error deleting memory {memory_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete memory {memory_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {str(e)}")
            raise RepositoryError(f"Error deleting memory {memory_id}: {str(e)}")

    async def search_memories(
        self, 
        query_embedding: Optional[list[float]] = None,
        query_text: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        min_importance: Optional[MemoryImportance] = None,
        time_range: Optional[tuple[datetime.datetime, datetime.datetime]] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> list[tuple[LTMMemory, MemoryRetrievalMetadata]]:
        """
        Search for memories based on various criteria.
        
        Args:
            query_embedding: Vector embedding for similarity search.
            query_text: Text to search for in memory content and metadata.
            memory_type: Filter by memory type.
            tags: Filter by tags.
            min_importance: Minimum importance level.
            time_range: Time range for memory creation (start, end).
            limit: Maximum number of results to return.
            threshold: Minimum similarity threshold for embedding search.
            
        Returns:
            List of tuples containing (memory, metadata) where metadata includes
            similarity score and other retrieval information.
            
        Raises:
            RepositoryError: If the search operation fails.
        """
        await self._ensure_connection()
        
        try:
            # Build query filters
            query_filter = {}
            
            if memory_type:
                query_filter["memory_type"] = memory_type.value
                
            if tags:
                query_filter["tags"] = {"$all": tags}
                
            if min_importance:
                query_filter["importance"] = {"$gte": min_importance.value}
                
            if time_range:
                start_time, end_time = time_range
                query_filter["created_at"] = {
                    "$gte": start_time.timestamp(),
                    "$lte": end_time.timestamp()
                }
                
            # Text search
            if query_text:
                query_filter["$text"] = {"$search": query_text}
                
            # Execute query
            cursor = self._collection.find(query_filter)
            
            # Sort by recency if no embedding search
            if not query_embedding:
                cursor = cursor.sort("created_at", -1)
                
            # Limit results
            cursor = cursor.limit(limit * 3)  # Get more than needed for filtering
            
            # Fetch results
            memories = []
            async for doc in cursor:
                memories.append(LTMMemory(**doc))
                
            # Calculate similarity scores if embedding provided
            if query_embedding:
                normalized_query = normalize_embedding(query_embedding)
                scored_memories = []
                
                for memory in memories:
                    if memory.embedding:
                        similarity = cosine_similarity(normalized_query, memory.embedding)
                        if similarity >= threshold:
                            metadata = MemoryRetrievalMetadata(
                                similarity_score=similarity,
                                retrieval_timestamp=get_current_timestamp(),
                                query_context={"query_embedding": True}
                            )
                            scored_memories.append((memory, metadata))
                
                # Sort by similarity score
                scored_memories.sort(key=lambda x: x[1].similarity_score, reverse=True)
                result = scored_memories[:limit]
            else:
                # For non-embedding searches, create metadata with zero similarity
                result = [
                    (memory, MemoryRetrievalMetadata(
                        similarity_score=0.0,
                        retrieval_timestamp=get_current_timestamp(),
                        query_context={"text_query": query_text is not None}
                    ))
                    for memory in memories[:limit]
                ]
                
            # Update access times for retrieved memories
            memory_ids = [memory.memory_id for memory, _ in result]
            if memory_ids:
                await self._collection.update_many(
                    {"memory_id": {"$in": memory_ids}},
                    {"$set": {"last_accessed": get_current_timestamp()}}
                )
                
            logger.info(f"Search returned {len(result)} memories")
            return result
            
        except PyMongoError as e:
            logger.error(f"Database error during memory search: {str(e)}")
            raise RepositoryError(f"Failed to search memories: {str(e)}")
        except Exception as e:
            logger.error(f"Error during memory search: {str(e)}")
            raise RepositoryError(f"Error searching memories: {str(e)}")

    async def consolidate_memories(
        self, 
        source_memories: list[str], 
        consolidated_memory: LTMMemory
    ) -> str:
        """
        Consolidate multiple memories into a new memory.
        
        This process creates a new consolidated memory and marks the source
        memories as consolidated, linking them to the new memory.
        
        Args:
            source_memories: List of memory IDs to consolidate.
            consolidated_memory: The new consolidated memory.
            
        Returns:
            str: ID of the new consolidated memory.
            
        Raises:
            MemoryStorageError: If consolidation fails.
        """
        await self._ensure_connection()
        
        # Start a transaction
        async with await self._client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Store the consolidated memory
                    if not consolidated_memory.memory_id:
                        consolidated_memory.memory_id = str(uuid.uuid4())
                        
                    # Set source references
                    consolidated_memory.source_memories = source_memories
                    
                    # Store the consolidated memory
                    memory_dict = consolidated_memory.model_dump()
                    await self._collection.insert_one(memory_dict, session=session)
                    
                    # Update source memories to mark as consolidated
                    await self._collection.update_many(
                        {"memory_id": {"$in": source_memories}},
                        {
                            "$set": {
                                "consolidated_into": consolidated_memory.memory_id,
                                "last_modified": get_current_timestamp()
                            }
                        },
                        session=session
                    )
                    
                    logger.info(
                        f"Consolidated {len(source_memories)} memories into {consolidated_memory.memory_id}"
                    )
                    return consolidated_memory.memory_id
                    
                except Exception as e:
                    logger.error(f"Memory consolidation failed: {str(e)}")
                    raise MemoryStorageError(f"Memory consolidation failed: {str(e)}")

    async def get_memories_by_time_range(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> list[LTMMemory]:
        """
        Retrieve memories created within a specific time range.
        
        Args:
            start_time: Start of the time range.
            end_time: End of the time range.
            memory_type: Optional filter by memory type.
            limit: Maximum number of memories to return.
            
        Returns:
            List[LTMMemory]: Memories within the time range.
            
        Raises:
            RepositoryError: If the retrieval fails.
        """
        await self._ensure_connection()
        
        try:
            query_filter = {
                "created_at": {
                    "$gte": start_time.timestamp(),
                    "$lte": end_time.timestamp()
                }
            }
            
            if memory_type:
                query_filter["memory_type"] = memory_type.value
                
            cursor = self._collection.find(query_filter).sort("created_at", -1).limit(limit)
            
            memories = []
            async for doc in cursor:
                memories.append(LTMMemory(**doc))
                
            logger.info(f"Retrieved {len(memories)} memories in time range")
            return memories
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving memories by time range: {str(e)}")
            raise RepositoryError(f"Failed to retrieve memories by time range: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving memories by time range: {str(e)}")
            raise RepositoryError(f"Error retrieving memories by time range: {str(e)}")

    async def get_memories_by_importance(
        self,
        min_importance: MemoryImportance,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50
    ) -> list[LTMMemory]:
        """
        Retrieve memories with importance at or above the specified level.
        
        Args:
            min_importance: Minimum importance level.
            memory_type: Optional filter by memory type.
            limit: Maximum number of memories to return.
            
        Returns:
            List[LTMMemory]: Memories meeting the importance criteria.
            
        Raises:
            RepositoryError: If the retrieval fails.
        """
        await self._ensure_connection()
        
        try:
            query_filter = {"importance": {"$gte": min_importance.value}}
            
            if memory_type:
                query_filter["memory_type"] = memory_type.value
                
            cursor = self._collection.find(query_filter).sort("importance", -1).limit(limit)
            
            memories = []
            async for doc in cursor:
                memories.append(LTMMemory(**doc))
                
            logger.info(f"Retrieved {len(memories)} memories by importance")
            return memories
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving memories by importance: {str(e)}")
            raise RepositoryError(f"Failed to retrieve memories by importance: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving memories by importance: {str(e)}")
            raise RepositoryError(f"Error retrieving memories by importance: {str(e)}")

    async def apply_forgetting_mechanism(
        self,
        older_than_days: int = 90,
        access_threshold_days: int = 30,
        importance_threshold: MemoryImportance = MemoryImportance.MEDIUM,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """
        Apply forgetting mechanism to remove or decay old, unimportant memories.
        
        This implements a biologically-inspired forgetting mechanism that:
        1. Removes very old, unimportant, and rarely accessed memories
        2. Decays the importance of memories that haven't been accessed recently
        
        Args:
            older_than_days: Only consider memories older than this many days
            access_threshold_days: Memories not accessed in this many days are candidates
            importance_threshold: Only memories below this importance are candidates
            dry_run: If True, report what would be done without making changes
            
        Returns:
            Dict with statistics about the operation
            
        Raises:
            RepositoryError: If the operation fails
        """
        await self._ensure_connection()
        
        try:
            now = datetime.datetime.now().timestamp()
            older_than_timestamp = now - (older_than_days * 86400)
            access_threshold_timestamp = now - (access_threshold_days * 86400)
            
            # Find memories to forget (delete)
            forget_query = {
                "created_at": {"$lt": older_than_timestamp},
                "last_accessed": {"$lt": access_threshold_timestamp},
                "importance": {"$lt": importance_threshold.value},
                "consolidated_into": {"$exists": False}  # Don't delete if part of consolidation
            }
            
            # Find memories to decay (reduce importance)
            decay_query = {
                "last_accessed": {"$lt": access_threshold_timestamp},
                "importance": {"$gte": importance_threshold.value},
                "consolidated_into": {"$exists": False}
            }
            
            # Count memories that would be affected
            forget_count = await self._collection.count_documents(forget_query)
            decay_count = await self._collection.count_documents(decay_query)
            
            results = {
                "forget_candidates": forget_count,
                "decay_candidates": decay_count,
                "forgotten": 0,
                "decayed": 0,
                "dry_run": dry_run
            }
            
            if dry_run:
                logger.info(f"Forgetting mechanism dry run: {forget_count} to forget, {decay_count} to decay")
                return results
                
            # Execute forgetting
            if forget_count > 0:
                delete_result = await self._collection.delete_many(forget_query)
                results["forgotten"] = delete_result.deleted_count
                
            # Execute decay (reduce importance by one level)
            if decay_count > 0:
                decay_cursor = self._collection.find(decay_query)
                decayed = 0
                
                async for memory in decay_cursor:
                    current_importance = memory.get("importance", 0)
                    if current_importance > 0:
                        new_importance = max(0, current_importance - 1)
                        update_result = await self._collection.update_one(
                            {"_id": memory["_id"]},
                            {"$set": {"importance": new_importance}}
                        )
                        if update_result.modified_count > 0:
                            decayed += 1
                            
                results["decayed"] = decayed
                
            logger.info(
                f"Forgetting mechanism applied: {results['forgotten']} forgotten, {results['decayed']} decayed"
            )
            return results
            
        except PyMongoError as e:
            logger.error(f"Database error applying forgetting mechanism: {str(e)}")
            raise RepositoryError(f"Failed to apply forgetting mechanism: {str(e)}")
        except Exception as e:
            logger.error(f"Error applying forgetting mechanism: {str(e)}")
            raise RepositoryError(f"Error applying forgetting mechanism: {str(e)}")

    async def get_memory_stats(self) -> dict[str, Any]:
        """
        Get statistics about the memories in the database.
        
        Returns:
            Dict with statistics including:
            - total_count: Total number of memories
            - by_type: Breakdown by memory type
            - by_importance: Breakdown by importance level
            - avg_age_days: Average age of memories in days
            
        Raises:
            RepositoryError: If the operation fails
        """
        await self._ensure_connection()
        
        try:
            # Get total count
            total_count = await self._collection.count_documents({})
            
            # Get counts by memory type
            type_pipeline = [
                {"$group": {"_id": "$memory_type", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            type_cursor = self._collection.aggregate(type_pipeline)
            type_stats = {}
            async for doc in type_cursor:
                type_stats[doc["_id"] or "unknown"] = doc["count"]
                
            # Get counts by importance
            importance_pipeline = [
                {"$group": {"_id": "$importance", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            importance_cursor = self._collection.aggregate(importance_pipeline)
            importance_stats = {}
            async for doc in importance_cursor:
                importance_stats[str(doc["_id"])] = doc["count"]
                
            # Calculate average age
            now = datetime.datetime.now().timestamp()
            age_pipeline = [
                {"$project": {"age": {"$subtract": [now, "$created_at"]}}},
                {"$group": {"_id": None, "avg_age": {"$avg": "$age"}}}
            ]
            age_cursor = self._collection.aggregate(age_pipeline)
            avg_age_seconds = 0
            async for doc in age_cursor:
                avg_age_seconds = doc["avg_age"]
                
            avg_age_days = round(avg_age_seconds / 86400, 2) if avg_age_seconds else 0
            
            stats = {
                "total_count": total_count,
                "by_type": type_stats,
                "by_importance": importance_stats,
                "avg_age_days": avg_age_days,
                "timestamp": get_current_timestamp()
            }
            
            logger.info(f"Retrieved memory stats: {total_count} total memories")
            return stats
            
        except PyMongoError as e:
            logger.error(f"Database error retrieving memory stats: {str(e)}")
            raise RepositoryError(f"Failed to retrieve memory stats: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving memory stats: {str(e)}")
            raise RepositoryError(f"Error retrieving memory stats: {str(e)}")