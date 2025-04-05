"""
Anthropic API Adapter for NeuroCognitive Architecture (NCA).

This module provides a robust integration with Anthropic's API services,
enabling the NCA system to leverage Anthropic's language models like Claude.
The adapter handles authentication, request formatting, response parsing,
error handling, and implements retry logic for resilient operation.

Usage:
    ```python
    from neuroca.integration.adapters.anthropic import AnthropicAdapter
    
    # Initialize the adapter with API key
    adapter = AnthropicAdapter(api_key="your_api_key")
    
    # Simple completion
    response = adapter.generate_completion(
        prompt="Explain quantum computing",
        max_tokens=1000
    )
    
    # Chat completion with system prompt and messages
    response = adapter.generate_chat_completion(
        system_prompt="You are a helpful AI assistant",
        messages=[
            {"role": "user", "content": "Tell me about neural networks"}
        ]
    )
    ```

Dependencies:
    - anthropic: Official Anthropic Python client
    - tenacity: For implementing retry logic
    - requests: For API calls if the official client is unavailable
"""

import json
import logging
import time
from enum import Enum
from typing import Optional

import anthropic
from anthropic.types import MessageParam
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from neuroca.integration.adapters.base import AdapterError, LLMAdapter, ModelNotFoundError
from neuroca.integration.schema import (
    ChatCompletionResponse,
    ChatMessage,
    CompletionResponse,
    TokenUsage,
)

# Configure module logger
logger = logging.getLogger(__name__)


class AnthropicModelFamily(str, Enum):
    """Enumeration of supported Anthropic model families."""
    CLAUDE = "claude"
    CLAUDE_INSTANT = "claude-instant"
    CLAUDE_2 = "claude-2"
    CLAUDE_3 = "claude-3"


class AnthropicError(AdapterError):
    """Base exception class for Anthropic adapter errors."""
    pass


class AnthropicAdapter(LLMAdapter):
    """
    Adapter for integrating with Anthropic's API services.
    
    This adapter provides methods to interact with Anthropic's language models,
    handling authentication, request formatting, and response parsing.
    
    Attributes:
        api_key (str): Anthropic API key for authentication
        client (anthropic.Anthropic): Initialized Anthropic client
        default_model (str): Default model to use for completions
        max_retries (int): Maximum number of retries for API calls
        timeout (int): Timeout in seconds for API calls
    """
    
    # Default models for different types of requests
    DEFAULT_COMPLETION_MODEL = "claude-2"
    DEFAULT_CHAT_MODEL = "claude-3-opus-20240229"
    
    # API constants
    API_VERSION = "2023-06-01"  # Update as needed
    
    def __init__(
        self,
        api_key: str,
        default_model: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60,
        organization_id: Optional[str] = None,
    ):
        """
        Initialize the Anthropic adapter.
        
        Args:
            api_key: Anthropic API key for authentication
            default_model: Default model to use (defaults to claude-3-opus)
            max_retries: Maximum number of retries for failed API calls
            timeout: Timeout in seconds for API calls
            organization_id: Optional organization ID for enterprise accounts
            
        Raises:
            AnthropicError: If initialization fails
        """
        self.api_key = api_key
        self.default_model = default_model or self.DEFAULT_CHAT_MODEL
        self.max_retries = max_retries
        self.timeout = timeout
        self.organization_id = organization_id
        
        try:
            # Initialize the Anthropic client
            self.client = anthropic.Anthropic(
                api_key=api_key,
                timeout=timeout,
            )
            logger.info(f"Initialized Anthropic adapter with default model: {self.default_model}")
        except Exception as e:
            error_msg = f"Failed to initialize Anthropic client: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
    
    @retry(
        retry=retry_if_exception_type((anthropic.APIError, anthropic.APITimeoutError, anthropic.RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[list[str]] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Generate a text completion using Anthropic's API.
        
        Args:
            prompt: The prompt to generate completion for
            model: Model to use (defaults to self.default_model)
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter (optional)
            stop_sequences: List of sequences that stop generation
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            CompletionResponse: Structured response with generated text and metadata
            
        Raises:
            AnthropicError: If the API call fails
            ModelNotFoundError: If the specified model is not available
        """
        model = model or self.DEFAULT_COMPLETION_MODEL
        
        # Validate model
        if not self._is_valid_model(model):
            error_msg = f"Model '{model}' is not a valid Anthropic model"
            logger.error(error_msg)
            raise ModelNotFoundError(error_msg)
        
        # Validate parameters
        if temperature < 0 or temperature > 1:
            error_msg = f"Temperature must be between 0 and 1, got {temperature}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if max_tokens < 1:
            error_msg = f"max_tokens must be positive, got {max_tokens}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Prepare request parameters
        request_params = {
            "model": model,
            "prompt": f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}",
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "stop_sequences": stop_sequences or [],
        }
        
        if top_p is not None:
            request_params["top_p"] = top_p
            
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in request_params:
                request_params[key] = value
        
        start_time = time.time()
        logger.debug(f"Sending completion request to Anthropic API: {json.dumps(request_params, default=str)}")
        
        try:
            # Make the API call
            response = self.client.completions.create(**request_params)
            
            # Calculate token usage (Anthropic doesn't provide this directly)
            # This is an estimation
            prompt_tokens = len(prompt) // 4  # Rough estimate
            completion_tokens = len(response.completion) // 4  # Rough estimate
            
            # Construct the response
            completion_response = CompletionResponse(
                text=response.completion,
                model=model,
                usage=TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                ),
                finish_reason=response.stop_reason,
                raw_response=response
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Anthropic completion successful in {elapsed_time:.2f}s using model {model}")
            return completion_response
            
        except anthropic.BadRequestError as e:
            error_msg = f"Bad request to Anthropic API: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except anthropic.AuthenticationError as e:
            error_msg = "Authentication failed with Anthropic API. Check your API key."
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except anthropic.RateLimitError as e:
            error_msg = f"Rate limit exceeded with Anthropic API: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except anthropic.APIError as e:
            error_msg = f"Anthropic API error: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during Anthropic completion: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e

    @retry(
        retry=retry_if_exception_type((anthropic.APIError, anthropic.APITimeoutError, anthropic.RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def generate_chat_completion(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop_sequences: Optional[list[str]] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        Generate a chat completion using Anthropic's API.
        
        Args:
            messages: List of chat messages in the conversation
            model: Model to use (defaults to self.default_model)
            system_prompt: Optional system prompt to guide the model
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter (optional)
            stop_sequences: List of sequences that stop generation
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            ChatCompletionResponse: Structured response with generated message and metadata
            
        Raises:
            AnthropicError: If the API call fails
            ModelNotFoundError: If the specified model is not available
        """
        model = model or self.DEFAULT_CHAT_MODEL
        
        # Validate model
        if not self._is_valid_model(model):
            error_msg = f"Model '{model}' is not a valid Anthropic model"
            logger.error(error_msg)
            raise ModelNotFoundError(error_msg)
        
        # Validate parameters
        if temperature < 0 or temperature > 1:
            error_msg = f"Temperature must be between 0 and 1, got {temperature}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if max_tokens < 1:
            error_msg = f"max_tokens must be positive, got {max_tokens}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages_to_anthropic_format(messages)
        
        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_prompt:
            request_params["system"] = system_prompt
            
        if top_p is not None:
            request_params["top_p"] = top_p
            
        if stop_sequences:
            request_params["stop_sequences"] = stop_sequences
            
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in request_params:
                request_params[key] = value
        
        start_time = time.time()
        logger.debug(f"Sending chat completion request to Anthropic API: {json.dumps(request_params, default=str)}")
        
        try:
            # Make the API call
            response = self.client.messages.create(**request_params)
            
            # Extract content from the response
            content = response.content[0].text if response.content else ""
            
            # Calculate token usage (Anthropic doesn't provide this directly in all responses)
            usage = None
            if hasattr(response, 'usage'):
                usage = TokenUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens
                )
            else:
                # Estimate token usage if not provided
                prompt_tokens = sum(len(msg.content) // 4 for msg in anthropic_messages)  # Rough estimate
                completion_tokens = len(content) // 4  # Rough estimate
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
            
            # Construct the response
            chat_response = ChatCompletionResponse(
                message=ChatMessage(role="assistant", content=content),
                model=model,
                usage=usage,
                finish_reason=response.stop_reason,
                raw_response=response
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Anthropic chat completion successful in {elapsed_time:.2f}s using model {model}")
            return chat_response
            
        except anthropic.BadRequestError as e:
            error_msg = f"Bad request to Anthropic API: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except anthropic.AuthenticationError as e:
            error_msg = "Authentication failed with Anthropic API. Check your API key."
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except anthropic.RateLimitError as e:
            error_msg = f"Rate limit exceeded with Anthropic API: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except anthropic.APIError as e:
            error_msg = f"Anthropic API error: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during Anthropic chat completion: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e

    def _convert_messages_to_anthropic_format(self, messages: list[ChatMessage]) -> list[MessageParam]:
        """
        Convert NCA message format to Anthropic's expected format.
        
        Args:
            messages: List of messages in NCA format
            
        Returns:
            List of messages in Anthropic format
            
        Raises:
            AnthropicError: If message conversion fails
        """
        try:
            anthropic_messages = []
            
            for message in messages:
                # Map NCA roles to Anthropic roles
                role = message.role
                if role == "user":
                    anthropic_role = "user"
                elif role == "assistant":
                    anthropic_role = "assistant"
                elif role == "system":
                    # System messages are handled separately in Anthropic's API
                    continue
                else:
                    # Default to user for unknown roles
                    logger.warning(f"Unknown message role '{role}', defaulting to 'user'")
                    anthropic_role = "user"
                
                anthropic_messages.append({
                    "role": anthropic_role,
                    "content": message.content
                })
            
            return anthropic_messages
        except Exception as e:
            error_msg = f"Failed to convert messages to Anthropic format: {str(e)}"
            logger.error(error_msg)
            raise AnthropicError(error_msg) from e

    def _is_valid_model(self, model: str) -> bool:
        """
        Check if the provided model is valid for Anthropic.
        
        Args:
            model: Model name to validate
            
        Returns:
            bool: True if model is valid, False otherwise
        """
        # List of supported models - update as Anthropic releases new models
        supported_models = [
            # Claude 3 family
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            # Claude 2 family
            "claude-2",
            "claude-2.0",
            "claude-2.1",
            # Claude Instant family
            "claude-instant-1",
            "claude-instant-1.2",
            # Legacy Claude models
            "claude-1",
            "claude-1.3",
            "claude-1.2",
            "claude-1.0",
        ]
        
        # Check if the model is in the supported list
        if model in supported_models:
            return True
            
        # Check if the model starts with a supported family prefix
        return any(model.startswith(family.value) for family in AnthropicModelFamily)

    def get_token_count(self, text: str) -> int:
        """
        Estimate the number of tokens in the given text.
        
        Note: This is an approximation as Anthropic doesn't provide a tokenizer.
        For more accurate counts, consider using tiktoken or a similar library.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            int: Estimated token count
        """
        # Simple approximation: ~4 characters per token
        return len(text) // 4

    def get_model_context_size(self, model: str) -> int:
        """
        Get the maximum context size for the specified model.
        
        Args:
            model: Model name
            
        Returns:
            int: Maximum context size in tokens
            
        Raises:
            ModelNotFoundError: If the model is not recognized
        """
        # Context sizes for Anthropic models (update as needed)
        context_sizes = {
            # Claude 3 family
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            # Claude 2 family
            "claude-2": 100000,
            "claude-2.0": 100000,
            "claude-2.1": 100000,
            # Claude Instant family
            "claude-instant-1": 100000,
            "claude-instant-1.2": 100000,
            # Legacy Claude models
            "claude-1": 100000,
            "claude-1.3": 100000,
            "claude-1.2": 100000,
            "claude-1.0": 100000,
        }
        
        # Check for exact model match
        if model in context_sizes:
            return context_sizes[model]
            
        # Check for model family match
        for family_prefix, size in [
            ("claude-3-opus", 200000),
            ("claude-3-sonnet", 200000),
            ("claude-3-haiku", 200000),
            ("claude-3", 200000),
            ("claude-2", 100000),
            ("claude-instant", 100000),
            ("claude-1", 100000),
            ("claude", 100000),
        ]:
            if model.startswith(family_prefix):
                return size
                
        # If model not found
        error_msg = f"Unknown model: {model}, cannot determine context size"
        logger.error(error_msg)
        raise ModelNotFoundError(error_msg)

    def health_check(self) -> tuple[bool, str]:
        """
        Perform a health check on the Anthropic API connection.
        
        Returns:
            Tuple[bool, str]: (is_healthy, status_message)
        """
        try:
            # Simple API call to check if the connection is working
            # We'll use a minimal prompt to minimize token usage
            self.generate_completion(
                prompt="Hello",
                max_tokens=5,
                temperature=0.0
            )
            return True, "Anthropic API connection is healthy"
        except Exception as e:
            error_msg = f"Anthropic API health check failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg