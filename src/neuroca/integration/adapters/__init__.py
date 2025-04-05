"""
Adapters Module for NeuroCognitive Architecture (NCA)

This module provides the adapter interface and registry for integrating with various
Large Language Models (LLMs). The adapter pattern allows the NCA system to interact
with different LLM providers through a consistent interface, abstracting away the
implementation details of each specific LLM API.

Usage:
    from neuroca.integration.adapters import AdapterRegistry, LLMAdapter
    
    # Get a registered adapter
    openai_adapter = AdapterRegistry.get_adapter("openai")
    
    # Use the adapter
    response = await openai_adapter.generate(prompt="Tell me about cognitive architecture")
    
    # Register a custom adapter
    AdapterRegistry.register_adapter("my_custom_llm", MyCustomAdapter())
"""

import abc
import logging
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union

# Configure module logger
logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Base exception class for adapter-related errors."""
    pass


class AdapterNotFoundError(AdapterError):
    """Exception raised when a requested adapter is not found in the registry."""
    pass


class AdapterRegistrationError(AdapterError):
    """Exception raised when there's an error during adapter registration."""
    pass


class AdapterConfigurationError(AdapterError):
    """Exception raised when an adapter is improperly configured."""
    pass


class AdapterExecutionError(AdapterError):
    """Exception raised when an adapter encounters an error during execution."""
    pass


class ModelCapability(Enum):
    """Enum representing capabilities that LLM models might support."""
    TEXT_GENERATION = auto()
    CHAT_COMPLETION = auto()
    EMBEDDINGS = auto()
    IMAGE_GENERATION = auto()
    AUDIO_TRANSCRIPTION = auto()
    FUNCTION_CALLING = auto()
    TOOL_USE = auto()
    CODE_GENERATION = auto()
    FINE_TUNING = auto()


class LLMAdapter(abc.ABC):
    """
    Abstract base class defining the interface for LLM adapters.
    
    All concrete LLM adapters must implement this interface to ensure
    consistent integration with the NCA system.
    """
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        Returns the name identifier for this adapter.
        
        Returns:
            str: The unique name of the adapter.
        """
        pass
    
    @property
    @abc.abstractmethod
    def capabilities(self) -> Set[ModelCapability]:
        """
        Returns the set of capabilities supported by this adapter.
        
        Returns:
            Set[ModelCapability]: Set of supported capabilities.
        """
        pass
    
    @abc.abstractmethod
    async def generate(self, 
                       prompt: str, 
                       max_tokens: Optional[int] = None,
                       temperature: Optional[float] = None,
                       stop_sequences: Optional[List[str]] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        Generate text based on the provided prompt.
        
        Args:
            prompt (str): The input prompt for text generation.
            max_tokens (Optional[int]): Maximum number of tokens to generate.
            temperature (Optional[float]): Sampling temperature (0.0-2.0).
                Lower values make output more deterministic, higher values more random.
            stop_sequences (Optional[List[str]]): Sequences that will stop generation if encountered.
            **kwargs: Additional model-specific parameters.
            
        Returns:
            Dict[str, Any]: Response containing generated text and metadata.
            
        Raises:
            AdapterExecutionError: If text generation fails.
        """
        pass
    
    @abc.abstractmethod
    async def chat(self,
                   messages: List[Dict[str, str]],
                   max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None,
                   **kwargs) -> Dict[str, Any]:
        """
        Generate a response based on a conversation history.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'.
            max_tokens (Optional[int]): Maximum number of tokens to generate.
            temperature (Optional[float]): Sampling temperature (0.0-2.0).
            **kwargs: Additional model-specific parameters.
            
        Returns:
            Dict[str, Any]: Response containing generated message and metadata.
            
        Raises:
            AdapterExecutionError: If chat completion fails.
        """
        pass
    
    @abc.abstractmethod
    async def embed(self, 
                    text: Union[str, List[str]], 
                    **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings for the provided text.
        
        Args:
            text (Union[str, List[str]]): Text or list of texts to embed.
            **kwargs: Additional model-specific parameters.
            
        Returns:
            Dict[str, Any]: Response containing embeddings and metadata.
            
        Raises:
            AdapterExecutionError: If embedding generation fails.
        """
        pass
    
    def validate_configuration(self) -> bool:
        """
        Validate that the adapter is properly configured.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
            
        Raises:
            AdapterConfigurationError: If configuration validation fails.
        """
        return True


class AdapterRegistry:
    """
    Registry for LLM adapters that provides access to registered adapters.
    
    This class implements the registry pattern to manage and provide access to
    different LLM adapters throughout the application.
    """
    
    _adapters: Dict[str, LLMAdapter] = {}
    _adapter_classes: Dict[str, Type[LLMAdapter]] = {}
    
    @classmethod
    def register_adapter(cls, name: str, adapter: LLMAdapter) -> None:
        """
        Register an adapter instance with the registry.
        
        Args:
            name (str): Name to register the adapter under.
            adapter (LLMAdapter): Adapter instance to register.
            
        Raises:
            AdapterRegistrationError: If registration fails or adapter is invalid.
        """
        if not isinstance(adapter, LLMAdapter):
            error_msg = f"Object {adapter} is not a valid LLMAdapter instance"
            logger.error(error_msg)
            raise AdapterRegistrationError(error_msg)
        
        if name in cls._adapters:
            logger.warning(f"Overwriting existing adapter registration for '{name}'")
            
        try:
            # Validate adapter configuration before registering
            adapter.validate_configuration()
            cls._adapters[name] = adapter
            logger.info(f"Successfully registered adapter '{name}'")
        except AdapterConfigurationError as e:
            error_msg = f"Failed to register adapter '{name}': {str(e)}"
            logger.error(error_msg)
            raise AdapterRegistrationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error registering adapter '{name}': {str(e)}"
            logger.error(error_msg)
            raise AdapterRegistrationError(error_msg) from e
    
    @classmethod
    def register_adapter_class(cls, name: str, adapter_class: Type[LLMAdapter]) -> None:
        """
        Register an adapter class with the registry for later instantiation.
        
        Args:
            name (str): Name to register the adapter class under.
            adapter_class (Type[LLMAdapter]): Adapter class to register.
            
        Raises:
            AdapterRegistrationError: If registration fails or class is invalid.
        """
        if not issubclass(adapter_class, LLMAdapter):
            error_msg = f"Class {adapter_class} is not a valid LLMAdapter subclass"
            logger.error(error_msg)
            raise AdapterRegistrationError(error_msg)
            
        if name in cls._adapter_classes:
            logger.warning(f"Overwriting existing adapter class registration for '{name}'")
            
        cls._adapter_classes[name] = adapter_class
        logger.info(f"Successfully registered adapter class '{name}'")
    
    @classmethod
    def get_adapter(cls, name: str) -> LLMAdapter:
        """
        Get a registered adapter by name.
        
        Args:
            name (str): Name of the adapter to retrieve.
            
        Returns:
            LLMAdapter: The requested adapter instance.
            
        Raises:
            AdapterNotFoundError: If no adapter is registered with the given name.
        """
        if name not in cls._adapters:
            error_msg = f"No adapter registered with name '{name}'"
            logger.error(error_msg)
            raise AdapterNotFoundError(error_msg)
            
        logger.debug(f"Retrieved adapter '{name}'")
        return cls._adapters[name]
    
    @classmethod
    def create_adapter(cls, name: str, **kwargs) -> LLMAdapter:
        """
        Create and register an adapter instance from a registered adapter class.
        
        Args:
            name (str): Name of the adapter class to instantiate.
            **kwargs: Arguments to pass to the adapter constructor.
            
        Returns:
            LLMAdapter: The newly created adapter instance.
            
        Raises:
            AdapterNotFoundError: If no adapter class is registered with the given name.
            AdapterRegistrationError: If adapter creation or registration fails.
        """
        if name not in cls._adapter_classes:
            error_msg = f"No adapter class registered with name '{name}'"
            logger.error(error_msg)
            raise AdapterNotFoundError(error_msg)
            
        try:
            adapter_class = cls._adapter_classes[name]
            adapter = adapter_class(**kwargs)
            
            # Register the new adapter instance
            instance_name = kwargs.get('instance_name', name)
            cls.register_adapter(instance_name, adapter)
            
            logger.info(f"Created and registered adapter instance '{instance_name}' from class '{name}'")
            return adapter
        except Exception as e:
            error_msg = f"Failed to create adapter from class '{name}': {str(e)}"
            logger.error(error_msg)
            raise AdapterRegistrationError(error_msg) from e
    
    @classmethod
    def list_adapters(cls) -> List[str]:
        """
        List all registered adapter names.
        
        Returns:
            List[str]: List of registered adapter names.
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def list_adapter_classes(cls) -> List[str]:
        """
        List all registered adapter class names.
        
        Returns:
            List[str]: List of registered adapter class names.
        """
        return list(cls._adapter_classes.keys())
    
    @classmethod
    def unregister_adapter(cls, name: str) -> None:
        """
        Unregister an adapter from the registry.
        
        Args:
            name (str): Name of the adapter to unregister.
            
        Raises:
            AdapterNotFoundError: If no adapter is registered with the given name.
        """
        if name not in cls._adapters:
            error_msg = f"Cannot unregister: no adapter registered with name '{name}'"
            logger.error(error_msg)
            raise AdapterNotFoundError(error_msg)
            
        del cls._adapters[name]
        logger.info(f"Unregistered adapter '{name}'")
    
    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered adapters and adapter classes."""
        cls._adapters.clear()
        cls._adapter_classes.clear()
        logger.info("Cleared adapter registry")