"""
Base utility classes for the NCA system.

This module provides base classes with common functionality that can be
used throughout the NCA system.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional


class BaseObject:
    """Base class for all serializable objects in the system."""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert object to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def to_json(self) -> str:
        """Convert object to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'BaseObject':
        """Create an object from a dictionary."""
        obj = cls()
        for k, v in data.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BaseObject':
        """Create an object from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class WithID(BaseObject):
    """Mixin class that adds an ID field to an object."""
    
    def __init__(self, id: Optional[str] = None):
        """
        Initialize with optional ID.
        
        Args:
            id: Object ID (generates UUID if None)
        """
        self.id = id or str(uuid.uuid4())
        
    def to_dict(self) -> dict[str, Any]:
        """Convert object to a dictionary."""
        return {**super().to_dict(), "id": self.id}


class WithTimestamp(BaseObject):
    """Mixin class that adds timestamp fields to an object."""
    
    def __init__(self):
        """Initialize with current timestamp."""
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        
    def update_timestamp(self):
        """Update the 'updated_at' timestamp to current time."""
        self.updated_at = datetime.now()
        
    def to_dict(self) -> dict[str, Any]:
        """Convert object to a dictionary with ISO format timestamps."""
        result = super().to_dict()
        if hasattr(self, 'created_at'):
            result['created_at'] = self.created_at.isoformat()
        if hasattr(self, 'updated_at'):
            result['updated_at'] = self.updated_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'WithTimestamp':
        """Create an object from a dictionary, parsing timestamps."""
        obj = super().from_dict(data)
        if 'created_at' in data and isinstance(data['created_at'], str):
            obj.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            obj.updated_at = datetime.fromisoformat(data['updated_at'])
        return obj


class WithMetadata(BaseObject):
    """Mixin class that adds a metadata dictionary to an object."""
    
    def __init__(self, metadata: Optional[dict[str, Any]] = None):
        """
        Initialize with optional metadata.
        
        Args:
            metadata: Initial metadata dictionary
        """
        self.metadata = metadata or {}
        
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add or update a metadata field.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key doesn't exist
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default) 