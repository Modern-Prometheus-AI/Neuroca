"""
Development Configuration for NeuroCognitive Architecture (NCA)

This module defines configuration settings specific to the development environment.
It includes database connections, API settings, logging configurations, feature flags,
and other environment-specific parameters needed during development.

Usage:
    Import this module directly or through the config package's dynamic loading:
    
    ```python
    from neuroca.config import development as dev_config
    # or
    from neuroca.config import get_config
    config = get_config('development')
    ```

Note:
    - This file should NOT contain sensitive information like passwords or API keys.
    - Use environment variables for sensitive data (loaded via python-dotenv).
    - Local overrides can be placed in a .env file (not committed to version control).
"""

import logging
import os
from pathlib import Path
from typing import Any

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Debug flag - always True in development
DEBUG = True

# Application settings
APP_NAME = "NeuroCognitive Architecture"
APP_VERSION = "0.1.0-dev"
APP_DESCRIPTION = "Biologically-inspired cognitive architecture for LLMs"

# Server settings
HOST = "127.0.0.1"
PORT = 8000
RELOAD = True  # Auto-reload on code changes
WORKERS = 1    # Single worker for development

# API settings
API_PREFIX = "/api/v1"
API_TITLE = f"{APP_NAME} API"
API_DESCRIPTION = "API for interacting with the NeuroCognitive Architecture"
API_VERSION = "v1"
OPENAPI_URL = f"{API_PREFIX}/openapi.json"
DOCS_URL = f"{API_PREFIX}/docs"
REDOC_URL = f"{API_PREFIX}/redoc"

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",    # Frontend development server
    "http://localhost:8000",    # Backend API when accessed directly
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Database settings
DATABASE = {
    "default": {
        "ENGINE": "sqlite",
        "NAME": str(DATA_DIR / "neuroca_dev.db"),
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "OPTIONS": {
            "timeout": 20,
            "check_same_thread": False,  # Allow multiple threads for SQLite in dev
        },
    }
}

# Redis settings (for caching, task queue, etc.)
REDIS = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "socket_timeout": 5,
}

# Celery settings (for async tasks)
CELERY = {
    "broker_url": "redis://localhost:6379/0",
    "result_backend": "redis://localhost:6379/0",
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "worker_concurrency": 2,  # Lower concurrency for development
    "task_always_eager": False,  # Set to True to run tasks synchronously for debugging
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "neuroca_dev.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
    "loggers": {
        "neuroca": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Third-party library logging
        "sqlalchemy": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Memory system settings
MEMORY_SYSTEM = {
    "working_memory": {
        "capacity": 10,  # Number of items
        "decay_rate": 0.05,  # Rate at which items decay
    },
    "short_term_memory": {
        "capacity": 100,
        "retention_period": 3600,  # 1 hour in seconds
    },
    "long_term_memory": {
        "vector_db": {
            "engine": "faiss",  # Options: faiss, milvus, qdrant
            "dimension": 1536,  # Vector dimension
            "index_type": "Flat",  # Simple index for development
            "path": str(DATA_DIR / "vector_indices"),
        },
        "document_db": {
            "engine": "sqlite",
            "path": str(DATA_DIR / "documents.db"),
        },
    },
}

# LLM Integration settings
LLM = {
    "provider": "openai",  # Default provider
    "model": "gpt-3.5-turbo",  # Default model
    "temperature": 0.7,
    "max_tokens": 1000,
    "timeout": 30,  # seconds
    "retry_attempts": 3,
    "cache_responses": True,
    "cache_ttl": 3600,  # 1 hour in seconds
}

# Feature flags for development
FEATURE_FLAGS = {
    "use_working_memory": True,
    "use_short_term_memory": True,
    "use_long_term_memory": True,
    "enable_health_dynamics": True,
    "enable_emotion_simulation": True,
    "enable_attention_mechanisms": True,
    "enable_performance_monitoring": True,
    "enable_advanced_logging": True,
}

# Development tools and debugging
DEV_TOOLS = {
    "enable_profiling": True,
    "profile_endpoints": True,
    "memory_profiling": True,
    "query_debugging": True,
    "slow_query_threshold": 0.5,  # seconds
    "mock_external_services": False,  # Set to True to use mock services instead of real ones
}

# Security settings (even for development, maintain basic security)
SECURITY = {
    "secret_key": "dev_secret_key_change_in_production",  # ONLY FOR DEVELOPMENT
    "algorithm": "HS256",
    "access_token_expire_minutes": 60 * 24,  # 1 day
    "refresh_token_expire_minutes": 60 * 24 * 7,  # 7 days
    "password_min_length": 8,
    "password_require_special": True,
    "password_require_number": True,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
}

# Email settings (for development, typically uses a local debugging server)
EMAIL = {
    "backend": "console",  # Options: smtp, console, file
    "host": "localhost",
    "port": 1025,  # Default port for mailhog
    "username": "",
    "password": "",
    "use_tls": False,
    "use_ssl": False,
    "default_from_email": "noreply@neuroca.local",
    "subject_prefix": "[NeuroCognitive Architecture] ",
}

# Health dynamics simulation parameters
HEALTH_DYNAMICS = {
    "energy": {
        "initial": 100.0,
        "decay_rate": 0.05,
        "min_value": 0.0,
        "max_value": 100.0,
        "critical_threshold": 20.0,
    },
    "stress": {
        "initial": 0.0,
        "growth_rate": 0.1,
        "recovery_rate": 0.05,
        "min_value": 0.0,
        "max_value": 100.0,
        "critical_threshold": 80.0,
    },
    "update_interval": 5.0,  # seconds
}

# Function to get a specific configuration value with dot notation
def get_config_value(path: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value using dot notation path.
    
    Args:
        path: Dot-separated path to the configuration value (e.g., 'DATABASE.default.ENGINE')
        default: Default value to return if the path doesn't exist
        
    Returns:
        The configuration value or the default if not found
        
    Example:
        engine = get_config_value('DATABASE.default.ENGINE', 'sqlite')
    """
    try:
        value = globals()
        for key in path.split('.'):
            value = value.get(key) if isinstance(value, dict) else getattr(value, key, None)
            
            if value is None:
                return default
        return value
    except (KeyError, AttributeError):
        return default

# Load any local overrides from .env file
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / '.env.development'
    load_dotenv(env_path)
    
    # Override settings with environment variables if they exist
    # This allows for local customization without changing the file
    if os.environ.get('NEUROCA_DEBUG'):
        DEBUG = os.environ.get('NEUROCA_DEBUG').lower() in ('true', '1', 't')
    
    if os.environ.get('NEUROCA_HOST'):
        HOST = os.environ.get('NEUROCA_HOST')
    
    if os.environ.get('NEUROCA_PORT'):
        PORT = int(os.environ.get('NEUROCA_PORT'))
    
    # Database overrides
    if os.environ.get('NEUROCA_DB_ENGINE'):
        DATABASE['default']['ENGINE'] = os.environ.get('NEUROCA_DB_ENGINE')
    
    if os.environ.get('NEUROCA_DB_NAME'):
        DATABASE['default']['NAME'] = os.environ.get('NEUROCA_DB_NAME')
    
    # Add more environment variable overrides as needed
    
except ImportError:
    logging.warning("python-dotenv not installed. Environment variables will not be loaded from .env file.")
except Exception as e:
    logging.warning(f"Error loading .env file: {e}")

# Initialize logging based on the configuration
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("neuroca.config.development")
logger.debug("Development configuration loaded")