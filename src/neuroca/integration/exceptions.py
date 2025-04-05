"""
Exceptions Module for NeuroCognitive Architecture (NCA) LLM Integration

This module defines the exception classes used by the LLM integration components.
These exceptions provide a structured way to handle and report errors that may
occur during LLM operations.

Usage:
    try:
        response = await llm_manager.query("What is cognitive architecture?")
    except ProviderNotFoundError:
        # Handle provider not found error
    except RateLimitError:
        # Handle rate limit error
    except LLMIntegrationError as e:
        # Handle general integration error
"""

class LLMIntegrationError(Exception):
    """Base exception class for all LLM integration errors."""
    
    def __init__(self, message: str, *args):
        super().__init__(message, *args)
        self.message = message


class ProviderNotFoundError(LLMIntegrationError):
    """Exception raised when a requested LLM provider is not found."""
    pass


class ModelNotAvailableError(LLMIntegrationError):
    """Exception raised when a requested model is not available."""
    pass


class AuthenticationError(LLMIntegrationError):
    """Exception raised when authentication with the LLM provider fails."""
    pass


class RateLimitError(LLMIntegrationError):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: float = None, *args):
        super().__init__(message, *args)
        self.retry_after = retry_after


class ContextLengthExceededError(LLMIntegrationError):
    """Exception raised when the context length is exceeded."""
    
    def __init__(self, message: str, max_tokens: int = None, actual_tokens: int = None, *args):
        super().__init__(message, *args)
        self.max_tokens = max_tokens
        self.actual_tokens = actual_tokens


class InvalidRequestError(LLMIntegrationError):
    """Exception raised when the request to the LLM provider is invalid."""
    pass


class ProviderAPIError(LLMIntegrationError):
    """Exception raised when the LLM provider API returns an error."""
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None, *args):
        super().__init__(message, *args)
        self.status_code = status_code
        self.response_body = response_body


class ProviderTimeoutError(LLMIntegrationError):
    """Exception raised when a request to the LLM provider times out."""
    pass


class ProviderConnectionError(LLMIntegrationError):
    """Exception raised when connection to the LLM provider fails."""
    pass


class ResponseParsingError(LLMIntegrationError):
    """Exception raised when parsing the response from the LLM provider fails."""
    pass


class ConfigurationError(LLMIntegrationError):
    """Exception raised when there is an error in the configuration."""
    pass


class ResourceExhaustedError(LLMIntegrationError):
    """Exception raised when a resource (e.g., quota, memory) is exhausted."""
    pass


class FeatureNotSupportedError(LLMIntegrationError):
    """Exception raised when a requested feature is not supported."""
    pass


class MemoryContextError(LLMIntegrationError):
    """Exception raised when there is an error with memory context integration."""
    pass


class HealthAwarenessError(LLMIntegrationError):
    """Exception raised when there is an error with health state adaptation."""
    pass


class GoalContextError(LLMIntegrationError):
    """Exception raised when there is an error with goal-directed context integration."""
    pass


class AdapterExecutionError(LLMIntegrationError):
    """Exception raised when an adapter encounters an error during execution."""
    
    def __init__(self, message: str, provider: str = None, model: str = None, *args):
        super().__init__(message, *args)
        self.provider = provider
        self.model = model
