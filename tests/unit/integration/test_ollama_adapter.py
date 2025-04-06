"""
Unit tests for the Ollama Adapter module.

This module tests the OllamaAdapter class, which allows the NCA to interface
with locally running LLM models through the Ollama API. It verifies that the
adapter correctly handles:
1. Initialization and configuration
2. Generating text
3. Chat completions
4. Embeddings generation
5. Error handling
"""

from unittest.mock import AsyncMock, MagicMock, call, patch

import aiohttp
import pytest
from aiohttp import ClientSession

# Corrected import: Use BaseAdapter instead of LLMAdapter (which doesn't exist in base.py)
# Also import other necessary items from base
from neuroca.integration.adapters.base import LLMResponse
from neuroca.integration.adapters.ollama import OllamaAdapter, OllamaError
from neuroca.integration.models import (
    LLMRequest,  # LLMResponse is imported above now
    TokenUsage,
)


class MockResponse:
    """Mock aiohttp response for testing."""
    
    def __init__(self, status=200, data=None, text=None):
        self.status = status
        self.data = data if data is not None else {}
        self.text_value = text
        
    async def json(self):
        """Return JSON data."""
        return self.data
        
    async def text(self):
        """Return text data."""
        return self.text_value
        
    async def __aenter__(self):
        """Context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class TestOllamaAdapter:
    """Test suite for the OllamaAdapter class."""
    
    @pytest.fixture()
    def basic_config(self):
        """Create a basic configuration for testing."""
        return {
            "base_url": "http://localhost:11434",
            "default_model": "llama3",
            "request_timeout": 60,
            "max_retries": 3
        }
    
    @pytest.fixture()
    def mock_session(self):
        """Create a mock aiohttp session for testing."""
        session = MagicMock(spec=ClientSession)
        session.get = AsyncMock()
        session.post = AsyncMock()
        session.closed = False
        session.close = AsyncMock()
        return session
    
    @pytest.fixture()
    def ollama_adapter(self, basic_config, mock_session):
        """Create an OllamaAdapter instance for testing."""
        with patch('neuroca.integration.adapters.ollama.aiohttp.ClientSession', return_value=mock_session):
            adapter = OllamaAdapter(basic_config)
            adapter._session = mock_session
            return adapter
    
    async def test_initialization(self, basic_config):
        """Test that the adapter initializes correctly."""
        with patch('neuroca.integration.adapters.ollama.aiohttp.ClientSession'):
            adapter = OllamaAdapter(basic_config)
            
            # Check default values
            assert adapter._base_url == "http://localhost:11434"
            assert adapter._default_model == "llama3"
            assert adapter._request_timeout == 60
            assert adapter._max_retries == 3
            assert adapter._name == "ollama"
    
    async def test_validate_configuration(self, basic_config):
        """Test configuration validation."""
        # Test with valid configuration
        valid_config = basic_config.copy()
        adapter = OllamaAdapter(valid_config)
        assert adapter.validate_configuration() is True
        
        # Test with missing base_url
        invalid_config = basic_config.copy()
        invalid_config["base_url"] = ""
        with pytest.raises(Exception):
            OllamaAdapter(invalid_config).validate_configuration()
        
        # Test with invalid base_url format
        invalid_config = basic_config.copy()
        invalid_config["base_url"] = "invalid-url"
        with pytest.raises(Exception):
            OllamaAdapter(invalid_config).validate_configuration()
    
    async def test_close(self, ollama_adapter, mock_session):
        """Test closing the adapter."""
        await ollama_adapter.close()
        mock_session.close.assert_called_once()
    
    async def test_get_available_models(self, ollama_adapter, mock_session):
        """Test getting available models."""
        # Configure mock response
        mock_response = MockResponse(status=200, data={
            "models": [
                {"name": "llama3"},
                {"name": "mistral"},
                {"name": "phi3"}
            ]
        })
        mock_session.get.return_value = mock_response
        
        # Call the method
        models = await ollama_adapter.get_available_models()
        
        # Verify the correct API endpoint was called
        mock_session.get.assert_called_with("http://localhost:11434/api/tags")
        
        # Verify the returned models
        assert "llama3" in models
        assert "mistral" in models
        assert "phi3" in models
        assert len(models) == 3
    
    async def test_get_available_models_error(self, ollama_adapter, mock_session):
        """Test error handling for getting available models."""
        # Configure mock response for error
        mock_response = MockResponse(status=500, text="Internal Server Error")
        mock_session.get.return_value = mock_response
        
        # Call the method and expect an error
        with pytest.raises(OllamaError):
            await ollama_adapter._fetch_available_models()
    
    async def test_execute_basic(self, ollama_adapter, mock_session):
        """Test basic execution of a request."""
        # Configure mock response
        mock_response = MockResponse(status=200, data={
            "model": "llama3",
            "response": "This is a test response",
            "eval_count": 20,
            "prompt_eval_count": 10,
            "total_duration": 500000000  # 500ms in nanoseconds
        })
        mock_session.post.return_value = mock_response
        
        # Create a request
        request = LLMRequest(
            provider="ollama",
            model="llama3",
            prompt="Test prompt"
        )
        
        # Execute the request
        response = await ollama_adapter.execute(request)
        
        # Verify the correct API endpoint was called with correct data
        mock_session.post.assert_called_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": "Test prompt",
                "stream": False
            }
        )
        
        # Verify the response
        assert response.provider == "ollama"
        assert response.model == "llama3"
        assert response.content == "This is a test response"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30
        assert "duration_ms" in response.metadata
        assert response.cost == 0.0  # Local models have no cost
    
    async def test_execute_with_parameters(self, ollama_adapter, mock_session):
        """Test execution with additional parameters."""
        # Configure mock response
        mock_response = MockResponse(status=200, data={
            "model": "llama3",
            "response": "This is a test response",
            "eval_count": 20,
            "prompt_eval_count": 10,
            "total_duration": 500000000
        })
        mock_session.post.return_value = mock_response
        
        # Create a request with parameters
        request = LLMRequest(
            provider="ollama",
            model="llama3",
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
            additional_params={"top_k": 40, "top_p": 0.9}
        )
        
        # Execute the request
        await ollama_adapter.execute(request)
        
        # Verify the parameters were passed correctly
        call_kwargs = mock_session.post.call_args[1]["json"]
        assert call_kwargs["model"] == "llama3"
        assert call_kwargs["prompt"] == "Test prompt"
        assert call_kwargs["num_predict"] == 100
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["top_k"] == 40
        assert call_kwargs["top_p"] == 0.9
    
    async def test_execute_api_error(self, ollama_adapter, mock_session):
        """Test error handling for API errors."""
        # Configure mock response for error
        mock_response = MockResponse(status=400, text="Bad request")
        mock_session.post.return_value = mock_response
        
        # Create a request
        request = LLMRequest(
            provider="ollama",
            model="llama3",
            prompt="Test prompt"
        )
        
        # Call the method and expect an error
        with pytest.raises(OllamaError):
            await ollama_adapter.execute(request)
    
    async def test_execute_connection_error(self, ollama_adapter, mock_session):
        """Test error handling for connection errors."""
        # Configure mock session to raise exception
        mock_session.post.side_effect = aiohttp.ClientError("Connection error")
        
        # Create a request
        request = LLMRequest(
            provider="ollama",
            model="llama3",
            prompt="Test prompt"
        )
        
        # Call the method and expect an error
        with pytest.raises(OllamaError):
            await ollama_adapter.execute(request)
    
    async def test_generate(self, ollama_adapter):
        """Test the generate method."""
        # Mock the execute method
        ollama_adapter.execute = AsyncMock()
        mock_response = LLMResponse(
            provider="ollama",
            model="llama3",
            content="Test response",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
        )
        ollama_adapter.execute.return_value = mock_response
        
        # Call the generate method
        response = await ollama_adapter.generate(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
            stop_sequences=["END"]
        )
        
        # Verify the execute method was called with correct parameters
        ollama_adapter.execute.assert_called_once()
        request = ollama_adapter.execute.call_args[0][0]
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        assert request.stop_sequences == ["END"]
        
        # Verify the response format
        assert response["text"] == "Test response"
        assert "usage" in response
        assert response["model"] == "llama3"
    
    async def test_chat(self, ollama_adapter):
        """Test the chat method."""
        # Mock the generate method
        ollama_adapter.generate = AsyncMock()
        ollama_adapter.generate.return_value = {
            "text": "Test response",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "model": "llama3"
        }
        
        # Create test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "How can I help?"},
            {"role": "user", "content": "Tell me about NCA"}
        ]
        
        # Call the chat method
        response = await ollama_adapter.chat(
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        # Verify the generate method was called
        ollama_adapter.generate.assert_called_once()
        
        # The formatted prompt should contain all the messages
        prompt = ollama_adapter.generate.call_args[1]["prompt"]
        assert "You are a helpful assistant" in prompt
        assert "Hello" in prompt
        assert "How can I help?" in prompt
        assert "Tell me about NCA" in prompt
        
        # Verify other parameters were passed correctly
        assert ollama_adapter.generate.call_args[1]["max_tokens"] == 100
        assert ollama_adapter.generate.call_args[1]["temperature"] == 0.7
        
        # Verify the response is passed through
        assert response["text"] == "Test response"
    
    async def test_format_chat_messages(self, ollama_adapter):
        """Test formatting of chat messages."""
        # Test with system, user, and assistant messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "How can I help?"},
            {"role": "user", "content": "Tell me about NCA"}
        ]
        
        formatted = ollama_adapter._format_chat_messages(messages)
        
        # Verify the formatting
        assert "<s>[INST] <<SYS>>" in formatted
        assert "You are a helpful assistant" in formatted
        assert "<</SYS>>" in formatted
        assert "[INST] Hello [/INST]" in formatted
        assert "How can I help?" in formatted
        assert "[INST] Tell me about NCA [/INST]" in formatted
    
    async def test_embed(self, ollama_adapter, mock_session):
        """Test the embed method."""
        # Configure mock response
        mock_response = MockResponse(status=200, data={
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        mock_session.post.return_value = mock_response
        
        # Call the embed method with a single text
        result = await ollama_adapter.embed("Test text")
        
        # Verify the correct API endpoint was called
        mock_session.post.assert_called_with(
            "http://localhost:11434/api/embeddings",
            json={"model": "llama3", "prompt": "Test text"}
        )
        
        # Verify the result
        assert "embeddings" in result
        assert result["embeddings"] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert "usage" in result
        assert result["metadata"]["embedding_size"] == 5
    
    async def test_embed_batch(self, ollama_adapter, mock_session):
        """Test the embed method with a batch of texts."""
        # Configure mock responses for multiple requests
        mock_responses = [
            MockResponse(status=200, data={"embedding": [0.1, 0.2, 0.3]}),
            MockResponse(status=200, data={"embedding": [0.4, 0.5, 0.6]})
        ]
        mock_session.post.side_effect = mock_responses
        
        # Call the embed method with multiple texts
        result = await ollama_adapter.embed(["Text 1", "Text 2"])
        
        # Verify the correct API endpoints were called
        mock_session.post.assert_has_calls([
            call("http://localhost:11434/api/embeddings", json={"model": "llama3", "prompt": "Text 1"}),
            call("http://localhost:11434/api/embeddings", json={"model": "llama3", "prompt": "Text 2"})
        ])
        
        # Verify the result contains both embeddings
        assert "embeddings" in result
        assert len(result["embeddings"]) == 2
        assert result["embeddings"][0] == [0.1, 0.2, 0.3]
        assert result["embeddings"][1] == [0.4, 0.5, 0.6]
    
    async def test_embed_error(self, ollama_adapter, mock_session):
        """Test error handling for embedding errors."""
        # Configure mock response for error
        mock_response = MockResponse(status=500, text="Internal Server Error")
        mock_session.post.return_value = mock_response
        
        # Call the method and expect an error
        with pytest.raises(OllamaError):
            await ollama_adapter.embed("Test text")
