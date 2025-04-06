"""
Unit tests for the LLM Integration Manager module.

This module tests the LLMIntegrationManager class, which is the central component
of the LLM integration layer. It verifies that the manager correctly handles:
1. LLM provider management
2. Memory context integration
3. Health awareness
4. Goal-directed prompting
5. Response processing
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from neuroca.core.cognitive_control.goal_manager import GoalManager
from neuroca.core.health.dynamics import HealthState

# Corrected import: Use BaseAdapter instead of LLMAdapter
from neuroca.integration.adapters.base import LLMResponse
from neuroca.integration.exceptions import ProviderNotFoundError
from neuroca.integration.manager import LLMIntegrationManager
from neuroca.integration.models import (
    LLMRequest,  # LLMResponse is imported above now
    TokenUsage,
)
from neuroca.memory.manager import MemoryManager


class TestLLMIntegrationManager:
    """Test suite for the LLMIntegrationManager class."""

    @pytest.fixture()
    def mock_memory_manager(self):
        """Create a mock memory manager for testing."""
        manager = MagicMock(spec=MemoryManager)
        manager.store = AsyncMock()
        manager.retrieve = AsyncMock(return_value=[])
        return manager

    @pytest.fixture()
    def mock_health_manager(self):
        """Create a mock health manager for testing."""
        # Removed spec=HealthDynamicsManager to avoid potential spec-related issues
        manager = MagicMock() 
        health_state = MagicMock()
        health_state.state = HealthState.NORMAL
        health_state.parameters = {
            "energy": 0.8,
            "attention_capacity": 0.9,
            "stress": 0.1
        }
        manager.get_system_health.return_value = health_state
        return manager

    @pytest.fixture()
    def mock_goal_manager(self):
        """Create a mock goal manager for testing."""
        manager = MagicMock(spec=GoalManager)
        manager.get_active_goals.return_value = []
        manager.get_highest_priority_active_goal.return_value = None
        return manager

    @pytest.fixture()
    def mock_adapter(self):
        """Create a mock LLM adapter for testing."""
        adapter = MagicMock()
        adapter.execute = AsyncMock()
        adapter.close = AsyncMock()
        return adapter

    @pytest.fixture()
    def basic_config(self):
        """Create a basic configuration for testing."""
        return {
            "default_provider": "test_provider",
            "default_model": "test_model",
            "providers": {
                "test_provider": {
                    "api_key": "test_key",
                    "default_model": "test_model"
                },
                "other_provider": {
                    "api_key": "other_key",
                    "default_model": "other_model"
                }
            },
            "store_interactions": True,
            "memory_integration": True,
            "health_awareness": True,
            "goal_directed": True
        }

    @pytest.fixture()
    def llm_manager(self, basic_config, mock_memory_manager, mock_health_manager, 
                    mock_goal_manager, mock_adapter):
        """Create an LLMIntegrationManager instance for testing."""
        # Patch the adapter classes where they are potentially imported/used in manager.py
        # Assuming manager.py might import them directly or via adapters/__init__.py
        with patch('neuroca.integration.manager.OpenAIAdapter', new_callable=MagicMock, create=True), \
             patch('neuroca.integration.manager.AnthropicAdapter', new_callable=MagicMock, create=True), \
             patch('neuroca.integration.manager.VertexAIAdapter', new_callable=MagicMock, create=True), \
             patch('neuroca.integration.manager.OllamaAdapter', new_callable=MagicMock, create=True): 
            
            # Configure the manager to use our mock adapter for the configured providers
            manager = LLMIntegrationManager(
                config=basic_config,
                memory_manager=mock_memory_manager,
                health_manager=mock_health_manager,
                goal_manager=mock_goal_manager
            )
            
            # Replace the real adapters with our mock
            manager.adapters = {"test_provider": mock_adapter, "other_provider": mock_adapter}
            
            yield manager

    async def test_initialization(self, basic_config, mock_memory_manager, 
                                 mock_health_manager, mock_goal_manager):
        """Test that the manager initializes correctly."""
        # Patch the adapter classes where they are potentially imported/used in manager.py
        with patch('neuroca.integration.manager.OpenAIAdapter', new_callable=MagicMock, create=True), \
             patch('neuroca.integration.manager.AnthropicAdapter', new_callable=MagicMock, create=True), \
             patch('neuroca.integration.manager.VertexAIAdapter', new_callable=MagicMock, create=True), \
             patch('neuroca.integration.manager.OllamaAdapter', new_callable=MagicMock, create=True): 
            
            manager = LLMIntegrationManager(
                config=basic_config,
                memory_manager=mock_memory_manager,
                health_manager=mock_health_manager,
                goal_manager=mock_goal_manager
            )
            
            # Check default values
            assert manager.default_provider == "test_provider"
            assert manager.default_model == "test_model"
            assert manager.memory_manager == mock_memory_manager
            assert manager.health_manager == mock_health_manager
            assert manager.goal_manager == mock_goal_manager

    async def test_query_basic(self, llm_manager, mock_adapter):
        """Test basic query functionality."""
        # Configure mock response
        mock_response = LLMResponse(
            provider="test_provider",
            model="test_model",
            content="Test response",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            elapsed_time=0.5
        )
        mock_adapter.execute.return_value = mock_response
        
        # Execute query
        response = await llm_manager.query("Test prompt")
        
        # Verify correct adapter was called with correct parameters
        mock_adapter.execute.assert_called_once()
        request = mock_adapter.execute.call_args[0][0]
        assert request.provider == "test_provider"
        assert request.model == "test_model"
        assert "Test prompt" in request.prompt
        
        # Verify response was processed correctly
        assert response == mock_response

    async def test_query_with_provider_and_model(self, llm_manager, mock_adapter):
        """Test query with specific provider and model."""
        # Configure mock response
        mock_response = LLMResponse(
            provider="other_provider",
            model="other_model",
            content="Test response",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            elapsed_time=0.5
        )
        mock_adapter.execute.return_value = mock_response
        
        # Execute query
        await llm_manager.query(
            prompt="Test prompt",
            provider="other_provider",
            model="other_model"
        )
        
        # Verify correct adapter was called with correct parameters
        mock_adapter.execute.assert_called_once()
        request = mock_adapter.execute.call_args[0][0]
        assert request.provider == "other_provider"
        assert request.model == "other_model"
        assert "Test prompt" in request.prompt

    async def test_query_with_memory_context(self, llm_manager, mock_adapter, mock_memory_manager):
        """Test query with memory context integration."""
        # Configure mock memory retrieval
        memory_results = [
            MagicMock(content="Memory 1", relevance=0.9),
            MagicMock(content="Memory 2", relevance=0.8)
        ]
        mock_memory_manager.retrieve.side_effect = [
            memory_results,  # working memory
            [],              # episodic memory
            []               # semantic memory
        ]
        
        # Configure mock response
        mock_response = LLMResponse(
            provider="test_provider",
            model="test_model",
            content="Test response",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            elapsed_time=0.5
        )
        mock_adapter.execute.return_value = mock_response
        
        # Execute query
        response = await llm_manager.query("Test prompt", memory_context=True)
        
        # Verify memory retrieval was called
        assert mock_memory_manager.retrieve.call_count == 3
        
        # Verify prompt includes memory information
        request = mock_adapter.execute.call_args[0][0]
        assert "Test prompt" in request.prompt
        
        # Verify response was processed correctly
        assert response == mock_response

    async def test_query_with_health_awareness(self, llm_manager, mock_adapter, mock_health_manager):
        """Test query with health state awareness."""
        # Configure mock health state
        health_state = MagicMock()
        health_state.state = HealthState.STRESSED
        health_state.parameters = {
            "energy": 0.5,
            "attention_capacity": 0.6,
            "stress": 0.7
        }
        mock_health_manager.get_system_health.return_value = health_state
        
        # Configure mock response
        mock_response = LLMResponse(
            provider="test_provider",
            model="test_model",
            content="Test response",
            metadata={},
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            elapsed_time=0.5
        )
        mock_adapter.execute.return_value = mock_response
        
        # Execute query
        response = await llm_manager.query("Test prompt", health_aware=True)
        
        # Verify health state was incorporated
        assert mock_health_manager.get_system_health.called
        
        # Verify response was processed with health info
        assert "health_state" in response.metadata
        assert response.metadata["health_state"] == "STRESSED"
        assert "caution_note" in response.metadata

    async def test_query_with_goal_context(self, llm_manager, mock_adapter, mock_goal_manager):
        """Test query with goal-directed context."""
        # Configure mock goals
        mock_goal = MagicMock()
        mock_goal.description = "Test goal"
        mock_goal.priority = 0.9
        mock_goal.completion_rate = 0.5
        
        mock_goal_manager.get_active_goals.return_value = [mock_goal]
        mock_goal_manager.get_highest_priority_active_goal.return_value = mock_goal
        
        # Configure mock response
        mock_response = LLMResponse(
            provider="test_provider",
            model="test_model",
            content="Test response",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            elapsed_time=0.5
        )
        mock_adapter.execute.return_value = mock_response
        
        # Execute query
        await llm_manager.query("Test prompt", goal_directed=True)
        
        # Verify goal information was incorporated
        assert mock_goal_manager.get_active_goals.called
        assert mock_goal_manager.get_highest_priority_active_goal.called
        
        # Verify prompt includes goal information
        request = mock_adapter.execute.call_args[0][0]
        assert "Test prompt" in request.prompt

    async def test_query_provider_not_found(self, llm_manager):
        """Test query with non-existent provider."""
        with pytest.raises(ProviderNotFoundError):
            await llm_manager.query("Test prompt", provider="non_existent_provider")

    async def test_query_with_additional_params(self, llm_manager, mock_adapter):
        """Test query with additional parameters."""
        # Configure mock response
        mock_response = LLMResponse(
            provider="test_provider",
            model="test_model",
            content="Test response",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            elapsed_time=0.5
        )
        mock_adapter.execute.return_value = mock_response
        
        # Execute query with additional parameters
        await llm_manager.query(
            prompt="Test prompt",
            temperature=0.7,
            max_tokens=100,
            additional_context={"test_key": "test_value"}
        )
        
        # Verify parameters were passed correctly
        request = mock_adapter.execute.call_args[0][0]
        assert request.temperature == 0.7
        assert request.max_tokens == 100

    async def test_get_providers(self, llm_manager):
        """Test getting available providers."""
        providers = llm_manager.get_providers()
        assert "test_provider" in providers
        assert "other_provider" in providers
        assert len(providers) == 2

    async def test_store_interactions(self, llm_manager, mock_adapter, mock_memory_manager):
        """Test that interactions are stored in memory."""
        # Configure mock response
        mock_response = LLMResponse(
            provider="test_provider",
            model="test_model",
            content="Test response",
            request=LLMRequest(
                provider="test_provider",
                model="test_model",
                prompt="Test prompt"
            ),
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            ),
            elapsed_time=0.5
        )
        mock_adapter.execute.return_value = mock_response
        
        # Execute query
        await llm_manager.query("Test prompt")
        
        # Verify interaction was stored
        mock_memory_manager.store.assert_called_once()
        stored_data = mock_memory_manager.store.call_args[1]["content"]
        assert stored_data["type"] == "llm_interaction"
        assert stored_data["prompt"] == mock_response.request.prompt
        assert stored_data["response"] == mock_response.content
        assert stored_data["model"] == mock_response.model
        assert stored_data["provider"] == mock_response.provider

    async def test_close(self, llm_manager, mock_adapter):
        """Test closing the manager."""
        await llm_manager.close()
        assert mock_adapter.close.call_count == 2  # Two adapters

    async def test_get_models(self, llm_manager, mock_adapter):
        """Test getting models for a provider."""
        mock_adapter.get_available_models.return_value = ["model1", "model2"]
        models = llm_manager.get_models("test_provider")
        assert "model1" in models
        assert "model2" in models
        assert len(models) == 2
        
        # Test with non-existent provider
        with pytest.raises(ProviderNotFoundError):
            llm_manager.get_models("non_existent_provider")

    async def test_get_metrics(self, llm_manager):
        """Test getting usage metrics."""
        # Set some metrics
        llm_manager.total_requests = 10
        llm_manager.total_tokens = 1000
        llm_manager.total_cost = 0.5
        llm_manager.request_times = [0.1, 0.2, 0.3]
        
        metrics = llm_manager.get_metrics()
        assert metrics["total_requests"] == 10
        assert metrics["total_tokens"] == 1000
        assert metrics["total_cost"] == 0.5
        assert metrics["average_response_time"] == 0.2
        assert "test_provider" in metrics["providers"]
        assert "other_provider" in metrics["providers"]
