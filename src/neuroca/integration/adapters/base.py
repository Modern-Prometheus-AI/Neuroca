"""
Base Adapter Module for LLM Integration.

This module defines the base adapter interface and abstract classes for integrating
with various Large Language Models (LLMs). It provides a standardized way to interact
with different LLM providers while abstracting away the implementation details.

The adapter pattern used here allows the NeuroCognitive Architecture to work with
different LLMs without being tightly coupled to their specific APIs or implementations.

Classes:
    AdapterConfig: Configuration dataclass for LLM adapters
    LLMResponse: Structured response from LLM interactions
    BaseAdapter: Abstract base class for all LLM adapters
    AdapterRegistry: Registry for managing and accessing available adapters

Usage:
    Concrete adapter implementations should inherit from BaseAdapter and implement
    all abstract methods. The AdapterRegistry can be used to register and retrieve
    adapter implementations.

Example:
    ```python
    # Registering a custom adapter
    @AdapterRegistry.register("my_llm")
    class MyLLMAdapter(BaseAdapter):
        # Implementation of abstract methods
        ...

    # Using the registry to get an adapter
    adapter = AdapterRegistry.get_adapter("my_llm", config=my_config)
    response = await adapter.generate("Tell me about cognitive architectures")
    ```
"""

import abc
import asyncio
import dataclasses
import enum
import json
import logging
import time
import typing
from typing import Any, ClassVar, Optional, Union

logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Base exception class for all adapter-related errors."""
    pass


class ConfigurationError(AdapterError):
    """Exception raised for errors in the adapter configuration."""
    pass


class AuthenticationError(AdapterError):
    """Exception raised for authentication failures with the LLM provider."""
    pass


class RateLimitError(AdapterError):
    """Exception raised when LLM provider rate limits are exceeded."""
    pass


class ServiceUnavailableError(AdapterError):
    """Exception raised when the LLM service is unavailable."""
    pass


class InvalidRequestError(AdapterError):
    """Exception raised for invalid requests to the LLM provider."""
    pass


class TokenLimitExceededError(AdapterError):
    """Exception raised when the token limit is exceeded."""
    pass


class ResponseFormatError(AdapterError):
    """Exception raised when the LLM response cannot be properly parsed."""
    pass


class ModelNotFoundError(AdapterError):
    """Exception raised when the requested model is not found."""
    pass


class AdapterNotFoundError(AdapterError):
    """Exception raised when a requested adapter is not found in the registry."""
    pass


class ResponseType(enum.Enum):
    """Enumeration of possible response types from LLMs."""
    TEXT = "text"
    JSON = "json"
    CHAT = "chat"
    EMBEDDING = "embedding"
    FUNCTION_CALL = "function_call"
    ERROR = "error"


@dataclasses.dataclass
class AdapterConfig:
    """
    Configuration for LLM adapters.
    
    This dataclass holds all necessary configuration parameters for initializing
    and operating an LLM adapter. It provides a standardized way to configure
    different adapters with their specific requirements.
    
    Attributes:
        model_name (str): Name of the LLM model to use
        api_key (Optional[str]): API key for authentication with the LLM provider
        api_base (Optional[str]): Base URL for the LLM API
        timeout (float): Timeout in seconds for API calls
        max_retries (int): Maximum number of retries for failed API calls
        retry_delay (float): Delay between retries in seconds
        temperature (float): Sampling temperature for generation (0.0 to 1.0)
        max_tokens (Optional[int]): Maximum tokens to generate in responses
        top_p (float): Nucleus sampling parameter (0.0 to 1.0)
        top_k (Optional[int]): Top-k sampling parameter
        presence_penalty (float): Presence penalty for token generation
        frequency_penalty (float): Frequency penalty for token generation
        stop_sequences (Optional[List[str]]): Sequences that stop generation
        extra_params (Dict[str, Any]): Additional model-specific parameters
    """
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    top_k: Optional[int] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    stop_sequences: Optional[list[str]] = None
    extra_params: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.model_name:
            raise ConfigurationError("model_name must be specified")
        
        if self.temperature < 0.0 or self.temperature > 1.0:
            raise ConfigurationError("temperature must be between 0.0 and 1.0")
        
        if self.top_p < 0.0 or self.top_p > 1.0:
            raise ConfigurationError("top_p must be between 0.0 and 1.0")
        
        if self.timeout <= 0:
            raise ConfigurationError("timeout must be positive")
        
        if self.max_retries < 0:
            raise ConfigurationError("max_retries cannot be negative")
        
        if self.retry_delay < 0:
            raise ConfigurationError("retry_delay cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary, excluding sensitive information."""
        config_dict = dataclasses.asdict(self)
        # Remove sensitive information
        if 'api_key' in config_dict:
            config_dict['api_key'] = '***' if config_dict['api_key'] else None
        return config_dict


@dataclasses.dataclass
class LLMResponse:
    """
    Structured response from LLM interactions.
    
    This dataclass encapsulates the response from an LLM, providing a standardized
    format regardless of the underlying LLM provider.
    
    Attributes:
        content (Any): The primary content of the response
        response_type (ResponseType): Type of the response
        model_name (str): Name of the model that generated the response
        usage (Dict[str, int]): Token usage statistics
        raw_response (Optional[Any]): The raw, unprocessed response from the LLM
        metadata (Dict[str, Any]): Additional metadata about the response
        finish_reason (Optional[str]): Reason why the LLM stopped generating
        created_at (float): Timestamp when the response was created
    """
    content: Any
    response_type: ResponseType
    model_name: str
    usage: dict[str, int]
    raw_response: Optional[Any] = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
    finish_reason: Optional[str] = None
    created_at: float = dataclasses.field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary for serialization."""
        result = dataclasses.asdict(self)
        result['response_type'] = self.response_type.value
        # Handle non-serializable objects in raw_response
        if 'raw_response' in result and result['raw_response'] is not None:
            try:
                # Test if it's JSON serializable
                json.dumps(result['raw_response'])
            except (TypeError, OverflowError):
                # If not serializable, convert to string representation
                result['raw_response'] = str(result['raw_response'])
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LLMResponse':
        """Create an LLMResponse instance from a dictionary."""
        if 'response_type' in data and isinstance(data['response_type'], str):
            data['response_type'] = ResponseType(data['response_type'])
        return cls(**data)

    def is_error(self) -> bool:
        """Check if the response represents an error."""
        return self.response_type == ResponseType.ERROR


class BaseAdapter(abc.ABC):
    """
    Abstract base class for all LLM adapters.
    
    This class defines the interface that all concrete LLM adapters must implement.
    It provides common functionality and enforces a consistent API across different
    LLM integrations.
    
    Attributes:
        config (AdapterConfig): Configuration for the adapter
        name (ClassVar[str]): Name identifier for the adapter
    """
    name: ClassVar[str] = "base"
    
    def __init__(self, config: AdapterConfig):
        """
        Initialize the adapter with the provided configuration.
        
        Args:
            config: Configuration for the adapter
            
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        self.config = config
        self.validate_config()
        self._setup_logging()
        logger.info(f"Initialized {self.__class__.__name__} adapter with model: {config.model_name}")

    def _setup_logging(self):
        """Configure adapter-specific logging."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def validate_config(self):
        """
        Validate that the configuration is suitable for this adapter.
        
        Raises:
            ConfigurationError: If the configuration is invalid for this adapter
        """
        # Base validation is handled by AdapterConfig.__post_init__
        # Subclasses should override to add adapter-specific validation
        pass

    @abc.abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate a text response from the LLM based on the provided prompt.
        
        Args:
            prompt: The text prompt to send to the LLM
            **kwargs: Additional parameters to override configuration
            
        Returns:
            LLMResponse containing the generated text
            
        Raises:
            AdapterError: If an error occurs during generation
        """
        pass

    @abc.abstractmethod
    async def generate_chat(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        """
        Generate a response from the LLM based on a conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters to override configuration
            
        Returns:
            LLMResponse containing the generated response
            
        Raises:
            AdapterError: If an error occurs during generation
        """
        pass

    @abc.abstractmethod
    async def generate_embedding(self, text: Union[str, list[str]], **kwargs) -> LLMResponse:
        """
        Generate embeddings for the provided text(s).
        
        Args:
            text: Single text or list of texts to embed
            **kwargs: Additional parameters to override configuration
            
        Returns:
            LLMResponse containing the embeddings
            
        Raises:
            AdapterError: If an error occurs during embedding generation
        """
        pass

    @abc.abstractmethod
    async def generate_with_functions(
        self, 
        messages: list[dict[str, str]], 
        functions: list[dict[str, Any]], 
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response that may include function calls.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            functions: List of function definitions the LLM can call
            **kwargs: Additional parameters to override configuration
            
        Returns:
            LLMResponse containing the generated response or function call
            
        Raises:
            AdapterError: If an error occurs during generation
        """
        pass

    async def _execute_with_retry(
        self, 
        operation: typing.Callable[[], typing.Awaitable[Any]], 
        max_retries: Optional[int] = None, 
        retry_delay: Optional[float] = None
    ) -> Any:
        """
        Execute an async operation with retry logic.
        
        Args:
            operation: Async callable to execute
            max_retries: Maximum number of retries (defaults to config value)
            retry_delay: Delay between retries in seconds (defaults to config value)
            
        Returns:
            Result of the operation
            
        Raises:
            AdapterError: If all retries fail
        """
        max_retries = max_retries if max_retries is not None else self.config.max_retries
        retry_delay = retry_delay if retry_delay is not None else self.config.retry_delay
        
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                return await operation()
            except RateLimitError as e:
                last_error = e
                wait_time = retry_delay * (2 ** retries)  # Exponential backoff
                self.logger.warning(
                    f"Rate limit exceeded. Retrying in {wait_time:.2f}s ({retries}/{max_retries})"
                )
            except (ServiceUnavailableError, ConnectionError) as e:
                last_error = e
                wait_time = retry_delay * (2 ** retries)  # Exponential backoff
                self.logger.warning(
                    f"Service unavailable. Retrying in {wait_time:.2f}s ({retries}/{max_retries})"
                )
            except Exception as e:
                # Don't retry other types of errors
                self.logger.error(f"Operation failed: {str(e)}")
                raise
            
            retries += 1
            if retries <= max_retries:
                await asyncio.sleep(wait_time)
        
        self.logger.error(f"Operation failed after {max_retries} retries: {str(last_error)}")
        raise last_error

    def get_merged_params(self, **kwargs) -> dict[str, Any]:
        """
        Merge configuration with provided parameters.
        
        Args:
            **kwargs: Parameters to override configuration
            
        Returns:
            Dictionary of merged parameters
        """
        # Start with the configuration parameters
        params = {
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        
        # Add optional parameters if they exist in config
        if self.config.max_tokens is not None:
            params["max_tokens"] = self.config.max_tokens
        if self.config.top_k is not None:
            params["top_k"] = self.config.top_k
        if self.config.stop_sequences is not None:
            params["stop"] = self.config.stop_sequences
        if self.config.presence_penalty != 0.0:
            params["presence_penalty"] = self.config.presence_penalty
        if self.config.frequency_penalty != 0.0:
            params["frequency_penalty"] = self.config.frequency_penalty
            
        # Add any extra parameters from config
        params.update(self.config.extra_params)
        
        # Override with any provided kwargs
        params.update(kwargs)
        
        return params

    def __str__(self) -> str:
        """String representation of the adapter."""
        return f"{self.__class__.__name__}(model={self.config.model_name})"

    def __repr__(self) -> str:
        """Detailed string representation of the adapter."""
        return f"{self.__class__.__name__}(config={self.config})"


class AdapterRegistry:
    """
    Registry for managing and accessing available LLM adapters.
    
    This class provides a centralized registry for adapter implementations,
    allowing them to be registered, discovered, and instantiated by name.
    """
    _adapters: dict[str, type[BaseAdapter]] = {}
    
    @classmethod
    def register(cls, name: Optional[str] = None):
        """
        Decorator to register an adapter class in the registry.
        
        Args:
            name: Optional name for the adapter (defaults to adapter's name attribute)
            
        Returns:
            Decorator function
            
        Example:
            ```python
            @AdapterRegistry.register("openai")
            class OpenAIAdapter(BaseAdapter):
                name = "openai"
                # Implementation...
            ```
        """
        def decorator(adapter_cls: type[BaseAdapter]) -> type[BaseAdapter]:
            adapter_name = name or adapter_cls.name
            if not adapter_name:
                raise ValueError("Adapter must have a name attribute or provide a name parameter")
            
            if adapter_name in cls._adapters:
                logger.warning(f"Overwriting existing adapter registration for '{adapter_name}'")
                
            cls._adapters[adapter_name] = adapter_cls
            logger.debug(f"Registered adapter '{adapter_name}'")
            return adapter_cls
        
        return decorator
    
    @classmethod
    def get_adapter_class(cls, name: str) -> type[BaseAdapter]:
        """
        Get an adapter class by name.
        
        Args:
            name: Name of the adapter to retrieve
            
        Returns:
            The adapter class
            
        Raises:
            AdapterNotFoundError: If no adapter with the given name is registered
        """
        if name not in cls._adapters:
            raise AdapterNotFoundError(f"No adapter registered with name '{name}'")
        return cls._adapters[name]
    
    @classmethod
    def get_adapter(cls, name: str, config: AdapterConfig) -> BaseAdapter:
        """
        Get an instantiated adapter by name.
        
        Args:
            name: Name of the adapter to retrieve
            config: Configuration for the adapter
            
        Returns:
            An instantiated adapter
            
        Raises:
            AdapterNotFoundError: If no adapter with the given name is registered
        """
        adapter_cls = cls.get_adapter_class(name)
        return adapter_cls(config)
    
    @classmethod
    def list_adapters(cls) -> list[str]:
        """
        List all registered adapter names.
        
        Returns:
            List of registered adapter names
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister an adapter by name.
        
        Args:
            name: Name of the adapter to unregister
            
        Raises:
            AdapterNotFoundError: If no adapter with the given name is registered
        """
        if name not in cls._adapters:
            raise AdapterNotFoundError(f"No adapter registered with name '{name}'")
        del cls._adapters[name]
        logger.debug(f"Unregistered adapter '{name}'")