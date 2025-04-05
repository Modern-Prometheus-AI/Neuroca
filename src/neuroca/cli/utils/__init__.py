"""
CLI Utilities Module for NeuroCognitive Architecture (NCA)

This module provides utility functions and classes for the NeuroCognitive Architecture CLI,
supporting command-line operations, configuration management, logging, and other common
functionality needed across CLI commands.

Usage:
    from neuroca.cli.utils import (
        setup_logging, 
        load_config, 
        validate_path,
        format_output,
        handle_errors,
        ProgressBar
    )

    # Setup logging for CLI operations
    logger = setup_logging("command-name")
    
    # Load configuration
    config = load_config()
    
    # Use other utilities
    with handle_errors(logger):
        if validate_path(user_input_path):
            # Perform operations
            with ProgressBar("Processing", total=100) as progress:
                # Do work and update progress
                progress.update(10)
"""

import json
import logging
import os
import sys
import time
import traceback
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import click
import yaml
from tqdm import tqdm

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Constants
DEFAULT_CONFIG_PATHS = [
    "./config.yaml",
    "~/.neuroca/config.yaml",
    "/etc/neuroca/config.yaml",
]
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO

class CLIError(Exception):
    """Base exception class for CLI-related errors."""
    pass

class ConfigError(CLIError):
    """Exception raised for configuration-related errors."""
    pass

class ValidationError(CLIError):
    """Exception raised for input validation errors."""
    pass

class ResourceError(CLIError):
    """Exception raised for resource access or availability errors."""
    pass

def setup_logging(
    name: str, 
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    log_format: str = LOG_FORMAT
) -> logging.Logger:
    """
    Set up logging for CLI commands.
    
    Args:
        name: The name of the logger, typically the command name
        level: The logging level (default: INFO)
        log_file: Optional path to a log file
        log_format: The format string for log messages
        
    Returns:
        A configured logger instance
        
    Example:
        >>> logger = setup_logging("init-command")
        >>> logger.info("Command started")
    """
    logger = logging.getLogger(f"neuroca.cli.{name}")
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not set up log file at {log_file}: {str(e)}")
    
    return logger

def load_config(
    config_path: Optional[str] = None,
    required: bool = False
) -> dict[str, Any]:
    """
    Load configuration from a YAML or JSON file.
    
    Args:
        config_path: Path to the configuration file. If None, searches in default locations.
        required: If True, raises an error when no config is found. If False, returns empty dict.
        
    Returns:
        The loaded configuration as a dictionary
        
    Raises:
        ConfigError: If the configuration file cannot be loaded and required=True
        
    Example:
        >>> config = load_config("./my_config.yaml")
        >>> api_key = config.get("api_key")
    """
    logger = logging.getLogger("neuroca.cli.utils")
    
    # If a specific path is provided, only try that one
    if config_path:
        paths_to_try = [config_path]
    else:
        # Otherwise try the default paths
        paths_to_try = [os.path.expanduser(p) for p in DEFAULT_CONFIG_PATHS]
    
    for path in paths_to_try:
        try:
            with open(path) as f:
                if path.endswith(('.yaml', '.yml')):
                    config = yaml.safe_load(f)
                elif path.endswith('.json'):
                    config = json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {path}")
                    continue
                
                logger.debug(f"Loaded configuration from {path}")
                return config if config is not None else {}
        except FileNotFoundError:
            continue
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            msg = f"Error parsing configuration file {path}: {str(e)}"
            logger.error(msg)
            if required:
                raise ConfigError(msg) from e
        except (OSError, PermissionError) as e:
            msg = f"Error reading configuration file {path}: {str(e)}"
            logger.error(msg)
            if required:
                raise ConfigError(msg) from e
    
    # If we get here, no config was loaded
    if required:
        tried_paths = ", ".join(paths_to_try)
        msg = f"No configuration file found. Tried: {tried_paths}"
        logger.error(msg)
        raise ConfigError(msg)
    
    logger.warning("No configuration file found, using empty configuration")
    return {}

def validate_path(
    path: str, 
    must_exist: bool = True,
    should_be_file: Optional[bool] = None,
    should_be_dir: Optional[bool] = None,
    writable: bool = False
) -> bool:
    """
    Validate a file or directory path.
    
    Args:
        path: The path to validate
        must_exist: If True, the path must exist
        should_be_file: If True, the path must be a file
        should_be_dir: If True, the path must be a directory
        writable: If True, the path must be writable
        
    Returns:
        True if the path is valid according to the criteria, False otherwise
        
    Example:
        >>> if validate_path("/path/to/file.txt", should_be_file=True, writable=True):
        ...     # Safe to write to the file
    """
    path_obj = Path(os.path.expanduser(path))
    
    # Check existence
    if must_exist and not path_obj.exists():
        return False
    
    # Check if it's a file
    if should_be_file is not None:
        if should_be_file and not path_obj.is_file():
            return False
        if not should_be_file and path_obj.is_file():
            return False
    
    # Check if it's a directory
    if should_be_dir is not None:
        if should_be_dir and not path_obj.is_dir():
            return False
        if not should_be_dir and path_obj.is_dir():
            return False
    
    # Check if it's writable
    if writable:
        if path_obj.exists():
            # Check if existing path is writable
            return os.access(path, os.W_OK)
        else:
            # Check if parent directory is writable for new files
            return os.access(path_obj.parent, os.W_OK)
    
    return True

def format_output(
    data: Any,
    output_format: str = "text",
    pretty: bool = True
) -> str:
    """
    Format data for CLI output in various formats.
    
    Args:
        data: The data to format
        output_format: The desired output format ('text', 'json', 'yaml')
        pretty: Whether to format the output for human readability
        
    Returns:
        The formatted string
        
    Raises:
        ValueError: If an unsupported output format is specified
        
    Example:
        >>> result = {"name": "Model1", "accuracy": 0.95}
        >>> print(format_output(result, output_format="json"))
    """
    if output_format == "json":
        if pretty:
            return json.dumps(data, indent=2, sort_keys=True)
        return json.dumps(data)
    
    elif output_format == "yaml":
        return yaml.dump(data, default_flow_style=False)
    
    elif output_format == "text":
        if isinstance(data, (dict, list)):
            if pretty:
                return json.dumps(data, indent=2, sort_keys=True)
            return str(data)
        return str(data)
    
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

@contextmanager
def handle_errors(
    logger: Optional[logging.Logger] = None,
    exit_on_error: bool = True,
    show_traceback: bool = False
):
    """
    Context manager for handling errors in CLI commands.
    
    Args:
        logger: Logger to use for error messages
        exit_on_error: Whether to exit the program on error
        show_traceback: Whether to show the full traceback
        
    Example:
        >>> with handle_errors(logger):
        ...     # Code that might raise exceptions
        ...     result = potentially_risky_operation()
    """
    if logger is None:
        logger = logging.getLogger("neuroca.cli")
    
    try:
        yield
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user", err=True)
        if exit_on_error:
            sys.exit(1)
    except CLIError as e:
        click.echo(f"Error: {str(e)}", err=True)
        if show_traceback:
            logger.error(traceback.format_exc())
        if exit_on_error:
            sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        logger.error(f"Unexpected error: {str(e)}")
        if show_traceback:
            logger.error(traceback.format_exc())
        if exit_on_error:
            sys.exit(1)

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying a function if it raises specified exceptions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff_factor: Factor by which the delay increases with each attempt
        exceptions: Tuple of exceptions that trigger a retry
        
    Returns:
        A decorator function
        
    Example:
        >>> @retry(max_attempts=5, exceptions=(ConnectionError, TimeoutError))
        ... def fetch_data(url):
        ...     # Code that might fail temporarily
        ...     return requests.get(url)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger = logging.getLogger("neuroca.cli.utils")
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {current_delay:.2f} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_attempts} attempts failed.")
            
            if last_exception:
                raise last_exception
            
            # This should never be reached, but keeps type checkers happy
            raise RuntimeError("Unexpected error in retry logic")
        
        return wrapper
    
    return decorator

class ProgressBar:
    """
    A context manager for displaying progress bars in CLI applications.
    
    Attributes:
        description: Text description of the operation
        total: Total number of steps
        
    Example:
        >>> with ProgressBar("Processing files", total=10) as progress:
        ...     for i in range(10):
        ...         # Do some work
        ...         progress.update(1)
    """
    
    def __init__(
        self, 
        description: str, 
        total: int,
        disable: bool = False,
        unit: str = "it"
    ):
        """
        Initialize the progress bar.
        
        Args:
            description: Text description of the operation
            total: Total number of steps
            disable: Whether to disable the progress bar
            unit: The unit of progress (e.g., "it", "files", "MB")
        """
        self.description = description
        self.total = total
        self.disable = disable
        self.unit = unit
        self.progress_bar = None
    
    def __enter__(self) -> 'ProgressBar':
        """Enter the context manager, creating the progress bar."""
        self.progress_bar = tqdm(
            total=self.total,
            desc=self.description,
            disable=self.disable,
            unit=self.unit
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager, closing the progress bar."""
        if self.progress_bar:
            self.progress_bar.close()
    
    def update(self, n: int = 1):
        """
        Update the progress bar.
        
        Args:
            n: Number of steps to increment
        """
        if self.progress_bar:
            self.progress_bar.update(n)
    
    def set_description(self, description: str):
        """
        Set a new description for the progress bar.
        
        Args:
            description: The new description text
        """
        if self.progress_bar:
            self.progress_bar.set_description(description)

def confirm_action(
    message: str,
    default: bool = False,
    abort: bool = False
) -> bool:
    """
    Prompt the user to confirm an action.
    
    Args:
        message: The confirmation message to display
        default: The default response if the user just presses Enter
        abort: Whether to abort the program if the user declines
        
    Returns:
        True if the user confirmed, False otherwise
        
    Example:
        >>> if confirm_action("Are you sure you want to delete this file?"):
        ...     delete_file(path)
    """
    try:
        result = click.confirm(message, default=default)
        if not result and abort:
            click.echo("Operation aborted.")
            sys.exit(1)
        return result
    except click.Abort:
        click.echo("\nOperation aborted.")
        sys.exit(1)

def get_terminal_size() -> dict[str, int]:
    """
    Get the current terminal size.
    
    Returns:
        A dictionary with 'width' and 'height' keys
        
    Example:
        >>> size = get_terminal_size()
        >>> print(f"Terminal is {size['width']} columns wide")
    """
    try:
        columns, lines = os.get_terminal_size()
        return {"width": columns, "height": lines}
    except (OSError, AttributeError):
        # Default fallback values
        return {"width": 80, "height": 24}

# Export public API
__all__ = [
    'setup_logging',
    'load_config',
    'validate_path',
    'format_output',
    'handle_errors',
    'retry',
    'ProgressBar',
    'confirm_action',
    'get_terminal_size',
    'CLIError',
    'ConfigError',
    'ValidationError',
    'ResourceError',
]