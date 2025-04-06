"""
Test Factories Module
=====================

This module provides factory classes for creating test objects used throughout the test suite.
Factories help maintain consistency in test data and reduce duplication across tests.

The module uses the factory_boy library to implement the Factory pattern, making it easy to:
- Create test objects with sensible defaults
- Override specific attributes when needed
- Create related objects automatically
- Generate sequences and random data

Usage Examples:
--------------
```python
# Create a user with default values
user = UserFactory()

# Create a user with specific values
admin_user = UserFactory(role='admin', is_active=True)

# Create multiple users
users = UserFactory.create_batch(5)

# Create a memory item with associated user
memory = MemoryItemFactory(user=admin_user)
```

Note: Import specific factories from their respective modules rather than importing
directly from this package to avoid circular imports.
"""

import logging
from typing import Any, Optional, TypeVar

# Configure logging for the factories module
logger = logging.getLogger(__name__)

# Import factory_boy - the main dependency for creating test factories
try:
    import factory
    from factory.faker import Faker
except ImportError:
    logger.critical("factory_boy package is required for test factories. "
                   "Install it with: pip install factory_boy")
    raise

# Import SQLAlchemy integration if using SQLAlchemy models
try:
    from factory.alchemy import SQLAlchemyModelFactory
except ImportError:
    logger.warning("SQLAlchemy integration for factory_boy not available. "
                  "If using SQLAlchemy models, install: pip install factory_boy[sqlalchemy]")

# Import Django integration if using Django models
try:
    from factory.django import DjangoModelFactory
except ImportError:
    logger.debug("Django integration for factory_boy not available. "
                "This is expected if not using Django.")

# Type variable for generic factory methods
T = TypeVar('T')

# Base factory configuration
class BaseFactory(factory.Factory):
    """
    Base factory class that all other factories should inherit from.
    Provides common functionality and configuration.
    """
    class Meta:
        abstract = True

    @classmethod
    def create_batch_dict(cls, size: int, **kwargs) -> dict[str, Any]:
        """
        Create a batch of objects and return them as a dictionary keyed by a specified attribute.
        
        Args:
            size: Number of objects to create
            **kwargs: Attributes to set on the created objects
            
        Returns:
            Dictionary of created objects keyed by the specified attribute
            
        Example:
            users = UserFactory.create_batch_dict(5, key_attr='username')
        """
        key_attr = kwargs.pop('key_attr', 'id')
        batch = cls.create_batch(size, **kwargs)
        return {getattr(obj, key_attr): obj for obj in batch}

    @classmethod
    def attributes(cls, create: bool = False, **kwargs) -> dict[str, Any]:
        """
        Get a dictionary of attributes that would be used to create an instance.
        Useful for testing validation without creating objects.
        
        Args:
            create: Whether to prepare attributes for object creation
            **kwargs: Attribute overrides
            
        Returns:
            Dictionary of attributes
        """
        return factory.build(dict, FACTORY_CLASS=cls, **kwargs)


# Base factory for SQLAlchemy models if used in the project
class BaseSQLAlchemyFactory(SQLAlchemyModelFactory):
    """
    Base factory for SQLAlchemy models.
    All SQLAlchemy model factories should inherit from this class.
    """
    class Meta:
        abstract = True
        # Session will be set in specific factory implementations or via fixture


# Base factory for Django models if used in the project
class BaseDjangoFactory(DjangoModelFactory):
    """
    Base factory for Django models.
    All Django model factories should inherit from this class.
    """
    class Meta:
        abstract = True


# Utility functions for working with factories
def register_factory(model_class: type[T], factory_class: type[factory.Factory]) -> None:
    """
    Register a factory class for a model to enable lookup by model class.
    
    Args:
        model_class: The model class
        factory_class: The factory class for the model
        
    Example:
        register_factory(User, UserFactory)
    """
    if not hasattr(register_factory, 'registry'):
        register_factory.registry = {}
    
    register_factory.registry[model_class] = factory_class
    logger.debug(f"Registered factory {factory_class.__name__} for model {model_class.__name__}")


def get_factory_for_model(model_class: type[T]) -> Optional[type[factory.Factory]]:
    """
    Get the factory class registered for a model class.
    
    Args:
        model_class: The model class to look up
        
    Returns:
        The factory class or None if not registered
        
    Example:
        user_factory = get_factory_for_model(User)
        user = user_factory(username='testuser')
    """
    if not hasattr(register_factory, 'registry'):
        return None
    
    return register_factory.registry.get(model_class)


def create_fixture_data(factories_config: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """
    Create fixture data based on a configuration dictionary.
    Useful for setting up test data in fixtures or test setup.
    
    Args:
        factories_config: List of dictionaries with factory configurations
            Each dict should have 'factory', 'count', and optional 'attrs' keys
            
    Returns:
        Dictionary of created objects grouped by factory class name
        
    Example:
        data = create_fixture_data([
            {'factory': UserFactory, 'count': 5, 'attrs': {'is_active': True}},
            {'factory': MemoryItemFactory, 'count': 10}
        ])
    """
    result = {}
    
    for config in factories_config:
        factory_class = config['factory']
        count = config.get('count', 1)
        attrs = config.get('attrs', {})
        
        factory_name = factory_class.__name__
        if count == 1:
            result[factory_name] = [factory_class(**attrs)]
        else:
            result[factory_name] = factory_class.create_batch(count, **attrs)
        
        logger.info(f"Created {count} instances using {factory_name}")
    
    return result


# Export public API
__all__ = [
    'BaseFactory',
    'BaseSQLAlchemyFactory', 
    'BaseDjangoFactory',
    'register_factory',
    'get_factory_for_model',
    'create_fixture_data',
    'factory',
    'Faker'
]

# Version information
__version__ = '0.1.0'

# Initialize module
logger.debug("Test factories module initialized")