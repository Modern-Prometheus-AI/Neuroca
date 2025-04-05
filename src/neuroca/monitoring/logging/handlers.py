"""
Custom logging handlers for the NeuroCognitive Architecture (NCA) system.

This module provides specialized logging handlers designed for the NCA system's monitoring
requirements. These handlers extend Python's standard logging handlers with additional
functionality specific to AI system monitoring, including:

- Structured JSON logging for machine-readable logs
- Rotating file handlers with compression
- Memory-efficient buffered handlers
- Context-aware handlers that include system state
- Secure handlers that redact sensitive information
- Performance-optimized handlers for high-throughput logging

Usage:
    from neuroca.monitoring.logging.handlers import JsonFileHandler, BufferedHandler
    
    # Configure a JSON file handler
    handler = JsonFileHandler(
        filename="app.log",
        max_bytes=10485760,  # 10MB
        backup_count=5,
        encoding="utf-8"
    )
    
    # Configure a buffered handler for performance
    buffered = BufferedHandler(
        target_handler=handler,
        buffer_size=1000,
        flush_interval=5.0  # seconds
    )
    
    # Add to logger
    logger = logging.getLogger("neuroca")
    logger.addHandler(buffered)
"""

import atexit
import datetime
import gzip
import json
import logging
import logging.handlers
import os
import queue
import re
import shutil
import threading
import traceback
from typing import Any, Optional

# Constants for common configuration
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_ENCODING = "utf-8"
DEFAULT_BUFFER_SIZE = 1000
DEFAULT_FLUSH_INTERVAL = 5.0  # seconds


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings for each logging record.
    
    This formatter structures log records as JSON objects, making them
    machine-readable and easily parseable by log analysis tools.
    
    Attributes:
        include_stack_info (bool): Whether to include stack info in logs
        additional_fields (dict): Additional fields to include in all logs
        reserved_attrs (set): Logger attributes that shouldn't be modified
    """
    
    def __init__(
        self,
        include_stack_info: bool = False,
        additional_fields: Optional[dict[str, Any]] = None,
        timestamp_format: str = "%Y-%m-%dT%H:%M:%S.%fZ",
    ):
        """
        Initialize the JSON formatter.
        
        Args:
            include_stack_info: Whether to include stack traces in logs
            additional_fields: Static fields to add to all log records
            timestamp_format: Format string for the timestamp
        """
        super().__init__()
        self.include_stack_info = include_stack_info
        self.additional_fields = additional_fields or {}
        self.timestamp_format = timestamp_format
        self.reserved_attrs = {
            "args", "asctime", "created", "exc_info", "exc_text", "filename",
            "funcName", "id", "levelname", "levelno", "lineno", "module",
            "msecs", "message", "msg", "name", "pathname", "process",
            "processName", "relativeCreated", "stack_info", "thread", "threadName"
        }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record to format
            
        Returns:
            A JSON string representation of the log record
        """
        log_data = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.timezone.utc
            ).strftime(self.timestamp_format),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add stack info if requested and available
        if self.include_stack_info and record.stack_info:
            log_data["stack_info"] = record.stack_info
        
        # Add any custom fields from the record
        for key, value in record.__dict__.items():
            if key not in self.reserved_attrs and not key.startswith("_"):
                log_data[key] = value
        
        # Add additional static fields
        log_data.update(self.additional_fields)
        
        return json.dumps(log_data, default=str)


class JsonFileHandler(logging.handlers.RotatingFileHandler):
    """
    A rotating file handler that writes logs in JSON format.
    
    This handler extends the standard RotatingFileHandler to write
    logs in JSON format and adds compression for rotated log files.
    
    Attributes:
        compress_logs (bool): Whether to compress rotated log files
        compression_level (int): Compression level for gzip (1-9)
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        encoding: str = DEFAULT_ENCODING,
        compress_logs: bool = True,
        compression_level: int = 6,
        include_stack_info: bool = False,
        additional_fields: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the JSON file handler.
        
        Args:
            filename: Path to the log file
            max_bytes: Maximum size of the log file before rotation
            backup_count: Number of backup files to keep
            encoding: Character encoding for the log file
            compress_logs: Whether to compress rotated log files
            compression_level: Compression level for gzip (1-9)
            include_stack_info: Whether to include stack traces in logs
            additional_fields: Static fields to add to all log records
        """
        # Ensure the directory exists
        log_dir = os.path.dirname(os.path.abspath(filename))
        os.makedirs(log_dir, exist_ok=True)
        
        super().__init__(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding
        )
        
        self.compress_logs = compress_logs
        self.compression_level = compression_level
        
        # Set JSON formatter
        self.setFormatter(
            JsonFormatter(
                include_stack_info=include_stack_info,
                additional_fields=additional_fields
            )
        )
    
    def doRollover(self) -> None:
        """
        Perform log rotation with optional compression.
        
        This method extends the standard rotation to add compression
        for rotated log files.
        """
        # Close the current file
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Rotate the files as in the parent class
        if self.backupCount > 0:
            # Remove the oldest log file if it exists
            oldest_backup = f"{self.baseFilename}.{self.backupCount}"
            if os.path.exists(oldest_backup):
                os.remove(oldest_backup)
            
            # Shift all existing backups
            for i in range(self.backupCount - 1, 0, -1):
                source = f"{self.baseFilename}.{i}"
                dest = f"{self.baseFilename}.{i + 1}"
                if os.path.exists(source):
                    if os.path.exists(dest):
                        os.remove(dest)
                    os.rename(source, dest)
            
            # Rename the current log file to .1
            if os.path.exists(self.baseFilename):
                backup_name = f"{self.baseFilename}.1"
                if os.path.exists(backup_name):
                    os.remove(backup_name)
                os.rename(self.baseFilename, backup_name)
                
                # Compress the rotated file if requested
                if self.compress_logs:
                    try:
                        with open(backup_name, 'rb') as f_in:
                            with gzip.open(f"{backup_name}.gz", 'wb', compresslevel=self.compression_level) as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        # Remove the uncompressed file after successful compression
                        os.remove(backup_name)
                    except Exception as e:
                        # If compression fails, keep the uncompressed file
                        sys.stderr.write(f"Error compressing log file {backup_name}: {str(e)}\n")
        
        # Open a new log file
        self.stream = self._open()


class BufferedHandler(logging.Handler):
    """
    A handler that buffers log records before sending them to a target handler.
    
    This handler improves performance by buffering log records and periodically
    flushing them to the target handler, reducing I/O operations.
    
    Attributes:
        target_handler (logging.Handler): The handler to which logs are forwarded
        buffer (queue.Queue): Queue holding buffered log records
        buffer_size (int): Maximum number of records to buffer
        flush_interval (float): Time in seconds between automatic flushes
        _flush_timer (threading.Timer): Timer for automatic flushing
        _lock (threading.RLock): Lock for thread safety
    """
    
    def __init__(
        self,
        target_handler: logging.Handler,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL,
    ):
        """
        Initialize the buffered handler.
        
        Args:
            target_handler: The handler to which logs are forwarded
            buffer_size: Maximum number of records to buffer
            flush_interval: Time in seconds between automatic flushes
        """
        super().__init__()
        self.target_handler = target_handler
        self.buffer = queue.Queue(maxsize=buffer_size)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self._flush_timer = None
        self._lock = threading.RLock()
        
        # Start the flush timer
        self._start_flush_timer()
        
        # Register cleanup on exit
        atexit.register(self.close)
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Add a log record to the buffer.
        
        If the buffer is full, it will be flushed automatically.
        
        Args:
            record: The log record to buffer
        """
        try:
            # Try to add the record to the buffer
            try:
                self.buffer.put_nowait(record)
            except queue.Full:
                # If the buffer is full, flush it and then add the record
                self.flush()
                self.buffer.put_nowait(record)
        except Exception:
            self.handleError(record)
    
    def flush(self) -> None:
        """
        Flush all buffered records to the target handler.
        
        This method is thread-safe and can be called manually or
        automatically by the flush timer.
        """
        with self._lock:
            # Process all records in the buffer
            while not self.buffer.empty():
                try:
                    record = self.buffer.get_nowait()
                    self.target_handler.handle(record)
                    self.buffer.task_done()
                except queue.Empty:
                    break
                except Exception as e:
                    # Log the error but continue processing other records
                    sys.stderr.write(f"Error processing buffered log record: {str(e)}\n")
    
    def _start_flush_timer(self) -> None:
        """Start the timer for automatic flushing."""
        if self._flush_timer is not None:
            self._flush_timer.cancel()
        
        self._flush_timer = threading.Timer(self.flush_interval, self._flush_and_reschedule)
        self._flush_timer.daemon = True
        self._flush_timer.start()
    
    def _flush_and_reschedule(self) -> None:
        """Flush the buffer and reschedule the timer."""
        try:
            self.flush()
        finally:
            # Reschedule the timer even if flush fails
            self._start_flush_timer()
    
    def close(self) -> None:
        """
        Close the handler and flush any remaining records.
        
        This method is called when the handler is no longer needed,
        such as during application shutdown.
        """
        if self._flush_timer is not None:
            self._flush_timer.cancel()
            self._flush_timer = None
        
        # Flush any remaining records
        self.flush()
        
        # Close the target handler
        self.target_handler.close()
        
        super().close()


class SensitiveDataFilter(logging.Filter):
    """
    A filter that redacts sensitive information from log records.
    
    This filter helps prevent sensitive data like passwords, API keys,
    and personal information from being logged.
    
    Attributes:
        patterns (List[Tuple[Pattern, str]]): Regex patterns and replacements
        fields_to_check (Set[str]): Log record fields to check for sensitive data
    """
    
    def __init__(
        self,
        patterns: Optional[list[tuple[str, str]]] = None,
        fields_to_check: Optional[list[str]] = None,
    ):
        """
        Initialize the sensitive data filter.
        
        Args:
            patterns: List of (regex_pattern, replacement) tuples
            fields_to_check: Log record fields to check for sensitive data
        """
        super().__init__()
        
        # Default patterns for common sensitive data
        default_patterns = [
            # Passwords
            (r'password["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', 'password=*****'),
            # API keys
            (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', 'api_key=*****'),
            # Access tokens
            (r'access[_-]?token["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', 'access_token=*****'),
            # Credit card numbers (simple pattern)
            (r'\b(?:\d{4}[- ]?){3}\d{4}\b', '**** **** **** ****'),
            # Social security numbers
            (r'\b\d{3}[-]?\d{2}[-]?\d{4}\b', '***-**-****'),
            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]'),
        ]
        
        # Compile the patterns
        self.patterns = [
            (re.compile(pattern), replacement)
            for pattern, replacement in (patterns or default_patterns)
        ]
        
        # Fields to check in the log record
        self.fields_to_check = set(fields_to_check or ["msg", "message"])
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter the log record by redacting sensitive information.
        
        This method modifies the log record in place, replacing sensitive
        information with redacted placeholders.
        
        Args:
            record: The log record to filter
            
        Returns:
            True to include the record (with redacted data), False to exclude it
        """
        # Check and redact the message
        if hasattr(record, "msg") and isinstance(record.msg, str):
            for pattern, replacement in self.patterns:
                record.msg = pattern.sub(replacement, record.msg)
        
        # Check and redact other specified fields
        for field in self.fields_to_check:
            if hasattr(record, field) and isinstance(getattr(record, field), str):
                value = getattr(record, field)
                for pattern, replacement in self.patterns:
                    value = pattern.sub(replacement, value)
                setattr(record, field, value)
        
        # Always include the record (with redacted data)
        return True


class ContextAwareHandler(logging.Handler):
    """
    A handler that enriches log records with contextual information.
    
    This handler adds system state and context information to log records,
    making them more useful for debugging and monitoring.
    
    Attributes:
        target_handler (logging.Handler): The handler to which logs are forwarded
        context_providers (List[Callable]): Functions that provide context data
    """
    
    def __init__(
        self,
        target_handler: logging.Handler,
        context_providers: Optional[list[callable]] = None,
    ):
        """
        Initialize the context-aware handler.
        
        Args:
            target_handler: The handler to which logs are forwarded
            context_providers: Functions that return context data dictionaries
        """
        super().__init__()
        self.target_handler = target_handler
        self.context_providers = context_providers or []
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Enrich the log record with context and forward it to the target handler.
        
        Args:
            record: The log record to enrich and forward
        """
        try:
            # Collect context from all providers
            for provider in self.context_providers:
                try:
                    context = provider()
                    if context and isinstance(context, dict):
                        # Add context data to the record
                        for key, value in context.items():
                            if not hasattr(record, key):
                                setattr(record, key, value)
                except Exception as e:
                    # If a context provider fails, log the error but continue
                    sys.stderr.write(f"Error collecting context from provider {provider.__name__}: {str(e)}\n")
            
            # Forward the enriched record to the target handler
            self.target_handler.handle(record)
        except Exception:
            self.handleError(record)
    
    def close(self) -> None:
        """Close the handler and its target handler."""
        self.target_handler.close()
        super().close()


class AsyncHandler(logging.Handler):
    """
    A handler that processes log records asynchronously.
    
    This handler offloads log processing to a background thread,
    preventing logging from blocking the main application.
    
    Attributes:
        target_handler (logging.Handler): The handler to which logs are forwarded
        queue (queue.Queue): Queue for log records
        worker (threading.Thread): Background thread for processing logs
        _shutdown (threading.Event): Event to signal shutdown
    """
    
    def __init__(self, target_handler: logging.Handler, queue_size: int = 10000):
        """
        Initialize the asynchronous handler.
        
        Args:
            target_handler: The handler to which logs are forwarded
            queue_size: Maximum size of the log record queue
        """
        super().__init__()
        self.target_handler = target_handler
        self.queue = queue.Queue(maxsize=queue_size)
        self._shutdown = threading.Event()
        
        # Start the worker thread
        self.worker = threading.Thread(target=self._process_logs, name="AsyncLogHandler")
        self.worker.daemon = True
        self.worker.start()
        
        # Register cleanup on exit
        atexit.register(self.close)
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Add a log record to the processing queue.
        
        Args:
            record: The log record to process asynchronously
        """
        if self._shutdown.is_set():
            return
        
        try:
            # Try to add the record to the queue without blocking
            try:
                self.queue.put_nowait(record)
            except queue.Full:
                # If the queue is full, log a warning and drop the record
                sys.stderr.write("AsyncHandler queue full, dropping log record\n")
                self.handleError(record)
        except Exception:
            self.handleError(record)
    
    def _process_logs(self) -> None:
        """
        Process log records from the queue in a background thread.
        
        This method runs in a separate thread and forwards log records
        to the target handler.
        """
        while not self._shutdown.is_set() or not self.queue.empty():
            try:
                # Get a record from the queue with timeout
                try:
                    record = self.queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                
                # Forward the record to the target handler
                self.target_handler.handle(record)
                self.queue.task_done()
            except Exception as e:
                # Log errors but keep the thread running
                sys.stderr.write(f"Error in AsyncHandler worker thread: {str(e)}\n")
    
    def close(self) -> None:
        """
        Close the handler and wait for the worker thread to finish.
        
        This method signals the worker thread to shut down and waits
        for it to process any remaining log records.
        """
        # Signal shutdown
        self._shutdown.set()
        
        # Wait for the worker thread to finish (with timeout)
        if self.worker.is_alive():
            self.worker.join(timeout=5.0)
        
        # Close the target handler
        self.target_handler.close()
        
        super().close()


# Ensure 'sys' is imported for error reporting
import sys

# Export all handlers
__all__ = [
    'JsonFormatter',
    'JsonFileHandler',
    'BufferedHandler',
    'SensitiveDataFilter',
    'ContextAwareHandler',
    'AsyncHandler',
]