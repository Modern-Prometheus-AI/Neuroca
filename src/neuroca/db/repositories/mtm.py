"""
Many-to-Many Repository Module for NeuroCognitive Architecture.

This module provides a generic repository implementation for handling many-to-many
relationships in the database. It offers functionality to create, read, update, and delete
association records between entities, supporting the complex relationship management
needed for the NeuroCognitive Architecture's memory and cognitive components.

The MTMRepository class is designed to be flexible and reusable across different
many-to-many relationships in the system, with proper error handling, validation,
and transaction management.

Usage:
    # Example: Managing concept-to-concept relationships
    mtm_repo = MTMRepository(
        db_session=session,
        association_model=ConceptAssociation,
        left_model=Concept,
        right_model=Concept
    )
    
    # Create association
    mtm_repo.associate(left_id=1, right_id=2, metadata={"strength": 0.8})
    
    # Get all associations for an entity
    associations = mtm_repo.get_associations_for_entity(entity_id=1, side="left")
    
    # Remove association
    mtm_repo.dissociate(left_id=1, right_id=2)
"""

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Literal, Optional

from sqlalchemy import and_, delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session, joinedload

from neuroca.core.exceptions import (
    DatabaseError,
    EntityNotFoundError,
    InvalidInputError,
    RepositoryError,
)

# Configure logger
logger = logging.getLogger(__name__)


class MTMRepository:
    """
    Repository for managing many-to-many relationships between entities.
    
    This class provides methods to create, read, update, and delete association records
    between two entity types, supporting metadata on the association if needed.
    
    Attributes:
        db_session (Session): SQLAlchemy database session
        association_model (Type[DeclarativeMeta]): SQLAlchemy model for the association table
        left_model (Type[DeclarativeMeta]): SQLAlchemy model for the left side entity
        right_model (Type[DeclarativeMeta]): SQLAlchemy model for the right side entity
        left_fk_name (str): Name of the foreign key column for the left entity
        right_fk_name (str): Name of the foreign key column for the right entity
    """
    
    def __init__(
        self,
        db_session: Session,
        association_model: type[DeclarativeMeta],
        left_model: type[DeclarativeMeta],
        right_model: type[DeclarativeMeta],
        left_fk_name: str = "left_id",
        right_fk_name: str = "right_id"
    ):
        """
        Initialize the MTMRepository with the necessary models and session.
        
        Args:
            db_session: SQLAlchemy database session
            association_model: SQLAlchemy model for the association table
            left_model: SQLAlchemy model for the left side entity
            right_model: SQLAlchemy model for the right side entity
            left_fk_name: Name of the foreign key column for the left entity (default: "left_id")
            right_fk_name: Name of the foreign key column for the right entity (default: "right_id")
        """
        self.db_session = db_session
        self.association_model = association_model
        self.left_model = left_model
        self.right_model = right_model
        self.left_fk_name = left_fk_name
        self.right_fk_name = right_fk_name
        
        logger.debug(
            f"Initialized MTMRepository with association_model={association_model.__name__}, "
            f"left_model={left_model.__name__}, right_model={right_model.__name__}"
        )
    
    @contextmanager
    def _transaction(self):
        """
        Context manager for handling database transactions.
        
        Provides automatic rollback on exception and proper error handling.
        
        Yields:
            Session: The active database session
            
        Raises:
            DatabaseError: If a database-related error occurs
        """
        try:
            yield self.db_session
            # The session will be committed by the caller if needed
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error in MTM repository transaction: {str(e)}")
            raise InvalidInputError(f"Database constraint violation: {str(e)}") from e
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error in MTM repository transaction: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}") from e
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error in MTM repository transaction: {str(e)}")
            raise RepositoryError(f"Repository operation failed: {str(e)}") from e
    
    def _validate_entity_exists(self, entity_id: Any, model: type[DeclarativeMeta], entity_name: str) -> None:
        """
        Validate that an entity with the given ID exists in the database.
        
        Args:
            entity_id: ID of the entity to check
            model: SQLAlchemy model class of the entity
            entity_name: Name of the entity for error messages
            
        Raises:
            EntityNotFoundError: If the entity does not exist
            InvalidInputError: If the entity_id is invalid
        """
        if entity_id is None:
            raise InvalidInputError(f"{entity_name} ID cannot be None")
        
        try:
            exists = self.db_session.query(
                self.db_session.query(model).filter(model.id == entity_id).exists()
            ).scalar()
            
            if not exists:
                logger.warning(f"{entity_name} with ID {entity_id} not found")
                raise EntityNotFoundError(f"{entity_name} with ID {entity_id} not found")
        except SQLAlchemyError as e:
            logger.error(f"Database error while validating {entity_name} existence: {str(e)}")
            raise DatabaseError(f"Failed to validate {entity_name} existence: {str(e)}") from e
    
    def associate(
        self, 
        left_id: Any, 
        right_id: Any, 
        metadata: Optional[dict[str, Any]] = None,
        validate_entities: bool = True
    ) -> Any:
        """
        Create an association between two entities.
        
        Args:
            left_id: ID of the left entity
            right_id: ID of the right entity
            metadata: Optional metadata to store with the association
            validate_entities: Whether to validate that both entities exist before associating
            
        Returns:
            The created association record
            
        Raises:
            EntityNotFoundError: If validate_entities is True and either entity doesn't exist
            InvalidInputError: If the input data is invalid
            DatabaseError: If a database error occurs
        """
        if validate_entities:
            self._validate_entity_exists(left_id, self.left_model, "Left entity")
            self._validate_entity_exists(right_id, self.right_model, "Right entity")
        
        # Check if association already exists
        existing = self.get_association(left_id, right_id)
        if existing:
            logger.info(f"Association between {left_id} and {right_id} already exists, updating metadata")
            if metadata:
                return self.update_association_metadata(left_id, right_id, metadata)
            return existing
        
        # Create association data
        association_data = {
            self.left_fk_name: left_id,
            self.right_fk_name: right_id
        }
        
        # Add metadata if provided
        if metadata:
            if hasattr(self.association_model, 'metadata'):
                association_data['metadata'] = metadata
            else:
                # If the model doesn't have a metadata column, add each key as a separate column
                for key, value in metadata.items():
                    if hasattr(self.association_model, key):
                        association_data[key] = value
                    else:
                        logger.warning(f"Metadata key '{key}' not found in association model, skipping")
        
        with self._transaction() as session:
            try:
                association = self.association_model(**association_data)
                session.add(association)
                session.commit()
                logger.info(f"Created association between {left_id} and {right_id}")
                return association
            except Exception as e:
                logger.error(f"Failed to create association: {str(e)}")
                raise
    
    def get_association(self, left_id: Any, right_id: Any) -> Optional[Any]:
        """
        Get a specific association between two entities.
        
        Args:
            left_id: ID of the left entity
            right_id: ID of the right entity
            
        Returns:
            The association record if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = select(self.association_model).where(
                and_(
                    getattr(self.association_model, self.left_fk_name) == left_id,
                    getattr(self.association_model, self.right_fk_name) == right_id
                )
            )
            
            result = self.db_session.execute(query).scalars().first()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting association: {str(e)}")
            raise DatabaseError(f"Failed to get association: {str(e)}") from e
    
    def get_associations_for_entity(
        self, 
        entity_id: Any, 
        side: Literal["left", "right"],
        include_related: bool = False,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[Any]:
        """
        Get all associations for a specific entity.
        
        Args:
            entity_id: ID of the entity
            side: Which side of the relationship the entity is on ("left" or "right")
            include_related: Whether to include the related entity in the results
            filters: Optional dictionary of filters to apply to the query
            limit: Optional limit on the number of results
            offset: Optional offset for pagination
            
        Returns:
            List of association records
            
        Raises:
            InvalidInputError: If the side parameter is invalid
            DatabaseError: If a database error occurs
        """
        if side not in ["left", "right"]:
            raise InvalidInputError("Side must be either 'left' or 'right'")
        
        try:
            # Determine which foreign key to filter on based on the side
            fk_name = self.left_fk_name if side == "left" else self.right_fk_name
            
            # Build the query
            query = select(self.association_model)
            
            # Add eager loading of related entity if requested
            if include_related:
                related_relationship = "right" if side == "left" else "left"
                if hasattr(self.association_model, related_relationship):
                    query = query.options(joinedload(getattr(self.association_model, related_relationship)))
            
            # Add the main filter for the entity ID
            query = query.where(getattr(self.association_model, fk_name) == entity_id)
            
            # Add any additional filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.association_model, key):
                        query = query.where(getattr(self.association_model, key) == value)
            
            # Add pagination if specified
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            
            # Execute the query
            result = self.db_session.execute(query).scalars().all()
            return list(result)
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting associations for entity: {str(e)}")
            raise DatabaseError(f"Failed to get associations: {str(e)}") from e
    
    def get_related_entities(
        self, 
        entity_id: Any, 
        side: Literal["left", "right"],
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[Any]:
        """
        Get all related entities for a specific entity.
        
        Args:
            entity_id: ID of the entity
            side: Which side of the relationship the entity is on ("left" or "right")
            filters: Optional dictionary of filters to apply to the query
            limit: Optional limit on the number of results
            offset: Optional offset for pagination
            
        Returns:
            List of related entity records
            
        Raises:
            InvalidInputError: If the side parameter is invalid
            DatabaseError: If a database error occurs
        """
        if side not in ["left", "right"]:
            raise InvalidInputError("Side must be either 'left' or 'right'")
        
        try:
            # Determine which models and foreign keys to use based on the side
            entity_fk = self.left_fk_name if side == "left" else self.right_fk_name
            related_model = self.right_model if side == "left" else self.left_model
            related_fk = self.right_fk_name if side == "left" else self.left_fk_name
            
            # Build the subquery to get the related IDs
            subquery = select(getattr(self.association_model, related_fk)).where(
                getattr(self.association_model, entity_fk) == entity_id
            )
            
            # Add any additional filters to the subquery
            if filters:
                for key, value in filters.items():
                    if hasattr(self.association_model, key):
                        subquery = subquery.where(getattr(self.association_model, key) == value)
            
            # Build the main query to get the related entities
            query = select(related_model).where(related_model.id.in_(subquery))
            
            # Add pagination if specified
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            
            # Execute the query
            result = self.db_session.execute(query).scalars().all()
            return list(result)
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting related entities: {str(e)}")
            raise DatabaseError(f"Failed to get related entities: {str(e)}") from e
    
    def update_association_metadata(
        self, 
        left_id: Any, 
        right_id: Any, 
        metadata: dict[str, Any]
    ) -> Optional[Any]:
        """
        Update the metadata for an existing association.
        
        Args:
            left_id: ID of the left entity
            right_id: ID of the right entity
            metadata: New metadata to store with the association
            
        Returns:
            The updated association record if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        association = self.get_association(left_id, right_id)
        if not association:
            logger.warning(f"Association between {left_id} and {right_id} not found for metadata update")
            return None
        
        with self._transaction() as session:
            try:
                # Update metadata based on the model structure
                if hasattr(association, 'metadata'):
                    # If the model has a metadata column, update it directly
                    if isinstance(association.metadata, dict):
                        # Merge with existing metadata if it's a dict
                        association.metadata.update(metadata)
                    else:
                        # Otherwise replace it
                        association.metadata = metadata
                else:
                    # If the model doesn't have a metadata column, update individual columns
                    for key, value in metadata.items():
                        if hasattr(association, key):
                            setattr(association, key, value)
                        else:
                            logger.warning(f"Metadata key '{key}' not found in association model, skipping")
                
                # Update timestamp if available
                if hasattr(association, 'updated_at'):
                    association.updated_at = datetime.utcnow()
                
                session.commit()
                logger.info(f"Updated metadata for association between {left_id} and {right_id}")
                return association
            except Exception as e:
                logger.error(f"Failed to update association metadata: {str(e)}")
                raise
    
    def dissociate(self, left_id: Any, right_id: Any) -> bool:
        """
        Remove an association between two entities.
        
        Args:
            left_id: ID of the left entity
            right_id: ID of the right entity
            
        Returns:
            True if the association was removed, False if it didn't exist
            
        Raises:
            DatabaseError: If a database error occurs
        """
        with self._transaction() as session:
            try:
                stmt = delete(self.association_model).where(
                    and_(
                        getattr(self.association_model, self.left_fk_name) == left_id,
                        getattr(self.association_model, self.right_fk_name) == right_id
                    )
                )
                
                result = session.execute(stmt)
                session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Removed association between {left_id} and {right_id}")
                    return True
                else:
                    logger.info(f"No association found between {left_id} and {right_id}")
                    return False
            except Exception as e:
                logger.error(f"Failed to remove association: {str(e)}")
                raise
    
    def dissociate_all(
        self, 
        entity_id: Any, 
        side: Literal["left", "right"]
    ) -> int:
        """
        Remove all associations for a specific entity.
        
        Args:
            entity_id: ID of the entity
            side: Which side of the relationship the entity is on ("left" or "right")
            
        Returns:
            Number of associations removed
            
        Raises:
            InvalidInputError: If the side parameter is invalid
            DatabaseError: If a database error occurs
        """
        if side not in ["left", "right"]:
            raise InvalidInputError("Side must be either 'left' or 'right'")
        
        fk_name = self.left_fk_name if side == "left" else self.right_fk_name
        
        with self._transaction() as session:
            try:
                stmt = delete(self.association_model).where(
                    getattr(self.association_model, fk_name) == entity_id
                )
                
                result = session.execute(stmt)
                session.commit()
                
                count = result.rowcount
                logger.info(f"Removed {count} associations for entity {entity_id} on {side} side")
                return count
            except Exception as e:
                logger.error(f"Failed to remove associations: {str(e)}")
                raise
    
    def count_associations(
        self, 
        entity_id: Any, 
        side: Literal["left", "right"],
        filters: Optional[dict[str, Any]] = None
    ) -> int:
        """
        Count the number of associations for a specific entity.
        
        Args:
            entity_id: ID of the entity
            side: Which side of the relationship the entity is on ("left" or "right")
            filters: Optional dictionary of filters to apply to the query
            
        Returns:
            Number of associations
            
        Raises:
            InvalidInputError: If the side parameter is invalid
            DatabaseError: If a database error occurs
        """
        if side not in ["left", "right"]:
            raise InvalidInputError("Side must be either 'left' or 'right'")
        
        try:
            # Determine which foreign key to filter on based on the side
            fk_name = self.left_fk_name if side == "left" else self.right_fk_name
            
            # Build the query
            query = select(self.association_model).where(
                getattr(self.association_model, fk_name) == entity_id
            )
            
            # Add any additional filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.association_model, key):
                        query = query.where(getattr(self.association_model, key) == value)
            
            # Count the results
            count = self.db_session.execute(select(
                self.db_session.query(query.exists()).scalar()
            )).scalar()
            
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error while counting associations: {str(e)}")
            raise DatabaseError(f"Failed to count associations: {str(e)}") from e
    
    def bulk_associate(
        self, 
        associations: list[dict[str, Any]],
        validate_entities: bool = True
    ) -> list[Any]:
        """
        Create multiple associations in bulk.
        
        Args:
            associations: List of dictionaries with left_id, right_id, and optional metadata
            validate_entities: Whether to validate that entities exist before associating
            
        Returns:
            List of created association records
            
        Raises:
            InvalidInputError: If the input data is invalid
            EntityNotFoundError: If validate_entities is True and an entity doesn't exist
            DatabaseError: If a database error occurs
        """
        if not associations:
            return []
        
        # Validate input format
        for assoc in associations:
            if 'left_id' not in assoc or 'right_id' not in assoc:
                raise InvalidInputError("Each association must have left_id and right_id")
        
        # Validate entities if requested
        if validate_entities:
            left_ids = {assoc['left_id'] for assoc in associations}
            right_ids = {assoc['right_id'] for assoc in associations}
            
            # Check left entities
            for left_id in left_ids:
                self._validate_entity_exists(left_id, self.left_model, "Left entity")
            
            # Check right entities
            for right_id in right_ids:
                self._validate_entity_exists(right_id, self.right_model, "Right entity")
        
        created_associations = []
        with self._transaction() as session:
            try:
                for assoc in associations:
                    left_id = assoc['left_id']
                    right_id = assoc['right_id']
                    metadata = assoc.get('metadata')
                    
                    # Check if association already exists
                    existing = self.get_association(left_id, right_id)
                    if existing:
                        if metadata:
                            # Update metadata if provided
                            self.update_association_metadata(left_id, right_id, metadata)
                        created_associations.append(existing)
                        continue
                    
                    # Create association data
                    association_data = {
                        self.left_fk_name: left_id,
                        self.right_fk_name: right_id
                    }
                    
                    # Add metadata if provided
                    if metadata:
                        if hasattr(self.association_model, 'metadata'):
                            association_data['metadata'] = metadata
                        else:
                            # If the model doesn't have a metadata column, add each key as a separate column
                            for key, value in metadata.items():
                                if hasattr(self.association_model, key):
                                    association_data[key] = value
                    
                    association = self.association_model(**association_data)
                    session.add(association)
                    created_associations.append(association)
                
                session.commit()
                logger.info(f"Created {len(created_associations)} associations in bulk")
                return created_associations
            except Exception as e:
                logger.error(f"Failed to create associations in bulk: {str(e)}")
                raise
    
    def bulk_dissociate(
        self, 
        associations: list[dict[str, Any]]
    ) -> int:
        """
        Remove multiple associations in bulk.
        
        Args:
            associations: List of dictionaries with left_id and right_id
            
        Returns:
            Number of associations removed
            
        Raises:
            InvalidInputError: If the input data is invalid
            DatabaseError: If a database error occurs
        """
        if not associations:
            return 0
        
        # Validate input format
        for assoc in associations:
            if 'left_id' not in assoc or 'right_id' not in assoc:
                raise InvalidInputError("Each association must have left_id and right_id")
        
        with self._transaction() as session:
            try:
                removed_count = 0
                for assoc in associations:
                    left_id = assoc['left_id']
                    right_id = assoc['right_id']
                    
                    stmt = delete(self.association_model).where(
                        and_(
                            getattr(self.association_model, self.left_fk_name) == left_id,
                            getattr(self.association_model, self.right_fk_name) == right_id
                        )
                    )
                    
                    result = session.execute(stmt)
                    removed_count += result.rowcount
                
                session.commit()
                logger.info(f"Removed {removed_count} associations in bulk")
                return removed_count
            except Exception as e:
                logger.error(f"Failed to remove associations in bulk: {str(e)}")
                raise