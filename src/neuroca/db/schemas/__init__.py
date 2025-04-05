"""
Database Schema Module for NeuroCognitive Architecture (NCA).

This module serves as the central point for all database schema definitions in the NCA system.
It provides a unified interface for accessing and managing database schemas across the application,
ensuring consistency and proper organization of data models.

The schema definitions follow SQLAlchemy's declarative base pattern and implement the core
data structures needed for the three-tiered memory system, health dynamics, and other
biological-inspired components of the NCA.

Usage:
    from neuroca.db.schemas import Base, get_all_models
    from neuroca.db.schemas.memory import WorkingMemoryItem

    # Access the declarative base for model definitions
    Base.metadata.create_all(engine)
    
    # Get all model classes for registration or introspection
    all_models = get_all_models()

Note:
    This module should be imported before any model is used to ensure proper
    registration of all models with the SQLAlchemy metadata.
"""

import importlib
import logging
import os
import pkgutil
from typing import Optional

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Configure module logger
logger = logging.getLogger(__name__)

# Convention for constraint naming to ensure consistency across migrations
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=convention)

# Create declarative base with the configured metadata
Base = declarative_base(metadata=metadata)

# Dictionary to store all model classes
_models: dict[str, type[Base]] = {}

def register_model(model_class: type[Base]) -> None:
    """
    Register a model class in the global models registry.
    
    This function is used to keep track of all model classes defined in the application,
    which can be useful for automatic schema generation, migrations, and introspection.
    
    Args:
        model_class: The SQLAlchemy model class to register
        
    Raises:
        ValueError: If a model with the same name is already registered
    """
    model_name = model_class.__name__
    if model_name in _models and _models[model_name] != model_class:
        raise ValueError(f"Model with name '{model_name}' is already registered")
    
    _models[model_name] = model_class
    logger.debug(f"Registered model: {model_name}")

def get_model(model_name: str) -> Optional[type[Base]]:
    """
    Get a model class by its name.
    
    Args:
        model_name: The name of the model class to retrieve
        
    Returns:
        The model class if found, None otherwise
    """
    return _models.get(model_name)

def get_all_models() -> dict[str, type[Base]]:
    """
    Get all registered model classes.
    
    Returns:
        A dictionary mapping model names to model classes
    """
    return _models.copy()

def _import_submodules() -> None:
    """
    Dynamically import all submodules in the schemas package.
    
    This ensures that all model definitions are loaded and registered
    when the schemas package is imported.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for _, module_name, is_pkg in pkgutil.iter_modules([current_dir]):
        if not module_name.startswith('_'):  # Skip private modules
            try:
                importlib.import_module(f"{__name__}.{module_name}")
                logger.debug(f"Imported schema module: {module_name}")
                
                # If it's a package, try to import its models module if it exists
                if is_pkg:
                    try:
                        importlib.import_module(f"{__name__}.{module_name}.models")
                        logger.debug(f"Imported models from package: {module_name}")
                    except ImportError:
                        # It's okay if the package doesn't have a models module
                        pass
            except ImportError as e:
                logger.error(f"Failed to import schema module {module_name}: {str(e)}")

# Initialize the module by importing all submodules
try:
    _import_submodules()
except Exception as e:
    logger.error(f"Error during schema initialization: {str(e)}")

# Export public interface
__all__ = [
    'Base',
    'metadata',
    'register_model',
    'get_model',
    'get_all_models',
]