# Getting Started with NeuroCognitive Architecture (NCA)

Welcome to the NeuroCognitive Architecture (NCA) for Large Language Models. This guide will help you set up your environment, understand the core concepts, and start building with NCA.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## Overview

NeuroCognitive Architecture (NCA) is a biologically-inspired framework that enhances Large Language Models with a three-tiered memory system, health dynamics, and cognitive processes that mimic human brain functions. NCA enables more contextually aware, adaptive, and human-like AI systems.

### Key Features

- **Three-Tiered Memory System**: Working memory, episodic memory, and semantic memory
- **Health Dynamics**: Simulated fatigue, attention, and cognitive load
- **Biological Inspiration**: Neural activation patterns and cognitive processes
- **Seamless LLM Integration**: Works with popular LLM frameworks

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9 or higher
- pip or poetry (recommended)
- Docker and Docker Compose (for containerized deployment)
- Git

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-organization/neuroca.git
cd neuroca

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/your-organization/neuroca.git
cd neuroca

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Using Docker

```bash
# Clone the repository
git clone https://github.com/your-organization/neuroca.git
cd neuroca

# Build and start the containers
docker-compose up -d
```

## Quick Start

Here's a minimal example to get you started with NCA:

```python
from neuroca import NCA
from neuroca.memory import WorkingMemory, EpisodicMemory, SemanticMemory
from neuroca.integration import LLMConnector

# Initialize the NCA with default settings
nca = NCA()

# Connect to your preferred LLM
llm_connector = LLMConnector(provider="openai", model="gpt-4")
nca.set_llm(llm_connector)

# Process input through the cognitive architecture
response = nca.process("Tell me about the solar system")

print(response)
```

## Core Concepts

### Memory System

NCA implements a three-tiered memory system inspired by human cognition:

1. **Working Memory**: Short-term, limited capacity storage for active processing
   ```python
   from neuroca.memory import WorkingMemory
   
   # Create a working memory with custom capacity
   wm = WorkingMemory(capacity=7)  # Miller's Law: 7±2 items
   
   # Add items to working memory
   wm.add("current_topic", "astronomy")
   
   # Retrieve items
   current_topic = wm.get("current_topic")
   ```

2. **Episodic Memory**: Stores experiences and events with temporal context
   ```python
   from neuroca.memory import EpisodicMemory
   
   # Create episodic memory
   em = EpisodicMemory()
   
   # Store an episode
   em.store(
       content="User asked about the solar system",
       context={"timestamp": "2023-10-15T14:30:00", "location": "chat_session_1"}
   )
   
   # Retrieve relevant episodes
   solar_system_episodes = em.retrieve("solar system", limit=5)
   ```

3. **Semantic Memory**: Long-term storage for facts, concepts, and knowledge
   ```python
   from neuroca.memory import SemanticMemory
   
   # Create semantic memory
   sm = SemanticMemory()
   
   # Store knowledge
   sm.store("The solar system has eight planets")
   
   # Query knowledge
   planets_info = sm.query("How many planets in the solar system?")
   ```

### Health Dynamics

NCA models cognitive health factors that affect performance:

```python
from neuroca.core.health import HealthSystem

# Initialize health system
health = HealthSystem()

# Update fatigue after intensive processing
health.update_fatigue(0.1)  # Increase fatigue by 10%

# Check current attention level
attention_level = health.get_attention()

# Apply cognitive rest
health.rest(duration=5)  # Rest for 5 time units
```

## Configuration

NCA can be configured through YAML files or environment variables:

### YAML Configuration

Create a `config.yaml` file:

```yaml
memory:
  working:
    capacity: 10
    decay_rate: 0.2
  episodic:
    max_episodes: 1000
    retrieval_strategy: "relevance"
  semantic:
    embedding_model: "text-embedding-ada-002"
    similarity_threshold: 0.85

health:
  fatigue:
    recovery_rate: 0.05
    max_level: 1.0
  attention:
    base_level: 0.8
    fluctuation_range: 0.2

llm:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 1000
```

Load the configuration:

```python
from neuroca import NCA
from neuroca.config import load_config

config = load_config("path/to/config.yaml")
nca = NCA(config=config)
```

### Environment Variables

You can also configure NCA using environment variables:

```bash
# Memory settings
export NEUROCA_MEMORY_WORKING_CAPACITY=10
export NEUROCA_MEMORY_EPISODIC_MAX_EPISODES=1000
export NEUROCA_MEMORY_SEMANTIC_SIMILARITY_THRESHOLD=0.85

# Health settings
export NEUROCA_HEALTH_FATIGUE_RECOVERY_RATE=0.05
export NEUROCA_HEALTH_ATTENTION_BASE_LEVEL=0.8

# LLM settings
export NEUROCA_LLM_PROVIDER=openai
export NEUROCA_LLM_MODEL=gpt-4
```

## Examples

### Conversation with Memory

```python
from neuroca import NCA

nca = NCA()

# First interaction
response1 = nca.process("My name is Alice")
print(response1)  # Acknowledges the name

# Second interaction (demonstrates memory)
response2 = nca.process("What's my name?")
print(response2)  # Should recall "Alice"

# Complex reasoning with memory
response3 = nca.process("I like astronomy. What topics might interest me?")
print(response3)  # Uses semantic memory to suggest astronomy-related topics
```

### Cognitive Load Simulation

```python
from neuroca import NCA
from neuroca.core.health import HealthSystem

nca = NCA()
health_system = nca.health_system

# Monitor health during complex processing
initial_attention = health_system.get_attention()
print(f"Initial attention: {initial_attention}")

# Process a complex query
response = nca.process("Explain quantum mechanics in detail")

# Check health after processing
post_attention = health_system.get_attention()
fatigue = health_system.get_fatigue()
print(f"Attention after processing: {post_attention}")
print(f"Fatigue level: {fatigue}")

# Apply rest
health_system.rest(duration=10)
print(f"Attention after rest: {health_system.get_attention()}")
```

## Troubleshooting

### Common Issues

#### Memory Retrieval Problems

If memory retrieval isn't working as expected:

1. Check memory capacity settings
2. Verify embedding models are properly loaded
3. Adjust similarity thresholds in configuration

```python
# Debug memory retrieval
from neuroca.utils.debugging import debug_memory_retrieval

debug_memory_retrieval(nca.episodic_memory, query="solar system")
```

#### Performance Issues

If you're experiencing slow performance:

1. Reduce memory capacity or retention
2. Use a lighter LLM model
3. Adjust health dynamics parameters

```python
# Performance optimization
nca.config.memory.working.capacity = 5  # Reduce working memory load
nca.config.llm.model = "gpt-3.5-turbo"  # Use a faster model
```

#### API Connection Errors

For LLM integration issues:

1. Verify API keys are correctly set
2. Check network connectivity
3. Ensure rate limits haven't been exceeded

```python
# Test LLM connection
from neuroca.integration import test_llm_connection

test_llm_connection(provider="openai", model="gpt-4")
```

## Next Steps

Now that you're familiar with NCA basics, you can:

1. Explore the [API Reference](../api/reference.md) for detailed documentation
2. Check out [Advanced Usage](./advanced-usage.md) for complex scenarios
3. Learn about [Custom Extensions](./extensions.md) to add your own components
4. Join our [Community](https://github.com/your-organization/neuroca/discussions) to share your experiences

For any questions or support, please [open an issue](https://github.com/your-organization/neuroca/issues) on our GitHub repository.

Happy building with NeuroCognitive Architecture!