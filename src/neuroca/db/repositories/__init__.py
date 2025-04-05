"""
Repository Module for Database Access Layer.

This module implements the repository pattern for the NeuroCognitive Architecture (NCA) system,
providing a clean abstraction layer between the database and application logic. The repositories
encapsulate data access operations and business logic, ensuring separation of concerns and
maintainability.

The repository pattern allows for:
- Centralized data access logic
- Abstraction of database implementation details
- Easier unit testing through dependency injection
- Consistent error handling and logging for database operations
- Type-safe interfaces for domain objects

Usage:
    from neuroca.db.repositories import BaseRepository, RepositoryFactory
    
    # Get a repository instance
    memory_repo = RepositoryFactory.get_repository('memory')
    
    # Use the repository for data operations
    memories = await memory_repo.get_all()
"""

import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generic, Optional, TypeVar

# Type variable for generic repository implementation
T = TypeVar('T')

# Configure logger
logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    """Base exception class for repository-related errors."""
    pass

class EntityNotFoundError(RepositoryError):
    """Exception raised when an entity cannot be found in the repository."""
    def __init__(self, entity_type: str, entity_id: Any):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message)

class DuplicateEntityError(RepositoryError):
    """Exception raised when attempting to create an entity that already exists."""
    def __init__(self, entity_type: str, identifier: Any):
        self.entity_type = entity_type
        self.identifier = identifier
        message = f"{entity_type} with identifier {identifier} already exists"
        super().__init__(message)

class ValidationError(RepositoryError):
    """Exception raised when entity validation fails."""
    def __init__(self, entity_type: str, errors: dict[str, str]):
        self.entity_type = entity_type
        self.errors = errors
        message = f"Validation failed for {entity_type}: {errors}"
        super().__init__(message)

class DatabaseConnectionError(RepositoryError):
    """Exception raised when database connection fails."""
    def __init__(self, original_error: Exception):
        self.original_error = original_error
        message = f"Database connection error: {str(original_error)}"
        super().__init__(message)

class BaseRepository(Generic[T], ABC):
    """
    Abstract base class for all repositories.
    
    Provides a common interface and shared functionality for all repository implementations.
    Repositories are responsible for data access operations and encapsulating the business logic
    related to retrieving and persisting entities.
    
    Attributes:
        entity_type (str): The name of the entity type this repository manages.
    """
    
    def __init__(self, entity_type: str):
        """
        Initialize the repository with the entity type it manages.
        
        Args:
            entity_type (str): The name of the entity type this repository manages.
        """
        self.entity_type = entity_type
        logger.debug(f"Initialized {entity_type} repository")
    
    @abstractmethod
    async def get_by_id(self, entity_id: Any) -> T:
        """
        Retrieve an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity.
            
        Returns:
            The entity with the specified ID.
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists.
            DatabaseConnectionError: If a database connection error occurs.
        """
        pass
    
    @abstractmethod
    async def get_all(self, filters: Optional[dict[str, Any]] = None) -> list[T]:
        """
        Retrieve all entities, optionally filtered.
        
        Args:
            filters: Optional dictionary of filter criteria.
            
        Returns:
            A list of entities matching the filter criteria.
            
        Raises:
            DatabaseConnectionError: If a database connection error occurs.
        """
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity in the repository.
        
        Args:
            entity: The entity to create.
            
        Returns:
            The created entity, potentially with generated fields (e.g., ID).
            
        Raises:
            ValidationError: If the entity fails validation.
            DuplicateEntityError: If an entity with the same unique identifier already exists.
            DatabaseConnectionError: If a database connection error occurs.
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: Any, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity_id: The unique identifier of the entity to update.
            entity: The updated entity data.
            
        Returns:
            The updated entity.
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists.
            ValidationError: If the entity fails validation.
            DatabaseConnectionError: If a database connection error occurs.
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity to delete.
            
        Returns:
            True if the entity was successfully deleted, False otherwise.
            
        Raises:
            EntityNotFoundError: If no entity with the given ID exists.
            DatabaseConnectionError: If a database connection error occurs.
        """
        pass
    
    @contextmanager
    def error_handling(self):
        """
        Context manager for standardized error handling in repository operations.
        
        Catches database-specific exceptions and wraps them in repository-specific exceptions
        for consistent error handling throughout the application.
        
        Example:
            ```
            async def get_by_id(self, entity_id: Any) -> T:
                with self.error_handling():
                    # Database access code here
                    return entity
            ```
        
        Raises:
            DatabaseConnectionError: If a database connection error occurs.
            RepositoryError: For other repository-related errors.
        """
        try:
            yield
        except Exception as e:
            logger.error(f"Repository error in {self.entity_type} repository: {str(e)}", exc_info=True)
            # Re-raise as appropriate repository exception
            # This would be expanded based on the specific database being used
            raise DatabaseConnectionError(e)

class RepositoryFactory:
    """
    Factory class for creating and managing repository instances.
    
    This class is responsible for creating and caching repository instances,
    ensuring that only one instance of each repository type exists.
    """
    
    _repositories: dict[str, BaseRepository] = {}
    
    @classmethod
    def register_repository(cls, name: str, repository: BaseRepository) -> None:
        """
        Register a repository instance with the factory.
        
        Args:
            name: The name to register the repository under.
            repository: The repository instance to register.
        """
        cls._repositories[name] = repository
        logger.info(f"Registered repository: {name}")
    
    @classmethod
    def get_repository(cls, name: str) -> BaseRepository:
        """
        Get a repository instance by name.
        
        Args:
            name: The name of the repository to retrieve.
            
        Returns:
            The requested repository instance.
            
        Raises:
            KeyError: If no repository with the given name is registered.
        """
        if name not in cls._repositories:
            logger.error(f"Repository not found: {name}")
            raise KeyError(f"No repository registered with name: {name}")
        
        logger.debug(f"Retrieved repository: {name}")
        return cls._repositories[name]
    
    @classmethod
    def list_repositories(cls) -> list[str]:
        """
        List all registered repository names.
        
        Returns:
            A list of registered repository names.
        """
        return list(cls._repositories.keys())

# Import specific repository implementations to make them available
# These imports will be uncommented as repositories are implemented
# from .memory_repository import MemoryRepository
# from .cognitive_repository import CognitiveRepository
# from .health_repository import HealthRepository
# from .user_repository import UserRepository

__all__ = [
    'BaseRepository',
    'RepositoryFactory',
    'RepositoryError',
    'EntityNotFoundError',
    'DuplicateEntityError',
    'ValidationError',
    'DatabaseConnectionError',
]