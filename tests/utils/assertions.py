"""
Assertions Utility Module for NeuroCognitive Architecture Tests.

This module provides specialized assertion utilities for testing the NeuroCognitive Architecture
components. It extends the standard Python unittest assertions with domain-specific validation
functions that make tests more expressive and provide better error messages when tests fail.

The assertions in this module are designed to:
1. Improve test readability by encapsulating complex validation logic
2. Provide detailed, contextual error messages for faster debugging
3. Handle common testing patterns in the NCA system
4. Support both unit and integration testing scenarios

Usage:
    from neuroca.tests.utils.assertions import (
        assert_memory_state,
        assert_response_contains,
        assert_health_metrics,
        # etc.
    )

    # In a test case
    def test_memory_retrieval():
        memory = system.retrieve_memory("concept_x")
        assert_memory_state(memory, 
                           expected_activation=0.7, 
                           expected_decay_rate=0.05,
                           tolerance=0.01)
"""

import inspect
import json
import logging
import re
from collections.abc import Sequence
from typing import Any, Optional, Union

import numpy as np

# Configure logger for assertions
logger = logging.getLogger(__name__)


def assert_equal(actual: Any, expected: Any, msg: Optional[str] = None) -> None:
    """
    Assert that two values are equal with a clear error message.
    
    Args:
        actual: The actual value from the system under test
        expected: The expected value
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the values are not equal
    """
    if actual != expected:
        error_msg = msg or f"Expected {expected!r}, but got {actual!r}"
        logger.debug(f"Equality assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_not_equal(actual: Any, unexpected: Any, msg: Optional[str] = None) -> None:
    """
    Assert that two values are not equal.
    
    Args:
        actual: The actual value from the system under test
        unexpected: The value that should not match actual
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the values are equal
    """
    if actual == unexpected:
        error_msg = msg or f"Expected value to differ from {unexpected!r}, but got the same value"
        logger.debug(f"Inequality assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_true(condition: bool, msg: Optional[str] = None) -> None:
    """
    Assert that a condition is True.
    
    Args:
        condition: The condition to evaluate
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the condition is False
    """
    if not condition:
        error_msg = msg or "Expected condition to be True, but got False"
        logger.debug(f"Truth assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_false(condition: bool, msg: Optional[str] = None) -> None:
    """
    Assert that a condition is False.
    
    Args:
        condition: The condition to evaluate
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the condition is True
    """
    if condition:
        error_msg = msg or "Expected condition to be False, but got True"
        logger.debug(f"Falsehood assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_is_none(value: Any, msg: Optional[str] = None) -> None:
    """
    Assert that a value is None.
    
    Args:
        value: The value to check
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the value is not None
    """
    if value is not None:
        error_msg = msg or f"Expected None, but got {value!r}"
        logger.debug(f"None assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_is_not_none(value: Any, msg: Optional[str] = None) -> None:
    """
    Assert that a value is not None.
    
    Args:
        value: The value to check
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the value is None
    """
    if value is None:
        error_msg = msg or "Expected a non-None value, but got None"
        logger.debug(f"Not None assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_in(item: Any, container: Sequence, msg: Optional[str] = None) -> None:
    """
    Assert that an item is in a container.
    
    Args:
        item: The item to check for
        container: The container to check in
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the item is not in the container
    """
    if item not in container:
        error_msg = msg or f"Expected {item!r} to be in {container!r}"
        logger.debug(f"Membership assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_not_in(item: Any, container: Sequence, msg: Optional[str] = None) -> None:
    """
    Assert that an item is not in a container.
    
    Args:
        item: The item to check for
        container: The container to check in
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the item is in the container
    """
    if item in container:
        error_msg = msg or f"Expected {item!r} not to be in {container!r}"
        logger.debug(f"Non-membership assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_almost_equal(
    actual: Union[float, np.ndarray], 
    expected: Union[float, np.ndarray], 
    tolerance: float = 1e-7,
    msg: Optional[str] = None
) -> None:
    """
    Assert that two numeric values or arrays are almost equal within a tolerance.
    
    Args:
        actual: The actual value or array
        expected: The expected value or array
        tolerance: The maximum allowed difference between values
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the values differ by more than the tolerance
        TypeError: If inputs are not numeric
    """
    if not isinstance(actual, (int, float, np.ndarray)) or not isinstance(expected, (int, float, np.ndarray)):
        raise TypeError("Both actual and expected must be numeric types or numpy arrays")
    
    if isinstance(actual, np.ndarray) and isinstance(expected, np.ndarray):
        if actual.shape != expected.shape:
            error_msg = msg or f"Array shapes don't match: {actual.shape} vs {expected.shape}"
            logger.debug(f"Array shape mismatch: {error_msg}")
            raise AssertionError(error_msg)
        
        if not np.allclose(actual, expected, rtol=tolerance, atol=tolerance):
            max_diff = np.max(np.abs(actual - expected))
            error_msg = msg or f"Arrays differ by max of {max_diff}, which exceeds tolerance {tolerance}"
            logger.debug(f"Array almost equal assertion failed: {error_msg}")
            raise AssertionError(error_msg)
    else:
        # Convert to float to handle int vs float comparisons
        actual_float = float(actual)
        expected_float = float(expected)
        if abs(actual_float - expected_float) > tolerance:
            error_msg = msg or f"Expected {expected} within tolerance {tolerance}, but got {actual}"
            logger.debug(f"Almost equal assertion failed: {error_msg}")
            raise AssertionError(error_msg)


def assert_dict_contains_subset(
    subset: dict[Any, Any], 
    full_dict: dict[Any, Any], 
    msg: Optional[str] = None
) -> None:
    """
    Assert that a dictionary contains all key-value pairs from a subset dictionary.
    
    Args:
        subset: The subset dictionary with expected key-value pairs
        full_dict: The full dictionary to check against
        msg: Optional custom error message
        
    Raises:
        AssertionError: If any key-value pair from subset is not in full_dict
    """
    missing_items = {}
    mismatched_items = {}
    
    for key, value in subset.items():
        if key not in full_dict:
            missing_items[key] = value
        elif full_dict[key] != value:
            mismatched_items[key] = (value, full_dict[key])
    
    if missing_items or mismatched_items:
        error_parts = []
        if missing_items:
            error_parts.append(f"Missing keys: {missing_items}")
        if mismatched_items:
            formatted_mismatches = {k: f"expected={v[0]!r}, actual={v[1]!r}" for k, v in mismatched_items.items()}
            error_parts.append(f"Mismatched values: {formatted_mismatches}")
        
        error_msg = msg or "; ".join(error_parts)
        logger.debug(f"Dict subset assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_raises(
    expected_exception: type, 
    callable_obj: callable, 
    *args, 
    **kwargs
) -> Any:
    """
    Context manager to assert that a specific exception is raised.
    
    Args:
        expected_exception: The exception class expected to be raised
        callable_obj: The callable to execute
        *args: Positional arguments to pass to the callable
        **kwargs: Keyword arguments to pass to the callable
        
    Returns:
        The exception that was raised
        
    Raises:
        AssertionError: If the expected exception is not raised
    """
    try:
        callable_obj(*args, **kwargs)
        caller = inspect.getframeinfo(inspect.currentframe().f_back)
        error_msg = (f"Expected {expected_exception.__name__} to be raised, but no exception was raised. "
                    f"Called from {caller.filename}:{caller.lineno}")
        logger.debug(f"Exception assertion failed: {error_msg}")
        raise AssertionError(error_msg)
    except Exception as e:
        if not isinstance(e, expected_exception):
            caller = inspect.getframeinfo(inspect.currentframe().f_back)
            error_msg = (f"Expected {expected_exception.__name__} but got {type(e).__name__}: {str(e)}. "
                        f"Called from {caller.filename}:{caller.lineno}")
            logger.debug(f"Wrong exception type: {error_msg}")
            raise AssertionError(error_msg) from e
        return e


def assert_json_equal(
    actual_json: Union[str, dict, list], 
    expected_json: Union[str, dict, list],
    msg: Optional[str] = None
) -> None:
    """
    Assert that two JSON objects or strings are equal, ignoring formatting differences.
    
    Args:
        actual_json: The actual JSON object or string
        expected_json: The expected JSON object or string
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the JSON objects are not equal
        ValueError: If the inputs are not valid JSON
    """
    # Convert strings to objects if needed
    if isinstance(actual_json, str):
        try:
            actual_obj = json.loads(actual_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid actual JSON: {e}")
    else:
        actual_obj = actual_json
        
    if isinstance(expected_json, str):
        try:
            expected_obj = json.loads(expected_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid expected JSON: {e}")
    else:
        expected_obj = expected_json
    
    # Compare the objects
    if actual_obj != expected_obj:
        # Create a detailed diff for better debugging
        actual_str = json.dumps(actual_obj, sort_keys=True, indent=2)
        expected_str = json.dumps(expected_obj, sort_keys=True, indent=2)
        
        error_msg = msg or f"JSON objects are not equal:\nExpected:\n{expected_str}\n\nActual:\n{actual_str}"
        logger.debug("JSON equality assertion failed")
        raise AssertionError(error_msg)


def assert_response_contains(
    response_text: str, 
    expected_content: Union[str, list[str], set[str]],
    case_sensitive: bool = True,
    msg: Optional[str] = None
) -> None:
    """
    Assert that a response text contains expected content (string or multiple strings).
    
    Args:
        response_text: The text response to check
        expected_content: String or list/set of strings that should be in the response
        case_sensitive: Whether to perform case-sensitive matching
        msg: Optional custom error message
        
    Raises:
        AssertionError: If any expected content is not found in the response
    """
    if not case_sensitive:
        response_text = response_text.lower()
    
    if isinstance(expected_content, str):
        expected_items = [expected_content]
    else:
        expected_items = list(expected_content)
    
    if not case_sensitive:
        expected_items = [item.lower() for item in expected_items]
    
    missing_items = [item for item in expected_items if item not in response_text]
    
    if missing_items:
        error_msg = msg or f"Response missing expected content: {missing_items}"
        logger.debug(f"Response content assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_memory_state(
    memory_obj: Any,
    expected_activation: Optional[float] = None,
    expected_decay_rate: Optional[float] = None,
    expected_content: Optional[Any] = None,
    expected_attributes: Optional[dict[str, Any]] = None,
    tolerance: float = 1e-5,
    msg: Optional[str] = None
) -> None:
    """
    Assert that a memory object has the expected state.
    
    Args:
        memory_obj: The memory object to check
        expected_activation: Expected activation level (if applicable)
        expected_decay_rate: Expected decay rate (if applicable)
        expected_content: Expected content of the memory
        expected_attributes: Dictionary of expected attribute values
        tolerance: Tolerance for floating point comparisons
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the memory state doesn't match expectations
    """
    assert_is_not_none(memory_obj, "Memory object is None")
    
    errors = []
    
    # Check activation if specified
    if expected_activation is not None:
        if not hasattr(memory_obj, 'activation'):
            errors.append("Memory object has no 'activation' attribute")
        else:
            actual_activation = memory_obj.activation
            if abs(actual_activation - expected_activation) > tolerance:
                errors.append(f"Expected activation {expected_activation}, got {actual_activation}")
    
    # Check decay rate if specified
    if expected_decay_rate is not None:
        if not hasattr(memory_obj, 'decay_rate'):
            errors.append("Memory object has no 'decay_rate' attribute")
        else:
            actual_decay_rate = memory_obj.decay_rate
            if abs(actual_decay_rate - expected_decay_rate) > tolerance:
                errors.append(f"Expected decay_rate {expected_decay_rate}, got {actual_decay_rate}")
    
    # Check content if specified
    if expected_content is not None:
        if not hasattr(memory_obj, 'content'):
            errors.append("Memory object has no 'content' attribute")
        else:
            actual_content = memory_obj.content
            if actual_content != expected_content:
                errors.append(f"Expected content {expected_content!r}, got {actual_content!r}")
    
    # Check additional attributes if specified
    if expected_attributes:
        for attr_name, expected_value in expected_attributes.items():
            if not hasattr(memory_obj, attr_name):
                errors.append(f"Memory object has no '{attr_name}' attribute")
            else:
                actual_value = getattr(memory_obj, attr_name)
                
                # Handle numeric comparisons with tolerance
                if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                    if abs(actual_value - expected_value) > tolerance:
                        errors.append(f"Attribute '{attr_name}': expected {expected_value}, got {actual_value}")
                elif actual_value != expected_value:
                    errors.append(f"Attribute '{attr_name}': expected {expected_value!r}, got {actual_value!r}")
    
    if errors:
        error_msg = msg or f"Memory state assertion failed: {'; '.join(errors)}"
        logger.debug(error_msg)
        raise AssertionError(error_msg)


def assert_health_metrics(
    health_obj: Any,
    expected_metrics: dict[str, Union[float, tuple[float, float]]],
    tolerance: float = 1e-5,
    msg: Optional[str] = None
) -> None:
    """
    Assert that a health object has the expected metrics within tolerance.
    
    Args:
        health_obj: The health object to check
        expected_metrics: Dictionary mapping metric names to expected values or (min, max) ranges
        tolerance: Tolerance for floating point comparisons
        msg: Optional custom error message
        
    Raises:
        AssertionError: If any health metric doesn't match expectations
    """
    assert_is_not_none(health_obj, "Health object is None")
    
    errors = []
    
    for metric_name, expected_value in expected_metrics.items():
        if not hasattr(health_obj, metric_name):
            errors.append(f"Health object has no '{metric_name}' attribute")
            continue
            
        actual_value = getattr(health_obj, metric_name)
        
        # Handle range checks (min, max)
        if isinstance(expected_value, tuple) and len(expected_value) == 2:
            min_val, max_val = expected_value
            if actual_value < min_val - tolerance or actual_value > max_val + tolerance:
                errors.append(f"Metric '{metric_name}': expected between {min_val} and {max_val}, got {actual_value}")
        # Handle exact value checks
        elif isinstance(expected_value, (int, float)):
            if abs(actual_value - expected_value) > tolerance:
                errors.append(f"Metric '{metric_name}': expected {expected_value}, got {actual_value}")
        else:
            if actual_value != expected_value:
                errors.append(f"Metric '{metric_name}': expected {expected_value!r}, got {actual_value!r}")
    
    if errors:
        error_msg = msg or f"Health metrics assertion failed: {'; '.join(errors)}"
        logger.debug(error_msg)
        raise AssertionError(error_msg)


def assert_network_structure(
    network: Any,
    expected_nodes: Optional[int] = None,
    expected_edges: Optional[int] = None,
    expected_connections: Optional[list[tuple[Any, Any]]] = None,
    expected_node_attributes: Optional[dict[Any, dict[str, Any]]] = None,
    msg: Optional[str] = None
) -> None:
    """
    Assert that a network/graph structure has the expected properties.
    
    Args:
        network: The network/graph object to check
        expected_nodes: Expected number of nodes
        expected_edges: Expected number of edges
        expected_connections: List of (source, target) tuples that should exist
        expected_node_attributes: Dict mapping node IDs to expected attribute dicts
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the network structure doesn't match expectations
    """
    assert_is_not_none(network, "Network object is None")
    
    errors = []
    
    # Check node count if specified
    if expected_nodes is not None:
        try:
            actual_nodes = len(network.nodes)
            if actual_nodes != expected_nodes:
                errors.append(f"Expected {expected_nodes} nodes, got {actual_nodes}")
        except (AttributeError, TypeError):
            errors.append("Network object doesn't support node counting")
    
    # Check edge count if specified
    if expected_edges is not None:
        try:
            actual_edges = len(network.edges)
            if actual_edges != expected_edges:
                errors.append(f"Expected {expected_edges} edges, got {actual_edges}")
        except (AttributeError, TypeError):
            errors.append("Network object doesn't support edge counting")
    
    # Check specific connections if specified
    if expected_connections:
        for source, target in expected_connections:
            try:
                if not network.has_edge(source, target):
                    errors.append(f"Expected connection from {source} to {target} not found")
            except (AttributeError, TypeError):
                errors.append("Network object doesn't support edge checking")
                break
    
    # Check node attributes if specified
    if expected_node_attributes:
        for node_id, expected_attrs in expected_node_attributes.items():
            try:
                if node_id not in network.nodes:
                    errors.append(f"Node {node_id} not found in network")
                    continue
                
                for attr_name, expected_value in expected_attrs.items():
                    try:
                        actual_value = network.nodes[node_id][attr_name]
                        if actual_value != expected_value:
                            errors.append(f"Node {node_id}, attribute '{attr_name}': "
                                         f"expected {expected_value!r}, got {actual_value!r}")
                    except KeyError:
                        errors.append(f"Node {node_id} has no attribute '{attr_name}'")
            except (AttributeError, TypeError):
                errors.append("Network object doesn't support node attribute checking")
                break
    
    if errors:
        error_msg = msg or f"Network structure assertion failed: {'; '.join(errors)}"
        logger.debug(error_msg)
        raise AssertionError(error_msg)


def assert_regex_match(
    text: str,
    pattern: Union[str, re.Pattern],
    msg: Optional[str] = None
) -> None:
    """
    Assert that a string matches a regular expression pattern.
    
    Args:
        text: The string to check
        pattern: The regex pattern to match against (string or compiled pattern)
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the string doesn't match the pattern
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    
    if not pattern.search(text):
        error_msg = msg or f"Text does not match pattern {pattern.pattern!r}: {text!r}"
        logger.debug(f"Regex match assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_regex_not_match(
    text: str,
    pattern: Union[str, re.Pattern],
    msg: Optional[str] = None
) -> None:
    """
    Assert that a string does not match a regular expression pattern.
    
    Args:
        text: The string to check
        pattern: The regex pattern that should not match (string or compiled pattern)
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the string matches the pattern
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    
    if pattern.search(text):
        error_msg = msg or f"Text unexpectedly matches pattern {pattern.pattern!r}: {text!r}"
        logger.debug(f"Regex non-match assertion failed: {error_msg}")
        raise AssertionError(error_msg)


def assert_logs_contain(
    caplog,  # pytest's caplog fixture
    expected_message: str,
    level: Optional[int] = None,
    logger_name: Optional[str] = None,
    msg: Optional[str] = None
) -> None:
    """
    Assert that captured logs contain an expected message.
    
    Args:
        caplog: pytest's caplog fixture
        expected_message: The message text to look for
        level: Optional log level to filter by (e.g., logging.INFO)
        logger_name: Optional logger name to filter by
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the expected message is not found in the logs
    """
    for record in caplog.records:
        matches_level = level is None or record.levelno == level
        matches_logger = logger_name is None or record.name == logger_name
        
        if matches_level and matches_logger and expected_message in record.message:
            return
    
    # If we get here, the message wasn't found
    level_name = logging.getLevelName(level) if level is not None else "any"
    logger_desc = f" from logger '{logger_name}'" if logger_name else ""
    
    error_msg = msg or f"Expected log message '{expected_message}' with level {level_name}{logger_desc} not found"
    logger.debug(f"Log content assertion failed: {error_msg}")
    raise AssertionError(error_msg)


def assert_performance(
    callable_obj: callable,
    max_time_seconds: float,
    *args,
    **kwargs
) -> Any:
    """
    Assert that a callable completes within a maximum time.
    
    Args:
        callable_obj: The callable to measure
        max_time_seconds: Maximum allowed execution time in seconds
        *args: Positional arguments to pass to the callable
        **kwargs: Keyword arguments to pass to the callable
        
    Returns:
        The result of the callable
        
    Raises:
        AssertionError: If the callable takes longer than max_time_seconds
    """
    import time
    
    start_time = time.time()
    result = callable_obj(*args, **kwargs)
    elapsed_time = time.time() - start_time
    
    if elapsed_time > max_time_seconds:
        caller = inspect.getframeinfo(inspect.currentframe().f_back)
        error_msg = (f"Performance assertion failed: function took {elapsed_time:.4f}s, "
                    f"exceeding limit of {max_time_seconds:.4f}s. "
                    f"Called from {caller.filename}:{caller.lineno}")
        logger.debug(error_msg)
        raise AssertionError(error_msg)
    
    return result