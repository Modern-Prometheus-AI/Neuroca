"""
Redis Utils Component

This module provides utility functions for Redis operations.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Set


class RedisUtils:
    """
    Utility functions for Redis operations.
    
    This class provides helper methods for various Redis operations such as
    key generation, data serialization/deserialization, and text processing.
    """
    
    def __init__(self, prefix: str):
        """
        Initialize the Redis utilities.
        
        Args:
            prefix: Key prefix for Redis keys (usually "memory:{tier_name}")
        """
        self.prefix = prefix
    
    def generate_id(self) -> str:
        """
        Generate a unique ID for a memory item.
        
        Returns:
            str: A unique ID (UUID4)
        """
        return str(uuid.uuid4())
    
    def create_memory_key(self, memory_id: str) -> str:
        """
        Create a Redis key for storing a memory item.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            str: Redis key for the memory
        """
        return f"{self.prefix}:{memory_id}"
    
    def create_metadata_key(self, memory_id: str) -> str:
        """
        Create a Redis key for storing memory metadata.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            str: Redis key for the metadata
        """
        return f"{self.prefix}:metadata:{memory_id}"
    
    def create_status_key(self, status: str) -> str:
        """
        Create a Redis key for the status index.
        
        Args:
            status: Status value
            
        Returns:
            str: Redis key for the status index
        """
        return f"{self.prefix}:index:status:{status}"
    
    def create_tag_key(self, tag: str) -> str:
        """
        Create a Redis key for a tag index.
        
        Args:
            tag: Tag value
            
        Returns:
            str: Redis key for the tag index
        """
        return f"{self.prefix}:index:tag:{tag}"
    
    def create_content_index_key(self, word: str) -> str:
        """
        Create a Redis key for the content index.
        
        Args:
            word: Word to index
            
        Returns:
            str: Redis key for the content index
        """
        return f"{self.prefix}:index:content:{word}"
    
    def create_stats_key(self) -> str:
        """
        Create a Redis key for storage statistics.
        
        Returns:
            str: Redis key for stats
        """
        return f"{self.prefix}:stats"
    
    def get_current_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            str: Current timestamp
        """
        return datetime.now().isoformat()
    
    def get_current_timestamp_seconds(self) -> float:
        """
        Get the current timestamp in seconds since epoch.
        
        Returns:
            float: Current timestamp in seconds
        """
        return time.time()
    
    def timestamp_to_seconds(self, timestamp: str) -> float:
        """
        Convert an ISO format timestamp to seconds since epoch.
        
        Args:
            timestamp: Timestamp in ISO format
            
        Returns:
            float: Timestamp in seconds
        """
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.timestamp()
        except (ValueError, TypeError):
            return 0.0
    
    def serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Serialize metadata to JSON string.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            str: JSON string
        """
        return json.dumps(metadata)
    
    def deserialize_metadata(self, json_string: Optional[str]) -> Dict[str, Any]:
        """
        Deserialize metadata from JSON string.
        
        Args:
            json_string: JSON string or None
            
        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        if not json_string:
            return {}
        return json.loads(json_string)
    
    def tokenize_content(self, content: str) -> Set[str]:
        """
        Tokenize content into words for indexing.
        
        Args:
            content: Content to tokenize
            
        Returns:
            Set[str]: Set of unique words
        """
        if not content:
            return set()
            
        # Simple tokenization by splitting on whitespace and removing punctuation
        words = content.lower()
        for char in ",.;:!?\"'()[]{}":
            words = words.replace(char, " ")
        
        # Return unique words
        return set(word for word in words.split() if word)
    
    def prepare_memory_data(self, memory_id: str, content: Optional[str] = None, 
                            summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare memory data for storage.
        
        Args:
            memory_id: Memory ID
            content: Memory content
            summary: Memory summary
            
        Returns:
            Dict[str, Any]: Memory data
        """
        memory_data = {
            "id": memory_id,
            "created_at": self.get_current_timestamp(),
        }
        
        if content is not None:
            memory_data["content"] = content
            
        if summary is not None:
            memory_data["summary"] = summary
            
        return memory_data
    
    def update_memory_data(self, content: Optional[str] = None, 
                          summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare memory data for update.
        
        Args:
            content: Memory content
            summary: Memory summary
            
        Returns:
            Dict[str, Any]: Memory data
        """
        memory_data = {
            "last_modified": self.get_current_timestamp(),
        }
        
        if content is not None:
            memory_data["content"] = content
            
        if summary is not None:
            memory_data["summary"] = summary
            
        return memory_data
