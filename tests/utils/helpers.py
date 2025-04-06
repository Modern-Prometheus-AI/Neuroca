"""
Test Helpers Module for NeuroCognitive Architecture (NCA)

This module provides utility functions and classes to facilitate testing across the NCA project.
It includes fixtures, mocks, data generators, assertion helpers, and other testing utilities
that can be reused across different test suites.

Usage:
    from neuroca.tests.utils.helpers import (
        generate_test_memory_data,
        MockLLMResponse,
        assert_memory_consistency,
        setup_test_environment,
        TeardownManager,
    )

    # Generate test data
    memory_data = generate_test_memory_data(size=10)
    
    # Use mock LLM responses
    with MockLLMResponse(responses=["Test response"]):
        result = my_function_that_calls_llm()
        
    # Use assertion helpers
    assert_memory_consistency(expected_memory, actual_memory)
"""

import json
import os
import random
import string
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional, Union
from unittest.mock import patch

import numpy as np
import pytest
from loguru import logger

# Constants for test data generation
DEFAULT_EMBEDDING_DIM = 768
DEFAULT_MEMORY_TYPES = ["episodic", "semantic", "procedural"]
DEFAULT_HEALTH_METRICS = ["energy", "coherence", "stability"]


def generate_random_string(length: int = 10) -> str:
    """
    Generate a random string of specified length.
    
    Args:
        length: Length of the string to generate (default: 10)
        
    Returns:
        A random string of the specified length
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_embedding(dim: int = DEFAULT_EMBEDDING_DIM) -> np.ndarray:
    """
    Generate a random embedding vector of specified dimension.
    
    Args:
        dim: Dimension of the embedding vector (default: 768)
        
    Returns:
        A normalized numpy array representing an embedding vector
    """
    vector = np.random.randn(dim)
    # Normalize to unit length
    return vector / np.linalg.norm(vector)


def generate_test_memory_data(
    size: int = 5,
    memory_type: str = "episodic",
    with_embeddings: bool = True,
    with_metadata: bool = True
) -> list[dict[str, Any]]:
    """
    Generate test memory data for testing memory-related functionality.
    
    Args:
        size: Number of memory items to generate (default: 5)
        memory_type: Type of memory to generate (default: "episodic")
        with_embeddings: Whether to include embedding vectors (default: True)
        with_metadata: Whether to include metadata (default: True)
        
    Returns:
        A list of dictionaries representing memory items
    
    Example:
        >>> memories = generate_test_memory_data(size=3, memory_type="semantic")
        >>> len(memories)
        3
        >>> "content" in memories[0]
        True
    """
    if memory_type not in DEFAULT_MEMORY_TYPES:
        raise ValueError(f"Invalid memory type: {memory_type}. Must be one of {DEFAULT_MEMORY_TYPES}")
    
    result = []
    
    for i in range(size):
        memory_item = {
            "id": str(uuid.uuid4()),
            "content": f"Test {memory_type} memory #{i}: {generate_random_string(20)}",
            "memory_type": memory_type,
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "last_accessed": (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat(),
            "access_count": random.randint(1, 100),
            "importance": random.uniform(0, 1),
        }
        
        if with_embeddings:
            memory_item["embedding"] = generate_random_embedding().tolist()
            
        if with_metadata:
            memory_item["metadata"] = {
                "source": random.choice(["user_input", "system_generated", "external_source"]),
                "context": generate_random_string(15),
                "tags": [generate_random_string(5) for _ in range(random.randint(1, 5))],
                "related_memories": [str(uuid.uuid4()) for _ in range(random.randint(0, 3))]
            }
            
        result.append(memory_item)
        
    return result


def generate_test_health_data(
    metrics: Optional[list[str]] = None,
    time_points: int = 10,
    with_fluctuations: bool = True
) -> dict[str, list[float]]:
    """
    Generate test health metrics data for testing health dynamics functionality.
    
    Args:
        metrics: List of health metrics to generate (default: DEFAULT_HEALTH_METRICS)
        time_points: Number of time points to generate (default: 10)
        with_fluctuations: Whether to add random fluctuations to the data (default: True)
        
    Returns:
        A dictionary mapping metric names to lists of values
    """
    if metrics is None:
        metrics = DEFAULT_HEALTH_METRICS
        
    result = {}
    
    for metric in metrics:
        # Start with a base value between 0.5 and 0.9
        base_value = random.uniform(0.5, 0.9)
        values = []
        
        for _i in range(time_points):
            if with_fluctuations:
                # Add some random fluctuation
                fluctuation = random.uniform(-0.1, 0.1)
                value = max(0.0, min(1.0, base_value + fluctuation))
            else:
                value = base_value
                
            values.append(round(value, 3))
            
        result[metric] = values
        
    return result


class MockLLMResponse:
    """
    Context manager for mocking LLM responses in tests.
    
    This class provides a convenient way to mock LLM responses during testing,
    allowing for deterministic testing of components that interact with LLMs.
    
    Attributes:
        responses: List of responses to return from the mocked LLM
        delay: Optional delay to simulate LLM processing time
        error_rate: Probability of simulating an error response
        
    Example:
        >>> with MockLLMResponse(responses=["Test response"]):
        ...     result = my_function_that_calls_llm()
        ...     assert result == "Test response"
    """
    
    def __init__(
        self,
        responses: list[str],
        delay: Optional[float] = None,
        error_rate: float = 0.0,
        error_message: str = "Simulated LLM error"
    ):
        """
        Initialize the MockLLMResponse context manager.
        
        Args:
            responses: List of responses to return from the mocked LLM
            delay: Optional delay in seconds to simulate LLM processing time
            error_rate: Probability (0.0-1.0) of simulating an error response
            error_message: Error message to use when simulating errors
        """
        self.responses = responses
        self.delay = delay
        self.error_rate = error_rate
        self.error_message = error_message
        self.response_index = 0
        self.patches = []
        
    def __enter__(self):
        """Set up the mock LLM response environment."""
        # This is a placeholder for the actual LLM integration path
        # Update this path when the actual LLM integration is implemented
        mock_paths = [
            "neuroca.integration.llm_client.LLMClient.generate",
            "neuroca.integration.llm_client.LLMClient.complete",
            "neuroca.integration.llm_client.LLMClient.chat"
        ]
        
        for path in mock_paths:
            mock = patch(path, side_effect=self._mock_llm_response)
            self.patches.append(mock)
            mock.start()
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the mock LLM response environment."""
        for mock_patch in self.patches:
            mock_patch.stop()
            
    def _mock_llm_response(self, *args, **kwargs):
        """
        Mock LLM response function.
        
        Args:
            *args: Arguments passed to the mocked function
            **kwargs: Keyword arguments passed to the mocked function
            
        Returns:
            A mocked LLM response
            
        Raises:
            Exception: If error simulation is triggered
        """
        # Simulate processing delay if specified
        if self.delay:
            time.sleep(self.delay)
            
        # Simulate error if error_rate probability is met
        if random.random() < self.error_rate:
            raise Exception(self.error_message)
            
        # Get the next response or cycle back to the beginning if exhausted
        if self.response_index >= len(self.responses):
            self.response_index = 0
            
        response = self.responses[self.response_index]
        self.response_index += 1
        
        return response


def assert_memory_consistency(expected: dict[str, Any], actual: dict[str, Any], tolerance: float = 1e-6):
    """
    Assert that two memory items are consistent, with special handling for embeddings.
    
    Args:
        expected: Expected memory item
        actual: Actual memory item
        tolerance: Tolerance for floating point comparisons (default: 1e-6)
        
    Raises:
        AssertionError: If the memory items are not consistent
    """
    # Check basic fields
    for key in expected:
        if key == "embedding":
            continue  # Handle embeddings separately
            
        assert key in actual, f"Key '{key}' missing from actual memory"
        assert expected[key] == actual[key], f"Value mismatch for key '{key}': expected {expected[key]}, got {actual[key]}"
        
    # Check embeddings if present
    if "embedding" in expected and "embedding" in actual:
        expected_embedding = np.array(expected["embedding"])
        actual_embedding = np.array(actual["embedding"])
        
        assert expected_embedding.shape == actual_embedding.shape, \
            f"Embedding shape mismatch: expected {expected_embedding.shape}, got {actual_embedding.shape}"
            
        # Check if embeddings are close enough (using L2 norm of difference)
        diff_norm = np.linalg.norm(expected_embedding - actual_embedding)
        assert diff_norm < tolerance, \
            f"Embeddings differ by {diff_norm}, which exceeds tolerance {tolerance}"


@contextmanager
def setup_test_environment(
    config_overrides: Optional[dict[str, Any]] = None,
    temp_dir: bool = False,
    env_vars: Optional[dict[str, str]] = None
):
    """
    Context manager to set up a controlled test environment.
    
    Args:
        config_overrides: Dictionary of configuration overrides
        temp_dir: Whether to create and use a temporary directory
        env_vars: Dictionary of environment variables to set
        
    Yields:
        Dictionary containing environment setup information
    
    Example:
        >>> with setup_test_environment(
        ...     config_overrides={"memory.capacity": 100},
        ...     temp_dir=True,
        ...     env_vars={"NEUROCA_LOG_LEVEL": "DEBUG"}
        ... ) as env:
        ...     # Run tests with the configured environment
        ...     temp_path = env["temp_dir"]
    """
    original_env = {}
    temp_directory = None
    
    try:
        # Set environment variables if provided
        if env_vars:
            for key, value in env_vars.items():
                if key in os.environ:
                    original_env[key] = os.environ[key]
                os.environ[key] = value
                
        # Create temporary directory if requested
        if temp_dir:
            temp_directory = tempfile.TemporaryDirectory()
            
        # Apply configuration overrides (placeholder - implement based on actual config system)
        if config_overrides:
            # This is a placeholder for the actual configuration override mechanism
            # Update this when the configuration system is implemented
            pass
            
        # Prepare environment info to yield
        env_info = {
            "config_overrides": config_overrides or {},
        }
        
        if temp_directory:
            env_info["temp_dir"] = Path(temp_directory.name)
            
        yield env_info
        
    finally:
        # Restore original environment variables
        for key, value in original_env.items():
            os.environ[key] = value
            
        # Remove any environment variables that were added
        if env_vars:
            for key in env_vars:
                if key not in original_env:
                    os.environ.pop(key, None)
                    
        # Clean up temporary directory
        if temp_directory:
            temp_directory.cleanup()


class TeardownManager:
    """
    Manager for test resource cleanup.
    
    This class helps manage resources that need to be cleaned up after tests,
    ensuring proper teardown even if tests fail.
    
    Example:
        >>> teardown = TeardownManager()
        >>> file_path = "/tmp/test_file.txt"
        >>> with open(file_path, "w") as f:
        ...     f.write("test")
        >>> teardown.add_cleanup(os.remove, file_path)
        >>> # Run tests...
        >>> teardown.cleanup()  # Will remove the file
    """
    
    def __init__(self):
        """Initialize the TeardownManager."""
        self.cleanup_functions = []
        
    def add_cleanup(self, func: Callable, *args, **kwargs):
        """
        Add a cleanup function to be called during teardown.
        
        Args:
            func: Function to call during cleanup
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        self.cleanup_functions.append((func, args, kwargs))
        
    def cleanup(self):
        """
        Execute all registered cleanup functions.
        
        This method calls all registered cleanup functions in reverse order
        (last added, first cleaned up) and handles any exceptions that occur.
        """
        errors = []
        
        # Process in reverse order (LIFO)
        for func, args, kwargs in reversed(self.cleanup_functions):
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                errors.append(str(e))
                
        # Clear the cleanup functions list
        self.cleanup_functions = []
        
        # Report any errors that occurred
        if errors:
            error_msg = "\n".join(errors)
            logger.error(f"Cleanup completed with {len(errors)} errors:\n{error_msg}")
            
    def __enter__(self):
        """Support use as a context manager."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting the context."""
        self.cleanup()


def create_test_file(content: Union[str, dict, list], file_path: Optional[Path] = None) -> Path:
    """
    Create a test file with the specified content.
    
    Args:
        content: Content to write to the file (string or JSON-serializable object)
        file_path: Path where the file should be created (default: temporary file)
        
    Returns:
        Path to the created file
    """
    if file_path is None:
        fd, temp_path = tempfile.mkstemp(suffix=".json" if not isinstance(content, str) else ".txt")
        os.close(fd)
        file_path = Path(temp_path)
        
    with open(file_path, "w", encoding="utf-8") as f:
        if isinstance(content, (dict, list)):
            json.dump(content, f, indent=2)
        else:
            f.write(content)
            
    return file_path


@pytest.fixture()
def mock_llm_response():
    """
    Pytest fixture for mocking LLM responses.
    
    This fixture provides a convenient way to mock LLM responses in pytest tests.
    
    Example:
        >>> def test_with_llm(mock_llm_response):
        ...     mock_llm_response.responses = ["Test response"]
        ...     result = my_function_that_calls_llm()
        ...     assert result == "Test response"
    """
    with MockLLMResponse(responses=[]) as mock:
        yield mock


@pytest.fixture()
def test_memory_data():
    """
    Pytest fixture providing test memory data.
    
    Returns:
        A list of dictionaries representing memory items
    """
    return generate_test_memory_data(size=10)


@pytest.fixture()
def test_health_data():
    """
    Pytest fixture providing test health metrics data.
    
    Returns:
        A dictionary mapping metric names to lists of values
    """
    return generate_test_health_data()


@pytest.fixture()
def teardown_manager():
    """
    Pytest fixture providing a TeardownManager.
    
    Returns:
        A TeardownManager instance
    """
    with TeardownManager() as manager:
        yield manager