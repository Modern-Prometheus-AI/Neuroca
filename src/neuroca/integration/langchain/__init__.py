"""
LangChain Integration Module for NeuroCognitive Architecture (NCA)

This module provides integration between the NeuroCognitive Architecture (NCA) system
and LangChain, enabling seamless use of LangChain's capabilities within the NCA framework.
It exposes key components, utilities, and adapters for working with LangChain models,
chains, memory systems, and other features.

The integration is designed to support the three-tiered memory system of NCA while
leveraging LangChain's powerful abstractions for language model interactions.

Usage Examples:
    # Basic usage with a LangChain LLM
    from neuroca.integration.langchain import LangChainModelAdapter
    from langchain.llms import OpenAI
    
    llm = OpenAI(temperature=0.7)
    adapter = LangChainModelAdapter(llm)
    response = adapter.generate("Tell me about cognitive architectures")
    
    # Using LangChain with NCA memory systems
    from neuroca.integration.langchain import MemoryAdapter
    from neuroca.memory import WorkingMemory
    
    memory = WorkingMemory()
    memory_adapter = MemoryAdapter(memory)
    chain = memory_adapter.create_chain_with_memory(llm)

Version: 0.1.0
"""

import logging
from typing import Any

# Set up module-level logger
logger = logging.getLogger(__name__)

# Import core LangChain components that we'll use or wrap
try:
    import langchain
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.chains.base import Chain
    from langchain.embeddings.base import Embeddings
    from langchain.llms.base import BaseLLM
    from langchain.memory import ConversationBufferMemory
    from langchain.schema import BaseMemory, Document
    from langchain.vectorstores.base import VectorStore
    
    LANGCHAIN_AVAILABLE = True
    logger.debug("LangChain successfully imported (version: %s)", langchain.__version__)
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain import failed: %s. LangChain integration will be unavailable.", str(e))

# Import NCA components needed for integration
try:
    from neuroca.core.exceptions import ConfigurationError, IntegrationError
    from neuroca.core.models import BaseModel
    from neuroca.memory.base import BaseMemory as NCABaseMemory
except ImportError as e:
    logger.error("Failed to import required NCA components: %s", str(e))
    raise ImportError(f"NCA core components not available: {str(e)}")

# Version information
__version__ = "0.1.0"


class LangChainIntegrationError(IntegrationError):
    """Exception raised for errors in the LangChain integration."""
    pass


class LangChainNotAvailableError(LangChainIntegrationError):
    """Exception raised when LangChain is not available but its functionality is requested."""
    
    def __init__(self, message: str = "LangChain is not installed. Install with 'pip install langchain'."):
        super().__init__(message)


def ensure_langchain_available() -> None:
    """
    Ensures that LangChain is available for use.
    
    Raises:
        LangChainNotAvailableError: If LangChain is not installed.
    """
    if not LANGCHAIN_AVAILABLE:
        logger.error("Operation requires LangChain but it's not available")
        raise LangChainNotAvailableError()


class LangChainModelAdapter(BaseModel):
    """
    Adapter for using LangChain language models within the NCA framework.
    
    This adapter wraps LangChain's LLM implementations to make them compatible
    with NCA's model interfaces and expectations.
    
    Attributes:
        llm (BaseLLM): The underlying LangChain language model.
        model_kwargs (Dict[str, Any]): Additional keyword arguments for the model.
    """
    
    def __init__(self, llm: 'BaseLLM', **kwargs: Any):
        """
        Initialize the LangChain model adapter.
        
        Args:
            llm: A LangChain language model instance.
            **kwargs: Additional configuration parameters.
            
        Raises:
            LangChainNotAvailableError: If LangChain is not installed.
            TypeError: If the provided llm is not a LangChain BaseLLM instance.
        """
        ensure_langchain_available()
        
        if not isinstance(llm, BaseLLM):
            raise TypeError(f"Expected a LangChain BaseLLM instance, got {type(llm).__name__}")
        
        super().__init__(**kwargs)
        self.llm = llm
        self.model_kwargs = kwargs
        logger.debug(f"Initialized LangChainModelAdapter with {type(llm).__name__}")
    
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate a response from the language model.
        
        Args:
            prompt: The input prompt for the language model.
            **kwargs: Additional parameters to pass to the model.
            
        Returns:
            The generated text response.
            
        Raises:
            LangChainIntegrationError: If an error occurs during generation.
        """
        try:
            logger.debug(f"Generating response for prompt: {prompt[:50]}...")
            response = self.llm(prompt, **kwargs)
            logger.debug(f"Generated response: {response[:50]}...")
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            raise LangChainIntegrationError(f"Error generating response: {str(e)}") from e
    
    def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the underlying LangChain model.
        
        Returns:
            A dictionary containing model information.
        """
        return {
            "type": "langchain",
            "model_type": type(self.llm).__name__,
            "model_id": getattr(self.llm, "model_name", "unknown"),
            "provider": self._get_provider_name(),
            "parameters": self.model_kwargs
        }
    
    def _get_provider_name(self) -> str:
        """
        Extract the provider name from the LangChain model.
        
        Returns:
            The name of the provider (e.g., "openai", "anthropic").
        """
        llm_class = type(self.llm).__name__.lower()
        if "openai" in llm_class:
            return "openai"
        elif "anthropic" in llm_class:
            return "anthropic"
        elif "huggingface" in llm_class:
            return "huggingface"
        else:
            return "unknown"


class MemoryAdapter:
    """
    Adapter for integrating NCA memory systems with LangChain's memory components.
    
    This adapter allows NCA's memory tiers to be used within LangChain chains
    and provides utilities for converting between the two memory systems.
    
    Attributes:
        nca_memory (NCABaseMemory): The NCA memory system to adapt.
        langchain_memory (Optional[BaseMemory]): The corresponding LangChain memory component.
    """
    
    def __init__(self, nca_memory: 'NCABaseMemory'):
        """
        Initialize the memory adapter.
        
        Args:
            nca_memory: An NCA memory system instance.
            
        Raises:
            LangChainNotAvailableError: If LangChain is not installed.
            TypeError: If the provided memory is not an NCA memory instance.
        """
        ensure_langchain_available()
        
        if not isinstance(nca_memory, NCABaseMemory):
            raise TypeError(f"Expected an NCA BaseMemory instance, got {type(nca_memory).__name__}")
        
        self.nca_memory = nca_memory
        self.langchain_memory = self._create_langchain_memory()
        logger.debug(f"Initialized MemoryAdapter for {type(nca_memory).__name__}")
    
    def _create_langchain_memory(self) -> 'BaseMemory':
        """
        Create a LangChain memory component that corresponds to the NCA memory.
        
        Returns:
            A LangChain memory component.
            
        Raises:
            LangChainIntegrationError: If the memory type cannot be mapped.
        """
        try:
            # This is a simplified implementation - in a real system, we would have
            # more sophisticated mapping between NCA memory types and LangChain memory types
            memory_type = type(self.nca_memory).__name__
            
            if "Working" in memory_type:
                return ConversationBufferMemory(output_key="output")
            elif "Episodic" in memory_type:
                # For episodic memory, we might use a more sophisticated memory type
                return ConversationBufferMemory(output_key="output")
            else:
                # Default to basic conversation memory
                return ConversationBufferMemory(output_key="output")
        except Exception as e:
            logger.error(f"Error creating LangChain memory: {str(e)}", exc_info=True)
            raise LangChainIntegrationError(f"Failed to create LangChain memory: {str(e)}") from e
    
    def create_chain_with_memory(self, llm: 'BaseLLM', **kwargs: Any) -> 'Chain':
        """
        Create a LangChain chain that uses the adapted memory.
        
        Args:
            llm: A LangChain language model.
            **kwargs: Additional parameters for chain creation.
            
        Returns:
            A LangChain chain with memory integration.
            
        Raises:
            LangChainIntegrationError: If chain creation fails.
        """
        try:
            from langchain.chains import ConversationChain
            
            chain = ConversationChain(
                llm=llm,
                memory=self.langchain_memory,
                verbose=kwargs.get("verbose", False)
            )
            logger.debug(f"Created chain with memory: {type(chain).__name__}")
            return chain
        except Exception as e:
            logger.error(f"Error creating chain with memory: {str(e)}", exc_info=True)
            raise LangChainIntegrationError(f"Failed to create chain with memory: {str(e)}") from e
    
    def sync_memories(self) -> None:
        """
        Synchronize the state between NCA memory and LangChain memory.
        
        This ensures that changes in one memory system are reflected in the other.
        
        Raises:
            LangChainIntegrationError: If synchronization fails.
        """
        try:
            # Implementation would depend on the specific memory types
            # This is a placeholder for the actual synchronization logic
            logger.debug("Synchronizing memories between NCA and LangChain")
            # Example: Copy conversation history from LangChain to NCA
            if hasattr(self.langchain_memory, "chat_memory") and hasattr(self.langchain_memory.chat_memory, "messages"):
                # Process and transfer messages
                pass
        except Exception as e:
            logger.error(f"Error synchronizing memories: {str(e)}", exc_info=True)
            raise LangChainIntegrationError(f"Failed to synchronize memories: {str(e)}") from e


class CallbackHandler(BaseCallbackHandler):
    """
    Custom callback handler for LangChain operations.
    
    This handler allows NCA to monitor and respond to events during
    LangChain operations, such as LLM calls, chain executions, etc.
    """
    
    def __init__(self, **kwargs: Any):
        """
        Initialize the callback handler.
        
        Args:
            **kwargs: Configuration parameters for the handler.
        """
        ensure_langchain_available()
        super().__init__()
        self.config = kwargs
        logger.debug("Initialized LangChain callback handler")
    
    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> None:
        """Called when LLM starts processing."""
        logger.debug(f"LLM started: {serialized.get('name', 'unknown')}")
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM completes processing."""
        logger.debug("LLM completed processing")
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM encounters an error."""
        logger.error(f"LLM error: {str(error)}", exc_info=True)
    
    def on_chain_start(self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain starts processing."""
        logger.debug(f"Chain started: {serialized.get('name', 'unknown')}")
    
    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain completes processing."""
        logger.debug("Chain completed processing")
    
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a chain encounters an error."""
        logger.error(f"Chain error: {str(error)}", exc_info=True)


# Export public components
__all__ = [
    'LangChainModelAdapter',
    'MemoryAdapter',
    'CallbackHandler',
    'LangChainIntegrationError',
    'LangChainNotAvailableError',
    'ensure_langchain_available',
    'LANGCHAIN_AVAILABLE',
    '__version__',
]

# Perform initialization checks
if not LANGCHAIN_AVAILABLE:
    logger.warning(
        "LangChain is not available. Some functionality will be limited. "
        "Install LangChain with 'pip install langchain' to enable full functionality."
    )

logger.info(f"LangChain integration module initialized (version: {__version__})")