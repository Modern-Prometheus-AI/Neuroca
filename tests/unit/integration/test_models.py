"""
Unit tests for the Integration Models module.

This module tests the data models used in the LLM integration layer, including:
1. TokenUsage
2. ProviderConfig
3. LLMRequest
4. LLMResponse
5. LLMError
"""

import time

from neuroca.integration.models import (
    LLMError,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderConfig,
    ResponseType,
    TokenUsage,
)


class TestTokenUsage:
    """Test suite for the TokenUsage class."""
    
    def test_init_defaults(self):
        """Test initialization with default values."""
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
    
    def test_init_with_values(self):
        """Test initialization with specific values."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        usage_dict = usage.to_dict()
        assert usage_dict == {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        usage_dict = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        usage = TokenUsage.from_dict(usage_dict)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30


class TestProviderConfig:
    """Test suite for the ProviderConfig class."""
    
    def test_init_defaults(self):
        """Test initialization with default values."""
        config = ProviderConfig()
        assert config.api_key is None
        assert config.api_base is None
        assert config.organization_id is None
        assert config.default_model is None
        assert config.request_timeout == 60.0
        assert config.max_retries == 3
        assert config.proxy is None
        assert isinstance(config.additional_headers, dict)
        assert isinstance(config.additional_params, dict)
    
    def test_init_with_values(self):
        """Test initialization with specific values."""
        config = ProviderConfig(
            api_key="test_key",
            api_base="https://api.example.com",
            organization_id="org_123",
            default_model="gpt-4",
            request_timeout=30.0,
            max_retries=5,
            proxy="http://proxy.example.com",
            additional_headers={"X-Custom": "Value"},
            additional_params={"custom_param": "value"}
        )
        assert config.api_key == "test_key"
        assert config.api_base == "https://api.example.com"
        assert config.organization_id == "org_123"
        assert config.default_model == "gpt-4"
        assert config.request_timeout == 30.0
        assert config.max_retries == 5
        assert config.proxy == "http://proxy.example.com"
        assert config.additional_headers == {"X-Custom": "Value"}
        assert config.additional_params == {"custom_param": "value"}
    
    def test_to_dict_with_masking(self):
        """Test conversion to dictionary with sensitive info masking."""
        config = ProviderConfig(api_key="sk_1234567890abcdef")
        config_dict = config.to_dict(mask_secrets=True)
        assert "api_key" in config_dict
        assert config_dict["api_key"] != "sk_1234567890abcdef"
        assert config_dict["api_key"].startswith("**********")
        assert config_dict["api_key"].endswith("cdef")  # Last 4 chars preserved
    
    def test_to_dict_without_masking(self):
        """Test conversion to dictionary without sensitive info masking."""
        config = ProviderConfig(api_key="sk_1234567890abcdef")
        config_dict = config.to_dict(mask_secrets=False)
        assert config_dict["api_key"] == "sk_1234567890abcdef"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        config_dict = {
            "api_key": "test_key",
            "api_base": "https://api.example.com",
            "default_model": "gpt-4"
        }
        config = ProviderConfig.from_dict(config_dict)
        assert config.api_key == "test_key"
        assert config.api_base == "https://api.example.com"
        assert config.default_model == "gpt-4"


class TestLLMRequest:
    """Test suite for the LLMRequest class."""
    
    def test_init_with_required_values(self):
        """Test initialization with only required values."""
        request = LLMRequest(provider="openai")
        assert request.provider == "openai"
        assert request.model is None
        assert request.prompt is None
        assert isinstance(request.additional_params, dict)
        assert request.created_at > 0  # Should be a timestamp
    
    def test_init_with_all_values(self):
        """Test initialization with all values."""
        now = time.time()
        request = LLMRequest(
            provider="openai",
            model="gpt-4",
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            presence_penalty=0.1,
            frequency_penalty=0.2,
            stop_sequences=["END"],
            additional_params={"custom": "value"},
            created_at=now
        )
        assert request.provider == "openai"
        assert request.model == "gpt-4"
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        assert request.top_p == 0.9
        assert request.top_k == 50
        assert request.presence_penalty == 0.1
        assert request.frequency_penalty == 0.2
        assert request.stop_sequences == ["END"]
        assert request.additional_params == {"custom": "value"}
        assert request.created_at == now
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = time.time()
        request = LLMRequest(
            provider="openai",
            model="gpt-4",
            prompt="Test prompt",
            created_at=now
        )
        request_dict = request.to_dict()
        assert request_dict["provider"] == "openai"
        assert request_dict["model"] == "gpt-4"
        assert request_dict["prompt"] == "Test prompt"
        assert request_dict["created_at"] == now
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        now = time.time()
        request_dict = {
            "provider": "openai",
            "model": "gpt-4",
            "prompt": "Test prompt",
            "max_tokens": 100,
            "created_at": now
        }
        request = LLMRequest.from_dict(request_dict)
        assert request.provider == "openai"
        assert request.model == "gpt-4"
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        assert request.created_at == now


class TestLLMResponse:
    """Test suite for the LLMResponse class."""
    
    def test_init_with_required_values(self):
        """Test initialization with only required values."""
        response = LLMResponse(
            provider="openai",
            model="gpt-4",
            content="Test response"
        )
        assert response.provider == "openai"
        assert response.model == "gpt-4"
        assert response.content == "Test response"
        assert response.raw_response is None
        assert isinstance(response.metadata, dict)
        assert response.usage is None
        assert response.cost is None
        assert response.request is None
        assert response.created_at > 0  # Should be a timestamp
        assert response.elapsed_time is None
        assert response.response_type == ResponseType.TEXT
    
    def test_init_with_all_values(self):
        """Test initialization with all values."""
        now = time.time()
        request = LLMRequest(provider="openai", model="gpt-4", prompt="Test prompt")
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        
        response = LLMResponse(
            provider="openai",
            model="gpt-4",
            content="Test response",
            raw_response={"choices": [{"text": "Test response"}]},
            metadata={"source": "test"},
            usage=usage,
            cost=0.05,
            request=request,
            created_at=now,
            elapsed_time=0.5,
            response_type=ResponseType.CHAT
        )
        
        assert response.provider == "openai"
        assert response.model == "gpt-4"
        assert response.content == "Test response"
        assert response.raw_response == {"choices": [{"text": "Test response"}]}
        assert response.metadata == {"source": "test"}
        assert response.usage == usage
        assert response.cost == 0.05
        assert response.request == request
        assert response.created_at == now
        assert response.elapsed_time == 0.5
        assert response.response_type == ResponseType.CHAT
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = time.time()
        request = LLMRequest(provider="openai", model="gpt-4", prompt="Test prompt")
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        
        response = LLMResponse(
            provider="openai",
            model="gpt-4",
            content="Test response",
            usage=usage,
            request=request,
            created_at=now,
            response_type=ResponseType.CHAT
        )
        
        response_dict = response.to_dict()
        assert response_dict["provider"] == "openai"
        assert response_dict["model"] == "gpt-4"
        assert response_dict["content"] == "Test response"
        assert response_dict["usage"] == usage.to_dict()
        assert response_dict["request"] == request.to_dict()
        assert response_dict["created_at"] == now
        assert response_dict["response_type"] == "chat"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        now = time.time()
        usage_dict = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        request_dict = {
            "provider": "openai",
            "model": "gpt-4",
            "prompt": "Test prompt"
        }
        
        response_dict = {
            "provider": "openai",
            "model": "gpt-4",
            "content": "Test response",
            "usage": usage_dict,
            "request": request_dict,
            "created_at": now,
            "response_type": "chat"
        }
        
        response = LLMResponse.from_dict(response_dict)
        assert response.provider == "openai"
        assert response.model == "gpt-4"
        assert response.content == "Test response"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 20
        assert response.usage.total_tokens == 30
        assert response.request.provider == "openai"
        assert response.request.model == "gpt-4"
        assert response.request.prompt == "Test prompt"
        assert response.created_at == now
        assert response.response_type == ResponseType.CHAT


class TestLLMError:
    """Test suite for the LLMError class."""
    
    def test_init_with_required_values(self):
        """Test initialization with only required values."""
        error = LLMError(
            provider="openai",
            error_type="rate_limit",
            message="Rate limit exceeded"
        )
        assert error.provider == "openai"
        assert error.error_type == "rate_limit"
        assert error.message == "Rate limit exceeded"
        assert error.request is None
        assert error.created_at > 0  # Should be a timestamp
        assert error.retryable is False
    
    def test_init_with_all_values(self):
        """Test initialization with all values."""
        now = time.time()
        request = LLMRequest(provider="openai", model="gpt-4", prompt="Test prompt")
        
        error = LLMError(
            provider="openai",
            error_type="rate_limit",
            message="Rate limit exceeded",
            request=request,
            created_at=now,
            retryable=True
        )
        
        assert error.provider == "openai"
        assert error.error_type == "rate_limit"
        assert error.message == "Rate limit exceeded"
        assert error.request == request
        assert error.created_at == now
        assert error.retryable is True
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = time.time()
        request = LLMRequest(provider="openai", model="gpt-4", prompt="Test prompt")
        
        error = LLMError(
            provider="openai",
            error_type="rate_limit",
            message="Rate limit exceeded",
            request=request,
            created_at=now,
            retryable=True
        )
        
        error_dict = error.to_dict()
        assert error_dict["provider"] == "openai"
        assert error_dict["error_type"] == "rate_limit"
        assert error_dict["message"] == "Rate limit exceeded"
        assert error_dict["request"] == request.to_dict()
        assert error_dict["created_at"] == now
        assert error_dict["retryable"] is True
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        now = time.time()
        request_dict = {
            "provider": "openai",
            "model": "gpt-4",
            "prompt": "Test prompt"
        }
        
        error_dict = {
            "provider": "openai",
            "error_type": "rate_limit",
            "message": "Rate limit exceeded",
            "request": request_dict,
            "created_at": now,
            "retryable": True
        }
        
        error = LLMError.from_dict(error_dict)
        assert error.provider == "openai"
        assert error.error_type == "rate_limit"
        assert error.message == "Rate limit exceeded"
        assert error.request.provider == "openai"
        assert error.request.model == "gpt-4"
        assert error.request.prompt == "Test prompt"
        assert error.created_at == now
        assert error.retryable is True


class TestResponseType:
    """Test suite for the ResponseType enum."""
    
    def test_enum_values(self):
        """Test enum values."""
        assert ResponseType.TEXT.value == "text"
        assert ResponseType.CHAT.value == "chat"
        assert ResponseType.EMBEDDING.value == "embedding"
        assert ResponseType.FUNCTION_CALL.value == "function_call"
        assert ResponseType.TOOL_USE.value == "tool_use"
        assert ResponseType.ERROR.value == "error"


class TestLLMProvider:
    """Test suite for the LLMProvider enum."""
    
    def test_enum_values(self):
        """Test enum values."""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.COHERE.value == "cohere"
        assert LLMProvider.HUGGINGFACE.value == "huggingface"
        assert LLMProvider.VERTEXAI.value == "vertexai"
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.LOCAL.value == "local"
        assert LLMProvider.CUSTOM.value == "custom"
