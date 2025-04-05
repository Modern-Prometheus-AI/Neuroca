"""
Context Management Module for NeuroCognitive Architecture (NCA)

This module provides comprehensive context management functionality for LLM integration,
enabling the system to maintain, manipulate, and track conversation context across
interactions. It serves as a bridge between the NCA's memory systems and external
LLM providers, ensuring context is appropriately managed for optimal LLM performance.

The module implements:
- Context objects for different types of interactions
- Context window management and optimization
- Context persistence and retrieval
- Context manipulation utilities
- Integration with memory tiers (working, episodic, semantic)

Usage:
    from neuroca.integration.context import Context, ContextManager
    
    # Create a new context for a conversation
    context = Context(user_id="user123", session_id="session456")
    
    # Add messages to context
    context.add_message("user", "Hello, how can you help me today?")
    context.add_message("assistant", "I can help answer questions and assist with tasks.")
    
    # Get formatted context for LLM consumption
    formatted_context = context.format_for_llm(provider="openai")
    
    # Manage context with the ContextManager
    context_manager = ContextManager()
    context_manager.register_context(context)
    context_manager.save_context(context.context_id)
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from neuroca.core.exceptions import ContextError, ContextLimitExceededError
from neuroca.memory.working_memory import WorkingMemory  # Corrected import path

# Configure module logger
logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Enumeration of possible message roles in a conversation context."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class Message:
    """Represents a single message in a conversation context."""
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate message after initialization."""
        if not isinstance(self.role, MessageRole):
            try:
                self.role = MessageRole(self.role)
            except ValueError:
                raise ValueError(f"Invalid role: {self.role}. Must be one of {[r.value for r in MessageRole]}")
        
        if not isinstance(self.content, str):
            raise TypeError(f"Message content must be a string, got {type(self.content)}")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Message':
        """Create a Message instance from a dictionary."""
        try:
            return cls(
                role=data["role"],
                content=data["content"],
                timestamp=data.get("timestamp", time.time()),
                metadata=data.get("metadata", {})
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in message data: {e}")


class Context:
    """
    Manages conversation context for LLM interactions.
    
    This class handles the storage, retrieval, and manipulation of conversation
    context, including message history, metadata, and context window management.
    """
    
    def __init__(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        context_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        metadata: Optional[dict[str, Any]] = None
    ):
        """
        Initialize a new Context instance.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the session (generated if not provided)
            context_id: Unique identifier for this context (generated if not provided)
            system_prompt: Optional system prompt to initialize the context
            max_tokens: Maximum number of tokens allowed in this context
            metadata: Additional metadata for this context
            
        Raises:
            ValueError: If invalid parameters are provided
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.context_id = context_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.max_tokens = max_tokens
        self.metadata = metadata or {}
        self.messages: list[Message] = []
        
        # Add system prompt if provided
        if system_prompt:
            self.add_message(MessageRole.SYSTEM, system_prompt)
        
        logger.debug(f"Created new context: {self.context_id} for user: {user_id}")
    
    def add_message(self, role: Union[str, MessageRole], content: str, metadata: Optional[dict[str, Any]] = None) -> Message:
        """
        Add a new message to the context.
        
        Args:
            role: Role of the message sender (system, user, assistant, etc.)
            content: Content of the message
            metadata: Additional metadata for this message
            
        Returns:
            The created Message object
            
        Raises:
            ContextLimitExceededError: If adding the message would exceed the context limit
            ValueError: If invalid role or content is provided
        """
        if not content:
            raise ValueError("Message content cannot be empty")
        
        # Create the message
        message = Message(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        # Check if adding this message would exceed the context limit
        # This is a simplified check - in production you'd use a proper tokenizer
        estimated_tokens = sum(len(msg.content.split()) for msg in self.messages) + len(content.split())
        if estimated_tokens > self.max_tokens:
            logger.warning(f"Context limit exceeded for context {self.context_id}")
            raise ContextLimitExceededError(
                f"Adding this message would exceed the context limit of {self.max_tokens} tokens"
            )
        
        # Add the message
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        logger.debug(f"Added {message.role.value} message to context {self.context_id}")
        return message
    
    def get_messages(self, limit: Optional[int] = None, roles: Optional[list[MessageRole]] = None) -> list[Message]:
        """
        Get messages from the context, optionally filtered by role and limited in number.
        
        Args:
            limit: Maximum number of messages to return (most recent first)
            roles: Only include messages with these roles
            
        Returns:
            List of Message objects
        """
        filtered_messages = self.messages
        
        # Filter by roles if specified
        if roles:
            role_set = set(roles)
            filtered_messages = [msg for msg in filtered_messages if msg.role in role_set]
        
        # Apply limit if specified
        if limit and limit > 0:
            filtered_messages = filtered_messages[-limit:]
            
        return filtered_messages
    
    def clear_messages(self, preserve_system: bool = True) -> None:
        """
        Clear all messages from the context.
        
        Args:
            preserve_system: Whether to preserve system messages
        """
        if preserve_system:
            system_messages = [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
            self.messages = system_messages
        else:
            self.messages = []
        
        self.updated_at = datetime.now()
        logger.debug(f"Cleared messages from context {self.context_id} (preserve_system={preserve_system})")
    
    def format_for_llm(self, provider: str = "openai") -> list[dict[str, str]]:
        """
        Format the context for consumption by a specific LLM provider.
        
        Args:
            provider: The LLM provider to format for (e.g., "openai", "anthropic")
            
        Returns:
            Formatted context suitable for the specified provider
            
        Raises:
            ValueError: If an unsupported provider is specified
        """
        if provider.lower() == "openai":
            return [{"role": msg.role.value, "content": msg.content} for msg in self.messages]
        elif provider.lower() == "anthropic":
            # Simplified example - actual implementation would be more complex
            formatted = []
            for msg in self.messages:
                if msg.role == MessageRole.SYSTEM:
                    formatted.append({"role": "system", "content": msg.content})
                elif msg.role == MessageRole.USER:
                    formatted.append({"role": "human", "content": msg.content})
                elif msg.role == MessageRole.ASSISTANT:
                    formatted.append({"role": "assistant", "content": msg.content})
            return formatted
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the context to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the context
        """
        return {
            "context_id": self.context_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
            "messages": [msg.to_dict() for msg in self.messages]
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Context':
        """
        Create a Context instance from a dictionary.
        
        Args:
            data: Dictionary containing context data
            
        Returns:
            Context instance
            
        Raises:
            ValueError: If the dictionary is missing required fields
        """
        try:
            context = cls(
                user_id=data["user_id"],
                session_id=data["session_id"],
                context_id=data["context_id"],
                max_tokens=data.get("max_tokens", 4000),
                metadata=data.get("metadata", {})
            )
            
            # Parse timestamps
            context.created_at = datetime.fromisoformat(data["created_at"])
            context.updated_at = datetime.fromisoformat(data["updated_at"])
            
            # Add messages
            context.messages = [Message.from_dict(msg_data) for msg_data in data.get("messages", [])]
            
            return context
        except KeyError as e:
            raise ValueError(f"Missing required field in context data: {e}")
        except Exception as e:
            logger.error(f"Error creating context from dictionary: {e}")
            raise


class ContextManager:
    """
    Manages multiple contexts, providing persistence and retrieval capabilities.
    
    This class serves as a central registry for contexts, allowing them to be
    saved, loaded, and managed throughout the application lifecycle.
    """
    
    def __init__(self, working_memory: Optional[WorkingMemory] = None):
        """
        Initialize a new ContextManager.
        
        Args:
            working_memory: Optional working memory instance for context persistence
        """
        self.contexts: dict[str, Context] = {}
        self.working_memory = working_memory
        logger.debug("Initialized ContextManager")
    
    def register_context(self, context: Context) -> None:
        """
        Register a context with the manager.
        
        Args:
            context: The context to register
            
        Raises:
            ContextError: If a context with the same ID is already registered
        """
        if context.context_id in self.contexts:
            raise ContextError(f"Context with ID {context.context_id} is already registered")
        
        self.contexts[context.context_id] = context
        logger.debug(f"Registered context {context.context_id}")
    
    def get_context(self, context_id: str) -> Context:
        """
        Get a context by its ID.
        
        Args:
            context_id: ID of the context to retrieve
            
        Returns:
            The requested Context
            
        Raises:
            ContextError: If no context with the given ID is found
        """
        if context_id not in self.contexts:
            # Try to load from working memory if available
            if self.working_memory:
                try:
                    return self.load_context(context_id)
                except Exception as e:
                    logger.error(f"Failed to load context {context_id} from working memory: {e}")
            
            raise ContextError(f"No context found with ID {context_id}")
        
        return self.contexts[context_id]
    
    def save_context(self, context_id: str) -> bool:
        """
        Save a context to persistent storage.
        
        Args:
            context_id: ID of the context to save
            
        Returns:
            True if the context was saved successfully, False otherwise
            
        Raises:
            ContextError: If no context with the given ID is found
        """
        if context_id not in self.contexts:
            raise ContextError(f"No context found with ID {context_id}")
        
        context = self.contexts[context_id]
        
        if self.working_memory:
            try:
                context_data = context.to_dict()
                self.working_memory.store(
                    key=f"context:{context_id}",
                    value=json.dumps(context_data),
                    metadata={
                        "user_id": context.user_id,
                        "session_id": context.session_id,
                        "type": "context"
                    }
                )
                logger.info(f"Saved context {context_id} to working memory")
                return True
            except Exception as e:
                logger.error(f"Failed to save context {context_id}: {e}")
                return False
        else:
            logger.warning("No working memory available for context persistence")
            return False
    
    def load_context(self, context_id: str) -> Context:
        """
        Load a context from persistent storage.
        
        Args:
            context_id: ID of the context to load
            
        Returns:
            The loaded Context
            
        Raises:
            ContextError: If the context cannot be loaded
        """
        if not self.working_memory:
            raise ContextError("No working memory available for context loading")
        
        try:
            context_json = self.working_memory.retrieve(f"context:{context_id}")
            if not context_json:
                raise ContextError(f"Context {context_id} not found in working memory")
            
            context_data = json.loads(context_json)
            context = Context.from_dict(context_data)
            
            # Register the loaded context
            self.contexts[context_id] = context
            
            logger.info(f"Loaded context {context_id} from working memory")
            return context
        except Exception as e:
            logger.error(f"Failed to load context {context_id}: {e}")
            raise ContextError(f"Failed to load context {context_id}: {str(e)}")
    
    def delete_context(self, context_id: str) -> bool:
        """
        Delete a context from memory and persistent storage.
        
        Args:
            context_id: ID of the context to delete
            
        Returns:
            True if the context was deleted successfully, False otherwise
        """
        # Remove from in-memory storage
        if context_id in self.contexts:
            del self.contexts[context_id]
        
        # Remove from persistent storage if available
        if self.working_memory:
            try:
                self.working_memory.delete(f"context:{context_id}")
                logger.info(f"Deleted context {context_id} from working memory")
                return True
            except Exception as e:
                logger.error(f"Failed to delete context {context_id} from working memory: {e}")
                return False
        
        return True
    
    def get_contexts_for_user(self, user_id: str) -> list[Context]:
        """
        Get all contexts for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of Context objects for the user
        """
        return [ctx for ctx in self.contexts.values() if ctx.user_id == user_id]
    
    def get_contexts_for_session(self, session_id: str) -> list[Context]:
        """
        Get all contexts for a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of Context objects for the session
        """
        return [ctx for ctx in self.contexts.values() if ctx.session_id == session_id]


# Export public classes and functions
__all__ = [
    'Context',
    'ContextManager',
    'Message',
    'MessageRole',
    'ContextError',
    'ContextLimitExceededError'
]
