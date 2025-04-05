"""
Context Injection Module for NeuroCognitive Architecture

This module provides functionality for injecting relevant context into LLM prompts
based on the current conversation state, memory retrieval, and cognitive processing.
It handles context window management, prioritization of information, and seamless
integration with the memory tiers of the NCA system.

The module implements strategies for:
1. Determining what context is relevant to inject
2. Managing context window limitations
3. Prioritizing information based on cognitive relevance
4. Formatting context for different LLM providers
5. Tracking context usage and effectiveness

Usage:
    context_manager = ContextInjectionManager(config)
    enhanced_prompt = context_manager.inject_context(
        prompt="Tell me about neural networks",
        conversation_history=history,
        memory_retrieval_results=memory_results
    )
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union

from neuroca.config.settings import ContextInjectionConfig
from neuroca.core.exceptions import ContextWindowExceededError, InvalidContextFormatError
from neuroca.memory.retrieval import MemoryRetrievalResult

# Configure logger
logger = logging.getLogger(__name__)


class ContextPriority(Enum):
    """Enumeration of priority levels for context elements."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class ContextElement:
    """Represents a single element of context to be injected."""
    content: str
    source: str  # e.g., "working_memory", "episodic_memory", "semantic_memory"
    priority: ContextPriority
    token_count: int
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ContextFormat(Enum):
    """Supported context formatting styles for different LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    CUSTOM = "custom"


class ContextInjectionStrategy(Enum):
    """Different strategies for injecting context."""
    PREPEND = "prepend"  # Add context before the prompt
    APPEND = "append"    # Add context after the prompt
    INTERLEAVE = "interleave"  # Mix context with conversation turns
    STRUCTURED = "structured"  # Use a structured format (e.g., JSON)


class ContextInjectionManager:
    """
    Manages the injection of relevant context into LLM prompts.
    
    This class handles the selection, prioritization, formatting, and injection
    of context elements into prompts sent to language models, ensuring optimal
    use of the context window while maintaining relevance.
    """
    
    def __init__(self, config: ContextInjectionConfig):
        """
        Initialize the context injection manager.
        
        Args:
            config: Configuration settings for context injection
        """
        self.config = config
        self.max_tokens = config.max_context_window_tokens
        self.reserved_tokens = config.reserved_tokens_for_response
        self.format = ContextFormat(config.context_format)
        self.strategy = ContextInjectionStrategy(config.injection_strategy)
        self.token_counter = self._get_token_counter()
        logger.debug(f"Initialized ContextInjectionManager with format={self.format.value}, "
                    f"strategy={self.strategy.value}, max_tokens={self.max_tokens}")
    
    def _get_token_counter(self):
        """
        Returns the appropriate token counting function based on configuration.
        
        Different LLMs may have different tokenization methods, so this allows
        for flexibility in how tokens are counted.
        
        Returns:
            A function that counts tokens in a string
        """
        # In a real implementation, this would use the appropriate tokenizer
        # for the selected LLM provider
        if self.format == ContextFormat.OPENAI:
            # This is a placeholder - in production code, you would use the actual tokenizer
            return lambda text: len(text.split())
        elif self.format == ContextFormat.ANTHROPIC:
            return lambda text: len(text.split())
        elif self.format == ContextFormat.GOOGLE:
            return lambda text: len(text.split())
        else:
            # Default simple tokenizer (word-based)
            return lambda text: len(text.split())
    
    def inject_context(
        self,
        prompt: str,
        conversation_history: list[dict[str, str]] = None,
        memory_retrieval_results: list[MemoryRetrievalResult] = None,
        system_instructions: str = None,
        additional_context: dict[str, Any] = None
    ) -> Union[str, dict[str, Any]]:
        """
        Inject relevant context into the prompt based on available information.
        
        Args:
            prompt: The user's current prompt/query
            conversation_history: Previous conversation turns
            memory_retrieval_results: Results from memory retrieval systems
            system_instructions: System-level instructions for the LLM
            additional_context: Any additional context to consider
            
        Returns:
            Enhanced prompt with injected context, formatted appropriately for the target LLM
            
        Raises:
            ContextWindowExceededError: If the resulting context exceeds the maximum token limit
            InvalidContextFormatError: If the context cannot be properly formatted
        """
        logger.debug(f"Injecting context for prompt: {prompt[:50]}...")
        
        # Initialize with empty lists if None
        conversation_history = conversation_history or []
        memory_retrieval_results = memory_retrieval_results or []
        additional_context = additional_context or {}
        
        # 1. Prepare context elements from various sources
        context_elements = self._prepare_context_elements(
            prompt=prompt,
            conversation_history=conversation_history,
            memory_retrieval_results=memory_retrieval_results,
            system_instructions=system_instructions,
            additional_context=additional_context
        )
        
        # 2. Prioritize and select context elements to fit within token limits
        selected_elements = self._select_context_elements(
            context_elements=context_elements,
            prompt_tokens=self.token_counter(prompt)
        )
        
        # 3. Format the selected context elements according to the chosen strategy
        try:
            enhanced_prompt = self._format_context(
                prompt=prompt,
                selected_elements=selected_elements,
                conversation_history=conversation_history,
                system_instructions=system_instructions
            )
        except Exception as e:
            logger.error(f"Error formatting context: {str(e)}")
            raise InvalidContextFormatError(f"Failed to format context: {str(e)}")
        
        # 4. Verify the final token count is within limits
        final_token_count = self.token_counter(enhanced_prompt) if isinstance(enhanced_prompt, str) else \
                           self._estimate_structured_token_count(enhanced_prompt)
        
        if final_token_count > self.max_tokens - self.reserved_tokens:
            logger.warning(f"Context window exceeded: {final_token_count} tokens (max: {self.max_tokens - self.reserved_tokens})")
            raise ContextWindowExceededError(
                f"Enhanced prompt exceeds token limit: {final_token_count} tokens "
                f"(max: {self.max_tokens - self.reserved_tokens})"
            )
        
        logger.info(f"Successfully injected context. Final token count: {final_token_count}")
        return enhanced_prompt
    
    def _prepare_context_elements(
        self,
        prompt: str,
        conversation_history: list[dict[str, str]],
        memory_retrieval_results: list[MemoryRetrievalResult],
        system_instructions: Optional[str],
        additional_context: dict[str, Any]
    ) -> list[ContextElement]:
        """
        Prepare context elements from various sources.
        
        Args:
            prompt: The user's current prompt/query
            conversation_history: Previous conversation turns
            memory_retrieval_results: Results from memory retrieval systems
            system_instructions: System-level instructions for the LLM
            additional_context: Any additional context to consider
            
        Returns:
            List of ContextElement objects representing all potential context
        """
        context_elements = []
        
        # Add system instructions as highest priority if present
        if system_instructions:
            context_elements.append(ContextElement(
                content=system_instructions,
                source="system_instructions",
                priority=ContextPriority.CRITICAL,
                token_count=self.token_counter(system_instructions)
            ))
        
        # Add conversation history
        for i, turn in enumerate(conversation_history):
            # More recent turns get higher priority
            priority = ContextPriority.HIGH if i >= len(conversation_history) - 3 else \
                      ContextPriority.MEDIUM if i >= len(conversation_history) - 6 else \
                      ContextPriority.LOW
            
            # Format the conversation turn
            if 'user' in turn and 'assistant' in turn:
                content = f"User: {turn['user']}\nAssistant: {turn['assistant']}"
            elif 'user' in turn:
                content = f"User: {turn['user']}"
            elif 'assistant' in turn:
                content = f"Assistant: {turn['assistant']}"
            else:
                content = str(turn)
            
            context_elements.append(ContextElement(
                content=content,
                source="conversation_history",
                priority=priority,
                token_count=self.token_counter(content),
                metadata={"turn_index": i}
            ))
        
        # Add memory retrieval results
        for result in memory_retrieval_results:
            # Determine priority based on relevance score
            if hasattr(result, 'relevance_score') and result.relevance_score is not None:
                if result.relevance_score > 0.8:
                    priority = ContextPriority.HIGH
                elif result.relevance_score > 0.6:
                    priority = ContextPriority.MEDIUM
                else:
                    priority = ContextPriority.LOW
            else:
                priority = ContextPriority.MEDIUM
            
            # Format the memory content
            if hasattr(result, 'content') and result.content:
                content = result.content
            else:
                content = str(result)
            
            # Add metadata about memory type if available
            metadata = {}
            if hasattr(result, 'memory_type'):
                metadata['memory_type'] = result.memory_type
            if hasattr(result, 'timestamp'):
                metadata['timestamp'] = result.timestamp
            if hasattr(result, 'relevance_score'):
                metadata['relevance_score'] = result.relevance_score
            
            context_elements.append(ContextElement(
                content=content,
                source="memory_retrieval",
                priority=priority,
                token_count=self.token_counter(content),
                metadata=metadata
            ))
        
        # Add additional context
        for key, value in additional_context.items():
            content = f"{key}: {value}" if isinstance(value, (str, int, float, bool)) else json.dumps(value)
            context_elements.append(ContextElement(
                content=content,
                source="additional_context",
                priority=ContextPriority.MEDIUM,
                token_count=self.token_counter(content),
                metadata={"context_key": key}
            ))
        
        logger.debug(f"Prepared {len(context_elements)} context elements")
        return context_elements
    
    def _select_context_elements(
        self,
        context_elements: list[ContextElement],
        prompt_tokens: int
    ) -> list[ContextElement]:
        """
        Select which context elements to include based on priority and token limits.
        
        Args:
            context_elements: List of all potential context elements
            prompt_tokens: Number of tokens in the original prompt
            
        Returns:
            List of selected context elements that fit within token limits
        """
        # Sort elements by priority (CRITICAL first, BACKGROUND last)
        sorted_elements = sorted(context_elements, key=lambda x: x.priority.value)
        
        # Calculate available tokens
        available_tokens = self.max_tokens - self.reserved_tokens - prompt_tokens
        
        # Select elements until we run out of space
        selected_elements = []
        current_tokens = 0
        
        for element in sorted_elements:
            # Always include CRITICAL elements
            if element.priority == ContextPriority.CRITICAL:
                selected_elements.append(element)
                current_tokens += element.token_count
                continue
                
            # For other priorities, check if we have space
            if current_tokens + element.token_count <= available_tokens:
                selected_elements.append(element)
                current_tokens += element.token_count
            else:
                # If we're out of space, skip this element
                logger.debug(f"Skipping context element due to token limits: {element.source} "
                           f"(priority: {element.priority.name}, tokens: {element.token_count})")
        
        logger.info(f"Selected {len(selected_elements)}/{len(context_elements)} context elements "
                   f"using {current_tokens}/{available_tokens} available tokens")
        
        return selected_elements
    
    def _format_context(
        self,
        prompt: str,
        selected_elements: list[ContextElement],
        conversation_history: list[dict[str, str]],
        system_instructions: Optional[str]
    ) -> Union[str, dict[str, Any]]:
        """
        Format the selected context elements according to the chosen strategy and format.
        
        Args:
            prompt: The user's current prompt/query
            selected_elements: The selected context elements to include
            conversation_history: Previous conversation turns
            system_instructions: System-level instructions for the LLM
            
        Returns:
            Formatted prompt with injected context, either as a string or structured object
        """
        # Group elements by source for easier handling
        elements_by_source = {}
        for element in selected_elements:
            if element.source not in elements_by_source:
                elements_by_source[element.source] = []
            elements_by_source[element.source].append(element)
        
        # Format based on the selected strategy
        if self.strategy == ContextInjectionStrategy.PREPEND:
            return self._format_prepend_strategy(prompt, selected_elements, system_instructions)
        elif self.strategy == ContextInjectionStrategy.APPEND:
            return self._format_append_strategy(prompt, selected_elements)
        elif self.strategy == ContextInjectionStrategy.INTERLEAVE:
            return self._format_interleave_strategy(prompt, selected_elements, conversation_history)
        elif self.strategy == ContextInjectionStrategy.STRUCTURED:
            return self._format_structured_strategy(prompt, elements_by_source, system_instructions)
        else:
            # Default to prepend if strategy is not recognized
            logger.warning(f"Unrecognized strategy {self.strategy}, defaulting to PREPEND")
            return self._format_prepend_strategy(prompt, selected_elements, system_instructions)
    
    def _format_prepend_strategy(
        self,
        prompt: str,
        selected_elements: list[ContextElement],
        system_instructions: Optional[str]
    ) -> str:
        """
        Format context by prepending it to the prompt.
        
        Args:
            prompt: The user's current prompt/query
            selected_elements: The selected context elements to include
            system_instructions: System-level instructions for the LLM
            
        Returns:
            Formatted prompt with context prepended
        """
        # Start with system instructions if present and not already in selected elements
        formatted_context = ""
        system_in_elements = any(e.source == "system_instructions" for e in selected_elements)
        
        if system_instructions and not system_in_elements:
            formatted_context += f"System: {system_instructions}\n\n"
        
        # Add other context elements
        for element in selected_elements:
            # Skip system instructions if we already added them
            if element.source == "system_instructions" and formatted_context.startswith("System:"):
                continue
                
            # Format based on source
            if element.source == "system_instructions":
                formatted_context += f"System: {element.content}\n\n"
            elif element.source == "conversation_history":
                formatted_context += f"{element.content}\n\n"
            elif element.source == "memory_retrieval":
                memory_type = element.metadata.get("memory_type", "Memory")
                formatted_context += f"Relevant {memory_type}: {element.content}\n\n"
            elif element.source == "additional_context":
                context_key = element.metadata.get("context_key", "Context")
                formatted_context += f"{context_key}: {element.content}\n\n"
            else:
                formatted_context += f"{element.content}\n\n"
        
        # Add the user's prompt
        formatted_context += f"User: {prompt}\n\nAssistant:"
        
        return formatted_context
    
    def _format_append_strategy(
        self,
        prompt: str,
        selected_elements: list[ContextElement]
    ) -> str:
        """
        Format context by appending it after the prompt.
        
        Args:
            prompt: The user's current prompt/query
            selected_elements: The selected context elements to include
            
        Returns:
            Formatted prompt with context appended
        """
        # Start with the user's prompt
        formatted_context = f"User: {prompt}\n\n"
        
        # Add context elements
        if selected_elements:
            formatted_context += "Additional context:\n"
            
            for element in selected_elements:
                if element.source == "system_instructions":
                    formatted_context += f"System instructions: {element.content}\n\n"
                elif element.source == "conversation_history":
                    formatted_context += f"Previous conversation: {element.content}\n\n"
                elif element.source == "memory_retrieval":
                    memory_type = element.metadata.get("memory_type", "Memory")
                    formatted_context += f"Relevant {memory_type}: {element.content}\n\n"
                elif element.source == "additional_context":
                    context_key = element.metadata.get("context_key", "Context")
                    formatted_context += f"{context_key}: {element.content}\n\n"
                else:
                    formatted_context += f"{element.content}\n\n"
        
        formatted_context += "Assistant:"
        
        return formatted_context
    
    def _format_interleave_strategy(
        self,
        prompt: str,
        selected_elements: list[ContextElement],
        conversation_history: list[dict[str, str]]
    ) -> str:
        """
        Format context by interleaving it with conversation history.
        
        Args:
            prompt: The user's current prompt/query
            selected_elements: The selected context elements to include
            conversation_history: Previous conversation turns
            
        Returns:
            Formatted prompt with interleaved context
        """
        # Filter out conversation history elements from selected_elements
        non_conversation_elements = [e for e in selected_elements 
                                    if e.source != "conversation_history"]
        
        # Get conversation history elements
        [e for e in selected_elements 
                               if e.source == "conversation_history"]
        
        # Build conversation with interleaved context
        formatted_context = ""
        
        # Add system instructions first if present
        system_elements = [e for e in selected_elements if e.source == "system_instructions"]
        if system_elements:
            for element in system_elements:
                formatted_context += f"System: {element.content}\n\n"
        
        # Add conversation history with interleaved context
        for i, turn in enumerate(conversation_history):
            # Add the conversation turn
            if 'user' in turn:
                formatted_context += f"User: {turn['user']}\n\n"
            if 'assistant' in turn:
                formatted_context += f"Assistant: {turn['assistant']}\n\n"
            
            # After certain turns, add relevant context
            if i % 2 == 1 and non_conversation_elements:  # Add after assistant responses
                # Take the next context element
                element = non_conversation_elements.pop(0)
                
                if element.source == "memory_retrieval":
                    memory_type = element.metadata.get("memory_type", "Memory")
                    formatted_context += f"[Relevant {memory_type}: {element.content}]\n\n"
                elif element.source == "additional_context":
                    context_key = element.metadata.get("context_key", "Context")
                    formatted_context += f"[{context_key}: {element.content}]\n\n"
                else:
                    formatted_context += f"[Context: {element.content}]\n\n"
                
                # If we've used all non-conversation elements, break out
                if not non_conversation_elements:
                    break
        
        # Add any remaining context elements
        for element in non_conversation_elements:
            if element.source == "memory_retrieval":
                memory_type = element.metadata.get("memory_type", "Memory")
                formatted_context += f"[Relevant {memory_type}: {element.content}]\n\n"
            elif element.source == "additional_context":
                context_key = element.metadata.get("context_key", "Context")
                formatted_context += f"[{context_key}: {element.content}]\n\n"
            else:
                formatted_context += f"[Context: {element.content}]\n\n"
        
        # Add the current prompt
        formatted_context += f"User: {prompt}\n\nAssistant:"
        
        return formatted_context
    
    def _format_structured_strategy(
        self,
        prompt: str,
        elements_by_source: dict[str, list[ContextElement]],
        system_instructions: Optional[str]
    ) -> dict[str, Any]:
        """
        Format context as a structured object (e.g., for ChatML or similar formats).
        
        Args:
            prompt: The user's current prompt/query
            elements_by_source: Context elements grouped by source
            system_instructions: System-level instructions for the LLM
            
        Returns:
            Structured object representing the prompt with context
        """
        messages = []
        
        # Add system message if present
        if system_instructions or "system_instructions" in elements_by_source:
            system_content = system_instructions or ""
            if "system_instructions" in elements_by_source:
                for element in elements_by_source["system_instructions"]:
                    system_content += element.content + "\n\n"
            
            messages.append({
                "role": "system",
                "content": system_content.strip()
            })
        
        # Add memory retrieval as system messages
        if "memory_retrieval" in elements_by_source:
            memory_content = "Relevant information from memory:\n\n"
            for element in elements_by_source["memory_retrieval"]:
                memory_type = element.metadata.get("memory_type", "Memory")
                memory_content += f"- {memory_type}: {element.content}\n\n"
            
            messages.append({
                "role": "system",
                "content": memory_content.strip()
            })
        
        # Add additional context as system messages
        if "additional_context" in elements_by_source:
            context_content = "Additional context:\n\n"
            for element in elements_by_source["additional_context"]:
                context_key = element.metadata.get("context_key", "Context")
                context_content += f"- {context_key}: {element.content}\n\n"
            
            messages.append({
                "role": "system",
                "content": context_content.strip()
            })
        
        # Add conversation history
        if "conversation_history" in elements_by_source:
            # Sort by turn index if available
            conversation_elements = sorted(
                elements_by_source["conversation_history"],
                key=lambda x: x.metadata.get("turn_index", 0) if x.metadata else 0
            )
            
            for element in conversation_elements:
                content = element.content
                
                # Parse the content to extract user and assistant messages
                if content.startswith("User: ") and "Assistant: " in content:
                    user_content, assistant_content = content.split("Assistant: ", 1)
                    user_content = user_content.replace("User: ", "", 1).strip()
                    
                    messages.append({
                        "role": "user",
                        "content": user_content
                    })
                    
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content.strip()
                    })
                elif content.startswith("User: "):
                    user_content = content.replace("User: ", "", 1).strip()
                    messages.append({
                        "role": "user",
                        "content": user_content
                    })
                elif content.startswith("Assistant: "):
                    assistant_content = content.replace("Assistant: ", "", 1).strip()
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
        
        # Add the current prompt
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return {"messages": messages}
    
    def _estimate_structured_token_count(self, structured_prompt: dict[str, Any]) -> int:
        """
        Estimate the token count for a structured prompt.
        
        Args:
            structured_prompt: The structured prompt object
            
        Returns:
            Estimated token count
        """
        # This is a simplified estimation - in production, you would use
        # the actual tokenizer for the model you're using
        total_tokens = 0
        
        if "messages" in structured_prompt:
            for message in structured_prompt["messages"]:
                # Add tokens for the message content
                if "content" in message and message["content"]:
                    total_tokens += self.token_counter(message["content"])
                
                # Add tokens for message structure (role, etc.)
                # This is a rough estimate - actual tokenization depends on the model
                total_tokens += 4  # Approximate overhead per message
        
        return total_tokens


class ContextInjector:
    """
    Utility class for injecting context into prompts with a simpler interface.
    
    This class provides a simplified interface to the ContextInjectionManager
    for common use cases.
    """
    
    def __init__(self, config: ContextInjectionConfig = None):
        """
        Initialize the context injector.
        
        Args:
            config: Configuration for context injection (optional)
        """
        if config is None:
            # Use default configuration
            from neuroca.config.defaults import get_default_context_injection_config
            config = get_default_context_injection_config()
        
        self.manager = ContextInjectionManager(config)
    
    def inject(
        self,
        prompt: str,
        conversation_history: list[dict[str, str]] = None,
        memory_results: list[MemoryRetrievalResult] = None,
        system_instructions: str = None,
        additional_context: dict[str, Any] = None
    ) -> Union[str, dict[str, Any]]:
        """
        Inject context into a prompt.
        
        Args:
            prompt: The user's prompt
            conversation_history: Previous conversation turns
            memory_results: Results from memory retrieval
            system_instructions: System instructions for the LLM
            additional_context: Additional context to include
            
        Returns:
            Enhanced prompt with injected context
        """
        return self.manager.inject_context(
            prompt=prompt,
            conversation_history=conversation_history,
            memory_retrieval_results=memory_results,
            system_instructions=system_instructions,
            additional_context=additional_context
        )


def inject_context(
    prompt: str,
    conversation_history: list[dict[str, str]] = None,
    memory_results: list[MemoryRetrievalResult] = None,
    system_instructions: str = None,
    additional_context: dict[str, Any] = None,
    config: ContextInjectionConfig = None
) -> Union[str, dict[str, Any]]:
    """
    Convenience function for injecting context into a prompt.
    
    Args:
        prompt: The user's prompt
        conversation_history: Previous conversation turns
        memory_results: Results from memory retrieval
        system_instructions: System instructions for the LLM
        additional_context: Additional context to include
        config: Configuration for context injection
        
    Returns:
        Enhanced prompt with injected context
    """
    injector = ContextInjector(config)
    return injector.inject(
        prompt=prompt,
        conversation_history=conversation_history,
        memory_results=memory_results,
        system_instructions=system_instructions,
        additional_context=additional_context
    )