"""
NeuroCognitive Architecture (NCA) - Integration Module

This module provides the integration layer between the NeuroCognitive Architecture
and various Large Language Models (LLMs). It handles the communication, data
transformation, and context management required to effectively utilize LLMs within
the NCA framework.

The integration module is responsible for:
1. Providing a unified interface to different LLM providers
2. Managing API connections and authentication
3. Transforming NCA internal representations to LLM-compatible formats
4. Processing and interpreting LLM responses
5. Implementing fallback and retry mechanisms
6. Monitoring and logging LLM interactions

Usage:
    from neuroca.integration import LLMIntegrationManager
    
    # Initialize the integration manager with configuration
    llm_manager = LLMIntegrationManager(config)
    
    # Send a query to the default LLM
    response = await llm_manager.query("What is the capital of France?")
    
    # Or specify a particular LLM provider
    response = await llm_manager.query(
        "Explain quantum computing",
        provider="openai",
        model="gpt-4"
    )

This module is thread-safe and designed for both synchronous and asynchronous usage.
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any

# Set up module-level logger
logger = logging.getLogger(__name__)

# Version information
__version__ = "0.1.0"

# Define module-level constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
SUPPORTED_PROVIDERS = ["openai", "anthropic", "cohere", "huggingface", "local"]

# Import all provider modules dynamically
_provider_modules = {}

def _import_providers():
    """
    Dynamically import all provider modules from the providers package.
    This allows for extensibility and plugin-like architecture for LLM providers.
    """
    try:
        # Import the providers subpackage
        from . import providers
        
        # Get the path to the providers package
        providers_path = Path(providers.__file__).parent
        
        # Iterate through all modules in the providers package
        for _, name, is_pkg in pkgutil.iter_modules([str(providers_path)]):
            if not is_pkg:  # Only import modules, not subpackages
                try:
                    module = importlib.import_module(f".providers.{name}", package=__name__.rsplit(".", 1)[0])
                    _provider_modules[name] = module
                    logger.debug(f"Successfully imported LLM provider module: {name}")
                except ImportError as e:
                    logger.warning(f"Failed to import LLM provider module {name}: {str(e)}")
    except ImportError:
        logger.warning("Could not import providers package. LLM integration may be limited.")

# Import core components
try:
    from .exceptions import (
        AuthenticationError,
        ContextLengthExceededError,
        InvalidRequestError,
        LLMIntegrationError,
        ModelNotAvailableError,
        ProviderNotFoundError,
        RateLimitError,
    )
    from .manager import LLMIntegrationManager
    from .models import LLMError, LLMProvider, LLMRequest, LLMResponse, ProviderConfig, TokenUsage
    from .utils import count_tokens, create_embedding, format_prompt, parse_response, sanitize_input
    
    # Initialize provider modules
    _import_providers()
    
    # Export public API
    __all__ = [
        # Main classes
        "LLMIntegrationManager",
        
        # Models
        "LLMRequest",
        "LLMResponse",
        "LLMProvider",
        "LLMError",
        "ProviderConfig",
        "TokenUsage",
        
        # Exceptions
        "LLMIntegrationError",
        "ProviderNotFoundError",
        "AuthenticationError",
        "RateLimitError",
        "ContextLengthExceededError",
        "ModelNotAvailableError",
        "InvalidRequestError",
        
        # Utility functions
        "count_tokens",
        "format_prompt",
        "parse_response",
        "sanitize_input",
        "create_embedding",
        
        # Constants
        "SUPPORTED_PROVIDERS",
        "DEFAULT_TIMEOUT",
        "MAX_RETRIES"
    ]
    
except ImportError as e:
    logger.error(f"Failed to import core integration components: {str(e)}")
    logger.warning("The integration module may not function correctly.")
    __all__ = []

# Provide version information
def get_version() -> str:
    """
    Returns the current version of the integration module.
    
    Returns:
        str: The version string in semantic versioning format.
    """
    return __version__

def get_supported_providers() -> list[str]:
    """
    Returns a list of all supported LLM providers.
    
    Returns:
        List[str]: A list of provider identifiers that can be used with the integration module.
    """
    return SUPPORTED_PROVIDERS.copy()

def get_provider_info(provider_name: str) -> dict[str, Any]:
    """
    Get detailed information about a specific provider.
    
    Args:
        provider_name (str): The name of the provider to get information for.
        
    Returns:
        Dict[str, Any]: A dictionary containing provider details including
                        supported models, features, and configuration options.
                        
    Raises:
        ProviderNotFoundError: If the specified provider is not supported.
    """
    if provider_name not in SUPPORTED_PROVIDERS:
        from .exceptions import ProviderNotFoundError
        raise ProviderNotFoundError(f"Provider '{provider_name}' is not supported")
    
    if provider_name in _provider_modules:
        provider_module = _provider_modules[provider_name]
        if hasattr(provider_module, "get_provider_info"):
            return provider_module.get_provider_info()
    
    # Return basic info if detailed info is not available
    return {
        "name": provider_name,
        "supported": True,
        "models": [],
        "features": [],
        "requires_api_key": True
    }

# Initialization code that runs when the module is imported
logger.debug(f"Initializing NeuroCognitive Architecture Integration Module v{__version__}")