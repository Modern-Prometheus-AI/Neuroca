"""
Default Configuration Module for NeuroCognitive Architecture (NCA)

This module defines the default configuration settings for the NeuroCognitive Architecture
system. It serves as the base configuration that can be extended or overridden by
environment-specific configurations (development, testing, production).

The configuration is organized into logical sections covering different aspects of the system:
- Core system settings
- Memory tier configurations (working, episodic, semantic)
- Health dynamics parameters
- LLM integration settings
- Database configurations
- API settings
- Logging configuration
- Security settings
- Performance tuning

Usage:
    from neuroca.config import config
    
    # Access configuration values
    db_url = config.DATABASE_URL
    working_memory_capacity = config.MEMORY_TIERS['working']['capacity']

Note: Sensitive values should not be hardcoded here but loaded from environment
variables or secure vaults in the environment-specific configuration files.
"""

import os
from pathlib import Path
from typing import Any

# Base directories
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure required directories exist
for directory in [DATA_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Core system settings
DEBUG = False
TESTING = False
ENV = "production"  # Options: development, testing, production
SECRET_KEY = "CHANGE_ME_IN_PRODUCTION"  # Will be overridden in production
TIMEZONE = "UTC"

# Application metadata
APP_NAME = "NeuroCognitive Architecture"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "A biologically-inspired cognitive architecture for LLMs"

# Memory tier configurations
MEMORY_TIERS = {
    "working": {
        "enabled": True,
        "capacity": 7,  # Miller's Law: 7±2 items
        "decay_rate": 0.1,  # Rate at which items decay from working memory
        "refresh_interval": 60,  # Seconds between memory refresh operations
        "priority_levels": 5,  # Number of priority levels for items
        "storage_backend": "in_memory",  # Options: in_memory, redis
    },
    "episodic": {
        "enabled": True,
        "max_episodes": 1000,
        "consolidation_interval": 3600,  # Seconds between consolidation operations
        "retrieval_strategy": "recency_and_relevance",  # Options: recency, relevance, recency_and_relevance
        "storage_backend": "postgres",  # Options: in_memory, postgres, vector_db
        "embedding_model": "default",  # Model used for creating memory embeddings
        "similarity_threshold": 0.75,  # Threshold for considering memories similar
    },
    "semantic": {
        "enabled": True,
        "consolidation_interval": 86400,  # Seconds (daily consolidation)
        "knowledge_graph_settings": {
            "max_nodes": 10000,
            "max_edges_per_node": 50,
            "edge_weight_decay": 0.01,
        },
        "storage_backend": "postgres",  # Options: in_memory, postgres, vector_db, graph_db
        "embedding_model": "default",
    }
}

# Health dynamics parameters
HEALTH_DYNAMICS = {
    "enabled": True,
    "base_values": {
        "energy": 100,
        "stability": 100,
        "coherence": 100,
    },
    "decay_rates": {
        "energy": 0.05,  # Units per hour
        "stability": 0.02,
        "coherence": 0.03,
    },
    "thresholds": {
        "critical": 20,  # Below this is critical
        "low": 40,       # Below this is low
        "optimal": 80,   # Above this is optimal
    },
    "recovery_rates": {
        "energy": 0.1,
        "stability": 0.05,
        "coherence": 0.07,
    },
    "check_interval": 300,  # Seconds between health checks
}

# LLM integration settings
LLM_INTEGRATION = {
    "provider": "openai",  # Options: openai, anthropic, huggingface, local
    "default_model": "gpt-4",
    "fallback_model": "gpt-3.5-turbo",
    "api_timeout": 30,  # Seconds
    "max_retries": 3,
    "retry_delay": 2,  # Seconds
    "temperature": 0.7,
    "max_tokens": 1000,
    "streaming": True,
    "cache_enabled": True,
    "cache_ttl": 3600,  # Seconds
    "rate_limit": {
        "tokens_per_minute": 90000,
        "requests_per_minute": 60,
    },
}

# Database configurations
DATABASE = {
    "default": {
        "engine": "postgresql",
        "name": "neuroca",
        "user": "neuroca_user",
        "password": "CHANGE_ME_IN_PRODUCTION",  # Will be overridden in production
        "host": "localhost",
        "port": 5432,
        "pool_size": 10,
        "max_overflow": 20,
        "timeout": 30,
    },
    "vector_store": {
        "engine": "pgvector",
        "connection_string": "postgresql://neuroca_user:CHANGE_ME_IN_PRODUCTION@localhost:5432/neuroca_vector",
        "dimension": 1536,  # Default embedding dimension
        "index_type": "ivfflat",  # Options: ivfflat, hnsw
    },
    "cache": {
        "engine": "redis",
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,
        "ssl": False,
    }
}

# Construct database URLs
DATABASE_URL = f"{DATABASE['default']['engine']}://{DATABASE['default']['user']}:{DATABASE['default']['password']}@{DATABASE['default']['host']}:{DATABASE['default']['port']}/{DATABASE['default']['name']}"
VECTOR_DB_URL = DATABASE["vector_store"]["connection_string"]

# API settings
API = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4,
    "cors_origins": ["*"],  # Restrict in production
    "rate_limiting": {
        "enabled": True,
        "rate": "100/minute",
    },
    "authentication": {
        "enabled": True,
        "jwt_expiration": 3600,  # Seconds
        "refresh_token_expiration": 86400,  # Seconds (1 day)
    },
    "documentation": {
        "enabled": True,
        "title": "NeuroCognitive Architecture API",
        "description": "API for interacting with the NeuroCognitive Architecture system",
        "version": "0.1.0",
    }
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": os.path.join(LOGS_DIR, "neuroca.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": os.path.join(LOGS_DIR, "error.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": True,
        },
        "neuroca": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "neuroca.memory": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "neuroca.api": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Security settings
SECURITY = {
    "password_hashing": {
        "algorithm": "bcrypt",
        "rounds": 12,
    },
    "content_security_policy": {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "font-src": ["'self'"],
        "object-src": ["'none'"],
        "media-src": ["'self'"],
        "frame-src": ["'none'"],
    },
    "ssl": {
        "enabled": True,
        "cert_path": None,  # Set in environment-specific config
        "key_path": None,   # Set in environment-specific config
    },
    "session": {
        "cookie_secure": True,
        "cookie_httponly": True,
        "cookie_samesite": "Lax",
        "expiration": 86400,  # Seconds (1 day)
    }
}

# Performance tuning
PERFORMANCE = {
    "cache": {
        "enabled": True,
        "ttl": 3600,  # Seconds
        "max_size": 1000,  # Maximum number of items in memory cache
    },
    "batch_size": 64,  # Default batch size for operations
    "worker_threads": 4,  # Number of worker threads
    "async_processing": True,  # Enable asynchronous processing
}

# Feature flags for gradual rollout and testing
FEATURE_FLAGS = {
    "advanced_memory_consolidation": False,
    "health_dynamics_feedback_loop": False,
    "multi_agent_collaboration": False,
    "external_knowledge_integration": False,
    "adaptive_reasoning": True,
    "emotional_modeling": False,
}

# Development and debugging options (disabled in production)
DEVELOPMENT = {
    "reload_on_change": False,
    "debug_toolbar": False,
    "mock_llm_responses": False,
    "profile_performance": False,
    "trace_memory_operations": False,
}

# Function to get a nested configuration value using dot notation
def get_config(path: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value using dot notation path.
    
    Args:
        path: Dot notation path to the configuration value (e.g., "DATABASE.default.host")
        default: Default value to return if the path doesn't exist
        
    Returns:
        The configuration value or the default if not found
        
    Example:
        db_host = get_config("DATABASE.default.host", "localhost")
    """
    parts = path.split('.')
    config_value = globals()
    
    try:
        for part in parts:
            if isinstance(config_value, dict):
                config_value = config_value.get(part)
            else:
                config_value = getattr(config_value, part, None)
                
            if config_value is None:
                return default
        return config_value
    except (KeyError, AttributeError):
        return default

# Initialize logging based on configuration
def setup_logging():
    """Configure logging based on the LOGGING configuration."""
    import logging.config
    logging.config.dictConfig(LOGGING)
    
    # Create a logger for this module
    logger = logging.getLogger(__name__)
    logger.debug("Logging initialized with configuration from default.py")
    
    return logger

# Initialize logger for this module
logger = setup_logging()
logger.info(f"Loaded default configuration for {APP_NAME} v{APP_VERSION}")

# Validate critical configuration settings
def validate_config():
    """Validate critical configuration settings and log warnings for potential issues."""
    warnings = []
    
    # Check for default secrets that should be changed
    if SECRET_KEY == "CHANGE_ME_IN_PRODUCTION" and ENV == "production":
        warnings.append("Default SECRET_KEY is being used in production environment")
        
    if DATABASE["default"]["password"] == "CHANGE_ME_IN_PRODUCTION" and ENV == "production":
        warnings.append("Default database password is being used in production environment")
    
    # Check for security settings in production
    if ENV == "production":
        if API["cors_origins"] == ["*"]:
            warnings.append("CORS is configured to allow all origins in production")
            
        if not SECURITY["ssl"]["enabled"]:
            warnings.append("SSL is disabled in production environment")
            
        if DEBUG:
            warnings.append("DEBUG mode is enabled in production environment")
    
    # Log any warnings
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    
    return len(warnings) == 0

# Run validation if this file is loaded directly
if __name__ == "__main__":
    validate_config()
    logger.info("Configuration validation complete")