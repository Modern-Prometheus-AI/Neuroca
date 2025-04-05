"""
Utilities Module for NeuroCognitive Architecture (NCA) LLM Integration

This module provides utility functions for the LLM integration components,
including token counting, prompt formatting, response parsing, and input sanitization.

Functions:
    count_tokens: Count the number of tokens in a text
    format_prompt: Format a prompt with templates and variables
    parse_response: Parse a response from an LLM provider
    sanitize_input: Sanitize input to remove sensitive or problematic content
    create_embedding: Create an embedding for text using a local model
"""

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import different tokenizers, falling back as needed
try:
    import tiktoken
    TOKENIZER_TYPE = "tiktoken"
except ImportError:
    try:
        from transformers import AutoTokenizer
        TOKENIZER_TYPE = "transformers"
    except ImportError:
        TOKENIZER_TYPE = "simple"
        logger.warning("Neither tiktoken nor transformers is available. Using simple word-based tokenization.")

# Cache for tokenizers to avoid recreating them
_tokenizers = {}


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string.
    
    This function attempts to use the most appropriate tokenizer based on
    what's available in the environment and the model specified.
    
    Args:
        text: The text to count tokens for
        model: The model to use for tokenization (determines tokenization rules)
        
    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0
        
    # Use TikToken for OpenAI models if available
    if TOKENIZER_TYPE == "tiktoken":
        # Convert model names to encoding names
        encoding_name = model
        if model.startswith("gpt-3.5"):
            encoding_name = "cl100k_base"  # ChatGPT models
        elif model.startswith("gpt-4"):
            encoding_name = "cl100k_base"  # GPT-4 models
        elif model.startswith("text-embedding"):
            encoding_name = "cl100k_base"  # Embedding models
        elif model == "text-davinci-003" or model.startswith("text-davinci-002"):
            encoding_name = "p50k_base"
        elif model.startswith("code-davinci"):
            encoding_name = "p50k_base"
        
        # Get or create tokenizer
        if encoding_name not in _tokenizers:
            try:
                _tokenizers[encoding_name] = tiktoken.get_encoding(encoding_name)
            except KeyError:
                # Fall back to cl100k_base for unknown models
                logger.warning(f"Unknown model {model}, falling back to cl100k_base encoding")
                _tokenizers[encoding_name] = tiktoken.get_encoding("cl100k_base")
                
        # Count tokens
        return len(_tokenizers[encoding_name].encode(text))
        
    # Use Transformers for other models if available
    elif TOKENIZER_TYPE == "transformers":
        # Map to HuggingFace model names
        hf_model = model
        if model.startswith("gpt-3.5") or model.startswith("gpt-4"):
            hf_model = "gpt2"  # Closest tokenizer for GPT models
        elif model.startswith("claude"):
            hf_model = "facebook/opt-30b"  # Similar to Claude's tokenizer
        elif model.startswith("llama"):
            hf_model = "meta-llama/Llama-2-7b-hf"
        elif model.startswith("mistral"):
            hf_model = "mistralai/Mistral-7B-v0.1"
            
        # Get or create tokenizer
        if hf_model not in _tokenizers:
            try:
                _tokenizers[hf_model] = AutoTokenizer.from_pretrained(hf_model)
            except Exception as e:
                logger.warning(f"Failed to load tokenizer for {hf_model}: {str(e)}")
                # Fall back to GPT-2 tokenizer
                _tokenizers[hf_model] = AutoTokenizer.from_pretrained("gpt2")
                
        # Count tokens
        return len(_tokenizers[hf_model].encode(text))
        
    # Simple fallback using word count with a multiplier
    else:
        # Most models use about 1.3 tokens per word on average for English text
        return int(len(text.split()) * 1.3)
        

def format_prompt(template: str, variables: dict[str, Any], preserve_unknown: bool = True) -> str:
    """
    Format a prompt template with variables.
    
    Args:
        template: The prompt template with {variable_name} placeholders
        variables: Dictionary of variable names and values
        preserve_unknown: Whether to preserve unknown variables as is
        
    Returns:
        The formatted prompt
    """
    if not template:
        return ""
        
    # Define a function to handle each match
    def replace_var(match):
        var_name = match.group(1)
        if var_name in variables:
            value = variables[var_name]
            # Convert non-string values to string
            if not isinstance(value, str):
                if isinstance(value, (dict, list)):
                    return json.dumps(value, ensure_ascii=False)
                return str(value)
            return value
        elif preserve_unknown:
            return f"{{{var_name}}}"
        else:
            return ""
            
    # Replace {variable_name} with the corresponding value
    return re.sub(r"\{([^{}]+)\}", replace_var, template)
    
    
def parse_response(response: str, expected_format: str = "text") -> Any:
    """
    Parse a response from an LLM provider into the expected format.
    
    Args:
        response: The response string from the LLM
        expected_format: The expected format (text, json, list, etc.)
        
    Returns:
        The parsed response in the expected format
        
    Raises:
        ValueError: If the response cannot be parsed into the expected format
    """
    if expected_format == "text" or not response:
        return response
        
    if expected_format == "json":
        # Try to extract JSON from the response
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(json_pattern, response)
        json_str = match.group(1) if match else response
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try to fix common JSON errors
            json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)  # Replace single quotes with double quotes in keys
            json_str = re.sub(r",\s*}", "}", json_str)  # Remove trailing commas
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {str(e)}")
                raise ValueError(f"Response is not valid JSON: {json_str}")
                
    elif expected_format == "list":
        # Try to extract a list from the response
        if response.startswith("[") and response.endswith("]"):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
                
        # Try to extract a list from each line
        items = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                items.append(line[2:].strip())
            elif re.match(r"^\d+\.\s", line):
                items.append(re.sub(r"^\d+\.\s", "", line).strip())
                
        if items:
            return items
            
        # Fall back to splitting by commas
        return [item.strip() for item in response.split(",")]
        
    # For other formats, return the raw response
    return response
    
    
def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize input to remove sensitive or problematic content.
    
    Args:
        text: The input text to sanitize
        max_length: Optional maximum length for the text
        
    Returns:
        The sanitized text
    """
    if not text:
        return ""
        
    # Remove potential command injection patterns
    text = re.sub(r"[`\\|;<>&$]", "", text)
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]
        
    return text
    
    
async def create_embedding(
    text: str, 
    model: str = "sentence-transformers/all-mpnet-base-v2",
    device: str = "cpu"
) -> list[float]:
    """
    Create an embedding for text using a local model.
    
    Args:
        text: The text to embed
        model: The model to use for embedding
        device: The device to run the model on (cpu, cuda, etc.)
        
    Returns:
        The embedding vector as a list of floats
        
    Raises:
        ImportError: If the required dependencies are not installed
        RuntimeError: If embedding creation fails
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error("sentence_transformers is required for local embeddings")
        raise ImportError("sentence_transformers is required for local embeddings. Install with 'pip install sentence-transformers'")
        
    # Get or create the model
    cache_key = f"{model}_{device}"
    if cache_key not in _tokenizers:
        try:
            _tokenizers[cache_key] = SentenceTransformer(model, device=device)
        except Exception as e:
            logger.error(f"Failed to load embedding model {model}: {str(e)}")
            raise RuntimeError(f"Failed to load embedding model: {str(e)}")
            
    # Create embedding
    try:
        embedding = _tokenizers[cache_key].encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to create embedding: {str(e)}")
        raise RuntimeError(f"Failed to create embedding: {str(e)}")
