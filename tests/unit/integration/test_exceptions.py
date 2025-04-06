"""
Unit tests for the Integration Exceptions module.

This module tests the exception classes in the LLM integration layer, ensuring
that they behave correctly and provide the expected functionality.
"""


from neuroca.integration.exceptions import (
    AdapterExecutionError,
    AuthenticationError,
    ConfigurationError,
    ContextLengthExceededError,
    FeatureNotSupportedError,
    GoalContextError,
    HealthAwarenessError,
    InvalidRequestError,
    LLMIntegrationError,
    MemoryContextError,
    ModelNotAvailableError,
    ProviderAPIError,
    ProviderConnectionError,
    ProviderNotFoundError,
    ProviderTimeoutError,
    RateLimitError,
    ResourceExhaustedError,
    ResponseParsingError,
)


class TestBaseException:
    """Test the base LLMIntegrationError class."""
    
    def test_constructor(self):
        """Test constructor with message."""
        error = LLMIntegrationError("Test error message")
        assert error.message == "Test error message"
        assert str(error) == "Test error message"
    
    def test_inheritance(self):
        """Test that LLMIntegrationError inherits from Exception."""
        error = LLMIntegrationError("Test error")
        assert isinstance(error, Exception)


class TestProviderExceptions:
    """Test provider-related exception classes."""
    
    def test_provider_not_found_error(self):
        """Test ProviderNotFoundError."""
        error = ProviderNotFoundError("Provider 'test' not found")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Provider 'test' not found"
    
    def test_model_not_available_error(self):
        """Test ModelNotAvailableError."""
        error = ModelNotAvailableError("Model 'gpt-5' not available")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Model 'gpt-5' not available"
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid API key")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Invalid API key"


class TestRateLimitError:
    """Test RateLimitError class."""
    
    def test_constructor_with_retry_after(self):
        """Test constructor with retry_after parameter."""
        error = RateLimitError("Rate limit exceeded", retry_after=60.0)
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Rate limit exceeded"
        assert error.retry_after == 60.0
    
    def test_constructor_without_retry_after(self):
        """Test constructor without retry_after parameter."""
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Rate limit exceeded"
        assert error.retry_after is None


class TestContextLengthExceededError:
    """Test ContextLengthExceededError class."""
    
    def test_constructor_with_token_info(self):
        """Test constructor with token information."""
        error = ContextLengthExceededError(
            "Context length exceeded",
            max_tokens=4096,
            actual_tokens=5000
        )
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Context length exceeded"
        assert error.max_tokens == 4096
        assert error.actual_tokens == 5000
    
    def test_constructor_without_token_info(self):
        """Test constructor without token information."""
        error = ContextLengthExceededError("Context length exceeded")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Context length exceeded"
        assert error.max_tokens is None
        assert error.actual_tokens is None


class TestProviderAPIError:
    """Test ProviderAPIError class."""
    
    def test_constructor_with_details(self):
        """Test constructor with status code and response body."""
        error = ProviderAPIError(
            "API error occurred",
            status_code=400,
            response_body='{"error": "Bad request"}'
        )
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "API error occurred"
        assert error.status_code == 400
        assert error.response_body == '{"error": "Bad request"}'
    
    def test_constructor_without_details(self):
        """Test constructor without status code and response body."""
        error = ProviderAPIError("API error occurred")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "API error occurred"
        assert error.status_code is None
        assert error.response_body is None


class TestAdapterExecutionError:
    """Test AdapterExecutionError class."""
    
    def test_constructor_with_details(self):
        """Test constructor with provider and model details."""
        error = AdapterExecutionError(
            "Execution failed",
            provider="openai",
            model="gpt-4"
        )
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Execution failed"
        assert error.provider == "openai"
        assert error.model == "gpt-4"
    
    def test_constructor_without_details(self):
        """Test constructor without provider and model details."""
        error = AdapterExecutionError("Execution failed")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Execution failed"
        assert error.provider is None
        assert error.model is None


class TestOtherExceptions:
    """Test other exception classes."""
    
    def test_invalid_request_error(self):
        """Test InvalidRequestError."""
        error = InvalidRequestError("Invalid request parameters")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Invalid request parameters"
    
    def test_provider_timeout_error(self):
        """Test ProviderTimeoutError."""
        error = ProviderTimeoutError("Request timed out after 60s")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Request timed out after 60s"
    
    def test_provider_connection_error(self):
        """Test ProviderConnectionError."""
        error = ProviderConnectionError("Failed to connect to API")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Failed to connect to API"
    
    def test_response_parsing_error(self):
        """Test ResponseParsingError."""
        error = ResponseParsingError("Failed to parse JSON response")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Failed to parse JSON response"
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid configuration")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Invalid configuration"
    
    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError."""
        error = ResourceExhaustedError("API quota exceeded")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "API quota exceeded"
    
    def test_feature_not_supported_error(self):
        """Test FeatureNotSupportedError."""
        error = FeatureNotSupportedError("Function calling not supported")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Function calling not supported"
    
    def test_memory_context_error(self):
        """Test MemoryContextError."""
        error = MemoryContextError("Failed to retrieve memories")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Failed to retrieve memories"
    
    def test_health_awareness_error(self):
        """Test HealthAwarenessError."""
        error = HealthAwarenessError("Failed to get health state")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Failed to get health state"
    
    def test_goal_context_error(self):
        """Test GoalContextError."""
        error = GoalContextError("Failed to retrieve active goals")
        assert isinstance(error, LLMIntegrationError)
        assert error.message == "Failed to retrieve active goals"
