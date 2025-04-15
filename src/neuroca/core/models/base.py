"""
Base Model Implementation for NeuroCognitive Architecture (NCA).

This module provides the foundational model classes and mixins that serve as the
building blocks for all domain models in the NCA system. It implements common
functionality such as serialization, validation, persistence hooks, and lifecycle
management that all models inherit.

The BaseModel class follows a composition pattern with mixins to allow for flexible
extension of functionality while maintaining a clean inheritance hierarchy.

Usage:
    from neuroca.core.models.base import BaseModel, TimestampMixin

    class MyModel(TimestampMixin, BaseModel):
        def __init__(self, id, name, **kwargs):
            self.name = name
            super().__init__(id=id, **kwargs)

        def validate(self):
            super().validate()
            if not self.name:
                raise ValidationError("Name cannot be empty")
"""

import abc
import copy
import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, cast

# Setup module logger
logger = logging.getLogger(__name__)

# Type variable for self-referencing return types
T = TypeVar('T', bound='BaseModel')


class ModelError(Exception):
    """Base exception class for all model-related errors."""
    pass


class ValidationError(ModelError):
    """Exception raised when model validation fails."""
    pass


class SerializationError(ModelError):
    """Exception raised when model serialization or deserialization fails."""
    pass


class PersistenceError(ModelError):
    """Exception raised when model persistence operations fail."""
    pass


class ModelNotFoundError(ModelError):
    """Exception raised when a model cannot be found by its identifier."""
    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp fields to models.
    
    Automatically manages timestamps during model lifecycle events.
    """
    
    def __init__(self, **kwargs):
        """Initialize timestamp fields with current time or provided values."""
        self.created_at = kwargs.get('created_at', datetime.datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', self.created_at)
        super().__init__(**kwargs)
    
    def pre_save(self) -> None:
        """Update the updated_at timestamp before saving."""
        self.updated_at = datetime.datetime.utcnow()
        super().pre_save()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert timestamps to ISO format strings in dictionary representation."""
        data = super().to_dict()
        # Convert datetime objects to ISO format strings
        if hasattr(self, 'created_at') and self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if hasattr(self, 'updated_at') and self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Parse ISO format timestamp strings from dictionary."""
        data_copy = copy.deepcopy(data)
        
        # Convert ISO format strings to datetime objects
        for field in ['created_at', 'updated_at']:
            if field in data_copy and isinstance(data_copy[field], str):
                try:
                    data_copy[field] = datetime.datetime.fromisoformat(data_copy[field])
                except ValueError as e:
                    logger.error(f"Failed to parse {field} timestamp: {e}")
                    raise SerializationError(f"Invalid timestamp format for {field}") from e
        
        return super(TimestampMixin, cls).from_dict(data_copy)


class VersionedMixin:
    """
    Mixin that adds versioning capability to models.
    
    Tracks version numbers and provides methods to handle version conflicts.
    """
    
    def __init__(self, **kwargs):
        """Initialize version field with default or provided value."""
        self.version = kwargs.get('version', 1)
        super().__init__(**kwargs)
    
    def pre_save(self) -> None:
        """Increment version number before saving."""
        self.version += 1
        super().pre_save()
    
    def check_version(self, expected_version: int) -> bool:
        """
        Check if the current version matches the expected version.
        
        Args:
            expected_version: The version number to check against
            
        Returns:
            bool: True if versions match, False otherwise
        """
        return self.version == expected_version


class BaseModel(abc.ABC):
    """
    Abstract base class for all domain models in the NCA system.
    
    Provides core functionality for model lifecycle, serialization,
    validation, and persistence operations.
    """
    
    # Class-level registry of field names to exclude from serialization
    _private_fields: Set[str] = {'_private_fields', '_id_field'}
    
    # Name of the field that serves as the primary identifier
    _id_field: str = 'id'
    
    def __init__(self, **kwargs):
        """
        Initialize a new model instance.
        
        Args:
            **kwargs: Keyword arguments corresponding to model fields
        """
        # Set ID field if provided, otherwise generate a new UUID
        id_value = kwargs.get(self._id_field)
        if id_value is None:
            id_value = str(uuid.uuid4())
        
        setattr(self, self._id_field, id_value)
        
        # Initialize any additional fields from kwargs
        for key, value in kwargs.items():
            if key != self._id_field and not key.startswith('_'):
                setattr(self, key, value)
        
        logger.debug(f"Initialized {self.__class__.__name__} with ID: {getattr(self, self._id_field)}")
    
    @property
    def id(self) -> str:
        """
        Get the model's unique identifier.
        
        Returns:
            str: The model's ID
        """
        return cast(str, getattr(self, self._id_field))
    
    def validate(self) -> None:
        """
        Validate the model state.
        
        Raises:
            ValidationError: If validation fails
        """
        # Base validation ensures ID is present
        if not getattr(self, self._id_field):
            raise ValidationError(f"Model {self.__class__.__name__} must have a valid {self._id_field}")
    
    def pre_save(self) -> None:
        """
        Hook called before the model is saved.
        
        Override in subclasses to implement custom pre-save logic.
        """
        pass
    
    def post_save(self) -> None:
        """
        Hook called after the model is saved.
        
        Override in subclasses to implement custom post-save logic.
        """
        pass
    
    def pre_delete(self) -> None:
        """
        Hook called before the model is deleted.
        
        Override in subclasses to implement custom pre-delete logic.
        """
        pass
    
    def post_delete(self) -> None:
        """
        Hook called after the model is deleted.
        
        Override in subclasses to implement custom post-delete logic.
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        result = {}
        
        for key, value in self.__dict__.items():
            # Skip private fields
            if key in self._private_fields or key.startswith('_'):
                continue
            
            # Handle nested models
            if isinstance(value, BaseModel):
                result[key] = value.to_dict()
            # Handle lists of models
            elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
                result[key] = [item.to_dict() if isinstance(item, BaseModel) else item for item in value]
            # Handle all other types
            else:
                result[key] = value
        
        return result
    
    def to_json(self, **kwargs) -> str:
        """
        Convert the model to a JSON string.
        
        Args:
            **kwargs: Additional arguments to pass to json.dumps()
            
        Returns:
            str: JSON string representation of the model
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            return json.dumps(self.to_dict(), **kwargs)
        except (TypeError, ValueError, OverflowError) as e:
            logger.error(f"JSON serialization error for {self.__class__.__name__}: {e}")
            raise SerializationError(f"Failed to serialize {self.__class__.__name__} to JSON") from e
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary.
        
        Args:
            data: Dictionary containing model data
            
        Returns:
            T: New model instance
            
        Raises:
            SerializationError: If deserialization fails
        """
        if not isinstance(data, dict):
            raise SerializationError(f"Expected dict, got {type(data).__name__}")
        
        try:
            # Create a copy to avoid modifying the input
            data_copy = copy.deepcopy(data)
            
            # Create a new instance with the data
            instance = cls(**data_copy)
            
            # Validate the new instance
            instance.validate()
            
            return instance
        except Exception as e:
            logger.error(f"Error deserializing {cls.__name__} from dict: {e}")
            raise SerializationError(f"Failed to deserialize {cls.__name__} from dictionary") from e
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """
        Create a model instance from a JSON string.
        
        Args:
            json_str: JSON string containing model data
            
        Returns:
            T: New model instance
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise SerializationError(f"Invalid JSON format for {cls.__name__}") from e
    
    def __eq__(self, other: Any) -> bool:
        """
        Compare two model instances for equality.
        
        Models are considered equal if they have the same class and ID.
        
        Args:
            other: Object to compare with
            
        Returns:
            bool: True if equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        
        return getattr(self, self._id_field) == getattr(other, self._id_field)
    
    def __hash__(self) -> int:
        """
        Generate a hash value for the model.
        
        Returns:
            int: Hash value based on the model's ID
        """
        return hash((self.__class__, getattr(self, self._id_field)))
    
    def __str__(self) -> str:
        """
        Get a string representation of the model.
        
        Returns:
            str: String representation including class name and ID
        """
        return f"{self.__class__.__name__}(id={getattr(self, self._id_field)})"
    
    def __repr__(self) -> str:
        """
        Get a detailed string representation of the model.
        
        Returns:
            str: Detailed string representation including all fields
        """
        fields = ', '.join(f"{k}={repr(v)}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({fields})"
    
    def clone(self: T, **kwargs) -> T:
        """
        Create a deep copy of the model with optional field overrides.
        
        Args:
            **kwargs: Fields to override in the cloned instance
            
        Returns:
            T: New model instance with the same data
        """
        # Create a dictionary representation
        data = self.to_dict()
        
        # Apply overrides
        data.update(kwargs)
        
        # Create a new instance
        return self.__class__.from_dict(data)


class AggregateRoot(BaseModel):
    """
    Base class for aggregate roots in the domain model.
    
    Aggregate roots are the entry point to an aggregate of domain objects and
    enforce consistency rules for the entire aggregate.
    """
    
    def __init__(self, **kwargs):
        """Initialize a new aggregate root instance."""
        self._events: List[Dict[str, Any]] = []
        super().__init__(**kwargs)
    
    def add_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a domain event that occurred within this aggregate.
        
        Args:
            event_type: Type of the event
            data: Additional event data
        """
        if data is None:
            data = {}
            
        event = {
            'type': event_type,
            'aggregate_id': self.id,
            'aggregate_type': self.__class__.__name__,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'data': data
        }
        
        self._events.append(event)
        logger.debug(f"Added event {event_type} to {self.__class__.__name__} {self.id}")
    
    def clear_events(self) -> List[Dict[str, Any]]:
        """
        Clear and return all recorded events.
        
        Returns:
            List[Dict[str, Any]]: List of recorded events
        """
        events = self._events.copy()
        self._events = []
        return events
    
    def get_events(self) -> List[Dict[str, Any]]:
        """
        Get all recorded events without clearing them.
        
        Returns:
            List[Dict[str, Any]]: List of recorded events
        """
        return self._events.copy()


class ReadOnlyModelError(ModelError):
    """Exception raised when attempting to modify a read-only model."""
    pass


class ReadOnlyModel(BaseModel):
    """
    Base class for read-only models.
    
    These models cannot be modified after creation and are typically used
    for query results or views.
    """
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Prevent modification of attributes after initialization.
        
        Args:
            name: Attribute name
            value: Attribute value
            
        Raises:
            ReadOnlyModelError: If attempting to modify an existing attribute
        """
        if hasattr(self, name):
            raise ReadOnlyModelError(f"Cannot modify {name} on read-only model {self.__class__.__name__}")
        super().__setattr__(name, value)
    
    def pre_save(self) -> None:
        """
        Prevent saving of read-only models.
        
        Raises:
            ReadOnlyModelError: Always raised when called
        """
        raise ReadOnlyModelError(f"Cannot save read-only model {self.__class__.__name__}")
    
    def pre_delete(self) -> None:
        """
        Prevent deletion of read-only models.
        
        Raises:
            ReadOnlyModelError: Always raised when called
        """
        raise ReadOnlyModelError(f"Cannot delete read-only model {self.__class__.__name__}")