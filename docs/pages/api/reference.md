# API Reference

This document provides detailed reference information for the NeuroCognitive Architecture (NCA) API.

## Core APIs

### Memory System

* [Memory Manager API](#memory-manager-api)
* [Memory Tier API](#memory-tier-api)
* [Memory Backend API](#memory-backend-api)
* [Memory Item API](#memory-item-api)
* [Memory Search API](#memory-search-api)

### Health System

* [Health Monitor API](#health-monitor-api)
* [Health Component API](#health-component-api)
* [Health Registry API](#health-registry-api)
* [Health Metrics API](#health-metrics-api)

### Cognitive Control System

* [Attention Manager API](#attention-manager-api)
* [Goal Manager API](#goal-manager-api)
* [Decision Maker API](#decision-maker-api)
* [Planner API](#planner-api)
* [Metacognition API](#metacognition-api)

## Integration APIs

### LangChain Integration

* [Chain Integration API](#chain-integration-api)
* [Memory Integration API](#memory-integration-api)
* [Tool Integration API](#tool-integration-api)

### LLM Integration

* [LLM Connector API](#llm-connector-api)
* [Embedding API](#embedding-api)
* [Provider API](#provider-api)

## REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/memory/items` | GET | Retrieve memory items |
| `/api/v1/memory/items` | POST | Store a new memory item |
| `/api/v1/memory/items/{id}` | GET | Retrieve a specific memory item |
| `/api/v1/memory/items/{id}` | PUT | Update a memory item |
| `/api/v1/memory/items/{id}` | DELETE | Delete a memory item |
| `/api/v1/memory/search` | POST | Search memory |
| `/api/v1/health/status` | GET | Get system health status |
| `/api/v1/health/components` | GET | List health monitored components |
| `/api/v1/health/metrics` | GET | Get health metrics |
| `/api/v1/system/info` | GET | Get system information |

## GraphQL API

The GraphQL API provides a flexible interface for querying and mutating data in the NCA system. 

### Example Query

```graphql
query {
  memoryItems(tier: "working", limit: 5) {
    id
    content
    metadata {
      contentType
      createdAt
      importance
    }
    relationships {
      targetId
      relationshipType
      strength
    }
  }
  
  healthStatus {
    overallHealth
    components {
      name
      status
      metrics {
        name
        value
        unit
      }
    }
  }
}
```

### Example Mutation

```graphql
mutation {
  storeMemoryItem(
    input: {
      content: "This is a new memory item",
      tier: "working",
      metadata: {
        contentType: "text/plain",
        importance: 0.8
      }
    }
  ) {
    id
    status
  }
}
```

## Memory Manager API

The Memory Manager API provides methods for interacting with the NCA memory system.

```python
from neuroca.memory.manager import MemoryManager

# Create a memory manager
memory_manager = MemoryManager()

# Store an item in working memory
item_id = memory_manager.store_item(
    content="Important information",
    tier="working",
    metadata={"importance": 0.9, "content_type": "text/plain"}
)

# Retrieve an item
item = memory_manager.get_item(item_id)

# Search memory
results = memory_manager.search(query="important", tiers=["working", "episodic"])

# Delete an item
memory_manager.delete_item(item_id)
```

For more detailed documentation, refer to the [Memory System Architecture](../architecture/diagrams/memory-system/index.md).

## Health Monitor API

The Health Monitor API provides methods for monitoring and managing the health of the NCA system.

```python
from neuroca.core.health import HealthMonitor

# Create a health monitor
health_monitor = HealthMonitor()

# Get overall system health
health_status = health_monitor.get_status()

# Register a component for health monitoring
health_monitor.register_component(
    component_id="memory_manager",
    component_type="memory",
    thresholds={"memory_usage": 0.9, "error_rate": 0.01}
)

# Report a metric for a component
health_monitor.report_metric(
    component_id="memory_manager",
    metric_name="memory_usage",
    metric_value=0.75
)

# Get all metrics for a component
metrics = health_monitor.get_component_metrics("memory_manager")
```

For more detailed documentation, refer to the [Health System Architecture](../architecture/diagrams/health-system/index.md).

## LangChain Integration API

The LangChain Integration API provides methods for integrating NCA with the LangChain framework.

```python
from neuroca.integration.langchain.chains import create_cognitive_chain
from neuroca.integration.langchain.memory import MemoryFactory
from neuroca.integration.langchain.tools import get_all_tools

# Create an NCA-powered chain
chain = create_cognitive_chain(
    llm=your_llm,
    memory_manager=your_memory_manager,
    health_monitor=your_health_monitor
)

# Use NCA memory with LangChain
memory = MemoryFactory.create_memory(memory_type="working")

# Get NCA tools for LangChain agents
tools = get_all_tools()

# Run the chain
result = chain.run("Process this information")
```

For more detailed documentation, refer to the [LangChain Integration Architecture](../architecture/diagrams/integration/langchain.md).
