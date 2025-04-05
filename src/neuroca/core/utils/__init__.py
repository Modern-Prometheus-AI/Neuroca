"""
Core Utilities Module for NeuroCognitive Architecture (NCA)

This module provides essential utility functions and classes used throughout the NCA system.
It includes tools for logging, error handling, data validation, performance monitoring,
type checking, and other common operations needed across the system.

Usage:
    from neuroca.core.utils import (
        validate_input, setup_logging, measure_execution_time,
        safe_serialize, retry_operation, is_valid_uuid
    )

    # Example: Set up logging
    logger = setup_logging("component_name")
    
    # Example: Validate input
    validate_input(data, required_fields=["id", "content"])
    
    # Example: Measure execution time
    with measure_execution_time("operation_name", logger) as timer:
        result = perform_complex_operation()
        timer.set_metadata({"data_size": len(result)})
"""

import contextlib
import functools
import hashlib
import inspect
import json
import logging
import os
import re
import time
import traceback
import uuid
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Configure default logging format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class ValidationError(Exception):
    """Exception raised for input validation errors."""
    pass

class RetryError(Exception):
    """Exception raised when a retry operation fails after maximum attempts."""
    pass

class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass

class ResourceError(Exception):
    """Exception raised for resource-related errors (missing, unavailable, etc.)."""
    pass

def setup_logging(
    name: str,
    level: int = logging.INFO,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up and configure a logger with the specified parameters.
    
    Args:
        name: The name of the logger
        level: The logging level (default: INFO)
        log_format: The format string for log messages
        date_format: The format string for timestamps
        log_file: Optional path to a log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    
    Returns:
        A configured logger instance
    
    Example:
        >>> logger = setup_logging("memory_manager", level=logging.DEBUG)
        >>> logger.debug("Initializing memory manager")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    formatter = logging.Formatter(log_format, date_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Ensure directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as e:
            logger.error(f"Failed to set up log file at {log_file}: {str(e)}")
    
    return logger

def validate_input(
    data: Any,
    required_fields: Optional[list[str]] = None,
    field_types: Optional[dict[str, type]] = None,
    min_length: Optional[dict[str, int]] = None,
    max_length: Optional[dict[str, int]] = None,
    regex_patterns: Optional[dict[str, str]] = None
) -> None:
    """
    Validate input data against specified requirements.
    
    Args:
        data: The data to validate (typically a dict)
        required_fields: List of field names that must be present
        field_types: Dict mapping field names to their expected types
        min_length: Dict mapping field names to their minimum lengths
        max_length: Dict mapping field names to their maximum lengths
        regex_patterns: Dict mapping field names to regex patterns they must match
    
    Raises:
        ValidationError: If validation fails
        
    Example:
        >>> user_data = {"id": "123", "name": "John", "email": "john@example.com"}
        >>> validate_input(
        ...     user_data,
        ...     required_fields=["id", "name", "email"],
        ...     field_types={"id": str, "name": str, "email": str},
        ...     regex_patterns={"email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"}
        ... )
    """
    if data is None:
        raise ValidationError("Input data cannot be None")
    
    # Check if data is a dictionary-like object
    if not hasattr(data, "__getitem__") or not hasattr(data, "get"):
        raise ValidationError(f"Expected dict-like object, got {type(data).__name__}")
    
    # Check required fields
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Check field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None and not isinstance(data[field], expected_type):
                raise ValidationError(
                    f"Field '{field}' has incorrect type. Expected {expected_type.__name__}, "
                    f"got {type(data[field]).__name__}"
                )
    
    # Check minimum lengths
    if min_length:
        for field, min_len in min_length.items():
            if field in data and data[field] is not None:
                if hasattr(data[field], "__len__") and len(data[field]) < min_len:
                    raise ValidationError(
                        f"Field '{field}' is too short. Minimum length is {min_len}, "
                        f"got {len(data[field])}"
                    )
    
    # Check maximum lengths
    if max_length:
        for field, max_len in max_length.items():
            if field in data and data[field] is not None:
                if hasattr(data[field], "__len__") and len(data[field]) > max_len:
                    raise ValidationError(
                        f"Field '{field}' is too long. Maximum length is {max_len}, "
                        f"got {len(data[field])}"
                    )
    
    # Check regex patterns
    if regex_patterns:
        for field, pattern in regex_patterns.items():
            if field in data and data[field] is not None and isinstance(data[field], str):
                if not re.match(pattern, data[field]):
                    raise ValidationError(
                        f"Field '{field}' does not match required pattern: {pattern}"
                    )

@contextlib.contextmanager
def measure_execution_time(
    operation_name: str,
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.DEBUG
):
    """
    Context manager to measure and log the execution time of a code block.
    
    Args:
        operation_name: Name of the operation being timed
        logger: Logger to use (if None, measurements are returned but not logged)
        log_level: Logging level to use
    
    Yields:
        A timer object with methods to add metadata
        
    Example:
        >>> logger = setup_logging("performance")
        >>> with measure_execution_time("data_processing", logger) as timer:
        ...     result = process_large_dataset()
        ...     timer.set_metadata({"records_processed": len(result)})
    """
    class Timer:
        def __init__(self):
            self.start_time = time.time()
            self.metadata = {}
            
        def set_metadata(self, metadata: dict[str, Any]) -> None:
            """Add metadata to be included in the log message."""
            self.metadata.update(metadata)
    
    timer = Timer()
    try:
        yield timer
    finally:
        elapsed_time = time.time() - timer.start_time
        
        # Format the log message
        message = f"{operation_name} completed in {elapsed_time:.4f} seconds"
        if timer.metadata:
            metadata_str = ", ".join(f"{k}={v}" for k, v in timer.metadata.items())
            message += f" ({metadata_str})"
        
        # Log the message if a logger was provided
        if logger:
            logger.log(log_level, message)

def retry_operation(
    max_attempts: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions_to_retry: tuple[Exception, ...] = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry operations that may fail temporarily.
    
    Args:
        max_attempts: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for the delay after each retry
        exceptions_to_retry: Tuple of exceptions that should trigger a retry
        logger: Logger to use for logging retry attempts
    
    Returns:
        A decorator function
        
    Example:
        >>> @retry_operation(max_attempts=5, exceptions_to_retry=(ConnectionError, TimeoutError))
        ... def fetch_remote_data(url):
        ...     return requests.get(url).json()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_delay = retry_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    
                    if logger:
                        if attempt < max_attempts:
                            logger.warning(
                                f"Attempt {attempt}/{max_attempts} for {func.__name__} failed: {str(e)}. "
                                f"Retrying in {current_delay:.2f} seconds..."
                            )
                        else:
                            logger.error(
                                f"All {max_attempts} attempts for {func.__name__} failed. "
                                f"Last error: {str(e)}"
                            )
                    
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
            
            if last_exception:
                raise RetryError(f"Operation {func.__name__} failed after {max_attempts} attempts") from last_exception
            
            # This should never happen, but added for type safety
            raise RetryError(f"Operation {func.__name__} failed for unknown reasons")
            
        return wrapper
    
    return decorator

def safe_serialize(obj: Any, default_value: Any = None) -> str:
    """
    Safely serialize an object to JSON, handling non-serializable types.
    
    Args:
        obj: The object to serialize
        default_value: Value to return if serialization fails
    
    Returns:
        JSON string or default_value if serialization fails
        
    Example:
        >>> data = {"name": "Test", "created_at": datetime.now()}
        >>> json_str = safe_serialize(data)
    """
    def json_serializer(o: Any) -> Any:
        """Handle non-serializable types."""
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, (set, frozenset)):
            return list(o)
        if isinstance(o, bytes):
            return o.decode('utf-8', errors='replace')
        if hasattr(o, '__dict__'):
            return o.__dict__
        if hasattr(o, 'to_dict') and callable(o.to_dict):
            return o.to_dict()
        
        # For other types, use their string representation
        return str(o)
    
    try:
        return json.dumps(obj, default=json_serializer)
    except Exception as e:
        if default_value is not None:
            return default_value
        raise ValueError(f"Failed to serialize object: {str(e)}") from e

def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        value: String to check
    
    Returns:
        True if the string is a valid UUID, False otherwise
        
    Example:
        >>> is_valid_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> is_valid_uuid("not-a-uuid")
        False
    """
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value
    except (ValueError, AttributeError, TypeError):
        return False

def generate_hash(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """
    Generate a hash of the provided data using the specified algorithm.
    
    Args:
        data: The data to hash (string or bytes)
        algorithm: The hashing algorithm to use (default: sha256)
    
    Returns:
        The hexadecimal digest of the hash
        
    Example:
        >>> generate_hash("important data")
        '9d30d0eec9c7b4c96e63e607e1a825780077cf73a11946f6f4b42d0c10a2f3c8'
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    try:
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data)
        return hash_obj.hexdigest()
    except ValueError as e:
        raise ValueError(f"Invalid hashing algorithm: {algorithm}") from e

def get_caller_info() -> dict[str, Any]:
    """
    Get information about the caller of a function.
    Useful for debugging and logging.
    
    Returns:
        Dictionary with caller information
        
    Example:
        >>> def my_function():
        ...     caller = get_caller_info()
        ...     print(f"Called by {caller['function']} in {caller['filename']}")
    """
    stack = inspect.stack()
    # stack[0] is get_caller_info, stack[1] is the function calling get_caller_info,
    # stack[2] is what we want - the caller of that function
    if len(stack) < 3:
        return {
            "filename": "unknown",
            "lineno": 0,
            "function": "unknown",
            "code_context": None
        }
    
    caller = stack[2]
    return {
        "filename": os.path.basename(caller.filename),
        "lineno": caller.lineno,
        "function": caller.function,
        "code_context": caller.code_context[0].strip() if caller.code_context else None
    }

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path as string or Path object
    
    Returns:
        Path object for the directory
        
    Raises:
        OSError: If directory creation fails
        
    Example:
        >>> data_dir = ensure_directory("./data/processed")
        >>> with open(data_dir / "results.txt", "w") as f:
        ...     f.write("Analysis complete")
    """
    path_obj = Path(path)
    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    except OSError as e:
        raise OSError(f"Failed to create directory {path}: {str(e)}") from e

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length, adding a suffix if truncated.
    
    Args:
        text: The string to truncate
        max_length: Maximum length of the result string
        suffix: String to append if truncation occurs
    
    Returns:
        Truncated string
        
    Example:
        >>> truncate_string("This is a very long string that needs truncation", 20)
        'This is a very long...'
    """
    if not text or len(text) <= max_length:
        return text
    
    # Adjust max_length to account for suffix
    adjusted_length = max_length - len(suffix)
    if adjusted_length <= 0:
        return suffix[:max_length]
    
    return text[:adjusted_length] + suffix

def format_exception(exc: Exception) -> str:
    """
    Format an exception with its traceback for logging.
    
    Args:
        exc: The exception to format
    
    Returns:
        Formatted exception string
        
    Example:
        >>> try:
        ...     1/0
        ... except Exception as e:
        ...     error_details = format_exception(e)
        ...     logger.error(f"Operation failed: {error_details}")
    """
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    return "".join(tb_lines)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename: The filename to sanitize
    
    Returns:
        Sanitized filename
        
    Example:
        >>> sanitize_filename("User Input: File/With\\Invalid*Chars?.txt")
        'User_Input_File_With_Invalid_Chars.txt'
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Replace multiple spaces/underscores with a single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Ensure the filename is not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized

# Export commonly used functions and classes
__all__ = [
    'ValidationError',
    'RetryError',
    'ConfigurationError',
    'ResourceError',
    'setup_logging',
    'validate_input',
    'measure_execution_time',
    'retry_operation',
    'safe_serialize',
    'is_valid_uuid',
    'generate_hash',
    'get_caller_info',
    'ensure_directory',
    'truncate_string',
    'format_exception',
    'sanitize_filename',
]