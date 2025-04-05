"""
Custom logging formatters for the NeuroCognitive Architecture (NCA) system.

This module provides specialized logging formatters that enhance the standard Python
logging with additional context, structured output formats, and integration with
the NCA monitoring system. These formatters support various output formats including
JSON, colored console output, and specialized formats for different environments.

Usage:
    from neuroca.monitoring.logging.formatters import JsonFormatter
    
    logger = logging.getLogger("neuroca")
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

The formatters in this module are designed to:
1. Provide consistent logging across all NCA components
2. Include contextual information like component name, memory tier, etc.
3. Support structured logging for easier parsing and analysis
4. Enhance debugging with detailed context when needed
5. Integrate with monitoring systems for alerts and dashboards
"""

import json
import logging
import os
import platform
import socket
import sys
import threading
import uuid
from typing import Any, Optional, Union

import pythonjsonlogger.jsonlogger as jsonlogger


class BaseFormatter(logging.Formatter):
    """
    Base formatter that provides common functionality for all NCA formatters.
    
    This formatter extends the standard logging.Formatter with additional context
    and utility methods used by specialized formatters.
    """
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        validate: bool = True,
        include_hostname: bool = True,
        include_process_info: bool = True
    ):
        """
        Initialize the base formatter with common configuration.
        
        Args:
            fmt: Format string for log messages
            datefmt: Format string for dates
            style: Style of the format string (%, {, or $)
            validate: Whether to validate the format string
            include_hostname: Whether to include the hostname in logs
            include_process_info: Whether to include process and thread info
        """
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)
        self.include_hostname = include_hostname
        self.include_process_info = include_process_info
        self._hostname = socket.gethostname() if include_hostname else None
    
    def get_common_fields(self, record: logging.LogRecord) -> dict[str, Any]:
        """
        Extract common fields from a log record that should be included in all formats.
        
        Args:
            record: The log record to process
            
        Returns:
            Dictionary of common fields extracted from the record
        """
        fields = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        
        # Add location information if available
        if hasattr(record, 'pathname') and record.pathname:
            fields['file'] = record.pathname
            fields['line'] = record.lineno
            fields['function'] = record.funcName
            
        # Add exception information if available
        if record.exc_info:
            fields['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        elif record.exc_text:
            fields['exception'] = {
                'traceback': record.exc_text
            }
            
        # Add process and thread information if configured
        if self.include_process_info:
            fields['process'] = {
                'id': record.process,
                'name': record.processName
            }
            fields['thread'] = {
                'id': record.thread,
                'name': record.threadName
            }
            
        # Add hostname if configured
        if self.include_hostname and self._hostname:
            fields['hostname'] = self._hostname
            
        # Add custom NCA context if available
        if hasattr(record, 'nca_context') and record.nca_context:
            fields['nca_context'] = record.nca_context
            
        return fields


class JsonFormatter(BaseFormatter):
    """
    Formatter that outputs log records as JSON objects.
    
    This formatter is ideal for structured logging to files or systems that
    can parse JSON, such as log aggregation services, Elasticsearch, etc.
    """
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = '%Y-%m-%dT%H:%M:%S.%fZ',
        style: str = '%',
        validate: bool = True,
        include_hostname: bool = True,
        include_process_info: bool = True,
        json_indent: Optional[int] = None,
        json_ensure_ascii: bool = False,
        extra_fields: Optional[dict[str, Any]] = None
    ):
        """
        Initialize the JSON formatter.
        
        Args:
            fmt: Format string (not used for JSON, but kept for compatibility)
            datefmt: Format string for dates (ISO 8601 by default)
            style: Style of the format string (%, {, or $)
            validate: Whether to validate the format string
            include_hostname: Whether to include the hostname in logs
            include_process_info: Whether to include process and thread info
            json_indent: Indentation level for pretty-printing JSON (None for compact)
            json_ensure_ascii: Whether to escape non-ASCII characters
            extra_fields: Additional static fields to include in every log record
        """
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            include_hostname=include_hostname,
            include_process_info=include_process_info
        )
        self.json_indent = json_indent
        self.json_ensure_ascii = json_ensure_ascii
        self.extra_fields = extra_fields or {}
        
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON string representation of the log record
        """
        # Get common fields
        log_data = self.get_common_fields(record)
        
        # Add any extra fields configured for this formatter
        log_data.update(self.extra_fields)
        
        # Add any extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in [
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 
                'filename', 'funcName', 'id', 'levelname', 'levelno',
                'lineno', 'module', 'msecs', 'message', 'msg', 'name',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'thread', 'threadName', 'nca_context'
            ]:
                # Skip internal attributes and those already processed
                try:
                    # Try to serialize the value to ensure it's JSON-compatible
                    json.dumps({key: value})
                    log_data[key] = value
                except (TypeError, OverflowError):
                    # If the value can't be serialized, convert it to a string
                    log_data[key] = str(value)
        
        # Convert to JSON
        try:
            return json.dumps(
                log_data,
                indent=self.json_indent,
                ensure_ascii=self.json_ensure_ascii,
                default=str  # Convert any non-serializable objects to strings
            )
        except Exception as e:
            # Fallback in case of serialization errors
            return json.dumps({
                "timestamp": self.formatTime(record, self.datefmt),
                "level": "ERROR",
                "name": "logging.formatter",
                "message": f"Failed to serialize log record: {str(e)}",
                "original_message": record.getMessage()
            })


class ColoredConsoleFormatter(BaseFormatter):
    """
    Formatter that outputs colored log records for console display.
    
    This formatter enhances readability in terminal environments by using
    ANSI color codes to highlight different log levels and components.
    """
    
    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
        'BACKGROUND_RED': '\033[41m',
        'BACKGROUND_GREEN': '\033[42m',
        'BACKGROUND_YELLOW': '\033[43m',
        'BACKGROUND_BLUE': '\033[44m',
    }
    
    # Level-specific colors
    LEVEL_COLORS = {
        'DEBUG': COLORS['BLUE'],
        'INFO': COLORS['GREEN'],
        'WARNING': COLORS['YELLOW'],
        'ERROR': COLORS['RED'],
        'CRITICAL': COLORS['BACKGROUND_RED'] + COLORS['WHITE'] + COLORS['BOLD'],
    }
    
    def __init__(
        self,
        fmt: Optional[str] = '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt: Optional[str] = '%Y-%m-%d %H:%M:%S',
        style: str = '%',
        validate: bool = True,
        include_hostname: bool = False,
        include_process_info: bool = False,
        use_colors: bool = True
    ):
        """
        Initialize the colored console formatter.
        
        Args:
            fmt: Format string for log messages
            datefmt: Format string for dates
            style: Style of the format string (%, {, or $)
            validate: Whether to validate the format string
            include_hostname: Whether to include the hostname in logs
            include_process_info: Whether to include process and thread info
            use_colors: Whether to use ANSI colors (can be disabled for non-terminal output)
        """
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            include_hostname=include_hostname,
            include_process_info=include_process_info
        )
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors for console display.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted string with ANSI color codes
        """
        # Make a copy of the record to avoid modifying the original
        record_copy = logging.makeLogRecord(record.__dict__)
        
        # Apply colors if enabled
        if self.use_colors:
            level_color = self.LEVEL_COLORS.get(record_copy.levelname, '')
            reset_color = self.COLORS['RESET']
            
            # Add colors to level name
            record_copy.levelname = f"{level_color}{record_copy.levelname}{reset_color}"
            
            # If there's an exception, format it with colors
            if record_copy.exc_info:
                record_copy.exc_text = self._colorize_traceback(
                    self.formatException(record_copy.exc_info)
                )
        
        # Format the record using the parent formatter
        formatted_message = super().format(record_copy)
        
        # Add NCA context if available
        if hasattr(record, 'nca_context') and record.nca_context:
            context_str = self._format_nca_context(record.nca_context)
            if context_str:
                formatted_message += f"\n{context_str}"
        
        return formatted_message
    
    def _colorize_traceback(self, traceback_text: str) -> str:
        """
        Add colors to a traceback to highlight important parts.
        
        Args:
            traceback_text: The traceback text to colorize
            
        Returns:
            Colorized traceback text
        """
        if not self.use_colors:
            return traceback_text
            
        lines = traceback_text.split('\n')
        colored_lines = []
        
        for line in lines:
            if line.startswith('Traceback'):
                # Highlight the traceback header
                colored_lines.append(f"{self.COLORS['BOLD']}{self.COLORS['WHITE']}{line}{self.COLORS['RESET']}")
            elif line.strip().startswith('File '):
                # Highlight file paths
                colored_lines.append(f"{self.COLORS['CYAN']}{line}{self.COLORS['RESET']}")
            elif line.strip().startswith('raise '):
                # Highlight the raise statement
                colored_lines.append(f"{self.COLORS['RED']}{line}{self.COLORS['RESET']}")
            else:
                colored_lines.append(line)
                
        return '\n'.join(colored_lines)
    
    def _format_nca_context(self, context: dict[str, Any]) -> str:
        """
        Format NCA context information for display.
        
        Args:
            context: Dictionary of NCA context information
            
        Returns:
            Formatted string representation of the context
        """
        if not context:
            return ""
            
        lines = ["NCA Context:"]
        
        for key, value in context.items():
            if self.use_colors:
                key_str = f"{self.COLORS['BOLD']}{key}{self.COLORS['RESET']}"
            else:
                key_str = key
                
            if isinstance(value, dict):
                lines.append(f"  {key_str}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"    {sub_key}: {sub_value}")
            else:
                lines.append(f"  {key_str}: {value}")
                
        return '\n'.join(lines)


class StructuredFormatter(jsonlogger.JsonFormatter):
    """
    Enhanced JSON formatter that provides structured logging with NCA-specific fields.
    
    This formatter extends the python-json-logger library's JsonFormatter with
    additional functionality specific to the NCA system, including standardized
    field names and automatic inclusion of contextual information.
    """
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = '%Y-%m-%dT%H:%M:%S.%fZ',
        style: str = '%',
        json_indent: Optional[int] = None,
        json_ensure_ascii: bool = False,
        reserved_attrs: Optional[list[str]] = None,
        rename_fields: Optional[dict[str, str]] = None,
        static_fields: Optional[dict[str, Any]] = None,
        include_hostname: bool = True,
        include_system_info: bool = True,
        include_request_id: bool = True
    ):
        """
        Initialize the structured formatter.
        
        Args:
            fmt: Format string (defaults to a comprehensive set of fields)
            datefmt: Format string for dates (ISO 8601 by default)
            style: Style of the format string (%, {, or $)
            json_indent: Indentation level for pretty-printing JSON
            json_ensure_ascii: Whether to escape non-ASCII characters
            reserved_attrs: List of attributes to exclude from the log record
            rename_fields: Dictionary mapping log record attributes to output field names
            static_fields: Dictionary of static fields to include in every log record
            include_hostname: Whether to include the hostname in logs
            include_system_info: Whether to include system information in logs
            include_request_id: Whether to include request ID tracking
        """
        # Default format string if none provided
        if fmt is None:
            fmt = '%(timestamp)s %(level)s %(name)s %(message)s'
            
        # Default reserved attributes to exclude
        if reserved_attrs is None:
            reserved_attrs = []
            
        # Default field name mapping
        if rename_fields is None:
            rename_fields = {
                'levelname': 'level',
                'asctime': 'timestamp',
                'exc_info': 'exception',
                'exc_text': 'exception_text',
                'pathname': 'file',
                'lineno': 'line',
                'funcName': 'function',
                'processName': 'process_name',
                'threadName': 'thread_name'
            }
            
        # Initialize the parent JSON formatter
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            json_indent=json_indent,
            json_ensure_ascii=json_ensure_ascii,
            reserved_attrs=reserved_attrs,
            rename_fields=rename_fields
        )
        
        self.static_fields = static_fields or {}
        self.include_hostname = include_hostname
        self.include_system_info = include_system_info
        self.include_request_id = include_request_id
        
        # Cache system information to avoid repeated calls
        self._hostname = socket.gethostname() if include_hostname else None
        self._system_info = self._get_system_info() if include_system_info else None
        
        # Initialize request ID tracking
        self._request_id_local = threading.local() if include_request_id else None
    
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        """
        Add custom fields to the log record before formatting.
        
        Args:
            log_record: The target dictionary for the formatted log record
            record: The original log record
            message_dict: Dictionary of fields extracted from the message
        """
        # Call the parent method first
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp if not present
        if 'timestamp' not in log_record:
            log_record['timestamp'] = self.formatTime(record, self.datefmt)
            
        # Add static fields
        log_record.update(self.static_fields)
        
        # Add hostname if configured
        if self.include_hostname and self._hostname:
            log_record['hostname'] = self._hostname
            
        # Add system info if configured
        if self.include_system_info and self._system_info:
            log_record['system'] = self._system_info
            
        # Add request ID if configured and available
        if self.include_request_id and hasattr(self._request_id_local, 'request_id'):
            log_record['request_id'] = self._request_id_local.request_id
            
        # Add NCA context if available
        if hasattr(record, 'nca_context') and record.nca_context:
            log_record['nca_context'] = record.nca_context
    
    def _get_system_info(self) -> dict[str, str]:
        """
        Collect system information for inclusion in log records.
        
        Returns:
            Dictionary of system information
        """
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'process_id': os.getpid()
        }
    
    def set_request_id(self, request_id: Optional[str] = None) -> str:
        """
        Set the request ID for the current thread.
        
        Args:
            request_id: The request ID to set, or None to generate a new one
            
        Returns:
            The request ID that was set
        """
        if not self.include_request_id or not self._request_id_local:
            return ""
            
        if request_id is None:
            request_id = str(uuid.uuid4())
            
        self._request_id_local.request_id = request_id
        return request_id
    
    def clear_request_id(self) -> None:
        """
        Clear the request ID for the current thread.
        """
        if self.include_request_id and self._request_id_local:
            if hasattr(self._request_id_local, 'request_id'):
                delattr(self._request_id_local, 'request_id')


class MemoryTierFormatter(StructuredFormatter):
    """
    Specialized formatter for memory tier components that includes memory-specific context.
    
    This formatter extends the StructuredFormatter with fields specific to the
    three-tiered memory system in the NCA architecture.
    """
    
    def __init__(
        self,
        memory_tier: str,
        component_name: str,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = '%Y-%m-%dT%H:%M:%S.%fZ',
        style: str = '%',
        json_indent: Optional[int] = None,
        json_ensure_ascii: bool = False,
        include_memory_stats: bool = True,
        **kwargs
    ):
        """
        Initialize the memory tier formatter.
        
        Args:
            memory_tier: The memory tier this formatter is for ('working', 'episodic', 'semantic')
            component_name: The name of the component within the memory tier
            fmt: Format string
            datefmt: Format string for dates
            style: Style of the format string
            json_indent: Indentation level for pretty-printing JSON
            json_ensure_ascii: Whether to escape non-ASCII characters
            include_memory_stats: Whether to include memory usage statistics
            **kwargs: Additional arguments to pass to the parent formatter
        """
        # Validate memory tier
        if memory_tier not in ('working', 'episodic', 'semantic'):
            raise ValueError(
                f"Invalid memory tier: {memory_tier}. "
                "Must be one of: 'working', 'episodic', 'semantic'"
            )
            
        # Set up static fields for this memory tier
        static_fields = kwargs.pop('static_fields', {})
        static_fields.update({
            'memory_tier': memory_tier,
            'component': component_name
        })
        
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            json_indent=json_indent,
            json_ensure_ascii=json_ensure_ascii,
            static_fields=static_fields,
            **kwargs
        )
        
        self.include_memory_stats = include_memory_stats
        self.memory_tier = memory_tier
        self.component_name = component_name
    
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        """
        Add memory-specific fields to the log record.
        
        Args:
            log_record: The target dictionary for the formatted log record
            record: The original log record
            message_dict: Dictionary of fields extracted from the message
        """
        # Call the parent method first
        super().add_fields(log_record, record, message_dict)
        
        # Add memory usage statistics if configured
        if self.include_memory_stats:
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                log_record['memory_usage'] = {
                    'rss': memory_info.rss,  # Resident Set Size
                    'vms': memory_info.vms,  # Virtual Memory Size
                    'percent': process.memory_percent()
                }
            except (ImportError, Exception) as e:
                # If psutil is not available or fails, add a note but don't crash
                log_record['memory_usage_error'] = str(e)


# Factory function to create appropriate formatters based on environment
def create_formatter(
    formatter_type: str = 'json',
    **kwargs
) -> Union[BaseFormatter, logging.Formatter]:
    """
    Factory function to create an appropriate formatter based on the environment.
    
    Args:
        formatter_type: Type of formatter to create ('json', 'colored', 'structured', 'memory_tier')
        **kwargs: Additional arguments to pass to the formatter constructor
        
    Returns:
        Configured formatter instance
        
    Raises:
        ValueError: If an invalid formatter type is specified
    """
    if formatter_type == 'json':
        return JsonFormatter(**kwargs)
    elif formatter_type == 'colored':
        return ColoredConsoleFormatter(**kwargs)
    elif formatter_type == 'structured':
        return StructuredFormatter(**kwargs)
    elif formatter_type == 'memory_tier':
        # Require memory_tier and component_name for this formatter
        if 'memory_tier' not in kwargs or 'component_name' not in kwargs:
            raise ValueError(
                "memory_tier and component_name are required for MemoryTierFormatter"
            )
        return MemoryTierFormatter(**kwargs)
    else:
        raise ValueError(
            f"Invalid formatter type: {formatter_type}. "
            "Must be one of: 'json', 'colored', 'structured', 'memory_tier'"
        )