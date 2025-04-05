"""
Ollama Adapter for NeuroCognitive Architecture (NCA)

This module provides an adapter for integrating with local Ollama models.
Ollama (https://ollama.com/) is an open-source framework for running LLMs locally,
which allows usage of models like Llama, Mistral, Phi, Gemma, etc. without relying
on external APIs.

Usage:
    from neuroca.integration.adapters import AdapterRegistry
    from neuroca.integration.adapters.ollama import OllamaAdapter
    
    # Register the adapter
    config = {
        "base_url": "http://localhost:11434",
        "default_model": "llama3"
    }
    adapter = OllamaAdapter(config)
    AdapterRegistry.register_adapter("ollama", adapter)
    
    # Use the adapter
    response = await adapter.generate(prompt="Explain neuroplasticity")
"""

import asyncio
import json
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

import aiohttp

from .base import LLMAdapter, AdapterError, ModelCapability, AdapterConfigurationError
from ..models import LLMRequest, LLMResponse, TokenUsage, ResponseType

logger = logging.getLogger(__name__)


class OllamaError(AdapterError):
    """Exception specific to Ollama adapter errors."""
    pass


class OllamaAdapter(LLMAdapter):
    """
    Adapter for Ollama local LLM deployments.
    
    This adapter enables the NCA to use locally running LLM models through
    the Ollama API, providing access to a variety of open-source models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Ollama adapter.
        
        Args:
            config: Configuration dictionary with Ollama-specific settings
                - base_url: Ollama API base URL (default: http://localhost:11434)
                - default_model: Default model to use
                - request_timeout: Request timeout in seconds
                - max_retries: Max number of retries for failed requests
                - other parameters that will be passed to Ollama API
        """
        self._name = "ollama"
        self._base_url = config.get("base_url", "http://localhost:11434")
        self._default_model = config.get("default_model", "llama3")
        self._request_timeout = config.get("request_timeout", 120)
        self._max_retries = config.get("max_retries", 3)
        self._config = config
        self._available_models = set()
        self._session = None
        
        # Initialize HTTP session
        self._initialize_session()
        logger.info(f"Initialized Ollama adapter with base URL: {self._base_url}")

    def _initialize_session(self):
        """Initialize the HTTP session for API requests."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._request_timeout)
        )
    
    @property
    def name(self) -> str:
        """Return the adapter name."""
        return self._name
    
    @property
    def capabilities(self) -> Set[ModelCapability]:
        """Return the set of capabilities supported by this adapter."""
        return {
            ModelCapability.TEXT_GENERATION,
            ModelCapability.CHAT_COMPLETION,
            ModelCapability.EMBEDDINGS
        }
    
    async def close(self):
        """Close the adapter and release resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed Ollama adapter HTTP session")
    
    def validate_configuration(self) -> bool:
        """
        Validate adapter configuration.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            AdapterConfigurationError: If configuration is invalid
        """
        # Check required configuration
        if not self._base_url:
            raise AdapterConfigurationError("base_url must be specified in configuration")
        
        # Validate URL format
        if not self._base_url.startswith(("http://", "https://")):
            raise AdapterConfigurationError(f"Invalid base_url format: {self._base_url}")
        
        return True
    
    async def _fetch_available_models(self) -> List[str]:
        """
        Fetch available models from Ollama API.
        
        Returns:
            List[str]: List of available model names
            
        Raises:
            OllamaError: If fetching models fails
        """
        if not self._session or self._session.closed:
            self._initialize_session()
            
        try:
            async with self._session.get(f"{self._base_url}/api/tags") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise OllamaError(f"Failed to fetch Ollama models: {error_text}")
                
                data = await response.json()
                models = [model["name"] for model in data.get("models", [])]
                self._available_models = set(models)
                return models
                
        except aiohttp.ClientError as e:
            raise OllamaError(f"Connection error when fetching Ollama models: {str(e)}")
        except json.JSONDecodeError as e:
            raise OllamaError(f"Invalid JSON response from Ollama API: {str(e)}")
        except Exception as e:
            raise OllamaError(f"Unexpected error: {str(e)}")
    
    async def get_available_models(self) -> List[str]:
        """
        Get a list of available Ollama models.
        
        Returns:
            List[str]: List of available model names
        """
        if not self._available_models:
            await self._fetch_available_models()
        return list(self._available_models)
    
    async def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Execute a request to the Ollama API.
        
        Args:
            request: The LLM request to execute
            
        Returns:
            LLMResponse containing the model's response
            
        Raises:
            OllamaError: If the request fails
        """
        # Extract model name
        model = request.model or self._default_model
        
        # Create API payload
        payload = {
            "model": model,
            "prompt": request.prompt,
            "stream": False
        }
        
        # Add optional parameters
        if request.max_tokens:
            payload["num_predict"] = request.max_tokens
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        
        # Add any additional parameters
        for key, value in request.additional_params.items():
            if key not in payload:
                payload[key] = value
        
        # Execute the request
        if not self._session or self._session.closed:
            self._initialize_session()
            
        start_time = time.time()
        
        try:
            async with self._session.post(
                f"{self._base_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise OllamaError(f"Ollama API error ({response.status}): {error_text}")
                
                response_data = await response.json()
                
                # Extract response content
                generated_text = response_data.get("response", "")
                
                # Extract token usage
                eval_count = response_data.get("eval_count", 0)
                prompt_eval_count = response_data.get("prompt_eval_count", 0)
                total_duration = response_data.get("total_duration", 0)
                
                # Create token usage info
                token_usage = TokenUsage(
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=prompt_eval_count + eval_count
                )
                
                # Create metadata
                metadata = {
                    "duration_ms": total_duration,
                    "model": model,
                    "adapter": self.name,
                    **response_data
                }
                
                # Calculate cost (always 0 for local models)
                cost = 0.0
                
                # Create LLMResponse
                return LLMResponse(
                    provider=self.name,
                    model=model,
                    content=generated_text,
                    raw_response=response_data,
                    metadata=metadata,
                    usage=token_usage,
                    cost=cost,
                    request=request,
                    created_at=time.time(),
                    elapsed_time=time.time() - start_time
                )
                
        except aiohttp.ClientError as e:
            raise OllamaError(f"Connection error with Ollama API: {str(e)}")
        except json.JSONDecodeError as e:
            raise OllamaError(f"Invalid JSON response from Ollama API: {str(e)}")
        except Exception as e:
            if not isinstance(e, OllamaError):
                raise OllamaError(f"Unexpected error during Ollama request: {str(e)}")
            raise
    
    async def generate(self, 
                       prompt: str, 
                       max_tokens: Optional[int] = None,
                       temperature: Optional[float] = None,
                       stop_sequences: Optional[List[str]] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        Generate text based on the provided prompt.
        
        Args:
            prompt: The input prompt for text generation
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            stop_sequences: Sequences that stop generation
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with generated text and metadata
        """
        # Create LLMRequest
        request = LLMRequest(
            provider=self.name,
            model=kwargs.get("model", self._default_model),
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop_sequences=stop_sequences,
            additional_params=kwargs
        )
        
        # Execute the request
        response = await self.execute(request)
        
        # Format as expected by LLMAdapter interface
        return {
            "text": response.content,
            "usage": response.usage.to_dict() if response.usage else {},
            "model": response.model,
            "metadata": response.metadata
        }
    
    async def chat(self,
                   messages: List[Dict[str, str]],
                   max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None,
                   **kwargs) -> Dict[str, Any]:
        """
        Generate a response based on a conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with generated response and metadata
        """
        # Convert chat messages to a prompt string
        formatted_prompt = self._format_chat_messages(messages)
        
        # Generate response using the formatted prompt
        return await self.generate(
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    
    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages into a prompt string for Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Formatted prompt string
        """
        formatted_prompt = ""
        
        for message in messages:
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            if role == "system":
                formatted_prompt += f"<s>[INST] <<SYS>>\n{content}\n<</SYS>>\n\n"
            elif role == "user":
                if not formatted_prompt:
                    formatted_prompt += f"<s>[INST] {content} [/INST]"
                else:
                    formatted_prompt += f"[INST] {content} [/INST]"
            elif role == "assistant":
                formatted_prompt += f"{content} </s>"
            else:
                # Handle unknown roles as user messages
                formatted_prompt += f"[INST] {content} [/INST]"
        
        return formatted_prompt
    
    async def embed(self, 
                    text: Union[str, List[str]], 
                    **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings for the provided text.
        
        Args:
            text: Text or list of texts to embed
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with embeddings and metadata
            
        Raises:
            OllamaError: If embedding generation fails
        """
        if not self._session or self._session.closed:
            self._initialize_session()
            
        model = kwargs.get("model", self._default_model)
        
        # Handle both single text and list of texts
        is_batch = isinstance(text, list)
        texts = text if is_batch else [text]
        
        embeddings = []
        total_tokens = 0
        
        try:
            for single_text in texts:
                payload = {
                    "model": model,
                    "prompt": single_text
                }
                
                async with self._session.post(
                    f"{self._base_url}/api/embeddings",
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise OllamaError(f"Ollama API error ({response.status}): {error_text}")
                    
                    response_data = await response.json()
                    embedding = response_data.get("embedding", [])
                    embeddings.append(embedding)
                    
                    # Track token usage (estimated)
                    total_tokens += len(single_text.split())
            
            # Return embeddings
            return {
                "embeddings": embeddings[0] if not is_batch else embeddings,
                "usage": {
                    "prompt_tokens": total_tokens,
                    "total_tokens": total_tokens
                },
                "model": model,
                "metadata": {
                    "batch_size": len(texts),
                    "embedding_size": len(embeddings[0]) if embeddings else 0
                }
            }
            
        except aiohttp.ClientError as e:
            raise OllamaError(f"Connection error with Ollama API: {str(e)}")
        except json.JSONDecodeError as e:
            raise OllamaError(f"Invalid JSON response from Ollama API: {str(e)}")
        except Exception as e:
            if not isinstance(e, OllamaError):
                raise OllamaError(f"Unexpected error during embedding: {str(e)}")
            raise

# Register the adapter
AdapterRegistry.register_adapter_class("ollama", OllamaAdapter)
