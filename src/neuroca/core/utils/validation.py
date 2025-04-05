"""
Validation Utilities for NeuroCognitive Architecture (NCA)

This module provides comprehensive validation utilities for the NCA system,
ensuring data integrity, type safety, and proper formatting across the application.
It includes validators for primitive types, complex structures, and domain-specific
objects used throughout the NCA system.

Usage:
    from neuroca.core.utils.validation import (
        validate_string, validate_int, validate_float,
        validate_dict, validate_list, validate_memory_object,
        validate_uuid, validate_timestamp, validate_json,
        ValidationError
    )

    # Validate a string parameter
    username = validate_string(username, min_length=3, max_length=50, 
                              allow_empty=False, field_name="username")
    
    # Validate a dictionary with specific required keys
    config = validate_dict(config, required_keys=["api_key", "model_name"], 
                          field_name="configuration")
"""

import datetime
import json
import logging
import re
import uuid
from typing import Any, Callable, Optional, TypeVar, Union

# Setup logging
logger = logging.getLogger(__name__)

# Type variable for generic validation functions
T = TypeVar('T')


class ValidationError(Exception):
    """
    Exception raised for validation errors.
    
    Attributes:
        message -- explanation of the error
        field_name -- name of the field that failed validation
        value -- the invalid value (may be omitted for security/privacy)
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 value: Any = None, include_value: bool = False):
        self.field_name = field_name
        self.value = value if include_value else None
        
        # Format the message to include field name if provided
        if field_name:
            message = f"Validation error for '{field_name}': {message}"
            
        super().__init__(message)


def validate_type(value: Any, expected_type: Union[type, tuple[type, ...]], 
                 field_name: Optional[str] = None, 
                 allow_none: bool = False) -> Any:
    """
    Validates that a value is of the expected type.
    
    Args:
        value: The value to validate
        expected_type: The expected type or tuple of types
        field_name: Optional name of the field being validated (for error messages)
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(
            "Value cannot be None", field_name=field_name
        )
    
    if not isinstance(value, expected_type):
        type_names = (
            [t.__name__ for t in expected_type] 
            if isinstance(expected_type, tuple) 
            else [expected_type.__name__]
        )
        type_str = " or ".join(type_names)
        
        raise ValidationError(
            f"Expected {type_str}, got {type(value).__name__}",
            field_name=field_name,
            value=value
        )
    
    return value


def validate_string(value: Any, min_length: int = 0, max_length: Optional[int] = None,
                   allow_empty: bool = True, pattern: Optional[str] = None,
                   field_name: Optional[str] = None, allow_none: bool = False) -> Optional[str]:
    """
    Validates a string value.
    
    Args:
        value: The string to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length (None for no limit)
        allow_empty: Whether empty strings are allowed
        pattern: Optional regex pattern the string must match
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    value = validate_type(value, str, field_name=field_name)
    
    if not allow_empty and not value:
        raise ValidationError("String cannot be empty", field_name=field_name)
    
    if len(value) < min_length:
        raise ValidationError(
            f"String must be at least {min_length} characters long",
            field_name=field_name
        )
    
    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"String cannot exceed {max_length} characters",
            field_name=field_name
        )
    
    if pattern is not None and not re.match(pattern, value):
        raise ValidationError(
            "String does not match required pattern",
            field_name=field_name
        )
    
    return value


def validate_int(value: Any, min_value: Optional[int] = None, 
                max_value: Optional[int] = None, field_name: Optional[str] = None,
                allow_none: bool = False) -> Optional[int]:
    """
    Validates an integer value.
    
    Args:
        value: The integer to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated integer
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    # Try to convert string to int if needed
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            raise ValidationError(
                f"Could not convert string '{value}' to integer",
                field_name=field_name
            )
    
    value = validate_type(value, int, field_name=field_name)
    
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Value must be at least {min_value}",
            field_name=field_name,
            value=value
        )
    
    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Value cannot exceed {max_value}",
            field_name=field_name,
            value=value
        )
    
    return value


def validate_float(value: Any, min_value: Optional[float] = None,
                  max_value: Optional[float] = None, field_name: Optional[str] = None,
                  allow_none: bool = False) -> Optional[float]:
    """
    Validates a float value.
    
    Args:
        value: The float to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated float
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    # Try to convert string to float if needed
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            raise ValidationError(
                f"Could not convert string '{value}' to float",
                field_name=field_name
            )
    
    value = validate_type(value, (int, float), field_name=field_name)
    
    # Convert to float if it's an int
    if isinstance(value, int):
        value = float(value)
    
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Value must be at least {min_value}",
            field_name=field_name,
            value=value
        )
    
    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Value cannot exceed {max_value}",
            field_name=field_name,
            value=value
        )
    
    return value


def validate_bool(value: Any, field_name: Optional[str] = None,
                 allow_none: bool = False) -> Optional[bool]:
    """
    Validates a boolean value.
    
    Args:
        value: The boolean to validate
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated boolean
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    # Handle string representations of booleans
    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ('true', 't', 'yes', 'y', '1'):
            return True
        elif lower_value in ('false', 'f', 'no', 'n', '0'):
            return False
        else:
            raise ValidationError(
                f"String '{value}' cannot be converted to boolean",
                field_name=field_name
            )
    
    # Handle numeric values
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        elif value == 0:
            return False
        else:
            raise ValidationError(
                f"Numeric value {value} must be 0 or 1 to convert to boolean",
                field_name=field_name
            )
    
    # For actual boolean values
    return validate_type(value, bool, field_name=field_name)


def validate_list(value: Any, item_validator: Optional[Callable[[Any], Any]] = None,
                 min_length: int = 0, max_length: Optional[int] = None,
                 field_name: Optional[str] = None, allow_none: bool = False) -> Optional[list]:
    """
    Validates a list and optionally its items.
    
    Args:
        value: The list to validate
        item_validator: Optional function to validate each item
        min_length: Minimum allowed length
        max_length: Maximum allowed length (None for no limit)
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated list
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    value = validate_type(value, list, field_name=field_name)
    
    if len(value) < min_length:
        raise ValidationError(
            f"List must contain at least {min_length} items",
            field_name=field_name
        )
    
    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"List cannot contain more than {max_length} items",
            field_name=field_name
        )
    
    if item_validator:
        validated_items = []
        for i, item in enumerate(value):
            try:
                validated_item = item_validator(item)
                validated_items.append(validated_item)
            except ValidationError as e:
                # Enhance error message with item index
                item_field = f"{field_name}[{i}]" if field_name else f"item[{i}]"
                raise ValidationError(
                    f"Invalid item at index {i}: {str(e)}",
                    field_name=item_field
                )
        return validated_items
    
    return value


def validate_dict(value: Any, required_keys: Optional[list[str]] = None,
                 optional_keys: Optional[list[str]] = None,
                 value_validators: Optional[dict[str, Callable]] = None,
                 allow_extra_keys: bool = True, field_name: Optional[str] = None,
                 allow_none: bool = False) -> Optional[dict]:
    """
    Validates a dictionary, its keys, and optionally its values.
    
    Args:
        value: The dictionary to validate
        required_keys: List of keys that must be present
        optional_keys: List of keys that may be present
        value_validators: Dict mapping keys to validation functions for their values
        allow_extra_keys: Whether keys not in required_keys or optional_keys are allowed
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    value = validate_type(value, dict, field_name=field_name)
    
    # Check for required keys
    if required_keys:
        missing_keys = [key for key in required_keys if key not in value]
        if missing_keys:
            raise ValidationError(
                f"Missing required keys: {', '.join(missing_keys)}",
                field_name=field_name
            )
    
    # Check for unexpected keys
    if not allow_extra_keys and (required_keys or optional_keys):
        allowed_keys = set(required_keys or []) | set(optional_keys or [])
        extra_keys = [key for key in value if key not in allowed_keys]
        if extra_keys:
            raise ValidationError(
                f"Unexpected keys: {', '.join(extra_keys)}",
                field_name=field_name
            )
    
    # Validate values
    if value_validators:
        validated_dict = {}
        for key, validator in value_validators.items():
            if key in value:
                try:
                    validated_dict[key] = validator(value[key])
                except ValidationError as e:
                    # Enhance error message with key
                    key_field = f"{field_name}.{key}" if field_name else key
                    raise ValidationError(
                        f"Invalid value for key '{key}': {str(e)}",
                        field_name=key_field
                    )
            elif key in (required_keys or []):
                # This should be caught by the required_keys check above,
                # but we include it here for completeness
                raise ValidationError(
                    f"Missing required key: {key}",
                    field_name=field_name
                )
        
        # Copy over any keys that don't have validators
        for key, val in value.items():
            if key not in validated_dict:
                validated_dict[key] = val
                
        return validated_dict
    
    return value


def validate_uuid(value: Any, field_name: Optional[str] = None,
                 allow_none: bool = False) -> Optional[uuid.UUID]:
    """
    Validates a UUID value.
    
    Args:
        value: The UUID to validate (can be string or UUID object)
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated UUID object
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    if isinstance(value, uuid.UUID):
        return value
    
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValidationError(
                f"Invalid UUID format: '{value}'",
                field_name=field_name
            )
    
    raise ValidationError(
        f"Expected UUID or string, got {type(value).__name__}",
        field_name=field_name
    )


def validate_timestamp(value: Any, min_time: Optional[datetime.datetime] = None,
                      max_time: Optional[datetime.datetime] = None,
                      field_name: Optional[str] = None,
                      allow_none: bool = False) -> Optional[datetime.datetime]:
    """
    Validates a timestamp value.
    
    Args:
        value: The timestamp to validate (datetime object, ISO string, or timestamp)
        min_time: Minimum allowed time
        max_time: Maximum allowed time
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated datetime object
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    # Convert to datetime if needed
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try parsing with different formats
                value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                try:
                    value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValidationError(
                        f"Invalid timestamp format: '{value}'",
                        field_name=field_name
                    )
    elif isinstance(value, (int, float)):
        try:
            value = datetime.datetime.fromtimestamp(value)
        except (ValueError, OverflowError):
            raise ValidationError(
                f"Invalid timestamp value: {value}",
                field_name=field_name
            )
    
    if not isinstance(value, datetime.datetime):
        raise ValidationError(
            f"Expected datetime, got {type(value).__name__}",
            field_name=field_name
        )
    
    if min_time is not None and value < min_time:
        raise ValidationError(
            f"Timestamp must be after {min_time.isoformat()}",
            field_name=field_name
        )
    
    if max_time is not None and value > max_time:
        raise ValidationError(
            f"Timestamp must be before {max_time.isoformat()}",
            field_name=field_name
        )
    
    return value


def validate_json(value: Any, schema: Optional[dict] = None,
                 field_name: Optional[str] = None,
                 allow_none: bool = False) -> Any:
    """
    Validates a JSON value or string.
    
    Args:
        value: The JSON to validate (string or parsed object)
        schema: Optional JSON schema to validate against (requires jsonschema package)
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The parsed JSON object
        
    Raises:
        ValidationError: If validation fails
        ImportError: If schema validation is requested but jsonschema is not installed
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    # Parse JSON string if needed
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON: {str(e)}",
                field_name=field_name
            )
    
    # Validate against schema if provided
    if schema:
        try:
            import jsonschema
        except ImportError:
            logger.warning("jsonschema package not installed, skipping schema validation")
            if schema:
                raise ImportError(
                    "jsonschema package is required for schema validation"
                )
        
        try:
            jsonschema.validate(instance=value, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(
                f"JSON schema validation failed: {str(e)}",
                field_name=field_name
            )
    
    return value


def validate_email(value: Any, field_name: Optional[str] = None,
                  allow_none: bool = False) -> Optional[str]:
    """
    Validates an email address.
    
    Args:
        value: The email to validate
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated email string
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    value = validate_string(value, field_name=field_name)
    
    # Basic email validation pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValidationError(
            f"Invalid email format: '{value}'",
            field_name=field_name
        )
    
    return value


def validate_url(value: Any, allowed_schemes: Optional[list[str]] = None,
                field_name: Optional[str] = None, allow_none: bool = False) -> Optional[str]:
    """
    Validates a URL.
    
    Args:
        value: The URL to validate
        allowed_schemes: List of allowed URL schemes (e.g., ['http', 'https'])
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated URL string
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    value = validate_string(value, field_name=field_name)
    
    # Basic URL validation pattern
    url_pattern = r'^(?:(?:(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*)://)?(?:(?P<user>[^:@]+)(?::(?P<password>[^@]*))?@)?(?P<host>[^:/]+)(?::(?P<port>\d+))?)?(?P<path>/[^?#]*)?(?:\?(?P<query>[^#]*))?(?:#(?P<fragment>.*))?$'
    match = re.match(url_pattern, value)
    
    if not match:
        raise ValidationError(
            f"Invalid URL format: '{value}'",
            field_name=field_name
        )
    
    scheme = match.group('scheme')
    if allowed_schemes and scheme and scheme.lower() not in [s.lower() for s in allowed_schemes]:
        raise ValidationError(
            f"URL scheme '{scheme}' not allowed. Allowed schemes: {', '.join(allowed_schemes)}",
            field_name=field_name
        )
    
    return value


def validate_memory_object(value: Any, required_attributes: Optional[list[str]] = None,
                          field_name: Optional[str] = None,
                          allow_none: bool = False) -> Any:
    """
    Validates a memory object for the NCA system.
    
    Args:
        value: The memory object to validate
        required_attributes: List of attributes that must be present
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated memory object
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Memory object cannot be None", field_name=field_name)
    
    # Check for required attributes
    if required_attributes:
        missing_attrs = [attr for attr in required_attributes if not hasattr(value, attr)]
        if missing_attrs:
            raise ValidationError(
                f"Memory object missing required attributes: {', '.join(missing_attrs)}",
                field_name=field_name
            )
    
    # Additional memory-specific validations could be added here
    
    return value


def validate_enum(value: Any, enum_values: list[Any], case_sensitive: bool = True,
                 field_name: Optional[str] = None, allow_none: bool = False) -> Any:
    """
    Validates that a value is one of a set of allowed values.
    
    Args:
        value: The value to validate
        enum_values: List of allowed values
        case_sensitive: Whether string comparison should be case-sensitive
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    # For case-insensitive string comparison
    if not case_sensitive and isinstance(value, str):
        if not any(
            isinstance(ev, str) and ev.lower() == value.lower() 
            for ev in enum_values
        ):
            raise ValidationError(
                f"Value '{value}' not in allowed values: {', '.join(str(v) for v in enum_values)}",
                field_name=field_name
            )
        # Return the canonical version from enum_values
        for ev in enum_values:
            if isinstance(ev, str) and ev.lower() == value.lower():
                return ev
    else:
        if value not in enum_values:
            raise ValidationError(
                f"Value '{value}' not in allowed values: {', '.join(str(v) for v in enum_values)}",
                field_name=field_name
            )
    
    return value


def validate_range(value: Any, min_value: Optional[Any] = None, max_value: Optional[Any] = None,
                  inclusive_min: bool = True, inclusive_max: bool = True,
                  field_name: Optional[str] = None, allow_none: bool = False) -> Any:
    """
    Validates that a value is within a specified range.
    
    Args:
        value: The value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        inclusive_min: Whether the minimum value is inclusive
        inclusive_max: Whether the maximum value is inclusive
        field_name: Optional name of the field being validated
        allow_none: Whether None is an acceptable value
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError("Value cannot be None", field_name=field_name)
    
    if min_value is not None:
        if (inclusive_min and value < min_value) or (not inclusive_min and value <= min_value):
            operator = ">=" if inclusive_min else ">"
            raise ValidationError(
                f"Value must be {operator} {min_value}",
                field_name=field_name,
                value=value
            )
    
    if max_value is not None:
        if (inclusive_max and value > max_value) or (not inclusive_max and value >= max_value):
            operator = "<=" if inclusive_max else "<"
            raise ValidationError(
                f"Value must be {operator} {max_value}",
                field_name=field_name,
                value=value
            )
    
    return value


# Convenience function for validating configuration objects
def validate_config(config: dict, schema: dict, field_name: str = "config") -> dict:
    """
    Validates a configuration dictionary against a schema.
    
    Args:
        config: The configuration dictionary to validate
        schema: Schema defining the expected structure and types
        field_name: Name of the configuration field
        
    Returns:
        The validated configuration dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(config, dict):
        raise ValidationError(
            f"Configuration must be a dictionary, got {type(config).__name__}",
            field_name=field_name
        )
    
    validated_config = {}
    
    for key, spec in schema.items():
        # Extract validation parameters from spec
        required = spec.get('required', True)
        validator = spec.get('validator')
        default = spec.get('default')
        
        if key in config:
            value = config[key]
            if validator:
                try:
                    validated_config[key] = validator(value)
                except ValidationError as e:
                    # Enhance error message with key
                    key_field = f"{field_name}.{key}" if field_name else key
                    raise ValidationError(
                        f"Invalid value for '{key}': {str(e)}",
                        field_name=key_field
                    )
            else:
                validated_config[key] = value
        elif required:
            if default is not None:
                validated_config[key] = default
            else:
                raise ValidationError(
                    f"Missing required configuration key: {key}",
                    field_name=field_name
                )
        elif default is not None:
            validated_config[key] = default
    
    # Copy any extra keys not in schema
    for key, value in config.items():
        if key not in schema:
            validated_config[key] = value
    
    return validated_config