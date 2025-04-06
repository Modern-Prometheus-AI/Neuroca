"""
Unit tests for the Integration Utilities module.

This module tests the utility functions in the integration.utils module, including:
1. Token counting
2. Prompt formatting
3. Response parsing
4. Input sanitization
5. Embedding creation
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from neuroca.integration.utils import (
    count_tokens,
    create_embedding,
    format_prompt,
    parse_response,
    sanitize_input,
)


class TestTokenCounting:
    """Test suite for token counting utilities."""
    
    def test_count_tokens_empty(self):
        """Test counting tokens for empty text."""
        assert count_tokens("") == 0
    
    def test_count_tokens_simple(self):
        """Test counting tokens for simple text."""
        # Use the fallback method since we can't guarantee tiktoken is available
        with patch('neuroca.integration.utils.TOKENIZER_TYPE', 'simple'):
            # Rough estimates based on number of words
            assert count_tokens("Hello world") == 2 * 1.3  # 2 words * 1.3 tokens/word
            assert count_tokens("This is a longer sentence with more tokens") == 8 * 1.3
    
    @pytest.mark.parametrize("model_name", [
        "gpt-3.5-turbo", "gpt-4", "text-embedding-ada-002", "text-davinci-003"
    ])
    def test_count_tokens_model_selection(self, model_name):
        """Test that model selection affects token counting logic."""
        # We can't test actual token counts without the tokenizers,
        # but we can ensure the function handles different models without error
        with patch('neuroca.integration.utils.TOKENIZER_TYPE', 'simple'):
            assert count_tokens("Test text", model=model_name) >= 0
    
    def test_count_tokens_with_tiktoken(self):
        """Test token counting with tiktoken if available."""
        # Mock tiktoken if available
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        
        with patch('neuroca.integration.utils.TOKENIZER_TYPE', 'tiktoken'), \
             patch('neuroca.integration.utils._tokenizers', {'cl100k_base': mock_encoding}), \
             patch('neuroca.integration.utils.tiktoken.get_encoding', return_value=mock_encoding):
            assert count_tokens("Test text", model="gpt-4") == 5
            mock_encoding.encode.assert_called_with("Test text")
    
    def test_count_tokens_with_transformers(self):
        """Test token counting with transformers if available."""
        # Mock transformers tokenizer if available
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4]  # 4 tokens
        
        with patch('neuroca.integration.utils.TOKENIZER_TYPE', 'transformers'), \
             patch('neuroca.integration.utils._tokenizers', {'gpt2': mock_tokenizer}), \
             patch('neuroca.integration.utils.AutoTokenizer.from_pretrained', return_value=mock_tokenizer):
            assert count_tokens("Test text", model="gpt-4") == 4
            mock_tokenizer.encode.assert_called_with("Test text")


class TestPromptFormatting:
    """Test suite for prompt formatting utilities."""
    
    def test_format_prompt_empty(self):
        """Test formatting an empty prompt."""
        assert format_prompt("", {}) == ""
    
    def test_format_prompt_no_variables(self):
        """Test formatting a prompt with no variables."""
        prompt = "This is a test prompt with no variables."
        assert format_prompt(prompt, {}) == prompt
    
    def test_format_prompt_with_variables(self):
        """Test formatting a prompt with variables."""
        template = "Hello, {name}! Your age is {age}."
        variables = {"name": "Alice", "age": 30}
        expected = "Hello, Alice! Your age is 30."
        assert format_prompt(template, variables) == expected
    
    def test_format_prompt_missing_variables(self):
        """Test formatting a prompt with missing variables."""
        template = "Hello, {name}! Your age is {age}."
        variables = {"name": "Alice"}
        
        # With preserve_unknown=True (default)
        assert format_prompt(template, variables) == "Hello, Alice! Your age is {age}."
        
        # With preserve_unknown=False
        assert format_prompt(template, variables, preserve_unknown=False) == "Hello, Alice! Your age is ."
    
    def test_format_prompt_with_complex_variables(self):
        """Test formatting a prompt with complex variables (dicts, lists)."""
        template = "Here is a list: {items} and a dict: {details}"
        variables = {
            "items": ["apple", "banana", "cherry"],
            "details": {"color": "red", "size": "large"}
        }
        result = format_prompt(template, variables)
        
        # The result should contain JSON stringified versions of the complex objects
        assert '["apple","banana","cherry"]' in result
        assert '"color":"red"' in result
        assert '"size":"large"' in result


class TestResponseParsing:
    """Test suite for response parsing utilities."""
    
    def test_parse_response_text(self):
        """Test parsing a text response."""
        response = "This is a plain text response."
        # For text format, the response should be returned as-is
        assert parse_response(response, "text") == response
    
    def test_parse_response_empty(self):
        """Test parsing an empty response."""
        assert parse_response("", "text") == ""
        assert parse_response("", "json") == ""
    
    def test_parse_response_json_clean(self):
        """Test parsing a clean JSON response."""
        json_data = {"name": "Alice", "age": 30}
        response = json.dumps(json_data)
        parsed = parse_response(response, "json")
        assert parsed == json_data
    
    def test_parse_response_json_with_code_block(self):
        """Test parsing a JSON response wrapped in a code block."""
        json_data = {"name": "Alice", "age": 30}
        response = f"```json\n{json.dumps(json_data)}\n```"
        parsed = parse_response(response, "json")
        assert parsed == json_data
    
    def test_parse_response_json_with_errors(self):
        """Test parsing a JSON response with common errors."""
        # Test with single quotes instead of double quotes
        response = "{'name': 'Alice', 'age': 30}"
        parsed = parse_response(response, "json")
        assert parsed == {"name": "Alice", "age": 30}
        
        # Test with trailing comma
        response = '{"name": "Alice", "age": 30,}'
        parsed = parse_response(response, "json")
        assert parsed == {"name": "Alice", "age": 30}
    
    def test_parse_response_list_from_json(self):
        """Test parsing a list from a JSON array."""
        json_data = ["apple", "banana", "cherry"]
        response = json.dumps(json_data)
        parsed = parse_response(response, "list")
        assert parsed == json_data
    
    def test_parse_response_list_from_bullets(self):
        """Test parsing a list from bullet points."""
        response = "- apple\n- banana\n- cherry"
        parsed = parse_response(response, "list")
        assert parsed == ["apple", "banana", "cherry"]
    
    def test_parse_response_list_from_numbered(self):
        """Test parsing a list from numbered points."""
        response = "1. apple\n2. banana\n3. cherry"
        parsed = parse_response(response, "list")
        assert parsed == ["apple", "banana", "cherry"]
    
    def test_parse_response_list_from_commas(self):
        """Test parsing a list from comma-separated values."""
        response = "apple, banana, cherry"
        parsed = parse_response(response, "list")
        assert parsed == ["apple", "banana", "cherry"]


class TestInputSanitization:
    """Test suite for input sanitization utilities."""
    
    def test_sanitize_input_empty(self):
        """Test sanitizing an empty input."""
        assert sanitize_input("") == ""
    
    def test_sanitize_input_clean(self):
        """Test sanitizing clean input."""
        text = "This is a clean input with no dangerous characters."
        assert sanitize_input(text) == text
    
    def test_sanitize_input_command_injection(self):
        """Test sanitizing input with potential command injection."""
        dangerous = "Run this command: `rm -rf /`"
        sanitized = sanitize_input(dangerous)
        assert "`" not in sanitized
        assert "rm -rf /" in sanitized  # The text is still there, but not the backticks
        
        dangerous = "Run this command: ls | grep password"
        sanitized = sanitize_input(dangerous)
        assert "|" not in sanitized
        
        dangerous = "Run this; echo 'Hacked'"
        sanitized = sanitize_input(dangerous)
        assert ";" not in sanitized
    
    def test_sanitize_input_truncation(self):
        """Test truncating input to maximum length."""
        long_text = "a" * 100
        max_length = 50
        truncated = sanitize_input(long_text, max_length=max_length)
        assert len(truncated) == max_length
        assert truncated == "a" * max_length


class TestEmbeddingCreation:
    """Test suite for embedding creation utilities."""
    
    async def test_create_embedding_missing_dependencies(self):
        """Test error handling when dependencies are missing."""
        with patch('neuroca.integration.utils.SentenceTransformer', side_effect=ImportError):
            with pytest.raises(ImportError):
                await create_embedding("Test text")
    
    async def test_create_embedding_basic(self):
        """Test basic embedding creation."""
        # Mock SentenceTransformer
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        with patch('neuroca.integration.utils.SentenceTransformer', return_value=mock_model):
            embedding = await create_embedding("Test text")
            
            # Verify the result
            assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_model.encode.assert_called_with("Test text")
    
    async def test_create_embedding_model_error(self):
        """Test error handling when the model fails."""
        # Mock SentenceTransformer initialization error
        with patch('neuroca.integration.utils.SentenceTransformer', side_effect=RuntimeError("Model error")):
            with pytest.raises(RuntimeError):
                await create_embedding("Test text")
        
        # Mock encoding error
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("Encoding error")
        
        with patch('neuroca.integration.utils.SentenceTransformer', return_value=mock_model):
            with pytest.raises(RuntimeError):
                await create_embedding("Test text")
    
    async def test_create_embedding_with_options(self):
        """Test embedding creation with custom options."""
        # Mock SentenceTransformer
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        with patch('neuroca.integration.utils.SentenceTransformer', return_value=mock_model):
            await create_embedding(
                text="Test text",
                model="custom-model",
                device="cuda"
            )
            
            # Verify SentenceTransformer was called with the right parameters
            from neuroca.integration.utils import SentenceTransformer
            SentenceTransformer.assert_called_with("custom-model", device="cuda")
