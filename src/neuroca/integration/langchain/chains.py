"""
LangChain Chain Integration Module for NeuroCognitive Architecture (NCA).

This module provides custom chain implementations and extensions for LangChain
that integrate with the NeuroCognitive Architecture. It includes specialized chains
that leverage NCA's memory tiers, health dynamics, and cognitive processes.

The chains in this module are designed to:
1. Connect LangChain's chain functionality with NCA's memory systems
2. Incorporate health dynamics and cognitive constraints into chain execution
3. Provide specialized reasoning and cognitive processing chains
4. Support monitoring and introspection of chain execution

Usage:
    from neuroca.integration.langchain.chains import NCACognitiveChain
    
    # Create a cognitive chain with memory integration
    chain = NCACognitiveChain(
        llm=your_llm,
        memory_manager=your_memory_manager,
        health_monitor=your_health_monitor
    )
    
    # Run the chain with cognitive processing
    result = chain.run("Process this information with your cognitive architecture")
"""

import logging
import time
from typing import Any, Optional, TypeVar

from langchain.callbacks.base import BaseCallbackHandler, Callbacks
from langchain.chains import LLMChain, SequentialChain

# LangChain imports
from langchain.chains.base import Chain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseLanguageModel, BaseMemory

from neuroca.core.exceptions import (
    CognitiveOverloadException,
    HealthConstraintException,
    MemoryAccessException,
    NCAChainException,
)
from neuroca.core.health import HealthMonitor

# NeuroCognitive Architecture imports
from neuroca.memory.manager import MemoryManager
from neuroca.memory.models import MemoryItem, MemoryTier

# Set up module logger
logger = logging.getLogger(__name__)

# Type variable for chain return types
T = TypeVar('T')

class NCACallbackHandler(BaseCallbackHandler):
    """
    Callback handler for monitoring and logging chain execution within the NCA system.
    
    This handler captures metrics, logs events, and can trigger health dynamics
    updates during chain execution.
    """
    
    def __init__(
        self, 
        health_monitor: Optional[HealthMonitor] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize the NCA callback handler.
        
        Args:
            health_monitor: Optional health monitor to update during chain execution
            log_level: Logging level for chain execution events
        """
        self.health_monitor = health_monitor
        self.log_level = log_level
        self.start_time = None
        self.total_tokens = 0
        
    def on_chain_start(
        self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs: Any
    ) -> None:
        """Log the start of chain execution and initialize metrics."""
        self.start_time = time.time()
        chain_type = serialized.get("id", ["unknown"])[-1]
        logger.log(self.log_level, f"Starting chain execution: {chain_type}")
        
    def on_chain_end(
        self, outputs: dict[str, Any], **kwargs: Any
    ) -> None:
        """
        Log the end of chain execution and update health metrics.
        
        This method calculates execution time and updates the health monitor
        with cognitive load metrics if available.
        """
        if self.start_time:
            execution_time = time.time() - self.start_time
            logger.log(
                self.log_level, 
                f"Chain execution completed in {execution_time:.2f}s with {self.total_tokens} tokens"
            )
            
            # Update health metrics if monitor is available
            if self.health_monitor:
                self.health_monitor.update_metrics(
                    cognitive_load=min(1.0, self.total_tokens / 10000),  # Normalize to 0-1
                    processing_time=execution_time
                )
                
    def on_chain_error(
        self, error: Exception, **kwargs: Any
    ) -> None:
        """Log chain execution errors and update health metrics."""
        logger.error(f"Chain execution error: {str(error)}", exc_info=True)
        
        # Update health metrics on error if monitor is available
        if self.health_monitor:
            self.health_monitor.register_error(error_type=type(error).__name__)


class NCAMemoryAdapter(BaseMemory):
    """
    Adapter that connects LangChain's memory interface with NCA's memory system.
    
    This adapter translates between LangChain's memory operations and NCA's
    multi-tiered memory system, allowing chains to leverage the cognitive
    architecture's memory capabilities.
    """
    
    def __init__(
        self, 
        memory_manager: MemoryManager,
        memory_key: str = "history",
        input_key: str = "input",
        output_key: str = "output",
        return_messages: bool = False,
        tier_preference: MemoryTier = MemoryTier.WORKING
    ):
        """
        Initialize the NCA memory adapter.
        
        Args:
            memory_manager: The NCA memory manager to use for storage
            memory_key: The key to use for the memory in chain inputs/outputs
            input_key: The key for inputs to be stored in memory
            output_key: The key for outputs to be stored in memory
            return_messages: Whether to return memory as messages or a string
            tier_preference: The preferred memory tier to use for storage/retrieval
        """
        self.memory_manager = memory_manager
        self.memory_key = memory_key
        self.input_key = input_key
        self.output_key = output_key
        self.return_messages = return_messages
        self.tier_preference = tier_preference
        
    @property
    def memory_variables(self) -> list[str]:
        """Return the memory variables that this memory adapter makes available."""
        return [self.memory_key]
    
    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Load memory variables from the NCA memory system.
        
        Args:
            inputs: The inputs to the chain
            
        Returns:
            Dict containing memory variables
            
        Raises:
            MemoryAccessException: If memory access fails
        """
        try:
            # Retrieve relevant memories from the memory manager
            query = inputs.get(self.input_key, "")
            memories = self.memory_manager.retrieve_relevant(
                query=query, 
                tier=self.tier_preference,
                limit=10  # Configurable limit
            )
            
            if self.return_messages:
                # Format as messages for chat models
                formatted_memories = [
                    {"role": "user" if i % 2 == 0 else "assistant", "content": m.content}
                    for i, m in enumerate(memories)
                ]
            else:
                # Format as string for completion models
                formatted_memories = "\n".join([m.content for m in memories])
                
            logger.debug(f"Loaded {len(memories)} memories from {self.tier_preference.name}")
            return {self.memory_key: formatted_memories}
            
        except Exception as e:
            logger.error(f"Memory access error: {str(e)}", exc_info=True)
            raise MemoryAccessException(f"Failed to load memories: {str(e)}") from e
    
    def save_context(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        """
        Save the context of this interaction to the NCA memory system.
        
        Args:
            inputs: The inputs to the chain
            outputs: The outputs from the chain
            
        Raises:
            MemoryAccessException: If memory storage fails
        """
        try:
            input_str = inputs.get(self.input_key, "")
            output_str = outputs.get(self.output_key, "")
            
            if input_str:
                # Store input as a memory item
                self.memory_manager.store(
                    MemoryItem(
                        content=input_str,
                        source="user",
                        importance=0.7,  # Default importance, could be dynamic
                        tier=self.tier_preference
                    )
                )
                
            if output_str:
                # Store output as a memory item
                self.memory_manager.store(
                    MemoryItem(
                        content=output_str,
                        source="system",
                        importance=0.7,  # Default importance, could be dynamic
                        tier=self.tier_preference
                    )
                )
                
            logger.debug(f"Saved interaction context to {self.tier_preference.name} memory")
            
        except Exception as e:
            logger.error(f"Memory storage error: {str(e)}", exc_info=True)
            raise MemoryAccessException(f"Failed to save context: {str(e)}") from e
    
    def clear(self) -> None:
        """
        Clear the memory contents for this adapter.
        
        Raises:
            MemoryAccessException: If memory clearing fails
        """
        try:
            # Clear only the working memory tier by default
            self.memory_manager.clear(tier=MemoryTier.WORKING)
            logger.info("Cleared working memory")
        except Exception as e:
            logger.error(f"Memory clear error: {str(e)}", exc_info=True)
            raise MemoryAccessException(f"Failed to clear memory: {str(e)}") from e


class NCACognitiveChain(Chain):
    """
    A chain that incorporates NCA's cognitive architecture components.
    
    This chain integrates with the memory system, health dynamics, and cognitive
    constraints of the NeuroCognitive Architecture to provide more biologically
    plausible processing.
    """
    
    memory_manager: MemoryManager
    llm: BaseLanguageModel
    prompt: PromptTemplate
    health_monitor: Optional[HealthMonitor] = None
    output_key: str = "output"
    
    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True
    
    @property
    def input_keys(self) -> list[str]:
        """Return the input keys for this chain."""
        return [k for k in self.prompt.input_variables if k != self.memory_key]
    
    @property
    def output_keys(self) -> list[str]:
        """Return the output keys for this chain."""
        return [self.output_key]
    
    @property
    def memory_key(self) -> str:
        """Return the memory key for this chain."""
        return "memory"
    
    def _check_health_constraints(self) -> None:
        """
        Check if health constraints allow chain execution.
        
        Raises:
            HealthConstraintException: If health constraints prevent execution
        """
        if self.health_monitor:
            health_status = self.health_monitor.get_status()
            
            # Check if cognitive resources are too depleted
            if health_status.cognitive_load > 0.9:
                logger.warning(f"Cognitive overload detected: {health_status.cognitive_load:.2f}")
                raise CognitiveOverloadException(
                    "Cognitive resources depleted, execution paused"
                )
                
            # Check other health constraints
            if not health_status.is_operational:
                logger.warning("System health below operational threshold")
                raise HealthConstraintException(
                    f"System health constraints prevent execution: {health_status.status_message}"
                )
    
    def _get_memory_adapter(self) -> NCAMemoryAdapter:
        """Create and return a memory adapter for this chain."""
        return NCAMemoryAdapter(
            memory_manager=self.memory_manager,
            memory_key=self.memory_key,
            tier_preference=MemoryTier.WORKING
        )
    
    def _get_callbacks(self, callbacks: Callbacks = None) -> list[BaseCallbackHandler]:
        """Get callbacks for this chain execution, including NCA-specific handlers."""
        # Start with any provided callbacks
        cb_list = callbacks or []
        if not isinstance(cb_list, list):
            cb_list = [cb_list]
            
        # Add NCA callback handler
        cb_list.append(NCACallbackHandler(health_monitor=self.health_monitor))
        
        return cb_list
    
    def _call(self, inputs: dict[str, Any], run_manager=None) -> dict[str, Any]:
        """
        Execute the cognitive chain with NCA integration.
        
        Args:
            inputs: The inputs to the chain
            run_manager: Optional run manager for callbacks
            
        Returns:
            Dict containing chain outputs
            
        Raises:
            NCAChainException: If chain execution fails
            HealthConstraintException: If health constraints prevent execution
            CognitiveOverloadException: If cognitive resources are depleted
        """
        try:
            # Check health constraints before execution
            self._check_health_constraints()
            
            # Load memory variables
            memory_adapter = self._get_memory_adapter()
            memory_variables = memory_adapter.load_memory_variables(inputs)
            
            # Combine inputs with memory
            chain_inputs = {**inputs, **memory_variables}
            
            # Create and run LLM chain
            llm_chain = LLMChain(
                llm=self.llm,
                prompt=self.prompt,
                output_key=self.output_key
            )
            
            # Execute the chain
            outputs = llm_chain(chain_inputs, callbacks=run_manager.get_child() if run_manager else None)
            
            # Save context to memory
            memory_adapter.save_context(
                inputs=inputs,
                outputs=outputs
            )
            
            return outputs
            
        except (HealthConstraintException, CognitiveOverloadException):
            # Re-raise health-related exceptions
            raise
            
        except Exception as e:
            logger.error(f"Cognitive chain execution error: {str(e)}", exc_info=True)
            raise NCAChainException(f"Chain execution failed: {str(e)}") from e


class NCAReflectiveChain(NCACognitiveChain):
    """
    A cognitive chain with reflective capabilities.
    
    This chain extends the basic cognitive chain with the ability to reflect on
    its own processing, incorporating metacognition into the chain execution.
    """
    
    reflection_prompt: PromptTemplate
    reflection_threshold: float = 0.7  # Threshold for when to trigger reflection
    
    def _should_reflect(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> bool:
        """
        Determine if reflection should be triggered based on inputs and outputs.
        
        Args:
            inputs: The inputs to the chain
            outputs: The outputs from the chain
            
        Returns:
            Boolean indicating whether reflection should be triggered
        """
        # Check if health monitor indicates high uncertainty
        if self.health_monitor and self.health_monitor.get_status().uncertainty > self.reflection_threshold:
            return True
            
        # Additional heuristics could be implemented here
        return False
    
    def _reflect(self, inputs: dict[str, Any], outputs: dict[str, Any], run_manager=None) -> dict[str, Any]:
        """
        Perform reflection on the chain's processing.
        
        Args:
            inputs: The inputs to the chain
            outputs: The outputs from the chain
            run_manager: Optional run manager for callbacks
            
        Returns:
            Dict containing reflection outputs
        """
        # Prepare reflection inputs
        reflection_inputs = {
            "original_input": inputs.get("input", ""),
            "original_output": outputs.get(self.output_key, ""),
            "memory": inputs.get(self.memory_key, "")
        }
        
        # Create reflection chain
        reflection_chain = LLMChain(
            llm=self.llm,
            prompt=self.reflection_prompt,
            output_key="reflection"
        )
        
        # Run reflection
        reflection_result = reflection_chain(
            reflection_inputs, 
            callbacks=run_manager.get_child() if run_manager else None
        )
        
        # Store reflection in memory
        self.memory_manager.store(
            MemoryItem(
                content=f"Reflection: {reflection_result['reflection']}",
                source="system_reflection",
                importance=0.8,
                tier=MemoryTier.WORKING
            )
        )
        
        logger.info("Performed chain reflection")
        return reflection_result
    
    def _call(self, inputs: dict[str, Any], run_manager=None) -> dict[str, Any]:
        """
        Execute the reflective cognitive chain.
        
        This overrides the base _call method to add reflection capabilities.
        
        Args:
            inputs: The inputs to the chain
            run_manager: Optional run manager for callbacks
            
        Returns:
            Dict containing chain outputs with possible reflection
        """
        # Execute the base cognitive chain
        outputs = super()._call(inputs, run_manager)
        
        # Check if reflection should be triggered
        if self._should_reflect(inputs, outputs):
            reflection_result = self._reflect(inputs, outputs, run_manager)
            
            # Optionally incorporate reflection into the output
            outputs["reflection"] = reflection_result["reflection"]
            
        return outputs


class NCASequentialChain(SequentialChain):
    """
    A sequential chain that incorporates NCA's cognitive architecture.
    
    This chain extends LangChain's SequentialChain with NCA-specific features
    like health monitoring, memory integration, and cognitive constraints.
    """
    
    health_monitor: Optional[HealthMonitor] = None
    memory_manager: Optional[MemoryManager] = None
    
    def _get_callbacks(self, callbacks: Callbacks = None) -> list[BaseCallbackHandler]:
        """Get callbacks for this chain execution, including NCA-specific handlers."""
        # Start with any provided callbacks
        cb_list = callbacks or []
        if not isinstance(cb_list, list):
            cb_list = [cb_list]
            
        # Add NCA callback handler
        if self.health_monitor:
            cb_list.append(NCACallbackHandler(health_monitor=self.health_monitor))
        
        return cb_list
    
    def _check_health_constraints(self) -> None:
        """
        Check if health constraints allow chain execution.
        
        Raises:
            HealthConstraintException: If health constraints prevent execution
        """
        if self.health_monitor:
            health_status = self.health_monitor.get_status()
            
            # Check if cognitive resources are too depleted
            if health_status.cognitive_load > 0.9:
                logger.warning(f"Cognitive overload detected: {health_status.cognitive_load:.2f}")
                raise CognitiveOverloadException(
                    "Cognitive resources depleted, execution paused"
                )
                
            # Check other health constraints
            if not health_status.is_operational:
                logger.warning("System health below operational threshold")
                raise HealthConstraintException(
                    f"System health constraints prevent execution: {health_status.status_message}"
                )
    
    def __call__(self, inputs: dict[str, Any], return_only_outputs: bool = False, callbacks: Callbacks = None) -> dict[str, Any]:
        """
        Execute the sequential chain with NCA integration.
        
        Args:
            inputs: The inputs to the chain
            return_only_outputs: Whether to return only the outputs
            callbacks: Optional callbacks for the chain
            
        Returns:
            Dict containing chain outputs
            
        Raises:
            NCAChainException: If chain execution fails
            HealthConstraintException: If health constraints prevent execution
            CognitiveOverloadException: If cognitive resources are depleted
        """
        try:
            # Check health constraints before execution
            self._check_health_constraints()
            
            # Get NCA-enhanced callbacks
            nca_callbacks = self._get_callbacks(callbacks)
            
            # Execute the chain with enhanced callbacks
            return super().__call__(
                inputs=inputs,
                return_only_outputs=return_only_outputs,
                callbacks=nca_callbacks
            )
            
        except (HealthConstraintException, CognitiveOverloadException):
            # Re-raise health-related exceptions
            raise
            
        except Exception as e:
            logger.error(f"NCA sequential chain execution error: {str(e)}", exc_info=True)
            raise NCAChainException(f"Sequential chain execution failed: {str(e)}") from e


# Factory functions for creating NCA-integrated chains

def create_cognitive_chain(
    llm: BaseLanguageModel,
    memory_manager: MemoryManager,
    health_monitor: Optional[HealthMonitor] = None,
    prompt_template: Optional[str] = None,
    output_key: str = "output"
) -> NCACognitiveChain:
    """
    Create a cognitive chain with NCA integration.
    
    Args:
        llm: The language model to use
        memory_manager: The memory manager for the chain
        health_monitor: Optional health monitor for the chain
        prompt_template: Optional custom prompt template
        output_key: The key for the chain output
        
    Returns:
        An initialized NCACognitiveChain
    """
    # Use default prompt if none provided
    if prompt_template is None:
        prompt_template = """
        You are an AI assistant with a cognitive architecture.
        
        Context from memory:
        {memory}
        
        Human: {input}
        AI:
        """
    
    # Create prompt template
    prompt = PromptTemplate(
        input_variables=["input", "memory"],
        template=prompt_template
    )
    
    # Create and return the chain
    return NCACognitiveChain(
        llm=llm,
        memory_manager=memory_manager,
        health_monitor=health_monitor,
        prompt=prompt,
        output_key=output_key
    )


def create_reflective_chain(
    llm: BaseLanguageModel,
    memory_manager: MemoryManager,
    health_monitor: Optional[HealthMonitor] = None,
    prompt_template: Optional[str] = None,
    reflection_template: Optional[str] = None,
    reflection_threshold: float = 0.7,
    output_key: str = "output"
) -> NCAReflectiveChain:
    """
    Create a reflective cognitive chain with NCA integration.
    
    Args:
        llm: The language model to use
        memory_manager: The memory manager for the chain
        health_monitor: Optional health monitor for the chain
        prompt_template: Optional custom prompt template
        reflection_template: Optional custom reflection template
        reflection_threshold: Threshold for triggering reflection
        output_key: The key for the chain output
        
    Returns:
        An initialized NCAReflectiveChain
    """
    # Use default prompt if none provided
    if prompt_template is None:
        prompt_template = """
        You are an AI assistant with a cognitive architecture.
        
        Context from memory:
        {memory}
        
        Human: {input}
        AI:
        """
    
    # Use default reflection prompt if none provided
    if reflection_template is None:
        reflection_template = """
        Reflect on your previous response. Consider:
        1. Was your response accurate and complete?
        2. Did you miss any important context?
        3. Could your reasoning be improved?
        
        Original input: {original_input}
        Your response: {original_output}
        Memory context: {memory}
        
        Reflection:
        """
    
    # Create prompt templates
    prompt = PromptTemplate(
        input_variables=["input", "memory"],
        template=prompt_template
    )
    
    reflection_prompt = PromptTemplate(
        input_variables=["original_input", "original_output", "memory"],
        template=reflection_template
    )
    
    # Create and return the chain
    return NCAReflectiveChain(
        llm=llm,
        memory_manager=memory_manager,
        health_monitor=health_monitor,
        prompt=prompt,
        reflection_prompt=reflection_prompt,
        reflection_threshold=reflection_threshold,
        output_key=output_key
    )