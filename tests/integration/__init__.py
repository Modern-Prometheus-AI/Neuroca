"""
Integration Test Package for NeuroCognitive Architecture (NCA).

This package contains integration tests that verify the correct interaction between
different components of the NCA system and external systems such as LLMs, databases,
and other services. Integration tests ensure that the system works correctly as a whole
and that components interact as expected.

Usage:
    Integration tests can be run using pytest:
    ```
    pytest neuroca/tests/integration
    ```

    Or with specific markers:
    ```
    pytest neuroca/tests/integration -m "llm_integration"
    ```

Available test markers:
    - llm_integration: Tests that verify integration with LLM providers
    - memory_integration: Tests that verify integration between memory tiers
    - api_integration: Tests that verify the API endpoints
    - db_integration: Tests that verify database interactions
    - full_system: End-to-end tests of the complete system

Note:
    Integration tests may require external resources and configurations.
    See the README.md in this directory for setup instructions.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pytest

# Configure logging for integration tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path("logs/integration_tests.log"), mode="a"),
    ],
)

logger = logging.getLogger("neuroca.tests.integration")

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Test environment configuration
TEST_ENV: dict[str, str] = {
    "ENVIRONMENT": os.environ.get("TEST_ENVIRONMENT", "test"),
    "LOG_LEVEL": os.environ.get("TEST_LOG_LEVEL", "INFO"),
}

# Integration test constants
DEFAULT_TIMEOUT = 30  # Default timeout for integration tests in seconds
MAX_RETRIES = 3  # Default number of retries for flaky tests


class IntegrationTestError(Exception):
    """Base exception for integration test errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize an integration test error.

        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(f"{message}: {details}" if details else message)
        logger.error(f"Integration test error: {self}")


def setup_test_environment() -> dict[str, str]:
    """
    Set up the integration test environment.

    This function ensures that all necessary environment variables and
    configurations are in place for running integration tests.

    Returns:
        Dict containing environment configuration

    Raises:
        IntegrationTestError: If required environment variables are missing
    """
    logger.info("Setting up integration test environment")
    
    # Check for required environment variables
    required_vars = []
    missing_vars = [var for var in required_vars if var not in os.environ]
    
    if missing_vars:
        raise IntegrationTestError(
            "Missing required environment variables for integration tests",
            {"missing_variables": missing_vars}
        )
    
    # Load test configuration from file if available
    config_path = Path(project_root) / "config" / "test_config.json"
    if config_path.exists():
        import json
        try:
            with open(config_path) as f:
                test_config = json.load(f)
                logger.debug(f"Loaded test configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load test configuration: {e}")
            test_config = {}
    else:
        test_config = {}
    
    # Merge environment variables with test configuration
    env_config = {**test_config, **TEST_ENV}
    
    logger.info(f"Integration test environment set up with config: {env_config}")
    return env_config


def cleanup_test_resources() -> None:
    """
    Clean up resources created during integration tests.

    This function should be called after integration tests to ensure
    that no test resources are left behind.
    """
    logger.info("Cleaning up integration test resources")
    # Implementation will depend on specific resources used in tests
    # This is a placeholder for the actual cleanup logic


# Initialize the test environment when the package is imported
try:
    test_env = setup_test_environment()
except IntegrationTestError as e:
    logger.error(f"Failed to set up integration test environment: {e}")
    # Don't raise here to allow importing the module without running tests
    test_env = {}

__all__ = [
    "IntegrationTestError",
    "setup_test_environment",
    "cleanup_test_resources",
    "DEFAULT_TIMEOUT",
    "MAX_RETRIES",
    "test_env",
]

if __name__ == "__main__":
    sys.exit(pytest.main())