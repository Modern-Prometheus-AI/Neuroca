"""
NeuroCognitive Architecture (NCA) - LLM Integration Manager

This module provides the main integration manager for LLM interactions. It serves
as the central coordinator between the NCA cognitive architecture and external
LLM providers, allowing seamless integration with various LLMs including cloud-based
and local models.

The manager:
1. Provides a provider-agnostic interface to LLMs
2. Manages LLM provider selection and fallbacks
3. Enhances prompts with memory state and cognitive context
4. Filters and processes responses based on NCA constraints
5. Adapts interactions based on health metrics and goal state
"""

import logging
import time
from typing import Any, Optional

from neuroca.core.cognitive_control.goal_manager import GoalManager
from neuroca.core.health.dynamics import HealthDynamicsManager, HealthState
from neuroca.memory.manager import MemoryManager

from .adapters import AnthropicAdapter, OpenAIAdapter, VertexAIAdapter
from .adapters import (  # Import necessary adapter classes
    BaseAdapter as LLMAdapter,  # Assuming BaseAdapter is the intended type for LLMAdapter
)
from .context.manager import ContextManager
from .exceptions import LLMIntegrationError, ProviderNotFoundError
from .models import LLMRequest, LLMResponse

# from .prompts.templates import get_template # Removed incorrect import
from .prompts.templates import TemplateManager  # Import the manager class

logger = logging.getLogger(__name__)

class LLMIntegrationManager:
    """
    The main manager class for integrating LLMs with the NeuroCognitive Architecture.
    
    This class provides a unified interface for interacting with various LLM providers,
    while enhancing queries with NCA's cognitive capabilities.
    """
    
    def __init__(
        self,
        config: dict[str, Any],
        memory_manager: Optional[MemoryManager] = None,
        health_manager: Optional[HealthDynamicsManager] = None,
        goal_manager: Optional[GoalManager] = None
    ):
        """
        Initialize the LLM integration manager.
        
        Args:
            config: Configuration dictionary with provider settings
            memory_manager: Optional MemoryManager for memory integration
            health_manager: Optional HealthDynamicsManager for health awareness
            goal_manager: Optional GoalManager for goal-directed prompting
        """
        self.config = config
        self.memory_manager = memory_manager
        self.health_manager = health_manager
        self.goal_manager = goal_manager
        self.context_manager = ContextManager()
        self.template_manager = TemplateManager(template_dirs=config.get("prompt_template_dirs")) # Instantiate TemplateManager
        
        # Initialize adapters for different providers
        self.adapters: dict[str, LLMAdapter] = {}
        self._initialize_adapters()
        
        # Track active provider and model
        self.default_provider = config.get("default_provider", "openai")
        self.default_model = config.get("default_model", "gpt-4")
        
        # Performance tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_times = []
        
        logger.info(f"LLM Integration Manager initialized with {len(self.adapters)} providers")
        
    def _initialize_adapters(self):
        """Initialize adapters for each configured provider."""
        provider_configs = self.config.get("providers", {})
        
        # Initialize built-in adapters
        if "openai" in provider_configs:
            self.adapters["openai"] = OpenAIAdapter(provider_configs["openai"])
            
        if "anthropic" in provider_configs:
            self.adapters["anthropic"] = AnthropicAdapter(provider_configs["anthropic"])
            
        if "vertexai" in provider_configs:
            self.adapters["vertexai"] = VertexAIAdapter(provider_configs["vertexai"])
            
        # Initialize Ollama local models if configured
        if "ollama" in provider_configs:
            try:
                from .adapters.ollama import OllamaAdapter
                self.adapters["ollama"] = OllamaAdapter(provider_configs["ollama"])
            except ImportError:
                logger.warning("Ollama adapter requested but not available - install with pip install neuroca[ollama]")
        
        # Load any custom adapters
        custom_adapters = self.config.get("custom_adapters", {})
        for adapter_name, adapter_config in custom_adapters.items():
            module_path = adapter_config.get("module")
            class_name = adapter_config.get("class")
            
            if module_path and class_name:
                try:
                    module = __import__(module_path, fromlist=[class_name])
                    adapter_class = getattr(module, class_name)
                    self.adapters[adapter_name] = adapter_class(adapter_config)
                    logger.info(f"Loaded custom adapter: {adapter_name}")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Failed to load custom adapter {adapter_name}: {str(e)}")
    
    async def query(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        memory_context: bool = True,
        health_aware: bool = True,
        goal_directed: bool = True,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        additional_context: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send a query to an LLM provider with NCA cognitive enhancements.
        
        Args:
            prompt: The base prompt to send to the LLM
            provider: Optional provider name (default: configured default)
            model: Optional model name (default: configured default)
            memory_context: Whether to enhance with memory context
            health_aware: Whether to adapt based on system health
            goal_directed: Whether to include goal context
            max_tokens: Maximum number of tokens in the response
            temperature: Temperature for response generation
            additional_context: Additional context to include
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse containing the model's response and metadata
            
        Raises:
            ProviderNotFoundError: If the specified provider is not available
            LLMIntegrationError: For general integration errors
        """
        start_time = time.time()
        self.total_requests += 1
        
        # Select provider and model
        provider = provider or self.default_provider
        model = model or self.default_model
        
        # Validate provider
        if provider not in self.adapters:
            raise ProviderNotFoundError(f"Provider {provider} not configured")
        
        # Enhance prompt with NCA cognitive capabilities
        enhanced_prompt = await self._enhance_prompt(
            prompt, 
            memory_context=memory_context,
            health_aware=health_aware,
            goal_directed=goal_directed,
            additional_context=additional_context
        )
        
        # Create request
        request = LLMRequest(
            provider=provider,
            model=model,
            prompt=enhanced_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        # Execute request
        try:
            response = await self.adapters[provider].execute(request)
            
            # Process response through NCA cognitive filter
            processed_response = await self._process_response(response)
            
            # Update metrics
            elapsed = time.time() - start_time
            self.request_times.append(elapsed)
            self.total_tokens += response.usage.total_tokens if response.usage else 0
            self.total_cost += response.cost if response.cost is not None else 0.0
            
            return processed_response
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error during LLM query: {str(e)}")
            raise LLMIntegrationError(f"Failed to execute query: {str(e)}") from e
            
    async def _enhance_prompt(
        self,
        base_prompt: str,
        memory_context: bool = True,
        health_aware: bool = True,
        goal_directed: bool = True,
        additional_context: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Enhance a prompt with NCA cognitive capabilities.
        
        This method enriches the base prompt with:
        - Relevant memories from the memory system
        - Health state awareness
        - Goal-directed context
        - Additional provided context
        
        Args:
            base_prompt: The original prompt
            memory_context: Whether to include memory context
            health_aware: Whether to adapt based on health state
            goal_directed: Whether to include goal context
            additional_context: Additional context to include
            
        Returns:
            Enhanced prompt with NCA cognitive capabilities
        """
        context_data = additional_context or {}
        
        # Add memory context if requested and available
        if memory_context and self.memory_manager:
            # Extract query vector or keywords from prompt
            memory_results = await self._retrieve_relevant_memories(base_prompt)
            if memory_results:
                context_data["memories"] = memory_results
                
        # Add health context if requested and available
        if health_aware and self.health_manager:
            health_state = await self._get_health_context()
            if health_state:
                context_data["health_state"] = health_state
                
        # Add goal context if requested and available
        if goal_directed and self.goal_manager:
            goal_context = await self._get_goal_context()
            if goal_context:
                context_data["goals"] = goal_context

        # Render the enhanced prompt using the TemplateManager
        try:
            # Assume a default template name or determine based on context
            template_name = "base_enhancement" # Placeholder template name
            variables = {
                "base_prompt": base_prompt,
                **context_data # Merge context data as variables
            }
            enhanced_prompt = self.template_manager.render_template(template_name, variables)
            logger.debug(f"Enhanced prompt using template '{template_name}'")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to render prompt template: {e}. Using base prompt.")
            enhanced_prompt = base_prompt # Fallback to base prompt

        # NOTE: The old context_manager.enhance_prompt call is replaced by template rendering.
        # Ensure the ContextManager class is updated or removed if its enhance_prompt is no longer needed.
        
        return enhanced_prompt
        
    async def _process_response(self, response: LLMResponse) -> LLMResponse:
        """
        Process an LLM response through NCA cognitive filters.
        
        This method:
        - Validates response against NCA constraints
        - Enhances response with additional NCA context if needed
        - Records interaction in memory if configured
        
        Args:
            response: The raw LLM response
            
        Returns:
            Processed LLM response
        """
        # Store interaction in memory if configured
        if self.memory_manager and self.config.get("store_interactions", True):
            # Create memory entry
            memory_entry = {
                "type": "llm_interaction",
                "prompt": response.request.prompt,
                "response": response.content,
                "model": response.model,
                "provider": response.provider,
                "timestamp": time.time()
            }
            
            await self.memory_manager.store(
                content=memory_entry,
                memory_type="episodic",
                tags=["llm_interaction"]
            )
            
        # Apply any response transformations based on NCA state
        if self.health_manager:
            health_state = self.health_manager.get_system_health().state
            
            # In compromised health states, add cautionary notes
            if health_state in [HealthState.STRESSED, HealthState.FATIGUED, HealthState.IMPAIRED]:
                caution_note = f"\n[Note: Response generated while system was in {health_state.name} state]"
                response.metadata["health_state"] = health_state.name
                
                # Only add the note in metadata, not to the actual content
                response.metadata["caution_note"] = caution_note
        
        return response
        
    async def _retrieve_relevant_memories(self, query: str) -> list[dict[str, Any]]:
        """
        Retrieve relevant memories based on the query.
        
        Args:
            query: The prompt to find relevant memories for
            
        Returns:
            List of relevant memory entries
        """
        if not self.memory_manager:
            return []
            
        # First check working memory for most relevant context
        working_results = await self.memory_manager.retrieve(
            query=query,
            memory_type="working",
            limit=3
        )
        
        # Then check episodic memory
        episodic_results = await self.memory_manager.retrieve(
            query=query,
            memory_type="episodic",
            limit=5
        )
        
        # Finally check semantic memory for factual knowledge
        semantic_results = await self.memory_manager.retrieve(
            query=query,
            memory_type="semantic",
            limit=3
        )
        
        # Combine and format results
        all_results = []
        
        for result in working_results:
            all_results.append({
                "content": result.content,
                "source": "working_memory",
                "relevance": result.relevance if hasattr(result, "relevance") else 1.0
            })
            
        for result in episodic_results:
            all_results.append({
                "content": result.content,
                "source": "episodic_memory",
                "relevance": result.relevance if hasattr(result, "relevance") else 0.8
            })
            
        for result in semantic_results:
            all_results.append({
                "content": result.content,
                "source": "semantic_memory",
                "relevance": result.relevance if hasattr(result, "relevance") else 0.7
            })
            
        # Sort by relevance
        all_results.sort(key=lambda x: x["relevance"], reverse=True)
        
        return all_results  # noqa: RET504 - Variable used for building list before return
        
    async def _get_health_context(self) -> dict[str, Any]:
        """
        Get current health context for LLM adaptation.
        
        Returns:
            Dictionary with health state information
        """
        if not self.health_manager:
            return {}
            
        system_health = self.health_manager.get_system_health()
        
        # RET504 Fix: Return dictionary directly
        return {
            "state": system_health.state.name,
            "energy_level": system_health.parameters.get("energy", 1.0),
            "attention_capacity": system_health.parameters.get("attention_capacity", 1.0),
            "stress_level": system_health.parameters.get("stress", 0.0)
        }
        
    async def _get_goal_context(self) -> dict[str, Any]:
        """
        Get current goal context for goal-directed prompting.
        
        Returns:
            Dictionary with goal information
        """
        if not self.goal_manager:
            return {}
            
        active_goals = self.goal_manager.get_active_goals(sorted_by_priority=True)
        highest_priority_goal = self.goal_manager.get_highest_priority_active_goal()
        
        # RET504 Fix: Return dictionary directly
        return {
            "active_goals": [
                {
                    "description": goal.description,
                    "priority": goal.priority,
                    "completion_rate": goal.completion_rate
                }
                for goal in active_goals[:3]  # Include only top 3
            ],
            "current_focus": {
                "description": highest_priority_goal.description if highest_priority_goal else None,
                "priority": highest_priority_goal.priority if highest_priority_goal else None,
                "completion_rate": highest_priority_goal.completion_rate if highest_priority_goal else None
            } if highest_priority_goal else None
        }
        
    def get_providers(self) -> list[str]:
        """
        Get a list of available providers.
        
        Returns:
            List of configured provider names
        """
        return list(self.adapters.keys())
        
    def get_models(self, provider: str) -> list[str]:
        """
        Get available models for a specific provider.
        
        Args:
            provider: The provider name
            
        Returns:
            List of available model names
            
        Raises:
            ProviderNotFoundError: If the provider is not configured
        """
        if provider not in self.adapters:
            raise ProviderNotFoundError(f"Provider {provider} not configured")
            
        return self.adapters[provider].get_available_models()
        
    def get_metrics(self) -> dict[str, Any]:
        """
        Get usage metrics for LLM interactions.
        
        Returns:
            Dictionary with usage metrics
        """
        avg_response_time = (
            sum(self.request_times) / len(self.request_times)
            if self.request_times else 0
        )
        
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "average_response_time": avg_response_time,
            "providers": list(self.adapters.keys())
        }
        
    async def close(self):
        """Close all provider connections and clean up resources."""
        for adapter in self.adapters.values():
            await adapter.close()
