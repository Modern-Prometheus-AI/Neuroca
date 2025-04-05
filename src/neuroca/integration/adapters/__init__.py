"""
Adapters Module for NeuroCognitive Architecture (NCA)

This module provides the adapter interface and registry for integrating with various
Large Language Models (LLMs). The adapter pattern allows the NCA system to interact
with different LLM providers through a consistent interface, abstracting away the
implementation details of each specific LLM API.

Usage:
    from neuroca.integration.adapters import AdapterRegistry, BaseAdapter

    # Get a registered adapter class
    openai_adapter_cls = AdapterRegistry.get_adapter_class("openai")
    # Instantiate (assuming config is loaded)
    # openai_adapter = openai_adapter_cls(config=provider_config)

    # Or create and register instance directly if registry manages instances
    # openai_adapter = AdapterRegistry.create_adapter("openai", **provider_config)

    # Use the adapter
    # response = await openai_adapter.generate(prompt="Tell me about cognitive architecture")

    # Register a custom adapter class
    # AdapterRegistry.register_adapter_class("my_custom_llm", MyCustomAdapter)
"""

import logging
from enum import Enum

# Configure module logger
logger = logging.getLogger(__name__)

# --- Import concrete adapter implementations ---
# Attempt to import adapters, handle potential ImportError if dependencies aren't installed
try:
    from .openai import OpenAIAdapter
except ImportError:
    OpenAIAdapter = None
    logger.debug("OpenAI adapter not available (openai package likely not installed)")

try:
    from .anthropic import AnthropicAdapter
except ImportError:
    AnthropicAdapter = None
    logger.debug("Anthropic adapter not available (anthropic package likely not installed)")

try:
    from .vertexai import VertexAIAdapter
except ImportError:
    VertexAIAdapter = None
    logger.debug("VertexAI adapter not available (google-cloud-aiplatform package likely not installed)")

try:
    from .ollama import OllamaAdapter
except ImportError:
    OllamaAdapter = None
    logger.debug("Ollama adapter not available (aiohttp package likely not installed)")

# --- Import Base Class, Registry, and Core Exceptions/Enums from base.py ---
# This centralizes the core definitions.
try:
    from .base import (
        AdapterConfigurationError,
        AdapterError,
        AdapterExecutionError,
        AdapterNotFoundError,
        AdapterRegistry,
        BaseAdapter,
        LLMResponse,  # Assuming LLMResponse is also defined in base or models
        ModelCapability,
        ResponseType,  # Assuming ResponseType is also defined in base or models
    )
except ImportError as e:
    logger.error(f"Failed to import base adapter components from .base: {e}. Adapters may not function correctly.")
    # Define minimal placeholders if base import fails to avoid crashing later imports
    class BaseAdapter: pass
    class AdapterRegistry:
        @classmethod
        def register_adapter_class(cls, name, adapter_class): pass # No-op
        @classmethod
        def get_adapter_class(cls, name): return None
        @classmethod
        def list_adapter_classes(cls): return []
    class AdapterError(Exception): pass
    class AdapterNotFoundError(AdapterError): pass
    class AdapterConfigurationError(AdapterError): pass
    class AdapterExecutionError(AdapterError): pass
    class ModelCapability(Enum): pass
    class LLMResponse: pass
    class ResponseType(Enum): pass

# --- Automatically register available built-in adapters ---
# Ensure AdapterRegistry was imported successfully before trying to use it
if 'AdapterRegistry' in globals() and hasattr(AdapterRegistry, 'register_adapter_class'):
    if OpenAIAdapter:
        AdapterRegistry.register_adapter_class("openai", OpenAIAdapter)
    if AnthropicAdapter:
        AdapterRegistry.register_adapter_class("anthropic", AnthropicAdapter)
    if VertexAIAdapter:
        AdapterRegistry.register_adapter_class("vertexai", VertexAIAdapter)
    if OllamaAdapter:
        AdapterRegistry.register_adapter_class("ollama", OllamaAdapter)
else:
    logger.error("AdapterRegistry not available for automatic registration.")


# --- Define public exports for the package ---
__all__ = [
    "BaseAdapter",
    "AdapterRegistry",
    "AdapterError",
    "AdapterNotFoundError",
    "AdapterConfigurationError",
    "AdapterExecutionError",
    "ModelCapability",
    "LLMResponse",
    "ResponseType",
    # Export available adapter classes if they were imported successfully
]

# Dynamically add imported adapters to __all__
if OpenAIAdapter: __all__.append("OpenAIAdapter")
if AnthropicAdapter: __all__.append("AnthropicAdapter")
if VertexAIAdapter: __all__.append("VertexAIAdapter")
if OllamaAdapter: __all__.append("OllamaAdapter")
