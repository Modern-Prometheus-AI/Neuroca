"""
Integration tests for memory backend configuration.

These tests verify that the configuration system properly integrates with the backend
factory and the created backends use the provided configuration values.
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any

from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory
from neuroca.memory.backends.base import BaseStorageBackend
from neuroca.memory.backends.in_memory_backend import InMemoryBackend
from neuroca.memory.config.loader import ConfigurationLoader, get_backend_config


@pytest.fixture
def test_config_files():
    """Create temporary test configuration files for various backends."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create base config
        base_config = {
            "common": {
                "cache": {
                    "enabled": True,
                    "max_size": 500,
                    "ttl_seconds": 180
                },
                "batch": {
                    "max_batch_size": 50,
                    "auto_commit": True
                },
                "performance": {
                    "connection_pool_size": 3,
                    "connection_timeout_seconds": 5
                }
            },
            "default_backend": "in_memory"
        }
        
        # Create in-memory config
        in_memory_config = {
            "in_memory": {
                "memory": {
                    "initial_capacity": 1000,
                    "auto_expand": True,
                    "expansion_factor": 2
                },
                "data_structure": {
                    "index_type": "hashmap",
                    "enable_secondary_indices": True
                },
                "pruning": {
                    "enabled": True,
                    "max_items": 500,
                    "strategy": "lru"
                }
            }
        }
        
        # Create sqlite config
        sqlite_config = {
            "sqlite": {
                "connection": {
                    "database_path": ":memory:",
                    "create_if_missing": True,
                    "timeout_seconds": 5
                },
                "performance": {
                    "journal_mode": "WAL",
                    "synchronous": "NORMAL"
                },
                "schema": {
                    "auto_migrate": True,
                    "enable_fts": True
                }
            }
        }
        
        # Write the config files
        base_path = Path(temp_dir) / "base_config.yaml"
        in_memory_path = Path(temp_dir) / "in_memory_config.yaml"
        sqlite_path = Path(temp_dir) / "sqlite_config.yaml"
        
        with open(base_path, 'w') as f:
            yaml.dump(base_config, f)
            
        with open(in_memory_path, 'w') as f:
            yaml.dump(in_memory_config, f)
            
        with open(sqlite_path, 'w') as f:
            yaml.dump(sqlite_config, f)
            
        yield temp_dir


class MockStorageBackendFactory(StorageBackendFactory):
    """Mock of the StorageBackendFactory for testing configuration integration."""
    
    @classmethod
    def reset(cls):
        """Reset the factory's instance cache."""
        cls._instances = {}


@pytest.fixture
def mock_factory():
    """Provide a clean factory instance for each test."""
    MockStorageBackendFactory.reset()
    yield MockStorageBackendFactory
    MockStorageBackendFactory.reset()


class TestBackendConfiguration:
    """Tests for backend configuration integration."""
    
    def test_in_memory_backend_configuration(self, test_config_files, mock_factory, monkeypatch):
        """Test that in-memory backend is properly configured from YAML files."""
        # Set the config loader to use our test files
        loader = ConfigurationLoader(test_config_files)
        
        # Patch the get_backend_config function to use our test loader
        def mock_get_config(backend_type: str) -> Dict[str, Any]:
            return loader.load_config(backend_type)
        
        monkeypatch.setattr(
            "neuroca.memory.config.loader.get_backend_config", 
            mock_get_config
        )
        
        # Now create a backend using the factory
        backend = mock_factory.create_backend(BackendType.MEMORY)
        
        # Verify it's the correct type
        assert isinstance(backend, InMemoryBackend)
        
        # Verify configuration was applied
        assert backend.config["cache"]["enabled"] is True
        assert backend.config["cache"]["max_size"] == 500
        assert backend.config["batch"]["max_batch_size"] == 50
        assert backend.config["in_memory"]["memory"]["initial_capacity"] == 1000
        assert backend.config["in_memory"]["pruning"]["strategy"] == "lru"
    
    def test_sqlite_backend_configuration(self, test_config_files, mock_factory, monkeypatch):
        """Test that SQLite backend is properly configured from YAML files."""
        # Set the config loader to use our test files
        loader = ConfigurationLoader(test_config_files)
        
        # Patch the get_backend_config function to use our test loader
        def mock_get_config(backend_type: str) -> Dict[str, Any]:
            return loader.load_config(backend_type)
        
        monkeypatch.setattr(
            "neuroca.memory.config.loader.get_backend_config", 
            mock_get_config
        )
        
        # Create a backend using the factory
        backend = mock_factory.create_backend(BackendType.SQLITE)
        
        # Verify configuration was applied
        assert backend.config["cache"]["enabled"] is True
        assert backend.config["batch"]["max_batch_size"] == 50
        assert backend.config["sqlite"]["connection"]["database_path"] == ":memory:"
        assert backend.config["sqlite"]["performance"]["journal_mode"] == "WAL"
        assert backend.config["sqlite"]["schema"]["enable_fts"] is True
    
    def test_backend_singleton(self, test_config_files, mock_factory, monkeypatch):
        """Test that backends are singletons per backend type."""
        # Set the config loader to use our test files
        loader = ConfigurationLoader(test_config_files)
        
        # Patch the get_backend_config function to use our test loader
        monkeypatch.setattr(
            "neuroca.memory.config.loader.get_backend_config", 
            lambda backend_type: loader.load_config(backend_type)
        )
        
        # Create backends
        backend1 = mock_factory.create_backend(BackendType.MEMORY)
        backend2 = mock_factory.create_backend(BackendType.MEMORY)
        backend3 = mock_factory.create_backend(BackendType.SQLITE)
        
        # Check that same backend type returns same instance
        assert backend1 is backend2
        
        # Check that different backend types return different instances
        assert backend1 is not backend3
    
    def test_backend_initialization_with_config(self, test_config_files, monkeypatch):
        """Test that backends can be manually initialized with config."""
        # Set the config loader to use our test files
        loader = ConfigurationLoader(test_config_files)
        in_memory_config = loader.load_config("in_memory")
        
        # Create a backend directly
        backend = InMemoryBackend(config=in_memory_config)
        
        # Verify configuration was applied
        assert backend.config["cache"]["enabled"] is True
        assert backend.config["cache"]["max_size"] == 500
        assert backend.config["in_memory"]["memory"]["initial_capacity"] == 1000
        assert backend.config["in_memory"]["pruning"]["strategy"] == "lru"
