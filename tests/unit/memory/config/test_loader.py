"""
Unit tests for the configuration loader module.

These tests verify that the configuration loader correctly loads, merges, and
provides access to configuration values from YAML files.
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest import mock

from neuroca.core.exceptions import ConfigurationError
from neuroca.memory.config.loader import (
    ConfigurationLoader,
    get_backend_config,
    get_config_value,
    config_loader,
    _deep_copy_dict,
    _deep_merge_dicts
)


# Using the fixture from conftest.py instead of defining it here


class TestConfigurationLoader:
    """Tests for the ConfigurationLoader class."""
    
    def test_init_with_custom_dir(self, test_config_dir):
        """Test initialization with a custom configuration directory."""
        loader = ConfigurationLoader(test_config_dir)
        assert loader.config_dir == test_config_dir
        assert not loader.config
        assert not loader.loaded_files
    
    def test_load_base_config(self, test_config_dir):
        """Test loading the base configuration file."""
        loader = ConfigurationLoader(test_config_dir)
        config = loader.load_base_config()
        
        assert config["common"]["cache"]["enabled"] is True
        assert config["common"]["cache"]["max_size"] == 1000
        assert config["common"]["batch"]["max_batch_size"] == 100
        assert config["default_backend"] == "in_memory"
        assert len(loader.loaded_files) == 1
        
    def test_load_backend_config(self, test_config_dir):
        """Test loading a backend-specific configuration file."""
        loader = ConfigurationLoader(test_config_dir)
        config = loader.load_backend_config("in_memory")
        
        assert config["in_memory"]["memory"]["initial_capacity"] == 500
        assert config["common"]["cache"]["ttl_seconds"] == 500
        assert len(loader.loaded_files) == 1
    
    def test_load_config(self, test_config_dir):
        """Test loading and merging configurations."""
        loader = ConfigurationLoader(test_config_dir)
        config = loader.load_config("in_memory")
        
        # Check base config values
        assert config["common"]["cache"]["enabled"] is True
        assert config["common"]["cache"]["max_size"] == 1000
        assert config["common"]["batch"]["max_batch_size"] == 100
        assert config["default_backend"] == "in_memory"
        
        # Check backend-specific values
        assert config["in_memory"]["memory"]["initial_capacity"] == 500
        
        # Check merged values
        assert config["common"]["cache"]["ttl_seconds"] == 500
        
        # Check that config was stored in instance
        assert loader.config == config
        assert len(loader.loaded_files) == 2
    
    def test_get_config(self, test_config_dir):
        """Test retrieving configurations."""
        loader = ConfigurationLoader(test_config_dir)
        
        # First call should load the config
        config1 = loader.get_config("in_memory")
        assert "common" in config1
        assert "in_memory" in config1
        
        # Second call without backend_type should return cached config
        config2 = loader.get_config()
        assert config2 == config1
        
        # Call with different backend_type should load new config
        config3 = loader.get_config("sqlite")
        assert config3 != config1
    
    def test_get_value(self, test_config_dir):
        """Test retrieving configuration values using dot notation."""
        loader = ConfigurationLoader(test_config_dir)
        loader.load_config("in_memory")
        
        # Test getting existing values
        assert loader.get_value("common.cache.enabled") is True
        assert loader.get_value("common.cache.max_size") == 1000
        assert loader.get_value("in_memory.memory.initial_capacity") == 500
        
        # Test getting non-existent values with default
        assert loader.get_value("common.nonexistent", "default") == "default"
        assert loader.get_value("nonexistent.path", 42) == 42
        
        # Test getting non-existent values without default
        assert loader.get_value("common.nonexistent") is None
    
    def test_file_not_found(self, test_config_dir):
        """Test error handling for missing config files."""
        loader = ConfigurationLoader(test_config_dir)
        
        with pytest.raises(ConfigurationError) as excinfo:
            loader.load_config_file("nonexistent_config.yaml")
        
        assert "not found" in str(excinfo.value)
    
    def test_invalid_yaml(self, test_config_dir):
        """Test error handling for invalid YAML content."""
        invalid_yaml_path = Path(test_config_dir) / "invalid_config.yaml"
        
        with open(invalid_yaml_path, 'w') as f:
            f.write("invalid: yaml: content:")
        
        loader = ConfigurationLoader(test_config_dir)
        
        with pytest.raises(ConfigurationError) as excinfo:
            loader.load_config_file("invalid_config.yaml")
        
        assert "Error parsing YAML" in str(excinfo.value)
    
    def test_default_config_dir(self):
        """Test that the default config directory is correctly determined."""
        with mock.patch.object(ConfigurationLoader, '_get_default_config_dir') as mock_get_dir:
            mock_get_dir.return_value = "/default/config/dir"
            loader = ConfigurationLoader()
            assert loader.config_dir == "/default/config/dir"
            mock_get_dir.assert_called_once()


class TestUtilityFunctions:
    """Tests for utility functions in the loader module."""
    
    def test_deep_copy_dict(self):
        """Test deep copying of dictionaries."""
        original = {
            "key1": "value1",
            "key2": ["item1", "item2"],
            "key3": {
                "nested1": "nested_value",
                "nested2": ["nested_item"]
            }
        }
        
        copied = _deep_copy_dict(original)
        
        # Check that it's a different object but with same content
        assert copied == original
        assert copied is not original
        assert copied["key3"] is not original["key3"]
        assert copied["key2"] is not original["key2"]
    
    def test_deep_merge_dicts(self):
        """Test deep merging of dictionaries."""
        dict1 = {
            "key1": "value1",
            "key2": ["item1"],
            "key3": {
                "nested1": "base_value",
                "nested2": ["base_item"]
            }
        }
        
        dict2 = {
            "key2": ["item2"],
            "key3": {
                "nested1": "override_value",
                "nested3": "new_value"
            },
            "key4": "new_key"
        }
        
        # Create a copy for testing
        target = _deep_copy_dict(dict1)
        
        # Merge dict2 into target
        _deep_merge_dicts(target, dict2)
        
        # Check that values were merged correctly
        assert target["key1"] == "value1"  # Unchanged
        assert target["key2"] == ["item1", "item2"]  # Lists merged
        assert target["key3"]["nested1"] == "override_value"  # Value overridden
        assert target["key3"]["nested2"] == ["base_item"]  # Unchanged
        assert target["key3"]["nested3"] == "new_value"  # New nested value
        assert target["key4"] == "new_key"  # New top-level key
    
    def test_get_backend_config(self, test_config_dir):
        """Test the get_backend_config utility function."""
        # Mock the global config_loader
        original_loader = config_loader
        
        try:
            from neuroca.memory.config.loader import config_loader as global_loader
            global_loader.config_dir = test_config_dir
            
            config = get_backend_config("in_memory")
            
            assert "common" in config
            assert "in_memory" in config
            assert config["common"]["cache"]["enabled"] is True
            assert config["in_memory"]["memory"]["initial_capacity"] == 500
            
        finally:
            # Restore the original global loader
            from neuroca.memory.config import loader
            loader.config_loader = original_loader
    
    def test_get_config_value(self, test_config_dir):
        """Test the get_config_value utility function."""
        # Mock the global config_loader
        original_loader = config_loader
        
        try:
            from neuroca.memory.config.loader import config_loader as global_loader
            global_loader.config_dir = test_config_dir
            
            # Test with backend_type
            value1 = get_config_value("common.cache.enabled", "in_memory")
            assert value1 is True
            
            # Test without backend_type (using already loaded config)
            value2 = get_config_value("in_memory.memory.initial_capacity")
            assert value2 == 500
            
            # Test with default value
            value3 = get_config_value("nonexistent.path", default="default_value")
            assert value3 == "default_value"
            
        finally:
            # Restore the original global loader
            from neuroca.memory.config import loader
            loader.config_loader = original_loader
