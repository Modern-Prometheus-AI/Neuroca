# NeuroCognitive Architecture (NCA) Usage Examples

This document provides practical examples of how to use the NeuroCognitive Architecture (NCA) system in various scenarios. These examples are designed to help you understand the capabilities of NCA and how to integrate it into your applications.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Memory System Examples](#memory-system-examples)
  - [Working Memory](#working-memory)
  - [Short-Term Memory](#short-term-memory)
  - [Long-Term Memory](#long-term-memory)
- [Health Dynamics Examples](#health-dynamics-examples)
- [Cognitive Function Examples](#cognitive-function-examples)
- [LLM Integration Examples](#llm-integration-examples)
- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Basic Setup

### Installation and Configuration

```python
# Install the NCA package
pip install neuroca

# Import the core components
from neuroca.core import NeuroCognitiveArchitecture
from neuroca.config import NCACoreConfig

# Create a basic configuration
config = NCACoreConfig(
    llm_provider="openai",
    api_key="your-api-key-here",
    memory_persistence_path="./nca_memory",
    log_level="INFO"
)

# Initialize the NCA system
nca = NeuroCognitiveArchitecture(config)
```

### Basic Interaction

```python
# Initialize a conversation
conversation_id = nca.create_conversation("general_assistant")

# Send a message and get a response
response = nca.process_message(
    conversation_id=conversation_id,
    message="What can you tell me about cognitive architectures?",
    user_id="user123"
)

print(response.content)
```

## Memory System Examples

### Working Memory

Working memory is designed for immediate, short-lived information processing.

```python
# Store information in working memory
nca.memory.working.store(
    conversation_id="conv123",
    content="The user is looking for information about neural networks",
    source="user_message",
    importance=0.8
)

# Retrieve recent items from working memory
recent_context = nca.memory.working.retrieve(
    conversation_id="conv123",
    limit=5
)

# Clear working memory when switching topics
nca.memory.working.clear(conversation_id="conv123")
```

### Short-Term Memory

Short-term memory retains information for the duration of a conversation or task.

```python
# Store user preferences in short-term memory
nca.memory.short_term.store(
    conversation_id="conv123",
    content={
        "preferred_language": "Python",
        "expertise_level": "intermediate",
        "interests": ["machine learning", "cognitive science"]
    },
    category="user_preferences"
)

# Retrieve user preferences
preferences = nca.memory.short_term.retrieve(
    conversation_id="conv123",
    category="user_preferences"
)

# Update existing memory
nca.memory.short_term.update(
    conversation_id="conv123",
    category="user_preferences",
    content={
        "preferred_language": "Python",
        "expertise_level": "advanced",  # Updated value
        "interests": ["machine learning", "cognitive science", "robotics"]  # Added interest
    }
)
```

### Long-Term Memory

Long-term memory persists across multiple conversations and sessions.

```python
# Store important information in long-term memory
nca.memory.long_term.store(
    user_id="user123",
    content="User has a background in neuroscience and is interested in computational models",
    category="user_background",
    importance=0.9
)

# Retrieve from long-term memory with semantic search
relevant_memories = nca.memory.long_term.semantic_search(
    user_id="user123",
    query="computational neuroscience models",
    limit=3
)

# Retrieve all memories in a category
all_background = nca.memory.long_term.retrieve_by_category(
    user_id="user123",
    category="user_background"
)
```

## Health Dynamics Examples

The health dynamics system models cognitive fatigue, attention, and other biological factors.

```python
# Check current health status
health_status = nca.health.get_status(conversation_id="conv123")
print(f"Attention level: {health_status.attention}")
print(f"Fatigue level: {health_status.fatigue}")

# Manually adjust health parameters (for testing)
nca.health.adjust(
    conversation_id="conv123",
    parameter="attention",
    value=0.9
)

# Reset health to default values
nca.health.reset(conversation_id="conv123")

# Enable automatic health dynamics
nca.health.enable_auto_dynamics(conversation_id="conv123")
```

## Cognitive Function Examples

NCA provides various cognitive functions that can be used independently or together.

### Reasoning

```python
# Perform step-by-step reasoning
reasoning_result = nca.cognition.reason(
    prompt="What would happen if we doubled the learning rate in a neural network?",
    conversation_id="conv123",
    steps=3  # Number of reasoning steps
)

print(reasoning_result.steps)  # List of reasoning steps
print(reasoning_result.conclusion)  # Final conclusion
```

### Planning

```python
# Generate a plan for a complex task
plan = nca.cognition.plan(
    goal="Build a recommendation system for an e-commerce website",
    constraints=["Must use Python", "Should be deployable on AWS", "Must handle 10,000 users"],
    conversation_id="conv123"
)

print(plan.steps)  # List of plan steps
print(plan.resources)  # Required resources
print(plan.timeline)  # Estimated timeline
```

### Reflection

```python
# Reflect on previous responses to improve future ones
reflection = nca.cognition.reflect(
    conversation_id="conv123",
    message_id="msg456",
    reflection_prompt="How could my previous response be improved?"
)

print(reflection.insights)
print(reflection.improvement_suggestions)
```

## LLM Integration Examples

NCA can integrate with various LLM providers.

### Switching LLM Providers

```python
# Switch to a different LLM provider
nca.integration.set_llm_provider(
    provider="anthropic",
    api_key="your-anthropic-api-key",
    model="claude-2"
)

# Use a specific model for a particular request
response = nca.process_message(
    conversation_id="conv123",
    message="Explain quantum computing",
    user_id="user123",
    llm_options={
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7
    }
)
```

### Custom Prompting

```python
# Create a custom prompt template
nca.integration.register_prompt_template(
    name="technical_explanation",
    template="Explain {topic} in technical terms, assuming the reader has background in {field}."
)

# Use the custom prompt
response = nca.integration.generate_from_template(
    template_name="technical_explanation",
    parameters={
        "topic": "neural networks",
        "field": "computer science"
    },
    conversation_id="conv123"
)
```

## Advanced Usage Patterns

### Conversation Management

```python
# List all active conversations
conversations = nca.list_conversations(user_id="user123")

# Get conversation history
history = nca.get_conversation_history(conversation_id="conv123", limit=10)

# Export conversation to JSON
exported_data = nca.export_conversation(conversation_id="conv123", format="json")

# Delete a conversation
nca.delete_conversation(conversation_id="conv123")
```

### Multi-Agent Collaboration

```python
# Create a multi-agent system
agent_system = nca.create_agent_system(
    agents=[
        {"role": "researcher", "expertise": ["data analysis", "literature review"]},
        {"role": "critic", "expertise": ["logical analysis", "fact checking"]},
        {"role": "writer", "expertise": ["content creation", "summarization"]}
    ],
    coordination_strategy="sequential"
)

# Process a complex query through the multi-agent system
result = agent_system.process(
    query="Research the latest advances in quantum computing and prepare a summary",
    conversation_id="conv123"
)

print(result.final_output)
print(result.agent_contributions)  # See what each agent contributed
```

## Troubleshooting Common Issues

### Memory Retrieval Issues

If you're experiencing issues with memory retrieval:

```python
# Debug memory retrieval
debug_info = nca.memory.debug_retrieval(
    conversation_id="conv123",
    query="user preferences",
    memory_type="short_term"
)

print(debug_info.search_parameters)
print(debug_info.matching_items)
print(debug_info.retrieval_score)
```

### Performance Optimization

```python
# Enable memory caching for better performance
nca.memory.enable_caching(max_size=1000)

# Optimize for low-latency responses
nca.set_optimization_profile("low_latency")

# Monitor resource usage
usage_stats = nca.get_resource_usage()
print(f"Memory usage: {usage_stats.memory_mb} MB")
print(f"Average response time: {usage_stats.avg_response_time} ms")
```

### Error Handling

```python
try:
    response = nca.process_message(
        conversation_id="invalid_id",
        message="Hello",
        user_id="user123"
    )
except Exception as e:
    if "conversation_id not found" in str(e):
        # Create a new conversation if the ID is invalid
        conversation_id = nca.create_conversation("general_assistant")
        response = nca.process_message(
            conversation_id=conversation_id,
            message="Hello",
            user_id="user123"
        )
    else:
        # Handle other types of errors
        print(f"Error: {e}")
        # Log the error
        nca.log_error(str(e), severity="high")
```

---

These examples demonstrate the core functionality of the NeuroCognitive Architecture. For more detailed information, please refer to the [API Reference](../api/reference.md) and [Conceptual Guide](../concepts/overview.md).

If you encounter any issues or have questions, please check the [Troubleshooting Guide](../troubleshooting.md) or open an issue on our [GitHub repository](https://github.com/neuroca/neuroca).