"""
NeuroCognitive Architecture (NCA) Test Suite.

This module initializes the test suite for the NeuroCognitive Architecture project.
It provides common utilities, fixtures, and configuration for testing the various
components of the NCA system, including memory tiers, health dynamics, and LLM integration.

Usage:
    This file is automatically imported when running tests with pytest.
    It sets up the test environment and provides shared resources for all test modules.

Example:
    ```python
    # In a test file
    from neuroca.tests import BaseTestCase, MockMemoryStore
    
    class TestMemoryComponent(BaseTestCase):
        def setUp(self):
            self.memory_store = MockMemoryStore()
            # Additional setup
    ```

Note:
    - Test configuration is loaded from environment variables and/or config files
    - Logging is configured specifically for the test environment
    - Common test fixtures and utilities are exposed for use in test modules
"""

import logging
import os
import sys
from pathlib import Path

# Configure test logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("NEUROCA_TEST_DEBUG") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("neuroca.tests")

# Ensure the project root is in the Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    logger.debug(f"Added project root to Python path: {PROJECT_ROOT}")

# Test environment setup
TEST_ENV = os.environ.get("NEUROCA_TEST_ENV", "development")
logger.info(f"Initializing test suite in {TEST_ENV} environment")

# Version information for the test suite
__version__ = "0.1.0"

# Export common test utilities and base classes
# These will be implemented in separate files and imported here
# as the project develops

def get_test_config():
    """
    Get the configuration for the test environment.
    
    Returns:
        dict: Configuration parameters for the test environment.
        
    Note:
        This function loads configuration from environment variables
        and/or configuration files specific to the test environment.
    """
    config = {
        "environment": TEST_ENV,
        "debug": os.environ.get("NEUROCA_TEST_DEBUG", "false").lower() == "true",
        "test_data_dir": os.environ.get(
            "NEUROCA_TEST_DATA_DIR", 
            str(PROJECT_ROOT / "tests" / "data")
        ),
    }
    
    logger.debug(f"Loaded test configuration: {config}")
    return config

# Initialize test configuration
test_config = get_test_config()

# This will be populated with test fixtures and utilities as they are developed
__all__ = [
    "get_test_config",
    "test_config",
    "PROJECT_ROOT",
    "TEST_ENV",
]

logger.debug("Test suite initialization complete")
