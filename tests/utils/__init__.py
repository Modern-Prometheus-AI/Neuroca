"""
Test Utilities Module for NeuroCognitive Architecture (NCA).

This module provides common utilities, fixtures, and helper functions to support
testing across the NeuroCognitive Architecture project. It aims to reduce code
duplication in tests and provide consistent testing patterns.

Usage:
    from neuroca.tests.utils import (
        create_test_memory_entry,
        MockLLMResponse,
        setup_test_database,
        assert_memory_consistency,
        ...
    )

    # Example: Create a test memory entry
    memory_entry = create_test_memory_entry(
        content="Test memory content",
        importance=0.8,
        memory_type=MemoryType.EPISODIC
    )
"""

import json
import logging
import os
import random
import string
import tempfile
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

# Configure logging for test utilities
logger = logging.getLogger(__name__)


def get_test_data_path() -> Path:
    """
    Get the path to the test data directory.
    
    Returns:
        Path: Path object pointing to the test data directory
    
    Raises:
        FileNotFoundError: If the test data directory doesn't exist
    """
    base_dir = Path(__file__).parent.parent
    test_data_path = base_dir / "data"
    
    if not test_data_path.exists():
        logger.warning(f"Test data directory not found at {test_data_path}")
        test_data_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created test data directory at {test_data_path}")
    
    return test_data_path


def load_test_json(filename: str) -> dict[str, Any]:
    """
    Load a JSON file from the test data directory.
    
    Args:
        filename: Name of the JSON file to load
        
    Returns:
        Dict containing the loaded JSON data
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    file_path = get_test_data_path() / filename
    
    try:
        with open(file_path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Test data file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in test data file {file_path}: {str(e)}")
        raise


def generate_random_string(length: int = 10) -> str:
    """
    Generate a random string of specified length.
    
    Args:
        length: Length of the random string to generate
        
    Returns:
        Random string of specified length
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_unique_id() -> str:
    """
    Generate a unique identifier for test resources.
    
    Returns:
        Unique string identifier
    """
    return f"test-{uuid.uuid4()}"


@contextmanager
def temp_env_vars(**kwargs) -> Generator[None, None, None]:
    """
    Temporarily set environment variables for testing.
    
    Args:
        **kwargs: Environment variables to set temporarily
        
    Yields:
        None
        
    Example:
        with temp_env_vars(API_KEY="test_key", DEBUG="true"):
            # Code that depends on these environment variables
            pass
    """
    original_values = {}
    
    # Save original values and set new values
    for key, value in kwargs.items():
        if key in os.environ:
            original_values[key] = os.environ[key]
        os.environ[key] = value
    
    try:
        yield
    finally:
        # Restore original values
        for key in kwargs:
            if key in original_values:
                os.environ[key] = original_values[key]
            else:
                del os.environ[key]


@contextmanager
def temp_file_with_content(content: str) -> Generator[str, None, None]:
    """
    Create a temporary file with the specified content.
    
    Args:
        content: Content to write to the temporary file
        
    Yields:
        Path to the temporary file
        
    Example:
        with temp_file_with_content("test data") as file_path:
            # Use file_path
            with open(file_path, 'r') as f:
                data = f.read()
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(content)
        temp_path = temp.name
    
    try:
        yield temp_path
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except OSError as e:
            logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")


class MockResponse:
    """
    Mock response object for testing HTTP requests.
    
    Attributes:
        status_code: HTTP status code
        json_data: Data to return when json() method is called
        text: Text content of the response
        headers: HTTP headers
        content: Binary content of the response
        
    Example:
        response = MockResponse(
            status_code=200,
            json_data={"result": "success"},
            headers={"Content-Type": "application/json"}
        )
    """
    
    def __init__(
        self,
        status_code: int = 200,
        json_data: Optional[dict[str, Any]] = None,
        text: str = "",
        headers: Optional[dict[str, str]] = None,
        content: bytes = b"",
        raise_for_status: Optional[Callable[[], None]] = None
    ):
        """
        Initialize a mock HTTP response.
        
        Args:
            status_code: HTTP status code
            json_data: Data to return when json() method is called
            text: Text content of the response
            headers: HTTP headers
            content: Binary content of the response
            raise_for_status: Custom function to call for raise_for_status method
        """
        self.status_code = status_code
        self.json_data = json_data or {}
        self.text = text
        self.headers = headers or {}
        self.content = content
        self._raise_for_status = raise_for_status
    
    def json(self) -> dict[str, Any]:
        """Return the JSON data."""
        return self.json_data
    
    def raise_for_status(self) -> None:
        """
        Raise an exception if the status code indicates an error.
        
        Raises:
            HTTPError: If status_code >= 400
        """
        if self._raise_for_status:
            self._raise_for_status()
        elif self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"Mock HTTP Error: {self.status_code}")


class TimeMock:
    """
    Utility for mocking time in tests.
    
    This class provides methods to simulate time passing in tests without
    actually waiting.
    
    Example:
        time_mock = TimeMock(start_time=datetime(2023, 1, 1))
        with time_mock.patch():
            # Code that uses time functions will use the mocked time
            assert time.time() == time_mock.current_timestamp
            
            # Advance time by 30 seconds
            time_mock.advance(seconds=30)
            assert time.time() == time_mock.current_timestamp
    """
    
    def __init__(self, start_time: Optional[datetime] = None):
        """
        Initialize the time mock.
        
        Args:
            start_time: Initial datetime to use (defaults to current time)
        """
        self.current_time = start_time or datetime.now()
        self.original_time_function = time.time
    
    @property
    def current_timestamp(self) -> float:
        """Get the current mocked timestamp as a Unix timestamp."""
        return self.current_time.timestamp()
    
    def advance(self, **kwargs) -> None:
        """
        Advance the mocked time.
        
        Args:
            **kwargs: Keyword arguments to pass to timedelta constructor
                (e.g., seconds=30, minutes=5, hours=1)
        """
        self.current_time += timedelta(**kwargs)
    
    def mocked_time(self) -> float:
        """Return the current mocked timestamp."""
        return self.current_timestamp
    
    @contextmanager
    def patch(self) -> Generator[None, None, None]:
        """
        Context manager to patch time.time with the mocked version.
        
        Yields:
            None
        """
        time.time = self.mocked_time
        try:
            yield
        finally:
            time.time = self.original_time_function


def assert_dict_subset(subset: dict[str, Any], full_dict: dict[str, Any]) -> None:
    """
    Assert that all key-value pairs in subset exist in full_dict.
    
    Args:
        subset: Dictionary with key-value pairs that should exist in full_dict
        full_dict: Dictionary to check against
        
    Raises:
        AssertionError: If any key-value pair in subset doesn't match in full_dict
    """
    for key, value in subset.items():
        assert key in full_dict, f"Key '{key}' not found in dictionary"
        
        if isinstance(value, dict) and isinstance(full_dict[key], dict):
            assert_dict_subset(value, full_dict[key])
        else:
            assert full_dict[key] == value, f"Value mismatch for key '{key}': expected {value}, got {full_dict[key]}"


def wait_for_condition(
    condition_func: Callable[[], bool],
    timeout: float = 10.0,
    interval: float = 0.1,
    error_message: str = "Condition not met within timeout period"
) -> None:
    """
    Wait for a condition to be true, with timeout.
    
    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between condition checks in seconds
        error_message: Message to include in the timeout exception
        
    Raises:
        TimeoutError: If the condition is not met within the timeout period
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return
        time.sleep(interval)
    
    raise TimeoutError(error_message)


# Export all utility functions and classes
__all__ = [
    'get_test_data_path',
    'load_test_json',
    'generate_random_string',
    'generate_unique_id',
    'temp_env_vars',
    'temp_file_with_content',
    'MockResponse',
    'TimeMock',
    'assert_dict_subset',
    'wait_for_condition',
]