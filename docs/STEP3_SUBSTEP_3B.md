
# NeuroCognitive Architecture (NCA) - File Templates and Conventions

This document defines the file templates, naming conventions, and organization rules for the NeuroCognitive Architecture (NCA) project. These standards ensure consistency, maintainability, and scalability across the codebase.

## 1. Core File Templates

### 1.1. Python Module Template

All Python modules should follow this basic structure:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module: {module_name}
Description: {brief description}

This module {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

# Standard library imports
import os
import sys
from typing import Dict, List, Optional, Union, Any

# Third-party imports
import numpy as np
import redis

# Local application imports
from neuroca.domain.models import MemoryItem
from neuroca.infrastructure.persistence import Repository

# Constants
MAX_ITEMS = 100
DEFAULT_TIMEOUT = 60  # seconds

# Module-level variables
_cache = {}


class SomeClass:
    """
    A class that represents {description}.

    Attributes:
        attr1 (type): Description of attr1.
        attr2 (type): Description of attr2.
    """

    def __init__(self, param1: str, param2: int = 10):
        """
        Initialize the class.

        Args:
            param1: Description of param1
            param2: Description of param2, defaults to 10
        """
        self.attr1 = param1
        self.attr2 = param2
        self._private_attr = None

    def public_method(self, arg1: str) -> Dict[str, Any]:
        """
        Do something and return a result.

        Args:
            arg1: Description of arg1

        Returns:
            A dictionary containing the results

        Raises:
            ValueError: If arg1 is empty
        """
        if not arg1:
            raise ValueError("arg1 cannot be empty")
        
        # Method implementation
        result = {"status": "success", "data": arg1}
        return result

    def _private_method(self):
        """Internal helper method."""
        pass


def main():
    """Main function executed when module is run directly."""
    instance = SomeClass("example", 42)
    result = instance.public_method("test")
    print(result)


if __name__ == "__main__":
    main()
```

### 1.2. Python Interface/Abstract Class Template

```python
"""
Module: {interface_name}
Description: Interface definition for {component}

This module defines the interface for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class SomeInterface(ABC):
    """
    Interface for {description}.
    
    This interface defines the contract that all implementations must follow.
    """

    @abstractmethod
    def method_one(self, param1: str) -> Dict[str, Any]:
        """
        Description of what method_one does.

        Args:
            param1: Description of param1

        Returns:
            A dictionary containing the results

        Raises:
            ValueError: If param1 is invalid
        """
        pass

    @abstractmethod
    def method_two(self, param1: int, param2: Optional[str] = None) -> List[Any]:
        """
        Description of what method_two does.

        Args:
            param1: Description of param1
            param2: Description of param2, defaults to None

        Returns:
            A list containing the results
        """
        pass
```

### 1.3. Python Implementation Class Template

```python
"""
Module: {implementation_name}
Description: Implementation of {interface} for {specific use case}

This module implements {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

from typing import Dict, List, Optional, Any
import logging

from neuroca.domain.interfaces import SomeInterface

# Configure logger
logger = logging.getLogger(__name__)


class ConcreteImplementation(SomeInterface):
    """
    Implementation of SomeInterface for {specific use case}.
    
    This class provides a concrete implementation of the SomeInterface
    for {detailed description of the specific use case}.
    
    Attributes:
        attr1 (type): Description of attr1.
        attr2 (type): Description of attr2.
    """

    def __init__(self, dependency1, dependency2):
        """
        Initialize the implementation.

        Args:
            dependency1: First dependency
            dependency2: Second dependency
        """
        self._dependency1 = dependency1
        self._dependency2 = dependency2
        logger.debug("Initialized ConcreteImplementation")

    def method_one(self, param1: str) -> Dict[str, Any]:
        """
        Implementation of method_one.

        Args:
            param1: Description of param1

        Returns:
            A dictionary containing the results

        Raises:
            ValueError: If param1 is invalid
        """
        logger.debug(f"method_one called with param1={param1}")
        
        if not param1:
            logger.error("Invalid param1: empty string")
            raise ValueError("param1 cannot be empty")
            
        # Implementation logic
        result = self._dependency1.process(param1)
        return {"status": "success", "data": result}

    def method_two(self, param1: int, param2: Optional[str] = None) -> List[Any]:
        """
        Implementation of method_two.

        Args:
            param1: Description of param1
            param2: Description of param2, defaults to None

        Returns:
            A list containing the results
        """
        logger.debug(f"method_two called with param1={param1}, param2={param2}")
        
        # Implementation logic
        results = self._dependency2.query(param1, additional_info=param2)
        return list(results)
```

### 1.4. Python Data Model Template

```python
"""
Module: {model_name}
Description: Data model for {entity}

This module defines the data model for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


@dataclass
class SomeModel:
    """
    Data model representing {entity}.
    
    This class defines the structure and behavior of {entity} in the system.
    
    Attributes:
        id (UUID): Unique identifier
        name (str): Name of the entity
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
        metadata (Dict): Additional metadata
    """
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update(self, **kwargs):
        """
        Update the model with new values.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SomeModel':
        """
        Create a model instance from a dictionary.
        
        Args:
            data: Dictionary containing model data
            
        Returns:
            New model instance
        """
        # Handle conversion of string ID to UUID
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])
            
        # Handle conversion of string timestamps to datetime
        for field_name in ["created_at", "updated_at"]:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
                
        return cls(**data)
```

### 1.5. Python Repository Interface Template

```python
"""
Module: {repository_interface_name}
Description: Repository interface for {entity}

This module defines the repository interface for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from uuid import UUID

from neuroca.domain.models import SomeModel


class SomeRepository(ABC):
    """
    Repository interface for {entity}.
    
    This interface defines the data access operations for {entity}.
    """

    @abstractmethod
    async def create(self, item: SomeModel) -> SomeModel:
        """
        Create a new item.
        
        Args:
            item: The item to create
            
        Returns:
            The created item with any generated fields
            
        Raises:
            RepositoryError: If the item cannot be created
        """
        pass
    
    @abstractmethod
    async def get(self, item_id: UUID) -> Optional[SomeModel]:
        """
        Get an item by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, item: SomeModel) -> SomeModel:
        """
        Update an existing item.
        
        Args:
            item: The item to update
            
        Returns:
            The updated item
            
        Raises:
            RepositoryError: If the item cannot be updated
            ItemNotFoundError: If the item does not exist
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: UUID) -> bool:
        """
        Delete an item by ID.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the item was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def list(self, filters: Optional[Dict[str, Any]] = None, 
                  limit: int = 100, offset: int = 0) -> List[SomeModel]:
        """
        List items with optional filtering.
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            List of items matching the criteria
        """
        pass
```

### 1.6. Python Repository Implementation Template

```python
"""
Module: {repository_implementation_name}
Description: {database} implementation of repository for {entity}

This module implements the repository for {detailed description} using {database}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from neuroca.domain.models import SomeModel
from neuroca.domain.repositories import SomeRepository
from neuroca.domain.exceptions import RepositoryError, ItemNotFoundError

# Configure logger
logger = logging.getLogger(__name__)


class SomeDatabaseRepository(SomeRepository):
    """
    {Database} implementation of SomeRepository.
    
    This class provides a concrete implementation of the SomeRepository
    interface using {database}.
    """

    def __init__(self, db_client):
        """
        Initialize the repository.
        
        Args:
            db_client: Database client
        """
        self._db_client = db_client
        self._collection = db_client.get_collection("some_collection")
        logger.debug("Initialized SomeDatabaseRepository")
    
    async def create(self, item: SomeModel) -> SomeModel:
        """
        Create a new item in the database.
        
        Args:
            item: The item to create
            
        Returns:
            The created item with any generated fields
            
        Raises:
            RepositoryError: If the item cannot be created
        """
        try:
            logger.debug(f"Creating item: {item.id}")
            item_dict = item.to_dict()
            result = await self._collection.insert_one(item_dict)
            
            if not result.acknowledged:
                raise RepositoryError("Failed to create item")
                
            return item
        except Exception as e:
            logger.error(f"Error creating item: {str(e)}")
            raise RepositoryError(f"Failed to create item: {str(e)}")
    
    async def get(self, item_id: UUID) -> Optional[SomeModel]:
        """
        Get an item by ID from the database.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item if found, None otherwise
        """
        try:
            logger.debug(f"Getting item: {item_id}")
            result = await self._collection.find_one({"id": str(item_id)})
            
            if not result:
                return None
                
            return SomeModel.from_dict(result)
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {str(e)}")
            return None
    
    async def update(self, item: SomeModel) -> SomeModel:
        """
        Update an existing item in the database.
        
        Args:
            item: The item to update
            
        Returns:
            The updated item
            
        Raises:
            RepositoryError: If the item cannot be updated
            ItemNotFoundError: If the item does not exist
        """
        try:
            logger.debug(f"Updating item: {item.id}")
            item_dict = item.to_dict()
            result = await self._collection.update_one(
                {"id": str(item.id)},
                {"$set": item_dict}
            )
            
            if result.matched_count == 0:
                raise ItemNotFoundError(f"Item with ID {item.id} not found")
                
            if result.modified_count == 0:
                logger.warning(f"Item {item.id} was not modified")
                
            return item
        except ItemNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating item {item.id}: {str(e)}")
            raise RepositoryError(f"Failed to update item: {str(e)}")
    
    async def delete(self, item_id: UUID) -> bool:
        """
        Delete an item by ID from the database.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the item was deleted, False otherwise
        """
        try:
            logger.debug(f"Deleting item: {item_id}")
            result = await self._collection.delete_one({"id": str(item_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {str(e)}")
            return False
    
    async def list(self, filters: Optional[Dict[str, Any]] = None, 
                  limit: int = 100, offset: int = 0) -> List[SomeModel]:
        """
        List items with optional filtering from the database.
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            List of items matching the criteria
        """
        try:
            logger.debug(f"Listing items with filters: {filters}")
            query = filters or {}
            cursor = self._collection.find(query).skip(offset).limit(limit)
            results = await cursor.to_list(length=limit)
            return [SomeModel.from_dict(item) for item in results]
        except Exception as e:
            logger.error(f"Error listing items: {str(e)}")
            return []
```

### 1.7. Python Service Template

```python
"""
Module: {service_name}
Description: Service for {functionality}

This module implements the service for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from neuroca.domain.models import SomeModel
from neuroca.domain.repositories import SomeRepository
from neuroca.domain.exceptions import ServiceError, ValidationError

# Configure logger
logger = logging.getLogger(__name__)


class SomeService:
    """
    Service for {functionality}.
    
    This class provides business logic for {functionality}.
    """

    def __init__(self, repository: SomeRepository, other_dependency=None):
        """
        Initialize the service.
        
        Args:
            repository: Repository for data access
            other_dependency: Other dependency
        """
        self._repository = repository
        self._other_dependency = other_dependency
        logger.debug("Initialized SomeService")
    
    async def create_item(self, data: Dict[str, Any]) -> SomeModel:
        """
        Create a new item.
        
        Args:
            data: Item data
            
        Returns:
            The created item
            
        Raises:
            ValidationError: If the data is invalid
            ServiceError: If the item cannot be created
        """
        try:
            logger.info("Creating new item")
            
            # Validate input data
            self._validate_item_data(data)
            
            # Create model instance
            item = SomeModel(
                name=data["name"],
                description=data.get("description"),
                metadata=data.get("metadata", {})
            )
            
            # Additional business logic
            if self._other_dependency:
                await self._other_dependency.process(item)
            
            # Save to repository
            created_item = await self._repository.create(item)
            logger.info(f"Created item with ID: {created_item.id}")
            
            return created_item
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating item: {str(e)}")
            raise ServiceError(f"Failed to create item: {str(e)}")
    
    async def get_item(self, item_id: UUID) -> Optional[SomeModel]:
        """
        Get an item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            The item if found, None otherwise
        """
        try:
            logger.info(f"Getting item with ID: {item_id}")
            return await self._repository.get(item_id)
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {str(e)}")
            return None
    
    async def update_item(self, item_id: UUID, data: Dict[str, Any]) -> SomeModel:
        """
        Update an existing item.
        
        Args:
            item_id: Item ID
            data: Updated item data
            
        Returns:
            The updated item
            
        Raises:
            ValidationError: If the data is invalid
            ServiceError: If the item cannot be updated
            ItemNotFoundError: If the item does not exist
        """
        try:
            logger.info(f"Updating item with ID: {item_id}")
            
            # Get existing item
            item = await self._repository.get(item_id)
            if not item:
                raise ItemNotFoundError(f"Item with ID {item_id} not found")
            
            # Validate input data
            self._validate_item_data(data, update=True)
            
            # Update model
            item.update(**data)
            
            # Additional business logic
            if self._other_dependency:
                await self._other_dependency.process(item)
            
            # Save to repository
            updated_item = await self._repository.update(item)
            logger.info(f"Updated item with ID: {updated_item.id}")
            
            return updated_item
        except (ValidationError, ItemNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error updating item {item_id}: {str(e)}")
            raise ServiceError(f"Failed to update item: {str(e)}")
    
    def _validate_item_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """
        Validate item data.
        
        Args:
            data: Data to validate
            update: Whether this is an update operation
            
        Raises:
            ValidationError: If the data is invalid
        """
        if not update and "name" not in data:
            raise ValidationError("Name is required")
            
        if "name" in data and not data["name"]:
            raise ValidationError("Name cannot be empty")
            
        if "metadata" in data and not isinstance(data["metadata"], dict):
            raise ValidationError("Metadata must be a dictionary")
```

### 1.8. Python API Controller Template

```python
"""
Module: {controller_name}
Description: API controller for {resource}

This module implements the API controller for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel, Field

from neuroca.application.services import SomeService
from neuroca.domain.exceptions import ValidationError, ServiceError, ItemNotFoundError
from neuroca.api.dependencies import get_some_service

# Configure logger
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(prefix="/some-resource", tags=["Some Resource"])

# Define request/response models
class ItemCreate(BaseModel):
    """Request model for creating an item."""
    name: str = Field(..., description="Name of the item", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description of the item")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ItemUpdate(BaseModel):
    """Request model for updating an item."""
    name: Optional[str] = Field(None, description="Name of the item", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description of the item")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ItemResponse(BaseModel):
    """Response model for an item."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the item")
    description: Optional[str] = Field(None, description="Description of the item")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class ItemListResponse(BaseModel):
    """Response model for a list of items."""
    items: List[ItemResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Maximum number of items returned")
    offset: int = Field(..., description="Number of items skipped")


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    service: SomeService = Depends(get_some_service)
):
    """
    Create a new item.
    
    Args:
        item: Item data
        service: Injected service
        
    Returns:
        The created item
        
    Raises:
        HTTPException: If the item cannot be created
    """
    try:
        logger.info("API request to create item")
        created_item = await service.create_item(item.dict())
        return created_item.to_dict()
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create item"
        )

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: UUID = Path(..., description="Item ID"),
    service: SomeService = Depends(get_some_service)
):
    """
    Get an item by ID.
    
    Args:
        item_id: Item ID
        service: Injected service
        
    Returns:
        The item
        
    Raises:
        HTTPException: If the item is not found
    """
    logger.info(f"API request to get item {item_id}")
    item = await service.get_item(item_id)
    
    if not item:
        logger.warning(f"Item {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
        
    return item.to_dict()

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item: ItemUpdate,
    item_id: UUID = Path(..., description="Item ID"),
    service: SomeService = Depends(get_some_service)
):
    """
    Update an item.
    
    Args:
        item: Updated item data
        item_id: Item ID
        service: Injected service
        
    Returns:
        The updated item
        
    Raises:
        HTTPException: If the item cannot be updated
    """
    try:
        logger.info(f"API request to update item {item_id}")
        updated_item = await service.update_item(item_id, item.dict(exclude_unset=True))
        return updated_item.to_dict()
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ItemNotFoundError:
        logger.warning(f"Item {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    except ServiceError as e:
        logger.error(f"Service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update item"
        )

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID = Path(..., description="Item ID"),
    service: SomeService = Depends(get_some_service)
):
    """
    Delete an item.
    
    Args:
        item_id: Item ID
        service: Injected service
        
    Raises:
        HTTPException: If the item cannot be deleted
    """
    logger.info(f"API request to delete item {item_id}")
    deleted = await service.delete_item(item_id)
    
    if not deleted:
        logger.warning(f"Item {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

@router.get("/", response_model=ItemListResponse)
async def list_items(
    limit: int = Query(100, description="Maximum number of items to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of items to skip", ge=0),
    name: Optional[str] = Query(None, description="Filter by name"),
    service: SomeService = Depends(get_some_service)
):
    """
    List items with optional filtering.
    
    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip
        name: Filter by name
        service: Injected service
        
    Returns:
        List of items matching the criteria
    """
    logger.info(f"API request to list items (limit={limit}, offset={offset})")
    
    # Build filters
    filters = {}
    if name:
        filters["name"] = name
    
    items, total = await service.list_items(filters, limit, offset)
    
    return {
        "items": [item.to_dict() for item in items],
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

### 1.9. Python Exception Template

```python
"""
Module: {exceptions_module_name}
Description: Exception definitions for {component}

This module defines the exceptions for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

class BaseError(Exception):
    """Base class for all exceptions in the application."""
    pass


class ValidationError(BaseError):
    """Exception raised for validation errors."""
    pass


class ServiceError(BaseError):
    """Exception raised for service-level errors."""
    pass


class RepositoryError(BaseError):
    """Exception raised for repository-level errors."""
    pass


class ItemNotFoundError(RepositoryError):
    """Exception raised when an item is not found."""
    pass


class AuthenticationError(BaseError):
    """Exception raised for authentication errors."""
    pass


class AuthorizationError(BaseError):
    """Exception raised for authorization errors."""
    pass


class ConfigurationError(BaseError):
    """Exception raised for configuration errors."""
    pass


class IntegrationError(BaseError):
    """Exception raised for integration errors."""
    pass


class LLMProviderError(IntegrationError):
    """Exception raised for LLM provider errors."""
    pass


class DatabaseError(IntegrationError):
    """Exception raised for database errors."""
    pass


class TimeoutError(IntegrationError):
    """Exception raised for timeout errors."""
    pass
```

### 1.10. Python Configuration Template

```python
"""
Module: {config_module_name}
Description: Configuration for {component}

This module defines the configuration for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)


class Configuration:
    """
    Configuration manager for the application.
    
    This class loads and provides access to configuration settings.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration.
        
        Args:
            config_path: Path to configuration file, defaults to environment variable or standard location
        """
        self._config_path = config_path or os.getenv(
            "NEUROCA_CONFIG_PATH", 
            f"config/{os.getenv('ENVIRONMENT', 'development')}/app.yaml"
        )
        self._config = {}
        self._load_config()
        logger.debug(f"Initialized configuration from {self._config_path}")
    
    def _load_config(self):
        """
        Load configuration from file.
        
        Raises:
            ConfigurationError: If the configuration file cannot be loaded
        """
        try:
            config_file = Path(self._config_path)
            
            if not config_file.exists():
                logger.warning(f"Configuration file not found: {self._config_path}")
                return
                
            with open(config_file, "r") as f:
                self._config = yaml.safe_load(f)
                
            logger.info(f"Loaded configuration from {self._config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (dot notation for nested keys)
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def get_required(self, key: str) -> Any:
        """
        Get a required configuration value.
        
        Args:
            key: Configuration key (dot notation for nested keys)
            
        Returns:
            Configuration value
            
        Raises:
            ConfigurationError: If the key is not found
        """
        value = self.get(key)
        
        if value is None:
            raise ConfigurationError(f"Required configuration key not found: {key}")
            
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of all configuration values
        """
        return self._config.copy()


# Singleton instance
config = Configuration()
```

### 1.11. Python Test Template

```python
"""
Module: {test_module_name}
Description: Tests for {component}

This module contains tests for {detailed description}

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from neuroca.domain.models import SomeModel
from neuroca.domain.exceptions import ValidationError


class TestSomeComponent:
    """Tests for SomeComponent."""
    
    @pytest.fixture
    def mock_dependency(self):
        """Fixture for mock dependency."""
        return AsyncMock()
    
    @pytest.fixture
    def component(self, mock_dependency):
        """Fixture for component under test."""
        from neuroca.domain.services import SomeComponent
        return SomeComponent(mock_dependency)
    
    @pytest.fixture
    def sample_data(self):
        """Fixture for sample data."""
        return {
            "id": str(uuid4()),
            "name": "Test Item",
            "description": "Test Description",
            "metadata": {"key": "value"}
        }
    
    @pytest.mark.asyncio
    async def test_create_item_success(self, component, mock_dependency, sample_data):
        """Test successful item creation."""
        # Arrange
        mock_dependency.process.return_value = AsyncMock()
        
        # Act
        result = await component.create_item(sample_data)
        
        # Assert
        assert result is not None
        assert result.name == sample_data["name"]
        assert result.description == sample_data["description"]
        mock_dependency.process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_item_validation_error(self, component):
        """Test validation error during item creation."""
        # Arrange
        invalid_data = {"description": "Missing name"}
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await component.create_item(invalid_data)
    
    @pytest.mark.asyncio
    async def test_get_item_success(self, component, mock_dependency, sample_data):
        """Test successful item retrieval."""
        # Arrange
        item_id = uuid4()
        mock_item = SomeModel(
            id=item_id,
            name=sample_data["name"],
            description=sample_data["description"],
            metadata=sample_data["metadata"]
        )
        mock_dependency.get_item.return_value = mock_item
        
        # Act
        result = await component.get_item(item_id)
        
        # Assert
        assert result is not None
        assert result.id == item_id
        assert result.name == sample_data["name"]
        mock_dependency.get_item.assert_called_once_with(item_id)
    
    @pytest.mark.asyncio
    async def test_get_item_not_found(self, component, mock_dependency):
        """Test item not found during retrieval."""
        # Arrange
        item_id = uuid4()
        mock_dependency.get_item.return_value = None
        
        # Act
        result = await component.get_item(item_id)
        
        # Assert
        assert result is None
        mock_dependency.get_item.assert_called_once_with(item_id)
```

### 1.12. Docker Compose Template

```yaml
version: '3.8'

services:
  # API Service
  api:
    build:
      context: .
      dockerfile: deploy/docker/Dockerfile
      target: development
    image: neuroca-api:dev
    container_name: neuroca-api
    restart: unless-stopped
    depends_on:
      - redis
      - mongodb
      - postgres
    environment:
      - ENVIRONMENT=development
      - NEUROCA_CONFIG_PATH=/app/config/development/app.yaml
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - MONGODB_URI=mongodb://mongodb:27017/neuroca
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    command: uvicorn neuroca.api.main:app --host 0.0.0.0 --port 8000 --reload

  # Worker Service
  worker:
    build:
      context: .
      dockerfile: deploy/docker/Dockerfile
      target: development
    image: neuroca-worker:dev
    container_name: neuroca-worker
    restart: unless-stopped
    depends_on:
      - redis
      - mongodb
      - postgres
    environment:
      - ENVIRONMENT=development
      - NEUROCA_CONFIG_PATH=/app/config/development/app.yaml
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - MONGODB_URI=mongodb://mongodb:27017/neuroca
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - .:/app
    command: celery -A neuroca.infrastructure.tasks.worker worker --loglevel=info

  # Redis (STM)
  redis:
    image: redis:7-alpine
    container_name: neuroca-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  # MongoDB (MTM)
  mongodb:
    image: mongo:6
    container_name: neuroca-mongodb
    restart: unless-stopped
    environment:
      - MONGO_INITDB_DATABASE=neuroca
    ports:
      - "27017:27017"
    volumes:
      - mongodb-data:/data/db

  # PostgreSQL (LTM)
  postgres:
    image: ankane/pgvector:latest
    container_name: neuroca-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  redis-data:
  mongodb-data:
  postgres-data:
```

### 1.13. Dockerfile Template

```dockerfile
# Base image
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Development image
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Production image
FROM base AS production

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run as non-root user
RUN useradd -m neuroca
USER neuroca

# Command
CMD ["uvicorn", "neuroca.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.14. YAML Configuration Template

```yaml
# Application configuration
app:
  name: NeuroCognitive Architecture
  version: 0.1.0
  description: Brain-inspired three-tiered memory system for LLMs
  environment: development
  debug: true
  log_level: debug

# API configuration
api:
  host: 0.0.0.0
  port: 8000
  cors:
    allowed_origins:
      - http://localhost:3000
      - https://app.example.com
    allowed_methods:
      - GET
      - POST
      - PUT
      - DELETE
    allowed_headers:
      - Authorization
      - Content-Type
  rate_limiting:
    enabled: true
    rate: 100
    period: 60

# Memory configuration
memory:
  # Short-Term Memory configuration
  stm:
    provider: redis
    ttl: 10800  # 3 hours in seconds
    max_items: 1000
    health:
      base_score: 80
      decay_rate: 0.1
      promotion_threshold: 90
      demotion_threshold: 30
    connection:
      host: ${REDIS_HOST:-localhost}
      port: ${REDIS_PORT:-6379}
      db: 0
      password: ${REDIS_PASSWORD:-}

  # Medium-Term Memory configuration
  mtm:
    provider: mongodb
    ttl: 1209600  # 14 days in seconds
    max_items: 10000
    health:
      base_score: 60
      decay_rate: 0.05
      promotion_threshold: 80
      demotion_threshold: 20
    connection:
      uri: ${MONGODB_URI:-mongodb://localhost:27017/neuroca}
      database: neuroca
      collection: mtm_memories

  # Long-Term Memory configuration
  ltm:
    provider: postgres
    ttl: null  # No expiration
    max_items: 100000
    health:
      base_score: 40
      decay_rate: 0.01
      promotion_threshold: 70
      demotion_threshold: 10
    connection:
      host: ${POSTGRES_HOST:-localhost}
      port: ${POSTGRES_PORT:-5432}
      database: ${POSTGRES_DB:-neuroca}
      user: ${POSTGRES_USER:-postgres}
      password: ${POSTGRES_PASSWORD:-postgres}

# Advanced components configuration
components:
  # Lymphatic System configuration
  lymphatic:
    enabled: true
    consolidation_interval: 3600  # 1 hour in seconds
    batch_size: 100
    max_concurrent_tasks: 5

  # Neural Tubules configuration
  neural_tubules:
    enabled: true
    connection_strength_threshold: 0.5
    max_connections_per_memory: 50
    reinforcement_factor: 0.1

  # Temporal Annealing configuration
  temporal_annealing:
    enabled: true
    schedule:
      - phase: fast
        interval: 300  # 5 minutes in seconds
        intensity: 0.2
      - phase: medium
        interval: 3600  # 1 hour in seconds
        intensity: 0.5
      - phase: slow
        interval: 86400  # 24 hours in seconds
        intensity: 1.0

# LLM integration configuration
llm:
  default_provider: openai
  context_window_size: 4096
  max_tokens: 1000
  providers:
    openai:
      api_key: ${OPENAI_API_KEY:-}
      model: gpt-4
      temperature: 0.7
      timeout: 30
    anthropic:
      api_key: ${ANTHROPIC_API_KEY:-}
      model: claude-2
      temperature: 0.7
      timeout: 30

# Security configuration
security:
  jwt:
    secret_key: ${JWT_SECRET_KEY:-change_this_in_production}
    algorithm: HS256
    access_token_expire_minutes: 30
  encryption:
    enabled: true
    algorithm: AES-256-GCM
    key_rotation_days: 30

# Monitoring configuration
monitoring:
  metrics:
    enabled: true
    prometheus:
      enabled: true
      port: 9090
  logging:
    level: ${LOG_LEVEL:-info}
    format: json
    output:
      console: true
      file: false
  tracing:
    enabled: true
    sampling_rate: 0.1
```

## 2. File Naming Conventions

### 2.1. General Naming Conventions

1. **Use lowercase for all filenames** - Ensures consistency across different operating systems
   - Example: `memory_manager.py` instead of `MemoryManager.py`

2. **Use underscores for word separation** - Python convention for file names
   - Example: `short_term_memory.py` instead of `shortTermMemory.py` or `short-term-memory.py`

3. **Be descriptive but concise** - Names should clearly indicate the file's purpose
   - Example: `redis_stm_repository.py` instead of `redis_repo.py` or `short_term_memory_repository_redis_implementation.py`

4. **Avoid special characters** - Use only alphanumeric characters and underscores
   - Example: `health_calculator.py` instead of `health-calculator.py` or `health_calculator!.py`

5. **Avoid generic names** - Names should be specific enough to understand the file's purpose
   - Example: `memory_health_service.py` instead of `service.py` or `handler.py`

### 2.2. Python File Naming Conventions

1. **Module files** - Use descriptive nouns or noun phrases
   - Example: `memory_item.py`, `health_calculator.py`

2. **Package initialization** - Always use `__init__.py`
   - Example: `neuroca/domain/models/__init__.py`

3. **Interface files** - Use the suffix `_interface` or `_abc` (abstract base class)
   - Example: `repository_interface.py`, `memory_service_abc.py`

4. **Implementation files** - Include the implementation technology or pattern
   - Example: `redis_stm_repository.py`, `postgres_ltm_repository.py`

5. **Test files** - Prefix with `test_` followed by the name of the module being tested
   - Example: `test_memory_manager.py`, `test_health_calculator.py`

6. **Configuration files** - Use the suffix `_config` or `_settings`
   - Example: `app_config.py`, `logging_settings.py`

### 2.3. API Endpoint Naming Conventions

1. **Controller files** - Use the suffix `_controller` or `_router`
   - Example: `memory_controller.py`, `health_router.py`

2. **Schema files** - Use the suffix `_schema`
   - Example: `memory_schema.py`, `health_schema.py`

3. **Middleware files** - Use the suffix `_middleware`
   - Example: `authentication_middleware.py`, `logging_middleware.py`

### 2.4. Database Migration Naming Conventions

1. **Migration files** - Use a timestamp prefix followed by a descriptive name
   - Example: `20230915123045_create_memory_tables.py`, `20230916084512_add_health_index.py`

### 2.5. Configuration File Naming Conventions

1. **Environment-specific configuration** - Use the environment name as a prefix
   - Example: `development_app.yaml`, `production_app.yaml`

2. **Component-specific configuration** - Use the component name as a prefix
   - Example: `memory_config.yaml`, `security_config.yaml`

### 2.6. Documentation File Naming Conventions

1. **Markdown files** - Use descriptive names with `.md` extension
   - Example: `architecture_overview.md`, `api_documentation.md`

2. **API documentation** - Use the prefix `api_` followed by the resource name
   - Example: `api_memory.md`, `api_health.md`

## 3. File Organization Rules

### 3.1. Module Organization

1. **One class per file** - Each significant class should be in its own file
   - Exception: Small helper classes or closely related classes can be in the same file

2. **Group related files in packages** - Use packages to organize related files
   - Example: All repository interfaces in `neuroca/domain/repositories/`

3. **Use `__init__.py` for package exports** - Control what is exported from packages
   ```python
   # neuroca/domain/models/__init__.py
   from .memory_item import MemoryItem
   from .health_metadata import HealthMetadata
   
   __all__ = ['MemoryItem', 'HealthMetadata']
   ```

4. **Separate interfaces from implementations** - Keep interfaces in the domain layer and implementations in the infrastructure layer
   - Example: `neuroca/domain/repositories/memory_repository.py` and `neuroca/infrastructure/persistence/redis/redis_stm_repository.py`

### 3.2. Import Organization

1. **Group imports by source** - Standard library, third-party, and local application imports
   ```python
   # Standard library imports
   import os
   import sys
   from typing import Dict, List
   
   # Third-party imports
   import numpy as np
   import redis
   
   # Local application imports
   from neuroca.domain.models import MemoryItem
   from neuroca.infrastructure.persistence import Repository
   ```

2. **Sort imports alphabetically within groups** - Makes it easier to find imports
   ```python
   # Standard library imports
   import os
   import sys
   from datetime import datetime
   from typing import Dict, List
   from uuid import UUID
   ```

3. **Use absolute imports** - Prefer absolute imports over relative imports
   ```python
   # Preferred
   from neuroca.domain.models import MemoryItem
   
   # Avoid
   from ...domain.models import MemoryItem
   ```

4. **Import specific classes/functions** - Avoid wildcard imports
   ```python
   # Preferred
   from neuroca.domain.models import MemoryItem, HealthMetadata
   
   # Avoid
   from neuroca.domain.models import *
   ```

### 3.3. Code Organization Within Files

1. **Order of elements** - Follow a consistent order for elements within a file
   ```
   1. Module docstring
   2. Imports
   3. Constants
   4. Module-level variables
   5. Classes
   6. Functions
   7. Main execution block
   ```

2. **Class organization** - Follow a consistent order for elements within a class
   ```
   1. Class docstring
   2. Class attributes
   3. Constructor (__init__)
   4. Properties
   5. Public methods
   6. Protected methods (prefixed with _)
   7. Private methods (prefixed with __)
   8. Static methods
   9. Class methods
   10. Magic methods (e.g., __str__, __eq__)
   ```

3. **Group related methods** - Keep related methods together
   ```python
   # CRUD methods
   def create(self):
       pass
       
   def read(self):
       pass
       
   def update(self):
       pass
       
   def delete(self):
       pass
       
   # Query methods
   def find_by_name(self):
       pass
       
   def find_by_date(self):
       pass
   ```

### 3.4. Configuration Organization

1. **Environment-based configuration** - Organize configuration by environment
   ```
   config/
   ├── development/
   │   ├── app.yaml
   │   ├── logging.yaml
   │   └── security.yaml
   ├── testing/
   │   ├── app.yaml
   │   ├── logging.yaml
   │   └── security.yaml
   └── production/
       ├── app.yaml
       ├── logging.yaml
       └── security.yaml
   ```

2. **Component-based configuration** - Organize configuration by component within each environment
   ```yaml
   # app.yaml
   memory:
     stm:
       # STM configuration
     mtm:
       # MTM configuration
     ltm:
       # LTM configuration
   
   security:
     # Security configuration
   
   logging:
     # Logging configuration
   ```

### 3.5. Test Organization

1. **Mirror the source structure** - Organize tests to mirror the source code structure
   ```
   src/
   ├── domain/
   │   └── models/
   │       └── memory_item.py
   
   tests/
   ├── unit/
   │   └── domain/
   │       └── models/
   │           └── test_memory_item.py
   ```

2. **Group tests by type** - Separate unit, integration, and system tests
   ```
   tests/
   ├── unit/
   │   └── domain/
   ├── integration/
   │   └── infrastructure/
   └── system/
       └── api/
   ```

3. **Test class organization** - Organize test methods within a test class
   ```python
   class TestMemoryItem:
       # Setup and teardown
       @pytest.fixture
       def sample_item(self):
           pass
       
       # Constructor tests
       def test_init_with_valid_data(self):
           pass
           
       def test_init_with_invalid_data(self):
           pass
       
       # Method tests
       def test_update_health(self):
           pass
           
       def test_calculate_relevance(self):
           pass
   ```

## 4. Example Files

### 4.1. Domain Model Example: `src/domain/models/memory_item.py`

```python
"""
Module: memory_item
Description: Memory item model

This module defines the memory item model, which is the core data structure
for storing memories in the NeuroCognitive Architecture.

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class MemoryTier(Enum):
    """Enumeration of memory tiers."""
    STM = "short_term_memory"
    MTM = "medium_term_memory"
    LTM = "long_term_memory"


@dataclass
class HealthMetadata:
    """
    Health metadata for a memory item.
    
    This class stores the health-related metadata for a memory item,
    which is used to determine the memory's lifecycle.
    
    Attributes:
        base_score: Base health score (0-100)
        relevance_score: Relevance score (0-100)
        last_accessed: Last access timestamp
        access_count: Number of times the memory has been accessed
        importance: Importance flag (0-10)
        tags: Content type tags
        embedding: Semantic embedding vector
    """
    base_score: float = 50.0
    relevance_score: float = 50.0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    importance: int = 5
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    
    def calculate_health(self) -> float:
        """
        Calculate the overall health score.
        
        Returns:
            Overall health score (0-100)
        """
        # Simple weighted average for demonstration
        now = datetime.utcnow()
        recency_factor = 1.0 - min(1.0, (now - self.last_accessed).total_seconds() / (24 * 3600))
        
        # Weighted components
        base_component = self.base_score * 0.4
        relevance_component = self.relevance_score * 0.3
        recency_component = recency_factor * 100 * 0.2
        importance_component = (self.importance / 10) * 100 * 0.1
        
        # Overall health score
        health_score = base_component + relevance_component + recency_component + importance_component
        
        return min(100.0, max(0.0, health_score))
    
    def update_access(self):
        """Update the access metadata."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


@dataclass
class MemoryItem:
    """
    Memory item model.
    
    This class represents a memory item in the NeuroCognitive Architecture.
    
    Attributes:
        id: Unique identifier
        content: Memory content
        tier: Memory tier (STM, MTM, LTM)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        health: Health metadata
        metadata: Additional metadata
        related_memories: IDs of related memories
    """
    content: str
    tier: MemoryTier = MemoryTier.STM
    health: HealthMetadata = field(default_factory=HealthMetadata)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_memories: List[UUID] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update(self, **kwargs):
        """
        Update the memory item with new values.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def access(self):
        """
        Record an access to this memory item.
        
        Updates the health metadata to reflect the access.
        """
        self.health.update_access()
        self.updated_at = datetime.utcnow()
    
    def add_related_memory(self, memory_id: UUID):
        """
        Add a related memory.
        
        Args:
            memory_id: ID of the related memory
        """
        if memory_id not in self.related_memories:
            self.related_memories.append(memory_id)
            self.updated_at = datetime.utcnow()
    
    def remove_related_memory(self, memory_id: UUID):
        """
        Remove a related memory.
        
        Args:
            memory_id: ID of the related memory
        """
        if memory_id in self.related_memories:
            self.related_memories.remove(memory_id)
            self.updated_at = datetime.utcnow()
    
    def calculate_health(self) -> float:
        """
        Calculate the overall health score.
        
        Returns:
            Overall health score (0-100)
        """
        return self.health.calculate_health()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the memory item to a dictionary.
        
        Returns:
            Dictionary representation of the memory item
        """
        return {
            "id": str(self.id),
            "content": self.content,
            "tier": self.tier.value,
            "health": {
                "base_score": self.health.base_score,
                "relevance_score": self.health.relevance_score,
                "last_accessed": self.health.last_accessed.isoformat(),
                "access_count": self.health.access_count,
                "importance": self.health.importance,
                "tags": self.health.tags,
                "embedding": self.health.embedding
            },
            "metadata": self.metadata,
            "related_memories": [str(memory_id) for memory_id in self.related_memories],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """
        Create a memory item from a dictionary.
        
        Args:
            data: Dictionary containing memory item data
            
        Returns:
            New memory item instance
        """
        # Handle conversion of string ID to UUID
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])
            
        # Handle conversion of string timestamps to datetime
        for field_name in ["created_at", "updated_at"]:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        # Handle conversion of tier string to enum
        if "tier" in data and isinstance(data["tier"], str):
            data["tier"] = MemoryTier(data["tier"])
        
        # Handle health metadata
        if "health" in data and isinstance(data["health"], dict):
            health_data = data.pop("health")
            
            # Handle conversion of string timestamp to datetime
            if "last_accessed" in health_data and isinstance(health_data["last_accessed"], str):
                health_data["last_accessed"] = datetime.fromisoformat(health_data["last_accessed"])
            
            data["health"] = HealthMetadata(**health_data)
        
        # Handle related memories
        if "related_memories" in data and isinstance(data["related_memories"], list):
            data["related_memories"] = [
                UUID(memory_id) if isinstance(memory_id, str) else memory_id
                for memory_id in data["related_memories"]
            ]
        
        return cls(**data)
```

### 4.2. Repository Interface Example: `src/domain/repositories/memory_repository.py`

```python
"""
Module: memory_repository
Description: Memory repository interface

This module defines the repository interface for memory items,
which provides data access operations for memory storage.

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from neuroca.domain.models import MemoryItem, MemoryTier


class MemoryRepository(ABC):
    """
    Repository interface for memory items.
    
    This interface defines the data access operations for memory items.
    """

    @abstractmethod
    async def create(self, item: MemoryItem) -> MemoryItem:
        """
        Create a new memory item.
        
        Args:
            item: The memory item to create
            
        Returns:
            The created memory item with any generated fields
            
        Raises:
            RepositoryError: If the memory item cannot be created
        """
        pass
    
    @abstractmethod
    async def get(self, item_id: UUID) -> Optional[MemoryItem]:
        """
        Get a memory item by ID.
        
        Args:
            item_id: The ID of the memory item to retrieve
            
        Returns:
            The memory item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, item: MemoryItem) -> MemoryItem:
        """
        Update an existing memory item.
        
        Args:
            item: The memory item to update
            
        Returns:
            The updated memory item
            
        Raises:
            RepositoryError: If the memory item cannot be updated
            ItemNotFoundError: If the memory item does not exist
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: UUID) -> bool:
        """
        Delete a memory item by ID.
        
        Args:
            item_id: The ID of the memory item to delete
            
        Returns:
            True if the memory item was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def list(self, filters: Optional[Dict[str, Any]] = None, 
                  limit: int = 100, offset: int = 0) -> Tuple[List[MemoryItem], int]:
        """
        List memory items with optional filtering.
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            Tuple of (list of memory items matching the criteria, total count)
        """
        pass
    
    @abstractmethod
    async def find_by_content(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """
        Find memory items by content similarity.
        
        Args:
            query: The content to search for
            limit: Maximum number of items to return
            
        Returns:
            List of memory items matching the query
        """
        pass
    
    @abstractmethod
    async def find_by_embedding(self, embedding: List[float], 
                              limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Find memory items by embedding similarity.
        
        Args:
            embedding: The embedding vector to search for
            limit: Maximum number of items to return
            
        Returns:
            List of tuples containing (memory item, similarity score)
        """
        pass
    
    @abstractmethod
    async def find_related(self, item_id: UUID, limit: int = 10) -> List[MemoryItem]:
        """
        Find memory items related to a given memory item.
        
        Args:
            item_id: The ID of the memory item to find related items for
            limit: Maximum number of items to return
            
        Returns:
            List of related memory items
        """
        pass
    
    @abstractmethod
    async def count_by_tier(self, tier: MemoryTier) -> int:
        """
        Count memory items by tier.
        
        Args:
            tier: The memory tier to count
            
        Returns:
            Number of memory items in the specified tier
        """
        pass
    
    @abstractmethod
    async def get_oldest_by_tier(self, tier: MemoryTier, 
                               limit: int = 10) -> List[MemoryItem]:
        """
        Get the oldest memory items by tier.
        
        Args:
            tier: The memory tier to query
            limit: Maximum number of items to return
            
        Returns:
            List of oldest memory items in the specified tier
        """
        pass
    
    @abstractmethod
    async def get_lowest_health_by_tier(self, tier: MemoryTier, 
                                      limit: int = 10) -> List[MemoryItem]:
        """
        Get the memory items with lowest health by tier.
        
        Args:
            tier: The memory tier to query
            limit: Maximum number of items to return
            
        Returns:
            List of memory items with lowest health in the specified tier
        """
        pass
```

### 4.3. Repository Implementation Example: `src/infrastructure/persistence/redis/redis_stm_repository.py`

```python
"""
Module: redis_stm_repository
Description: Redis implementation of STM repository

This module implements the memory repository for Short-Term Memory (STM)
using Redis as the storage backend.

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import redis.asyncio as redis
from redis.asyncio import Redis

from neuroca.domain.models import MemoryItem, MemoryTier
from neuroca.domain.repositories import MemoryRepository
from neuroca.domain.exceptions import RepositoryError, ItemNotFoundError
from neuroca.infrastructure.embedding import EmbeddingService

# Configure logger
logger = logging.getLogger(__name__)


class RedisSTMRepository(MemoryRepository):
    """
    Redis implementation of MemoryRepository for Short-Term Memory (STM).
    
    This class provides a concrete implementation of the MemoryRepository
    interface using Redis as the storage backend for STM.
    """

    def __init__(self, redis_client: Redis, embedding_service: EmbeddingService, ttl: int = 10800):
        """
        Initialize the repository.
        
        Args:
            redis_client: Redis client
            embedding_service: Service for generating and comparing embeddings
            ttl: Time-to-live for memory items in seconds (default: 3 hours)
        """
        self._redis = redis_client
        self._embedding_service = embedding_service
        self._ttl = ttl
        self._key_prefix = "stm:memory:"
        self._index_prefix = "stm:index:"
        logger.debug("Initialized RedisSTMRepository")
    
    async def create(self, item: MemoryItem) -> MemoryItem:
        """
        Create a new memory item in Redis.
        
        Args:
            item: The memory item to create
            
        Returns:
            The created memory item with any generated fields
            
        Raises:
            RepositoryError: If the memory item cannot be created
        """
        try:
            logger.debug(f"Creating STM item: {item.id}")
            
            # Ensure the item is in the STM tier
            if item.tier != MemoryTier.STM:
                item.tier = MemoryTier.STM
            
            # Generate embedding if not present
            if not item.health.embedding:
                item.health.embedding = await self._embedding_service.generate_embedding(item.content)
            
            # Convert to dictionary
            item_dict = item.to_dict()
            item_json = json.dumps(item_dict)
            
            # Store in Redis with TTL
            key = f"{self._key_prefix}{item.id}"
            await self._redis.set(key, item_json, ex=self._ttl)
            
            # Add to content index
            await self._add_to_content_index(item)
            
            # Add to embedding index
            await self._add_to_embedding_index(item)
            
            logger.info(f"Created STM item: {item.id}")
            return item
        except Exception as e:
            logger.error(f"Error creating STM item: {str(e)}")
            raise RepositoryError(f"Failed to create STM item: {str(e)}")
    
    async def get(self, item_id: UUID) -> Optional[MemoryItem]:
        """
        Get a memory item by ID from Redis.
        
        Args:
            item_id: The ID of the memory item to retrieve
            
        Returns:
            The memory item if found, None otherwise
        """
        try:
            logger.debug(f"Getting STM item: {item_id}")
            
            # Get from Redis
            key = f"{self._key_prefix}{item_id}"
            item_json = await self._redis.get(key)
            
            if not item_json:
                logger.debug(f"STM item not found: {item_id}")
                return None
            
            # Parse JSON
            item_dict = json.loads(item_json)
            
            # Create memory item
            item = MemoryItem.from_dict(item_dict)
            
            # Update access metadata
            item.access()
            
            # Update in Redis
            await self.update(item)
            
            logger.debug(f"Retrieved STM item: {item_id}")
            return item
        except Exception as e:
            logger.error(f"Error getting STM item {item_id}: {str(e)}")
            return None
    
    async def update(self, item: MemoryItem) -> MemoryItem:
        """
        Update an existing memory item in Redis.
        
        Args:
            item: The memory item to update
            
        Returns:
            The updated memory item
            
        Raises:
            RepositoryError: If the memory item cannot be updated
            ItemNotFoundError: If the memory item does not exist
        """
        try:
            logger.debug(f"Updating STM item: {item.id}")
            
            # Check if item exists
            key = f"{self._key_prefix}{item.id}"
            exists = await self._redis.exists(key)
            
            if not exists:
                raise ItemNotFoundError(f"STM item with ID {item.id} not found")
            
            # Ensure the item is in the STM tier
            if item.tier != MemoryTier.STM:
                item.tier = MemoryTier.STM
            
            # Convert to dictionary
            item_dict = item.to_dict()
            item_json = json.dumps(item_dict)
            
            # Update in Redis with TTL
            await self._redis.set(key, item_json, ex=self._ttl)
            
            # Update in content index
            await self._update_in_content_index(item)
            
            # Update in embedding index
            await self._update_in_embedding_index(item)
            
            logger.info(f"Updated STM item: {item.id}")
            return item
        except ItemNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating STM item {item.id}: {str(e)}")
            raise RepositoryError(f"Failed to update STM item: {str(e)}")
    
    async def delete(self, item_id: UUID) -> bool:
        """
        Delete a memory item by ID from Redis.
        
        Args:
            item_id: The ID of the memory item to delete
            
        Returns:
            True if the memory item was deleted, False otherwise
        """
        try:
            logger.debug(f"Deleting STM item: {item_id}")
            
            # Get item first to remove from indexes
            item = await self.get(item_id)
            
            if not item:
                logger.debug(f"STM item not found for deletion: {item_id}")
                return False
            
            # Remove from content index
            await self._remove_from_content_index(item)
            
            # Remove from embedding index
            await self._remove_from_embedding_index(item)
            
            # Delete from Redis
            key = f"{self._key_prefix}{item_id}"
            deleted = await self._redis.delete(key)
            
            success = deleted > 0
            if success:
                logger.info(f"Deleted STM item: {item_id}")
            else:
                logger.warning(f"Failed to delete STM item: {item_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error deleting STM item {item_id}: {str(e)}")
            return False
    
    async def list(self, filters: Optional[Dict[str, Any]] = None, 
                  limit: int = 100, offset: int = 0) -> Tuple[List[MemoryItem], int]:
        """
        List memory items with optional filtering from Redis.
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            Tuple of (list of memory items matching the criteria, total count)
        """
        try:
            logger.debug(f"Listing STM items with filters: {filters}")
            
            # Get all keys matching the prefix
            pattern = f"{self._key_prefix}*"
            cursor = 0
            all_keys = []
            
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=1000)
                all_keys.extend(keys)
                
                if cursor == 0:
                    break
            
            # Apply filters if provided
            filtered_keys = all_keys
            if filters:
                filtered_keys = await self._apply_filters(all_keys, filters)
            
            # Get total count
            total = len(filtered_keys)
            
            # Apply pagination
            paginated_keys = filtered_keys[offset:offset + limit]
            
            # Get items
            items = []
            for key in paginated_keys:
                item_json = await self._redis.get(key)
                if item_json:
                    item_dict = json.loads(item_json)
                    item = MemoryItem.from_dict(item_dict)
                    items.append(item)
            
            logger.debug(f"Listed {len(items)} STM items (total: {total})")
            return items, total
        except Exception as e:
            logger.error(f"Error listing STM items: {str(e)}")
            return [], 0
    
    async def find_by_content(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """
        Find memory items by content similarity using Redis search.
        
        Args:
            query: The content to search for
            limit: Maximum number of items to return
            
        Returns:
            List of memory items matching the query
        """
        try:
            logger.debug(f"Finding STM items by content: {query}")
            
            # Generate embedding for the query
            query_embedding = await self._embedding_service.generate_embedding(query)
            
            # Find by embedding similarity
            results = await self.find_by_embedding(query_embedding, limit)
            
            # Extract just the items
            items = [item for item, _ in results]
            
            logger.debug(f"Found {len(items)} STM items by content")
            return items
        except Exception as e:
            logger.error(f"Error finding STM items by content: {str(e)}")
            return []
    
    async def find_by_embedding(self, embedding: List[float], 
                              limit: int = 10) -> List[Tuple[MemoryItem, float]]:
        """
        Find memory items by embedding similarity using Redis.
        
        Args:
            embedding: The embedding vector to search for
            limit: Maximum number of items to return
            
        Returns:
            List of tuples containing (memory item, similarity score)
        """
        try:
            logger.debug("Finding STM items by embedding")
            
            # Get all keys matching the prefix
            pattern = f"{self._key_prefix}*"
            cursor = 0
            all_keys = []
            
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=1000)
                all_keys.extend(keys)
                
                if cursor == 0:
                    break
            
            # Get all items
            items = []
            for key in all_keys:
                item_json = await self._redis.get(key)
                if item_json:
                    item_dict = json.loads(item_json)
                    item = MemoryItem.from_dict(item_dict)
                    items.append(item)
            
            # Calculate similarity scores
            results = []
            for item in items:
                if item.health.embedding:
                    similarity = self._embedding_service.calculate_similarity(
                        embedding, item.health.embedding
                    )
                    results.append((item, similarity))
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Limit results
            limited_results = results[:limit]
            
            logger.debug(f"Found {len(limited_results)} STM items by embedding")
            return limited_results
        except Exception as e:
            logger.error(f"Error finding STM items by embedding: {str(e)}")
            return []
    
    async def find_related(self, item_id: UUID, limit: int = 10) -> List[MemoryItem]:
        """
        Find memory items related to a given memory item.
        
        Args:
            item_id: The ID of the memory item to find related items for
            limit: Maximum number of items to return
            
        Returns:
            List of related memory items
        """
        try:
            logger.debug(f"Finding STM items related to: {item_id}")
            
            # Get the item
            item = await self.get(item_id)
            
            if not item:
                logger.warning(f"STM item not found for related search: {item_id}")
                return []
            
            # Get related memory IDs
            related_ids = item.related_memories
            
            # Get related items
            related_items = []
            for related_id in related_ids:
                related_item = await self.get(related_id)
                if related_item:
                    related_items.append(related_item)
                    
                    if len(related_items) >= limit:
                        break
            
            # If we don't have enough related items, find by embedding similarity
            if len(related_items) < limit and item.health.embedding:
                embedding_results = await self.find_by_embedding(
                    item.health.embedding, limit - len(related_items)
                )
                
                # Add items that aren't already in the results
                for related_item, _ in embedding_results:
                    if related_item.id != item.id and related_item.id not in related_ids:
                        related_items.append(related_item)
                        
                        if len(related_items) >= limit:
                            break
            
            logger.debug(f"Found {len(related_items)} STM items related to {item_id}")
            return related_items
        except Exception as e:
            logger.error(f"Error finding related STM items for {item_id}: {str(e)}")
            return []
    
    async def count_by_tier(self, tier: MemoryTier) -> int:
        """
        Count memory items by tier.
        
        Args:
            tier: The memory tier to count
            
        Returns:
            Number of memory items in the specified tier
        """
        try:
            logger.debug(f"Counting STM items")
            
            if tier != MemoryTier.STM:
                return 0
            
            # Get all keys matching the prefix
            pattern = f"{self._key_prefix}*"
            cursor = 0
            all_keys = []
            
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=1000)
                all_keys.extend(keys)
                
                if cursor == 0:
                    break
            
            count = len(all_keys)
            logger.debug(f"Counted {count} STM items")
            return count
        except Exception as e:
            logger.error(f"Error counting STM items: {str(e)}")
            return 0
    
    async def get_oldest_by_tier(self, tier: MemoryTier, 
                               limit: int = 10) -> List[MemoryItem]:
        """
        Get the oldest memory items by tier.
        
        Args:
            tier: The memory tier to query
            limit: Maximum number of items to return
            
        Returns:
            List of oldest memory items in the specified tier
        """
        try:
            logger.debug(f"Getting oldest STM items")
            
            if tier != MemoryTier.STM:
                return []
            
            # Get all items
            items, _ = await self.list(limit=1000)
            
            # Sort by creation time (ascending)
            items.sort(key=lambda x: x.created_at)
            
            # Limit results
            limited_items = items[:limit]
            
            logger.debug(f"Got {len(limited_items)} oldest STM items")
            return limited_items
        except Exception as e:
            logger.error(f"Error getting oldest STM items: {str(e)}")
            return []
    
    async def get_lowest_health_by_tier(self, tier: MemoryTier, 
                                      limit: int = 10) -> List[MemoryItem]:
        """
        Get the memory items with lowest health by tier.
        
        Args:
            tier: The memory tier to query
            limit: Maximum number of items to return
            
        Returns:
            List of memory items with lowest health in the specified tier
        """
        try:
            logger.debug(f"Getting lowest health STM items")
            
            if tier != MemoryTier.STM:
                return []
            
            # Get all items
            items, _ = await self.list(limit=1000)
            
            # Calculate health for each item
            for item in items:
                item.calculate_health()
            
            # Sort by health score (ascending)
            items.sort(key=lambda x: x.calculate_health())
            
            # Limit results
            limited_items = items[:limit]
            
            logger.debug(f"Got {len(limited_items)} lowest health STM items")
            return limited_items
        except Exception as e:
            logger.error(f"Error getting lowest health STM items: {str(e)}")
            return []
    
    async def _add_to_content_index(self, item: MemoryItem) -> None:
        """
        Add a memory item to the content index.
        
        Args:
            item: The memory item to add
        """
        # This is a simplified implementation
        # In a production system, this would use Redis Search or a more sophisticated indexing strategy
        pass
    
    async def _update_in_content_index(self, item: MemoryItem) -> None:
        """
        Update a memory item in the content index.
        
        Args:
            item: The memory item to update
        """
        # This is a simplified implementation
        # In a production system, this would use Redis Search or a more sophisticated indexing strategy
        pass
    
    async def _remove_from_content_index(self, item: MemoryItem) -> None:
        """
        Remove a memory item from the content index.
        
        Args:
            item: The memory item to remove
        """
        # This is a simplified implementation
        # In a production system, this would use Redis Search or a more sophisticated indexing strategy
        pass
    
    async def _add_to_embedding_index(self, item: MemoryItem) -> None:
        """
        Add a memory item to the embedding index.
        
        Args:
            item: The memory item to add
        """
        # This is a simplified implementation
        # In a production system, this would use Redis Search or a more sophisticated indexing strategy
        pass
    
    async def _update_in_embedding_index(self, item: MemoryItem) -> None:
        """
        Update a memory item in the embedding index.
        
        Args:
            item: The memory item to update
        """
        # This is a simplified implementation
        # In a production system, this would use Redis Search or a more sophisticated indexing strategy
        pass
    
    async def _remove_from_embedding_index(self, item: MemoryItem) -> None:
        """
        Remove a memory item from the embedding index.
        
        Args:
            item: The memory item to remove
        """
        # This is a simplified implementation
        # In a production system, this would use Redis Search or a more sophisticated indexing strategy
        pass
    
    async def _apply_filters(self, keys: List[str], 
                           filters: Dict[str, Any]) -> List[str]:
        """
        Apply filters to a list of keys.
        
        Args:
            keys: List of keys to filter
            filters: Filters to apply
            
        Returns:
            Filtered list of keys
        """
        # This is a simplified implementation
        # In a production system, this would use Redis Search or a more sophisticated filtering strategy
        filtered_keys = []
        
        for key in keys:
            item_json = await self._redis.get(key)
            if item_json:
                item_dict = json.loads(item_json)
                
                # Check if item matches all filters
                matches = True
                for filter_key, filter_value in filters.items():
                    if filter_key in item_dict:
                        if item_dict[filter_key] != filter_value:
                            matches = False
                            break
                    else:
                        matches = False
                        break
                
                if matches:
                    filtered_keys.append(key)
        
        return filtered_keys
```

### 4.4. Service Example: `src/application/services/memory_service.py`

```python
"""
Module: memory_service
Description: Memory service

This module implements the memory service, which provides business logic
for memory operations in the NeuroCognitive Architecture.

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from neuroca.domain.models import MemoryItem, MemoryTier
from neuroca.domain.repositories import MemoryRepository
from neuroca.domain.exceptions import ServiceError, ValidationError, ItemNotFoundError
from neuroca.infrastructure.embedding import EmbeddingService

# Configure logger
logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for memory operations.
    
    This class provides business logic for memory operations in the NCA.
    """

    def __init__(self, stm_repository: MemoryRepository, 
                mtm_repository: MemoryRepository,
                ltm_repository: MemoryRepository,
                embedding_service: EmbeddingService):
        """
        Initialize the service.
        
        Args:
            stm_repository: Repository for Short-Term Memory
            mtm_repository: Repository for Medium-Term Memory
            ltm_repository: Repository for Long-Term Memory
            embedding_service: Service for generating and comparing embeddings
        """
        self._repositories = {
            MemoryTier.STM: stm_repository,
            MemoryTier.MTM: mtm_repository,
            MemoryTier.LTM: ltm_repository
        }
        self._embedding_service = embedding_service
        logger.debug("Initialized MemoryService")
    
    async def create_memory(self, content: str, tier: MemoryTier = MemoryTier.STM, 
                          importance: int = 5, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """
        Create a new memory.
        
        Args:
            content: Memory content
            tier: Memory tier (default: STM)
            importance: Importance flag (0-10, default: 5)
            metadata: Additional metadata
            
        Returns:
            The created memory
            
        Raises:
            ValidationError: If the data is invalid
            ServiceError: If the memory cannot be created
        """
        try:
            logger.info(f"Creating new memory in tier: {tier.value}")
            
            # Validate input
            self._validate_memory_data(content, importance, metadata)
            
            # Generate embedding
            embedding = await self._embedding_service.generate_embedding(content)
            
            # Create memory item
            memory = MemoryItem(
                content=content,
                tier=tier,
                metadata=metadata or {},
                health={
                    "base_score": self._get_base_score_for_tier(tier),
                    "importance": importance,
                    "embedding": embedding
                }
            )
            
            # Save to repository
            repository = self._repositories[tier]
            created_memory = await repository.create(memory)
            
            logger.info(f"Created memory with ID: {created_memory.id} in tier: {tier.value}")
            return created_memory
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating memory: {str(e)}")
            raise ServiceError(f"Failed to create memory: {str(e)}")
    
    async def get_memory(self, memory_id: UUID) -> Optional[MemoryItem]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            The memory if found, None otherwise
        """
        logger.info(f"Getting memory with ID: {memory_id}")
        
        # Try to find in each tier
        for tier, repository in self._repositories.items():
            memory = await repository.get(memory_id)
            if memory:
                logger.info(f"Found memory with ID: {memory_id} in tier: {tier.value}")
                return memory
        
        logger.warning(f"Memory with ID: {memory_id} not found in any tier")
        return None
    
    async def update_memory(self, memory_id: UUID, 
                          data: Dict[str, Any]) -> MemoryItem:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory ID
            data: Updated memory data
            
        Returns:
            The updated memory
            
        Raises:
            ValidationError: If the data is invalid
            ServiceError: If the memory cannot be updated
            ItemNotFoundError: If the memory does not exist
        """
        try:
            logger.info(f"Updating memory with ID: {memory_id}")
            
            # Get existing memory
            memory = await self.get_memory(memory_id)
            if not memory:
                raise ItemNotFoundError(f"Memory with ID {memory_id} not found")
            
            # Validate input data
            if "content" in data:
                self._validate_memory_data(
                    data["content"], 
                    data.get("importance", memory.health.importance),
                    data.get("metadata", memory.metadata)
                )
            
            # Update memory
            if "content" in data:
                memory.content = data["content"]
                
                # Update embedding
                memory.health.embedding = await self._embedding_service.generate_embedding(data["content"])
            
            if "importance" in data:
                memory.health.importance = data["importance"]
            
            if "metadata" in data:
                memory.metadata = data["metadata"]
            
            # Save to repository
            repository = self._repositories[memory.tier]
            updated_memory = await repository.update(memory)
            
            logger.info(f"Updated memory with ID: {updated_memory.id}")
            return updated_memory
        except (ValidationError, ItemNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {str(e)}")
            raise ServiceError(f"Failed to update memory: {str(e)}")
    
    async def delete_memory(self, memory_id: UUID) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if the memory was deleted, False otherwise
        """
        logger.info(f"Deleting memory with ID: {memory_id}")
        
        # Try to delete from each tier
        for tier, repository in self._repositories.items():
            deleted = await repository.delete(memory_id)
            if deleted:
                logger.info(f"Deleted memory with ID: {memory_id} from tier: {tier.value}")
                return True
        
        logger.warning(f"Memory with ID: {memory_id} not found for deletion")
        return False
    
    async def promote_memory(self, memory_id: UUID) -> Optional[MemoryItem]:
        """
        Promote a memory to a higher tier.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            The promoted memory if successful, None otherwise
            
        Raises:
            ServiceError: If the memory cannot be promoted
        """
        try:
            logger.info(f"Promoting memory with ID: {memory_id}")
            
            # Get existing memory
            memory = await self.get_memory(memory_id)
            if not memory:
                logger.warning(f"Memory with ID: {memory_id} not found for promotion")
                return None
            
            # Determine target tier
            current_tier = memory.tier
            target_tier = None
            
            if current_tier == MemoryTier.STM:
                target_tier = MemoryTier.MTM
            elif current_tier == MemoryTier.MTM:
                target_tier = MemoryTier.LTM
            else:
                logger.info(f"Memory with ID: {memory_id} is already in the highest tier")
                return memory
            
            # Delete from current tier
            current_repository = self._repositories[current_tier]
            deleted = await current_repository.delete(memory_id)
            
            if not deleted:
                logger.warning(f"Failed to delete memory with ID: {memory_id} from tier: {current_tier.value}")
                return None
            
            # Update tier and health
            memory.tier = target_tier
            memory.health.base_score = self._get_base_score_for_tier(target_tier)
            
            # Save to target tier
            target_repository = self._repositories[target_tier]
            promoted_memory = await target_repository.create(memory)
            
            logger.info(f"Promoted memory with ID: {memory_id} from {current_tier.value} to {target_tier.value}")
            return promoted_memory
        except Exception as e:
            logger.error(f"Error promoting memory {memory_id}: {str(e)}")
            raise ServiceError(f"Failed to promote memory: {str(e)}")
    
    async def demote_memory(self, memory_id: UUID) -> Optional[MemoryItem]:
        """
        Demote a memory to a lower tier.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            The demoted memory if successful, None otherwise
            
        Raises:
            ServiceError: If the memory cannot be demoted
        """
        try:
            logger.info(f"Demoting memory with ID: {memory_id}")
            
            # Get existing memory
            memory = await self.get_memory(memory_id)
            if not memory:
                logger.warning(f"Memory with ID: {memory_id} not found for demotion")
                return None
            
            # Determine target tier
            current_tier = memory.tier
            target_tier = None
            
            if current_tier == MemoryTier.LTM:
                target_tier = MemoryTier.MTM
            elif current_tier == MemoryTier.MTM:
                target_tier = MemoryTier.STM
            else:
                logger.info(f"Memory with ID: {memory_id} is already in the lowest tier")
                return memory
            
            # Delete from current tier
            current_repository = self._repositories[current_tier]
            deleted = await current_repository.delete(memory_id)
            
            if not deleted:
                logger.warning(f"Failed to delete memory with ID: {memory_id} from tier: {current_tier.value}")
                return None
            
            # Update tier and health
            memory.tier = target_tier
            memory.health.base_score = self._get_base_score_for_tier(target_tier)
            
            # Save to target tier
            target_repository = self._repositories[target_tier]
            demoted_memory = await target_repository.create(memory)
            
            logger.info(f"Demoted memory with ID: {memory_id} from {current_tier.value} to {target_tier.value}")
            return demoted_memory
        except Exception as e:
            logger.error(f"Error demoting memory {memory_id}: {str(e)}")
            raise ServiceError(f"Failed to demote memory: {str(e)}")
    
    async def find_memories(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """
        Find memories by content similarity.
        
        Args:
            query: The content to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of memories matching the query
        """
        try:
            logger.info(f"Finding memories by query: {query}")
            
            # Generate embedding for the query
            query_embedding = await self._embedding_service.generate_embedding(query)
            
            # Search in each tier
            all_results = []
            
            for tier, repository in self._repositories.items():
                tier_results = await repository.find_by_embedding(query_embedding, limit)
                all_results.extend(tier_results)
            
            # Sort by similarity (descending)
            all_results.sort(key=lambda x: x[1], reverse=True)
            
            # Limit results
            limited_results = all_results[:limit]
            
            # Extract just the memories
            memories = [memory for memory, _ in limited_results]
            
            logger.info(f"Found {len(memories)} memories matching query")
            return memories
        except Exception as e:
            logger.error(f"Error finding memories: {str(e)}")
            return []
    
    async def find_related_memories(self, memory_id: UUID, limit: int = 10) -> List[MemoryItem]:
        """
        Find memories related to a given memory.
        
        Args:
            memory_id: The ID of the memory to find related memories for
            limit: Maximum number of memories to return
            
        Returns:
            List of related memories
        """
        try:
            logger.info(f"Finding memories related to: {memory_id}")
            
            # Get the memory
            memory = await self.get_memory(memory_id)
            
            if not memory:
                logger.warning(f"Memory with ID: {memory_id} not found for related search")
                return []
            
            # Get related memories from each tier
            all_related = []
            
            for tier, repository in self._repositories.items():
                tier_related = await repository.find_related(memory_id, limit)
                all_related.extend(tier_related)
            
            # Limit results
            limited_related = all_related[:limit]
            
            logger.info(f"Found {len(limited_related)} memories related to {memory_id}")
            return limited_related
        except Exception as e:
            logger.error(f"Error finding related memories for {memory_id}: {str(e)}")
            return []
    
    async def list_memories(self, filters: Optional[Dict[str, Any]] = None, 
                          limit: int = 100, offset: int = 0) -> Tuple[List[MemoryItem], int]:
        """
        List memories with optional filtering.
        
        Args:
            filters: Optional filters to apply
            limit: Maximum number of memories to return
            offset: Number of memories to skip
            
        Returns:
            Tuple of (list of memories matching the criteria, total count)
        """
        try:
            logger.info(f"Listing memories with filters: {filters}")
            
            # Determine which tiers to query
            tiers_to_query = list(self._repositories.keys())
            
            if filters and "tier" in filters:
                tier_value = filters.pop("tier")
                try:
                    tier = MemoryTier(tier_value)
                    tiers_to_query = [tier]
                except ValueError:
                    logger.warning(f"Invalid tier value: {tier_value}")
            
            # Query each tier
            all_memories = []
            total_count = 0
            
            for tier in tiers_to_query:
                repository = self._repositories[tier]
                tier_memories, tier_count = await repository.list(filters, limit, offset)
                
                all_memories.extend(tier_memories)
                total_count += tier_count
            
            # Sort by creation time (descending)
            all_memories.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply offset and limit
            paginated_memories = all_memories[offset:offset + limit]
            
            logger.info(f"Listed {len(paginated_memories)} memories (total: {total_count})")
            return paginated_memories, total_count
        except Exception as e:
            logger.error(f"Error listing memories: {str(e)}")
            return [], 0
    
    def _validate_memory_data(self, content: str, importance: int, 
                            metadata: Optional[Dict[str, Any]]) -> None:
        """
        Validate memory data.
        
        Args:
            content: Memory content
            importance: Importance flag
            metadata: Additional metadata
            
        Raises:
            ValidationError: If the data is invalid
        """
        if not content:
            raise ValidationError("Content cannot be empty")
        
        if len(content) > 10000:
            raise ValidationError("Content is too long (max 10000 characters)")
        
        if not isinstance(importance, int) or importance < 0 or importance > 10:
            raise ValidationError("Importance must be an integer between 0 and 10")
        
        if metadata is not None and not isinstance(metadata, dict):
            raise ValidationError("Metadata must be a dictionary")
    
    def _get_base_score_for_tier(self, tier: MemoryTier) -> float:
        """
        Get the base health score for a tier.
        
        Args:
            tier: Memory tier
            
        Returns:
            Base health score
        """
        if tier == MemoryTier.STM:
            return 80.0
        elif tier == MemoryTier.MTM:
            return 60.0
        else:  # LTM
            return 40.0
```

### 4.5. API Controller Example: `src/api/rest/controllers/memory_controller.py`

```python
"""
Module: memory_controller
Description: API controller for memory operations

This module implements the API controller for memory operations in the NCA.

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel, Field, validator

from neuroca.application.services import MemoryService
from neuroca.domain.models import MemoryTier
from neuroca.domain.exceptions import ValidationError, ServiceError, ItemNotFoundError
from neuroca.api.dependencies import get_memory_service

# Configure logger
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(prefix="/memories", tags=["Memories"])

# Define request/response models
class HealthMetadataResponse(BaseModel):
    """Response model for health metadata."""
    base_score: float = Field(..., description="Base health score (0-100)")
    relevance_score: float = Field(..., description="Relevance score (0-100)")
    last_accessed: str = Field(..., description="Last access timestamp")
    access_count: int = Field(..., description="Number of times the memory has been accessed")
    importance: int = Field(..., description="Importance flag (0-10)")
    tags: List[str] = Field(..., description="Content type tags")

class MemoryCreate(BaseModel):
    """Request model for creating a memory."""
    content: str = Field(..., description="Memory content", min_length=1, max_length=10000)
    tier: str = Field("short_term_memory", description="Memory tier")
    importance: int = Field(5, description="Importance flag (0-10)", ge=0, le=10)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator("tier")
    def validate_tier(cls, v):
        """Validate that the tier is valid."""
        try:
            MemoryTier(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid tier: {v}")

class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""
    content: Optional[str] = Field(None, description="Memory content", min_length=1, max_length=10000)
    importance: Optional[int] = Field(None, description="Importance flag (0-10)", ge=0, le=10)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class MemoryResponse(BaseModel):
    """Response model for a memory."""
    id: str = Field(..., description="Unique identifier")
    content: str = Field(..., description="Memory content")
    tier: str = Field(..., description="Memory tier")
    health: HealthMetadataResponse = Field(..., description="Health metadata")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    related_memories: List[str] = Field(..., description="IDs of related memories")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class MemoryListResponse(BaseModel):
    """Response model for a list of memories."""
    items: List[MemoryResponse] = Field(..., description="List of memories")
    total: int = Field(..., description="Total number of memories")
    limit: int = Field(..., description="Maximum number of memories returned")
    offset: int = Field(..., description="Number of memories skipped")


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory: MemoryCreate,
    service: MemoryService = Depends(get_memory_service)
):
    """
    Create a new memory.
    
    Args:
        memory: Memory data
        service: Injected service
        
    Returns:
        The created memory
        
    Raises:
        HTTPException: If the memory cannot be created
    """
    try:
        logger.info("API request to create memory")
        
        # Convert tier string to enum
        tier = MemoryTier(memory.tier)
        
        created_memory = await service.create_memory(
            content=memory.content,
            tier=tier,
            importance=memory.importance,
            metadata=memory.metadata
        )
        
        return created_memory.to_dict()
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create memory"
        )

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: UUID = Path(..., description="Memory ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """
    Get a memory by ID.
    
    Args:
        memory_id: Memory ID
        service: Injected service
        
    Returns:
        The memory
        
    Raises:
        HTTPException: If the memory is not found
    """
    logger.info(f"API request to get memory {memory_id}")
    memory = await service.get_memory(memory_id)
    
    if not memory:
        logger.warning(f"Memory {memory_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
        
    return memory.to_dict()

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory: MemoryUpdate,
    memory_id: UUID = Path(..., description="Memory ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """
    Update a memory.
    
    Args:
        memory: Updated memory data
        memory_id: Memory ID
        service: Injected service
        
    Returns:
        The updated memory
        
    Raises:
        HTTPException: If the memory cannot be updated
    """
    try:
        logger.info(f"API request to update memory {memory_id}")
        updated_memory = await service.update_memory(memory_id, memory.dict(exclude_unset=True))
        return updated_memory.to_dict()
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ItemNotFoundError:
        logger.warning(f"Memory {memory_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    except ServiceError as e:
        logger.error(f"Service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update memory"
        )

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID = Path(..., description="Memory ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """
    Delete a memory.
    
    Args:
        memory_id: Memory ID
        service: Injected service
        
    Raises:
        HTTPException: If the memory cannot be deleted
    """
    logger.info(f"API request to delete memory {memory_id}")
    deleted = await service.delete_memory(memory_id)
    
    if not deleted:
        logger.warning(f"Memory {memory_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

@router.post("/{memory_id}/promote", response_model=MemoryResponse)
async def promote_memory(
    memory_id: UUID = Path(..., description="Memory ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """
    Promote a memory to a higher tier.
    
    Args:
        memory_id: Memory ID
        service: Injected service
        
    Returns:
        The promoted memory
        
    Raises:
        HTTPException: If the memory cannot be promoted
    """
    try:
        logger.info(f"API request to promote memory {memory_id}")
        promoted_memory = await service.promote_memory(memory_id)
        
        if not promoted_memory:
            logger.warning(f"Memory {memory_id} not found or already in highest tier")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found or already in highest tier"
            )
            
        return promoted_memory.to_dict()
    except ServiceError as e:
        logger.error(f"Service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote memory"
        )

@router.post("/{memory_id}/demote", response_model=MemoryResponse)
async def demote_memory(
    memory_id: UUID = Path(..., description="Memory ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """
    Demote a memory to a lower tier.
    
    Args:
        memory_id: Memory ID
        service: Injected service
        
    Returns:
        The demoted memory
        
    Raises:
        HTTPException: If the memory cannot be demoted
    """
    try:
        logger.info(f"API request to demote memory {memory_id}")
        demoted_memory = await service.demote_memory(memory_id)
        
        if not demoted_memory:
            logger.warning(f"Memory {memory_id} not found or already in lowest tier")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found or already in lowest tier"
            )
            
        return demoted_memory.to_dict()
    except ServiceError as e:
        logger.error(f"Service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to demote memory"
        )

@router.get("/", response_model=MemoryListResponse)
async def list_memories(
    limit: int = Query(100, description="Maximum number of memories to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of memories to skip", ge=0),
    tier: Optional[str] = Query(None, description="Filter by tier"),
    service: MemoryService = Depends(get_memory_service)
):
    """
    List memories with optional filtering.
    
    Args:
        limit: Maximum number of memories to return
        offset: Number of memories to skip
        tier: Filter by tier
        service: Injected service
        
    Returns:
        List of memories matching the criteria
    """
    logger.info(f"API request to list memories (limit={limit}, offset={offset}, tier={tier})")
    
    # Build filters
    filters = {}
    if tier:
        try:
            # Validate tier
            MemoryTier(tier)
            filters["tier"] = tier
        except ValueError:
            logger.warning(f"Invalid tier: {tier}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tier: {tier}"
            )
    
    memories, total = await service.list_memories(filters, limit, offset)
    
    return {
        "items": [memory.to_dict() for memory in memories],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/search", response_model=List[MemoryResponse])
async def search_memories(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of memories to return", ge=1, le=100),
    service: MemoryService = Depends(get_memory_service)
):
    """
    Search memories by content.
    
    Args:
        query: Search query
        limit: Maximum number of memories to return
        service: Injected service
        
    Returns:
        List of memories matching the query
    """
    logger.info(f"API request to search memories: {query}")
    memories = await service.find_memories(query, limit)
    
    return [memory.to_dict() for memory in memories]

@router.get("/{memory_id}/related", response_model=List[MemoryResponse])
async def get_related_memories(
    memory_id: UUID = Path(..., description="Memory ID"),
    limit: int = Query(10, description="Maximum number of memories to return", ge=1, le=100),
    service: MemoryService = Depends(get_memory_service)
):
    """
    Get memories related to a given memory.
    
    Args:
        memory_id: Memory ID
        limit: Maximum number of memories to return
        service: Injected service
        
    Returns:
        List of related memories
        
    Raises:
        HTTPException: If the memory is not found
    """
    logger.info(f"API request to get memories related to {memory_id}")
    
    # Check if the memory exists
    memory = await service.get_memory(memory_id)
    if not memory:
        logger.warning(f"Memory {memory_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    related_memories = await service.find_related_memories(memory_id, limit)
    
    return [memory.to_dict() for memory in related_memories]
```

### 4.6. Configuration Example: `config/development/app.yaml`

```yaml
# NeuroCognitive Architecture - Development Configuration

# Application configuration
app:
  name: NeuroCognitive Architecture
  version: 0.1.0
  description: Brain-inspired three-tiered memory system for LLMs
  environment: development
  debug: true
  log_level: debug

# API configuration
api:
  host: 0.0.0.0
  port: 8000
  cors:
    allowed_origins:
      - http://localhost:3000
      - http://localhost:8080
    allowed_methods:
      - GET
      - POST
      - PUT
      - DELETE
    allowed_headers:
      - Authorization
      - Content-Type
  rate_limiting:
    enabled: true
    rate: 100
    period: 60

# Memory configuration
memory:
  # Short-Term Memory configuration
  stm:
    provider: redis
    ttl: 10800  # 3 hours in seconds
    max_items: 1000
    health:
      base_score: 80
      decay_rate: 0.1
      promotion_threshold: 90
      demotion_threshold: 30
    connection:
      host: ${REDIS_HOST:-localhost}
      port: ${REDIS_PORT:-6379}
      db: 0
      password: ${REDIS_PASSWORD:-}

  # Medium-Term Memory configuration
  mtm:
    provider: mongodb
    ttl: 1209600  # 14 days in seconds
    max_items: 10000
    health:
      base_score: 60
      decay_rate: 0.05
      promotion_threshold: 80
      demotion_threshold: 20
    connection:
      uri: ${MONGODB_URI:-mongodb://localhost:27017/neuroca}
      database: neuroca
      collection: mtm_memories

  # Long-Term Memory configuration
  ltm:
    provider: postgres
    ttl: null  # No expiration
    max_items: 100000
    health:
      base_score: 40
      decay_rate: 0.01
      promotion_threshold: 70
      demotion_threshold: 10
    connection:
      host: ${POSTGRES_HOST:-localhost}
      port: ${POSTGRES_PORT:-5432}
      database: ${POSTGRES_DB:-neuroca}
      user: ${POSTGRES_USER:-postgres}
      password: ${POSTGRES_PASSWORD:-postgres}

# Advanced components configuration
components:
  # Lymphatic System configuration
  lymphatic:
    enabled: true
    consolidation_interval: 3600  # 1 hour in seconds
    batch_size: 100
    max_concurrent_tasks: 5
    schedule:
      - time: "*/30 * * * *"  # Every 30 minutes
        operation: "merge_redundant"
      - time: "0 */2 * * *"   # Every 2 hours
        operation: "abstract_concepts"
      - time: "0 0 * * *"     # Every day at midnight
        operation: "full_consolidation"

  # Neural Tubules configuration
  neural_tubules:
    enabled: true
    connection_strength_threshold: 0.5
    max_connections_per_memory: 50
    reinforcement_factor: 0.1
    decay_factor: 0.01
    similarity_threshold: 0.7

  # Temporal Annealing configuration
  temporal_annealing:
    enabled: true
    schedule:
      - phase: fast
        interval: 300  # 5 minutes in seconds
        intensity: 0.2
      - phase: medium
        interval: 3600  # 1 hour in seconds
        intensity: 0.5
      - phase: slow
        interval: 86400  # 24 hours in seconds
        intensity: 1.0

# LLM integration configuration
llm:
  default_provider: openai
  context_window_size: 4096
  max_tokens: 1000
  providers:
    openai:
      api_key: ${OPENAI_API_KEY:-}
      model: gpt-4
      temperature: 0.7
      timeout: 30
    anthropic:
      api_key: ${ANTHROPIC_API_KEY:-}
      model: claude-2
      temperature: 0.7
      timeout: 30

# Embedding configuration
embedding:
  provider: openai
  model: text-embedding-ada-002
  dimensions: 1536
  batch_size: 100
  cache:
    enabled: true
    ttl: 86400  # 24 hours in seconds

# Security configuration
security:
  jwt:
    secret_key: ${JWT_SECRET_KEY:-development_secret_key}
    algorithm: HS256
    access_token_expire_minutes: 30
  encryption:
    enabled: true
    algorithm: AES-256-GCM
    key_rotation_days: 30

# Monitoring configuration
monitoring:
  metrics:
    enabled: true
    prometheus:
      enabled: true
      port: 9090
  logging:
    level: ${LOG_LEVEL:-debug}
    format: json
    output:
      console: true
      file: false
      file_path: logs/neuroca.log
  tracing:
    enabled: true
    sampling_rate: 0.1
```

### 4.7. Main Application Example: `src/api/main.py`

```python
"""
Module: main
Description: Main application entry point

This module initializes and configures the NeuroCognitive Architecture API.

Copyright (c) 2023 NeuroCognitive Architecture Team
"""

import logging
import os
from pathlib import Path

import yaml
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from neuroca.api.rest.controllers import (
    memory_controller,
    health_controller,
    lymphatic_controller,
    neural_tubules_controller,
    temporal_annealing_controller,
    llm_controller
)
from neuroca.api.middleware import (
    logging_middleware,
    authentication_middleware,
    rate_limiting_middleware
)
from neuroca.domain.exceptions import BaseError, ValidationError, ServiceError, ItemNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load configuration from file."""
    env = os.getenv("ENVIRONMENT", "development")
    config_path = Path(f"config/{env}/app.yaml")
    
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}

config = load_config()

# Create FastAPI application
app = FastAPI(
    title=config.get("app", {}).get("name", "NeuroCognitive Architecture"),
    description=config.get("app", {}).get("description", "Brain-inspired three-tiered memory system for LLMs"),
    version=config.get("app", {}).get("version", "0.1.0"),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
cors_config = config.get("api", {}).get("cors", {})
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get("allowed_origins", ["*"]),
    allow_credentials=cors_config.get("allow_credentials", True),
    allow_methods=cors_config.get("allowed_methods", ["*"]),
    allow_headers=cors_config.get("allowed_headers", ["*"]),
)

# Add custom middleware
app.add_middleware(logging_middleware.LoggingMiddleware)
if config.get("security", {}).get("jwt", {}).get("enabled", True):
    app.add_middleware(authentication_middleware.AuthenticationMiddleware)
if config.get("api", {}).get("rate_limiting", {}).get("enabled", True):
    app.add_middleware(rate_limiting_middleware.RateLimitingMiddleware)

# Include routers
app.include_router(memory_controller.router, prefix="/api")
app.include_router(health_controller.router, prefix="/api")
app.include_router(lymphatic_controller.router, prefix="/api")
app.include_router(neural_tubules_controller.router, prefix="/api")
app.include_router(temporal_annealing_controller.router, prefix="/api")
app.include_router(llm_controller.router, prefix="/api")

# Add exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(ItemNotFoundError)
async def not_found_exception_handler(request, exc):
    """Handle not found errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )

@app.exception_handler(ServiceError)
async def service_exception_handler(request, exc):
    """Handle service errors."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

@app.exception_handler(BaseError)
async def base_exception_handler(request, exc):
    """Handle all other custom errors."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": config.get("app", {}).get("name", "NeuroCognitive Architecture"),
        "version": config.get("app", {}).get("version", "0.1.0"),
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Run the application
if __name__ == "__main__":
    api_config = config.get("api", {})
    uvicorn.run(
        "neuroca.api.main:app",
        host=api_config.get("host", "0.0.0.0"),
        port=api_config.get("port", 8000),
        reload=config.get("app", {}).get("debug", False)
    )
```

## 5. Configuration Templates

### 5.1. Environment Variables Template: `.env.example`

```
# NeuroCognitive Architecture - Environment Variables Example

# Application
ENVIRONMENT=development
LOG_LEVEL=debug

# API
API_HOST=0.0.0.0
API_PORT=8000

# Redis (STM)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MongoDB (MTM)
MONGODB_URI=mongodb://localhost:27017/neuroca

# PostgreSQL (LTM)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=neuroca
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# LLM Providers
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Security
JWT_SECRET_KEY=change_this_in_production
```

### 5.2. Docker Compose Development Template: `deploy/docker/docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  # API Service
  api:
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
      target: development
    image: neuroca-api:dev
    container_name: neuroca-api-dev
    restart: unless-stopped
    depends_on:
      - redis
      - mongodb
      - postgres
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=debug
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - MONGODB_URI=mongodb://mongodb:27017/neuroca
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET_KEY=development_secret_key
    ports:
      - "8000:8000"
    volumes:
      - ../..:/app
    command: uvicorn neuroca.api.main:app --host 0.0.0.0 --port 8000 --reload

  # Worker Service
  worker:
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
      target: development
    image: neuroca-worker:dev
    container_name: neuroca-worker-dev
    restart: unless-stopped
    depends_on:
      - redis
      - mongodb
      - postgres
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=debug
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - MONGODB_URI=mongodb://mongodb:27017/neuroca
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ../..:/app
    command: celery -A neuroca.infrastructure.tasks.worker worker --loglevel=info

  # Redis (STM)
  redis:
    image: redis:7-alpine
    container_name: neuroca-redis-dev
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  # MongoDB (MTM)
  mongodb:
    image: mongo:6
    container_name: neuroca-mongodb-dev
    restart: unless-stopped
    environment:
      - MONGO_INITDB_DATABASE=neuroca
    ports:
      - "27017:27017"
    volumes:
      - mongodb-data:/data/db

  # PostgreSQL (LTM)
  postgres:
    image: ankane/pgvector:latest
    container_name: neuroca-postgres-dev
    restart: unless-stopped
    environment:
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

  # Prometheus (Monitoring)
  prometheus:
    image: prom/prometheus:latest
    container_name: neuroca-prometheus-dev
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ../../config/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  # Grafana (Monitoring)
  grafana:
    image: grafana/grafana:latest
    container_name: neuroca-grafana-dev
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ../../config/monitoring/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana

volumes:
  redis-data:
  mongodb-data:
  postgres-data:
  prometheus-data:
  grafana-data:
```

### 5.3. Docker Compose Production Template: `deploy/docker/docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  # API Service
  api:
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
      target: production
    image: neuroca-api:${VERSION:-latest}
    container_name: neuroca-api
    restart: unless-stopped
    depends_on:
      - redis
      - mongodb
      - postgres
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - MONGODB_URI=mongodb://mongodb:27017/neuroca
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - api-logs:/app/logs
    deploy:
      replicas: ${API_REPLICAS:-3}
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Worker Service
  worker:
    build:
      context: ../..
      dockerfile: deploy/docker/Dockerfile
      target: production
    image: neuroca-worker:${VERSION:-latest}
    container_name: neuroca-worker
    restart: unless-stopped
    depends_on:
      - redis
      - mongodb
      - postgres
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - MONGODB_URI=mongodb://mongodb:27017/neuroca
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - worker-logs:/app/logs
    deploy:
      replicas: ${WORKER_REPLICAS:-2}
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    command: celery -A neuroca.infrastructure.tasks.worker worker --loglevel=${LOG_LEVEL:-info}

  # Redis (STM)
  redis:
    image: redis:7-alpine
    container_name: neuroca-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis-data:/data
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # MongoDB (MTM)
  mongodb:
    image: mongo:6
    container_name: neuroca-mongodb
    restart: unless-stopped
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
      - MONGO_INITDB_DATABASE=neuroca
    volumes:
      - mongodb-data:/data/db
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "mongo", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # PostgreSQL (LTM)
  postgres:
    image: ankane/pgvector:latest
    container_name: neuroca-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=neuroca
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    container_name: neuroca-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ../../config/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ../../config/nginx/conf.d:/etc/nginx/conf.d
      - ../../config/nginx/ssl:/etc/nginx/ssl
      - nginx-logs:/var/log/nginx
    depends_on:
      - api
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Prometheus (Monitoring)
  prometheus:
    image: prom/prometheus:latest
    container_name: neuroca-prometheus
    restart: unless-stopped
    volumes:
      - ../../config/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Grafana (Monitoring)
  grafana:
    image: grafana/grafana:latest
    container_name: neuroca-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - ../../config/monitoring/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  redis-data:
  mongodb-data:
  postgres-data:
  prometheus-data:
  grafana-data:
  api-logs:
  worker-logs:
  nginx-logs:
```

### 5.4. Kubernetes Deployment Template: `deploy/kubernetes/base/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neuroca-api
  labels:
    app: neuroca
    component: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: neuroca
      component: api
  template:
    metadata:
      labels:
        app: neuroca
        component: api
    spec:
      containers:
      - name: api
        image: neuroca-api:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: ENVIRONMENT
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: LOG_LEVEL
        - name: REDIS_HOST
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: REDIS_HOST
        - name: REDIS_PORT
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: REDIS_PORT
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: REDIS_PASSWORD
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: MONGODB_URI
        - name: POSTGRES_HOST
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: POSTGRES_HOST
        - name: POSTGRES_PORT
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: POSTGRES_PORT
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: POSTGRES_PASSWORD
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: OPENAI_API_KEY
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: ANTHROPIC_API_KEY
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: JWT_SECRET_KEY
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: logs-volume
          mountPath: /app/logs
      volumes:
      - name: config-volume
        configMap:
          name: neuroca-app-config
      - name: logs-volume
        emptyDir: {}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neuroca-worker
  labels:
    app: neuroca
    component: worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: neuroca
      component: worker
  template:
    metadata:
      labels:
        app: neuroca
        component: worker
    spec:
      containers:
      - name: worker
        image: neuroca-worker:latest
        imagePullPolicy: IfNotPresent
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: ENVIRONMENT
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: LOG_LEVEL
        - name: REDIS_HOST
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: REDIS_HOST
        - name: REDIS_PORT
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: REDIS_PORT
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: REDIS_PASSWORD
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: MONGODB_URI
        - name: POSTGRES_HOST
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: POSTGRES_HOST
        - name: POSTGRES_PORT
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: POSTGRES_PORT
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: POSTGRES_PASSWORD
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: OPENAI_API_KEY
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: ANTHROPIC_API_KEY
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: logs-volume
          mountPath: /app/logs
      volumes:
      - name: config-volume
        configMap:
          name: neuroca-app-config
      - name: logs-volume
        emptyDir: {}
```

### 5.5. Kubernetes ConfigMap Template: `deploy/kubernetes/base/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: neuroca-config
data:
  ENVIRONMENT: production
  LOG_LEVEL: info
  REDIS_HOST: redis
  REDIS_PORT: "6379"
  POSTGRES_HOST: postgres
  POSTGRES_PORT: "5432"
  POSTGRES_DB: neuroca
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: neuroca-app-config
data:
  app.yaml: |
    # NeuroCognitive Architecture - Production Configuration
    
    # Application configuration
    app:
      name: NeuroCognitive Architecture
      version: 0.1.0
      description: Brain-inspired three-tiered memory system for LLMs
      environment: production
      debug: false
      log_level: info
    
    # API configuration
    api:
      host: 0.0.0.0
      port: 8000
      cors:
        allowed_origins:
          - https://app.example.com
        allowed_methods:
          - GET
          - POST
          - PUT
          - DELETE
        allowed_headers:
          - Authorization
          - Content-Type
      rate_limiting:
        enabled: true
        rate: 100
        period: 60
    
    # Memory configuration
    memory:
      # Short-Term Memory configuration
      stm:
        provider: redis
        ttl: 10800  # 3 hours in seconds
        max_items: 1000
        health:
          base_score: 80
          decay_rate: 0.1
          promotion_threshold: 90
          demotion_threshold: 30
        connection:
          host: ${REDIS_HOST}
          port: ${REDIS_PORT}
          db: 0
          password: ${REDIS_PASSWORD}
    
      # Medium-Term Memory configuration
      mtm:
        provider: mongodb
        ttl: 1209600  # 14 days in seconds
        max_items: 10000
        health:
          base_score: 60
          decay_rate: 0.05
          promotion_threshold: 80
          demotion_threshold: 20
        connection:
          uri: ${MONGODB_URI}
          database: neuroca
          collection: mtm_memories
    
      # Long-Term Memory configuration
      ltm:
        provider: postgres
        ttl: null  # No expiration
        max_items: 100000
        health:
          base_score: 40
          decay_rate: 0.01
          promotion_threshold: 70
          demotion_threshold: 10
        connection:
          host: ${POSTGRES_HOST}
          port: ${POSTGRES_PORT}
          database: ${POSTGRES_DB}
          user: ${POSTGRES_USER}
          password: ${POSTGRES_PASSWORD}
    
    # Advanced components configuration
    components:
      # Lymphatic System configuration
      lymphatic:
        enabled: true
        consolidation_interval: 3600  # 1 hour in seconds
        batch_size: 100
        max_concurrent_tasks: 5
        schedule:
          - time: "*/30 * * * *"  # Every 30 minutes
            operation: "merge_redundant"
          - time: "0 */2 * * *"   # Every 2 hours
            operation: "abstract_concepts"
          - time: "0 0 * * *"     # Every day at midnight
            operation: "full_consolidation"
    
      # Neural Tubules configuration
      neural_tubules:
        enabled: true
        connection_strength_threshold: 0.5
        max_connections_per_memory: 50
        reinforcement_factor: 0.1
        decay_factor: 0.01
        similarity_threshold: 0.7
    
      # Temporal Annealing configuration
      temporal_annealing:
        enabled: true
        schedule:
          - phase: fast
            interval: 300  # 5 minutes in seconds
            intensity: 0.2
          - phase: medium
            interval: 3600  # 1 hour in seconds
            intensity: 0.5
          - phase: slow
            interval: 86400  # 24 hours in seconds
            intensity: 1.0
    
    # LLM integration configuration
    llm:
      default_provider: openai
      context_window_size: 4096
      max_tokens: 1000
      providers:
        openai:
          api_key: ${OPENAI_API_KEY}
          model: gpt-4
          temperature: 0.7
          timeout: 30
        anthropic:
          api_key: ${ANTHROPIC_API_KEY}
          model: claude-2
          temperature: 0.7
          timeout: 30
    
    # Embedding configuration
    embedding:
      provider: openai
      model: text-embedding-ada-002
      dimensions: 1536
      batch_size: 100
      cache:
        enabled: true
        ttl: 86400  # 24 hours in seconds
    
    # Security configuration
    security:
      jwt:
        secret_key: ${JWT_SECRET_KEY}
        algorithm: HS256
        access_token_expire_minutes: 30
      encryption:
        enabled: true
        algorithm: AES-256-GCM
        key_rotation_days: 30
    
    # Monitoring configuration
    monitoring:
      metrics:
        enabled: true
        prometheus:
          enabled: true
          port: 9090
      logging:
        level: ${LOG_LEVEL}
        format: json
        output:
          console: true
          file: true
          file_path: logs/neuroca.log
      tracing:
        enabled: true
        sampling_rate: 0.1
```

### 5.6. Kubernetes Secret Template: `deploy/kubernetes/base/secret.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: neuroca-secrets
type: Opaque
data:
  # These values should be base64 encoded in a real deployment
  REDIS_PASSWORD: cGFzc3dvcmQ=  # "password"
  MONGODB_URI: bW9uZ29kYjovL3VzZXI6cGFzc3dvcmRAbW9uZ29kYjoyNzAxNy9uZXVyb2Nh  # "mongodb://user:password@mongodb:27017/neuroca"
  POSTGRES_USER: cG9zdGdyZXM=  # "postgres"
  POSTGRES_PASSWORD: cGFzc3dvcmQ=  # "password"
  OPENAI_API_KEY: c2stZXhhbXBsZQ==  # "sk-example"
  ANTHROPIC_API_KEY: c2stZXhhbXBsZQ==  # "sk-example"
  JWT_SECRET_KEY: c2VjcmV0X2tleQ==  # "secret_key"
```

### 5.7. Kubernetes Service Template: `deploy/kubernetes/base/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: neuroca-api
  labels:
    app: neuroca
    component: api
spec:
  selector:
    app: neuroca
    component: api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  labels:
    app: neuroca
    component: redis
spec:
  selector:
    app: neuroca
    component: redis
  ports:
  - port: 6379
    targetPort: 6379
    protocol: TCP
    name: redis
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
  labels:
    app: neuroca
    component: mongodb
spec:
  selector:
    app: neuroca
    component: mongodb
  ports:
  - port: 27017
    targetPort: 27017
    protocol: TCP
    name: mongodb
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  labels:
    app: neuroca
    component: postgres
spec:
  selector:
    app: neuroca
    component: postgres
  ports:
  - port: 5432
    targetPort: 5432
    protocol: TCP
    name: postgres
  type: ClusterIP
```

### 5.8. Kubernetes Ingress Template: `deploy/kubernetes/base/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: neuroca-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /$1
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.neuroca.example.com
    secretName: neuroca-tls
  rules:
  - host: api.neuroca.example.com
    http:
      paths:
      - path: /(.*)
        pathType: Prefix
        backend:
          service:
            name: neuroca-api
            port:
              number: 80
```

### 5.9. Prometheus Configuration Template: `config/monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
    - targets: ['localhost:9090']

  - job_name: 'neuroca-api'
    metrics_path: /metrics
    static_configs:
    - targets: ['api:8000']

  - job_name: 'neuroca-worker'
    metrics_path: /metrics
    static_configs:
    - targets: ['worker:8000']

  - job_name: 'redis'
    static_configs:
    - targets: ['redis:9121']

  - job_name: 'mongodb'
    static_configs:
    - targets: ['mongodb-exporter:9216']

  - job_name: 'postgres'
    static_configs:
    - targets: ['postgres-exporter:9187']
```

### 5.10. Nginx Configuration Template: `config/nginx/nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; img-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'";
    add_header Referrer-Policy no-referrer-when-downgrade;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # Gzip Settings
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Include server configurations
    include /etc/nginx/conf.d/*.conf;
}
```

### 5.11. Nginx Server Configuration Template: `config/nginx/conf.d/default.conf`

```nginx
server {
    listen 80;
    server_name _;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.neuroca.example.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/neuroca.crt;
    ssl_certificate_key /etc/nginx/ssl/neuroca.key;
    
    # API Proxy
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://api:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # API Documentation
    location /api/docs {
        proxy_pass http://api:8000/api/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health Check
    location /health {
        proxy_pass http://api:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Allow internal access only
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }
    
    # Metrics
    location /metrics {
        proxy_pass http://api:8000/metrics;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Allow internal access only
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }
    
    # Root path
    location / {
        return 301 /api/docs;
    }
    
    # Error pages
    error_page 404 /404.html;
    location = /404.html {
        root /usr/share/nginx/html;
        internal;
    }
    
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
        internal;
    }
}
```