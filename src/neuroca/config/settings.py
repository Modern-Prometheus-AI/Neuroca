"""
NeuroCognitive Architecture (NCA) Configuration Settings Module.

This module provides a centralized configuration management system for the NCA project.
It handles loading settings from multiple sources with the following precedence:
1. Environment variables (highest priority)
2. .env files
3. User configuration files
4. Default configuration values (lowest priority)

The module supports different environments (development, testing, production)
and provides type validation, secret management, and dynamic configuration updates.

Usage:
    from neuroca.config.settings import settings
    
    # Access configuration values
    db_url = settings.DATABASE_URL
    
    # Access nested configuration
    memory_settings = settings.MEMORY_SYSTEM
    working_memory_capacity = memory_settings.WORKING_MEMORY.CAPACITY
    
    # Check if in development mode
    if settings.is_development():
        # Enable development-specific features
        
Example:
    # Loading specific environment configuration
    from neuroca.config.settings import Settings
    test_settings = Settings(env="test")
"""

import logging
import os
import pathlib
from enum import Enum
from functools import lru_cache
from typing import Any, Optional, Union

import dotenv
import yaml
from pydantic import AnyHttpUrl, BaseSettings, Field, PostgresDsn, SecretStr, validator

# Configure logging
logger = logging.getLogger(__name__)

# Define environment types
class EnvironmentType(str, Enum):
    """Environment types supported by the application."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

# Base paths
ROOT_DIR = pathlib.Path(__file__).parent.parent.parent.resolve()
CONFIG_DIR = ROOT_DIR / "config"

# Default configuration files
DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"
ENV_CONFIG_PATHS = {
    EnvironmentType.DEVELOPMENT: CONFIG_DIR / "development.yaml",
    EnvironmentType.TESTING: CONFIG_DIR / "testing.yaml",
    EnvironmentType.STAGING: CONFIG_DIR / "staging.yaml",
    EnvironmentType.PRODUCTION: CONFIG_DIR / "production.yaml",
}

# Local override file (not in version control)
LOCAL_OVERRIDE_PATH = CONFIG_DIR / "local.yaml"

class MemorySettings(BaseSettings):
    """Configuration settings for the memory system."""
    
    class WorkingMemorySettings(BaseSettings):
        """Working memory tier configuration."""
        CAPACITY: int = 7  # Default capacity based on Miller's Law
        DECAY_RATE: float = 0.1  # Rate at which items decay from working memory
        REFRESH_INTERVAL: int = 60  # Seconds between refresh operations
        PRIORITY_LEVELS: int = 5  # Number of priority levels
        
        class Config:
            env_prefix = "NCA_WORKING_MEMORY_"
    
    class ShortTermMemorySettings(BaseSettings):
        """Short-term memory tier configuration."""
        CAPACITY: int = 100  # Default capacity
        RETENTION_PERIOD: int = 3600  # Default retention in seconds (1 hour)
        CONSOLIDATION_THRESHOLD: float = 0.7  # Threshold for consolidation to long-term
        RETRIEVAL_BOOST: float = 0.5  # Boost factor for recently retrieved items
        
        class Config:
            env_prefix = "NCA_SHORT_TERM_MEMORY_"
    
    class LongTermMemorySettings(BaseSettings):
        """Long-term memory tier configuration."""
        INDEXING_STRATEGY: str = "hybrid"  # Options: semantic, keyword, hybrid
        EMBEDDING_DIMENSIONS: int = 1536  # Default embedding dimensions
        SIMILARITY_THRESHOLD: float = 0.75  # Threshold for similarity matching
        PRUNING_ENABLED: bool = True  # Whether to enable memory pruning
        PRUNING_INTERVAL: int = 86400  # Seconds between pruning operations (1 day)
        
        class Config:
            env_prefix = "NCA_LONG_TERM_MEMORY_"
    
    # Memory tier configurations
    WORKING_MEMORY: WorkingMemorySettings = Field(default_factory=WorkingMemorySettings)
    SHORT_TERM_MEMORY: ShortTermMemorySettings = Field(default_factory=ShortTermMemorySettings)
    LONG_TERM_MEMORY: LongTermMemorySettings = Field(default_factory=LongTermMemorySettings)
    
    # General memory system settings
    ENABLE_COMPRESSION: bool = True  # Whether to enable memory compression
    CONSOLIDATION_INTERVAL: int = 300  # Seconds between consolidation operations (5 min)
    BACKUP_INTERVAL: int = 3600  # Seconds between memory backups (1 hour)
    
    class Config:
        env_prefix = "NCA_MEMORY_"


class DatabaseSettings(BaseSettings):
    """Database connection and configuration settings."""
    URL: Optional[PostgresDsn] = None
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    TIMEOUT: int = 30
    ECHO: bool = False  # SQL query logging
    MIGRATION_DIR: str = "db/migrations"
    
    # Connection retry settings
    RETRY_ATTEMPTS: int = 5
    RETRY_DELAY: int = 2  # seconds
    
    @validator("URL", pre=True)
    def validate_db_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL and provide helpful error messages."""
        if not v:
            logger.warning("Database URL not configured. Using in-memory database.")
            return None
        return v
    
    class Config:
        env_prefix = "NCA_DB_"


class LLMIntegrationSettings(BaseSettings):
    """LLM integration and API settings."""
    PROVIDER: str = "openai"  # Default LLM provider
    MODEL: str = "gpt-4"  # Default model
    API_KEY: Optional[SecretStr] = None
    API_BASE_URL: Optional[AnyHttpUrl] = None
    TIMEOUT: int = 60  # Request timeout in seconds
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    TOP_P: float = 1.0
    FREQUENCY_PENALTY: float = 0.0
    PRESENCE_PENALTY: float = 0.0
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 60  # Requests per minute
    
    # Caching
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 3600  # Cache time-to-live in seconds
    
    @validator("API_KEY")
    def validate_api_key(cls, v: Optional[SecretStr], values: dict[str, Any]) -> Optional[SecretStr]:
        """Validate that API key is provided for external LLM providers."""
        provider = values.get("PROVIDER", "").lower()
        if provider in ["openai", "anthropic", "cohere"] and not v:
            logger.warning(f"API key not provided for {provider}. LLM integration will not function.")
        return v
    
    class Config:
        env_prefix = "NCA_LLM_"


class APISettings(BaseSettings):
    """API server configuration."""
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False
    WORKERS: int = 4
    TIMEOUT: int = 60
    
    # Security settings
    SECRET_KEY: SecretStr = Field(default_factory=lambda: SecretStr(os.urandom(32).hex()))
    ALLOWED_ORIGINS: list[str] = ["*"]
    ALLOWED_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: list[str] = ["*"]
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # Requests per minute
    
    # Authentication
    AUTH_ENABLED: bool = True
    AUTH_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: Any) -> Any:
        """Ensure secret key is set and warn if using default in production."""
        if isinstance(v, str) and len(v) < 32:
            logger.warning("Secret key is too short. Using a generated key instead.")
            return SecretStr(os.urandom(32).hex())
        return v
    
    class Config:
        env_prefix = "NCA_API_"


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    LEVEL: str = "INFO"
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    FILE_ENABLED: bool = True
    FILE_PATH: str = "logs/neuroca.log"
    FILE_MAX_BYTES: int = 10485760  # 10MB
    FILE_BACKUP_COUNT: int = 5
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: Optional[str] = None
    
    @validator("LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a recognized level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            logger.warning(f"Invalid log level: {v}. Defaulting to INFO.")
            return "INFO"
        return v.upper()
    
    class Config:
        env_prefix = "NCA_LOGGING_"


class Settings(BaseSettings):
    """
    Main settings class that combines all configuration components.
    
    This class handles loading configuration from multiple sources with the following precedence:
    1. Environment variables (highest priority)
    2. .env files
    3. User configuration files
    4. Default configuration values (lowest priority)
    """
    # Application metadata
    APP_NAME: str = "NeuroCognitive Architecture"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "Biologically-inspired cognitive architecture for LLMs"
    
    # Environment configuration
    ENV: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = False
    TESTING: bool = False
    
    # Component configurations
    MEMORY_SYSTEM: MemorySettings = Field(default_factory=MemorySettings)
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    LLM_INTEGRATION: LLMIntegrationSettings = Field(default_factory=LLMIntegrationSettings)
    API: APISettings = Field(default_factory=APISettings)
    LOGGING: LoggingSettings = Field(default_factory=LoggingSettings)
    
    # Paths
    DATA_DIR: str = str(ROOT_DIR / "data")
    TEMP_DIR: str = str(ROOT_DIR / "tmp")
    
    # Feature flags
    ENABLE_HEALTH_DYNAMICS: bool = True
    ENABLE_EMOTION_MODELING: bool = True
    ENABLE_ATTENTION_MECHANISM: bool = True
    
    class Config:
        env_prefix = "NCA_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, env: Optional[str] = None, **kwargs):
        """
        Initialize settings with optional environment override.
        
        Args:
            env: Optional environment name to load specific settings
            **kwargs: Additional settings to override
        """
        # Load .env file if it exists
        dotenv.load_dotenv()
        
        # Determine environment
        if env:
            kwargs["ENV"] = env
        elif os.environ.get("NCA_ENV"):
            kwargs["ENV"] = os.environ.get("NCA_ENV")
        
        # Load configuration from files
        config_dict = self._load_config_files(kwargs.get("ENV", EnvironmentType.DEVELOPMENT))
        
        # Update kwargs with file config (env vars will still take precedence)
        kwargs.update(config_dict)
        
        # Initialize settings
        super().__init__(**kwargs)
        
        # Set derived settings
        self.DEBUG = self.ENV == EnvironmentType.DEVELOPMENT
        self.TESTING = self.ENV == EnvironmentType.TESTING
        
        # Configure logging
        self._configure_logging()
        
        # Log initialization
        logger.info(f"Initialized {self.APP_NAME} settings for environment: {self.ENV}")
    
    def _load_config_files(self, env: Union[str, EnvironmentType]) -> dict[str, Any]:
        """
        Load configuration from YAML files based on environment.
        
        Args:
            env: Environment name or type
        
        Returns:
            Dict of configuration values
        """
        config: dict[str, Any] = {}
        
        # Convert string env to enum if needed
        if isinstance(env, str):
            try:
                env = EnvironmentType(env)
            except ValueError:
                logger.warning(f"Unknown environment: {env}. Using development.")
                env = EnvironmentType.DEVELOPMENT
        
        # Load default config
        if DEFAULT_CONFIG_PATH.exists():
            try:
                with open(DEFAULT_CONFIG_PATH) as f:
                    config.update(yaml.safe_load(f) or {})
                logger.debug(f"Loaded default configuration from {DEFAULT_CONFIG_PATH}")
            except Exception as e:
                logger.error(f"Error loading default config: {e}")
        
        # Load environment-specific config
        env_config_path = ENV_CONFIG_PATHS.get(env)
        if env_config_path and env_config_path.exists():
            try:
                with open(env_config_path) as f:
                    config.update(yaml.safe_load(f) or {})
                logger.debug(f"Loaded {env} configuration from {env_config_path}")
            except Exception as e:
                logger.error(f"Error loading {env} config: {e}")
        
        # Load local override if it exists
        if LOCAL_OVERRIDE_PATH.exists():
            try:
                with open(LOCAL_OVERRIDE_PATH) as f:
                    config.update(yaml.safe_load(f) or {})
                logger.debug(f"Loaded local override configuration from {LOCAL_OVERRIDE_PATH}")
            except Exception as e:
                logger.error(f"Error loading local override config: {e}")
        
        return config
    
    def _configure_logging(self) -> None:
        """Configure logging based on settings."""
        log_level = getattr(logging, self.LOGGING.LEVEL)
        log_format = self.LOGGING.FORMAT
        date_format = self.LOGGING.DATE_FORMAT
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format,
        )
        
        # Add file handler if enabled
        if self.LOGGING.FILE_ENABLED:
            try:
                # Ensure log directory exists
                log_path = pathlib.Path(self.LOGGING.FILE_PATH)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Add rotating file handler
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.LOGGING.FILE_PATH,
                    maxBytes=self.LOGGING.FILE_MAX_BYTES,
                    backupCount=self.LOGGING.FILE_BACKUP_COUNT,
                )
                file_handler.setFormatter(logging.Formatter(log_format, date_format))
                logging.getLogger().addHandler(file_handler)
                logger.debug(f"File logging configured to {self.LOGGING.FILE_PATH}")
            except Exception as e:
                logger.error(f"Failed to configure file logging: {e}")
        
        # Configure Sentry if enabled
        if self.LOGGING.SENTRY_ENABLED and self.LOGGING.SENTRY_DSN:
            try:
                import sentry_sdk
                sentry_sdk.init(
                    dsn=self.LOGGING.SENTRY_DSN,
                    environment=self.ENV,
                    release=self.APP_VERSION,
                )
                logger.debug("Sentry logging configured")
            except ImportError:
                logger.warning("Sentry SDK not installed. Sentry logging disabled.")
            except Exception as e:
                logger.error(f"Failed to configure Sentry: {e}")
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENV == EnvironmentType.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENV == EnvironmentType.TESTING
    
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENV == EnvironmentType.STAGING
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENV == EnvironmentType.PRODUCTION
    
    def as_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary (with secrets redacted)."""
        def _process_value(v: Any) -> Any:
            if isinstance(v, SecretStr):
                return "**REDACTED**"
            elif hasattr(v, "as_dict") and callable(v.as_dict):
                return v.as_dict()
            elif hasattr(v, "dict") and callable(v.dict):
                return v.dict()
            return v
        
        return {k: _process_value(v) for k, v in self.dict().items()}
    
    def create_directories(self) -> None:
        """Create necessary directories for the application."""
        dirs = [
            self.DATA_DIR,
            self.TEMP_DIR,
            os.path.dirname(self.LOGGING.FILE_PATH),
        ]
        
        for dir_path in dirs:
            try:
                pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")


# Create a singleton instance of Settings
@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()


# Export settings as a singleton
settings = get_settings()

# Export environment type enum for use in other modules
__all__ = ["settings", "Settings", "EnvironmentType"]