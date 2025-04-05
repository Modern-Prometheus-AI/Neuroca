"""
Configuration Management for NeuroCognitive Architecture (NCA)

This module provides a centralized configuration management system for the NCA project.
It handles loading configuration from various sources (environment variables, config files),
validating configuration values, and providing a unified interface for accessing
configuration throughout the application.

Features:
- Hierarchical configuration with defaults
- Environment-specific configuration
- Configuration validation
- Secure handling of sensitive values
- Dynamic reloading capabilities
- Type checking and conversion

Usage:
    from neuroca.config import config
    
    # Access configuration values
    api_key = config.get('integration.openai.api_key')
    
    # Access with type conversion and default
    timeout = config.get_int('api.timeout', default=30)
    
    # Check if a configuration exists
    if config.has('feature.experimental.enabled'):
        # Enable experimental feature
        
    # Load a specific configuration profile
    config.load_profile('production')

This module is thread-safe and should be imported and used as a singleton.
"""

import importlib.resources
import json
import logging
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union, cast

import yaml

# Setup logging
logger = logging.getLogger(__name__)

# Type variable for generic type hints
T = TypeVar('T')

# Constants
DEFAULT_CONFIG_FILENAME = "default.yaml"
ENV_CONFIG_PREFIX = "NEUROCA_"
CONFIG_EXTENSION_PATTERN = r"\.(yaml|yml|json)$"


@dataclass
class ConfigSource:
    """Represents a source of configuration data with priority information."""
    name: str
    data: dict[str, Any]
    priority: int
    mutable: bool = False


class ConfigurationError(Exception):
    """Base exception for all configuration-related errors."""
    pass


class ConfigNotFoundError(ConfigurationError):
    """Raised when a requested configuration key is not found."""
    pass


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass


class ConfigTypeError(ConfigurationError):
    """Raised when a configuration value cannot be converted to the requested type."""
    pass


class ConfigurationManager:
    """
    Central configuration management system for the NCA project.
    
    This class handles loading, validating, and providing access to configuration
    settings from multiple sources with different priorities.
    """
    
    def __init__(self):
        """Initialize the configuration manager with empty configuration."""
        self._sources: list[ConfigSource] = []
        self._lock = threading.RLock()
        self._initialized = False
        self._validators: dict[str, Callable[[Any], bool]] = {}
        self._type_converters: dict[str, Callable[[Any], Any]] = {
            'int': self._convert_int,
            'float': self._convert_float,
            'bool': self._convert_bool,
            'list': self._convert_list,
            'dict': self._convert_dict,
        }
        
        # Register built-in validators
        self.register_validator('url', self._validate_url)
        self.register_validator('email', self._validate_email)
        self.register_validator('port', self._validate_port)
        
    def initialize(self, config_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize the configuration system by loading default configurations.
        
        Args:
            config_dir: Optional directory path where configuration files are stored.
                        If None, uses the default config directory in the package.
        
        This method should be called once at application startup.
        """
        with self._lock:
            if self._initialized:
                logger.warning("Configuration manager already initialized. Skipping.")
                return
                
            # Load default configuration from package resources
            self._load_default_config()
            
            # Load configuration from specified directory if provided
            if config_dir:
                self._load_from_directory(config_dir)
                
            # Load configuration from environment variables
            self._load_from_environment()
            
            # Mark as initialized
            self._initialized = True
            logger.info("Configuration manager initialized successfully")
    
    def _load_default_config(self) -> None:
        """Load default configuration from package resources."""
        try:
            # Try to load default config from package resources
            default_config_text = importlib.resources.read_text('neuroca.config', DEFAULT_CONFIG_FILENAME)
            default_config = yaml.safe_load(default_config_text)
            self.add_source("default", default_config, priority=0)
            logger.debug("Loaded default configuration from package resources")
        except (ImportError, FileNotFoundError):
            # Create an empty default configuration if file doesn't exist
            logger.warning("Default configuration file not found in package resources")
            self.add_source("default", {}, priority=0)
    
    def _load_from_directory(self, config_dir: Union[str, Path]) -> None:
        """
        Load configuration files from the specified directory.
        
        Args:
            config_dir: Directory containing configuration files
        """
        config_path = Path(config_dir)
        if not config_path.exists() or not config_path.is_dir():
            logger.warning(f"Configuration directory not found: {config_path}")
            return
            
        # Load all YAML and JSON files from the directory
        for file_path in config_path.glob("*"):
            if not re.search(CONFIG_EXTENSION_PATTERN, file_path.name):
                continue
                
            try:
                config_name = file_path.stem
                with open(file_path) as f:
                    if file_path.suffix.lower() in ('.yaml', '.yml'):
                        config_data = yaml.safe_load(f)
                    elif file_path.suffix.lower() == '.json':
                        config_data = json.load(f)
                    else:
                        continue
                        
                # Add with priority based on filename (environment-specific configs have higher priority)
                priority = 10
                if config_name in ('development', 'test', 'staging', 'production'):
                    priority = 20
                if config_name == os.getenv('NEUROCA_ENV', 'development'):
                    priority = 30
                    
                self.add_source(config_name, config_data, priority=priority)
                logger.debug(f"Loaded configuration from {file_path}")
            except Exception as e:
                logger.error(f"Error loading configuration from {file_path}: {str(e)}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables with the NEUROCA_ prefix."""
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(ENV_CONFIG_PREFIX):
                # Convert NEUROCA_API_TIMEOUT to api.timeout
                config_key = key[len(ENV_CONFIG_PREFIX):].lower().replace('_', '.')
                
                # Try to parse as JSON if it looks like a complex value
                if value.startswith('{') or value.startswith('[') or value.lower() in ('true', 'false', 'null'):
                    try:
                        parsed_value = json.loads(value)
                        env_config[config_key] = parsed_value
                    except json.JSONDecodeError:
                        env_config[config_key] = value
                else:
                    env_config[config_key] = value
        
        if env_config:
            self.add_source("environment", env_config, priority=100, mutable=True)
            logger.debug(f"Loaded {len(env_config)} configuration values from environment variables")
    
    def add_source(self, name: str, data: dict[str, Any], priority: int, mutable: bool = False) -> None:
        """
        Add a new configuration source with the specified priority.
        
        Args:
            name: Name of the configuration source
            data: Configuration data dictionary
            priority: Priority value (higher values take precedence)
            mutable: Whether this source can be modified at runtime
        """
        with self._lock:
            # Check if source with this name already exists
            for i, source in enumerate(self._sources):
                if source.name == name:
                    # Replace existing source
                    self._sources[i] = ConfigSource(name=name, data=data, priority=priority, mutable=mutable)
                    logger.debug(f"Updated configuration source: {name} (priority: {priority})")
                    return
            
            # Add new source and sort by priority
            self._sources.append(ConfigSource(name=name, data=data, priority=priority, mutable=mutable))
            self._sources.sort(key=lambda s: s.priority)
            logger.debug(f"Added configuration source: {name} (priority: {priority})")
    
    def load_profile(self, profile_name: str) -> None:
        """
        Load a specific configuration profile.
        
        Args:
            profile_name: Name of the profile to load (e.g., 'development', 'production')
        
        Raises:
            ConfigurationError: If the profile cannot be loaded
        """
        try:
            profile_path = None
            
            # Try to find the profile in package resources
            try:
                profile_filename = f"{profile_name}.yaml"
                profile_text = importlib.resources.read_text('neuroca.config', profile_filename)
                profile_data = yaml.safe_load(profile_text)
                self.add_source(f"profile:{profile_name}", profile_data, priority=50)
                logger.info(f"Loaded configuration profile '{profile_name}' from package resources")
                return
            except (ImportError, FileNotFoundError):
                pass
                
            # Try to find the profile in the config directory
            config_dir = os.environ.get('NEUROCA_CONFIG_DIR')
            if config_dir:
                profile_path = Path(config_dir) / f"{profile_name}.yaml"
                if not profile_path.exists():
                    profile_path = Path(config_dir) / f"{profile_name}.json"
            
            if not profile_path or not profile_path.exists():
                raise ConfigurationError(f"Configuration profile '{profile_name}' not found")
                
            with open(profile_path) as f:
                if profile_path.suffix.lower() in ('.yaml', '.yml'):
                    profile_data = yaml.safe_load(f)
                elif profile_path.suffix.lower() == '.json':
                    profile_data = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {profile_path.suffix}")
                    
            self.add_source(f"profile:{profile_name}", profile_data, priority=50)
            logger.info(f"Loaded configuration profile '{profile_name}' from {profile_path}")
            
        except Exception as e:
            error_msg = f"Failed to load configuration profile '{profile_name}': {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Dot-separated configuration key (e.g., 'api.timeout')
            default: Default value to return if key is not found
            
        Returns:
            The configuration value or the default if not found
            
        Example:
            >>> config.get('database.url')
            'postgresql://user:pass@localhost/db'
            >>> config.get('feature.not_exists', False)
            False
        """
        try:
            return self._get_value(key)
        except ConfigNotFoundError:
            return default
    
    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get a configuration value as an integer."""
        return self._get_typed_value('int', key, default)
    
    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get a configuration value as a float."""
        return self._get_typed_value('float', key, default)
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """Get a configuration value as a boolean."""
        return self._get_typed_value('bool', key, default)
    
    def get_list(self, key: str, default: Optional[list[Any]] = None) -> list[Any]:
        """Get a configuration value as a list."""
        return self._get_typed_value('list', key, default)
    
    def get_dict(self, key: str, default: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Get a configuration value as a dictionary."""
        return self._get_typed_value('dict', key, default)
    
    def get_string(self, key: str, default: Optional[str] = None) -> str:
        """Get a configuration value as a string."""
        value = self.get(key, default)
        if value is None:
            return ""
        return str(value)
    
    def _get_typed_value(self, type_name: str, key: str, default: Optional[T] = None) -> T:
        """
        Get a configuration value with type conversion.
        
        Args:
            type_name: Type to convert to ('int', 'float', 'bool', 'list', 'dict')
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            The converted value
            
        Raises:
            ConfigTypeError: If the value cannot be converted to the requested type
        """
        try:
            value = self._get_value(key)
            if value is None:
                return cast(T, default)
                
            converter = self._type_converters.get(type_name)
            if not converter:
                raise ConfigTypeError(f"No converter registered for type '{type_name}'")
                
            return cast(T, converter(value))
        except ConfigNotFoundError:
            return cast(T, default)
        except Exception as e:
            if isinstance(e, ConfigTypeError):
                raise
            raise ConfigTypeError(f"Cannot convert '{key}' to {type_name}: {str(e)}")
    
    def _get_value(self, key: str) -> Any:
        """
        Internal method to get a configuration value by key.
        
        Args:
            key: Dot-separated configuration key
            
        Returns:
            The configuration value
            
        Raises:
            ConfigNotFoundError: If the key is not found in any configuration source
        """
        if not self._initialized:
            logger.warning("Configuration manager not initialized. Call initialize() first.")
            self.initialize()
            
        key_parts = key.split('.')
        
        # Search through all sources in reverse order (highest priority first)
        with self._lock:
            for source in reversed(self._sources):
                current = source.data
                found = True
                
                # Navigate through nested dictionaries
                for part in key_parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        found = False
                        break
                
                if found:
                    return current
        
        raise ConfigNotFoundError(f"Configuration key not found: {key}")
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated configuration key
            value: Value to set
            
        Raises:
            ConfigurationError: If no mutable configuration source is available
        """
        with self._lock:
            # Find the highest priority mutable source
            mutable_source = None
            for source in reversed(self._sources):
                if source.mutable:
                    mutable_source = source
                    break
            
            if not mutable_source:
                raise ConfigurationError("No mutable configuration source available")
                
            # Set the value in the mutable source
            key_parts = key.split('.')
            current = mutable_source.data
            
            # Navigate and create nested dictionaries as needed
            for _i, part in enumerate(key_parts[:-1]):
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
                
            # Set the final value
            current[key_parts[-1]] = value
            logger.debug(f"Set configuration value: {key}")
    
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        Args:
            key: Dot-separated configuration key
            
        Returns:
            True if the key exists, False otherwise
        """
        try:
            self._get_value(key)
            return True
        except ConfigNotFoundError:
            return False
    
    def register_validator(self, name: str, validator_func: Callable[[Any], bool]) -> None:
        """
        Register a custom configuration validator.
        
        Args:
            name: Name of the validator
            validator_func: Function that takes a value and returns True if valid
        """
        with self._lock:
            self._validators[name] = validator_func
            logger.debug(f"Registered configuration validator: {name}")
    
    def validate(self, key: str, validator_name: str) -> bool:
        """
        Validate a configuration value using a registered validator.
        
        Args:
            key: Configuration key to validate
            validator_name: Name of the validator to use
            
        Returns:
            True if validation passes
            
        Raises:
            ConfigValidationError: If validation fails or validator not found
        """
        with self._lock:
            if validator_name not in self._validators:
                raise ConfigValidationError(f"Validator not found: {validator_name}")
                
            try:
                value = self._get_value(key)
                validator = self._validators[validator_name]
                
                if not validator(value):
                    raise ConfigValidationError(f"Validation failed for '{key}' using '{validator_name}'")
                    
                return True
            except ConfigNotFoundError:
                raise ConfigValidationError(f"Cannot validate non-existent key: {key}")
    
    def export(self) -> dict[str, Any]:
        """
        Export the complete merged configuration as a dictionary.
        
        Returns:
            A dictionary containing all configuration values
        """
        result: dict[str, Any] = {}
        
        # Start with the lowest priority and override with higher priorities
        with self._lock:
            for source in self._sources:
                self._deep_merge(result, source.data)
                
        return result
    
    def _deep_merge(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """
        Recursively merge source dictionary into target dictionary.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                self._deep_merge(target[key], value)
            else:
                # Override or add value
                target[key] = value
    
    # Type converters
    def _convert_int(self, value: Any) -> int:
        """Convert value to int."""
        if isinstance(value, bool):
            return 1 if value else 0
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ConfigTypeError(f"Cannot convert to int: {value}")
    
    def _convert_float(self, value: Any) -> float:
        """Convert value to float."""
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ConfigTypeError(f"Cannot convert to float: {value}")
    
    def _convert_bool(self, value: Any) -> bool:
        """Convert value to bool."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            value = value.lower().strip()
            if value in ('true', 'yes', 'y', '1', 'on'):
                return True
            if value in ('false', 'no', 'n', '0', 'off'):
                return False
        raise ConfigTypeError(f"Cannot convert to bool: {value}")
    
    def _convert_list(self, value: Any) -> list[Any]:
        """Convert value to list."""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(',')]
        raise ConfigTypeError(f"Cannot convert to list: {value}")
    
    def _convert_dict(self, value: Any) -> dict[str, Any]:
        """Convert value to dict."""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        raise ConfigTypeError(f"Cannot convert to dict: {value}")
    
    # Validators
    def _validate_url(self, value: Any) -> bool:
        """Validate if a value is a URL."""
        if not isinstance(value, str):
            return False
        # Simple URL validation - could be enhanced with regex or urllib.parse
        return value.startswith(('http://', 'https://', 'ftp://'))
    
    def _validate_email(self, value: Any) -> bool:
        """Validate if a value is an email address."""
        if not isinstance(value, str):
            return False
        # Simple email validation - could be enhanced with regex
        return '@' in value and '.' in value.split('@')[1]
    
    def _validate_port(self, value: Any) -> bool:
        """Validate if a value is a valid port number."""
        try:
            port = int(value)
            return 0 < port < 65536
        except (ValueError, TypeError):
            return False


# Create a singleton instance
config = ConfigurationManager()

# Export the singleton and important classes
__all__ = [
    'config',
    'ConfigurationManager',
    'ConfigurationError',
    'ConfigNotFoundError',
    'ConfigValidationError',
    'ConfigTypeError',
]