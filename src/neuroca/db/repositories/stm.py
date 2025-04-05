"""
Short-Term Memory (STM) Repository Module.

This module provides the repository implementation for managing Short-Term Memory (STM)
operations in the NeuroCognitive Architecture. It handles CRUD operations for STM items,
manages memory decay, implements priority-based retrieval, and enforces capacity constraints.

The STM repository serves as the data access layer for the middle tier of the three-tiered
memory system, providing temporary storage with moderate retention duration and capacity.

Usage:
    stm_repo = STMRepository(db_session)
    
    # Store a new memory item
    memory_id = await stm_repo.store(content="New information", priority=0.8)
    
    # Retrieve memory items
    items = await stm_repo.retrieve(limit=5, min_priority=0.5)
    
    # Update memory item
    updated = await stm_repo.update(memory_id, priority=0.9)
    
    # Delete memory item
    deleted = await stm_repo.delete(memory_id)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, delete, desc, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from neuroca.config.settings import get_settings
from neuroca.core.exceptions import (
    InvalidParameterError,
    MemoryCapacityExceededError,
    MemoryItemNotFoundError,
    RepositoryError,
)
from neuroca.core.models.memory import STMItem

# Configure logger
logger = logging.getLogger(__name__)


class STMRepository:
    """
    Repository for Short-Term Memory (STM) operations.
    
    This class handles all database interactions for the STM component,
    including storing, retrieving, updating, and deleting memory items,
    as well as managing memory decay and capacity constraints.
    
    Attributes:
        db_session (AsyncSession): The database session for executing queries
        settings (Settings): Application settings containing STM configuration
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the STM repository with a database session.
        
        Args:
            db_session (AsyncSession): SQLAlchemy async session for database operations
        """
        self.db_session = db_session
        self.settings = get_settings()
        self.max_capacity = self.settings.stm_max_capacity
        self.retention_period = self.settings.stm_retention_period  # in seconds
        
        logger.debug(f"Initialized STMRepository with max_capacity={self.max_capacity}, "
                    f"retention_period={self.retention_period}s")

    async def store(self, 
                   content: str, 
                   priority: float = 0.5, 
                   metadata: Optional[dict[str, Any]] = None,
                   source: Optional[str] = None,
                   context_id: Optional[str] = None) -> str:
        """
        Store a new memory item in the STM.
        
        Args:
            content (str): The content of the memory item
            priority (float, optional): Priority value between 0.0 and 1.0. Defaults to 0.5.
            metadata (Dict[str, Any], optional): Additional metadata for the memory item
            source (str, optional): Source of the memory item
            context_id (str, optional): ID of the context this memory belongs to
            
        Returns:
            str: The ID of the newly created memory item
            
        Raises:
            MemoryCapacityExceededError: If STM capacity is exceeded
            InvalidParameterError: If input parameters are invalid
            RepositoryError: If a database error occurs
        """
        # Validate inputs
        if not content or not isinstance(content, str):
            raise InvalidParameterError("Content must be a non-empty string")
        
        if not 0.0 <= priority <= 1.0:
            raise InvalidParameterError("Priority must be between 0.0 and 1.0")
        
        if metadata is not None and not isinstance(metadata, dict):
            raise InvalidParameterError("Metadata must be a dictionary")
            
        try:
            # Check current capacity
            await self._enforce_capacity_limits()
            
            # Create new STM item
            memory_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(seconds=self.retention_period)
            
            stm_item = STMItem(
                id=memory_id,
                content=content,
                priority=priority,
                metadata=metadata or {},
                source=source,
                context_id=context_id,
                created_at=created_at,
                updated_at=created_at,
                expires_at=expires_at,
                access_count=0,
                last_accessed=created_at
            )
            
            self.db_session.add(stm_item)
            await self.db_session.commit()
            
            logger.info(f"Stored new STM item with ID: {memory_id}")
            logger.debug(f"STM item details: priority={priority}, expires_at={expires_at}")
            
            return memory_id
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while storing STM item: {str(e)}")
            raise RepositoryError(f"Failed to store memory item: {str(e)}")
    
    async def retrieve(self, 
                      limit: int = 10, 
                      min_priority: float = 0.0,
                      context_id: Optional[str] = None,
                      query: Optional[str] = None,
                      update_access_stats: bool = True) -> list[dict[str, Any]]:
        """
        Retrieve memory items from STM based on specified criteria.
        
        Args:
            limit (int, optional): Maximum number of items to retrieve. Defaults to 10.
            min_priority (float, optional): Minimum priority threshold. Defaults to 0.0.
            context_id (str, optional): Filter by context ID
            query (str, optional): Search query to filter content
            update_access_stats (bool, optional): Whether to update access statistics. Defaults to True.
            
        Returns:
            List[Dict[str, Any]]: List of memory items matching the criteria
            
        Raises:
            InvalidParameterError: If input parameters are invalid
            RepositoryError: If a database error occurs
        """
        if limit < 1:
            raise InvalidParameterError("Limit must be a positive integer")
        
        if not 0.0 <= min_priority <= 1.0:
            raise InvalidParameterError("min_priority must be between 0.0 and 1.0")
            
        try:
            # Remove expired items first
            await self._cleanup_expired_items()
            
            # Build query
            current_time = datetime.utcnow()
            query_stmt = select(STMItem).where(
                and_(
                    STMItem.priority >= min_priority,
                    STMItem.expires_at > current_time
                )
            )
            
            # Add context filter if provided
            if context_id:
                query_stmt = query_stmt.where(STMItem.context_id == context_id)
                
            # Add content search if provided
            if query:
                query_stmt = query_stmt.where(STMItem.content.contains(query))
                
            # Order by priority (descending) and last_accessed (descending)
            query_stmt = query_stmt.order_by(
                desc(STMItem.priority),
                desc(STMItem.last_accessed)
            ).limit(limit)
            
            result = await self.db_session.execute(query_stmt)
            items = result.scalars().all()
            
            # Update access statistics if requested
            if update_access_stats and items:
                item_ids = [item.id for item in items]
                await self._update_access_stats(item_ids)
            
            # Convert to dictionaries
            items_list = []
            for item in items:
                item_dict = {
                    "id": item.id,
                    "content": item.content,
                    "priority": item.priority,
                    "metadata": item.metadata,
                    "source": item.source,
                    "context_id": item.context_id,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "expires_at": item.expires_at.isoformat(),
                    "access_count": item.access_count,
                    "last_accessed": item.last_accessed.isoformat()
                }
                items_list.append(item_dict)
            
            logger.info(f"Retrieved {len(items_list)} STM items")
            logger.debug(f"Retrieve parameters: limit={limit}, min_priority={min_priority}, "
                        f"context_id={context_id}, query={query}")
            
            return items_list
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving STM items: {str(e)}")
            raise RepositoryError(f"Failed to retrieve memory items: {str(e)}")
    
    async def update(self, 
                    memory_id: str, 
                    content: Optional[str] = None,
                    priority: Optional[float] = None, 
                    metadata: Optional[dict[str, Any]] = None,
                    extend_expiry: bool = False) -> bool:
        """
        Update an existing STM item.
        
        Args:
            memory_id (str): ID of the memory item to update
            content (str, optional): New content for the memory item
            priority (float, optional): New priority value between 0.0 and 1.0
            metadata (Dict[str, Any], optional): New or updated metadata
            extend_expiry (bool, optional): Whether to reset the expiry time. Defaults to False.
            
        Returns:
            bool: True if the update was successful, False otherwise
            
        Raises:
            MemoryItemNotFoundError: If the memory item is not found
            InvalidParameterError: If input parameters are invalid
            RepositoryError: If a database error occurs
        """
        if not memory_id:
            raise InvalidParameterError("memory_id must be provided")
            
        if priority is not None and not 0.0 <= priority <= 1.0:
            raise InvalidParameterError("Priority must be between 0.0 and 1.0")
            
        if metadata is not None and not isinstance(metadata, dict):
            raise InvalidParameterError("Metadata must be a dictionary")
            
        try:
            # Check if item exists
            result = await self.db_session.execute(
                select(STMItem).where(STMItem.id == memory_id)
            )
            item = result.scalars().first()
            
            if not item:
                logger.warning(f"Attempted to update non-existent STM item with ID: {memory_id}")
                raise MemoryItemNotFoundError(f"Memory item with ID {memory_id} not found")
            
            # Prepare update data
            update_data = {}
            if content is not None:
                update_data["content"] = content
            if priority is not None:
                update_data["priority"] = priority
            if metadata is not None:
                # Merge with existing metadata rather than replacing
                updated_metadata = {**item.metadata, **metadata}
                update_data["metadata"] = updated_metadata
                
            update_data["updated_at"] = datetime.utcnow()
            
            if extend_expiry:
                update_data["expires_at"] = datetime.utcnow() + timedelta(seconds=self.retention_period)
            
            # Execute update
            if update_data:
                await self.db_session.execute(
                    update(STMItem)
                    .where(STMItem.id == memory_id)
                    .values(**update_data)
                )
                await self.db_session.commit()
                
                logger.info(f"Updated STM item with ID: {memory_id}")
                logger.debug(f"Update data: {update_data}")
                
                return True
            
            return False
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while updating STM item: {str(e)}")
            raise RepositoryError(f"Failed to update memory item: {str(e)}")
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from STM.
        
        Args:
            memory_id (str): ID of the memory item to delete
            
        Returns:
            bool: True if the deletion was successful, False if item not found
            
        Raises:
            InvalidParameterError: If memory_id is invalid
            RepositoryError: If a database error occurs
        """
        if not memory_id:
            raise InvalidParameterError("memory_id must be provided")
            
        try:
            result = await self.db_session.execute(
                delete(STMItem).where(STMItem.id == memory_id).returning(STMItem.id)
            )
            deleted_id = result.scalar_one_or_none()
            
            if deleted_id:
                await self.db_session.commit()
                logger.info(f"Deleted STM item with ID: {memory_id}")
                return True
            else:
                logger.warning(f"Attempted to delete non-existent STM item with ID: {memory_id}")
                return False
                
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while deleting STM item: {str(e)}")
            raise RepositoryError(f"Failed to delete memory item: {str(e)}")
    
    async def get_item_count(self) -> int:
        """
        Get the current count of STM items.
        
        Returns:
            int: Number of items currently in STM
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Count only non-expired items
            current_time = datetime.utcnow()
            result = await self.db_session.execute(
                select(func.count()).select_from(STMItem).where(STMItem.expires_at > current_time)
            )
            count = result.scalar_one()
            
            logger.debug(f"Current STM item count: {count}")
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while counting STM items: {str(e)}")
            raise RepositoryError(f"Failed to get item count: {str(e)}")
    
    async def get_by_id(self, memory_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve a specific memory item by ID.
        
        Args:
            memory_id (str): ID of the memory item to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Memory item if found, None otherwise
            
        Raises:
            InvalidParameterError: If memory_id is invalid
            RepositoryError: If a database error occurs
        """
        if not memory_id:
            raise InvalidParameterError("memory_id must be provided")
            
        try:
            result = await self.db_session.execute(
                select(STMItem).where(STMItem.id == memory_id)
            )
            item = result.scalars().first()
            
            if not item:
                logger.debug(f"STM item with ID {memory_id} not found")
                return None
                
            # Update access stats
            await self._update_access_stats([memory_id])
            
            # Convert to dictionary
            item_dict = {
                "id": item.id,
                "content": item.content,
                "priority": item.priority,
                "metadata": item.metadata,
                "source": item.source,
                "context_id": item.context_id,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "expires_at": item.expires_at.isoformat(),
                "access_count": item.access_count + 1,  # Include the current access
                "last_accessed": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Retrieved STM item with ID: {memory_id}")
            return item_dict
            
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving STM item by ID: {str(e)}")
            raise RepositoryError(f"Failed to retrieve memory item: {str(e)}")
    
    async def _cleanup_expired_items(self) -> int:
        """
        Remove expired items from STM.
        
        Returns:
            int: Number of items removed
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            current_time = datetime.utcnow()
            result = await self.db_session.execute(
                delete(STMItem).where(STMItem.expires_at <= current_time).returning(STMItem.id)
            )
            deleted_ids = result.scalars().all()
            
            if deleted_ids:
                await self.db_session.commit()
                logger.info(f"Cleaned up {len(deleted_ids)} expired STM items")
                
            return len(deleted_ids)
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while cleaning up expired STM items: {str(e)}")
            raise RepositoryError(f"Failed to clean up expired items: {str(e)}")
    
    async def _enforce_capacity_limits(self) -> None:
        """
        Enforce STM capacity limits by removing lowest priority items if needed.
        
        Raises:
            MemoryCapacityExceededError: If capacity cannot be enforced
            RepositoryError: If a database error occurs
        """
        try:
            # Get current count
            count = await self.get_item_count()
            
            # If we're at or over capacity, remove lowest priority items
            if count >= self.max_capacity:
                # Calculate how many items to remove (remove at least one)
                items_to_remove = max(1, count - self.max_capacity + 1)
                
                # Get IDs of lowest priority items
                result = await self.db_session.execute(
                    select(STMItem.id)
                    .order_by(STMItem.priority, STMItem.last_accessed)
                    .limit(items_to_remove)
                )
                item_ids = result.scalars().all()
                
                if not item_ids:
                    logger.warning("Failed to identify low-priority items for removal")
                    raise MemoryCapacityExceededError(
                        f"STM capacity exceeded ({count}/{self.max_capacity}) and unable to free space"
                    )
                
                # Delete the identified items
                await self.db_session.execute(
                    delete(STMItem).where(STMItem.id.in_(item_ids))
                )
                await self.db_session.commit()
                
                logger.info(f"Removed {len(item_ids)} low-priority items to enforce STM capacity limits")
                
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while enforcing capacity limits: {str(e)}")
            raise RepositoryError(f"Failed to enforce capacity limits: {str(e)}")
    
    async def _update_access_stats(self, item_ids: list[str]) -> None:
        """
        Update access statistics for the specified items.
        
        Args:
            item_ids (List[str]): List of item IDs to update
            
        Raises:
            RepositoryError: If a database error occurs
        """
        if not item_ids:
            return
            
        try:
            current_time = datetime.utcnow()
            
            # Update access count and last_accessed time
            await self.db_session.execute(
                update(STMItem)
                .where(STMItem.id.in_(item_ids))
                .values(
                    access_count=STMItem.access_count + 1,
                    last_accessed=current_time
                )
            )
            await self.db_session.commit()
            
            logger.debug(f"Updated access stats for {len(item_ids)} STM items")
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while updating access stats: {str(e)}")
            raise RepositoryError(f"Failed to update access statistics: {str(e)}")
    
    async def search(self, 
                    query: str, 
                    limit: int = 10,
                    min_priority: float = 0.0,
                    context_id: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Search for memory items in STM based on content.
        
        Args:
            query (str): Search query to match against content
            limit (int, optional): Maximum number of items to retrieve. Defaults to 10.
            min_priority (float, optional): Minimum priority threshold. Defaults to 0.0.
            context_id (str, optional): Filter by context ID
            
        Returns:
            List[Dict[str, Any]]: List of memory items matching the search criteria
            
        Raises:
            InvalidParameterError: If input parameters are invalid
            RepositoryError: If a database error occurs
        """
        if not query:
            raise InvalidParameterError("Search query must be provided")
            
        # Delegate to retrieve method with query parameter
        return await self.retrieve(
            limit=limit,
            min_priority=min_priority,
            context_id=context_id,
            query=query
        )
    
    async def clear_all(self) -> int:
        """
        Clear all items from STM.
        
        Returns:
            int: Number of items removed
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            result = await self.db_session.execute(
                delete(STMItem).returning(STMItem.id)
            )
            deleted_ids = result.scalars().all()
            
            if deleted_ids:
                await self.db_session.commit()
                logger.warning(f"Cleared all STM items ({len(deleted_ids)} items removed)")
                
            return len(deleted_ids)
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while clearing STM: {str(e)}")
            raise RepositoryError(f"Failed to clear STM: {str(e)}")
    
    async def adjust_priority(self, memory_id: str, adjustment: float) -> float:
        """
        Adjust the priority of a memory item by the specified amount.
        
        Args:
            memory_id (str): ID of the memory item
            adjustment (float): Amount to adjust priority by (positive or negative)
            
        Returns:
            float: New priority value after adjustment
            
        Raises:
            MemoryItemNotFoundError: If the memory item is not found
            InvalidParameterError: If input parameters are invalid
            RepositoryError: If a database error occurs
        """
        if not memory_id:
            raise InvalidParameterError("memory_id must be provided")
            
        try:
            # Get current item
            result = await self.db_session.execute(
                select(STMItem).where(STMItem.id == memory_id)
            )
            item = result.scalars().first()
            
            if not item:
                logger.warning(f"Attempted to adjust priority of non-existent STM item: {memory_id}")
                raise MemoryItemNotFoundError(f"Memory item with ID {memory_id} not found")
            
            # Calculate new priority, ensuring it stays within bounds
            new_priority = max(0.0, min(1.0, item.priority + adjustment))
            
            # Update the item
            await self.db_session.execute(
                update(STMItem)
                .where(STMItem.id == memory_id)
                .values(
                    priority=new_priority,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db_session.commit()
            
            logger.info(f"Adjusted priority of STM item {memory_id} by {adjustment} to {new_priority}")
            return new_priority
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while adjusting priority: {str(e)}")
            raise RepositoryError(f"Failed to adjust priority: {str(e)}")
    
    async def extend_expiry(self, memory_id: str, seconds: Optional[int] = None) -> datetime:
        """
        Extend the expiry time of a memory item.
        
        Args:
            memory_id (str): ID of the memory item
            seconds (int, optional): Number of seconds to extend by. If None, uses default retention period.
            
        Returns:
            datetime: New expiry time
            
        Raises:
            MemoryItemNotFoundError: If the memory item is not found
            InvalidParameterError: If input parameters are invalid
            RepositoryError: If a database error occurs
        """
        if not memory_id:
            raise InvalidParameterError("memory_id must be provided")
            
        if seconds is not None and seconds <= 0:
            raise InvalidParameterError("Extension seconds must be positive")
            
        extension_seconds = seconds if seconds is not None else self.retention_period
            
        try:
            # Get current item
            result = await self.db_session.execute(
                select(STMItem).where(STMItem.id == memory_id)
            )
            item = result.scalars().first()
            
            if not item:
                logger.warning(f"Attempted to extend expiry of non-existent STM item: {memory_id}")
                raise MemoryItemNotFoundError(f"Memory item with ID {memory_id} not found")
            
            # Calculate new expiry time
            current_time = datetime.utcnow()
            new_expiry = current_time + timedelta(seconds=extension_seconds)
            
            # Update the item
            await self.db_session.execute(
                update(STMItem)
                .where(STMItem.id == memory_id)
                .values(
                    expires_at=new_expiry,
                    updated_at=current_time
                )
            )
            await self.db_session.commit()
            
            logger.info(f"Extended expiry of STM item {memory_id} to {new_expiry}")
            return new_expiry
            
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(f"Database error while extending expiry: {str(e)}")
            raise RepositoryError(f"Failed to extend expiry: {str(e)}")