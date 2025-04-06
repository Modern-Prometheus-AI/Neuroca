"""
NeuroCognitive Architecture (NCA) Test Configuration

This module contains pytest fixtures and configuration for the NCA test suite.
It provides common test dependencies, mock objects, and utilities that can be
reused across test modules to ensure consistent testing environments.

The fixtures defined here are automatically discovered by pytest and made
available to all test functions without explicit imports.
"""

import logging
import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

# Ensure the project root is in the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Load test environment variables
load_dotenv(Path(__file__).parent / ".env.test", override=True)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """
    Set up the global test environment.
    
    This fixture runs once per test session and configures the environment
    for all tests. It sets environment variables, configures logging,
    and performs any other necessary setup.
    """
    # Set test-specific environment variables
    os.environ["NEUROCA_ENV"] = "test"
    os.environ["NEUROCA_LOG_LEVEL"] = "DEBUG"
    
    # Yield control to tests
    yield
    
    # Clean up after all tests have run
    logging.info("Cleaning up test environment")


@pytest.fixture()
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test file operations.
    
    Yields:
        Path: Path to the temporary directory
        
    The directory is automatically cleaned up after the test completes.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture()
def sample_config() -> dict[str, Any]:
    """
    Provide a sample configuration dictionary for testing.
    
    Returns:
        Dict[str, Any]: A dictionary containing sample configuration values
    """
    return {
        "memory": {
            "working_memory": {
                "capacity": 7,
                "decay_rate": 0.1
            },
            "short_term_memory": {
                "capacity": 100,
                "retention_period": 3600  # 1 hour in seconds
            },
            "long_term_memory": {
                "storage_path": "/tmp/neuroca/ltm",
                "indexing_strategy": "semantic"
            }
        },
        "health": {
            "energy": {
                "max_level": 100,
                "depletion_rate": 0.05,
                "recovery_rate": 0.02
            },
            "stress": {
                "initial_level": 0,
                "max_level": 100,
                "recovery_rate": 0.01
            }
        },
        "llm": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "logging": {
            "level": "INFO",
            "file_path": "/tmp/neuroca/logs/neuroca.log"
        }
    }


@pytest.fixture()
def mock_llm_client() -> MagicMock:
    """
    Create a mock LLM client for testing LLM integration components.
    
    Returns:
        MagicMock: A mock object that simulates an LLM client
    """
    mock = MagicMock()
    
    # Configure the mock to return a predefined response
    mock.generate.return_value = {
        "text": "This is a mock LLM response for testing purposes.",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20
        }
    }
    
    return mock


@pytest.fixture()
def mock_db_session() -> Generator[MagicMock, None, None]:
    """
    Create a mock database session for testing database interactions.
    
    Yields:
        MagicMock: A mock database session object
        
    The mock session is configured to simulate basic database operations.
    """
    session = MagicMock()
    
    # Configure common database operations
    session.query.return_value = session
    session.filter.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    
    return session


@pytest.fixture()
def sample_memory_item() -> dict[str, Any]:
    """
    Provide a sample memory item for testing memory components.
    
    Returns:
        Dict[str, Any]: A dictionary representing a memory item
    """
    return {
        "id": "mem_12345",
        "content": "This is a sample memory for testing",
        "created_at": "2023-01-01T12:00:00Z",
        "last_accessed": "2023-01-02T12:00:00Z",
        "access_count": 5,
        "importance": 0.75,
        "metadata": {
            "source": "test",
            "category": "general",
            "tags": ["sample", "test", "memory"]
        }
    }


@pytest.fixture()
def mock_file_system() -> Generator[None, None, None]:
    """
    Mock file system operations for testing file I/O.
    
    This fixture patches common file system operations to prevent
    actual file system changes during tests.
    """
    mock_open_data = {}
    
    def mock_open_impl(file, mode='r', *args, **kwargs):
        file_str = str(file)
        mock_file = MagicMock()
        
        if 'w' in mode:
            mock_open_data[file_str] = ''
            mock_file.write.side_effect = lambda data: mock_open_data.update({file_str: mock_open_data.get(file_str, '') + data})
        elif 'r' in mode and file_str in mock_open_data:
            mock_file.read.return_value = mock_open_data[file_str]
            mock_file.__iter__.return_value = mock_open_data[file_str].splitlines(True)
        
        return mock_file
    
    with patch('builtins.open', mock_open_impl):
        with patch('os.path.exists', lambda path: str(path) in mock_open_data):
            with patch('os.makedirs'):
                yield


@pytest.fixture()
def api_client() -> MagicMock:
    """
    Create a mock API client for testing API interactions.
    
    Returns:
        MagicMock: A mock API client object
    """
    client = MagicMock()
    
    # Configure common response patterns
    def mock_get(url, *args, **kwargs):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"status": "success", "data": {}}
        return response
    
    def mock_post(url, *args, **kwargs):
        response = MagicMock()
        response.status_code = 201
        response.json.return_value = {"status": "created", "data": {}}
        return response
    
    client.get.side_effect = mock_get
    client.post.side_effect = mock_post
    
    return client


@pytest.fixture()
def sample_health_state() -> dict[str, Any]:
    """
    Provide a sample health state for testing health dynamics components.
    
    Returns:
        Dict[str, Any]: A dictionary representing a health state
    """
    return {
        "energy": {
            "current": 80,
            "max": 100,
            "rate_of_change": -0.05
        },
        "stress": {
            "current": 20,
            "max": 100,
            "rate_of_change": 0.02
        },
        "focus": {
            "current": 90,
            "max": 100,
            "rate_of_change": -0.01
        },
        "last_updated": "2023-01-01T12:00:00Z"
    }


@pytest.fixture()
def disable_external_calls() -> Generator[None, None, None]:
    """
    Disable all external API calls during tests.
    
    This fixture patches common HTTP libraries to prevent actual
    external API calls during tests.
    """
    with patch('requests.get'), patch('requests.post'), patch('requests.put'), patch('requests.delete'):
        with patch('aiohttp.ClientSession.get'), patch('aiohttp.ClientSession.post'):
            with patch('httpx.get'), patch('httpx.post'):
                yield


@pytest.fixture()
def capture_logs() -> Generator[list[dict[str, Any]], None, None]:
    """
    Capture log messages during test execution.
    
    Yields:
        List[Dict[str, Any]]: A list of captured log records
    """
    captured_logs = []
    
    class LogCaptureHandler(logging.Handler):
        def emit(self, record):
            captured_logs.append({
                'level': record.levelname,
                'message': record.getMessage(),
                'logger': record.name
            })
    
    handler = LogCaptureHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    yield captured_logs
    
    root_logger.removeHandler(handler)


# Add pytest configuration
def pytest_addoption(parser):
    """
    Add custom command line options to pytest.
    
    Args:
        parser: The pytest command line parser
    """
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that may have external dependencies"
    )
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Run slow tests that may take a long time to complete"
    )


def pytest_configure(config):
    """
    Configure pytest based on command line options.
    
    Args:
        config: The pytest configuration object
    """
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection based on command line options.
    
    Args:
        config: The pytest configuration object
        items: List of collected test items
    """
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    skip_slow = pytest.mark.skip(reason="need --slow option to run")
    
    for item in items:
        if "integration" in item.keywords and not config.getoption("--integration"):
            item.add_marker(skip_integration)
        if "slow" in item.keywords and not config.getoption("--slow"):
            item.add_marker(skip_slow)