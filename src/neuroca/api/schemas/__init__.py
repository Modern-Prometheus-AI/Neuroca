"""
API Schema Definitions
======================

This module contains Pydantic schema definitions for the NeuroCognitive Architecture (NCA) API.
These schemas are used for request/response validation, serialization, and documentation.

The schemas are organized by domain and functionality, with common base schemas
providing shared functionality across different endpoints.

Usage:
------
Import specific schemas directly:
    from neuroca.api.schemas import MemorySchema, CognitiveStateSchema

Or import domain-specific schema collections:
    from neuroca.api.schemas.memory import WorkingMemorySchema, LongTermMemorySchema

Structure:
----------
- Base schemas: Common validation and serialization logic
- Request schemas: Input validation for API endpoints
- Response schemas: Output formatting for API responses
- Domain-specific schemas: Organized by NCA subsystem

Security:
---------
All schemas implement proper input validation to prevent injection attacks and
ensure data integrity. Sensitive fields are properly handled with appropriate
serialization controls.
"""

import logging
from typing import Optional

# Import Pydantic for schema definitions
try:
    # Removed unused imports: Extra, Field, ValidationError, confloat, conint, constr, root_validator, validator
    from pydantic import BaseModel
except ImportError:
    logging.critical("Pydantic is required for API schema definitions. Please install it with: pip install pydantic")
    raise

# Setup module logger
logger = logging.getLogger(__name__)

# Version information
__version__ = "0.1.0"

# Import all schema modules to make them available through the package
try:
    # Base schemas
    # User and auth schemas
    from .auth import (
        LoginRequestSchema,
        PermissionSchema,
        RegisterRequestSchema,
        TokenSchema,
        UserSchema,
    )
    from .base import BaseSchema, ErrorSchema, PaginationSchema, ResponseEnvelope
    from .cognitive import (
        AttentionSchema,
        BeliefSchema,
        CognitiveStateSchema,
        EmotionSchema,
        GoalSchema,
        IntentionSchema,
    )
    from .health import (
        EnergyLevelSchema,
        FatigueSchema,
        HealthSchema,
        HealthStatusSchema,
        StressSchema,
    )
    from .integration import (
        CompletionSchema,
        EmbeddingSchema,
        LLMRequestSchema,
        LLMResponseSchema,
        PromptSchema,
    )

    # Domain-specific schemas
    from .memory import (
        EpisodicMemorySchema,
        LongTermMemorySchema,
        MemoryQuerySchema,
        MemorySchema,
        MemoryUpdateSchema,
        ProceduralMemorySchema,
        SemanticMemorySchema,
        WorkingMemorySchema,
    )

    # Export all schemas in a flat namespace for easy imports
    __all__ = [
        # Base schemas
        'BaseSchema', 'ErrorSchema', 'PaginationSchema', 'ResponseEnvelope',
        
        # Memory schemas
        'MemorySchema', 'WorkingMemorySchema', 'LongTermMemorySchema',
        'EpisodicMemorySchema', 'SemanticMemorySchema', 'ProceduralMemorySchema',
        'MemoryQuerySchema', 'MemoryUpdateSchema',
        
        # Cognitive schemas
        'CognitiveStateSchema', 'AttentionSchema', 'EmotionSchema',
        'GoalSchema', 'BeliefSchema', 'IntentionSchema',
        
        # Health schemas
        'HealthSchema', 'EnergyLevelSchema', 'FatigueSchema',
        'StressSchema', 'HealthStatusSchema',
        
        # Integration schemas
        'LLMRequestSchema', 'LLMResponseSchema', 'PromptSchema',
        'CompletionSchema', 'EmbeddingSchema',
        
        # Auth schemas
        'UserSchema', 'TokenSchema', 'LoginRequestSchema',
        'RegisterRequestSchema', 'PermissionSchema'
    ]

except ImportError as e:
    # Log the import error but don't crash - allows partial functionality
    logger.warning(f"Some schema modules could not be imported: {str(e)}")
    logger.warning("The API schema package is partially initialized and may not function correctly.")
    __all__ = []


# Schema registry for dynamic schema lookup
_schema_registry: dict[str, type[BaseModel]] = {}

def register_schema(schema_class: type[BaseModel]) -> type[BaseModel]:
    """
    Register a schema class in the global schema registry.
    
    This decorator allows for runtime schema lookup by name, useful for
    dynamic API handlers and documentation generation.
    
    Args:
        schema_class: The Pydantic model class to register
        
    Returns:
        The original schema class (unchanged)
        
    Example:
        @register_schema
        class MyCustomSchema(BaseModel):
            field1: str
            field2: int
    """
    schema_name = schema_class.__name__
    if schema_name in _schema_registry:
        logger.warning(f"Schema '{schema_name}' already registered. Overwriting previous registration.")
    
    _schema_registry[schema_name] = schema_class
    logger.debug(f"Registered schema: {schema_name}")
    return schema_class


def get_schema(schema_name: str) -> Optional[type[BaseModel]]:
    """
    Retrieve a schema class by name from the registry.
    
    Args:
        schema_name: Name of the schema class to retrieve
        
    Returns:
        The schema class if found, None otherwise
        
    Example:
        UserSchemaClass = get_schema('UserSchema')
        if UserSchemaClass:
            user_instance = UserSchemaClass(username='test', email='test@example.com')
    """
    schema = _schema_registry.get(schema_name)
    if not schema:
        logger.warning(f"Schema '{schema_name}' not found in registry")
    return schema


def list_schemas() -> list[str]:
    """
    List all registered schema names.
    
    Returns:
        List of schema names available in the registry
        
    Example:
        available_schemas = list_schemas()
        print(f"Available schemas: {', '.join(available_schemas)}")
    """
    return list(_schema_registry.keys())


# Register all imported schemas in the registry
for schema_name in __all__:
    if schema_name in globals():
        schema_class = globals()[schema_name]
        if isinstance(schema_class, type) and issubclass(schema_class, BaseModel):
            _schema_registry[schema_name] = schema_class

# Log initialization status
logger.info(f"API schemas initialized with {len(_schema_registry)} registered schemas")
