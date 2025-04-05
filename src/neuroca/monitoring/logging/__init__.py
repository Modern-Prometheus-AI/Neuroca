"""
NeuroCognitive Architecture (NCA) Logging Module
================================================

This module provides a comprehensive logging system for the NeuroCognitive Architecture.
It offers structured logging with configurable levels, formats, and outputs to support
both development and production environments.

Features:
- Hierarchical loggers that respect the project's module structure
- Configurable logging levels per module
- JSON formatting for machine-readable logs in production
- Console output with color-coding for development
- Integration with monitoring systems
- Context-aware logging with correlation IDs
- Performance metrics for logging operations
- Secure handling of sensitive information

Usage Examples:
--------------
Basic usage:
    from neuroca.monitoring.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("Processing started")
    logger.error("Error occurred", extra={"context": {"user_id": "123"}})

With context manager:
    from neuroca.monitoring.logging import LogContext
    
    with LogContext(operation="data_processing", correlation_id="abc-123"):
        logger.info("Processing with context")

Configuration:
    from neuroca.monitoring.logging import configure_logging
    
    configure_logging(
        level="INFO",
        format="json",
        output=["console", "file"],
        file_path="/var/log/neuroca.log"
    )
"""

import datetime
import inspect
import json
import logging
import logging.config
import logging.handlers
import os
import platform
import sys
import threading
from enum import Enum
from functools import wraps
from typing import Any, Optional, Union

# Constants
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "standard"
DEFAULT_LOG_OUTPUT = ["console"]
LOG_RECORD_BUILT_IN_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module",
    "msecs", "message", "msg", "name", "pathname", "process",
    "processName", "relativeCreated", "stack_info", "thread", "threadName"
}

# Global context storage (thread-local)
_context_store = threading.local()


class LogLevel(str, Enum):
    """Enum representing available logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Enum representing available log formats."""
    STANDARD = "standard"
    JSON = "json"
    DETAILED = "detailed"


class LogOutput(str, Enum):
    """Enum representing available log outputs."""
    CONSOLE = "console"
    FILE = "file"
    SYSLOG = "syslog"


class SensitiveDataFilter(logging.Filter):
    """
    Filter that redacts sensitive information from logs.
    
    This filter identifies and masks sensitive data patterns like passwords,
    tokens, and personal information to prevent security issues.
    """
    
    # Patterns to identify sensitive data (keys in dictionaries)
    SENSITIVE_PATTERNS = [
        "password", "secret", "token", "key", "auth", "credential",
        "ssn", "social_security", "credit_card", "card_number"
    ]
    
    def __init__(self, name: str = ""):
        super().__init__(name)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to redact sensitive information.
        
        Args:
            record: The log record to process
            
        Returns:
            bool: Always True (to keep the record), but modifies the record
        """
        if isinstance(record.args, dict):
            record.args = self._redact_sensitive_data(record.args)
        
        # Handle extra fields
        if hasattr(record, "__dict__"):
            for key, value in list(record.__dict__.items()):
                if key not in LOG_RECORD_BUILT_IN_ATTRS:
                    if isinstance(value, dict):
                        record.__dict__[key] = self._redact_sensitive_data(value)
                    elif isinstance(value, str) and self._is_sensitive_key(key):
                        record.__dict__[key] = "********"
        
        return True
    
    def _redact_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively redact sensitive data in dictionaries.
        
        Args:
            data: Dictionary that may contain sensitive information
            
        Returns:
            Dict: Dictionary with sensitive information redacted
        """
        result = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                result[key] = "********"
            elif isinstance(value, dict):
                result[key] = self._redact_sensitive_data(value)
            else:
                result[key] = value
        return result
    
    def _is_sensitive_key(self, key: str) -> bool:
        """
        Check if a key might contain sensitive information.
        
        Args:
            key: The key to check
            
        Returns:
            bool: True if the key matches sensitive patterns
        """
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in self.SENSITIVE_PATTERNS)


class ContextualLogRecord(logging.LogRecord):
    """
    Extended LogRecord that includes contextual information.
    
    This class enhances standard log records with additional context
    from the current thread's context store.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add context from thread-local storage
        self._add_context_data()
    
    def _add_context_data(self):
        """Add contextual data from thread-local storage to the log record."""
        if hasattr(_context_store, "context"):
            for key, value in _context_store.context.items():
                setattr(self, key, value)


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON objects.
    
    This formatter is designed for production environments where logs
    are processed by log aggregation systems.
    """
    
    def __init__(self, include_stack_info: bool = False):
        super().__init__()
        self.include_stack_info = include_stack_info
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record to format
            
        Returns:
            str: JSON-formatted log entry
        """
        log_data = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName,
            "host": platform.node()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add stack info if configured and available
        if self.include_stack_info and record.stack_info:
            log_data["stack_info"] = record.stack_info
        
        # Add extra contextual information
        for key, value in record.__dict__.items():
            if key not in LOG_RECORD_BUILT_IN_ATTRS and not key.startswith("_"):
                log_data[key] = value
        
        return json.dumps(log_data)


class DetailedFormatter(logging.Formatter):
    """
    Formatter that provides detailed, human-readable log output.
    
    This formatter is designed for development and debugging,
    with color-coding and comprehensive information.
    """
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
        "RESET": "\033[0m"       # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with detailed, readable output.
        
        Args:
            record: The log record to format
            
        Returns:
            str: Formatted log entry
        """
        # Create timestamp
        timestamp = datetime.datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Format the basic log message
        level_name = record.levelname
        if self.use_colors:
            colored_level = f"{self.COLORS[level_name]}{level_name:8}{self.COLORS['RESET']}"
        else:
            colored_level = f"{level_name:8}"
        
        log_message = f"{timestamp} | {colored_level} | {record.name} | {record.getMessage()}"
        
        # Add location info
        location = f"{record.pathname}:{record.lineno} in {record.funcName}()"
        log_message += f"\n    Location: {location}"
        
        # Add context info if available
        context_items = {}
        for key, value in record.__dict__.items():
            if key not in LOG_RECORD_BUILT_IN_ATTRS and not key.startswith("_"):
                context_items[key] = value
        
        if context_items:
            context_str = "\n    ".join(f"{k}: {v}" for k, v in context_items.items())
            log_message += f"\n    Context:\n    {context_str}"
        
        # Add exception info if present
        if record.exc_info:
            exception_str = self.formatException(record.exc_info)
            log_message += f"\n    Exception:\n{exception_str}"
        
        # Add stack info if available
        if record.stack_info:
            log_message += f"\n    Stack:\n{record.stack_info}"
        
        return log_message


class LogContext:
    """
    Context manager for adding contextual information to logs.
    
    This class allows adding temporary context to all logs within
    a specific code block, which is useful for tracking operations
    across multiple function calls.
    
    Example:
        with LogContext(operation="user_login", user_id="123"):
            logger.info("Processing user login")
            # The log will include operation and user_id context
    """
    
    def __init__(self, **context):
        """
        Initialize with context key-value pairs.
        
        Args:
            **context: Arbitrary keyword arguments to add to the logging context
        """
        self.context = context
        self.previous_context = None
    
    def __enter__(self):
        """
        Enter the context block, adding context to thread-local storage.
        
        Returns:
            self: The context manager instance
        """
        # Save previous context if it exists
        if hasattr(_context_store, "context"):
            self.previous_context = _context_store.context.copy()
        else:
            self.previous_context = {}
        
        # Create or update context
        if not hasattr(_context_store, "context"):
            _context_store.context = {}
        
        # Add new context items
        _context_store.context.update(self.context)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context block, restoring previous context.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        # Restore previous context
        _context_store.context = self.previous_context


def log_execution(logger=None, level: str = "DEBUG"):
    """
    Decorator to log function execution with timing information.
    
    This decorator logs when a function starts and ends, including
    the execution time and any exceptions that occur.
    
    Args:
        logger: Logger to use (if None, gets logger from function's module)
        level: Log level to use for the messages
    
    Returns:
        Callable: Decorated function
    
    Example:
        @log_execution(level="INFO")
        def process_data(data):
            # Function implementation
    """
    def decorator(func):
        # Get the logger if not provided
        nonlocal logger
        if logger is None:
            module = inspect.getmodule(func)
            logger = get_logger(module.__name__ if module else __name__)
        
        log_level = getattr(logging, level)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__qualname__
            # Log start
            logger.log(log_level, f"Starting {func_name}")
            start_time = datetime.datetime.now()
            
            try:
                result = func(*args, **kwargs)
                # Log end with timing
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.log(log_level, f"Completed {func_name} in {duration:.3f}s")
                return result
            except Exception as e:
                # Log exception
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.exception(
                    f"Exception in {func_name} after {duration:.3f}s: {str(e)}"
                )
                raise
        
        return wrapper
    
    return decorator


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    This function returns a logger configured according to the project's
    logging settings. It ensures that loggers are hierarchical and respect
    the project's module structure.
    
    Args:
        name: Logger name, typically __name__ of the calling module
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("This is an info message")
    """
    # Ensure the name is prefixed with the project name if needed
    if not name.startswith("neuroca.") and name != "neuroca":
        if "." in name:
            # Handle cases where __name__ is used from a submodule
            parts = name.split(".")
            if parts[0] != "neuroca":
                name = f"neuroca.{name}"
        else:
            name = f"neuroca.{name}"
    
    return logging.getLogger(name)


def configure_logging(
    level: Union[str, LogLevel] = DEFAULT_LOG_LEVEL,
    format: Union[str, LogFormat] = DEFAULT_LOG_FORMAT,
    output: list[Union[str, LogOutput]] = DEFAULT_LOG_OUTPUT,
    file_path: Optional[str] = None,
    syslog_address: Optional[tuple] = None,
    include_stack_info: bool = False,
    use_colors: bool = True
) -> None:
    """
    Configure the logging system.
    
    This function sets up the logging system according to the specified
    parameters. It configures handlers, formatters, and filters.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format (standard, json, detailed)
        output: List of outputs (console, file, syslog)
        file_path: Path to log file (required if 'file' in output)
        syslog_address: Syslog address as (host, port) (required if 'syslog' in output)
        include_stack_info: Whether to include stack info in logs
        use_colors: Whether to use colors in console output
    
    Raises:
        ValueError: If required parameters are missing for selected outputs
    
    Example:
        configure_logging(
            level="INFO",
            format="json",
            output=["console", "file"],
            file_path="/var/log/neuroca.log"
        )
    """
    # Normalize inputs
    if isinstance(level, str):
        level = LogLevel(level.upper())
    
    if isinstance(format, str):
        format = LogFormat(format.lower())
    
    normalized_output = []
    for out in output:
        if isinstance(out, str):
            normalized_output.append(LogOutput(out.lower()))
        else:
            normalized_output.append(out)
    output = normalized_output
    
    # Validate required parameters
    if LogOutput.FILE in output and not file_path:
        raise ValueError("file_path is required when 'file' output is selected")
    
    if LogOutput.SYSLOG in output and not syslog_address:
        raise ValueError("syslog_address is required when 'syslog' output is selected")
    
    # Create logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {},
        "filters": {
            "sensitive_data_filter": {
                "()": SensitiveDataFilter
            }
        },
        "handlers": {},
        "loggers": {
            "neuroca": {
                "level": level.value,
                "handlers": [],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": []
        }
    }
    
    # Configure formatters based on format
    if format == LogFormat.JSON:
        config["formatters"]["json"] = {
            "()": JsonFormatter,
            "include_stack_info": include_stack_info
        }
        formatter_name = "json"
    elif format == LogFormat.DETAILED:
        config["formatters"]["detailed"] = {
            "()": DetailedFormatter,
            "use_colors": use_colors
        }
        formatter_name = "detailed"
    else:  # Standard format
        config["formatters"]["standard"] = {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
        formatter_name = "standard"
    
    # Configure handlers based on output
    handlers = []
    
    if LogOutput.CONSOLE in output:
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": level.value,
            "formatter": formatter_name,
            "filters": ["sensitive_data_filter"],
            "stream": "ext://sys.stdout"
        }
        handlers.append("console")
    
    if LogOutput.FILE in output:
        # Ensure directory exists
        log_dir = os.path.dirname(file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level.value,
            "formatter": formatter_name,
            "filters": ["sensitive_data_filter"],
            "filename": file_path,
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf8"
        }
        handlers.append("file")
    
    if LogOutput.SYSLOG in output:
        config["handlers"]["syslog"] = {
            "class": "logging.handlers.SysLogHandler",
            "level": level.value,
            "formatter": formatter_name,
            "filters": ["sensitive_data_filter"],
            "address": syslog_address
        }
        handlers.append("syslog")
    
    # Update logger handlers
    config["loggers"]["neuroca"]["handlers"] = handlers
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Set custom log record factory
    logging.setLogRecordFactory(ContextualLogRecord)
    
    # Log configuration applied
    logger = get_logger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": level.value,
            "format": format.value,
            "output": [o.value for o in output]
        }
    )


def add_context(**kwargs) -> None:
    """
    Add persistent context to the current thread's logs.
    
    This function adds context that will be included in all subsequent
    log messages from the current thread.
    
    Args:
        **kwargs: Key-value pairs to add to the logging context
    
    Example:
        add_context(user_id="123", session_id="abc-456")
        logger.info("User action")  # Will include the context
    """
    if not hasattr(_context_store, "context"):
        _context_store.context = {}
    
    _context_store.context.update(kwargs)


def clear_context() -> None:
    """
    Clear all context from the current thread's logs.
    
    Example:
        clear_context()
        logger.info("No context included")
    """
    if hasattr(_context_store, "context"):
        _context_store.context = {}


def get_context() -> dict[str, Any]:
    """
    Get the current thread's logging context.
    
    Returns:
        Dict[str, Any]: Current context dictionary
    
    Example:
        context = get_context()
        print(f"Current correlation_id: {context.get('correlation_id')}")
    """
    if not hasattr(_context_store, "context"):
        _context_store.context = {}
    
    return _context_store.context.copy()


# Initialize default logging configuration
configure_logging()

# Export public API
__all__ = [
    "get_logger",
    "configure_logging",
    "LogContext",
    "log_execution",
    "add_context",
    "clear_context",
    "get_context",
    "LogLevel",
    "LogFormat",
    "LogOutput"
]