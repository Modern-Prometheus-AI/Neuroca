"""
Redis Indexing Component

This module provides the RedisIndexing class for managing Redis indices for memory items.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from neuroca.memory.backends.redis.components.connection import RedisConnection
from neuroca.memory.backends.redis.components.utils import RedisUtils
from neuroca.memory.exceptions import StorageOperationError

logger = logging.getLogger(__name__)


class RedisIndexing:
    """
    Manages Redis indices for memory items.
    
    This class handles creating and updating indices for content and metadata,
    enabling efficient search and filtering of memory items.
    """
    
    def __init__(self, connection: RedisConnection, utils: RedisUtils):
        """
        Initialize the Redis indexing component.
        
        Args:
            connection: Redis connection component
            utils: Redis utilities
        """
        self.connection = connection
        self.utils = utils
    
    async def index_content(self, memory_id: str, content: str) -> None:
        """
        Index memory content for search.
        
        Args:
            memory_id: Memory ID
            content: Memory content
            
        Raises:
            StorageOperationError: If indexing fails
        """
        try:
            # Tokenize content
            words = self.utils.tokenize_content(content)
            
            # Add each word to the index
            async with await self.connection.pipeline() as pipe:
                for word in words:
                    word_key = self.utils.create_content_index_key(word)
                    await pipe.sadd(word_key, memory_id)
                
                # Execute pipeline
                await pipe.execute()
            
            logger.debug(f"Indexed content for memory {memory_id} with {len(words)} words")
        except Exception as e:
            error_msg = f"Failed to index content for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update_content_index(self, memory_id: str, old_content: Optional[str], new_content: str) -> None:
        """
        Update content index for a memory item.
        
        Args:
            memory_id: Memory ID
            old_content: Old content (for removing old indices)
            new_content: New content
            
        Raises:
            StorageOperationError: If update fails
        """
        try:
            # Tokenize old and new content
            old_words = self.utils.tokenize_content(old_content) if old_content else set()
            new_words = self.utils.tokenize_content(new_content)
            
            # Find words to add and remove
            words_to_remove = old_words - new_words
            words_to_add = new_words - old_words
            
            # Update indices
            async with await self.connection.pipeline() as pipe:
                # Remove from old indices
                for word in words_to_remove:
                    word_key = self.utils.create_content_index_key(word)
                    await pipe.srem(word_key, memory_id)
                
                # Add to new indices
                for word in words_to_add:
                    word_key = self.utils.create_content_index_key(word)
                    await pipe.sadd(word_key, memory_id)
                
                # Execute pipeline
                await pipe.execute()
            
            logger.debug(f"Updated content index for memory {memory_id}")
        except Exception as e:
            error_msg = f"Failed to update content index for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def remove_content_index(self, memory_id: str, content: Optional[str]) -> None:
        """
        Remove content indices for a memory item.
        
        Args:
            memory_id: Memory ID
            content: Memory content
            
        Raises:
            StorageOperationError: If removal fails
        """
        try:
            if not content:
                return
                
            # Tokenize content
            words = self.utils.tokenize_content(content)
            
            # Remove from indices
            async with await self.connection.pipeline() as pipe:
                for word in words:
                    word_key = self.utils.create_content_index_key(word)
                    await pipe.srem(word_key, memory_id)
                
                # Execute pipeline
                await pipe.execute()
            
            logger.debug(f"Removed content indices for memory {memory_id}")
        except Exception as e:
            error_msg = f"Failed to remove content indices for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def index_tags(self, memory_id: str, tags: List[str]) -> None:
        """
        Index memory tags.
        
        Args:
            memory_id: Memory ID
            tags: List of tags
            
        Raises:
            StorageOperationError: If indexing fails
        """
        try:
            if not tags:
                return
                
            # Add memory to tag indices
            async with await self.connection.pipeline() as pipe:
                for tag in tags:
                    tag_key = self.utils.create_tag_key(tag)
                    await pipe.sadd(tag_key, memory_id)
                
                # Execute pipeline
                await pipe.execute()
            
            logger.debug(f"Indexed tags for memory {memory_id}: {tags}")
        except Exception as e:
            error_msg = f"Failed to index tags for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update_tag_indices(self, memory_id: str, old_tags: List[str], new_tags: List[str]) -> None:
        """
        Update tag indices for a memory item.
        
        Args:
            memory_id: Memory ID
            old_tags: Old tags (for removing old indices)
            new_tags: New tags
            
        Raises:
            StorageOperationError: If update fails
        """
        try:
            # Convert to sets for comparison
            old_tag_set = set(old_tags)
            new_tag_set = set(new_tags)
            
            # Find tags to add and remove
            tags_to_remove = old_tag_set - new_tag_set
            tags_to_add = new_tag_set - old_tag_set
            
            # Update indices
            async with await self.connection.pipeline() as pipe:
                # Remove from old indices
                for tag in tags_to_remove:
                    tag_key = self.utils.create_tag_key(tag)
                    await pipe.srem(tag_key, memory_id)
                
                # Add to new indices
                for tag in tags_to_add:
                    tag_key = self.utils.create_tag_key(tag)
                    await pipe.sadd(tag_key, memory_id)
                
                # Execute pipeline
                await pipe.execute()
            
            logger.debug(f"Updated tag indices for memory {memory_id}")
        except Exception as e:
            error_msg = f"Failed to update tag indices for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def remove_tag_indices(self, memory_id: str, tags: List[str]) -> None:
        """
        Remove tag indices for a memory item.
        
        Args:
            memory_id: Memory ID
            tags: List of tags
            
        Raises:
            StorageOperationError: If removal fails
        """
        try:
            if not tags:
                return
                
            # Remove memory from tag indices
            async with await self.connection.pipeline() as pipe:
                for tag in tags:
                    tag_key = self.utils.create_tag_key(tag)
                    await pipe.srem(tag_key, memory_id)
                
                # Execute pipeline
                await pipe.execute()
            
            logger.debug(f"Removed tag indices for memory {memory_id}")
        except Exception as e:
            error_msg = f"Failed to remove tag indices for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def index_status(self, memory_id: str, status: str) -> None:
        """
        Index memory status.
        
        Args:
            memory_id: Memory ID
            status: Status value
            
        Raises:
            StorageOperationError: If indexing fails
        """
        try:
            if not status:
                return
                
            # Add memory to status index
            status_key = self.utils.create_status_key(status)
            await self.connection.execute("sadd", status_key, memory_id)
            
            logger.debug(f"Indexed status for memory {memory_id}: {status}")
        except Exception as e:
            error_msg = f"Failed to index status for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def update_status_index(self, memory_id: str, old_status: Optional[str], new_status: str) -> None:
        """
        Update status index for a memory item.
        
        Args:
            memory_id: Memory ID
            old_status: Old status (for removing old index)
            new_status: New status
            
        Raises:
            StorageOperationError: If update fails
        """
        try:
            # No change needed if status hasn't changed
            if old_status == new_status:
                return
                
            # Update indices
            async with await self.connection.pipeline() as pipe:
                # Remove from old index
                if old_status:
                    old_status_key = self.utils.create_status_key(old_status)
                    await pipe.srem(old_status_key, memory_id)
                
                # Add to new index
                new_status_key = self.utils.create_status_key(new_status)
                await pipe.sadd(new_status_key, memory_id)
                
                # Execute pipeline
                await pipe.execute()
            
            logger.debug(f"Updated status index for memory {memory_id} from {old_status} to {new_status}")
        except Exception as e:
            error_msg = f"Failed to update status index for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
    
    async def remove_status_index(self, memory_id: str, status: Optional[str]) -> None:
        """
        Remove status index for a memory item.
        
        Args:
            memory_id: Memory ID
            status: Status value
            
        Raises:
            StorageOperationError: If removal fails
        """
        try:
            if not status:
                return
                
            # Remove memory from status index
            status_key = self.utils.create_status_key(status)
            await self.connection.execute("srem", status_key, memory_id)
            
            logger.debug(f"Removed status index for memory {memory_id}")
        except Exception as e:
            error_msg = f"Failed to remove status index for memory {memory_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageOperationError(error_msg) from e
