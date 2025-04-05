"""
Context Manager for NeuroCognitive Architecture (NCA) LLM Integration

This module provides a robust context management system for LLM interactions within the
NeuroCognitive Architecture. It handles the lifecycle of context objects, manages context
windows, implements context compression strategies, and ensures proper resource cleanup.

The ContextManager serves as a central component in the integration layer, facilitating
the exchange of information between the NCA core components and external LLM services.

Usage:
    context_manager = ContextManager()
    
    # Create a new context
    context_id = context_manager.create_context(user_id="user123", session_id="session456")
    
    # Add content to context
    context_manager.add_to_context(context_id, "User query about neural networks")
    
    # Get context for LLM processing
    context_data = context_manager.get_context(context_id)
    
    # Update context after LLM response
    context_manager.update_context(context_id, "LLM response about neural networks")
    
    # Release context when done
    context_manager.release_context(context_id)
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

# Configure logger
logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Enumeration of different context types supported by the system."""
    CONVERSATION = "conversation"
    TASK = "task"
    RESEARCH = "research"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CUSTOM = "custom"


class ContextPriority(Enum):
    """Priority levels for context management and retention decisions."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class ContextCompressionStrategy(Enum):
    """Available strategies for compressing context when approaching size limits."""
    NONE = "none"  # No compression
    SUMMARIZE = "summarize"  # Summarize older context entries
    PRUNE_OLDEST = "prune_oldest"  # Remove oldest entries
    PRUNE_LEAST_RELEVANT = "prune_least_relevant"  # Remove least relevant entries
    SEMANTIC_CLUSTERING = "semantic_clustering"  # Group similar content


@dataclass
class ContextEntry:
    """Represents a single entry in the context history."""
    content: str
    timestamp: float = field(default_factory=time.time)
    source: str = "user"  # Can be 'user', 'system', 'llm', etc.
    metadata: dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 1.0  # Used for pruning decisions
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the context entry to a dictionary representation."""
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "source": self.source,
            "metadata": self.metadata,
            "relevance_score": self.relevance_score
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ContextEntry':
        """Create a ContextEntry from a dictionary representation."""
        return cls(
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            source=data.get("source", "user"),
            metadata=data.get("metadata", {}),
            relevance_score=data.get("relevance_score", 1.0)
        )


@dataclass
class Context:
    """Represents a complete context object with history and metadata."""
    id: str
    type: ContextType
    user_id: str
    session_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    entries: list[ContextEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: ContextPriority = ContextPriority.MEDIUM
    max_size: int = 100  # Maximum number of entries
    compression_strategy: ContextCompressionStrategy = ContextCompressionStrategy.SUMMARIZE
    is_active: bool = True
    
    def add_entry(self, entry: Union[ContextEntry, str], source: str = "user", 
                  metadata: Optional[dict[str, Any]] = None) -> None:
        """
        Add a new entry to the context.
        
        Args:
            entry: The content to add, either as a string or ContextEntry object
            source: The source of the entry (if entry is a string)
            metadata: Additional metadata for the entry (if entry is a string)
        """
        if isinstance(entry, str):
            entry = ContextEntry(
                content=entry,
                source=source,
                metadata=metadata or {}
            )
        
        self.entries.append(entry)
        self.updated_at = time.time()
    
    def get_formatted_context(self, max_entries: Optional[int] = None) -> str:
        """
        Get a formatted string representation of the context for LLM consumption.
        
        Args:
            max_entries: Optional limit on the number of most recent entries to include
            
        Returns:
            A formatted string containing the context history
        """
        entries_to_use = self.entries
        if max_entries is not None:
            entries_to_use = self.entries[-max_entries:]
        
        formatted = []
        for entry in entries_to_use:
            prefix = f"[{entry.source}]: "
            formatted.append(f"{prefix}{entry.content}")
        
        return "\n".join(formatted)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the context to a dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "entries": [entry.to_dict() for entry in self.entries],
            "metadata": self.metadata,
            "priority": self.priority.value,
            "max_size": self.max_size,
            "compression_strategy": self.compression_strategy.value,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Context':
        """Create a Context object from a dictionary representation."""
        return cls(
            id=data["id"],
            type=ContextType(data["type"]),
            user_id=data["user_id"],
            session_id=data["session_id"],
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            entries=[ContextEntry.from_dict(entry) for entry in data.get("entries", [])],
            metadata=data.get("metadata", {}),
            priority=ContextPriority(data.get("priority", ContextPriority.MEDIUM.value)),
            max_size=data.get("max_size", 100),
            compression_strategy=ContextCompressionStrategy(
                data.get("compression_strategy", ContextCompressionStrategy.SUMMARIZE.value)
            ),
            is_active=data.get("is_active", True)
        )


class ContextManager:
    """
    Manages context objects for LLM interactions within the NCA system.
    
    This class is responsible for creating, retrieving, updating, and releasing
    context objects. It also handles context compression, persistence, and cleanup.
    """
    
    def __init__(self, 
                 default_max_size: int = 100,
                 default_compression_strategy: ContextCompressionStrategy = ContextCompressionStrategy.SUMMARIZE,
                 auto_cleanup_interval: int = 3600):  # 1 hour in seconds
        """
        Initialize the ContextManager.
        
        Args:
            default_max_size: Default maximum size for new contexts
            default_compression_strategy: Default compression strategy for new contexts
            auto_cleanup_interval: Interval in seconds for automatic cleanup of inactive contexts
        """
        self._contexts: dict[str, Context] = {}
        self._default_max_size = default_max_size
        self._default_compression_strategy = default_compression_strategy
        self._auto_cleanup_interval = auto_cleanup_interval
        self._last_cleanup_time = time.time()
        
        logger.info("ContextManager initialized with default_max_size=%d, "
                   "compression_strategy=%s, auto_cleanup_interval=%d",
                   default_max_size, default_compression_strategy.value, auto_cleanup_interval)
    
    def create_context(self, 
                       user_id: str, 
                       session_id: str,
                       context_type: ContextType = ContextType.CONVERSATION,
                       priority: ContextPriority = ContextPriority.MEDIUM,
                       max_size: Optional[int] = None,
                       compression_strategy: Optional[ContextCompressionStrategy] = None,
                       metadata: Optional[dict[str, Any]] = None) -> str:
        """
        Create a new context and return its ID.
        
        Args:
            user_id: ID of the user associated with this context
            session_id: ID of the session associated with this context
            context_type: Type of context to create
            priority: Priority level for this context
            max_size: Maximum number of entries for this context
            compression_strategy: Strategy to use when context exceeds max_size
            metadata: Additional metadata for the context
            
        Returns:
            The ID of the newly created context
            
        Raises:
            ValueError: If required parameters are invalid
        """
        if not user_id:
            raise ValueError("user_id is required")
        if not session_id:
            raise ValueError("session_id is required")
        
        context_id = str(uuid.uuid4())
        
        # Use default values if not specified
        max_size = max_size if max_size is not None else self._default_max_size
        compression_strategy = compression_strategy or self._default_compression_strategy
        metadata = metadata or {}
        
        # Create the context
        context = Context(
            id=context_id,
            type=context_type,
            user_id=user_id,
            session_id=session_id,
            priority=priority,
            max_size=max_size,
            compression_strategy=compression_strategy,
            metadata=metadata
        )
        
        # Store the context
        self._contexts[context_id] = context
        
        logger.debug("Created new context with ID %s for user %s, session %s",
                    context_id, user_id, session_id)
        
        # Check if we need to run cleanup
        self._check_auto_cleanup()
        
        return context_id
    
    def get_context(self, context_id: str) -> Context:
        """
        Retrieve a context by its ID.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            The Context object
            
        Raises:
            KeyError: If the context_id does not exist
            ValueError: If the context is no longer active
        """
        if context_id not in self._contexts:
            raise KeyError(f"Context with ID {context_id} not found")
        
        context = self._contexts[context_id]
        
        if not context.is_active:
            raise ValueError(f"Context with ID {context_id} is no longer active")
        
        logger.debug("Retrieved context %s with %d entries", 
                    context_id, len(context.entries))
        
        return context
    
    def add_to_context(self, 
                       context_id: str, 
                       content: str,
                       source: str = "user",
                       metadata: Optional[dict[str, Any]] = None) -> None:
        """
        Add content to an existing context.
        
        Args:
            context_id: The ID of the context to add to
            content: The content to add
            source: The source of the content
            metadata: Additional metadata for this entry
            
        Raises:
            KeyError: If the context_id does not exist
            ValueError: If the context is no longer active
        """
        context = self.get_context(context_id)
        
        # Add the entry
        context.add_entry(content, source, metadata)
        
        # Check if we need to compress the context
        if len(context.entries) > context.max_size:
            self._compress_context(context)
        
        logger.debug("Added entry to context %s, new size: %d entries", 
                    context_id, len(context.entries))
    
    def update_context(self, 
                       context_id: str, 
                       content: str,
                       source: str = "system",
                       metadata: Optional[dict[str, Any]] = None) -> None:
        """
        Update a context with new content (alias for add_to_context with different defaults).
        
        Args:
            context_id: The ID of the context to update
            content: The content to add
            source: The source of the content (default: system)
            metadata: Additional metadata for this entry
            
        Raises:
            KeyError: If the context_id does not exist
            ValueError: If the context is no longer active
        """
        self.add_to_context(context_id, content, source, metadata)
    
    def release_context(self, context_id: str) -> None:
        """
        Mark a context as inactive and release resources.
        
        Args:
            context_id: The ID of the context to release
            
        Raises:
            KeyError: If the context_id does not exist
        """
        if context_id not in self._contexts:
            raise KeyError(f"Context with ID {context_id} not found")
        
        context = self._contexts[context_id]
        context.is_active = False
        
        logger.info("Released context %s", context_id)
    
    def delete_context(self, context_id: str) -> None:
        """
        Permanently delete a context.
        
        Args:
            context_id: The ID of the context to delete
            
        Raises:
            KeyError: If the context_id does not exist
        """
        if context_id not in self._contexts:
            raise KeyError(f"Context with ID {context_id} not found")
        
        del self._contexts[context_id]
        
        logger.info("Deleted context %s", context_id)
    
    def get_contexts_for_user(self, user_id: str) -> list[Context]:
        """
        Get all active contexts for a specific user.
        
        Args:
            user_id: The user ID to filter by
            
        Returns:
            List of active Context objects for the user
        """
        return [
            context for context in self._contexts.values()
            if context.user_id == user_id and context.is_active
        ]
    
    def get_contexts_for_session(self, session_id: str) -> list[Context]:
        """
        Get all active contexts for a specific session.
        
        Args:
            session_id: The session ID to filter by
            
        Returns:
            List of active Context objects for the session
        """
        return [
            context for context in self._contexts.values()
            if context.session_id == session_id and context.is_active
        ]
    
    def export_context(self, context_id: str) -> dict[str, Any]:
        """
        Export a context to a serializable dictionary.
        
        Args:
            context_id: The ID of the context to export
            
        Returns:
            Dictionary representation of the context
            
        Raises:
            KeyError: If the context_id does not exist
        """
        context = self.get_context(context_id)
        return context.to_dict()
    
    def import_context(self, context_data: dict[str, Any]) -> str:
        """
        Import a context from a dictionary representation.
        
        Args:
            context_data: Dictionary representation of a context
            
        Returns:
            The ID of the imported context
            
        Raises:
            ValueError: If the context data is invalid
        """
        try:
            context = Context.from_dict(context_data)
            self._contexts[context.id] = context
            logger.info("Imported context %s with %d entries", 
                       context.id, len(context.entries))
            return context.id
        except (KeyError, ValueError) as e:
            logger.error("Failed to import context: %s", str(e))
            raise ValueError(f"Invalid context data: {str(e)}")
    
    def cleanup_inactive_contexts(self, max_age_seconds: int = 86400) -> int:
        """
        Clean up inactive contexts older than the specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds for inactive contexts
            
        Returns:
            Number of contexts removed
        """
        current_time = time.time()
        contexts_to_remove = []
        
        for context_id, context in self._contexts.items():
            if (not context.is_active and 
                current_time - context.updated_at > max_age_seconds):
                contexts_to_remove.append(context_id)
        
        for context_id in contexts_to_remove:
            del self._contexts[context_id]
        
        logger.info("Cleaned up %d inactive contexts", len(contexts_to_remove))
        self._last_cleanup_time = current_time
        
        return len(contexts_to_remove)
    
    def _compress_context(self, context: Context) -> None:
        """
        Apply the appropriate compression strategy to a context.
        
        Args:
            context: The Context object to compress
        """
        strategy = context.compression_strategy
        
        logger.debug("Compressing context %s using strategy %s", 
                    context.id, strategy.value)
        
        if strategy == ContextCompressionStrategy.NONE:
            # No compression, just log a warning
            logger.warning("Context %s exceeds max size but compression is disabled", 
                          context.id)
            return
        
        elif strategy == ContextCompressionStrategy.PRUNE_OLDEST:
            # Remove oldest entries until we're under the limit
            excess = len(context.entries) - context.max_size
            if excess > 0:
                context.entries = context.entries[excess:]
                logger.debug("Pruned %d oldest entries from context %s", 
                            excess, context.id)
        
        elif strategy == ContextCompressionStrategy.PRUNE_LEAST_RELEVANT:
            # Sort by relevance score and remove least relevant entries
            excess = len(context.entries) - context.max_size
            if excess > 0:
                # Sort entries by relevance score (ascending)
                sorted_entries = sorted(
                    enumerate(context.entries), 
                    key=lambda x: x[1].relevance_score
                )
                
                # Get indices to remove (lowest relevance scores)
                indices_to_remove = {idx for idx, _ in sorted_entries[:excess]}
                
                # Keep only entries that aren't in the removal set
                context.entries = [
                    entry for i, entry in enumerate(context.entries)
                    if i not in indices_to_remove
                ]
                
                logger.debug("Pruned %d least relevant entries from context %s", 
                            excess, context.id)
        
        elif strategy == ContextCompressionStrategy.SUMMARIZE:
            # This would typically call an LLM to summarize older content
            # For now, we'll implement a simple version that combines older entries
            if len(context.entries) > context.max_size:
                # Keep the most recent half of max_size entries intact
                keep_intact = context.max_size // 2
                entries_to_summarize = context.entries[:-keep_intact]
                entries_to_keep = context.entries[-keep_intact:]
                
                # Create a simple summary entry
                summary_text = f"[Summary of {len(entries_to_summarize)} previous messages]"
                summary_entry = ContextEntry(
                    content=summary_text,
                    source="system",
                    metadata={"summarized_count": len(entries_to_summarize)}
                )
                
                # Replace the summarized entries with the summary
                context.entries = [summary_entry] + entries_to_keep
                
                logger.debug("Summarized %d entries in context %s", 
                            len(entries_to_summarize), context.id)
        
        elif strategy == ContextCompressionStrategy.SEMANTIC_CLUSTERING:
            # This would require embedding and clustering capabilities
            # For now, fall back to the summarize strategy
            logger.warning("Semantic clustering compression not fully implemented, "
                          "falling back to summarization for context %s", context.id)
            context.compression_strategy = ContextCompressionStrategy.SUMMARIZE
            self._compress_context(context)
    
    def _check_auto_cleanup(self) -> None:
        """Check if it's time to run automatic cleanup of inactive contexts."""
        current_time = time.time()
        if current_time - self._last_cleanup_time > self._auto_cleanup_interval:
            logger.debug("Running automatic cleanup of inactive contexts")
            self.cleanup_inactive_contexts()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create a context manager
    manager = ContextManager()
    
    # Create a new context
    context_id = manager.create_context(
        user_id="user123",
        session_id="session456",
        context_type=ContextType.CONVERSATION
    )
    
    # Add some entries
    manager.add_to_context(context_id, "Hello, I have a question about neural networks.")
    manager.add_to_context(context_id, "What are the key differences between CNNs and RNNs?")
    
    # Add a system response
    manager.update_context(
        context_id,
        "CNNs (Convolutional Neural Networks) are primarily used for spatial data like images, "
        "while RNNs (Recurrent Neural Networks) are designed for sequential data like text or time series.",
        source="llm"
    )
    
    # Get the context
    context = manager.get_context(context_id)
    
    # Print the formatted context
    print(context.get_formatted_context())
    
    # Release the context when done
    manager.release_context(context_id)