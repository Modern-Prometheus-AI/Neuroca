# NeuroCognitive Architecture (NCA) API Examples

This document provides practical examples for using the NeuroCognitive Architecture API. These examples demonstrate how to interact with the various components of the NCA system, including memory management, cognitive processes, health dynamics, and LLM integration.

## Table of Contents

- [Authentication](#authentication)
- [Basic Usage](#basic-usage)
- [Memory System Examples](#memory-system-examples)
  - [Working Memory](#working-memory)
  - [Short-Term Memory](#short-term-memory)
  - [Long-Term Memory](#long-term-memory)
- [Cognitive Process Examples](#cognitive-process-examples)
- [Health Dynamics Examples](#health-dynamics-examples)
- [LLM Integration Examples](#llm-integration-examples)
- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Error Handling](#error-handling)
- [Batch Operations](#batch-operations)

## Authentication

Before using the API, you need to authenticate. Here's how to obtain and use an API token:

```python
import requests
import json

# Get API token
response = requests.post(
    "https://api.neuroca.ai/v1/auth/token",
    json={
        "client_id": "your_client_id",
        "client_secret": "your_client_secret"
    }
)

if response.status_code == 200:
    token = response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
else:
    print(f"Authentication failed: {response.text}")
```

## Basic Usage

### Creating a New NCA Instance

```python
# Create a new NCA instance
response = requests.post(
    "https://api.neuroca.ai/v1/instances",
    headers=headers,
    json={
        "name": "My NCA Instance",
        "description": "A test instance for exploring NCA capabilities",
        "config": {
            "memory_capacity": {
                "working": 7,  # Miller's number for working memory capacity
                "short_term": 100,
                "long_term": 10000
            },
            "health_dynamics": {
                "enabled": True,
                "initial_values": {
                    "energy": 100,
                    "stress": 0,
                    "fatigue": 0
                }
            }
        }
    }
)

instance_id = response.json()["instance_id"]
print(f"Created NCA instance with ID: {instance_id}")
```

### Basic Interaction with the NCA

```python
# Send a prompt to the NCA instance
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/interact",
    headers=headers,
    json={
        "prompt": "What is the capital of France?",
        "context": "We're discussing European geography.",
        "options": {
            "use_working_memory": True,
            "use_short_term_memory": True,
            "use_long_term_memory": True
        }
    }
)

print(json.dumps(response.json(), indent=2))
```

## Memory System Examples

### Working Memory

Working memory is used for immediate processing and has limited capacity.

```python
# Store information in working memory
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/working",
    headers=headers,
    json={
        "content": "The meeting is scheduled for 3 PM tomorrow.",
        "importance": 0.8,  # 0-1 scale
        "metadata": {
            "source": "calendar",
            "category": "appointment"
        }
    }
)

memory_id = response.json()["memory_id"]

# Retrieve from working memory
response = requests.get(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/working/{memory_id}",
    headers=headers
)

print(json.dumps(response.json(), indent=2))

# List all items in working memory
response = requests.get(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/working",
    headers=headers
)

print(f"Working memory items: {len(response.json()['items'])}")
```

### Short-Term Memory

Short-term memory has a larger capacity but decays over time without reinforcement.

```python
# Store information in short-term memory
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/short-term",
    headers=headers,
    json={
        "content": "The client mentioned they prefer blue for the website theme.",
        "importance": 0.6,
        "retention_period": 86400,  # 24 hours in seconds
        "metadata": {
            "source": "client_meeting",
            "category": "preferences"
        }
    }
)

memory_id = response.json()["memory_id"]

# Reinforce a memory to prevent decay
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/short-term/{memory_id}/reinforce",
    headers=headers,
    json={
        "strength": 0.5  # 0-1 scale
    }
)

# Search short-term memory
response = requests.get(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/short-term/search",
    headers=headers,
    params={
        "query": "website theme",
        "limit": 5
    }
)

print(json.dumps(response.json(), indent=2))
```

### Long-Term Memory

Long-term memory is persistent and has the largest capacity.

```python
# Store information in long-term memory
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/long-term",
    headers=headers,
    json={
        "content": "The company was founded in 2010 by Jane Smith and has grown to 500 employees.",
        "importance": 0.9,
        "metadata": {
            "source": "company_history",
            "category": "facts",
            "tags": ["founding", "history", "growth"]
        }
    }
)

memory_id = response.json()["memory_id"]

# Retrieve from long-term memory with semantic search
response = requests.get(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/long-term/semantic-search",
    headers=headers,
    params={
        "query": "When was the company founded and by whom?",
        "limit": 3
    }
)

print(json.dumps(response.json(), indent=2))

# Transfer from short-term to long-term memory
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/transfer",
    headers=headers,
    json={
        "source_type": "short_term",
        "source_id": "short_term_memory_id",
        "target_type": "long_term",
        "importance_boost": 0.2
    }
)
```

## Cognitive Process Examples

```python
# Initiate a reasoning process
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/cognitive/reason",
    headers=headers,
    json={
        "question": "Should we expand our business to international markets?",
        "context": "Our domestic market share is 45%, and we've seen 20% growth annually for 3 years.",
        "options": {
            "depth": "deep",  # shallow, medium, deep
            "use_memory": True
        }
    }
)

reasoning_id = response.json()["reasoning_id"]

# Get reasoning results
response = requests.get(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/cognitive/reason/{reasoning_id}",
    headers=headers
)

print(json.dumps(response.json(), indent=2))

# Perform pattern recognition
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/cognitive/pattern",
    headers=headers,
    json={
        "data": [
            {"date": "2023-01-01", "sales": 1200},
            {"date": "2023-01-02", "sales": 1250},
            {"date": "2023-01-03", "sales": 1180},
            # ... more data points
        ],
        "pattern_type": "trend",
        "options": {
            "sensitivity": 0.7
        }
    }
)

print(json.dumps(response.json(), indent=2))
```

## Health Dynamics Examples

```python
# Get current health status
response = requests.get(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/health",
    headers=headers
)

print(json.dumps(response.json(), indent=2))

# Update energy level
response = requests.patch(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/health",
    headers=headers,
    json={
        "energy": 80  # Decrease energy to 80%
    }
)

# Simulate rest to recover energy and reduce fatigue
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/health/rest",
    headers=headers,
    json={
        "duration": 3600  # Rest for 1 hour (in seconds)
    }
)

# Get health history
response = requests.get(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/health/history",
    headers=headers,
    params={
        "from": "2023-01-01T00:00:00Z",
        "to": "2023-01-07T23:59:59Z",
        "interval": "day"
    }
)

print(json.dumps(response.json(), indent=2))
```

## LLM Integration Examples

```python
# Configure LLM integration
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/llm/configure",
    headers=headers,
    json={
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "your_openai_api_key",
        "options": {
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }
)

# Generate content with LLM through NCA
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/llm/generate",
    headers=headers,
    json={
        "prompt": "Write a summary of the quarterly financial results.",
        "context": "Revenue increased by 15%, but expenses grew by 20%.",
        "options": {
            "use_memory": True,
            "format": "markdown"
        }
    }
)

print(json.dumps(response.json(), indent=2))

# Analyze sentiment with LLM
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/llm/analyze",
    headers=headers,
    json={
        "text": "I'm extremely disappointed with the customer service I received today.",
        "analysis_type": "sentiment"
    }
)

print(json.dumps(response.json(), indent=2))
```

## Advanced Usage Patterns

### Chaining Operations

```python
# Example of chaining operations: store memory, reason about it, then generate content

# 1. Store information
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/short-term",
    headers=headers,
    json={
        "content": "Sales increased by 15% in Q1, 12% in Q2, and 8% in Q3, but decreased by 3% in Q4.",
        "importance": 0.8,
        "metadata": {
            "source": "financial_report",
            "year": "2023"
        }
    }
)

# 2. Reason about the information
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/cognitive/reason",
    headers=headers,
    json={
        "question": "What might be causing the sales slowdown throughout the year?",
        "options": {
            "use_memory": True,
            "depth": "deep"
        }
    }
)

reasoning_result = response.json()["result"]

# 3. Generate a report based on the reasoning
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/llm/generate",
    headers=headers,
    json={
        "prompt": "Write a brief report on our sales trend and potential causes for the slowdown.",
        "context": reasoning_result,
        "options": {
            "use_memory": True,
            "format": "markdown"
        }
    }
)

final_report = response.json()["content"]
print(final_report)
```

### Batch Processing

```python
# Process multiple items in a batch
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/batch",
    headers=headers,
    json={
        "items": [
            {
                "content": "Client meeting scheduled for Monday at 10 AM.",
                "memory_type": "short_term",
                "importance": 0.7
            },
            {
                "content": "Project deadline is Friday, March 15th.",
                "memory_type": "working",
                "importance": 0.9
            },
            {
                "content": "The new product launch generated $1.2M in first-month sales.",
                "memory_type": "long_term",
                "importance": 0.8
            }
        ]
    }
)

print(json.dumps(response.json(), indent=2))
```

## Error Handling

```python
# Example of handling API errors
try:
    response = requests.get(
        f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/working/non_existent_id",
        headers=headers
    )
    
    if response.status_code != 200:
        error_data = response.json()
        print(f"Error: {error_data['error']}")
        print(f"Message: {error_data['message']}")
        print(f"Code: {error_data['code']}")
        
        # Handle specific error codes
        if error_data['code'] == 'memory_not_found':
            print("The requested memory item doesn't exist.")
        elif error_data['code'] == 'memory_capacity_exceeded':
            print("Memory capacity has been reached. Consider clearing some items.")
        
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
```

## Batch Operations

```python
# Batch retrieve multiple memory items
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/batch-retrieve",
    headers=headers,
    json={
        "ids": [
            {"type": "working", "id": "working_memory_id_1"},
            {"type": "short_term", "id": "short_term_memory_id_1"},
            {"type": "long_term", "id": "long_term_memory_id_1"}
        ]
    }
)

print(json.dumps(response.json(), indent=2))

# Batch delete multiple memory items
response = requests.post(
    f"https://api.neuroca.ai/v1/instances/{instance_id}/memory/batch-delete",
    headers=headers,
    json={
        "ids": [
            {"type": "working", "id": "working_memory_id_2"},
            {"type": "short_term", "id": "short_term_memory_id_2"}
        ]
    }
)

print(f"Deleted {response.json()['deleted_count']} memory items")
```

## Conclusion

These examples demonstrate the core functionality of the NeuroCognitive Architecture API. For more detailed information about specific endpoints, parameters, and response formats, please refer to the [API Reference](./reference.md).

For support, please contact us at support@neuroca.ai or visit our [developer forum](https://forum.neuroca.ai).