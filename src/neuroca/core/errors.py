"""
Error handling module for the NeuroCognitive Architecture (NCA) system.

This module defines a comprehensive error handling system for the NCA, including:
- Base exception classes
- Domain-specific exceptions
- Error codes and categories
- Error formatting utilities
- Error logging helpers

The error system is designed to provide:
1. Consistent error reporting across the application
2. Structured error information for both humans and programmatic handling
3. Clear categorization of errors by domain and severity
4. Integration with the logging system
5. Support for internationalization of error messages

Usage:
    from neuroca.core.errors import (
        NCAError, MemoryError, ConfigurationError, 
        ErrorCode, log_error, format_error_context
    )

    try:
        # Some operation
        if not valid_condition:
            raise ConfigurationError(
                ErrorCode.INVALID_CONFIGURATION,
                "Invalid memory configuration",
                context={"param": value}
            )
    except NCAError as e:
        log_error(e)
        # Handle the error appropriately
"""

import enum
import logging
import traceback
import typing
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Union

# Configure module logger
logger = logging.getLogger(__name__)


class ErrorCategory(enum.Enum):
    """Categories of errors in the NCA system."""
    
    # System-level errors
    SYSTEM = "system"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    
    # Core functionality errors
    MEMORY = "memory"
    COGNITION = "cognition"
    INTEGRATION = "integration"
    
    # Data-related errors
    DATA = "data"
    VALIDATION = "validation"
    PERSISTENCE = "persistence"
    
    # External interaction errors
    API = "api"
    EXTERNAL = "external"
    
    # Security-related errors
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    
    # Operational errors
    OPERATIONAL = "operational"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    
    # Unknown/unclassified errors
    UNKNOWN = "unknown"


class ErrorSeverity(enum.Enum):
    """Severity levels for errors in the NCA system."""
    
    # Fatal errors that require immediate attention and stop execution
    CRITICAL = "critical"
    
    # Serious errors that might allow partial functionality
    ERROR = "error"
    
    # Issues that should be addressed but don't prevent core functionality
    WARNING = "warning"
    
    # Minor issues or edge cases that are handled but worth noting
    INFO = "info"
    
    # Debugging information about potential issues
    DEBUG = "debug"


class ErrorCode(enum.Enum):
    """Specific error codes for the NCA system.
    
    Format: CATEGORY_SPECIFIC_ERROR
    
    Each error code is associated with a default message and severity level.
    """
    
    # System errors (1000-1999)
    SYSTEM_INITIALIZATION_FAILED = (1000, "System initialization failed", ErrorSeverity.CRITICAL)
    SYSTEM_SHUTDOWN_ERROR = (1001, "Error during system shutdown", ErrorSeverity.ERROR)
    SYSTEM_RESOURCE_EXHAUSTED = (1002, "System resources exhausted", ErrorSeverity.CRITICAL)
    
    # Configuration errors (2000-2999)
    INVALID_CONFIGURATION = (2000, "Invalid configuration", ErrorSeverity.ERROR)
    MISSING_CONFIGURATION = (2001, "Missing required configuration", ErrorSeverity.ERROR)
    CONFIGURATION_LOAD_ERROR = (2002, "Failed to load configuration", ErrorSeverity.ERROR)
    
    # Memory errors (3000-3999)
    MEMORY_ACCESS_ERROR = (3000, "Memory access error", ErrorSeverity.ERROR)
    MEMORY_CORRUPTION = (3001, "Memory corruption detected", ErrorSeverity.CRITICAL)
    MEMORY_CAPACITY_EXCEEDED = (3002, "Memory capacity exceeded", ErrorSeverity.ERROR)
    MEMORY_RETRIEVAL_FAILED = (3003, "Failed to retrieve from memory", ErrorSeverity.ERROR)
    MEMORY_STORAGE_FAILED = (3004, "Failed to store in memory", ErrorSeverity.ERROR)
    MEMORY_TIER_UNAVAILABLE = (3005, "Memory tier unavailable", ErrorSeverity.ERROR)
    
    # Cognition errors (4000-4999)
    COGNITION_PROCESS_FAILED = (4000, "Cognition process failed", ErrorSeverity.ERROR)
    COGNITION_TIMEOUT = (4001, "Cognition process timed out", ErrorSeverity.WARNING)
    COGNITION_RESOURCE_LIMIT = (4002, "Cognition resource limit reached", ErrorSeverity.WARNING)
    
    # Integration errors (5000-5999)
    LLM_CONNECTION_ERROR = (5000, "Failed to connect to LLM", ErrorSeverity.ERROR)
    LLM_RESPONSE_ERROR = (5001, "Invalid response from LLM", ErrorSeverity.ERROR)
    LLM_TIMEOUT = (5002, "LLM request timed out", ErrorSeverity.WARNING)
    LLM_RATE_LIMIT = (5003, "LLM rate limit exceeded", ErrorSeverity.WARNING)
    INTEGRATION_CONFIGURATION_ERROR = (5004, "Integration configuration error", ErrorSeverity.ERROR)
    
    # Data errors (6000-6999)
    DATA_VALIDATION_ERROR = (6000, "Data validation error", ErrorSeverity.ERROR)
    DATA_INTEGRITY_ERROR = (6001, "Data integrity error", ErrorSeverity.ERROR)
    DATA_FORMAT_ERROR = (6002, "Data format error", ErrorSeverity.ERROR)
    
    # Persistence errors (7000-7999)
    DATABASE_CONNECTION_ERROR = (7000, "Database connection error", ErrorSeverity.ERROR)
    DATABASE_QUERY_ERROR = (7001, "Database query error", ErrorSeverity.ERROR)
    DATABASE_INTEGRITY_ERROR = (7002, "Database integrity error", ErrorSeverity.ERROR)
    
    # API errors (8000-8999)
    API_REQUEST_ERROR = (8000, "API request error", ErrorSeverity.ERROR)
    API_RESPONSE_ERROR = (8001, "API response error", ErrorSeverity.ERROR)
    API_AUTHENTICATION_ERROR = (8002, "API authentication error", ErrorSeverity.ERROR)
    API_AUTHORIZATION_ERROR = (8003, "API authorization error", ErrorSeverity.ERROR)
    API_RATE_LIMIT = (8004, "API rate limit exceeded", ErrorSeverity.WARNING)
    
    # Security errors (9000-9999)
    SECURITY_VIOLATION = (9000, "Security violation", ErrorSeverity.CRITICAL)
    AUTHENTICATION_FAILED = (9001, "Authentication failed", ErrorSeverity.ERROR)
    AUTHORIZATION_FAILED = (9002, "Authorization failed", ErrorSeverity.ERROR)
    
    def __init__(self, code: int, default_message: str, severity: ErrorSeverity):
        self.code = code
        self.default_message = default_message
        self.severity = severity


@dataclass
class ErrorContext:
    """Contextual information about an error occurrence."""
    
    # When the error occurred
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Where the error occurred (file, function, line)
    file: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    
    # Additional context data relevant to the error
    data: dict[str, Any] = field(default_factory=dict)
    
    # Stack trace if available
    stack_trace: Optional[list[str]] = None


class NCAError(Exception):
    """Base exception class for all NCA-specific errors.
    
    This class provides a structured way to represent errors in the NCA system,
    including error codes, categories, severity levels, and contextual information.
    """
    
    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        cause: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None
    ):
        """Initialize a new NCA error.
        
        Args:
            code: The specific error code
            message: A human-readable error message (defaults to code's default message)
            cause: The underlying exception that caused this error, if any
            context: Additional contextual data about the error
        """
        self.code = code
        self.message = message or code.default_message
        self.cause = cause
        
        # Create error context with stack information
        frame = traceback.extract_stack()[-2]  # Get caller's frame
        self.context = ErrorContext(
            file=frame.filename,
            function=frame.name,
            line=frame.lineno,
            data=context or {},
            stack_trace=traceback.format_stack()[:-1]  # Exclude this frame
        )
        
        # Construct the full error message
        full_message = f"[{self.code.name}] {self.message}"
        super().__init__(full_message)
    
    @property
    def severity(self) -> ErrorSeverity:
        """Get the severity level of this error."""
        return self.code.severity
    
    @property
    def category(self) -> ErrorCategory:
        """Derive the error category from the error code name."""
        # Extract category from the error code name (e.g., MEMORY_ACCESS_ERROR -> MEMORY)
        try:
            category_name = self.code.name.split('_')[0]
            return ErrorCategory[category_name]
        except (IndexError, KeyError):
            return ErrorCategory.UNKNOWN
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the error to a dictionary representation.
        
        Returns:
            A dictionary containing all error information.
        """
        return {
            "code": {
                "name": self.code.name,
                "value": self.code.code,
            },
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": {
                "timestamp": self.context.timestamp.isoformat(),
                "location": {
                    "file": self.context.file,
                    "function": self.context.function,
                    "line": self.context.line,
                },
                "data": self.context.data,
            },
            "cause": str(self.cause) if self.cause else None,
        }


# Domain-specific exception classes

class NCASystemError(NCAError): # Renamed from SystemError
    """Errors related to system operations and initialization."""
    pass


class ConfigurationError(NCAError):
    """Errors related to system configuration."""
    pass


class NCAMemoryError(NCAError): # Renamed from MemoryError
    """Errors related to the memory subsystem."""
    pass


class CognitionError(NCAError):
    """Errors related to cognitive processes."""
    pass


class IntegrationError(NCAError):
    """Errors related to LLM and external system integration."""
    pass


class DataError(NCAError):
    """Errors related to data handling and validation."""
    pass


class PersistenceError(NCAError):
    """Errors related to data persistence and storage."""
    pass


class APIError(NCAError):
    """Errors related to API operations."""
    pass


class SecurityError(NCAError):
    """Errors related to security, authentication, and authorization."""
    pass


# Error handling utilities

def log_error(
    error: Union[NCAError, Exception],
    logger_instance: Optional[logging.Logger] = None,
    include_traceback: bool = True,
    additional_context: Optional[dict[str, Any]] = None
) -> None:
    """Log an error with appropriate severity and context.
    
    Args:
        error: The error to log
        logger_instance: The logger to use (defaults to module logger)
        include_traceback: Whether to include the traceback in the log
        additional_context: Additional context to include in the log
    """
    log = logger_instance or logger
    
    if isinstance(error, NCAError):
        # Map severity to log level
        level_map = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.DEBUG: logging.DEBUG,
        }
        level = level_map.get(error.severity, logging.ERROR)
        
        # Format error context
        context_str = format_error_context(error, additional_context)
        
        # Log with appropriate level
        log.log(level, f"{error}\n{context_str}")
        
        # Log cause if present
        if error.cause and include_traceback:
            log.log(level, f"Caused by: {error.cause}", exc_info=error.cause)
    else:
        # For standard exceptions, log as error with traceback
        log.error(f"Unexpected error: {error}", exc_info=include_traceback)  # noqa: BLE001


def format_error_context(
    error: NCAError,
    additional_context: Optional[dict[str, Any]] = None
) -> str:
    """Format error context information for logging or display.
    
    Args:
        error: The NCA error with context
        additional_context: Additional context to include
    
    Returns:
        A formatted string with error context information
    """
    ctx = error.context
    
    # Combine error context data with additional context
    context_data = ctx.data.copy()
    if additional_context:
        context_data.update(additional_context)
    
    # Format the context data
    data_str = "\n".join(f"  {k}: {v}" for k, v in context_data.items())
    
    return (
        f"Error Context:\n"
        f"  Time: {ctx.timestamp.isoformat()}\n"
        f"  Location: {ctx.file}:{ctx.line} in {ctx.function}\n"
        f"  Category: {error.category.value}\n"
        f"  Severity: {error.severity.value}\n"
        f"  Code: {error.code.name} ({error.code.code})\n"
        f"Context Data:\n{data_str if data_str else '  None'}"
    )


def handle_exceptions(
    error_map: dict[type[Exception], ErrorCode],
    default_code: ErrorCode = ErrorCode.SYSTEM_INITIALIZATION_FAILED,
    logger_instance: Optional[logging.Logger] = None,
    reraise: bool = True
) -> typing.Callable:
    """Decorator for consistent exception handling.
    
    Args:
        error_map: Mapping from exception types to error codes
        default_code: Default error code for unmapped exceptions
        logger_instance: Logger to use for error logging
        reraise: Whether to reraise the wrapped exception as an NCAError
    
    Returns:
        A decorator function
    
    Example:
        @handle_exceptions({
            ValueError: ErrorCode.DATA_VALIDATION_ERROR,
            IOError: ErrorCode.SYSTEM_RESOURCE_EXHAUSTED
        })
        def process_data(data):
            # Function implementation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:  # noqa: BLE001 - Intentionally catching Exception in decorator
                # Find the most specific matching exception type
                matched_code = None
                for exc_type, code in error_map.items():
                    if isinstance(e, exc_type):
                        matched_code = code
                        break
                
                # Use default code if no match found
                error_code = matched_code or default_code
                
                # Create NCA error
                nca_error = NCAError(
                    code=error_code,
                    message=str(e),
                    cause=e,
                    context={"args": args, "kwargs": {k: v for k, v in kwargs.items() if not k.startswith("_")}}
                )
                
                # Log the error
                log_error(nca_error, logger_instance)
                
                # Reraise as NCA error if requested
                if reraise:
                    raise nca_error from e
                
                # Otherwise, return None or other default value
                return None
        
        return wrapper
    
    return decorator
