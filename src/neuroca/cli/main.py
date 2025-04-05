#!/usr/bin/env python3
"""
NeuroCognitive Architecture (NCA) Command Line Interface

This module serves as the main entry point for the NCA CLI, providing a comprehensive
interface for interacting with the NeuroCognitive Architecture system. It enables users
to manage, monitor, and control various aspects of the NCA system through a structured
command hierarchy.

The CLI is built using Click for command parsing and organization, with comprehensive
logging, error handling, and configuration management.

Usage:
    neuroca --help
    neuroca [command] [options]
    
Examples:
    neuroca --version
    neuroca init --config path/to/config.yaml
    neuroca memory list
    neuroca run --model gpt-4 --input "Process this text"
    
Environment Variables:
    NEUROCA_CONFIG_PATH: Path to configuration file
    NEUROCA_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    NEUROCA_API_KEY: API key for LLM service integration
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Annotated, Any, Optional  # Added Annotated for Typer options

# import click # Remove click
import typer
import yaml
from rich.console import Console
from rich.logging import RichHandler

# Package version - Consider moving to __init__.py or a central place
try:
    from neuroca import __version__
except ImportError:
     __version__ = "0.1.0" # Fallback

# Initialize rich console for pretty output
console = Console()

# Configure logging with rich handler
logging.basicConfig(
    level=os.environ.get("NEUROCA_LOG_LEVEL", "INFO").upper(),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__) # Use __name__


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class NCAConfig:
    """
    Configuration manager for the NCA system.
    
    Handles loading, validation, and access to configuration settings from
    various sources (environment variables, config files, CLI parameters).
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or os.environ.get("NEUROCA_CONFIG_PATH")
        self.config: dict[str, Any] = {}
        
    def load(self) -> dict[str, Any]:
        """
        Load configuration from file if specified.
        
        Returns:
            Dict containing configuration values
            
        Raises:
            ConfigurationError: If configuration file cannot be loaded or parsed
        """
        if not self.config_path:
            logger.debug("No configuration file specified, using defaults")
            return {}
            
        config_path = Path(self.config_path)
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
            
        try:
            if config_path.suffix.lower() in ('.yaml', '.yml'):
                with open(config_path) as f:
                    self.config = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path) as f:
                    self.config = json.load(f)
            else:
                raise ConfigurationError(f"Unsupported configuration format: {config_path.suffix}")
                
            logger.debug(f"Loaded configuration from {self.config_path}")
            return self.config
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to parse configuration file: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key. Uses dot notation for nested keys.
        
        Args:
            key: Configuration key to retrieve (e.g., "memory.working_memory.capacity")
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key to set
            value: Value to assign
        """
        self.config[key] = value
        
    def save(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            path: Optional path to save configuration to (defaults to self.config_path)
            
        Raises:
            ConfigurationError: If configuration cannot be saved
        """
        save_path = Path(path or self.config_path)
        if not save_path:
            raise ConfigurationError("No configuration path specified for saving")
            
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            if save_path.suffix.lower() in ('.yaml', '.yml'):
                with open(save_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif save_path.suffix.lower() == '.json':
                with open(save_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            else:
                raise ConfigurationError(f"Unsupported configuration format: {save_path.suffix}")
                
            logger.debug(f"Saved configuration to {save_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")

# --- Typer App Definition ---

# Create the main Typer app
app = typer.Typer(
    name="neuroca",
    help="NeuroCognitive Architecture (NCA) command line interface",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]}
)

# State dictionary to hold shared objects like config
state = {"config_manager": None}

# Callback runs before any command
@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output.")] = False,
    config_path: Annotated[Optional[str], typer.Option("--config", "-c", help="Path to configuration file.")] = None,
):
    """
    NeuroCognitive Architecture (NCA) CLI.
    """
    # Configure logging level based on verbosity
    if verbose:
        logging.getLogger("neuroca").setLevel(logging.DEBUG) # Target root logger
        logger.debug("Verbose logging enabled")
    else:
        # Ensure root logger is at least INFO if not verbose
        logging.getLogger("neuroca").setLevel(logging.INFO)

    # Initialize configuration
    try:
        config_manager = NCAConfig(config_path)
        config_manager.load()
        state["config_manager"] = config_manager
        # Store config manager in context if needed by subcommands (Typer handles this differently than Click)
        # ctx.obj = state # Typer uses context parameters more directly
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        raise typer.Exit(code=1)

# --- Commands ---

@app.command()
def init(
    force: Annotated[bool, typer.Option("--force", "-f", help="Force initialization even if already initialized.")] = False,
    template: Annotated[Optional[str], typer.Option("--template", "-t", help="Template configuration to use.")] = None,
    # verbose and config_path are handled by the callback
) -> None:
    """
    Initialize the NCA system with required configuration and resources.
    """
    logger.info("Initializing NeuroCognitive Architecture system...")
    config_manager: NCAConfig = state["config_manager"] # Get config from state

    try:
        # Load template configuration if specified
        template_config = {}
        if template:
            template_path = Path(template)
            if not template_path.exists():
                logger.error(f"Template configuration not found: {template}")
                sys.exit(1)
                
            try:
                if template_path.suffix.lower() in ('.yaml', '.yml'):
                    with open(template_path) as f:
                        template_config = yaml.safe_load(f)
                elif template_path.suffix.lower() == '.json':
                    with open(template_path) as f:
                        template_config = json.load(f)
                else:
                    logger.error(f"Unsupported template format: {template_path.suffix}")
                    raise typer.Exit(code=1)
            except Exception as e:
                logger.error(f"Failed to load template: {str(e)}")
                raise typer.Exit(code=1)
        
        # Create default configuration
        default_config = {
            "version": __version__,
            "memory": {
                "working_memory": {
                    "capacity": 7,
                    "decay_rate": 0.1
                },
                "short_term": {
                    "capacity": 100,
                    "retention_period": 3600  # 1 hour in seconds
                },
                "long_term": {
                    "storage_path": "data/long_term",
                    "indexing": "semantic"
                }
            },
            "llm": {
                "default_model": "gpt-3.5-turbo",
                "api_key_env": "NEUROCA_API_KEY",
                "timeout": 30
            },
            "health": {
                "energy_decay_rate": 0.05,
                "rest_recovery_rate": 0.1,
                "critical_threshold": 0.2
            }
        }
        
        # Merge with template if provided
        if template_config:
            # Deep merge the configurations
            def deep_merge(source, destination):
                for key, value in source.items():
                    if isinstance(value, dict):
                        node = destination.setdefault(key, {})
                        deep_merge(value, node)
                    else:
                        destination[key] = value
                return destination
                
            config_data = deep_merge(template_config, default_config)
        else:
            config_data = default_config
        
        # Determine configuration path (config_path from callback is already considered by NCAConfig)
        # Use the path stored in the config manager instance
        config_file_path_str = config_manager.config_path or "config/neuroca.yaml" # Default path if none provided
        config_file = Path(config_file_path_str)

        # Check if already initialized
        if config_file.exists() and not force:
            logger.warning(f"Configuration already exists at {config_file}. Use --force to overwrite.")
            raise typer.Exit(code=1)
            
        # Create directory structure
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create data directories
        data_dirs = [
            Path("data/working_memory"),
            Path("data/short_term"),
            Path("data/long_term"),
            Path("logs")
        ]
        
        for directory in data_dirs:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
        
        # Save configuration using the manager instance
        config_manager.config = config_data
        config_manager.config_path = str(config_file) # Ensure path is updated if default was used
        config_manager.save()
        
        logger.info(f"NCA system initialized successfully. Configuration saved to {config_file}")
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        # Verbosity is handled by logger level set in callback
        # if verbose: logger.exception("Detailed error information:") # Not needed
        raise typer.Exit(code=1)

# --- Import Command Modules ---
# Import sub-apps from the commands directory
from .commands.health import health_app  # Import health commands
from .commands.llm import llm_app  # Import LLM commands
from .commands.memory import memory_app  # Import memory commands

# Add imported sub-apps to the main app
app.add_typer(memory_app)
app.add_typer(health_app)
app.add_typer(llm_app)
# Remove the old inline command definitions below


# --- Run Command ---
# (Keep run command here as it's a top-level command)
@app.command()
def run(
    model: Annotated[Optional[str], typer.Option("--model", "-m", help="LLM model to use for processing.")] = None,
    input_source: Annotated[Optional[str], typer.Option("--input", "-i", help="Input text or file path for processing.")] = None, # Renamed to avoid conflict with built-in
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path for results.")] = None,
    interactive: Annotated[bool, typer.Option("--interactive", help="Run in interactive mode.")] = False,
) -> None:
    """
    Run the NCA system with the specified input and configuration.
    """
    logger.info("Starting NCA processing...")
    config_manager: NCAConfig = state["config_manager"]

    # Determine which model to use
    model_name = model or config_manager.get("llm.default_model", "gpt-3.5-turbo") # Use dot notation
    logger.debug(f"Using model: {model_name}")
    
    # Handle input
    input_text = ""
    if input_source:
        input_path = Path(input_source)
        if input_path.exists() and input_path.is_file():
            try:
                with open(input_path) as f:
                    input_text = f.read()
                logger.debug(f"Loaded input from file: {input_source}")
            except Exception as e:
                logger.error(f"Failed to read input file: {str(e)}")
                raise typer.Exit(code=1)
        else:
            input_text = input_source
            logger.debug("Using direct input text")
    
    # Interactive mode
    if interactive:
        logger.info("Starting interactive session. Type 'exit' or 'quit' to end.")
        console.print(f"[bold]NCA Interactive Mode[/bold] (Model: {model_name})")
        console.print("Type your input and press Enter. Type 'exit' or 'quit' to end the session.")
        
        while True:
            try:
                user_input = console.input("\n[bold cyan]> [/bold cyan]")
                if user_input.lower() in ('exit', 'quit'):
                    break
                
                # This would process the input through the NCA system in a real implementation
                console.print("\n[dim]Processing...[/dim]")
                
                # Simulate processing
                import time
                time.sleep(1.5) # Simulate processing time
                
                # NOTE: Implement call to the actual NCA processing logic here.
                # This should involve initializing the NCA core and passing the user_input.
                # Example: nca_instance = initialize_nca(config_manager.config)
                # Example: response_data = nca_instance.process(user_input)
                
                # NOTE: Replace simulated response with actual result from NCA.
                response = f"NCA processed: {user_input}\n\n[Simulated Response - Model: {model_name}]"
                console.print(f"\n[green]{response}[/green]")
                
            except KeyboardInterrupt:
                console.print("\nSession terminated by user.")
                break
            except Exception as e:
                logger.error(f"Error in interactive session: {str(e)}")
                # Verbosity handled by logger level
                # if verbose: logger.exception("Detailed error information:")
        
        logger.info("Interactive session ended")
        raise typer.Exit() # Exit after interactive session

    # Non-interactive mode requires input
    if not input_text:
        logger.error("No input provided. Use --input option or --interactive mode.")
        raise typer.Exit(code=1)
    
    # Process the input
    logger.info("Processing input...")
    
    # NOTE: Implement call to the actual NCA processing logic here.
    # This should involve initializing the NCA core and passing the input_text.
    # Example: nca_instance = initialize_nca(config_manager.config)
    # Example: result_data = nca_instance.process(input_text)
    
    # NOTE: Replace simulated result with actual result from NCA.
    result = f"NCA processed the input using {model_name} model.\n\n[Simulated Result]"
    result += "This is a simulated response that would normally contain the output from the NCA system."
    
    # Handle output
    if output:
        output_path = Path(output)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(result)
            logger.info(f"Results saved to {output}")
        except Exception as e:
            logger.error(f"Failed to write output file: {str(e)}")
            # Verbosity handled by logger level
            # if verbose: logger.exception("Detailed error information:")
            raise typer.Exit(code=1)
    else:
        # Print to console
        console.print("\n[bold]Processing Results:[/bold]")
        console.print(result)
    
    logger.info("NCA processing completed successfully")

# --- Version Command (already Typer) ---
# Keep the existing Typer version command
@app.command()
def version():
    """Display the current version of NeuroCognitive Architecture."""
    # Use rich print for consistency
    console.print(f"NeuroCognitive Architecture v[bold cyan]{__version__}[/bold cyan]")

# Remove the old hello command if not needed
# @app.command()
# def hello(name: str = typer.Argument("world")):
#     """Say hello to NAME."""
#     print(f"Hello, {name}!")

# --- Main Execution ---
if __name__ == "__main__":
    try:
        app() # Execute the Typer app
    except Exception as e:
        # Log unhandled exceptions using the configured logger
        logger.error(f"Unhandled exception: {str(e)}")
        # logger.debug("Detailed error information:", exc_info=True) # Already handled by RichHandler? Check Typer docs.
        # Exit with error code
        sys.exit(1) # Use sys.exit for consistency
