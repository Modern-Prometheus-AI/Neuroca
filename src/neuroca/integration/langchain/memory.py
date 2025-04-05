"""
LangChain Memory Integration Module for NeuroCognitive Architecture (NCA).

This module provides adapters and integration components that connect NCA's
three-tiered memory system with LangChain's memory capabilities. It enables
seamless use of NCA's sophisticated memory management within LangChain workflows.

Key components:
- NCAMemory: Base memory class that implements LangChain's BaseMemory interface
- WorkingMemoryAdapter: Adapter for NCA's working memory
- EpisodicMemoryAdapter: Adapter for NCA's episodic memory
- SemanticMemoryAdapter: Adapter for NCA's semantic memory
- MemoryFactory: Factory for creating appropriate memory instances

Usage:
    from neuroca.integration.langchain.memory import NCAMemory, MemoryFactory
    
    # Create a memory instance with default settings
    memory = MemoryFactory.create_memory(memory_type="working")
    
    # Use in a LangChain chain
    chain = LLMChain(llm=llm, prompt=prompt, memory=memory)
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

# LangChain imports
from langchain.memory.chat_memory import BaseChatMemory
from langchain.memory.utils import get_prompt_input_key
from langchain.schema import AIMessage, HumanMessage

from neuroca.core.exceptions import MemoryCapacityError
from neuroca.core.models import MemoryEntry, MemoryQuery, MemoryType
from neuroca.memory.episodic_memory import EpisodicMemory
from neuroca.memory.semantic_memory import SemanticMemory

# NCA imports
from neuroca.memory.working_memory import WorkingMemory

# Set up logging
logger = logging.getLogger(__name__)


class NCAMemory(BaseChatMemory):
    """
    Base memory class that implements LangChain's BaseMemory interface.
    
    This abstract class serves as the foundation for all NCA memory adapters,
    providing common functionality and ensuring consistent implementation
    of the LangChain memory interface.
    
    Attributes:
        memory_key (str): The key to use for the memory in the chain's context
        input_key (Optional[str]): The key to extract input from chain's inputs
        output_key (Optional[str]): The key to extract output from chain's outputs
        return_messages (bool): Whether to return messages or a string summary
        human_prefix (str): Prefix for human messages in string representation
        ai_prefix (str): Prefix for AI messages in string representation
        memory_id (str): Unique identifier for this memory instance
    """
    
    def __init__(
        self,
        memory_key: str = "memory",
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        return_messages: bool = False,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the NCA memory adapter.
        
        Args:
            memory_key: Key to use for the memory in the chain's context
            input_key: Key to extract input from chain's inputs
            output_key: Key to extract output from chain's outputs
            return_messages: Whether to return messages or a string summary
            human_prefix: Prefix for human messages in string representation
            ai_prefix: Prefix for AI messages in string representation
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            memory_key=memory_key,
            input_key=input_key,
            output_key=output_key,
            return_messages=return_messages,
            human_prefix=human_prefix,
            ai_prefix=ai_prefix,
            **kwargs
        )
        self.memory_id = str(uuid.uuid4())
        logger.debug(f"Initialized NCAMemory with ID: {self.memory_id}")
    
    def _get_input_output(
        self, inputs: dict[str, Any], outputs: dict[str, str]
    ) -> tuple[str, str]:
        """
        Extract the input and output from the chain's inputs and outputs.
        
        Args:
            inputs: The inputs to the chain
            outputs: The outputs from the chain
            
        Returns:
            A tuple of (input_str, output_str)
            
        Raises:
            ValueError: If input_key or output_key is not found
        """
        if self.input_key is None:
            try:
                input_key = get_prompt_input_key(inputs, self.memory_variables)
                self.input_key = input_key
            except ValueError as e:
                logger.error(f"Failed to automatically determine input key: {e}")
                raise ValueError(
                    f"Input key not found in inputs. Received: {inputs.keys()}"
                ) from e
        
        if self.input_key not in inputs:
            raise ValueError(
                f"Input key '{self.input_key}' not found in inputs. Received: {inputs.keys()}"
            )
        
        if self.output_key is None:
            if len(outputs) == 1:
                self.output_key = list(outputs.keys())[0]
            else:
                raise ValueError(
                    f"Output key not specified and multiple outputs found: {outputs.keys()}"
                )
        
        if self.output_key not in outputs:
            raise ValueError(
                f"Output key '{self.output_key}' not found in outputs. Received: {outputs.keys()}"
            )
        
        input_str = str(inputs[self.input_key])
        output_str = str(outputs[self.output_key])
        
        return input_str, output_str


class WorkingMemoryAdapter(NCAMemory):
    """
    Adapter for NCA's working memory to LangChain's memory interface.
    
    This adapter provides access to the short-term, limited capacity
    working memory of the NCA system, suitable for maintaining context
    in ongoing conversations.
    
    Attributes:
        capacity (int): Maximum number of messages to store
        working_memory (WorkingMemory): The underlying working memory instance
    """
    
    def __init__(
        self,
        capacity: int = 10,
        decay_rate: float = 0.1,
        memory_key: str = "working_memory",
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        return_messages: bool = False,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the working memory adapter.
        
        Args:
            capacity: Maximum number of messages to store
            decay_rate: Rate at which memory items decay
            memory_key: Key to use for the memory in the chain's context
            input_key: Key to extract input from chain's inputs
            output_key: Key to extract output from chain's outputs
            return_messages: Whether to return messages or a string summary
            human_prefix: Prefix for human messages in string representation
            ai_prefix: Prefix for AI messages in string representation
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            memory_key=memory_key,
            input_key=input_key,
            output_key=output_key,
            return_messages=return_messages,
            human_prefix=human_prefix,
            ai_prefix=ai_prefix,
            **kwargs
        )
        self.capacity = capacity
        self.decay_rate = decay_rate
        self.working_memory = WorkingMemory(capacity=capacity, decay_rate=decay_rate)
        logger.debug(f"Initialized WorkingMemoryAdapter with capacity: {capacity}")
    
    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """
        Save the context of the conversation to working memory.
        
        Args:
            inputs: The inputs to the chain
            outputs: The outputs from the chain
            
        Raises:
            MemoryCapacityError: If the memory capacity is exceeded
        """
        input_str, output_str = self._get_input_output(inputs, outputs)
        
        try:
            # Create memory entries for both input and output
            human_entry = MemoryEntry(
                content=input_str,
                source="human",
                timestamp=datetime.now(),
                memory_type=MemoryType.WORKING,
                metadata={"session_id": self.memory_id}
            )
            
            ai_entry = MemoryEntry(
                content=output_str,
                source="ai",
                timestamp=datetime.now(),
                memory_type=MemoryType.WORKING,
                metadata={"session_id": self.memory_id}
            )
            
            # Add to working memory
            self.working_memory.add(human_entry)
            self.working_memory.add(ai_entry)
            
            logger.debug(f"Saved context to working memory: {len(self.working_memory)} items")
        except MemoryCapacityError as e:
            logger.warning(f"Working memory capacity exceeded: {e}")
            # Implement forgetting strategy - remove oldest items
            self.working_memory.forget_oldest()
            # Try again
            self.save_context(inputs, outputs)
        except Exception as e:
            logger.error(f"Error saving context to working memory: {e}")
            raise
    
    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Load memory variables from working memory.
        
        Args:
            inputs: The inputs to the chain
            
        Returns:
            Dict containing the memory key and its value
        """
        if not self.working_memory:
            logger.debug("Working memory is empty, returning empty context")
            return {self.memory_key: "" if not self.return_messages else []}
        
        try:
            # Retrieve all entries from working memory
            entries = self.working_memory.retrieve_all()
            
            if self.return_messages:
                messages = []
                for entry in entries:
                    if entry.source == "human":
                        messages.append(HumanMessage(content=entry.content))
                    elif entry.source == "ai":
                        messages.append(AIMessage(content=entry.content))
                return {self.memory_key: messages}
            else:
                # Format as string
                string_buffer = []
                for entry in entries:
                    prefix = self.human_prefix if entry.source == "human" else self.ai_prefix
                    string_buffer.append(f"{prefix}: {entry.content}")
                
                return {self.memory_key: "\n".join(string_buffer)}
        except Exception as e:
            logger.error(f"Error loading memory variables: {e}")
            # Return empty context on error to avoid breaking the chain
            return {self.memory_key: "" if not self.return_messages else []}
    
    def clear(self) -> None:
        """Clear all working memory."""
        try:
            self.working_memory.clear()
            logger.debug("Working memory cleared")
        except Exception as e:
            logger.error(f"Error clearing working memory: {e}")
            raise


class EpisodicMemoryAdapter(NCAMemory):
    """
    Adapter for NCA's episodic memory to LangChain's memory interface.
    
    This adapter provides access to the medium-term episodic memory
    of the NCA system, suitable for recalling specific interactions
    and events from past conversations.
    
    Attributes:
        episodic_memory (EpisodicMemory): The underlying episodic memory instance
        retrieval_threshold (float): Threshold for memory retrieval relevance
    """
    
    def __init__(
        self,
        retrieval_threshold: float = 0.7,
        memory_key: str = "episodic_memory",
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        return_messages: bool = False,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the episodic memory adapter.
        
        Args:
            retrieval_threshold: Threshold for memory retrieval relevance
            memory_key: Key to use for the memory in the chain's context
            input_key: Key to extract input from chain's inputs
            output_key: Key to extract output from chain's outputs
            return_messages: Whether to return messages or a string summary
            human_prefix: Prefix for human messages in string representation
            ai_prefix: Prefix for AI messages in string representation
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            memory_key=memory_key,
            input_key=input_key,
            output_key=output_key,
            return_messages=return_messages,
            human_prefix=human_prefix,
            ai_prefix=ai_prefix,
            **kwargs
        )
        self.retrieval_threshold = retrieval_threshold
        self.episodic_memory = EpisodicMemory()
        logger.debug(f"Initialized EpisodicMemoryAdapter with threshold: {retrieval_threshold}")
    
    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """
        Save the context of the conversation to episodic memory.
        
        Args:
            inputs: The inputs to the chain
            outputs: The outputs from the chain
        """
        input_str, output_str = self._get_input_output(inputs, outputs)
        
        try:
            # Create a combined memory entry representing the exchange
            timestamp = datetime.now()
            episode = MemoryEntry(
                content=f"{self.human_prefix}: {input_str}\n{self.ai_prefix}: {output_str}",
                source="conversation",
                timestamp=timestamp,
                memory_type=MemoryType.EPISODIC,
                metadata={
                    "session_id": self.memory_id,
                    "human_message": input_str,
                    "ai_message": output_str,
                    "timestamp_iso": timestamp.isoformat()
                }
            )
            
            # Add to episodic memory
            self.episodic_memory.add(episode)
            logger.debug(f"Saved context to episodic memory: {episode.content[:50]}...")
        except Exception as e:
            logger.error(f"Error saving context to episodic memory: {e}")
            raise
    
    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Load memory variables from episodic memory based on relevance to current input.
        
        Args:
            inputs: The inputs to the chain
            
        Returns:
            Dict containing the memory key and its value
        """
        if self.input_key is None:
            try:
                input_key = get_prompt_input_key(inputs, self.memory_variables)
                self.input_key = input_key
            except ValueError:
                logger.warning("Could not automatically determine input key")
                return {self.memory_key: "" if not self.return_messages else []}
        
        if self.input_key not in inputs:
            logger.warning(f"Input key '{self.input_key}' not found in inputs")
            return {self.memory_key: "" if not self.return_messages else []}
        
        query_text = str(inputs[self.input_key])
        
        try:
            # Create a query to search episodic memory
            query = MemoryQuery(
                text=query_text,
                threshold=self.retrieval_threshold,
                limit=5  # Retrieve top 5 relevant episodes
            )
            
            # Retrieve relevant episodes
            relevant_episodes = self.episodic_memory.retrieve(query)
            
            if not relevant_episodes:
                logger.debug("No relevant episodes found in episodic memory")
                return {self.memory_key: "" if not self.return_messages else []}
            
            if self.return_messages:
                messages = []
                for episode in relevant_episodes:
                    # Extract human and AI messages from the episode metadata
                    if "human_message" in episode.metadata and "ai_message" in episode.metadata:
                        messages.append(HumanMessage(content=episode.metadata["human_message"]))
                        messages.append(AIMessage(content=episode.metadata["ai_message"]))
                return {self.memory_key: messages}
            else:
                # Format as string with timestamps
                string_buffer = []
                for episode in relevant_episodes:
                    timestamp_str = episode.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    string_buffer.append(f"[{timestamp_str}] {episode.content}")
                
                return {self.memory_key: "\n\n".join(string_buffer)}
        except Exception as e:
            logger.error(f"Error loading episodic memory variables: {e}")
            # Return empty context on error to avoid breaking the chain
            return {self.memory_key: "" if not self.return_messages else []}
    
    def clear(self) -> None:
        """Clear all episodic memory for the current session."""
        try:
            # Only clear episodes from the current session
            self.episodic_memory.clear(filter_criteria={"session_id": self.memory_id})
            logger.debug(f"Episodic memory cleared for session: {self.memory_id}")
        except Exception as e:
            logger.error(f"Error clearing episodic memory: {e}")
            raise


class SemanticMemoryAdapter(NCAMemory):
    """
    Adapter for NCA's semantic memory to LangChain's memory interface.
    
    This adapter provides access to the long-term semantic memory
    of the NCA system, suitable for storing and retrieving conceptual
    knowledge and learned information.
    
    Attributes:
        semantic_memory (SemanticMemory): The underlying semantic memory instance
        retrieval_threshold (float): Threshold for memory retrieval relevance
        max_tokens (int): Maximum number of tokens to return in memory
    """
    
    def __init__(
        self,
        retrieval_threshold: float = 0.6,
        max_tokens: int = 1000,
        memory_key: str = "semantic_memory",
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        return_messages: bool = False,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the semantic memory adapter.
        
        Args:
            retrieval_threshold: Threshold for memory retrieval relevance
            max_tokens: Maximum number of tokens to return in memory
            memory_key: Key to use for the memory in the chain's context
            input_key: Key to extract input from chain's inputs
            output_key: Key to extract output from chain's outputs
            return_messages: Whether to return messages or a string summary
            human_prefix: Prefix for human messages in string representation
            ai_prefix: Prefix for AI messages in string representation
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            memory_key=memory_key,
            input_key=input_key,
            output_key=output_key,
            return_messages=return_messages,
            human_prefix=human_prefix,
            ai_prefix=ai_prefix,
            **kwargs
        )
        self.retrieval_threshold = retrieval_threshold
        self.max_tokens = max_tokens
        self.semantic_memory = SemanticMemory()
        self._important_concepts: set[str] = set()
        logger.debug(f"Initialized SemanticMemoryAdapter with threshold: {retrieval_threshold}")
    
    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """
        Extract and save important concepts and knowledge to semantic memory.
        
        Args:
            inputs: The inputs to the chain
            outputs: The outputs from the chain
        """
        input_str, output_str = self._get_input_output(inputs, outputs)
        
        try:
            # Extract potential knowledge from the AI's response
            # In a real implementation, this would use NLP to identify
            # factual statements, definitions, and important concepts
            
            # For this implementation, we'll use a simple approach:
            # Save the entire AI response as a semantic memory entry
            knowledge_entry = MemoryEntry(
                content=output_str,
                source="ai_response",
                timestamp=datetime.now(),
                memory_type=MemoryType.SEMANTIC,
                metadata={
                    "session_id": self.memory_id,
                    "context": input_str[:200],  # Store partial context
                    "confidence": 0.8  # Arbitrary confidence score
                }
            )
            
            # Add to semantic memory
            self.semantic_memory.add(knowledge_entry)
            
            # Track important concepts mentioned (simplified implementation)
            # In a real system, this would use NLP for entity extraction
            self._update_important_concepts(input_str, output_str)
            
            logger.debug(f"Saved knowledge to semantic memory: {output_str[:50]}...")
        except Exception as e:
            logger.error(f"Error saving context to semantic memory: {e}")
            raise
    
    def _update_important_concepts(self, input_str: str, output_str: str) -> None:
        """
        Extract and track important concepts from the conversation.
        
        This is a simplified implementation. In a real system, this would
        use NLP techniques to extract entities, concepts, and relationships.
        
        Args:
            input_str: The input from the human
            output_str: The output from the AI
        """
        # Simple implementation - look for capitalized phrases as potential concepts
        # This is just a placeholder for a more sophisticated NLP approach
        combined_text = f"{input_str} {output_str}"
        words = combined_text.split()
        
        for i, word in enumerate(words):
            if word and word[0].isupper() and len(word) > 3:
                # Check if this is part of a multi-word concept
                concept = word
                j = i + 1
                while j < len(words) and words[j][0].isupper() if words[j] else False:
                    concept += " " + words[j]
                    j += 1
                
                if concept not in self._important_concepts:
                    self._important_concepts.add(concept)
                    logger.debug(f"Added concept to tracking: {concept}")
    
    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Load relevant knowledge from semantic memory based on the current input.
        
        Args:
            inputs: The inputs to the chain
            
        Returns:
            Dict containing the memory key and its value
        """
        if self.input_key is None:
            try:
                input_key = get_prompt_input_key(inputs, self.memory_variables)
                self.input_key = input_key
            except ValueError:
                logger.warning("Could not automatically determine input key")
                return {self.memory_key: "" if not self.return_messages else []}
        
        if self.input_key not in inputs:
            logger.warning(f"Input key '{self.input_key}' not found in inputs")
            return {self.memory_key: "" if not self.return_messages else []}
        
        query_text = str(inputs[self.input_key])
        
        try:
            # Create a query to search semantic memory
            query = MemoryQuery(
                text=query_text,
                threshold=self.retrieval_threshold,
                limit=10  # Retrieve top 10 relevant knowledge entries
            )
            
            # Retrieve relevant knowledge
            relevant_knowledge = self.semantic_memory.retrieve(query)
            
            if not relevant_knowledge:
                logger.debug("No relevant knowledge found in semantic memory")
                return {self.memory_key: "" if not self.return_messages else []}
            
            # Format the knowledge for return
            if self.return_messages:
                # For message format, we'll create a single AI message with the knowledge
                knowledge_text = "Relevant knowledge from memory:\n\n"
                for entry in relevant_knowledge:
                    knowledge_text += f"- {entry.content}\n\n"
                
                # Truncate if too long (simple token estimation)
                if len(knowledge_text.split()) > self.max_tokens:
                    knowledge_text = " ".join(knowledge_text.split()[:self.max_tokens]) + "..."
                
                return {self.memory_key: [AIMessage(content=knowledge_text)]}
            else:
                # Format as string
                knowledge_sections = []
                for entry in relevant_knowledge:
                    knowledge_sections.append(f"KNOWLEDGE: {entry.content}")
                
                knowledge_text = "\n\n".join(knowledge_sections)
                
                # Truncate if too long (simple token estimation)
                if len(knowledge_text.split()) > self.max_tokens:
                    knowledge_text = " ".join(knowledge_text.split()[:self.max_tokens]) + "..."
                
                return {self.memory_key: knowledge_text}
        except Exception as e:
            logger.error(f"Error loading semantic memory variables: {e}")
            # Return empty context on error to avoid breaking the chain
            return {self.memory_key: "" if not self.return_messages else []}
    
    def clear(self) -> None:
        """Clear semantic memory for the current session."""
        try:
            # Only clear entries from the current session
            self.semantic_memory.clear(filter_criteria={"session_id": self.memory_id})
            self._important_concepts.clear()
            logger.debug(f"Semantic memory cleared for session: {self.memory_id}")
        except Exception as e:
            logger.error(f"Error clearing semantic memory: {e}")
            raise


class MemoryFactory:
    """
    Factory class for creating appropriate memory instances.
    
    This factory provides methods to create different types of memory
    adapters with appropriate configuration, simplifying the integration
    of NCA memory with LangChain.
    """
    
    @staticmethod
    def create_memory(
        memory_type: str = "working",
        **kwargs: Any
    ) -> NCAMemory:
        """
        Create a memory instance of the specified type.
        
        Args:
            memory_type: Type of memory to create ("working", "episodic", "semantic", or "combined")
            **kwargs: Additional configuration parameters for the memory
            
        Returns:
            An instance of NCAMemory
            
        Raises:
            ValueError: If an invalid memory type is specified
        """
        memory_type = memory_type.lower()
        
        if memory_type == "working":
            return WorkingMemoryAdapter(**kwargs)
        elif memory_type == "episodic":
            return EpisodicMemoryAdapter(**kwargs)
        elif memory_type == "semantic":
            return SemanticMemoryAdapter(**kwargs)
        elif memory_type == "combined":
            # Implementation of combined memory would go here
            # This would integrate all three memory types
            raise NotImplementedError("Combined memory type is not yet implemented")
        else:
            raise ValueError(f"Invalid memory type: {memory_type}")
    
    @staticmethod
    def create_working_memory(
        capacity: int = 10,
        decay_rate: float = 0.1,
        **kwargs: Any
    ) -> WorkingMemoryAdapter:
        """
        Create a working memory adapter with the specified configuration.
        
        Args:
            capacity: Maximum number of messages to store
            decay_rate: Rate at which memory items decay
            **kwargs: Additional configuration parameters
            
        Returns:
            A WorkingMemoryAdapter instance
        """
        return WorkingMemoryAdapter(capacity=capacity, decay_rate=decay_rate, **kwargs)
    
    @staticmethod
    def create_episodic_memory(
        retrieval_threshold: float = 0.7,
        **kwargs: Any
    ) -> EpisodicMemoryAdapter:
        """
        Create an episodic memory adapter with the specified configuration.
        
        Args:
            retrieval_threshold: Threshold for memory retrieval relevance
            **kwargs: Additional configuration parameters
            
        Returns:
            An EpisodicMemoryAdapter instance
        """
        return EpisodicMemoryAdapter(retrieval_threshold=retrieval_threshold, **kwargs)
    
    @staticmethod
    def create_semantic_memory(
        retrieval_threshold: float = 0.6,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> SemanticMemoryAdapter:
        """
        Create a semantic memory adapter with the specified configuration.
        
        Args:
            retrieval_threshold: Threshold for memory retrieval relevance
            max_tokens: Maximum number of tokens to return in memory
            **kwargs: Additional configuration parameters
            
        Returns:
            A SemanticMemoryAdapter instance
        """
        return SemanticMemoryAdapter(
            retrieval_threshold=retrieval_threshold,
            max_tokens=max_tokens,
            **kwargs
        )