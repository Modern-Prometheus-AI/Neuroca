"""
NeuroCognitive Architecture (NCA) CLI Commands Package.

This package contains all command-line interface commands for the NeuroCognitive Architecture system.
It provides a structured way to interact with the NCA system through the command line, enabling
operations such as system initialization, memory management, health monitoring, and more.

The commands are organized into logical groups based on their functionality and are designed
to be composable and extensible. Each command follows consistent patterns for argument parsing,
error handling, and output formatting.

Usage:
    Import specific commands or command groups as needed:
    ```python
    from neuroca.cli.commands import memory_commands, health_commands
    ```

    Or access all available commands through the ALL_COMMANDS dictionary:
    ```python
    from neuroca.cli.commands import ALL_COMMANDS
    ```

Note:
    This module serves as the entry point for all CLI commands and should maintain
    backward compatibility when adding or modifying commands.

Security:
    All user inputs through CLI commands are validated and sanitized to prevent
    injection attacks or other security vulnerabilities.
"""

import importlib
import logging
import os
import pkgutil
from typing import Any, Callable, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Command type definition
CommandFunction = Callable[..., Any]

# Dictionary to store all registered commands
ALL_COMMANDS: dict[str, CommandFunction] = {}

# Dictionary to store command groups
COMMAND_GROUPS: dict[str, dict[str, CommandFunction]] = {}

# Dictionary to store command help information
COMMAND_HELP: dict[str, str] = {}

# Dictionary to store command examples
COMMAND_EXAMPLES: dict[str, list[str]] = {}


def register_command(
    name: str, 
    group: str = "general", 
    help_text: str = "", 
    examples: Optional[list[str]] = None
) -> Callable[[CommandFunction], CommandFunction]:
    """
    Decorator to register a function as a CLI command.
    
    This decorator registers the decorated function in the ALL_COMMANDS dictionary
    and organizes it into the specified command group. It also stores help text
    and usage examples for the command.
    
    Args:
        name: The name of the command as it will be invoked from the CLI
        group: The group to which this command belongs (default: "general")
        help_text: A description of what the command does
        examples: A list of usage examples for the command
        
    Returns:
        The decorator function that registers the command
        
    Example:
        ```python
        @register_command(
            name="init",
            group="system",
            help_text="Initialize the NCA system with default settings",
            examples=["neuroca init", "neuroca init --config custom_config.yaml"]
        )
        def init_command(config_path: Optional[str] = None) -> None:
            # Command implementation
            pass
        ```
    """
    def decorator(func: CommandFunction) -> CommandFunction:
        if name in ALL_COMMANDS:
            logger.warning(f"Command '{name}' is being overridden")
            
        ALL_COMMANDS[name] = func
        
        # Initialize the group if it doesn't exist
        if group not in COMMAND_GROUPS:
            COMMAND_GROUPS[group] = {}
            
        COMMAND_GROUPS[group][name] = func
        COMMAND_HELP[name] = help_text
        
        if examples:
            COMMAND_EXAMPLES[name] = examples
        else:
            COMMAND_EXAMPLES[name] = []
            
        logger.debug(f"Registered command '{name}' in group '{group}'")
        return func
    
    return decorator


def get_command(name: str) -> Optional[CommandFunction]:
    """
    Get a command function by name.
    
    Args:
        name: The name of the command to retrieve
        
    Returns:
        The command function if found, None otherwise
        
    Example:
        ```python
        cmd = get_command("init")
        if cmd:
            cmd(config_path="custom_config.yaml")
        ```
    """
    return ALL_COMMANDS.get(name)


def get_commands_in_group(group: str) -> dict[str, CommandFunction]:
    """
    Get all commands in a specific group.
    
    Args:
        group: The name of the group
        
    Returns:
        A dictionary mapping command names to command functions
        
    Example:
        ```python
        memory_commands = get_commands_in_group("memory")
        for name, cmd in memory_commands.items():
            print(f"Memory command: {name}")
        ```
    """
    return COMMAND_GROUPS.get(group, {})


def get_command_help(name: str) -> str:
    """
    Get the help text for a command.
    
    Args:
        name: The name of the command
        
    Returns:
        The help text for the command, or an empty string if not found
        
    Example:
        ```python
        help_text = get_command_help("init")
        print(help_text)
        ```
    """
    return COMMAND_HELP.get(name, "")


def get_command_examples(name: str) -> list[str]:
    """
    Get usage examples for a command.
    
    Args:
        name: The name of the command
        
    Returns:
        A list of usage examples for the command
        
    Example:
        ```python
        examples = get_command_examples("init")
        for example in examples:
            print(f"Example: {example}")
        ```
    """
    return COMMAND_EXAMPLES.get(name, [])


def list_all_commands() -> dict[str, dict[str, str]]:
    """
    List all available commands organized by group with their help text.
    
    Returns:
        A dictionary mapping group names to dictionaries of command names and help texts
        
    Example:
        ```python
        all_commands = list_all_commands()
        for group, commands in all_commands.items():
            print(f"Group: {group}")
            for name, help_text in commands.items():
                print(f"  {name}: {help_text}")
        ```
    """
    result: dict[str, dict[str, str]] = {}
    
    for group, commands in COMMAND_GROUPS.items():
        result[group] = {}
        for name in commands:
            result[group][name] = COMMAND_HELP.get(name, "")
            
    return result


def _discover_and_load_commands() -> None:
    """
    Automatically discover and load command modules in the commands package.
    
    This function is called during package initialization to discover and import
    all command modules in the package, ensuring that their commands are registered.
    
    Note:
        This is an internal function and should not be called directly.
    """
    logger.debug("Discovering command modules...")
    
    # Get the directory of the current package
    package_dir = os.path.dirname(__file__)
    
    for _, module_name, _is_pkg in pkgutil.iter_modules([package_dir]):
        # Skip __init__.py and other special modules
        if module_name.startswith('_'):
            continue
            
        # Import the module
        try:
            importlib.import_module(f"neuroca.cli.commands.{module_name}")
            logger.debug(f"Loaded command module: {module_name}")
        except ImportError as e:
            logger.error(f"Failed to import command module {module_name}: {str(e)}")
            
    logger.info(f"Discovered {len(ALL_COMMANDS)} commands in {len(COMMAND_GROUPS)} groups")


# Automatically discover and load command modules when the package is imported
try:
    _discover_and_load_commands()
except Exception as e:
    logger.error(f"Error during command discovery: {str(e)}")
    # Don't re-raise the exception to avoid breaking imports,
    # but log it for debugging purposes

# Export public API
__all__ = [
    'ALL_COMMANDS',
    'COMMAND_GROUPS',
    'register_command',
    'get_command',
    'get_commands_in_group',
    'get_command_help',
    'get_command_examples',
    'list_all_commands',
]