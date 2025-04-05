"""
Request Schema Definitions for NeuroCognitive Architecture API

This module contains all Pydantic models that define the structure and validation
for incoming API requests in the NeuroCognitive Architecture system. These schemas
ensure proper data validation, type checking, and provide clear documentation for
API consumers.

The schemas are organized by functional domain and include comprehensive validation
rules to ensure data integrity before processing by the application core.

Usage:
    from neuroca.api.schemas.requests import MemoryCreateRequest

    @router.post("/memories")
    async def create_memory(request: MemoryCreateRequest):
        # Request is already validated by Pydantic
        memory_data = request.dict()
        # Process the validated data...
"""

import datetime
import enum
import logging
import re
import uuid
from typing import Any, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    confloat,
    conint,
    root_validator,
    validator,
)

# Configure module logger
logger = logging.getLogger(__name__)


class HealthMetricsRequest(BaseModel):
    """
    Request schema for updating or creating health metrics for the cognitive system.
    
    Health metrics represent the current state of the system's cognitive health,
    including energy levels, stress, and other biological-inspired parameters.
    """
    energy_level: confloat(ge=0.0, le=1.0) = Field(
        ..., 
        description="Current energy level of the system (0.0 to 1.0)"
    )
    stress_level: confloat(ge=0.0, le=1.0) = Field(
        ..., 
        description="Current stress level of the system (0.0 to 1.0)"
    )
    cognitive_load: confloat(ge=0.0, le=1.0) = Field(
        ..., 
        description="Current cognitive load of the system (0.0 to 1.0)"
    )
    timestamp: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.utcnow,
        description="Timestamp of the health metrics measurement (UTC)"
    )
    
    @validator('timestamp')
    def ensure_utc(cls, v):
        """Ensure timestamp is in UTC timezone."""
        if v and v.tzinfo is not None and v.tzinfo != datetime.timezone.utc:
            return v.astimezone(datetime.timezone.utc)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "energy_level": 0.75,
                "stress_level": 0.3,
                "cognitive_load": 0.5,
                "timestamp": "2023-10-15T14:30:00Z"
            }
        }


class MemoryPriority(str, enum.Enum):
    """Priority levels for memory items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryTier(str, enum.Enum):
    """Memory tier classification for the three-tiered memory system."""
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class MemoryCreateRequest(BaseModel):
    """
    Request schema for creating a new memory item in the cognitive system.
    
    Memory items are the fundamental units of information storage in the
    NeuroCognitive Architecture, supporting the three-tiered memory system.
    """
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=10000,
        description="The content of the memory to be stored"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata associated with the memory"
    )
    initial_tier: MemoryTier = Field(
        default=MemoryTier.WORKING,
        description="The initial memory tier for placement"
    )
    priority: MemoryPriority = Field(
        default=MemoryPriority.MEDIUM,
        description="Priority level affecting memory retention and recall"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorizing and retrieving memories"
    )
    expiration: Optional[datetime.datetime] = Field(
        default=None,
        description="Optional expiration time for temporary memories"
    )
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate that tags are properly formatted."""
        if not all(isinstance(tag, str) for tag in v):
            raise ValueError("All tags must be strings")
        
        if not all(re.match(r'^[a-zA-Z0-9_-]+$', tag) for tag in v):
            raise ValueError("Tags must contain only alphanumeric characters, underscores, and hyphens")
        
        return v
    
    @validator('expiration')
    def validate_expiration(cls, v):
        """Ensure expiration is in the future if provided."""
        if v and v < datetime.datetime.now(datetime.timezone.utc):
            raise ValueError("Expiration time must be in the future")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "content": "The user prefers to be addressed as 'Dr. Smith' in conversations.",
                "metadata": {"source": "conversation", "confidence": 0.92},
                "initial_tier": "working",
                "priority": "high",
                "tags": ["preference", "user-info", "conversation"],
                "expiration": None
            }
        }


class MemoryQueryRequest(BaseModel):
    """
    Request schema for querying memories from the cognitive system.
    
    Supports various query parameters for flexible memory retrieval across
    the three-tiered memory system.
    """
    query: str = Field(
        ...,
        min_length=1,
        description="Search query text or semantic query"
    )
    tiers: list[MemoryTier] = Field(
        default_factory=lambda: list(MemoryTier),
        description="Memory tiers to search in"
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Filter by tags (optional)"
    )
    min_priority: Optional[MemoryPriority] = Field(
        default=None,
        description="Minimum priority level to include"
    )
    limit: Optional[conint(ge=1, le=100)] = Field(
        default=10,
        description="Maximum number of results to return (1-100)"
    )
    include_expired: bool = Field(
        default=False,
        description="Whether to include expired memories in results"
    )
    semantic_search: bool = Field(
        default=True,
        description="Whether to use semantic search or exact matching"
    )
    
    @root_validator
    def check_query_parameters(cls, values):
        """Validate that the query parameters make sense together."""
        query = values.get('query')
        semantic_search = values.get('semantic_search')
        
        if semantic_search and (not query or len(query.strip()) < 3):
            raise ValueError("Semantic search requires a query of at least 3 characters")
        
        # Log debug information about the query
        logger.debug(
            "Memory query request: query='%s', semantic=%s, tiers=%s, tags=%s", 
            query, semantic_search, values.get('tiers'), values.get('tags')
        )
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "query": "user preferences",
                "tiers": ["working", "short_term", "long_term"],
                "tags": ["preference", "user-info"],
                "min_priority": "medium",
                "limit": 20,
                "include_expired": False,
                "semantic_search": True
            }
        }


class LLMIntegrationRequest(BaseModel):
    """
    Request schema for LLM integration operations.
    
    This schema defines the structure for requests that involve interaction
    with integrated Large Language Models.
    """
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=32000,
        description="The prompt to send to the LLM"
    )
    model_id: str = Field(
        ...,
        description="Identifier for the LLM model to use"
    )
    temperature: confloat(ge=0.0, le=2.0) = Field(
        default=0.7,
        description="Temperature parameter for controlling randomness (0.0-2.0)"
    )
    max_tokens: conint(ge=1, le=32000) = Field(
        default=1000,
        description="Maximum number of tokens to generate"
    )
    include_memory_context: bool = Field(
        default=True,
        description="Whether to include relevant memories as context"
    )
    memory_query: Optional[str] = Field(
        default=None,
        description="Optional query to retrieve specific memories for context"
    )
    system_message: Optional[str] = Field(
        default=None,
        description="Optional system message to prepend to the conversation"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate that the prompt is properly formatted and safe."""
        # Check for potential prompt injection patterns
        suspicious_patterns = [
            r"ignore previous instructions",
            r"disregard .*?instructions",
            r"ignore .*?constraints",
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                logger.warning(f"Potentially unsafe prompt detected: {v[:100]}...")
                raise ValueError("Prompt contains potentially unsafe instructions")
        
        return v
    
    @root_validator
    def validate_memory_context(cls, values):
        """Ensure memory query is provided if memory context is requested."""
        include_memory = values.get('include_memory_context')
        memory_query = values.get('memory_query')
        
        if include_memory and not memory_query:
            logger.info("Memory context requested but no memory query provided, using prompt as query")
            values['memory_query'] = values.get('prompt')[:200]  # Use first 200 chars of prompt
            
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "What are the user's food preferences?",
                "model_id": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500,
                "include_memory_context": True,
                "memory_query": "user food preferences",
                "system_message": "You are a helpful assistant with access to the user's memory."
            }
        }


class CognitiveProcessRequest(BaseModel):
    """
    Request schema for triggering cognitive processes in the system.
    
    Cognitive processes include memory consolidation, forgetting, association building,
    and other operations that mimic human cognitive functions.
    """
    process_type: str = Field(
        ...,
        description="Type of cognitive process to execute"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters specific to the cognitive process"
    )
    priority: MemoryPriority = Field(
        default=MemoryPriority.MEDIUM,
        description="Priority level for the cognitive process"
    )
    async_execution: bool = Field(
        default=True,
        description="Whether to execute the process asynchronously"
    )
    
    @validator('process_type')
    def validate_process_type(cls, v):
        """Validate that the process type is supported."""
        valid_processes = [
            "memory_consolidation",
            "memory_forgetting",
            "association_building",
            "concept_formation",
            "knowledge_integration",
            "emotional_processing",
            "attention_shift",
            "cognitive_reflection"
        ]
        
        if v not in valid_processes:
            raise ValueError(f"Process type must be one of: {', '.join(valid_processes)}")
        
        return v
    
    @root_validator
    def validate_parameters(cls, values):
        """Validate that the required parameters for the process type are provided."""
        process_type = values.get('process_type')
        parameters = values.get('parameters', {})
        
        # Define required parameters for each process type
        required_params = {
            "memory_consolidation": ["target_tier", "selection_criteria"],
            "memory_forgetting": ["forgetting_threshold", "memory_tier"],
            "association_building": ["source_items", "association_strength"],
            "concept_formation": ["input_memories", "concept_name"],
            "knowledge_integration": ["knowledge_source", "integration_strategy"],
            "emotional_processing": ["emotion_type", "intensity"],
            "attention_shift": ["focus_target", "attention_duration"],
            "cognitive_reflection": ["reflection_target", "depth"]
        }
        
        if process_type in required_params:
            for param in required_params[process_type]:
                if param not in parameters:
                    raise ValueError(f"Missing required parameter '{param}' for process type '{process_type}'")
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "process_type": "memory_consolidation",
                "parameters": {
                    "target_tier": "long_term",
                    "selection_criteria": {
                        "min_priority": "high",
                        "min_access_count": 3,
                        "min_age_hours": 24
                    }
                },
                "priority": "medium",
                "async_execution": True
            }
        }


class UserProfileUpdateRequest(BaseModel):
    """
    Request schema for updating user profile information.
    
    User profiles contain information about the human users interacting with
    the cognitive system, helping to personalize interactions.
    """
    name: Optional[str] = Field(
        default=None,
        description="User's name"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="User's email address"
    )
    preferences: Optional[dict[str, Any]] = Field(
        default=None,
        description="User preferences for system interaction"
    )
    communication_style: Optional[str] = Field(
        default=None,
        description="Preferred communication style (formal, casual, technical, etc.)"
    )
    interests: Optional[list[str]] = Field(
        default=None,
        description="User's interests and topics they care about"
    )
    
    @validator('communication_style')
    def validate_communication_style(cls, v):
        """Validate that the communication style is supported."""
        if v is not None:
            valid_styles = ["formal", "casual", "technical", "simple", "detailed", "concise"]
            if v not in valid_styles:
                raise ValueError(f"Communication style must be one of: {', '.join(valid_styles)}")
        return v
    
    @root_validator
    def ensure_not_empty(cls, values):
        """Ensure that at least one field is being updated."""
        if all(v is None for v in values.values()):
            raise ValueError("At least one field must be provided for update")
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Dr. Jane Smith",
                "email": "jane.smith@example.com",
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "language": "en-US"
                },
                "communication_style": "technical",
                "interests": ["artificial intelligence", "cognitive science", "neurology"]
            }
        }


class SystemConfigUpdateRequest(BaseModel):
    """
    Request schema for updating system configuration parameters.
    
    System configuration controls various aspects of the cognitive system's
    behavior and performance characteristics.
    """
    memory_settings: Optional[dict[str, Any]] = Field(
        default=None,
        description="Settings for the memory subsystem"
    )
    health_dynamics: Optional[dict[str, Any]] = Field(
        default=None,
        description="Settings for health dynamics simulation"
    )
    llm_integration: Optional[dict[str, Any]] = Field(
        default=None,
        description="Settings for LLM integration"
    )
    cognitive_processes: Optional[dict[str, Any]] = Field(
        default=None,
        description="Settings for cognitive processes"
    )
    
    @root_validator
    def validate_config_structure(cls, values):
        """Validate the structure of configuration settings."""
        # Validate memory settings if provided
        memory_settings = values.get('memory_settings')
        if memory_settings is not None:
            valid_memory_keys = [
                "working_memory_capacity", 
                "short_term_retention_period",
                "long_term_consolidation_threshold",
                "forgetting_rate",
                "association_strength_decay"
            ]
            
            for key in memory_settings:
                if key not in valid_memory_keys:
                    raise ValueError(f"Invalid memory setting: {key}")
        
        # Validate health dynamics settings if provided
        health_dynamics = values.get('health_dynamics')
        if health_dynamics is not None:
            valid_health_keys = [
                "energy_decay_rate",
                "stress_recovery_rate",
                "cognitive_load_threshold",
                "rest_efficiency",
                "performance_degradation_factors"
            ]
            
            for key in health_dynamics:
                if key not in valid_health_keys:
                    raise ValueError(f"Invalid health dynamics setting: {key}")
        
        # Ensure at least one setting is being updated
        if all(v is None for v in values.values()):
            raise ValueError("At least one configuration category must be provided for update")
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "memory_settings": {
                    "working_memory_capacity": 10,
                    "short_term_retention_period": 86400,  # 24 hours in seconds
                    "long_term_consolidation_threshold": 3,
                    "forgetting_rate": 0.05
                },
                "health_dynamics": {
                    "energy_decay_rate": 0.01,
                    "stress_recovery_rate": 0.2,
                    "cognitive_load_threshold": 0.8
                },
                "llm_integration": {
                    "default_model": "gpt-4",
                    "context_window_tokens": 8000,
                    "temperature": 0.7
                },
                "cognitive_processes": {
                    "consolidation_frequency": 3600,  # 1 hour in seconds
                    "association_building_threshold": 0.6
                }
            }
        }


class SessionInitRequest(BaseModel):
    """
    Request schema for initializing a new cognitive session.
    
    A cognitive session represents a continuous interaction period with
    the cognitive system, maintaining context and state.
    """
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="ID of the user initiating the session (if authenticated)"
    )
    session_type: str = Field(
        default="standard",
        description="Type of session to initialize"
    )
    initial_context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Initial context information for the session"
    )
    session_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for session configuration"
    )
    
    @validator('session_type')
    def validate_session_type(cls, v):
        """Validate that the session type is supported."""
        valid_types = ["standard", "focused", "creative", "analytical", "emergency"]
        if v not in valid_types:
            raise ValueError(f"Session type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "session_type": "analytical",
                "initial_context": {
                    "task": "data analysis",
                    "domain": "financial",
                    "urgency": "medium"
                },
                "session_parameters": {
                    "timeout_minutes": 60,
                    "memory_priority": "high",
                    "cognitive_focus": "problem_solving"
                }
            }
        }


# Additional request schemas can be added as the API expands