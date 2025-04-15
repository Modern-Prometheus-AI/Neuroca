"""
Memory Backend Configuration Loader

This module provides utilities for loading and managing memory backend configurations.
It can load configuration from YAML files and provide a unified access interface.
"""

import logging
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

from neuroca.core.exceptions import ConfigurationError

# Configure logger
logger = logging.getLogger(__name__)


class ConfigurationLoader:
    """
    Loader for memory backend configurations.
    
    This class is responsible for loading configuration from YAML files,
    merging configurations from multiple sources, and providing a unified
    access interface for configuration values.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files.
                        If None, defaults to 'config/backends' relative to project root.
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config: Dict[str, Any] = {}
        self.loaded_files: List[str] = []
        
        logger.debug(f"Initialized ConfigurationLoader with config_dir: {self.config_dir}")
    
    def _get_default_config_dir(self) -> str:
        """
        Get the default configuration directory.
        
        Returns:
            Path to the default configuration directory.
        """
        # Determine project root directory (assuming consistent structure)
        # Start with the current file's directory and go up until finding the project root
        current_dir = Path(__file__).resolve().parent
        
        # Go up to find the project root (where pyproject.toml or similar exists)
        root_dir = current_dir
        for _ in range(10):  # Limit iterations to prevent infinite loop
            if (root_dir / "pyproject.toml").exists() or (root_dir / "setup.py").exists():
                break
            root_dir = root_dir.parent
        
        # Default config dir is at the project root
        config_dir = root_dir.parent.parent / "config" / "backends"
        
        logger.debug(f"Detected default config directory: {config_dir}")
        return str(config_dir)
    
    def load_base_config(self) -> Dict[str, Any]:
        """
        Load the base configuration.
        
        Returns:
            Base configuration dictionary.
            
        Raises:
            ConfigurationError: If the base configuration file cannot be loaded.
        """
        return self.load_config_file("base_config.yaml")
    
    def load_backend_config(self, backend_type: str) -> Dict[str, Any]:
        """
        Load configuration for a specific backend type.
        
        Args:
            backend_type: Type of backend (e.g., 'in_memory', 'sqlite', 'redis')
            
        Returns:
            Backend-specific configuration dictionary.
            
        Raises:
            ConfigurationError: If the backend configuration file cannot be loaded.
        """
        config_file = f"{backend_type}_config.yaml"
        return self.load_config_file(config_file)
    
    def load_config_file(self, filename: str) -> Dict[str, Any]:
        """
        Load a configuration file.
        
        Args:
            filename: Name of the configuration file to load.
            
        Returns:
            Configuration dictionary.
            
        Raises:
            ConfigurationError: If the configuration file cannot be loaded.
        """
        file_path = os.path.join(self.config_dir, filename)
        
        try:
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file)
                
            if not isinstance(config, dict):
                raise ConfigurationError(f"Invalid configuration format in {file_path}")
                
            logger.debug(f"Loaded configuration from {file_path}")
            self.loaded_files.append(file_path)
            return config
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            raise ConfigurationError(f"Configuration file not found: {file_path}")
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML in {file_path}: {str(e)}")
            raise ConfigurationError(f"Error parsing YAML in {file_path}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {str(e)}")
            raise ConfigurationError(f"Error loading configuration: {str(e)}")
    
    def load_config(self, backend_type: str) -> Dict[str, Any]:
        """
        Load and merge configurations for a backend.
        
        This loads the base configuration and merges it with the backend-specific
        configuration.
        
        Args:
            backend_type: Type of backend (e.g., 'in_memory', 'sqlite', 'redis')
            
        Returns:
            Merged configuration dictionary.
            
        Raises:
            ConfigurationError: If configurations cannot be loaded or merged.
        """
        try:
            # Load base configuration
            base_config = self.load_base_config()
            
            # Load backend-specific configuration
            backend_config = self.load_backend_config(backend_type)
            
            # Merge configurations
            merged_config = self._merge_configs(base_config, backend_config)
            
            logger.info(f"Loaded and merged configuration for backend type: {backend_type}")
            self.config = merged_config
            return merged_config
            
        except Exception as e:
            logger.error(f"Error loading configuration for backend type {backend_type}: {str(e)}")
            raise ConfigurationError(f"Error loading configuration: {str(e)}")
    
    def _merge_configs(self, base_config: Dict[str, Any], backend_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge base and backend-specific configurations.
        
        Args:
            base_config: Base configuration dictionary.
            backend_config: Backend-specific configuration dictionary.
            
        Returns:
            Merged configuration dictionary.
        """
        # Create a deep copy of the base configuration
        merged = _deep_copy_dict(base_config)
        
        # Merge backend-specific configuration
        _deep_merge_dicts(merged, backend_config)
        
        return merged
    
    def get_config(self, backend_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the configuration for a backend type.
        
        If backend_type is provided, load and return the configuration for that backend.
        Otherwise, return the last loaded configuration.
        
        Args:
            backend_type: Type of backend (e.g., 'in_memory', 'sqlite', 'redis')
            
        Returns:
            Configuration dictionary.
            
        Raises:
            ConfigurationError: If no configuration has been loaded yet.
        """
        if backend_type:
            return self.load_config(backend_type)
            
        if not self.config:
            logger.warning("No configuration loaded, loading default backend configuration")
            base_config = self.load_base_config()
            default_backend = base_config.get("default_backend", "in_memory")
            return self.load_config(default_backend)
            
        return self.config
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using a dot-separated path.
        
        For example, 'common.cache.enabled' would retrieve config['common']['cache']['enabled'].
        
        Args:
            key_path: Dot-separated path to the configuration value.
            default: Default value to return if the key is not found.
            
        Returns:
            Configuration value, or default if not found.
        """
        if not self.config:
            logger.warning("No configuration loaded when trying to access: " + key_path)
            return default
            
        keys = key_path.split('.')
        config_section = self.config
        
        for key in keys:
            if not isinstance(config_section, dict) or key not in config_section:
                return default
            config_section = config_section[key]
            
        return config_section


def _deep_copy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a deep copy of a dictionary.
    
    Args:
        d: Dictionary to copy.
        
    Returns:
        Deep copy of the dictionary.
    """
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _deep_copy_dict(v)
        elif isinstance(v, list):
            result[k] = [x for x in v]
        else:
            result[k] = v
    return result


def _deep_merge_dicts(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Deeply merge source dictionary into target dictionary.
    
    Args:
        target: Target dictionary to merge into (modified in-place).
        source: Source dictionary to merge from.
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge_dicts(target[key], value)
        elif key in target and isinstance(target[key], list) and isinstance(value, list):
            target[key].extend(value)
        else:
            target[key] = value


# Create a singleton instance for global use
config_loader = ConfigurationLoader()


def get_backend_config(backend_type: str) -> Dict[str, Any]:
    """
    Get configuration for a specific backend type.
    
    This is a convenience function that uses the singleton config_loader.
    
    Args:
        backend_type: Type of backend (e.g., 'in_memory', 'sqlite', 'redis')
        
    Returns:
        Configuration dictionary for the specified backend.
    """
    return config_loader.load_config(backend_type)


def get_config_value(key_path: str, backend_type: Optional[str] = None, default: Any = None) -> Any:
    """
    Get a configuration value using a dot-separated path.
    
    This is a convenience function that uses the singleton config_loader.
    
    Args:
        key_path: Dot-separated path to the configuration value.
        backend_type: Type of backend (optional if config already loaded).
        default: Default value to return if the key is not found.
        
    Returns:
        Configuration value, or default if not found.
    """
    if backend_type:
        config_loader.load_config(backend_type)
    return config_loader.get_value(key_path, default)
