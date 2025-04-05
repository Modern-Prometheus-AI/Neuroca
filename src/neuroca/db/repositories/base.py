"""
Base Repository Module for NeuroCognitive Architecture (NCA)

This module provides the foundation for all database repository implementations
in the NCA system. It implements the Repository pattern to abstract database
operations and provide a consistent interface for data access across the application.

The BaseRepository class is designed to be extended by concrete repository implementations
for specific entity types, providing common CRUD operations and transaction management.

Usage:
    class UserRepository(BaseRepository[User, UUID]):
        def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
            super().__init__(User, session_factory)
            
        def find_by_email(self, email: str) -> Optional[User]:
            with self.session_factory() as session:
                return session.query(self.model).filter(self.model.email == email).first()
"""

import logging
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any, Callable, Generic, Optional, TypeVar
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

# Type variables for entity models and their ID types
T = TypeVar('T')  # Entity type
ID = TypeVar('ID', UUID, int, str)  # ID type (UUID, int, or str)

# Configure logger
logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Base exception for repository-related errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Exception raised when an entity cannot be found."""
    
    def __init__(self, entity_type: str, entity_id: Any):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message)


class DuplicateEntityError(RepositoryError):
    """Exception raised when attempting to create a duplicate entity."""
    
    def __init__(self, entity_type: str, details: str = None):
        self.entity_type = entity_type
        message = f"Duplicate {entity_type} entity"
        if details:
            message += f": {details}"
        super().__init__(message)


class RepositoryInterface(Generic[T, ID], ABC):
    """
    Abstract interface defining the standard operations for repository implementations.
    
    This interface ensures all repositories implement a consistent set of methods
    for interacting with the database.
    """
    
    @abstractmethod
    def get(self, entity_id: ID) -> Optional[T]:
        """Retrieve an entity by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> list[T]:
        """Retrieve all entities."""
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: ID) -> bool:
        """Delete an entity by its ID."""
        pass


class BaseRepository(Generic[T, ID], RepositoryInterface[T, ID]):
    """
    Base implementation of the Repository pattern for SQLAlchemy ORM models.
    
    This class provides common database operations and transaction management
    for all entity types. It should be extended by concrete repository implementations.
    
    Attributes:
        model: The SQLAlchemy model class this repository manages
        session_factory: A callable that returns a SQLAlchemy session context manager
    """
    
    def __init__(self, model: type[T], session_factory: Callable[..., AbstractContextManager[Session]]):
        """
        Initialize the repository with a model class and session factory.
        
        Args:
            model: The SQLAlchemy model class this repository will manage
            session_factory: A callable that returns a SQLAlchemy session context manager
        """
        self.model = model
        self.session_factory = session_factory
        logger.debug(f"Initialized {self.__class__.__name__} for model {model.__name__}")
    
    def get(self, entity_id: ID) -> Optional[T]:
        """
        Retrieve an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            with self.session_factory() as session:
                entity = session.query(self.model).get(entity_id)
                if entity:
                    logger.debug(f"Retrieved {self.model.__name__} with ID {entity_id}")
                else:
                    logger.debug(f"{self.model.__name__} with ID {entity_id} not found")
                return entity
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving {self.model.__name__} with ID {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve {self.model.__name__}") from e
    
    def get_or_raise(self, entity_id: ID) -> T:
        """
        Retrieve an entity by its ID or raise an exception if not found.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            The entity if found
            
        Raises:
            EntityNotFoundError: If the entity is not found
            RepositoryError: If a database error occurs
        """
        entity = self.get(entity_id)
        if not entity:
            logger.warning(f"{self.model.__name__} with ID {entity_id} not found")
            raise EntityNotFoundError(self.model.__name__, entity_id)
        return entity
    
    def get_all(self) -> list[T]:
        """
        Retrieve all entities of this type.
        
        Returns:
            A list of all entities
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            with self.session_factory() as session:
                entities = session.query(self.model).all()
                logger.debug(f"Retrieved {len(entities)} {self.model.__name__} entities")
                return entities
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all {self.model.__name__} entities: {str(e)}")
            raise RepositoryError(f"Failed to retrieve {self.model.__name__} entities") from e
    
    def create(self, entity: T) -> T:
        """
        Create a new entity in the database.
        
        Args:
            entity: The entity to create
            
        Returns:
            The created entity with any database-generated values
            
        Raises:
            DuplicateEntityError: If an entity with the same unique constraints already exists
            RepositoryError: If a database error occurs
        """
        try:
            with self.session_factory() as session:
                session.add(entity)
                session.commit()
                session.refresh(entity)
                logger.info(f"Created {self.model.__name__} with ID {getattr(entity, 'id', None)}")
                return entity
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Integrity error creating {self.model.__name__}: {str(e)}")
            raise DuplicateEntityError(self.model.__name__, str(e)) from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to create {self.model.__name__}") from e
    
    def update(self, entity: T) -> T:
        """
        Update an existing entity in the database.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
            
        Raises:
            EntityNotFoundError: If the entity does not exist
            DuplicateEntityError: If the update violates unique constraints
            RepositoryError: If a database error occurs
        """
        try:
            with self.session_factory() as session:
                entity_id = getattr(entity, 'id', None)
                if entity_id is None:
                    logger.error(f"Cannot update {self.model.__name__} without ID")
                    raise RepositoryError(f"Cannot update {self.model.__name__} without ID")
                
                # Check if entity exists
                existing = session.query(self.model).get(entity_id)
                if not existing:
                    logger.warning(f"{self.model.__name__} with ID {entity_id} not found for update")
                    raise EntityNotFoundError(self.model.__name__, entity_id)
                
                # Merge the entity
                updated = session.merge(entity)
                session.commit()
                session.refresh(updated)
                logger.info(f"Updated {self.model.__name__} with ID {entity_id}")
                return updated
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Integrity error updating {self.model.__name__} with ID {entity_id}: {str(e)}")
            raise DuplicateEntityError(self.model.__name__, str(e)) from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating {self.model.__name__} with ID {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to update {self.model.__name__}") from e
    
    def delete(self, entity_id: ID) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity to delete
            
        Returns:
            True if the entity was deleted, False if it didn't exist
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            with self.session_factory() as session:
                entity = session.query(self.model).get(entity_id)
                if not entity:
                    logger.debug(f"{self.model.__name__} with ID {entity_id} not found for deletion")
                    return False
                
                session.delete(entity)
                session.commit()
                logger.info(f"Deleted {self.model.__name__} with ID {entity_id}")
                return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error deleting {self.model.__name__} with ID {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete {self.model.__name__}") from e
    
    def count(self) -> int:
        """
        Count the total number of entities.
        
        Returns:
            The count of entities
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            with self.session_factory() as session:
                count = session.query(self.model).count()
                logger.debug(f"Counted {count} {self.model.__name__} entities")
                return count
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__} entities: {str(e)}")
            raise RepositoryError(f"Failed to count {self.model.__name__} entities") from e
    
    def exists(self, entity_id: ID) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            entity_id: The unique identifier to check
            
        Returns:
            True if the entity exists, False otherwise
            
        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            with self.session_factory() as session:
                exists = session.query(session.query(self.model).filter_by(id=entity_id).exists()).scalar()
                logger.debug(f"{self.model.__name__} with ID {entity_id} exists: {exists}")
                return exists
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} with ID {entity_id}: {str(e)}")
            raise RepositoryError(f"Failed to check if {self.model.__name__} exists") from e
    
    def find_by_attributes(self, **kwargs) -> list[T]:
        """
        Find entities matching the given attributes.
        
        Args:
            **kwargs: Attribute name-value pairs to filter by
            
        Returns:
            A list of matching entities
            
        Raises:
            RepositoryError: If a database error occurs or invalid attributes are provided
        """
        try:
            with self.session_factory() as session:
                # Validate that all attributes exist on the model
                for attr in kwargs:
                    if not hasattr(self.model, attr):
                        logger.error(f"Invalid attribute '{attr}' for {self.model.__name__}")
                        raise RepositoryError(f"Invalid attribute '{attr}' for {self.model.__name__}")
                
                query = session.query(self.model)
                for attr, value in kwargs.items():
                    query = query.filter(getattr(self.model, attr) == value)
                
                results = query.all()
                logger.debug(f"Found {len(results)} {self.model.__name__} entities with attributes {kwargs}")
                return results
        except SQLAlchemyError as e:
            logger.error(f"Error finding {self.model.__name__} by attributes {kwargs}: {str(e)}")
            raise RepositoryError(f"Failed to find {self.model.__name__} by attributes") from e
    
    def bulk_create(self, entities: list[T]) -> list[T]:
        """
        Create multiple entities in a single transaction.
        
        Args:
            entities: List of entities to create
            
        Returns:
            The list of created entities
            
        Raises:
            DuplicateEntityError: If any entity violates unique constraints
            RepositoryError: If a database error occurs
        """
        if not entities:
            logger.debug(f"No {self.model.__name__} entities provided for bulk creation")
            return []
        
        try:
            with self.session_factory() as session:
                session.add_all(entities)
                session.commit()
                # Refresh all entities to get database-generated values
                for entity in entities:
                    session.refresh(entity)
                logger.info(f"Bulk created {len(entities)} {self.model.__name__} entities")
                return entities
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Integrity error during bulk creation of {self.model.__name__}: {str(e)}")
            raise DuplicateEntityError(self.model.__name__, str(e)) from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error during bulk creation of {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to bulk create {self.model.__name__} entities") from e
    
    def bulk_delete(self, entity_ids: list[ID]) -> int:
        """
        Delete multiple entities by their IDs in a single transaction.
        
        Args:
            entity_ids: List of entity IDs to delete
            
        Returns:
            The number of entities deleted
            
        Raises:
            RepositoryError: If a database error occurs
        """
        if not entity_ids:
            logger.debug(f"No {self.model.__name__} IDs provided for bulk deletion")
            return 0
        
        try:
            with self.session_factory() as session:
                deleted_count = session.query(self.model).filter(
                    self.model.id.in_(entity_ids)
                ).delete(synchronize_session=False)
                session.commit()
                logger.info(f"Bulk deleted {deleted_count} {self.model.__name__} entities")
                return deleted_count
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error during bulk deletion of {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to bulk delete {self.model.__name__} entities") from e