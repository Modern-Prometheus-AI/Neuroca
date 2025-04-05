"""
Validation utilities for the NeuroCognitive Architecture CLI.

This module provides a comprehensive set of validation functions for checking
and validating various types of inputs used throughout the CLI components.
These utilities help ensure data integrity, prevent errors, and provide
meaningful feedback to users when validation fails.

Usage examples:
    >>> from neuroca.cli.utils.validation import validate_memory_id
    >>> try:
    ...     validate_memory_id("mem_12345")
    ...     print("Memory ID is valid")
    ... except ValidationError as e:
    ...     print(f"Invalid memory ID: {e}")

    >>> from neuroca.cli.utils.validation import validate_config_file
    >>> if validate_config_file("/path/to/config.yaml"):
    ...     print("Config file is valid")
"""

import ipaddress
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID

import yaml

# Setup module logger
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for validation errors in the CLI utilities."""
    pass


def validate_memory_id(memory_id: str) -> bool:
    """
    Validate a memory ID format.
    
    Memory IDs should follow the format: mem_[alphanumeric string]
    
    Args:
        memory_id: The memory ID string to validate
        
    Returns:
        bool: True if the memory ID is valid
        
    Raises:
        ValidationError: If the memory ID format is invalid
    """
    if not memory_id:
        raise ValidationError("Memory ID cannot be empty")
    
    pattern = r'^mem_[a-zA-Z0-9]{6,32}$'
    if not re.match(pattern, memory_id):
        raise ValidationError(
            f"Invalid memory ID format: {memory_id}. "
            f"Expected format: mem_[alphanumeric string of 6-32 characters]"
        )
    
    logger.debug(f"Memory ID validated successfully: {memory_id}")
    return True


def validate_config_file(file_path: Union[str, Path]) -> bool:
    """
    Validate that a configuration file exists and has valid YAML or JSON format.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        bool: True if the file exists and has valid format
        
    Raises:
        ValidationError: If the file doesn't exist or has invalid format
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    
    # Check if file exists
    if not path.exists():
        raise ValidationError(f"Configuration file not found: {path}")
    
    # Check if it's a file
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {path}")
    
    # Check file extension and content
    extension = path.suffix.lower()
    try:
        if extension == '.yaml' or extension == '.yml':
            with open(path) as f:
                yaml.safe_load(f)
        elif extension == '.json':
            with open(path) as f:
                json.load(f)
        else:
            raise ValidationError(f"Unsupported configuration file format: {extension}")
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML format in {path}: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format in {path}: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error reading configuration file {path}: {str(e)}")
    
    logger.debug(f"Configuration file validated successfully: {path}")
    return True


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate that a string is a valid UUID.
    
    Args:
        uuid_str: The UUID string to validate
        
    Returns:
        bool: True if the UUID is valid
        
    Raises:
        ValidationError: If the UUID format is invalid
    """
    if not uuid_str:
        raise ValidationError("UUID cannot be empty")
    
    try:
        UUID(uuid_str)
        logger.debug(f"UUID validated successfully: {uuid_str}")
        return True
    except ValueError:
        raise ValidationError(f"Invalid UUID format: {uuid_str}")


def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validate that a string matches the specified date format.
    
    Args:
        date_str: The date string to validate
        format_str: The expected date format (default: YYYY-MM-DD)
        
    Returns:
        bool: True if the date format is valid
        
    Raises:
        ValidationError: If the date format is invalid
    """
    if not date_str:
        raise ValidationError("Date string cannot be empty")
    
    try:
        datetime.strptime(date_str, format_str)
        logger.debug(f"Date format validated successfully: {date_str}")
        return True
    except ValueError:
        raise ValidationError(
            f"Invalid date format: {date_str}. Expected format: {format_str}"
        )


def validate_ip_address(ip_str: str) -> bool:
    """
    Validate that a string is a valid IP address (IPv4 or IPv6).
    
    Args:
        ip_str: The IP address string to validate
        
    Returns:
        bool: True if the IP address is valid
        
    Raises:
        ValidationError: If the IP address format is invalid
    """
    if not ip_str:
        raise ValidationError("IP address cannot be empty")
    
    try:
        ipaddress.ip_address(ip_str)
        logger.debug(f"IP address validated successfully: {ip_str}")
        return True
    except ValueError:
        raise ValidationError(f"Invalid IP address format: {ip_str}")


def validate_port_number(port: Union[str, int]) -> bool:
    """
    Validate that a value is a valid port number (1-65535).
    
    Args:
        port: The port number to validate (string or integer)
        
    Returns:
        bool: True if the port number is valid
        
    Raises:
        ValidationError: If the port number is invalid
    """
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValidationError(
                f"Port number out of range: {port}. Must be between 1 and 65535."
            )
        logger.debug(f"Port number validated successfully: {port}")
        return True
    except ValueError:
        raise ValidationError(f"Invalid port number format: {port}. Must be an integer.")


def validate_directory_path(dir_path: Union[str, Path], must_exist: bool = True, 
                           writable: bool = False) -> bool:
    """
    Validate a directory path.
    
    Args:
        dir_path: The directory path to validate
        must_exist: Whether the directory must already exist
        writable: Whether the directory must be writable
        
    Returns:
        bool: True if the directory path is valid
        
    Raises:
        ValidationError: If the directory path is invalid
    """
    path = Path(dir_path) if isinstance(dir_path, str) else dir_path
    
    if must_exist:
        if not path.exists():
            raise ValidationError(f"Directory does not exist: {path}")
        if not path.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")
    
    if writable and path.exists() and not os.access(path, os.W_OK):
        raise ValidationError(f"Directory is not writable: {path}")
    
    logger.debug(f"Directory path validated successfully: {path}")
    return True


def validate_file_path(file_path: Union[str, Path], must_exist: bool = True,
                      readable: bool = True) -> bool:
    """
    Validate a file path.
    
    Args:
        file_path: The file path to validate
        must_exist: Whether the file must already exist
        readable: Whether the file must be readable
        
    Returns:
        bool: True if the file path is valid
        
    Raises:
        ValidationError: If the file path is invalid
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    
    if must_exist:
        if not path.exists():
            raise ValidationError(f"File does not exist: {path}")
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {path}")
    
    if readable and path.exists() and not os.access(path, os.R_OK):
        raise ValidationError(f"File is not readable: {path}")
    
    logger.debug(f"File path validated successfully: {path}")
    return True


def validate_url(url: str) -> bool:
    """
    Validate that a string is a valid URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        bool: True if the URL is valid
        
    Raises:
        ValidationError: If the URL format is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")
    
    # Basic URL pattern
    pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        raise ValidationError(f"Invalid URL format: {url}")
    
    logger.debug(f"URL validated successfully: {url}")
    return True


def validate_email(email: str) -> bool:
    """
    Validate that a string is a valid email address.
    
    Args:
        email: The email string to validate
        
    Returns:
        bool: True if the email is valid
        
    Raises:
        ValidationError: If the email format is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")
    
    # Email pattern based on RFC 5322
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    logger.debug(f"Email validated successfully: {email}")
    return True


def validate_numeric_range(value: Union[int, float], min_val: Optional[Union[int, float]] = None, 
                          max_val: Optional[Union[int, float]] = None) -> bool:
    """
    Validate that a numeric value is within a specified range.
    
    Args:
        value: The numeric value to validate
        min_val: The minimum allowed value (inclusive)
        max_val: The maximum allowed value (inclusive)
        
    Returns:
        bool: True if the value is within range
        
    Raises:
        ValidationError: If the value is outside the specified range
    """
    if min_val is not None and value < min_val:
        raise ValidationError(f"Value {value} is below minimum allowed value {min_val}")
    
    if max_val is not None and value > max_val:
        raise ValidationError(f"Value {value} is above maximum allowed value {max_val}")
    
    logger.debug(f"Numeric value {value} validated successfully within range")
    return True


def validate_string_length(string: str, min_length: Optional[int] = None, 
                          max_length: Optional[int] = None) -> bool:
    """
    Validate that a string's length is within a specified range.
    
    Args:
        string: The string to validate
        min_length: The minimum allowed length (inclusive)
        max_length: The maximum allowed length (inclusive)
        
    Returns:
        bool: True if the string length is within range
        
    Raises:
        ValidationError: If the string length is outside the specified range
    """
    if string is None:
        raise ValidationError("String cannot be None")
    
    length = len(string)
    
    if min_length is not None and length < min_length:
        raise ValidationError(
            f"String length ({length}) is below minimum allowed length ({min_length})"
        )
    
    if max_length is not None and length > max_length:
        raise ValidationError(
            f"String length ({length}) is above maximum allowed length ({max_length})"
        )
    
    logger.debug(f"String length ({length}) validated successfully within range")
    return True


def validate_required_keys(data: dict[str, Any], required_keys: list[str]) -> bool:
    """
    Validate that a dictionary contains all required keys.
    
    Args:
        data: The dictionary to validate
        required_keys: List of keys that must be present
        
    Returns:
        bool: True if all required keys are present
        
    Raises:
        ValidationError: If any required keys are missing
    """
    if not data:
        raise ValidationError("Data dictionary cannot be empty")
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        raise ValidationError(f"Missing required keys: {', '.join(missing_keys)}")
    
    logger.debug("All required keys present in data dictionary")
    return True


def validate_enum_value(value: Any, valid_values: set[Any]) -> bool:
    """
    Validate that a value is one of a set of valid values.
    
    Args:
        value: The value to validate
        valid_values: Set of allowed values
        
    Returns:
        bool: True if the value is valid
        
    Raises:
        ValidationError: If the value is not in the set of valid values
    """
    if value not in valid_values:
        raise ValidationError(
            f"Invalid value: {value}. Must be one of: {', '.join(str(v) for v in valid_values)}"
        )
    
    logger.debug(f"Value {value} validated successfully against enum")
    return True


def validate_json_string(json_str: str) -> dict[str, Any]:
    """
    Validate that a string is valid JSON and return the parsed object.
    
    Args:
        json_str: The JSON string to validate
        
    Returns:
        Dict[str, Any]: The parsed JSON object
        
    Raises:
        ValidationError: If the string is not valid JSON
    """
    if not json_str:
        raise ValidationError("JSON string cannot be empty")
    
    try:
        parsed = json.loads(json_str)
        logger.debug("JSON string validated successfully")
        return parsed
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")


def validate_yaml_string(yaml_str: str) -> dict[str, Any]:
    """
    Validate that a string is valid YAML and return the parsed object.
    
    Args:
        yaml_str: The YAML string to validate
        
    Returns:
        Dict[str, Any]: The parsed YAML object
        
    Raises:
        ValidationError: If the string is not valid YAML
    """
    if not yaml_str:
        raise ValidationError("YAML string cannot be empty")
    
    try:
        parsed = yaml.safe_load(yaml_str)
        logger.debug("YAML string validated successfully")
        return parsed
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML format: {str(e)}")