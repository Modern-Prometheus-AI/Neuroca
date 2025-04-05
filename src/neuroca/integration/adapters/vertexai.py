"""
Vertex AI Adapter for NeuroCognitive Architecture

This module provides integration with Google Cloud's Vertex AI platform, allowing
the NeuroCognitive Architecture to leverage Google's large language models.

The adapter handles authentication, request formatting, response parsing, and
error handling for Vertex AI API interactions.

Usage:
    from neuroca.integration.adapters.vertexai import VertexAIAdapter
    
    # Initialize the adapter with your project and location
    adapter = VertexAIAdapter(
        project_id="your-gcp-project",
        location="us-central1"
    )
    
    # Generate text using a Vertex AI model
    response = await adapter.generate_text(
        "Tell me about cognitive architectures",
        model="text-bison@001",
        max_tokens=1024
    )

Requirements:
    - Google Cloud credentials must be properly configured
    - Required permissions for Vertex AI API access
    - Network access to Google Cloud APIs

Security:
    - Uses application default credentials for authentication
    - Implements rate limiting to prevent abuse
    - Sanitizes inputs to prevent injection attacks
    - Handles sensitive information in logs appropriately
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp
import google.auth
import tenacity
from google.auth.transport.requests import Request
from google.cloud import aiplatform
from google.oauth2 import service_account

from neuroca.integration.adapters.base import AdapterResponse, BaseAdapter
from neuroca.integration.exceptions import (
    AuthenticationError,
    InvalidRequestError,
    ModelNotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServiceUnavailableError,
    UnexpectedResponseError,
)

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class VertexAIConfig:
    """Configuration for Vertex AI adapter."""
    project_id: str
    location: str
    api_endpoint: str = "us-central1-aiplatform.googleapis.com"
    credentials_path: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    retry_delay: int = 2
    rate_limit_requests: int = 60
    rate_limit_period: int = 60  # 60 requests per minute by default


class VertexAIAdapter(BaseAdapter):
    """
    Adapter for Google Cloud's Vertex AI platform.
    
    This adapter provides methods to interact with Vertex AI models for text generation,
    embeddings, and other NLP tasks. It handles authentication, request formatting,
    response parsing, and error handling.
    """
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        credentials_path: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: int = 2,
        rate_limit_requests: int = 60,
        rate_limit_period: int = 60,
    ):
        """
        Initialize the Vertex AI adapter.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region (e.g., "us-central1")
            credentials_path: Path to service account credentials JSON file.
                If None, uses application default credentials.
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            rate_limit_requests: Maximum number of requests in the rate limit period
            rate_limit_period: Rate limit period in seconds
        
        Raises:
            AuthenticationError: If authentication with Google Cloud fails
        """
        self.config = VertexAIConfig(
            project_id=project_id,
            location=location,
            credentials_path=credentials_path,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            rate_limit_requests=rate_limit_requests,
            rate_limit_period=rate_limit_period,
        )
        
        # Initialize rate limiting
        self._request_timestamps = []
        
        # Initialize credentials
        try:
            self._init_credentials()
            self._init_client()
            logger.info(f"Initialized Vertex AI adapter for project {project_id} in {location}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI adapter: {str(e)}")
            raise AuthenticationError(f"Failed to authenticate with Vertex AI: {str(e)}") from e
    
    def _init_credentials(self) -> None:
        """
        Initialize Google Cloud credentials.
        
        Uses service account credentials if provided, otherwise falls back to
        application default credentials.
        
        Raises:
            AuthenticationError: If credentials cannot be obtained
        """
        try:
            if self.config.credentials_path:
                logger.debug(f"Using service account credentials from {self.config.credentials_path}")
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.config.credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            else:
                logger.debug("Using application default credentials")
                self.credentials, self.project_id = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                
                # If project_id wasn't explicitly provided, use the one from credentials
                if not self.config.project_id:
                    self.config.project_id = self.project_id
            
            # Refresh credentials if needed
            if not self.credentials.valid:
                self.credentials.refresh(Request())
                
        except Exception as e:
            logger.error(f"Failed to initialize credentials: {str(e)}")
            raise AuthenticationError(f"Failed to obtain Google Cloud credentials: {str(e)}") from e
    
    def _init_client(self) -> None:
        """
        Initialize the Vertex AI client.
        
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            # Initialize the Vertex AI client
            aiplatform.init(
                project=self.config.project_id,
                location=self.config.location,
                credentials=self.credentials
            )
            logger.debug("Vertex AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {str(e)}")
            raise AuthenticationError(f"Failed to initialize Vertex AI client: {str(e)}") from e
    
    async def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limiting for API requests.
        
        This method implements a sliding window rate limiter to prevent
        exceeding API quotas. It blocks until a request can be made within
        the configured rate limits.
        
        Raises:
            RateLimitError: If rate limit is exceeded and max wait time is reached
        """
        now = time.time()
        
        # Remove timestamps outside the current window
        self._request_timestamps = [ts for ts in self._request_timestamps 
                                   if now - ts < self.config.rate_limit_period]
        
        # If we're at the limit, wait until we can make another request
        if len(self._request_timestamps) >= self.config.rate_limit_requests:
            wait_time = self._request_timestamps[0] + self.config.rate_limit_period - now
            
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                if wait_time > 30:  # If wait time is excessive, raise an error
                    raise RateLimitError(f"Rate limit exceeded. Try again in {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current timestamp to the list
        self._request_timestamps.append(time.time())
    
    def _build_api_url(self, model_id: str, endpoint: str = "generateText") -> str:
        """
        Build the Vertex AI API URL for a specific model and endpoint.
        
        Args:
            model_id: The Vertex AI model ID
            endpoint: The API endpoint to call (e.g., "generateText", "embedText")
        
        Returns:
            The complete API URL
        """
        base_url = f"https://{self.config.location}-aiplatform.googleapis.com/v1"
        return f"{base_url}/projects/{self.config.project_id}/locations/{self.config.location}/publishers/google/models/{model_id}:{endpoint}"
    
    def _handle_error_response(self, status_code: int, response_text: str, model: str) -> None:
        """
        Handle error responses from the Vertex AI API.
        
        Args:
            status_code: HTTP status code
            response_text: Response body text
            model: Model ID that was used
        
        Raises:
            Various exceptions based on the error type
        """
        error_msg = f"Vertex AI API error ({status_code})"
        try:
            error_data = json.loads(response_text)
            if "error" in error_data:
                error_msg = f"{error_msg}: {error_data['error'].get('message', 'Unknown error')}"
        except json.JSONDecodeError:
            error_msg = f"{error_msg}: {response_text[:100]}..."
        
        logger.error(f"Error calling Vertex AI model {model}: {error_msg}")
        
        if status_code == 400:
            raise InvalidRequestError(f"Invalid request to Vertex AI: {error_msg}")
        elif status_code == 401 or status_code == 403:
            raise AuthenticationError(f"Authentication failed with Vertex AI: {error_msg}")
        elif status_code == 404:
            raise ModelNotFoundError(f"Model {model} not found: {error_msg}")
        elif status_code == 429:
            raise RateLimitError(f"Rate limit exceeded for Vertex AI: {error_msg}")
        elif status_code == 503:
            raise ServiceUnavailableError(f"Vertex AI service unavailable: {error_msg}")
        elif "quota" in error_msg.lower():
            raise QuotaExceededError(f"Quota exceeded for Vertex AI: {error_msg}")
        else:
            raise UnexpectedResponseError(f"Unexpected response from Vertex AI: {error_msg}")
    
    @tenacity.retry(
        retry=tenacity.retry_if_exception_type((
            ServiceUnavailableError,
            aiohttp.ClientError,
            asyncio.TimeoutError
        )),
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=lambda retry_state: logger.info(
            f"Retrying Vertex AI request (attempt {retry_state.attempt_number})"
        ),
        reraise=True
    )
    async def generate_text(
        self,
        prompt: str,
        model: str = "text-bison@001",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        stop_sequences: Optional[list[str]] = None,
        safety_settings: Optional[list[dict[str, Any]]] = None,
        **kwargs
    ) -> AdapterResponse:
        """
        Generate text using a Vertex AI language model.
        
        Args:
            prompt: The input prompt for text generation
            model: The Vertex AI model ID (e.g., "text-bison@001")
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: List of sequences that stop generation
            safety_settings: Custom safety settings for content filtering
            **kwargs: Additional model-specific parameters
        
        Returns:
            AdapterResponse containing the generated text and metadata
        
        Raises:
            AuthenticationError: If authentication fails
            ModelNotFoundError: If the specified model doesn't exist
            RateLimitError: If rate limits are exceeded
            QuotaExceededError: If API quotas are exceeded
            ServiceUnavailableError: If the service is unavailable
            InvalidRequestError: If the request is invalid
            UnexpectedResponseError: For other unexpected errors
        """
        # Input validation
        if not prompt or not isinstance(prompt, str):
            raise InvalidRequestError("Prompt must be a non-empty string")
        
        if not model or not isinstance(model, str):
            raise InvalidRequestError("Model must be a non-empty string")
        
        if temperature < 0.0 or temperature > 1.0:
            raise InvalidRequestError("Temperature must be between 0.0 and 1.0")
        
        if top_p < 0.0 or top_p > 1.0:
            raise InvalidRequestError("Top-p must be between 0.0 and 1.0")
        
        if max_tokens < 1:
            raise InvalidRequestError("max_tokens must be a positive integer")
        
        # Enforce rate limiting
        await self._enforce_rate_limit()
        
        # Prepare request payload
        request_data = {
            "prompt": prompt,
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": top_p,
            "topK": top_k,
        }
        
        if stop_sequences:
            request_data["stopSequences"] = stop_sequences
            
        if safety_settings:
            request_data["safetySettings"] = safety_settings
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in request_data:
                request_data[key] = value
        
        # Build API URL
        api_url = self._build_api_url(model, "generateText")
        
        # Prepare headers with authentication
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        logger.debug(f"Sending request to Vertex AI model {model}: {json.dumps(request_data)[:200]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    json=request_data,
                    headers=headers,
                    timeout=self.config.timeout
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        self._handle_error_response(response.status, response_text, model)
                    
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Vertex AI response: {response_text[:200]}...")
                        raise UnexpectedResponseError(f"Invalid JSON response from Vertex AI: {str(e)}") from e
                    
                    # Extract the generated text
                    try:
                        generated_text = response_data.get("candidates", [{}])[0].get("content", "")
                        
                        # Extract metadata
                        metadata = {
                            "model": model,
                            "usage": {
                                "prompt_tokens": response_data.get("usageMetadata", {}).get("promptTokenCount", 0),
                                "completion_tokens": response_data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                                "total_tokens": response_data.get("usageMetadata", {}).get("totalTokenCount", 0),
                            },
                            "finish_reason": response_data.get("candidates", [{}])[0].get("finishReason", ""),
                            "safety_ratings": response_data.get("candidates", [{}])[0].get("safetyRatings", []),
                            "latency_ms": int((time.time() - start_time) * 1000)
                        }
                        
                        logger.info(f"Successfully generated text with Vertex AI model {model} "
                                   f"({metadata['usage']['total_tokens']} tokens, "
                                   f"{metadata['latency_ms']}ms)")
                        
                        return AdapterResponse(
                            text=generated_text,
                            raw_response=response_data,
                            metadata=metadata
                        )
                    except (KeyError, IndexError) as e:
                        logger.error(f"Unexpected response structure from Vertex AI: {response_data}")
                        raise UnexpectedResponseError(f"Unexpected response structure from Vertex AI: {str(e)}") from e
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error when calling Vertex AI: {str(e)}")
            raise ServiceUnavailableError(f"Failed to connect to Vertex AI: {str(e)}") from e
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout when calling Vertex AI model {model} after {self.config.timeout}s")
            raise ServiceUnavailableError(f"Request to Vertex AI timed out after {self.config.timeout} seconds")
    
    async def get_embeddings(
        self,
        texts: list[str],
        model: str = "textembedding-gecko@001",
        **kwargs
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts using Vertex AI.
        
        Args:
            texts: List of texts to generate embeddings for
            model: The Vertex AI embedding model ID
            **kwargs: Additional model-specific parameters
        
        Returns:
            List of embedding vectors (each vector is a list of floats)
        
        Raises:
            AuthenticationError: If authentication fails
            ModelNotFoundError: If the specified model doesn't exist
            RateLimitError: If rate limits are exceeded
            QuotaExceededError: If API quotas are exceeded
            ServiceUnavailableError: If the service is unavailable
            InvalidRequestError: If the request is invalid
            UnexpectedResponseError: For other unexpected errors
        """
        # Input validation
        if not texts:
            raise InvalidRequestError("Texts list cannot be empty")
        
        if not all(isinstance(text, str) for text in texts):
            raise InvalidRequestError("All texts must be strings")
        
        if not model or not isinstance(model, str):
            raise InvalidRequestError("Model must be a non-empty string")
        
        # Enforce rate limiting
        await self._enforce_rate_limit()
        
        # Prepare request payload
        request_data = {
            "instances": [{"content": text} for text in texts],
        }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in request_data:
                request_data[key] = value
        
        # Build API URL
        api_url = self._build_api_url(model, "embedText")
        
        # Prepare headers with authentication
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        logger.debug(f"Sending embedding request to Vertex AI model {model} for {len(texts)} texts")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    json=request_data,
                    headers=headers,
                    timeout=self.config.timeout
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        self._handle_error_response(response.status, response_text, model)
                    
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Vertex AI response: {response_text[:200]}...")
                        raise UnexpectedResponseError(f"Invalid JSON response from Vertex AI: {str(e)}") from e
                    
                    # Extract embeddings
                    try:
                        embeddings = [
                            prediction.get("embeddings", {}).get("values", [])
                            for prediction in response_data.get("predictions", [])
                        ]
                        
                        latency_ms = int((time.time() - start_time) * 1000)
                        logger.info(f"Successfully generated {len(embeddings)} embeddings with "
                                   f"Vertex AI model {model} ({latency_ms}ms)")
                        
                        return embeddings
                    except (KeyError, IndexError) as e:
                        logger.error(f"Unexpected response structure from Vertex AI: {response_data}")
                        raise UnexpectedResponseError(f"Unexpected response structure from Vertex AI: {str(e)}") from e
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error when calling Vertex AI: {str(e)}")
            raise ServiceUnavailableError(f"Failed to connect to Vertex AI: {str(e)}") from e
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout when calling Vertex AI model {model} after {self.config.timeout}s")
            raise ServiceUnavailableError(f"Request to Vertex AI timed out after {self.config.timeout} seconds")
    
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "chat-bison@001",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        stop_sequences: Optional[list[str]] = None,
        safety_settings: Optional[list[dict[str, Any]]] = None,
        **kwargs
    ) -> AdapterResponse:
        """
        Generate a chat completion using a Vertex AI chat model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: The Vertex AI chat model ID
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: List of sequences that stop generation
            safety_settings: Custom safety settings for content filtering
            **kwargs: Additional model-specific parameters
        
        Returns:
            AdapterResponse containing the generated response and metadata
        
        Raises:
            AuthenticationError: If authentication fails
            ModelNotFoundError: If the specified model doesn't exist
            RateLimitError: If rate limits are exceeded
            QuotaExceededError: If API quotas are exceeded
            ServiceUnavailableError: If the service is unavailable
            InvalidRequestError: If the request is invalid
            UnexpectedResponseError: For other unexpected errors
        """
        # Input validation
        if not messages:
            raise InvalidRequestError("Messages list cannot be empty")
        
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                raise InvalidRequestError("Each message must be a dictionary with 'role' and 'content' keys")
        
        if not model or not isinstance(model, str):
            raise InvalidRequestError("Model must be a non-empty string")
        
        if temperature < 0.0 or temperature > 1.0:
            raise InvalidRequestError("Temperature must be between 0.0 and 1.0")
        
        if top_p < 0.0 or top_p > 1.0:
            raise InvalidRequestError("Top-p must be between 0.0 and 1.0")
        
        if max_tokens < 1:
            raise InvalidRequestError("max_tokens must be a positive integer")
        
        # Enforce rate limiting
        await self._enforce_rate_limit()
        
        # Convert messages to Vertex AI format
        context = ""
        examples = []
        message_history = []
        
        for msg in messages:
            role = msg['role'].lower()
            content = msg['content']
            
            if role == 'system':
                context += content + "\n"
            elif role == 'user':
                message_history.append({"author": "user", "content": content})
            elif role == 'assistant':
                message_history.append({"author": "assistant", "content": content})
            elif role == 'example_user':
                # Handle examples for few-shot learning
                if not examples or len(examples[-1]) != 1:
                    examples.append({"input": {"content": content}})
                else:
                    examples[-1]["input"] = {"content": content}
            elif role == 'example_assistant':
                # Complete the example pair
                if examples and "input" in examples[-1]:
                    examples[-1]["output"] = {"content": content}
        
        # Prepare request payload
        request_data = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": top_p,
            "topK": top_k,
        }
        
        if context:
            request_data["context"] = context.strip()
            
        if examples:
            request_data["examples"] = examples
            
        if message_history:
            request_data["messages"] = message_history
        
        if stop_sequences:
            request_data["stopSequences"] = stop_sequences
            
        if safety_settings:
            request_data["safetySettings"] = safety_settings
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in request_data:
                request_data[key] = value
        
        # Build API URL
        api_url = self._build_api_url(model, "generateMessage")
        
        # Prepare headers with authentication
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        logger.debug(f"Sending chat request to Vertex AI model {model}: {json.dumps(request_data)[:200]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    json=request_data,
                    headers=headers,
                    timeout=self.config.timeout
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        self._handle_error_response(response.status, response_text, model)
                    
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Vertex AI response: {response_text[:200]}...")
                        raise UnexpectedResponseError(f"Invalid JSON response from Vertex AI: {str(e)}") from e
                    
                    # Extract the generated response
                    try:
                        generated_text = response_data.get("candidates", [{}])[0].get("content", "")
                        
                        # Extract metadata
                        metadata = {
                            "model": model,
                            "usage": {
                                "prompt_tokens": response_data.get("usageMetadata", {}).get("promptTokenCount", 0),
                                "completion_tokens": response_data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                                "total_tokens": response_data.get("usageMetadata", {}).get("totalTokenCount", 0),
                            },
                            "finish_reason": response_data.get("candidates", [{}])[0].get("finishReason", ""),
                            "safety_ratings": response_data.get("candidates", [{}])[0].get("safetyRatings", []),
                            "latency_ms": int((time.time() - start_time) * 1000)
                        }
                        
                        logger.info(f"Successfully generated chat response with Vertex AI model {model} "
                                   f"({metadata['usage']['total_tokens']} tokens, "
                                   f"{metadata['latency_ms']}ms)")
                        
                        return AdapterResponse(
                            text=generated_text,
                            raw_response=response_data,
                            metadata=metadata
                        )
                    except (KeyError, IndexError) as e:
                        logger.error(f"Unexpected response structure from Vertex AI: {response_data}")
                        raise UnexpectedResponseError(f"Unexpected response structure from Vertex AI: {str(e)}") from e
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error when calling Vertex AI: {str(e)}")
            raise ServiceUnavailableError(f"Failed to connect to Vertex AI: {str(e)}") from e
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout when calling Vertex AI model {model} after {self.config.timeout}s")
            raise ServiceUnavailableError(f"Request to Vertex AI timed out after {self.config.timeout} seconds")