"""
Core Constants for the NeuroCognitive Architecture (NCA)

This module defines all global constants used throughout the NeuroCognitive Architecture system.
Constants are organized by functional domain and include comprehensive documentation.

Usage:
    from neuroca.core.constants import MEMORY_CONSTANTS, HEALTH_CONSTANTS
    
    retention_period = MEMORY_CONSTANTS.SHORT_TERM_RETENTION_PERIOD
    critical_health_threshold = HEALTH_CONSTANTS.CRITICAL_THRESHOLD

Note:
    - All constants are immutable and should be treated as read-only
    - Constants are organized into namespaces using dataclasses to provide structure
    - When adding new constants, place them in the appropriate namespace or create a new one if needed
"""

import os
from dataclasses import dataclass
from typing import Final


# System Constants
@dataclass(frozen=True)
class SystemConstants:
    """System-wide constants for configuration and operation."""
    
    # Version information
    VERSION: Final[str] = "0.1.0"
    API_VERSION: Final[str] = "v1"
    
    # Environment settings
    ENV_PRODUCTION: Final[str] = "production"
    ENV_DEVELOPMENT: Final[str] = "development"
    ENV_TESTING: Final[str] = "testing"
    CURRENT_ENV: Final[str] = os.getenv("NEUROCA_ENV", "development")
    
    # Default paths
    CONFIG_DIR: Final[str] = os.getenv("NEUROCA_CONFIG_DIR", "config")
    DATA_DIR: Final[str] = os.getenv("NEUROCA_DATA_DIR", "data")
    LOG_DIR: Final[str] = os.getenv("NEUROCA_LOG_DIR", "logs")
    
    # Default timeouts (in seconds)
    DEFAULT_TIMEOUT: Final[int] = 30
    EXTENDED_TIMEOUT: Final[int] = 120
    
    # Concurrency settings
    DEFAULT_WORKERS: Final[int] = 4
    MAX_WORKERS: Final[int] = 16


# Memory System Constants
@dataclass(frozen=True)
class MemoryConstants:
    """Constants related to the three-tiered memory system."""
    
    # Memory tier identifiers
    WORKING_MEMORY: Final[str] = "working_memory"
    SHORT_TERM_MEMORY: Final[str] = "short_term_memory"
    LONG_TERM_MEMORY: Final[str] = "long_term_memory"
    
    # Memory capacity limits (number of items)
    WORKING_MEMORY_CAPACITY: Final[int] = 7  # Miller's Law: 7±2 items
    SHORT_TERM_MEMORY_CAPACITY: Final[int] = 100
    LONG_TERM_MEMORY_CAPACITY: Final[int] = 10000
    
    # Retention periods (in seconds)
    WORKING_MEMORY_RETENTION: Final[int] = 60  # 1 minute
    SHORT_TERM_RETENTION_PERIOD: Final[int] = 3600  # 1 hour
    LONG_TERM_RETENTION_PERIOD: Final[int] = 2592000  # 30 days
    
    # Memory importance thresholds (0.0 to 1.0)
    LOW_IMPORTANCE_THRESHOLD: Final[float] = 0.3
    MEDIUM_IMPORTANCE_THRESHOLD: Final[float] = 0.6
    HIGH_IMPORTANCE_THRESHOLD: Final[float] = 0.9
    
    # Memory consolidation settings
    CONSOLIDATION_INTERVAL: Final[int] = 300  # 5 minutes
    CONSOLIDATION_BATCH_SIZE: Final[int] = 50
    
    # Embedding dimensions
    EMBEDDING_DIMENSIONS: Final[int] = 1536  # Default for many LLMs
    
    # Vector similarity thresholds
    SIMILARITY_THRESHOLD: Final[float] = 0.75
    HIGH_SIMILARITY_THRESHOLD: Final[float] = 0.9


# Health System Constants
@dataclass(frozen=True)
class HealthConstants:
    """Constants related to the health dynamics system."""
    
    # Health attribute ranges
    MIN_HEALTH_VALUE: Final[int] = 0
    MAX_HEALTH_VALUE: Final[int] = 100
    DEFAULT_HEALTH_VALUE: Final[int] = 80
    
    # Health thresholds
    CRITICAL_THRESHOLD: Final[int] = 20
    LOW_THRESHOLD: Final[int] = 40
    MODERATE_THRESHOLD: Final[int] = 60
    OPTIMAL_THRESHOLD: Final[int] = 80
    
    # Health decay rates (points per hour)
    SLOW_DECAY_RATE: Final[float] = 0.5
    NORMAL_DECAY_RATE: Final[float] = 1.0
    RAPID_DECAY_RATE: Final[float] = 2.0
    
    # Recovery rates (points per hour)
    SLOW_RECOVERY_RATE: Final[float] = 1.0
    NORMAL_RECOVERY_RATE: Final[float] = 2.0
    RAPID_RECOVERY_RATE: Final[float] = 4.0
    
    # Health check intervals (in seconds)
    HEALTH_CHECK_INTERVAL: Final[int] = 300  # 5 minutes
    
    # Health attribute weights (must sum to 1.0)
    ATTRIBUTE_WEIGHTS: Final[dict[str, float]] = {
        "energy": 0.25,
        "stability": 0.25,
        "coherence": 0.25,
        "responsiveness": 0.25
    }


# LLM Integration Constants
@dataclass(frozen=True)
class LLMConstants:
    """Constants related to LLM integration."""
    
    # Supported LLM providers
    PROVIDER_OPENAI: Final[str] = "openai"
    PROVIDER_ANTHROPIC: Final[str] = "anthropic"
    PROVIDER_COHERE: Final[str] = "cohere"
    PROVIDER_HUGGINGFACE: Final[str] = "huggingface"
    PROVIDER_LOCAL: Final[str] = "local"
    
    # Default models by provider
    DEFAULT_MODELS: Final[dict[str, str]] = {
        "openai": "gpt-4",
        "anthropic": "claude-2",
        "cohere": "command",
        "huggingface": "mistral-7b",
        "local": "llama-2-13b"
    }
    
    # Token limits by model (approximate)
    TOKEN_LIMITS: Final[dict[str, int]] = {
        "gpt-3.5-turbo": 4096,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "claude-2": 100000,
        "command": 4096,
        "mistral-7b": 8192,
        "llama-2-13b": 4096
    }
    
    # Default parameters
    DEFAULT_TEMPERATURE: Final[float] = 0.7
    DEFAULT_TOP_P: Final[float] = 0.9
    DEFAULT_MAX_TOKENS: Final[int] = 1024
    
    # Rate limiting (requests per minute)
    DEFAULT_RATE_LIMIT: Final[int] = 60
    
    # Retry settings
    MAX_RETRIES: Final[int] = 3
    RETRY_DELAY: Final[int] = 2  # seconds


# Cognitive Process Constants
@dataclass(frozen=True)
class CognitiveConstants:
    """Constants related to cognitive processes."""
    
    # Cognitive process types
    PROCESS_REASONING: Final[str] = "reasoning"
    PROCESS_PLANNING: Final[str] = "planning"
    PROCESS_LEARNING: Final[str] = "learning"
    PROCESS_DECISION: Final[str] = "decision_making"
    PROCESS_CREATIVITY: Final[str] = "creativity"
    
    # Process priority levels
    PRIORITY_LOW: Final[int] = 0
    PRIORITY_MEDIUM: Final[int] = 1
    PRIORITY_HIGH: Final[int] = 2
    PRIORITY_CRITICAL: Final[int] = 3
    
    # Process states
    STATE_IDLE: Final[str] = "idle"
    STATE_ACTIVE: Final[str] = "active"
    STATE_PAUSED: Final[str] = "paused"
    STATE_COMPLETED: Final[str] = "completed"
    STATE_FAILED: Final[str] = "failed"
    
    # Default process timeouts (seconds)
    PROCESS_TIMEOUT: Final[int] = 60
    
    # Cognitive load thresholds (0.0 to 1.0)
    LOW_LOAD_THRESHOLD: Final[float] = 0.3
    MEDIUM_LOAD_THRESHOLD: Final[float] = 0.6
    HIGH_LOAD_THRESHOLD: Final[float] = 0.8
    OVERLOAD_THRESHOLD: Final[float] = 0.95


# Error and Logging Constants
@dataclass(frozen=True)
class LoggingConstants:
    """Constants related to logging and error handling."""
    
    # Log levels
    LOG_LEVEL_DEBUG: Final[str] = "DEBUG"
    LOG_LEVEL_INFO: Final[str] = "INFO"
    LOG_LEVEL_WARNING: Final[str] = "WARNING"
    LOG_LEVEL_ERROR: Final[str] = "ERROR"
    LOG_LEVEL_CRITICAL: Final[str] = "CRITICAL"
    
    # Default log level by environment
    DEFAULT_LOG_LEVELS: Final[dict[str, str]] = {
        "development": "DEBUG",
        "testing": "INFO",
        "production": "WARNING"
    }
    
    # Log formats
    DEFAULT_LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
    
    # Error codes
    ERROR_MEMORY_FULL: Final[int] = 1001
    ERROR_HEALTH_CRITICAL: Final[int] = 1002
    ERROR_LLM_CONNECTION: Final[int] = 1003
    ERROR_PROCESS_TIMEOUT: Final[int] = 1004
    ERROR_INVALID_INPUT: Final[int] = 1005
    ERROR_UNAUTHORIZED: Final[int] = 1006
    
    # Error messages
    ERROR_MESSAGES: Final[dict[int, str]] = {
        1001: "Memory capacity exceeded",
        1002: "System health is in critical state",
        1003: "Failed to connect to LLM provider",
        1004: "Cognitive process timed out",
        1005: "Invalid input provided",
        1006: "Unauthorized access attempt"
    }


# API Constants
@dataclass(frozen=True)
class APIConstants:
    """Constants related to API functionality."""
    
    # HTTP methods
    METHOD_GET: Final[str] = "GET"
    METHOD_POST: Final[str] = "POST"
    METHOD_PUT: Final[str] = "PUT"
    METHOD_DELETE: Final[str] = "DELETE"
    METHOD_PATCH: Final[str] = "PATCH"
    
    # Status codes
    STATUS_OK: Final[int] = 200
    STATUS_CREATED: Final[int] = 201
    STATUS_ACCEPTED: Final[int] = 202
    STATUS_BAD_REQUEST: Final[int] = 400
    STATUS_UNAUTHORIZED: Final[int] = 401
    STATUS_FORBIDDEN: Final[int] = 403
    STATUS_NOT_FOUND: Final[int] = 404
    STATUS_TIMEOUT: Final[int] = 408
    STATUS_SERVER_ERROR: Final[int] = 500
    
    # Content types
    CONTENT_TYPE_JSON: Final[str] = "application/json"
    CONTENT_TYPE_TEXT: Final[str] = "text/plain"
    
    # Default pagination
    DEFAULT_PAGE_SIZE: Final[int] = 20
    MAX_PAGE_SIZE: Final[int] = 100
    
    # Rate limiting
    API_RATE_LIMIT: Final[int] = 100  # requests per minute
    API_RATE_LIMIT_WINDOW: Final[int] = 60  # seconds


# Export all constant namespaces
SYSTEM_CONSTANTS = SystemConstants()
MEMORY_CONSTANTS = MemoryConstants()
HEALTH_CONSTANTS = HealthConstants()
LLM_CONSTANTS = LLMConstants()
COGNITIVE_CONSTANTS = CognitiveConstants()
LOGGING_CONSTANTS = LoggingConstants()
API_CONSTANTS = APIConstants()

# For backwards compatibility and direct imports
__all__ = [
    'SYSTEM_CONSTANTS',
    'MEMORY_CONSTANTS',
    'HEALTH_CONSTANTS',
    'LLM_CONSTANTS',
    'COGNITIVE_CONSTANTS',
    'LOGGING_CONSTANTS',
    'API_CONSTANTS',
]