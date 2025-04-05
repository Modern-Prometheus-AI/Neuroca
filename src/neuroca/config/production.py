"""
Production Configuration for NeuroCognitive Architecture (NCA)

This module defines all configuration settings for the production environment.
It includes database connections, security settings, logging configuration,
memory tier settings, and LLM integration parameters optimized for production use.

Usage:
    Import this module when running the application in production:
    ```
    from neuroca.config import production as config
    ```

Security Note:
    This file should NOT contain actual secrets. Instead, it should reference
    environment variables or a secure secrets management system.
"""

import logging
import os
from pathlib import Path

# Base paths and directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.environ.get('NEUROCA_DATA_DIR', os.path.join(BASE_DIR, 'data'))
LOG_DIR = os.environ.get('NEUROCA_LOG_DIR', os.path.join(BASE_DIR, 'logs'))

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Application settings
DEBUG = False
TESTING = False
SECRET_KEY = os.environ.get('NEUROCA_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("Production environment requires NEUROCA_SECRET_KEY to be set")

# Host and port configuration
HOST = os.environ.get('NEUROCA_HOST', '0.0.0.0')
PORT = int(os.environ.get('NEUROCA_PORT', '8000'))

# Security settings
ALLOWED_HOSTS = os.environ.get('NEUROCA_ALLOWED_HOSTS', '*').split(',')
CORS_ORIGINS = os.environ.get('NEUROCA_CORS_ORIGINS', '').split(',')
SSL_ENABLED = os.environ.get('NEUROCA_SSL_ENABLED', 'true').lower() == 'true'
SSL_CERT_PATH = os.environ.get('NEUROCA_SSL_CERT_PATH', '')
SSL_KEY_PATH = os.environ.get('NEUROCA_SSL_KEY_PATH', '')

# Rate limiting
RATE_LIMIT_ENABLED = True
RATE_LIMIT_DEFAULT = "100/minute"
RATE_LIMIT_STRATEGY = "fixed-window"

# Database configuration
DATABASE = {
    'engine': os.environ.get('NEUROCA_DB_ENGINE', 'postgresql'),
    'host': os.environ.get('NEUROCA_DB_HOST', 'localhost'),
    'port': int(os.environ.get('NEUROCA_DB_PORT', '5432')),
    'name': os.environ.get('NEUROCA_DB_NAME', 'neuroca'),
    'user': os.environ.get('NEUROCA_DB_USER', 'neuroca'),
    'password': os.environ.get('NEUROCA_DB_PASSWORD', ''),
    'pool_size': int(os.environ.get('NEUROCA_DB_POOL_SIZE', '10')),
    'max_overflow': int(os.environ.get('NEUROCA_DB_MAX_OVERFLOW', '20')),
    'pool_timeout': int(os.environ.get('NEUROCA_DB_POOL_TIMEOUT', '30')),
    'pool_recycle': int(os.environ.get('NEUROCA_DB_POOL_RECYCLE', '1800')),
    'ssl_enabled': os.environ.get('NEUROCA_DB_SSL_ENABLED', 'true').lower() == 'true',
}

# Redis configuration (for caching, task queue, etc.)
REDIS = {
    'host': os.environ.get('NEUROCA_REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('NEUROCA_REDIS_PORT', '6379')),
    'db': int(os.environ.get('NEUROCA_REDIS_DB', '0')),
    'password': os.environ.get('NEUROCA_REDIS_PASSWORD', ''),
    'ssl': os.environ.get('NEUROCA_REDIS_SSL', 'true').lower() == 'true',
}

# Caching configuration
CACHE = {
    'type': os.environ.get('NEUROCA_CACHE_TYPE', 'redis'),
    'ttl': int(os.environ.get('NEUROCA_CACHE_TTL', '3600')),  # Default 1 hour
    'max_size': int(os.environ.get('NEUROCA_CACHE_MAX_SIZE', '1000')),
}

# Memory tier configuration
MEMORY_CONFIG = {
    # Working memory settings
    'working_memory': {
        'capacity': int(os.environ.get('NEUROCA_WM_CAPACITY', '7')),  # Miller's Law default
        'decay_rate': float(os.environ.get('NEUROCA_WM_DECAY_RATE', '0.1')),
        'refresh_threshold': float(os.environ.get('NEUROCA_WM_REFRESH_THRESHOLD', '0.3')),
        'priority_levels': int(os.environ.get('NEUROCA_WM_PRIORITY_LEVELS', '5')),
    },
    
    # Short-term memory settings
    'short_term_memory': {
        'capacity': int(os.environ.get('NEUROCA_STM_CAPACITY', '100')),
        'retention_period': int(os.environ.get('NEUROCA_STM_RETENTION', '86400')),  # 24 hours in seconds
        'consolidation_threshold': float(os.environ.get('NEUROCA_STM_CONSOLIDATION', '0.7')),
        'storage_type': os.environ.get('NEUROCA_STM_STORAGE', 'redis'),
    },
    
    # Long-term memory settings
    'long_term_memory': {
        'vector_db': os.environ.get('NEUROCA_LTM_VECTOR_DB', 'pinecone'),
        'vector_db_url': os.environ.get('NEUROCA_LTM_VECTOR_DB_URL', ''),
        'vector_db_api_key': os.environ.get('NEUROCA_LTM_VECTOR_DB_API_KEY', ''),
        'vector_db_namespace': os.environ.get('NEUROCA_LTM_VECTOR_DB_NAMESPACE', 'neuroca-production'),
        'embedding_model': os.environ.get('NEUROCA_LTM_EMBEDDING_MODEL', 'text-embedding-ada-002'),
        'embedding_dimension': int(os.environ.get('NEUROCA_LTM_EMBEDDING_DIM', '1536')),
        'similarity_threshold': float(os.environ.get('NEUROCA_LTM_SIMILARITY', '0.75')),
        'max_results': int(os.environ.get('NEUROCA_LTM_MAX_RESULTS', '50')),
    }
}

# LLM integration settings
LLM_CONFIG = {
    'provider': os.environ.get('NEUROCA_LLM_PROVIDER', 'openai'),
    'api_key': os.environ.get('NEUROCA_LLM_API_KEY', ''),
    'api_base': os.environ.get('NEUROCA_LLM_API_BASE', 'https://api.openai.com/v1'),
    'default_model': os.environ.get('NEUROCA_LLM_DEFAULT_MODEL', 'gpt-4'),
    'fallback_model': os.environ.get('NEUROCA_LLM_FALLBACK_MODEL', 'gpt-3.5-turbo'),
    'timeout': int(os.environ.get('NEUROCA_LLM_TIMEOUT', '60')),
    'max_tokens': int(os.environ.get('NEUROCA_LLM_MAX_TOKENS', '4096')),
    'temperature': float(os.environ.get('NEUROCA_LLM_TEMPERATURE', '0.7')),
    'retry_attempts': int(os.environ.get('NEUROCA_LLM_RETRY', '3')),
    'retry_delay': int(os.environ.get('NEUROCA_LLM_RETRY_DELAY', '2')),
    'streaming': os.environ.get('NEUROCA_LLM_STREAMING', 'true').lower() == 'true',
}

# Health dynamics configuration
HEALTH_DYNAMICS = {
    'enabled': os.environ.get('NEUROCA_HEALTH_ENABLED', 'true').lower() == 'true',
    'initial_energy': float(os.environ.get('NEUROCA_HEALTH_INITIAL_ENERGY', '100.0')),
    'energy_decay_rate': float(os.environ.get('NEUROCA_HEALTH_ENERGY_DECAY', '0.05')),
    'rest_recovery_rate': float(os.environ.get('NEUROCA_HEALTH_REST_RECOVERY', '0.2')),
    'critical_threshold': float(os.environ.get('NEUROCA_HEALTH_CRITICAL', '20.0')),
    'task_energy_costs': {
        'default': float(os.environ.get('NEUROCA_HEALTH_COST_DEFAULT', '1.0')),
        'complex_reasoning': float(os.environ.get('NEUROCA_HEALTH_COST_REASONING', '3.0')),
        'memory_retrieval': float(os.environ.get('NEUROCA_HEALTH_COST_MEMORY', '1.5')),
        'learning': float(os.environ.get('NEUROCA_HEALTH_COST_LEARNING', '2.5')),
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z'
        },
    },
    'handlers': {
        'console': {
            'level': os.environ.get('NEUROCA_LOG_LEVEL', 'INFO'),
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'json',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'neuroca.log'),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10,
        },
        'error_file': {
            'level': 'ERROR',
            'formatter': 'json',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10,
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': os.environ.get('NEUROCA_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'neuroca': {
            'handlers': ['console', 'file', 'error_file'],
            'level': os.environ.get('NEUROCA_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'neuroca.security': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Monitoring and observability
MONITORING = {
    'enabled': os.environ.get('NEUROCA_MONITORING_ENABLED', 'true').lower() == 'true',
    'prometheus_enabled': os.environ.get('NEUROCA_PROMETHEUS_ENABLED', 'true').lower() == 'true',
    'prometheus_port': int(os.environ.get('NEUROCA_PROMETHEUS_PORT', '9090')),
    'health_check_interval': int(os.environ.get('NEUROCA_HEALTH_CHECK_INTERVAL', '60')),
    'tracing_enabled': os.environ.get('NEUROCA_TRACING_ENABLED', 'true').lower() == 'true',
    'tracing_exporter': os.environ.get('NEUROCA_TRACING_EXPORTER', 'jaeger'),
    'tracing_endpoint': os.environ.get('NEUROCA_TRACING_ENDPOINT', 'http://jaeger:14268/api/traces'),
}

# API settings
API = {
    'version': os.environ.get('NEUROCA_API_VERSION', 'v1'),
    'prefix': os.environ.get('NEUROCA_API_PREFIX', '/api'),
    'docs_enabled': os.environ.get('NEUROCA_API_DOCS_ENABLED', 'false').lower() == 'true',
    'docs_url': os.environ.get('NEUROCA_API_DOCS_URL', '/docs'),
    'redoc_url': os.environ.get('NEUROCA_API_REDOC_URL', '/redoc'),
    'openapi_url': os.environ.get('NEUROCA_API_OPENAPI_URL', '/openapi.json'),
    'token_expiration': int(os.environ.get('NEUROCA_TOKEN_EXPIRATION', '86400')),  # 24 hours in seconds
}

# Worker and task queue settings
WORKER = {
    'concurrency': int(os.environ.get('NEUROCA_WORKER_CONCURRENCY', '4')),
    'prefetch_multiplier': int(os.environ.get('NEUROCA_WORKER_PREFETCH', '4')),
    'max_tasks_per_child': int(os.environ.get('NEUROCA_WORKER_MAX_TASKS', '1000')),
    'task_soft_time_limit': int(os.environ.get('NEUROCA_TASK_SOFT_LIMIT', '300')),  # 5 minutes
    'task_hard_time_limit': int(os.environ.get('NEUROCA_TASK_HARD_LIMIT', '600')),  # 10 minutes
}

# Initialize logging as early as possible
try:
    import logging.config
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(__name__)
    logger.info("Production configuration loaded successfully")
except Exception as e:
    # Fallback to basic logging if configuration fails
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"Error configuring logging: {e}")
    logger.info("Using basic logging configuration as fallback")

def get_database_url() -> str:
    """
    Constructs and returns a database URL from the configuration.
    
    Returns:
        str: A formatted database connection string
    
    Example:
        >>> get_database_url()
        'postgresql://user:password@localhost:5432/neuroca'
    """
    db = DATABASE
    password = db['password']
    
    # URL encode the password if it contains special characters
    if password and any(c in password for c in [':', '/', '@', '?', '&', '=']):
        from urllib.parse import quote_plus
        password = quote_plus(password)
    
    # Construct the database URL
    ssl_param = "?sslmode=require" if db['ssl_enabled'] else ""
    return f"{db['engine']}://{db['user']}:{password}@{db['host']}:{db['port']}/{db['name']}{ssl_param}"

def validate_config() -> list[str]:
    """
    Validates the production configuration and returns a list of warnings or issues.
    
    Returns:
        List[str]: A list of configuration warnings or issues
    
    Example:
        >>> issues = validate_config()
        >>> if issues:
        ...     for issue in issues:
        ...         logger.warning(f"Configuration issue: {issue}")
    """
    issues = []
    
    # Check for missing critical environment variables
    if not SECRET_KEY or len(SECRET_KEY) < 32:
        issues.append("SECRET_KEY is missing or too short (should be at least 32 characters)")
    
    # Check database configuration
    if not DATABASE['password']:
        issues.append("Database password is not set")
    
    # Check LLM configuration
    if not LLM_CONFIG['api_key']:
        issues.append("LLM API key is not set")
    
    # Check SSL configuration if enabled
    if SSL_ENABLED:
        if not SSL_CERT_PATH or not os.path.exists(SSL_CERT_PATH):
            issues.append(f"SSL certificate not found at {SSL_CERT_PATH}")
        if not SSL_KEY_PATH or not os.path.exists(SSL_KEY_PATH):
            issues.append(f"SSL key not found at {SSL_KEY_PATH}")
    
    # Check directory permissions
    try:
        test_file = os.path.join(LOG_DIR, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except (OSError, PermissionError):
        issues.append(f"Cannot write to log directory: {LOG_DIR}")
    
    try:
        test_file = os.path.join(DATA_DIR, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except (OSError, PermissionError):
        issues.append(f"Cannot write to data directory: {DATA_DIR}")
    
    return issues

# Run validation on module import
config_issues = validate_config()
for issue in config_issues:
    logger.warning(f"Configuration issue: {issue}")