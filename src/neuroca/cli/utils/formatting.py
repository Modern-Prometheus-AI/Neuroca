"""
Formatting utilities for the NeuroCognitive Architecture CLI.

This module provides a comprehensive set of formatting utilities for the CLI interface,
ensuring consistent, readable, and accessible output across all CLI commands.
It handles various data types, supports color coding, and provides structured
formatting for different types of information (tables, lists, JSON, etc.).

Usage:
    from neuroca.cli.utils.formatting import (
        format_table, format_json, format_list, format_status,
        highlight_text, format_memory_size, format_duration
    )

    # Format a table of data
    headers = ["Name", "Type", "Size"]
    rows = [["memory_1", "working", "2.5 MB"], ["memory_2", "long-term", "10 GB"]]
    formatted_table = format_table(headers, rows)
    print(formatted_table)

    # Format a status message
    print(format_status("Memory system initialized", "success"))
"""

import json
import logging
import math
import os
import re
import textwrap
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Union

# Configure module logger
logger = logging.getLogger(__name__)


class TextColor(Enum):
    """ANSI color codes for terminal text formatting."""
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class StatusType(Enum):
    """Status types for formatting status messages."""
    SUCCESS = ("SUCCESS", TextColor.GREEN)
    ERROR = ("ERROR", TextColor.RED)
    WARNING = ("WARNING", TextColor.YELLOW)
    INFO = ("INFO", TextColor.BLUE)
    DEBUG = ("DEBUG", TextColor.BRIGHT_BLACK)


def supports_color() -> bool:
    """
    Determine if the current terminal supports color output.
    
    Returns:
        bool: True if the terminal supports color, False otherwise.
    """
    # Check if color is forced or disabled via environment variable
    if os.environ.get("FORCE_COLOR", "").lower() in ("1", "true", "yes"):
        return True
    if os.environ.get("NO_COLOR", "").lower() in ("1", "true", "yes"):
        return False
    
    # Check if output is redirected
    if not os.isatty(1):  # 1 is stdout file descriptor
        return False
    
    # Check platform-specific terminal support
    plat = os.environ.get("TERM", "")
    return plat != "dumb" and "COLORTERM" in os.environ


def colorize(text: str, color: TextColor) -> str:
    """
    Apply color formatting to text if supported by the terminal.
    
    Args:
        text: The text to colorize
        color: The color to apply
        
    Returns:
        str: Colorized text if supported, original text otherwise
    """
    if not supports_color():
        return text
    return f"{color.value}{text}{TextColor.RESET.value}"


def bold(text: str) -> str:
    """
    Make text bold if supported by the terminal.
    
    Args:
        text: The text to make bold
        
    Returns:
        str: Bold text if supported, original text otherwise
    """
    if not supports_color():
        return text
    return f"{TextColor.BOLD.value}{text}{TextColor.RESET.value}"


def underline(text: str) -> str:
    """
    Underline text if supported by the terminal.
    
    Args:
        text: The text to underline
        
    Returns:
        str: Underlined text if supported, original text otherwise
    """
    if not supports_color():
        return text
    return f"{TextColor.UNDERLINE.value}{text}{TextColor.RESET.value}"


def highlight_text(text: str, pattern: str, color: TextColor = TextColor.YELLOW) -> str:
    """
    Highlight occurrences of a pattern within text.
    
    Args:
        text: The text to search within
        pattern: The pattern to highlight
        color: The color to use for highlighting
        
    Returns:
        str: Text with highlighted pattern occurrences
        
    Example:
        >>> highlight_text("Memory usage is high", "high", TextColor.RED)
        'Memory usage is \033[31mhigh\033[0m'
    """
    if not text or not pattern:
        return text
    
    try:
        highlighted = re.sub(
            f"({re.escape(pattern)})",
            f"{color.value}\\1{TextColor.RESET.value}" if supports_color() else "\\1",
            text,
            flags=re.IGNORECASE
        )
        return highlighted
    except Exception as e:
        logger.warning(f"Failed to highlight text: {e}")
        return text


def format_table(
    headers: list[str],
    rows: list[list[str]],
    max_width: Optional[int] = None,
    title: Optional[str] = None
) -> str:
    """
    Format data as a table with aligned columns.
    
    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of column values
        max_width: Maximum width of the table (defaults to terminal width)
        title: Optional title for the table
        
    Returns:
        str: Formatted table as a string
        
    Example:
        >>> headers = ["Name", "Type", "Size"]
        >>> rows = [["memory_1", "working", "2.5 MB"], ["memory_2", "long-term", "10 GB"]]
        >>> print(format_table(headers, rows, title="Memory Systems"))
        ┌─────────────────────────┐
        │     Memory Systems      │
        ├────────┬───────────┬────┤
        │ Name   │ Type      │ Size│
        ├────────┼───────────┼────┤
        │memory_1│ working   │2.5 MB│
        │memory_2│ long-term │10 GB│
        └────────┴───────────┴────┘
    """
    if not headers or not rows:
        logger.warning("Empty headers or rows provided to format_table")
        return ""
    
    # Determine terminal width if max_width not specified
    if max_width is None:
        try:
            terminal_size = os.get_terminal_size()
            max_width = terminal_size.columns
        except (AttributeError, OSError):
            max_width = 80  # Default if terminal size can't be determined
    
    # Ensure all rows have the same number of columns as headers
    sanitized_rows = []
    for row in rows:
        if len(row) < len(headers):
            # Pad with empty strings if row has fewer columns
            sanitized_rows.append(row + [""] * (len(headers) - len(row)))
        elif len(row) > len(headers):
            # Truncate if row has more columns
            sanitized_rows.append(row[:len(headers)])
        else:
            sanitized_rows.append(row)
    
    # Convert all values to strings
    str_rows = [[str(cell) for cell in row] for row in sanitized_rows]
    
    # Calculate column widths (minimum width is the header length)
    col_widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))
    
    # Adjust column widths if total exceeds max_width
    total_width = sum(col_widths) + (3 * (len(headers) - 1)) + 4  # Include separators and borders
    if total_width > max_width:
        # Distribute available width proportionally
        available_width = max_width - (3 * (len(headers) - 1)) - 4
        total_content = sum(col_widths)
        col_widths = [max(3, int((w / total_content) * available_width)) for w in col_widths]
    
    # Build the table
    result = []
    
    # Add title if provided
    if title:
        total_width = sum(col_widths) + (3 * (len(headers) - 1)) + 4
        result.append("┌" + "─" * (total_width - 2) + "┐")
        centered_title = title.center(total_width - 2)
        result.append("│" + centered_title + "│")
    
    # Add header row
    header_sep = "┬".join(["─" * (w + 2) for w in col_widths])
    result.append("┌" + header_sep + "┐" if not title else "├" + header_sep + "┤")
    
    header_row = "│"
    for i, header in enumerate(headers):
        header_text = header.ljust(col_widths[i])
        if len(header_text) > col_widths[i]:
            header_text = header_text[:col_widths[i] - 3] + "..."
        header_row += f" {header_text} │"
    result.append(header_row)
    
    # Add separator between header and data
    result.append("├" + "┼".join(["─" * (w + 2) for w in col_widths]) + "┤")
    
    # Add data rows
    for row in str_rows:
        data_row = "│"
        for i, cell in enumerate(row):
            cell_text = cell.ljust(col_widths[i])
            if len(cell_text) > col_widths[i]:
                cell_text = cell_text[:col_widths[i] - 3] + "..."
            data_row += f" {cell_text} │"
        result.append(data_row)
    
    # Add bottom border
    result.append("└" + "┴".join(["─" * (w + 2) for w in col_widths]) + "┘")
    
    return "\n".join(result)


def format_json(
    data: Union[dict, list],
    indent: int = 2,
    sort_keys: bool = False,
    colorize: bool = True,
    max_width: Optional[int] = None
) -> str:
    """
    Format and optionally colorize JSON data.
    
    Args:
        data: The data to format as JSON
        indent: Number of spaces for indentation
        sort_keys: Whether to sort dictionary keys
        colorize: Whether to apply syntax highlighting
        max_width: Maximum width before wrapping
        
    Returns:
        str: Formatted JSON string
        
    Example:
        >>> data = {"name": "working_memory", "capacity": 7, "active": True}
        >>> print(format_json(data))
        {
          "name": "working_memory",
          "capacity": 7,
          "active": true
        }
    """
    if not data:
        return "{}" if isinstance(data, dict) else "[]"
    
    try:
        # Format the JSON with indentation
        formatted = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
        
        # Apply syntax highlighting if requested
        if colorize and supports_color():
            # Simple syntax highlighting
            formatted = re.sub(
                r'("(?:\\.|[^"\\])*")',
                f"{TextColor.GREEN.value}\\1{TextColor.RESET.value}",
                formatted
            )
            formatted = re.sub(
                r'\b(true|false|null)\b',
                f"{TextColor.YELLOW.value}\\1{TextColor.RESET.value}",
                formatted
            )
            formatted = re.sub(
                r'(\b\d+\.?\d*\b)',
                f"{TextColor.CYAN.value}\\1{TextColor.RESET.value}",
                formatted
            )
        
        # Apply width limiting if requested
        if max_width:
            lines = formatted.split('\n')
            wrapped_lines = []
            for line in lines:
                if len(line) > max_width:
                    # Find a good place to wrap (after a comma)
                    wrapped = textwrap.fill(line, width=max_width, break_on_hyphens=False)
                    wrapped_lines.extend(wrapped.split('\n'))
                else:
                    wrapped_lines.append(line)
            formatted = '\n'.join(wrapped_lines)
        
        return formatted
    except Exception as e:
        logger.error(f"Error formatting JSON: {e}")
        return str(data)


def format_list(
    items: list[str],
    bullet: str = "•",
    indentation: int = 2,
    nested_level: int = 0
) -> str:
    """
    Format a list of items with bullet points and proper indentation.
    
    Args:
        items: List of items to format
        bullet: Bullet character to use
        indentation: Number of spaces for each indentation level
        nested_level: Current nesting level (for recursive calls)
        
    Returns:
        str: Formatted list as a string
        
    Example:
        >>> items = ["Working memory", "Episodic memory", "Semantic memory"]
        >>> print(format_list(items))
          • Working memory
          • Episodic memory
          • Semantic memory
    """
    if not items:
        return ""
    
    result = []
    indent = " " * (indentation * nested_level)
    
    for item in items:
        if isinstance(item, list):
            # Handle nested lists
            nested_items = format_list(item, bullet, indentation, nested_level + 1)
            result.append(nested_items)
        else:
            result.append(f"{indent}{bullet} {item}")
    
    return "\n".join(result)


def format_status(
    message: str,
    status_type: Union[str, StatusType] = StatusType.INFO,
    include_timestamp: bool = False
) -> str:
    """
    Format a status message with appropriate styling.
    
    Args:
        message: The status message to format
        status_type: Type of status (success, error, warning, info)
        include_timestamp: Whether to include a timestamp
        
    Returns:
        str: Formatted status message
        
    Example:
        >>> print(format_status("Memory system initialized", "success"))
        [SUCCESS] Memory system initialized
        
        >>> print(format_status("Connection failed", StatusType.ERROR, True))
        [2023-06-15 14:30:22] [ERROR] Connection failed
    """
    # Convert string status type to enum if needed
    if isinstance(status_type, str):
        try:
            status_type = StatusType[status_type.upper()]
        except KeyError:
            logger.warning(f"Unknown status type: {status_type}, defaulting to INFO")
            status_type = StatusType.INFO
    
    # Get status label and color
    label, color = status_type.value
    
    # Format timestamp if requested
    timestamp_str = ""
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_str = f"[{timestamp}] "
    
    # Format the status message
    status_label = colorize(f"[{label}]", color)
    return f"{timestamp_str}{status_label} {message}"


def format_memory_size(
    size_bytes: Union[int, float],
    decimal_places: int = 2,
    binary: bool = True
) -> str:
    """
    Format a memory size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        decimal_places: Number of decimal places to show
        binary: If True, use binary units (KiB, MiB); otherwise use decimal (KB, MB)
        
    Returns:
        str: Formatted memory size string
        
    Example:
        >>> format_memory_size(1024)
        '1.00 KiB'
        >>> format_memory_size(1500000, binary=False)
        '1.50 MB'
    """
    if size_bytes < 0:
        logger.warning(f"Negative memory size provided: {size_bytes}")
        return f"-{format_memory_size(abs(size_bytes), decimal_places, binary)}"
    
    if size_bytes == 0:
        return "0 B"
    
    base = 1024 if binary else 1000
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"] if binary else \
            ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    
    # Calculate the appropriate unit
    power = min(int(math.log(size_bytes, base)), len(units) - 1)
    size = size_bytes / (base ** power)
    
    # Format with the specified decimal places
    return f"{size:.{decimal_places}f} {units[power]}"


def format_duration(
    duration: Union[int, float, timedelta],
    compact: bool = False,
    include_milliseconds: bool = True
) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        duration: Duration in seconds or a timedelta object
        compact: If True, use compact format (1h 2m 3s); otherwise use verbose (1 hour, 2 minutes, 3 seconds)
        include_milliseconds: Whether to include milliseconds in the output
        
    Returns:
        str: Formatted duration string
        
    Example:
        >>> format_duration(3661.5)
        '1 hour, 1 minute, 1.50 seconds'
        >>> format_duration(3661.5, compact=True)
        '1h 1m 1.50s'
    """
    # Convert timedelta to seconds if needed
    if isinstance(duration, timedelta):
        duration_seconds = duration.total_seconds()
    else:
        duration_seconds = float(duration)
    
    if duration_seconds < 0:
        logger.warning(f"Negative duration provided: {duration_seconds}")
        return f"-{format_duration(abs(duration_seconds), compact, include_milliseconds)}"
    
    # Extract time components
    days, remainder = divmod(duration_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format the duration string
    parts = []
    
    if days > 0:
        if compact:
            parts.append(f"{int(days)}d")
        else:
            parts.append(f"{int(days)} {'day' if days == 1 else 'days'}")
    
    if hours > 0:
        if compact:
            parts.append(f"{int(hours)}h")
        else:
            parts.append(f"{int(hours)} {'hour' if hours == 1 else 'hours'}")
    
    if minutes > 0:
        if compact:
            parts.append(f"{int(minutes)}m")
        else:
            parts.append(f"{int(minutes)} {'minute' if minutes == 1 else 'minutes'}")
    
    # Format seconds with or without milliseconds
    if seconds > 0 or (not parts and seconds == 0):
        if include_milliseconds:
            sec_format = f"{seconds:.2f}"
            if sec_format.endswith(".00"):
                sec_format = f"{int(seconds)}"
        else:
            sec_format = f"{int(seconds)}"
        
        if compact:
            parts.append(f"{sec_format}s")
        else:
            parts.append(f"{sec_format} {'second' if seconds == 1 else 'seconds'}")
    
    # Join the parts
    if compact:
        return " ".join(parts)
    else:
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def truncate_text(text: str, max_length: int, ellipsis: str = "...") -> str:
    """
    Truncate text to a maximum length, adding an ellipsis if truncated.
    
    Args:
        text: The text to truncate
        max_length: Maximum length of the result
        ellipsis: String to append if truncated
        
    Returns:
        str: Truncated text
        
    Example:
        >>> truncate_text("This is a long text", 10)
        'This is...'
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Ensure we have room for the ellipsis
    if max_length <= len(ellipsis):
        return ellipsis[:max_length]
    
    return text[:max_length - len(ellipsis)] + ellipsis


def format_progress_bar(
    progress: float,
    width: int = 40,
    fill_char: str = "█",
    empty_char: str = "░",
    include_percentage: bool = True
) -> str:
    """
    Create a text-based progress bar.
    
    Args:
        progress: Progress value between 0.0 and 1.0
        width: Width of the progress bar in characters
        fill_char: Character to use for filled portion
        empty_char: Character to use for empty portion
        include_percentage: Whether to include percentage text
        
    Returns:
        str: Formatted progress bar
        
    Example:
        >>> format_progress_bar(0.75, width=20)
        '[███████████████     ] 75%'
    """
    # Validate and clamp progress value
    if progress < 0:
        logger.warning(f"Negative progress value provided: {progress}, clamping to 0.0")
        progress = 0.0
    elif progress > 1:
        logger.warning(f"Progress value > 1 provided: {progress}, clamping to 1.0")
        progress = 1.0
    
    # Calculate filled width
    filled_width = int(width * progress)
    
    # Create the progress bar
    bar = f"[{fill_char * filled_width}{empty_char * (width - filled_width)}]"
    
    # Add percentage if requested
    if include_percentage:
        percentage = int(progress * 100)
        return f"{bar} {percentage}%"
    
    return bar


def format_key_value(
    data: dict[str, Any],
    separator: str = ": ",
    indent: int = 0,
    key_color: Optional[TextColor] = TextColor.CYAN
) -> str:
    """
    Format a dictionary as key-value pairs.
    
    Args:
        data: Dictionary to format
        separator: String to separate keys and values
        indent: Number of spaces to indent
        key_color: Color to apply to keys (None for no color)
        
    Returns:
        str: Formatted key-value pairs
        
    Example:
        >>> data = {"Name": "Working Memory", "Capacity": 7, "Active": True}
        >>> print(format_key_value(data))
        Name: Working Memory
        Capacity: 7
        Active: True
    """
    if not data:
        return ""
    
    result = []
    indent_str = " " * indent
    
    for key, value in data.items():
        key_str = str(key)
        if key_color and supports_color():
            key_str = colorize(key_str, key_color)
        
        # Format the value based on its type
        if isinstance(value, dict):
            # Recursively format nested dictionaries with increased indentation
            nested_str = format_key_value(value, separator, indent + 2, key_color)
            result.append(f"{indent_str}{key_str}{separator}")
            result.append(nested_str)
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            # Handle list of dictionaries
            result.append(f"{indent_str}{key_str}{separator}")
            for i, item in enumerate(value):
                result.append(f"{indent_str}  [{i}]:")
                result.append(format_key_value(item, separator, indent + 4, key_color))
        elif isinstance(value, list):
            # Format simple lists
            value_str = ", ".join(str(item) for item in value)
            result.append(f"{indent_str}{key_str}{separator}{value_str}")
        else:
            # Format simple values
            result.append(f"{indent_str}{key_str}{separator}{value}")
    
    return "\n".join(result)


def wrap_text(text: str, width: int = 80, indent: int = 0, subsequent_indent: Optional[int] = None) -> str:
    """
    Wrap text to a specified width with indentation.
    
    Args:
        text: Text to wrap
        width: Maximum line width
        indent: Number of spaces to indent the first line
        subsequent_indent: Number of spaces to indent subsequent lines (defaults to same as indent)
        
    Returns:
        str: Wrapped text
        
    Example:
        >>> text = "This is a long text that needs to be wrapped to multiple lines for better readability."
        >>> print(wrap_text(text, width=40, indent=2, subsequent_indent=4))
          This is a long text that needs to be
            wrapped to multiple lines for better
            readability.
    """
    if not text:
        return ""
    
    if subsequent_indent is None:
        subsequent_indent = indent
    
    first_indent = " " * indent
    subseq_indent = " " * subsequent_indent
    
    # Use textwrap to wrap the text
    wrapper = textwrap.TextWrapper(
        width=width,
        initial_indent=first_indent,
        subsequent_indent=subseq_indent,
        break_long_words=True,
        break_on_hyphens=True
    )
    
    return wrapper.fill(text)


def format_header(text: str, style: int = 1, width: Optional[int] = None) -> str:
    """
    Format text as a header with decorative elements.
    
    Args:
        text: Header text
        style: Header style (1-5)
        width: Width of the header (defaults to length of text + padding)
        
    Returns:
        str: Formatted header
        
    Example:
        >>> print(format_header("Memory System", style=2))
        ==================
        | Memory System |
        ==================
    """
    if not text:
        return ""
    
    # Determine width
    if width is None:
        width = len(text) + 4  # Add some padding
    
    # Center the text
    centered_text = text.center(width - 4)  # Account for side characters
    
    # Apply different header styles
    if style == 1:
        # ===============
        # = Header Text =
        # ===============
        border = "=" * width
        return f"{border}\n= {centered_text} =\n{border}"
    
    elif style == 2:
        # ===============
        # | Header Text |
        # ===============
        border = "=" * width
        return f"{border}\n| {centered_text} |\n{border}"
    
    elif style == 3:
        # ---------------
        # | HEADER TEXT |
        # ---------------
        border = "-" * width
        return f"{border}\n| {centered_text.upper()} |\n{border}"
    
    elif style == 4:
        # ┌─────────────┐
        # │ Header Text │
        # └─────────────┘
        return f"┌{'─' * (width - 2)}┐\n│ {centered_text} │\n└{'─' * (width - 2)}┘"
    
    elif style == 5:
        # << Header Text >>
        return f"<< {centered_text} >>"
    
    else:
        # Default to simple style
        return f"--- {text} ---"


def format_timestamp(
    timestamp: Optional[Union[float, datetime]] = None,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    include_ms: bool = False
) -> str:
    """
    Format a timestamp in a consistent way.
    
    Args:
        timestamp: Timestamp to format (float, datetime, or None for current time)
        format_str: strftime format string
        include_ms: Whether to include milliseconds
        
    Returns:
        str: Formatted timestamp
        
    Example:
        >>> format_timestamp(datetime(2023, 6, 15, 14, 30, 45, 123456))
        '2023-06-15 14:30:45'
        >>> format_timestamp(datetime(2023, 6, 15, 14, 30, 45, 123456), include_ms=True)
        '2023-06-15 14:30:45.123'
    """
    # Use current time if no timestamp provided
    if timestamp is None:
        dt = datetime.now()
    elif isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        logger.warning(f"Unsupported timestamp type: {type(timestamp)}")
        return str(timestamp)
    
    # Format with the specified format string
    formatted = dt.strftime(format_str)
    
    # Add milliseconds if requested
    if include_ms:
        ms = int(dt.microsecond / 1000)
        formatted += f".{ms:03d}"
    
    return formatted