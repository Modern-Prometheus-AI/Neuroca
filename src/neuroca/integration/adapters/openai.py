"""
OpenAI Adapter for NeuroCognitive Architecture (NCA)

This module provides a robust adapter for integrating OpenAI's language models
with the NeuroCognitive Architecture system. It handles authentication, request
formatting, response parsing, error handling, and implements retry logic for
resilient operation in production environments.

The adapter supports all OpenAI models and provides methods for:
- Text completion
- Chat completion
- Embeddings generation
- Function calling
- Tool use

Usage:
    from neuroca.integration.adapters.openai import OpenAIAdapter
    
    # Initialize with API key
    adapter = OpenAIAdapter(api_key="your-api-key")
    
    # Or initialize with environment variable OPENAI_API_KEY
    adapter = OpenAIAdapter()
    
    # Generate a completion
    response = adapter.complete(
        prompt="Translate the following English text to French: 'Hello, world!'",
        model="gpt-4"
    )
    
    # Generate a chat completion
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the capital of France?"}
    ]
    response = adapter.chat_complete(messages=messages, model="gpt-3.5-turbo")
"""

import json
import logging
import os
from enum import Enum
from typing import Any, Optional, Union

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from neuroca.integration.adapters.base import BaseModelAdapter
from neuroca.integration.exceptions import (
    AdapterAuthenticationError,
    AdapterConnectionError,
    AdapterRateLimitError,
    AdapterRequestError,
    AdapterResponseError,
    AdapterTimeoutError,
    ModelNotFoundError,
)

# Configure module logger
logger = logging.getLogger(__name__)


class OpenAIEndpoints(str, Enum):
    """Enum for OpenAI API endpoints."""
    COMPLETIONS = "completions"
    CHAT_COMPLETIONS = "chat/completions"
    EMBEDDINGS = "embeddings"
    MODELS = "models"


class OpenAIAdapter(BaseModelAdapter):
    """
    Adapter for OpenAI's API, providing a standardized interface for the NCA system
    to interact with OpenAI's language models.
    
    This adapter handles:
    - Authentication with OpenAI
    - Request formatting and validation
    - Response parsing and error handling
    - Rate limiting and retry logic
    - Logging and monitoring
    
    Attributes:
        api_key (str): OpenAI API key for authentication
        api_base (str): Base URL for OpenAI API
        api_version (str): API version to use
        organization (str): OpenAI organization ID
        timeout (float): Request timeout in seconds
        max_retries (int): Maximum number of retries for failed requests
        http_client (httpx.Client): HTTP client for making requests
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: str = "https://api.openai.com/v1",
        api_version: Optional[str] = None,
        organization: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        Initialize the OpenAI adapter.
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY env var.
            api_base: Base URL for the OpenAI API.
            api_version: API version to use.
            organization: OpenAI organization ID.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            
        Raises:
            AdapterAuthenticationError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise AdapterAuthenticationError(
                "OpenAI API key not provided. Set it during initialization or "
                "via the OPENAI_API_KEY environment variable."
            )
        
        self.api_base = api_base
        self.api_version = api_version
        self.organization = organization
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize HTTP client with default headers
        self.http_client = httpx.Client(
            timeout=timeout,
            headers=self._get_default_headers(),
        )
        
        logger.debug("OpenAI adapter initialized with API base: %s", api_base)
    
    def _get_default_headers(self) -> dict[str, str]:
        """
        Get default headers for API requests.
        
        Returns:
            Dict containing the default headers for OpenAI API requests.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
            
        if self.api_version:
            headers["OpenAI-Version"] = self.api_version
            
        return headers
    
    def _build_url(self, endpoint: Union[str, OpenAIEndpoints]) -> str:
        """
        Build the full URL for an API endpoint.
        
        Args:
            endpoint: API endpoint to access.
            
        Returns:
            Full URL for the specified endpoint.
        """
        if isinstance(endpoint, OpenAIEndpoints):
            endpoint = endpoint.value
            
        return f"{self.api_base}/{endpoint}"
    
    @retry(
        retry=retry_if_exception_type((
            httpx.ConnectTimeout, 
            httpx.ReadTimeout,
            AdapterRateLimitError,
            httpx.ConnectError
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying request after error: {retry_state.outcome.exception()}, "
            f"attempt {retry_state.attempt_number}"
        )
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: Union[str, OpenAIEndpoints], 
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the OpenAI API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to access
            data: Request payload
            params: Query parameters
            
        Returns:
            Parsed JSON response from the API
            
        Raises:
            AdapterConnectionError: For network connectivity issues
            AdapterTimeoutError: When the request times out
            AdapterRateLimitError: When rate limited by the API
            AdapterAuthenticationError: For authentication issues
            AdapterRequestError: For invalid requests
            AdapterResponseError: For unexpected API responses
        """
        url = self._build_url(endpoint)
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method.upper() == "GET":
                response = self.http_client.get(url, params=params)
            elif method.upper() == "POST":
                response = self.http_client.post(url, json=data, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle HTTP errors
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 30))
                logger.warning(f"Rate limited by OpenAI API. Retry after {retry_after}s")
                raise AdapterRateLimitError(
                    f"OpenAI API rate limit exceeded. Retry after {retry_after} seconds.",
                    retry_after=retry_after
                )
                
            if response.status_code == 401:
                logger.error("Authentication error with OpenAI API")
                raise AdapterAuthenticationError(
                    "Authentication failed. Check your OpenAI API key."
                )
                
            if response.status_code == 404:
                if "model" in data and "models" in url:
                    logger.error(f"Model not found: {data.get('model')}")
                    raise ModelNotFoundError(f"Model not found: {data.get('model')}")
                logger.error(f"Resource not found: {url}")
                raise AdapterRequestError(f"Resource not found: {url}")
                
            if response.status_code >= 400:
                error_data = response.json() if response.content else {"error": {"message": "Unknown error"}}
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"API error: {error_message} (Status: {response.status_code})")
                raise AdapterRequestError(
                    f"OpenAI API error: {error_message}",
                    status_code=response.status_code
                )
                
            # Parse response
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.error("Failed to parse API response as JSON")
                raise AdapterResponseError(
                    "Failed to parse OpenAI API response as JSON",
                    response_text=response.text
                )
                
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {str(e)}")
            raise AdapterConnectionError(f"Failed to connect to OpenAI API: {str(e)}")
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {str(e)}")
            raise AdapterTimeoutError(f"OpenAI API request timed out: {str(e)}")
            
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Request error: {str(e)}")
            raise AdapterRequestError(f"OpenAI API request failed: {str(e)}")
    
    def complete(
        self,
        prompt: str,
        model: str = "text-davinci-003",
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[Union[str, list[str]]] = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Generate a text completion using OpenAI's completion API.
        
        Args:
            prompt: The prompt to generate completions for
            model: ID of the model to use
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty parameter (-2.0 to 2.0)
            presence_penalty: Presence penalty parameter (-2.0 to 2.0)
            stop: Sequences where the API will stop generating further tokens
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The API response containing the generated completion
            
        Raises:
            Various adapter exceptions for API errors
        """
        # Validate inputs
        if not prompt:
            raise ValueError("Prompt cannot be empty")
            
        if temperature < 0 or temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
            
        if top_p < 0 or top_p > 1:
            raise ValueError("top_p must be between 0 and 1")
            
        if frequency_penalty < -2 or frequency_penalty > 2:
            raise ValueError("frequency_penalty must be between -2 and 2")
            
        if presence_penalty < -2 or presence_penalty > 2:
            raise ValueError("presence_penalty must be between -2 and 2")
        
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }
        
        if stop:
            payload["stop"] = stop
            
        # Add any additional parameters
        payload.update(kwargs)
        
        logger.debug(f"Sending completion request with model: {model}")
        
        try:
            response = self._make_request(
                method="POST",
                endpoint=OpenAIEndpoints.COMPLETIONS,
                data=payload
            )
            return response
        except Exception as e:
            logger.error(f"Error in complete: {str(e)}")
            raise
    
    def chat_complete(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        top_p: float = 1.0,
        n: int = 1,
        stream: bool = False,
        stop: Optional[Union[str, list[str]]] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        functions: Optional[list[dict[str, Any]]] = None,
        function_call: Optional[Union[str, dict[str, str]]] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Generate a chat completion using OpenAI's chat completion API.
        
        Args:
            messages: List of message objects with role and content
            model: ID of the model to use
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            n: Number of completions to generate
            stream: Whether to stream the response
            stop: Sequences where the API will stop generating further tokens
            max_tokens: Maximum number of tokens to generate
            presence_penalty: Presence penalty parameter (-2.0 to 2.0)
            frequency_penalty: Frequency penalty parameter (-2.0 to 2.0)
            functions: List of function definitions for function calling
            function_call: Controls how functions are called
            tools: List of tools available to the model
            tool_choice: Controls which tool the model will use
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The API response containing the generated chat completion
            
        Raises:
            Various adapter exceptions for API errors
        """
        # Validate inputs
        if not messages:
            raise ValueError("Messages list cannot be empty")
            
        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must contain 'role' and 'content' keys")
                
        if temperature < 0 or temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
            
        if top_p < 0 or top_p > 1:
            raise ValueError("top_p must be between 0 and 1")
            
        if frequency_penalty < -2 or frequency_penalty > 2:
            raise ValueError("frequency_penalty must be between -2 and 2")
            
        if presence_penalty < -2 or presence_penalty > 2:
            raise ValueError("presence_penalty must be between -2 and 2")
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stream": stream,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
        }
        
        if stop:
            payload["stop"] = stop
            
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if functions:
            payload["functions"] = functions
            
        if function_call:
            payload["function_call"] = function_call
            
        if tools:
            payload["tools"] = tools
            
        if tool_choice:
            payload["tool_choice"] = tool_choice
            
        # Add any additional parameters
        payload.update(kwargs)
        
        logger.debug(f"Sending chat completion request with model: {model}")
        
        try:
            response = self._make_request(
                method="POST",
                endpoint=OpenAIEndpoints.CHAT_COMPLETIONS,
                data=payload
            )
            return response
        except Exception as e:
            logger.error(f"Error in chat_complete: {str(e)}")
            raise
    
    def generate_embeddings(
        self,
        texts: Union[str, list[str]],
        model: str = "text-embedding-ada-002",
        **kwargs
    ) -> dict[str, Any]:
        """
        Generate embeddings for the given texts using OpenAI's embeddings API.
        
        Args:
            texts: Text or list of texts to generate embeddings for
            model: ID of the model to use
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The API response containing the generated embeddings
            
        Raises:
            Various adapter exceptions for API errors
        """
        # Validate inputs
        if not texts:
            raise ValueError("Texts cannot be empty")
            
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
            
        # Prepare request payload
        payload = {
            "model": model,
            "input": texts,
        }
        
        # Add any additional parameters
        payload.update(kwargs)
        
        logger.debug(f"Sending embeddings request with model: {model}")
        
        try:
            response = self._make_request(
                method="POST",
                endpoint=OpenAIEndpoints.EMBEDDINGS,
                data=payload
            )
            return response
        except Exception as e:
            logger.error(f"Error in generate_embeddings: {str(e)}")
            raise
    
    def list_models(self) -> dict[str, Any]:
        """
        List available models from OpenAI API.
        
        Returns:
            The API response containing the list of available models
            
        Raises:
            Various adapter exceptions for API errors
        """
        logger.debug("Fetching available models from OpenAI API")
        
        try:
            response = self._make_request(
                method="GET",
                endpoint=OpenAIEndpoints.MODELS
            )
            return response
        except Exception as e:
            logger.error(f"Error in list_models: {str(e)}")
            raise
    
    def get_model_info(self, model_id: str) -> dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_id: ID of the model to get information for
            
        Returns:
            The API response containing information about the model
            
        Raises:
            ModelNotFoundError: If the model is not found
            Various adapter exceptions for API errors
        """
        if not model_id:
            raise ValueError("Model ID cannot be empty")
            
        logger.debug(f"Fetching information for model: {model_id}")
        
        try:
            response = self._make_request(
                method="GET",
                endpoint=f"{OpenAIEndpoints.MODELS.value}/{model_id}"
            )
            return response
        except Exception as e:
            logger.error(f"Error in get_model_info: {str(e)}")
            raise
    
    def close(self):
        """
        Close the HTTP client and release resources.
        """
        if hasattr(self, 'http_client') and self.http_client:
            self.http_client.close()
            logger.debug("OpenAI adapter HTTP client closed")
    
    def __enter__(self):
        """
        Context manager entry point.
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        """
        self.close()