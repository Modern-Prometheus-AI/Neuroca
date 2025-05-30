"""
Pytest fixtures for memory configuration tests.

This module provides fixtures specific to testing the memory configuration system.
"""

import os
import tempfile
import yaml
from pathlib import Path

import pytest


@pytest.fixture
def test_config_dir():
    """Create a temporary directory with test configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create base config file
        base_config = {
            "common": {
                "cache": {
                    "enabled": True,
                    "max_size": 1000,
                    "ttl_seconds": 300
                },
                "batch": {
                    "max_batch_size": 100,
                    "auto_commit": True
                }
            },
            "default_backend": "in_memory"
        }
        
        # Create in-memory backend-specific config file
        in_memory_config = {
            "in_memory": {
                "memory": {
                    "initial_capacity": 500
                }
            },
            "common": {
                "cache": {
                    "ttl_seconds": 500
                }
            }
        }
        
        # Create sqlite backend-specific config file
        sqlite_config = {
            "sqlite": {
                "connection": {
                    "database_path": ":memory:",
                    "timeout_seconds": 10
                }
            },
            "common": {
                "cache": {
                    "ttl_seconds": 600
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
