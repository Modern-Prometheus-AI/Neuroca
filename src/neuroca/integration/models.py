"""
Models Module for NeuroCognitive Architecture (NCA) LLM Integration

This module defines the data models used for LLM integration, providing
structured representations of requests, responses, and configuration.

Classes:
    TokenUsage: Represents token usage statistics for LLM operations
    ProviderConfig: Configuration for an LLM provider
    LLMRequest: Represents a request to an LLM provider
    LLMResponse: Represents a response from an LLM provider
    LLMProvider: Enum of supported LLM providers
    LLMError: Represents an error from an LLM provider
"""

import dataclasses
import enum
import time
from typing import Any, Optional


class ResponseType(enum.Enum):
    """Enumeration of response types from LLMs."""
    TEXT = "text"
    CHAT = "chat"
    EMBEDDING = "embedding"
    FUNCTION_CALL = "function_call"
    TOOL_USE = "tool_use"
    ERROR = "error"


class LLMProvider(enum.Enum):
    """Enumeration of supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    VERTEXAI = "vertexai"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclasses.dataclass
class TokenUsage:
    """
    Token usage statistics for LLM operations.
    
    Attributes:
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total number of tokens used
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary for serialization."""
        return dataclasses.asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, int]) -> 'TokenUsage':
        """Create from dictionary."""
        return cls(**data)


@dataclasses.dataclass
class ProviderConfig:
    """
    Configuration for an LLM provider.
    
    Attributes:
        api_key: API key for authentication
        api_base: Base URL for API requests
        organization_id: Organization ID for shared accounts
        default_model: Default model to use for this provider
        request_timeout: Timeout for API requests
        max_retries: Maximum number of retries for failed requests
        proxy: Optional proxy configuration
        additional_headers: Additional HTTP headers to include
        additional_params: Additional provider-specific parameters
    """
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    organization_id: Optional[str] = None
    default_model: Optional[str] = None
    request_timeout: float = 60.0
    max_retries: int = 3
    proxy: Optional[str] = None
    additional_headers: dict[str, str] = dataclasses.field(default_factory=dict)
    additional_params: dict[str, Any] = dataclasses.field(default_factory=dict)
    
    def to_dict(self, mask_secrets: bool = True) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Args:
            mask_secrets: Whether to mask sensitive fields
        """
        result = dataclasses.asdict(self)
        
        # Mask sensitive fields if requested
        if mask_secrets and self.api_key:
            result["api_key"] = "**********" + self.api_key[-4:] if len(self.api_key) > 4 else "**********"
            
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ProviderConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclasses.dataclass
class LLMRequest:
    """
    Request to an LLM provider.
    
    Attributes:
        provider: Provider name
        model: Model name
        prompt: Text prompt or message content
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        top_p: Top-p sampling parameter
        top_k: Top-k sampling parameter
        presence_penalty: Presence penalty parameter
        frequency_penalty: Frequency penalty parameter
        stop_sequences: Sequences that stop generation
        additional_params: Additional provider-specific parameters
        created_at: Request creation timestamp
    """
    provider: str
    model: Optional[str] = None
    prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop_sequences: Optional[list[str]] = None
    additional_params: dict[str, Any] = dataclasses.field(default_factory=dict)
    created_at: float = dataclasses.field(default_factory=time.time)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return dataclasses.asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LLMRequest':
        """Create from dictionary."""
        return cls(**data)


@dataclasses.dataclass
class LLMResponse:
    """
    Response from an LLM provider.
    
    Attributes:
        provider: Provider name
        model: Model name
        content: Response content
        usage: Token usage statistics
        raw_response: Raw provider response
        metadata: Additional metadata about the response
        cost: Estimated cost of the request
        request: Original request
        created_at: Response creation timestamp
        elapsed_time: Time elapsed during request
    """
    provider: str
    model: str
    content: Any
    raw_response: Optional[Any] = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
    usage: Optional[TokenUsage] = None
    cost: Optional[float] = None
    request: Optional[LLMRequest] = None
    created_at: float = dataclasses.field(default_factory=time.time)
    elapsed_time: Optional[float] = None
    response_type: ResponseType = ResponseType.TEXT
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = dataclasses.asdict(self)
        
        # Handle special types
        if self.usage:
            result["usage"] = self.usage.to_dict()
        if self.request:
            result["request"] = self.request.to_dict()
        if self.response_type:
            result["response_type"] = self.response_type.value
            
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LLMResponse':
        """Create from dictionary."""
        # Handle special types
        if "usage" in data and isinstance(data["usage"], dict):
            data["usage"] = TokenUsage.from_dict(data["usage"])
        if "request" in data and isinstance(data["request"], dict):
            data["request"] = LLMRequest.from_dict(data["request"])
        if "response_type" in data and isinstance(data["response_type"], str):
            data["response_type"] = ResponseType(data["response_type"])
            
        return cls(**data)


@dataclasses.dataclass
class LLMError:
    """
    Error from an LLM provider.
    
    Attributes:
        provider: Provider name
        error_type: Type of error
        message: Error message
        request: Original request
        created_at: Error creation timestamp
        retryable: Whether the request can be retried
    """
    provider: str
    error_type: str
    message: str
    request: Optional[LLMRequest] = None
    created_at: float = dataclasses.field(default_factory=time.time)
    retryable: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = dataclasses.asdict(self)
        
        # Handle special types
        if self.request:
            result["request"] = self.request.to_dict()
            
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LLMError':
        """Create from dictionary."""
        # Handle special types
        if "request" in data and isinstance(data["request"], dict):
            data["request"] = LLMRequest.from_dict(data["request"])
            
        return cls(**data)
