"""
Long-Term Memory (LTM) Operations Module.

This module provides a comprehensive set of operations for interacting with the Long-Term Memory
component of the NeuroCognitive Architecture. It includes functions for storing, retrieving,
updating, and managing memory entries in the LTM system.

The LTM operations are designed to support persistent storage of information with semantic
organization, associative retrieval, and memory consolidation processes that mimic human
long-term memory characteristics.

Usage:
    from neuroca.memory.ltm.operations import store_memory, retrieve_memory
    
    # Store a new memory
    memory_id = store_memory(content="Important fact about neural networks", 
                            metadata={"source": "research paper", "importance": 0.8})
    
    # Retrieve a memory by ID
    memory = retrieve_memory(memory_id)
    
    # Search memories by semantic query
    relevant_memories = search_memories("neural network architecture")

Note:
    All operations include proper error handling, validation, and logging to ensure
    robust performance in production environments.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from neuroca.core.exceptions import (
    InvalidMemoryError,
    MemoryNotFoundError,
    MemoryOperationError,
    MemoryStorageError,
)
from neuroca.memory.ltm.models import LTMEntry, MemoryAssociation, MemoryMetadata
from neuroca.memory.ltm.schema import validate_ltm_entry
from neuroca.memory.ltm.storage import LTMStorage
from neuroca.memory.ltm.vector_store import VectorStore
from neuroca.monitoring.metrics import track_operation_time, update_memory_metrics

# Configure logger for LTM operations
logger = logging.getLogger(__name__)


@track_operation_time("ltm_store")
def store_memory(
    content: str,
    metadata: Optional[dict[str, Any]] = None,
    associations: Optional[list[str]] = None,
    importance: float = 0.5,
    encoding_timestamp: Optional[datetime] = None,
    ttl: Optional[int] = None,
) -> str:
    """
    Store a new memory entry in the Long-Term Memory system.
    
    This function creates a new memory entry with the provided content and metadata,
    generates embeddings for semantic search, and stores it in the LTM storage system.
    
    Args:
        content: The main content of the memory to store
        metadata: Optional dictionary of additional metadata for the memory
        associations: Optional list of memory IDs to associate with this memory
        importance: Importance score (0.0 to 1.0) affecting memory retention
        encoding_timestamp: Optional timestamp for when the memory was encoded
                           (defaults to current time if not provided)
        ttl: Optional time-to-live in seconds (None means no expiration)
    
    Returns:
        str: The unique ID of the stored memory
        
    Raises:
        InvalidMemoryError: If the memory content or metadata is invalid
        MemoryStorageError: If there's an error storing the memory
        MemoryOperationError: For other operational errors
        
    Example:
        >>> memory_id = store_memory(
        ...     content="The transformer architecture was introduced in the paper 'Attention is All You Need'",
        ...     metadata={"source": "research_paper", "year": 2017},
        ...     importance=0.8
        ... )
        >>> print(f"Stored memory with ID: {memory_id}")
    """
    try:
        # Input validation
        if not content or not isinstance(content, str):
            raise InvalidMemoryError("Memory content must be a non-empty string")
        
        if importance < 0.0 or importance > 1.0:
            raise InvalidMemoryError("Importance must be between 0.0 and 1.0")
            
        # Generate a unique ID for the memory
        memory_id = str(uuid.uuid4())
        
        # Set encoding timestamp if not provided
        if encoding_timestamp is None:
            encoding_timestamp = datetime.utcnow()
            
        # Prepare metadata object
        memory_metadata = MemoryMetadata(
            created_at=encoding_timestamp,
            last_accessed=encoding_timestamp,
            importance=importance,
            access_count=0,
            ttl=ttl,
            custom=metadata or {},
        )
        
        # Create memory entry
        memory_entry = LTMEntry(
            id=memory_id,
            content=content,
            metadata=memory_metadata,
            associations=associations or [],
        )
        
        # Validate the memory entry against schema
        validate_ltm_entry(memory_entry)
        
        # Get storage instance
        storage = LTMStorage()
        vector_store = VectorStore()
        
        # Generate embedding for the content
        embedding = vector_store.generate_embedding(content)
        
        # Store the memory entry and its embedding
        storage.store(memory_entry)
        vector_store.store_embedding(memory_id, embedding)
        
        # Create associations if provided
        if associations:
            for associated_id in associations:
                create_association(memory_id, associated_id)
        
        # Update metrics
        update_memory_metrics("ltm", "store")
        
        logger.info(f"Successfully stored memory with ID: {memory_id}")
        return memory_id
        
    except InvalidMemoryError as e:
        logger.error(f"Invalid memory data: {str(e)}")
        raise
    except Exception as e:
        logger.exception(f"Failed to store memory: {str(e)}")
        raise MemoryStorageError(f"Failed to store memory: {str(e)}") from e


@track_operation_time("ltm_retrieve")
def retrieve_memory(memory_id: str) -> LTMEntry:
    """
    Retrieve a specific memory entry by its ID.
    
    This function fetches a memory entry from the LTM storage system and updates
    its access metadata (last accessed time, access count).
    
    Args:
        memory_id: The unique identifier of the memory to retrieve
        
    Returns:
        LTMEntry: The retrieved memory entry
        
    Raises:
        MemoryNotFoundError: If no memory with the given ID exists
        MemoryOperationError: For other operational errors
        
    Example:
        >>> try:
        ...     memory = retrieve_memory("550e8400-e29b-41d4-a716-446655440000")
        ...     print(f"Retrieved memory: {memory.content}")
        ... except MemoryNotFoundError:
        ...     print("Memory not found")
    """
    try:
        logger.debug(f"Retrieving memory with ID: {memory_id}")
        
        # Input validation
        if not memory_id or not isinstance(memory_id, str):
            raise InvalidMemoryError("Memory ID must be a non-empty string")
        
        # Get storage instance
        storage = LTMStorage()
        
        # Retrieve the memory
        memory = storage.retrieve(memory_id)
        
        if not memory:
            logger.warning(f"Memory with ID {memory_id} not found")
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
        
        # Update access metadata
        memory.metadata.last_accessed = datetime.utcnow()
        memory.metadata.access_count += 1
        
        # Save the updated metadata
        storage.update(memory)
        
        # Update metrics
        update_memory_metrics("ltm", "retrieve")
        
        logger.info(f"Successfully retrieved memory with ID: {memory_id}")
        return memory
        
    except MemoryNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve memory {memory_id}: {str(e)}")
        raise MemoryOperationError(f"Failed to retrieve memory: {str(e)}") from e


@track_operation_time("ltm_update")
def update_memory(
    memory_id: str,
    content: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    importance: Optional[float] = None,
) -> LTMEntry:
    """
    Update an existing memory entry in the LTM system.
    
    This function updates the content and/or metadata of an existing memory entry.
    If the content is updated, the embedding is regenerated for semantic search.
    
    Args:
        memory_id: The unique identifier of the memory to update
        content: Optional new content for the memory
        metadata: Optional new or updated metadata fields
        importance: Optional new importance score (0.0 to 1.0)
        
    Returns:
        LTMEntry: The updated memory entry
        
    Raises:
        MemoryNotFoundError: If no memory with the given ID exists
        InvalidMemoryError: If the updated content or metadata is invalid
        MemoryOperationError: For other operational errors
        
    Example:
        >>> try:
        ...     updated_memory = update_memory(
        ...         "550e8400-e29b-41d4-a716-446655440000",
        ...         content="Updated information about transformers",
        ...         importance=0.9
        ...     )
        ...     print(f"Updated memory: {updated_memory.content}")
        ... except MemoryNotFoundError:
        ...     print("Memory not found")
    """
    try:
        logger.debug(f"Updating memory with ID: {memory_id}")
        
        # Input validation
        if not memory_id or not isinstance(memory_id, str):
            raise InvalidMemoryError("Memory ID must be a non-empty string")
            
        if importance is not None and (importance < 0.0 or importance > 1.0):
            raise InvalidMemoryError("Importance must be between 0.0 and 1.0")
        
        # Get storage instance
        storage = LTMStorage()
        vector_store = VectorStore()
        
        # Retrieve the existing memory
        memory = storage.retrieve(memory_id)
        
        if not memory:
            logger.warning(f"Memory with ID {memory_id} not found for update")
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
        
        # Update content if provided
        content_updated = False
        if content is not None:
            if not isinstance(content, str) or not content:
                raise InvalidMemoryError("Memory content must be a non-empty string")
            memory.content = content
            content_updated = True
        
        # Update importance if provided
        if importance is not None:
            memory.metadata.importance = importance
        
        # Update custom metadata if provided
        if metadata is not None:
            # Merge new metadata with existing metadata
            for key, value in metadata.items():
                memory.metadata.custom[key] = value
        
        # Update modification timestamp
        memory.metadata.last_modified = datetime.utcnow()
        
        # Validate the updated memory entry
        validate_ltm_entry(memory)
        
        # If content was updated, regenerate the embedding
        if content_updated:
            embedding = vector_store.generate_embedding(memory.content)
            vector_store.update_embedding(memory_id, embedding)
        
        # Store the updated memory
        storage.update(memory)
        
        # Update metrics
        update_memory_metrics("ltm", "update")
        
        logger.info(f"Successfully updated memory with ID: {memory_id}")
        return memory
        
    except (MemoryNotFoundError, InvalidMemoryError):
        raise
    except Exception as e:
        logger.exception(f"Failed to update memory {memory_id}: {str(e)}")
        raise MemoryOperationError(f"Failed to update memory: {str(e)}") from e


@track_operation_time("ltm_delete")
def delete_memory(memory_id: str) -> bool:
    """
    Delete a memory entry from the LTM system.
    
    This function removes a memory entry and its associated embeddings from storage.
    
    Args:
        memory_id: The unique identifier of the memory to delete
        
    Returns:
        bool: True if the memory was successfully deleted
        
    Raises:
        MemoryNotFoundError: If no memory with the given ID exists
        MemoryOperationError: For other operational errors
        
    Example:
        >>> try:
        ...     success = delete_memory("550e8400-e29b-41d4-a716-446655440000")
        ...     if success:
        ...         print("Memory successfully deleted")
        ... except MemoryNotFoundError:
        ...     print("Memory not found")
    """
    try:
        logger.debug(f"Deleting memory with ID: {memory_id}")
        
        # Input validation
        if not memory_id or not isinstance(memory_id, str):
            raise InvalidMemoryError("Memory ID must be a non-empty string")
        
        # Get storage instance
        storage = LTMStorage()
        vector_store = VectorStore()
        
        # Check if memory exists
        memory = storage.retrieve(memory_id)
        if not memory:
            logger.warning(f"Memory with ID {memory_id} not found for deletion")
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
        
        # Delete associations
        delete_all_associations(memory_id)
        
        # Delete the memory and its embedding
        storage.delete(memory_id)
        vector_store.delete_embedding(memory_id)
        
        # Update metrics
        update_memory_metrics("ltm", "delete")
        
        logger.info(f"Successfully deleted memory with ID: {memory_id}")
        return True
        
    except MemoryNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete memory {memory_id}: {str(e)}")
        raise MemoryOperationError(f"Failed to delete memory: {str(e)}") from e


@track_operation_time("ltm_search")
def search_memories(
    query: str,
    limit: int = 10,
    threshold: float = 0.7,
    metadata_filters: Optional[dict[str, Any]] = None,
) -> list[tuple[LTMEntry, float]]:
    """
    Search for memories semantically related to the query.
    
    This function performs a semantic search using vector embeddings to find
    memories that are conceptually related to the query, regardless of exact
    keyword matches.
    
    Args:
        query: The search query text
        limit: Maximum number of results to return (default: 10)
        threshold: Minimum similarity score threshold (0.0 to 1.0)
        metadata_filters: Optional filters to apply to memory metadata
        
    Returns:
        List[Tuple[LTMEntry, float]]: List of tuples containing memory entries and their
                                     similarity scores, sorted by relevance
        
    Raises:
        InvalidMemoryError: If the query is invalid
        MemoryOperationError: For operational errors
        
    Example:
        >>> results = search_memories(
        ...     "How do transformers handle attention?",
        ...     limit=5,
        ...     metadata_filters={"source": "research_paper"}
        ... )
        >>> for memory, score in results:
        ...     print(f"Score: {score:.2f} - {memory.content[:50]}...")
    """
    try:
        logger.debug(f"Searching memories with query: {query}")
        
        # Input validation
        if not query or not isinstance(query, str):
            raise InvalidMemoryError("Search query must be a non-empty string")
            
        if threshold < 0.0 or threshold > 1.0:
            raise InvalidMemoryError("Threshold must be between 0.0 and 1.0")
            
        if limit < 1:
            raise InvalidMemoryError("Limit must be a positive integer")
        
        # Get storage instances
        storage = LTMStorage()
        vector_store = VectorStore()
        
        # Generate embedding for the query
        query_embedding = vector_store.generate_embedding(query)
        
        # Search for similar embeddings
        similar_ids = vector_store.search_similar(
            query_embedding, limit=limit * 2, threshold=threshold
        )
        
        # Retrieve the actual memory entries
        results = []
        for memory_id, score in similar_ids:
            memory = storage.retrieve(memory_id)
            if memory:
                # Apply metadata filters if provided
                if metadata_filters and not _matches_metadata_filters(memory, metadata_filters):
                    continue
                
                # Update access metadata
                memory.metadata.last_accessed = datetime.utcnow()
                memory.metadata.access_count += 1
                storage.update(memory)
                
                results.append((memory, score))
                
                # Break if we have enough results after filtering
                if len(results) >= limit:
                    break
        
        # Update metrics
        update_memory_metrics("ltm", "search")
        
        logger.info(f"Search completed with {len(results)} results for query: {query}")
        return results
        
    except InvalidMemoryError:
        raise
    except Exception as e:
        logger.exception(f"Failed to search memories: {str(e)}")
        raise MemoryOperationError(f"Failed to search memories: {str(e)}") from e


@track_operation_time("ltm_create_association")
def create_association(source_id: str, target_id: str, strength: float = 0.5) -> MemoryAssociation:
    """
    Create an association between two memory entries.
    
    This function establishes a bidirectional link between two memory entries,
    allowing for associative retrieval.
    
    Args:
        source_id: ID of the source memory
        target_id: ID of the target memory
        strength: Association strength (0.0 to 1.0)
        
    Returns:
        MemoryAssociation: The created association object
        
    Raises:
        MemoryNotFoundError: If either memory ID doesn't exist
        InvalidMemoryError: If the parameters are invalid
        MemoryOperationError: For other operational errors
        
    Example:
        >>> association = create_association(
        ...     "550e8400-e29b-41d4-a716-446655440000",
        ...     "661f9511-f3ab-52e5-b827-557766551111",
        ...     strength=0.8
        ... )
        >>> print(f"Created association with strength: {association.strength}")
    """
    try:
        logger.debug(f"Creating association between {source_id} and {target_id}")
        
        # Input validation
        if not source_id or not isinstance(source_id, str):
            raise InvalidMemoryError("Source ID must be a non-empty string")
            
        if not target_id or not isinstance(target_id, str):
            raise InvalidMemoryError("Target ID must be a non-empty string")
            
        if source_id == target_id:
            raise InvalidMemoryError("Cannot create association between a memory and itself")
            
        if strength < 0.0 or strength > 1.0:
            raise InvalidMemoryError("Association strength must be between 0.0 and 1.0")
        
        # Get storage instance
        storage = LTMStorage()
        
        # Verify both memories exist
        source_memory = storage.retrieve(source_id)
        if not source_memory:
            raise MemoryNotFoundError(f"Source memory with ID {source_id} not found")
            
        target_memory = storage.retrieve(target_id)
        if not target_memory:
            raise MemoryNotFoundError(f"Target memory with ID {target_id} not found")
        
        # Create association object
        association = MemoryAssociation(
            source_id=source_id,
            target_id=target_id,
            strength=strength,
            created_at=datetime.utcnow(),
        )
        
        # Store the association
        storage.store_association(association)
        
        # Update the memory entries to include the association
        if target_id not in source_memory.associations:
            source_memory.associations.append(target_id)
            storage.update(source_memory)
            
        if source_id not in target_memory.associations:
            target_memory.associations.append(source_id)
            storage.update(target_memory)
        
        # Update metrics
        update_memory_metrics("ltm", "create_association")
        
        logger.info(f"Successfully created association between {source_id} and {target_id}")
        return association
        
    except (MemoryNotFoundError, InvalidMemoryError):
        raise
    except Exception as e:
        logger.exception(f"Failed to create association: {str(e)}")
        raise MemoryOperationError(f"Failed to create association: {str(e)}") from e


@track_operation_time("ltm_get_associations")
def get_associations(memory_id: str) -> list[tuple[LTMEntry, float]]:
    """
    Retrieve all memories associated with the given memory ID.
    
    This function returns all memories that have an association with the specified
    memory, along with their association strengths.
    
    Args:
        memory_id: ID of the memory to get associations for
        
    Returns:
        List[Tuple[LTMEntry, float]]: List of tuples containing associated memory entries
                                     and their association strengths
        
    Raises:
        MemoryNotFoundError: If the memory ID doesn't exist
        MemoryOperationError: For other operational errors
        
    Example:
        >>> associations = get_associations("550e8400-e29b-41d4-a716-446655440000")
        >>> for memory, strength in associations:
        ...     print(f"Association strength: {strength:.2f} - {memory.content[:50]}...")
    """
    try:
        logger.debug(f"Getting associations for memory ID: {memory_id}")
        
        # Input validation
        if not memory_id or not isinstance(memory_id, str):
            raise InvalidMemoryError("Memory ID must be a non-empty string")
        
        # Get storage instance
        storage = LTMStorage()
        
        # Verify memory exists
        memory = storage.retrieve(memory_id)
        if not memory:
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
        
        # Get all associations for this memory
        associations = storage.get_associations(memory_id)
        
        # Retrieve the associated memories
        results = []
        for association in associations:
            associated_id = (
                association.target_id if association.source_id == memory_id else association.source_id
            )
            associated_memory = storage.retrieve(associated_id)
            
            if associated_memory:
                results.append((associated_memory, association.strength))
        
        # Update metrics
        update_memory_metrics("ltm", "get_associations")
        
        logger.info(f"Retrieved {len(results)} associations for memory ID: {memory_id}")
        return results
        
    except MemoryNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Failed to get associations for {memory_id}: {str(e)}")
        raise MemoryOperationError(f"Failed to get associations: {str(e)}") from e


@track_operation_time("ltm_delete_association")
def delete_association(source_id: str, target_id: str) -> bool:
    """
    Delete an association between two memory entries.
    
    This function removes the bidirectional link between two memory entries.
    
    Args:
        source_id: ID of the source memory
        target_id: ID of the target memory
        
    Returns:
        bool: True if the association was successfully deleted
        
    Raises:
        MemoryNotFoundError: If either memory ID doesn't exist
        MemoryOperationError: For other operational errors
        
    Example:
        >>> success = delete_association(
        ...     "550e8400-e29b-41d4-a716-446655440000",
        ...     "661f9511-f3ab-52e5-b827-557766551111"
        ... )
        >>> if success:
        ...     print("Association successfully deleted")
    """
    try:
        logger.debug(f"Deleting association between {source_id} and {target_id}")
        
        # Input validation
        if not source_id or not isinstance(source_id, str):
            raise InvalidMemoryError("Source ID must be a non-empty string")
            
        if not target_id or not isinstance(target_id, str):
            raise InvalidMemoryError("Target ID must be a non-empty string")
        
        # Get storage instance
        storage = LTMStorage()
        
        # Verify both memories exist
        source_memory = storage.retrieve(source_id)
        if not source_memory:
            raise MemoryNotFoundError(f"Source memory with ID {source_id} not found")
            
        target_memory = storage.retrieve(target_id)
        if not target_memory:
            raise MemoryNotFoundError(f"Target memory with ID {target_id} not found")
        
        # Delete the association
        storage.delete_association(source_id, target_id)
        
        # Update the memory entries to remove the association
        if target_id in source_memory.associations:
            source_memory.associations.remove(target_id)
            storage.update(source_memory)
            
        if source_id in target_memory.associations:
            target_memory.associations.remove(source_id)
            storage.update(target_memory)
        
        # Update metrics
        update_memory_metrics("ltm", "delete_association")
        
        logger.info(f"Successfully deleted association between {source_id} and {target_id}")
        return True
        
    except (MemoryNotFoundError, InvalidMemoryError):
        raise
    except Exception as e:
        logger.exception(f"Failed to delete association: {str(e)}")
        raise MemoryOperationError(f"Failed to delete association: {str(e)}") from e


def delete_all_associations(memory_id: str) -> int:
    """
    Delete all associations for a given memory.
    
    This function removes all associations where the specified memory is either
    the source or target.
    
    Args:
        memory_id: ID of the memory to remove all associations for
        
    Returns:
        int: Number of associations deleted
        
    Raises:
        MemoryNotFoundError: If the memory ID doesn't exist
        MemoryOperationError: For other operational errors
    """
    try:
        logger.debug(f"Deleting all associations for memory ID: {memory_id}")
        
        # Input validation
        if not memory_id or not isinstance(memory_id, str):
            raise InvalidMemoryError("Memory ID must be a non-empty string")
        
        # Get storage instance
        storage = LTMStorage()
        
        # Verify memory exists
        memory = storage.retrieve(memory_id)
        if not memory:
            raise MemoryNotFoundError(f"Memory with ID {memory_id} not found")
        
        # Get all associations for this memory
        associations = storage.get_associations(memory_id)
        
        # Delete each association and update the associated memories
        count = 0
        for association in associations:
            associated_id = (
                association.target_id if association.source_id == memory_id else association.source_id
            )
            
            # Delete the association
            storage.delete_association(association.source_id, association.target_id)
            
            # Update the associated memory
            associated_memory = storage.retrieve(associated_id)
            if associated_memory and memory_id in associated_memory.associations:
                associated_memory.associations.remove(memory_id)
                storage.update(associated_memory)
            
            count += 1
        
        # Clear the associations list for this memory
        memory.associations = []
        storage.update(memory)
        
        logger.info(f"Deleted {count} associations for memory ID: {memory_id}")
        return count
        
    except (MemoryNotFoundError, InvalidMemoryError):
        raise
    except Exception as e:
        logger.exception(f"Failed to delete all associations for {memory_id}: {str(e)}")
        raise MemoryOperationError(f"Failed to delete all associations: {str(e)}") from e


@track_operation_time("ltm_consolidate")
def consolidate_memories(
    threshold_days: int = 7,
    importance_threshold: float = 0.3,
    max_memories: int = 100,
) -> int:
    """
    Consolidate memories based on age, importance, and access patterns.
    
    This function implements a memory consolidation process that mimics human memory
    consolidation during sleep. It identifies memories that are candidates for
    strengthening, weakening, or pruning based on various factors.
    
    Args:
        threshold_days: Age threshold in days for consolidation
        importance_threshold: Minimum importance score for retention
        max_memories: Maximum number of memories to process in one consolidation
        
    Returns:
        int: Number of memories processed
        
    Raises:
        MemoryOperationError: For operational errors
        
    Example:
        >>> processed_count = consolidate_memories(
        ...     threshold_days=14,
        ...     importance_threshold=0.2,
        ...     max_memories=200
        ... )
        >>> print(f"Consolidated {processed_count} memories")
    """
    try:
        logger.info(f"Starting memory consolidation process with threshold of {threshold_days} days")
        
        # Input validation
        if threshold_days < 0:
            raise InvalidMemoryError("Threshold days must be non-negative")
            
        if importance_threshold < 0.0 or importance_threshold > 1.0:
            raise InvalidMemoryError("Importance threshold must be between 0.0 and 1.0")
            
        if max_memories < 1:
            raise InvalidMemoryError("Max memories must be positive")
        
        # Get storage instance
        storage = LTMStorage()
        
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - datetime.timedelta(days=threshold_days)
        
        # Get memories older than the threshold
        old_memories = storage.get_memories_before_date(cutoff_date, limit=max_memories)
        
        processed_count = 0
        strengthened_count = 0
        weakened_count = 0
        pruned_count = 0
        
        for memory in old_memories:
            # Skip memories with TTL set (they have their own expiration logic)
            if memory.metadata.ttl is not None:
                continue
                
            # Calculate a consolidation score based on importance, access count, and age
            age_factor = (datetime.utcnow() - memory.metadata.created_at).days / threshold_days
            access_factor = min(1.0, memory.metadata.access_count / 10.0)  # Cap at 10 accesses
            
            # More important memories and frequently accessed ones should be strengthened
            consolidation_score = (
                memory.metadata.importance * 0.5 +
                access_factor * 0.3 +
                (1.0 - age_factor) * 0.2
            )
            
            # Decide what to do with the memory
            if consolidation_score > 0.7:
                # Strengthen important memories
                memory.metadata.importance = min(1.0, memory.metadata.importance * 1.1)
                strengthened_count += 1
            elif consolidation_score < 0.3:
                # Weaken or prune unimportant memories
                if memory.metadata.importance < importance_threshold:
                    # Prune very unimportant memories
                    storage.delete(memory.id)
                    pruned_count += 1
                else:
                    # Weaken somewhat unimportant memories
                    memory.metadata.importance *= 0.9
                    weakened_count += 1
            
            # Update the memory if not pruned
            if consolidation_score >= 0.3:
                memory.metadata.last_consolidated = datetime.utcnow()
                storage.update(memory)
            
            processed_count += 1
        
        # Update metrics
        update_memory_metrics("ltm", "consolidate")
        
        logger.info(
            f"Consolidation complete: processed {processed_count} memories "
            f"(strengthened: {strengthened_count}, weakened: {weakened_count}, pruned: {pruned_count})"
        )
        return processed_count
        
    except Exception as e:
        logger.exception(f"Failed to consolidate memories: {str(e)}")
        raise MemoryOperationError(f"Failed to consolidate memories: {str(e)}") from e


def _matches_metadata_filters(memory: LTMEntry, filters: dict[str, Any]) -> bool:
    """
    Check if a memory entry matches the given metadata filters.
    
    Args:
        memory: The memory entry to check
        filters: Dictionary of metadata filters to apply
        
    Returns:
        bool: True if the memory matches all filters, False otherwise
    """
    for key, value in filters.items():
        # Handle special metadata fields
        if key == "importance":
            if memory.metadata.importance < value:
                return False
        elif key == "min_access_count":
            if memory.metadata.access_count < value:
                return False
        elif key == "max_age_days":
            age_days = (datetime.utcnow() - memory.metadata.created_at).days
            if age_days > value:
                return False
        # Handle custom metadata fields
        elif key not in memory.metadata.custom or memory.metadata.custom[key] != value:
            return False
    
    return True


def cleanup_expired_memories() -> int:
    """
    Remove memories that have expired based on their TTL.
    
    Returns:
        int: Number of expired memories removed
        
    Raises:
        MemoryOperationError: For operational errors
    """
    try:
        logger.info("Starting cleanup of expired memories")
        
        # Get storage instance
        storage = LTMStorage()
        vector_store = VectorStore()
        
        # Get all memories with TTL
        memories_with_ttl = storage.get_memories_with_ttl()
        
        current_time = datetime.utcnow()
        expired_count = 0
        
        for memory in memories_with_ttl:
            # Skip memories without TTL
            if memory.metadata.ttl is None:
                continue
                
            # Calculate expiration time
            expiration_time = memory.metadata.created_at + datetime.timedelta(seconds=memory.metadata.ttl)
            
            # Check if memory has expired
            if current_time > expiration_time:
                # Delete associations first
                delete_all_associations(memory.id)
                
                # Delete the memory and its embedding
                storage.delete(memory.id)
                vector_store.delete_embedding(memory.id)
                
                expired_count += 1
        
        logger.info(f"Cleanup complete: removed {expired_count} expired memories")
        return expired_count
        
    except Exception as e:
        logger.exception(f"Failed to cleanup expired memories: {str(e)}")
        raise MemoryOperationError(f"Failed to cleanup expired memories: {str(e)}") from e