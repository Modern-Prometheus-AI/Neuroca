"""
Testing Configuration Module for NeuroCognitive Architecture (NCA)

This module provides comprehensive testing configuration, utilities, and fixtures
for the NeuroCognitive Architecture project. It includes:

1. Test environment configuration management
2. Mock data generators for various components
3. Test fixtures for common testing scenarios
4. Utilities for setting up and tearing down test environments
5. Configuration for different testing types (unit, integration, performance)

Usage:
    from neuroca.config.testing import (
        TestConfig, 
        setup_test_environment, 
        teardown_test_environment,
        generate_mock_memory_data
    )
    
    # Configure test environment
    test_config = TestConfig()
    test_config.set_mode('integration')
    
    # Setup test environment
    setup_test_environment(test_config)
    
    # Generate mock data for testing
    mock_data = generate_mock_memory_data(size='medium')
    
    # Run tests...
    
    # Clean up
    teardown_test_environment()
"""

import datetime
import json
import logging
import os
import random
import shutil
import tempfile
import time
import uuid
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

# Configure logging for testing
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neuroca.testing")

# Constants
DEFAULT_TEST_CONFIG_PATH = Path("tests/test_config.json")
TEST_DATA_DIR = Path("tests/test_data")
MAX_MOCK_MEMORY_SIZE = 10000  # Maximum number of items in mock memory


class TestMode(Enum):
    """Test execution modes supported by the framework."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    STRESS = "stress"
    SECURITY = "security"
    E2E = "end_to_end"


class TestEnvironment(Enum):
    """Test environments supported by the framework."""
    LOCAL = "local"
    CI = "ci"
    STAGING = "staging"
    PRODUCTION_LIKE = "production_like"


class MemoryTier(Enum):
    """Memory tiers in the NCA system for testing purposes."""
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class TestConfig:
    """
    Configuration class for NCA testing.
    
    This class manages test configuration settings, including test mode,
    environment, mock data settings, and test-specific parameters.
    
    Attributes:
        mode (TestMode): The testing mode (unit, integration, etc.)
        environment (TestEnvironment): The testing environment
        mock_data_size (str): Size of mock data to generate ('small', 'medium', 'large')
        temp_dir (Path): Temporary directory for test artifacts
        timeout (int): Default timeout for tests in seconds
        custom_settings (Dict): Custom test-specific settings
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize test configuration, optionally loading from a config file.
        
        Args:
            config_path: Path to a JSON configuration file (optional)
        """
        # Default configuration
        self.mode = TestMode.UNIT
        self.environment = TestEnvironment.LOCAL
        self.mock_data_size = "small"
        self.temp_dir = Path(tempfile.mkdtemp(prefix="neuroca_test_"))
        self.timeout = 30  # seconds
        self.custom_settings = {}
        self.debug = os.environ.get("NEUROCA_TEST_DEBUG", "0") == "1"
        
        # Load from file if provided
        if config_path:
            self._load_from_file(config_path)
        
        # Override with environment variables
        self._load_from_env()
        
        logger.debug(f"Initialized TestConfig with mode={self.mode.value}, "
                    f"environment={self.environment.value}, "
                    f"mock_data_size={self.mock_data_size}")
    
    def _load_from_file(self, config_path: Path) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Raises:
            FileNotFoundError: If the config file doesn't exist
            json.JSONDecodeError: If the config file contains invalid JSON
        """
        try:
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_path}")
                return
                
            with open(config_path) as f:
                config_data = json.load(f)
            
            # Apply configuration from file
            if 'mode' in config_data:
                self.set_mode(config_data['mode'])
            
            if 'environment' in config_data:
                self.set_environment(config_data['environment'])
            
            if 'mock_data_size' in config_data:
                self.mock_data_size = config_data['mock_data_size']
            
            if 'timeout' in config_data:
                self.timeout = config_data['timeout']
            
            if 'custom_settings' in config_data:
                self.custom_settings.update(config_data['custom_settings'])
                
            logger.debug(f"Loaded configuration from {config_path}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {config_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            raise
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Test mode from environment
        env_mode = os.environ.get("NEUROCA_TEST_MODE")
        if env_mode:
            self.set_mode(env_mode)
        
        # Test environment from environment variable
        env_environment = os.environ.get("NEUROCA_TEST_ENVIRONMENT")
        if env_environment:
            self.set_environment(env_environment)
        
        # Mock data size from environment
        env_mock_data_size = os.environ.get("NEUROCA_MOCK_DATA_SIZE")
        if env_mock_data_size:
            self.mock_data_size = env_mock_data_size
        
        # Timeout from environment
        env_timeout = os.environ.get("NEUROCA_TEST_TIMEOUT")
        if env_timeout:
            try:
                self.timeout = int(env_timeout)
            except ValueError:
                logger.warning(f"Invalid timeout value in environment: {env_timeout}")
    
    def set_mode(self, mode: Union[str, TestMode]) -> None:
        """
        Set the test mode.
        
        Args:
            mode: Test mode as string or TestMode enum
            
        Raises:
            ValueError: If the provided mode is invalid
        """
        if isinstance(mode, str):
            try:
                self.mode = TestMode(mode.lower())
            except ValueError:
                valid_modes = [m.value for m in TestMode]
                logger.error(f"Invalid test mode: {mode}. Valid modes: {valid_modes}")
                raise ValueError(f"Invalid test mode: {mode}. Valid modes: {valid_modes}")
        elif isinstance(mode, TestMode):
            self.mode = mode
        else:
            raise ValueError(f"Mode must be a string or TestMode enum, got {type(mode)}")
        
        logger.debug(f"Test mode set to {self.mode.value}")
    
    def set_environment(self, environment: Union[str, TestEnvironment]) -> None:
        """
        Set the test environment.
        
        Args:
            environment: Test environment as string or TestEnvironment enum
            
        Raises:
            ValueError: If the provided environment is invalid
        """
        if isinstance(environment, str):
            try:
                self.environment = TestEnvironment(environment.lower())
            except ValueError:
                valid_envs = [e.value for e in TestEnvironment]
                logger.error(f"Invalid test environment: {environment}. Valid environments: {valid_envs}")
                raise ValueError(f"Invalid test environment: {environment}. Valid environments: {valid_envs}")
        elif isinstance(environment, TestEnvironment):
            self.environment = environment
        else:
            raise ValueError(f"Environment must be a string or TestEnvironment enum, got {type(environment)}")
        
        logger.debug(f"Test environment set to {self.environment.value}")
    
    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a custom setting by key with an optional default value.
        
        Args:
            key: The setting key
            default: Default value if key doesn't exist
            
        Returns:
            The setting value or default
        """
        return self.custom_settings.get(key, default)
    
    def set_custom_setting(self, key: str, value: Any) -> None:
        """
        Set a custom setting.
        
        Args:
            key: The setting key
            value: The setting value
        """
        self.custom_settings[key] = value
        logger.debug(f"Custom setting '{key}' set to {value}")
    
    def save_to_file(self, path: Optional[Path] = None) -> Path:
        """
        Save the current configuration to a JSON file.
        
        Args:
            path: Path to save the configuration (optional)
            
        Returns:
            Path to the saved configuration file
            
        Raises:
            IOError: If the file cannot be written
        """
        if path is None:
            path = DEFAULT_TEST_CONFIG_PATH
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            'mode': self.mode.value,
            'environment': self.environment.value,
            'mock_data_size': self.mock_data_size,
            'timeout': self.timeout,
            'custom_settings': self.custom_settings
        }
        
        try:
            with open(path, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.debug(f"Configuration saved to {path}")
            return path
        except OSError as e:
            logger.error(f"Failed to save configuration to {path}: {e}")
            raise
    
    def cleanup(self) -> None:
        """Clean up temporary resources used by the test configuration."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory {self.temp_dir}: {e}")


def setup_test_environment(config: TestConfig) -> dict[str, Any]:
    """
    Set up the test environment based on the provided configuration.
    
    This function prepares the testing environment, including:
    - Creating necessary directories
    - Setting up mock databases if needed
    - Configuring environment variables
    - Initializing test fixtures
    
    Args:
        config: Test configuration
        
    Returns:
        Dictionary containing environment setup information
        
    Raises:
        RuntimeError: If environment setup fails
    """
    logger.info(f"Setting up test environment: {config.environment.value}")
    
    env_info = {
        "start_time": datetime.datetime.now(),
        "config": config,
        "resources": {}
    }
    
    try:
        # Create test data directory if it doesn't exist
        test_data_path = config.temp_dir / "test_data"
        test_data_path.mkdir(parents=True, exist_ok=True)
        env_info["resources"]["test_data_path"] = test_data_path
        
        # Set up environment variables for testing
        os.environ["NEUROCA_TESTING"] = "1"
        os.environ["NEUROCA_TEST_MODE"] = config.mode.value
        os.environ["NEUROCA_TEST_ENVIRONMENT"] = config.environment.value
        
        # Additional setup based on test mode
        if config.mode == TestMode.INTEGRATION:
            # Set up mock databases or services for integration testing
            db_path = setup_test_database(config)
            env_info["resources"]["db_path"] = db_path
        
        elif config.mode == TestMode.PERFORMANCE:
            # Set up performance testing resources
            perf_data_path = setup_performance_test_data(config)
            env_info["resources"]["perf_data_path"] = perf_data_path
        
        logger.info(f"Test environment setup complete: {config.environment.value}")
        return env_info
        
    except Exception as e:
        logger.error(f"Failed to set up test environment: {e}")
        # Clean up any partially created resources
        teardown_test_environment(config)
        raise RuntimeError(f"Test environment setup failed: {e}")


def teardown_test_environment(config: TestConfig) -> None:
    """
    Clean up the test environment.
    
    Args:
        config: Test configuration
        
    Raises:
        RuntimeError: If environment teardown fails
    """
    logger.info(f"Tearing down test environment: {config.environment.value}")
    
    try:
        # Clean up temporary directories
        config.cleanup()
        
        # Remove test environment variables
        for env_var in ["NEUROCA_TESTING", "NEUROCA_TEST_MODE", "NEUROCA_TEST_ENVIRONMENT"]:
            if env_var in os.environ:
                del os.environ[env_var]
        
        logger.info("Test environment teardown complete")
        
    except Exception as e:
        logger.error(f"Failed to tear down test environment: {e}")
        raise RuntimeError(f"Test environment teardown failed: {e}")


def setup_test_database(config: TestConfig) -> Path:
    """
    Set up a test database for integration testing.
    
    Args:
        config: Test configuration
        
    Returns:
        Path to the test database
        
    Raises:
        RuntimeError: If database setup fails
    """
    db_path = config.temp_dir / "test_db"
    db_path.mkdir(exist_ok=True)
    
    # Create a simple JSON file-based test database
    try:
        # Initialize empty collections
        collections = ["memory", "health", "system", "logs"]
        for collection in collections:
            collection_file = db_path / f"{collection}.json"
            with open(collection_file, 'w') as f:
                json.dump([], f)
        
        logger.debug(f"Test database initialized at {db_path}")
        return db_path
        
    except Exception as e:
        logger.error(f"Failed to set up test database: {e}")
        raise RuntimeError(f"Test database setup failed: {e}")


def setup_performance_test_data(config: TestConfig) -> Path:
    """
    Set up data for performance testing.
    
    Args:
        config: Test configuration
        
    Returns:
        Path to the performance test data
        
    Raises:
        RuntimeError: If performance data setup fails
    """
    perf_data_path = config.temp_dir / "perf_data"
    perf_data_path.mkdir(exist_ok=True)
    
    try:
        # Generate performance test data based on size
        sizes = {
            "small": 100,
            "medium": 1000,
            "large": 10000
        }
        
        sizes.get(config.mock_data_size, sizes["medium"])
        
        # Generate memory test data
        memory_data = generate_mock_memory_data(size=config.mock_data_size)
        with open(perf_data_path / "memory_data.json", 'w') as f:
            json.dump(memory_data, f)
        
        logger.debug(f"Performance test data created at {perf_data_path}")
        return perf_data_path
        
    except Exception as e:
        logger.error(f"Failed to set up performance test data: {e}")
        raise RuntimeError(f"Performance test data setup failed: {e}")


def generate_mock_memory_data(size: str = "medium", 
                             memory_tier: Optional[MemoryTier] = None) -> list[dict[str, Any]]:
    """
    Generate mock memory data for testing.
    
    Args:
        size: Size of the dataset ('small', 'medium', 'large')
        memory_tier: Specific memory tier to generate data for
        
    Returns:
        List of mock memory items
        
    Raises:
        ValueError: If an invalid size is provided
    """
    # Define sizes
    sizes = {
        "small": 50,
        "medium": 500,
        "large": 5000
    }
    
    if size not in sizes:
        valid_sizes = list(sizes.keys())
        logger.error(f"Invalid mock data size: {size}. Valid sizes: {valid_sizes}")
        raise ValueError(f"Invalid mock data size: {size}. Valid sizes: {valid_sizes}")
    
    count = sizes[size]
    if count > MAX_MOCK_MEMORY_SIZE:
        logger.warning(f"Requested mock data size exceeds maximum ({MAX_MOCK_MEMORY_SIZE}). Limiting to maximum.")
        count = MAX_MOCK_MEMORY_SIZE
    
    logger.debug(f"Generating {count} mock memory items")
    
    # Generate mock data
    memory_data = []
    
    # If memory tier is specified, only generate for that tier
    tiers = [memory_tier] if memory_tier else list(MemoryTier)
    
    for _ in range(count):
        # Select a random tier if none specified
        tier = random.choice(tiers) if memory_tier is None else memory_tier
        
        # Generate a memory item with appropriate structure for the tier
        item = {
            "id": str(uuid.uuid4()),
            "tier": tier.value,
            "created_at": (datetime.datetime.now() - datetime.timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )).isoformat(),
            "content": generate_random_text(random.randint(20, 200)),
            "metadata": {
                "source": random.choice(["user", "system", "external"]),
                "importance": random.uniform(0, 1),
                "tags": random.sample(["memory", "concept", "fact", "rule", "experience"], 
                                     random.randint(1, 3))
            }
        }
        
        # Add tier-specific fields
        if tier == MemoryTier.WORKING:
            item["ttl"] = random.randint(60, 3600)  # Time to live in seconds
            item["active"] = random.choice([True, False])
        
        elif tier == MemoryTier.SHORT_TERM:
            item["access_count"] = random.randint(1, 50)
            item["last_accessed"] = (datetime.datetime.now() - datetime.timedelta(
                hours=random.randint(0, 48)
            )).isoformat()
        
        elif tier == MemoryTier.LONG_TERM:
            item["strength"] = random.uniform(0.1, 1.0)
            item["connections"] = [str(uuid.uuid4()) for _ in range(random.randint(0, 5))]
            item["consolidated"] = random.choice([True, False])
        
        memory_data.append(item)
    
    return memory_data


def generate_random_text(length: int) -> str:
    """
    Generate random text for testing purposes.
    
    Args:
        length: Approximate length of text to generate
        
    Returns:
        Random text string
    """
    words = [
        "memory", "cognitive", "neural", "architecture", "system", "process", 
        "data", "information", "knowledge", "learning", "model", "function",
        "structure", "pattern", "concept", "idea", "thought", "recall",
        "storage", "retrieval", "encoding", "decoding", "processing", "analysis",
        "synthesis", "integration", "connection", "network", "node", "link"
    ]
    
    # Generate a random text of approximately the requested length
    result = []
    current_length = 0
    
    while current_length < length:
        word = random.choice(words)
        result.append(word)
        current_length += len(word) + 1  # +1 for space
    
    return " ".join(result)


@contextmanager
def timed_test_context(name: str, threshold_ms: Optional[int] = None):
    """
    Context manager for timing test execution.
    
    Args:
        name: Name of the test for logging
        threshold_ms: Optional threshold in milliseconds for warnings
        
    Yields:
        None
        
    Example:
        with timed_test_context("memory_retrieval", threshold_ms=100):
            result = memory_system.retrieve("test_query")
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if threshold_ms and elapsed_time > threshold_ms:
            logger.warning(f"Test '{name}' exceeded time threshold: {elapsed_time:.2f}ms (threshold: {threshold_ms}ms)")
        else:
            logger.debug(f"Test '{name}' completed in {elapsed_time:.2f}ms")


def create_test_fixture(fixture_type: str, **kwargs) -> dict[str, Any]:
    """
    Create a test fixture for testing.
    
    Args:
        fixture_type: Type of fixture to create
        **kwargs: Additional parameters for fixture creation
        
    Returns:
        Dictionary containing fixture data
        
    Raises:
        ValueError: If an invalid fixture type is provided
    """
    valid_types = ["memory_system", "health_system", "cognitive_process", "integration"]
    
    if fixture_type not in valid_types:
        logger.error(f"Invalid fixture type: {fixture_type}. Valid types: {valid_types}")
        raise ValueError(f"Invalid fixture type: {fixture_type}. Valid types: {valid_types}")
    
    logger.debug(f"Creating test fixture of type '{fixture_type}'")
    
    if fixture_type == "memory_system":
        return create_memory_system_fixture(**kwargs)
    elif fixture_type == "health_system":
        return create_health_system_fixture(**kwargs)
    elif fixture_type == "cognitive_process":
        return create_cognitive_process_fixture(**kwargs)
    elif fixture_type == "integration":
        return create_integration_fixture(**kwargs)
    
    # This should never happen due to the validation above
    return {}


def create_memory_system_fixture(**kwargs) -> dict[str, Any]:
    """
    Create a memory system test fixture.
    
    Args:
        **kwargs: Additional parameters for fixture creation
        
    Returns:
        Dictionary containing memory system fixture data
    """
    # Default parameters
    params = {
        "working_memory_size": kwargs.get("working_memory_size", 10),
        "short_term_memory_size": kwargs.get("short_term_memory_size", 100),
        "long_term_memory_size": kwargs.get("long_term_memory_size", 1000),
        "consolidation_threshold": kwargs.get("consolidation_threshold", 0.7),
        "decay_rate": kwargs.get("decay_rate", 0.05),
    }
    
    # Generate initial memory contents
    memory_contents = {
        "working": generate_mock_memory_data("small", MemoryTier.WORKING),
        "short_term": generate_mock_memory_data("small", MemoryTier.SHORT_TERM),
        "long_term": generate_mock_memory_data("small", MemoryTier.LONG_TERM)
    }
    
    return {
        "type": "memory_system",
        "params": params,
        "contents": memory_contents
    }


def create_health_system_fixture(**kwargs) -> dict[str, Any]:
    """
    Create a health system test fixture.
    
    Args:
        **kwargs: Additional parameters for fixture creation
        
    Returns:
        Dictionary containing health system fixture data
    """
    # Default parameters
    params = {
        "energy_level": kwargs.get("energy_level", 100),
        "fatigue_rate": kwargs.get("fatigue_rate", 0.1),
        "recovery_rate": kwargs.get("recovery_rate", 0.05),
        "stress_level": kwargs.get("stress_level", 0),
        "stress_threshold": kwargs.get("stress_threshold", 80),
    }
    
    return {
        "type": "health_system",
        "params": params,
        "status": {
            "current_energy": params["energy_level"],
            "current_stress": params["stress_level"],
            "is_fatigued": False,
            "is_stressed": False,
            "last_recovery": datetime.datetime.now().isoformat()
        }
    }


def create_cognitive_process_fixture(**kwargs) -> dict[str, Any]:
    """
    Create a cognitive process test fixture.
    
    Args:
        **kwargs: Additional parameters for fixture creation
        
    Returns:
        Dictionary containing cognitive process fixture data
    """
    # Default parameters
    params = {
        "process_type": kwargs.get("process_type", "reasoning"),
        "complexity": kwargs.get("complexity", 0.5),
        "energy_cost": kwargs.get("energy_cost", 10),
        "accuracy": kwargs.get("accuracy", 0.9),
    }
    
    return {
        "type": "cognitive_process",
        "params": params,
        "state": {
            "active": False,
            "progress": 0,
            "results": [],
            "errors": []
        }
    }


def create_integration_fixture(**kwargs) -> dict[str, Any]:
    """
    Create an integration test fixture.
    
    Args:
        **kwargs: Additional parameters for fixture creation
        
    Returns:
        Dictionary containing integration fixture data
    """
    # Default parameters
    params = {
        "llm_provider": kwargs.get("llm_provider", "mock"),
        "api_key": kwargs.get("api_key", "test_key"),
        "model": kwargs.get("model", "test-model"),
        "max_tokens": kwargs.get("max_tokens", 1000),
    }
    
    return {
        "type": "integration",
        "params": params,
        "mock_responses": {
            "default": "This is a mock response from the LLM integration.",
            "error": {"error": "This is a mock error response."},
            "timeout": {"error": "Request timed out."}
        }
    }


# Main execution guard
if __name__ == "__main__":
    logger.warning("This module is not intended to be run directly.")