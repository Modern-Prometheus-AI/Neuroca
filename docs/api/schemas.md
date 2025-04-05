# API Schemas

This document defines the data schemas used throughout the NeuroCognitive Architecture (NCA) API. These schemas represent the structure of data objects exchanged between clients and the NCA system, ensuring consistent data validation and documentation.

## Table of Contents

- [Common Schemas](#common-schemas)
- [Memory Schemas](#memory-schemas)
  - [Working Memory](#working-memory)
  - [Short-Term Memory](#short-term-memory)
  - [Long-Term Memory](#long-term-memory)
- [Health Schemas](#health-schemas)
- [Cognitive Function Schemas](#cognitive-function-schemas)
- [System Schemas](#system-schemas)
- [Integration Schemas](#integration-schemas)

## Common Schemas

### BaseResponse

Base schema for all API responses.

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "error"],
      "description": "Response status"
    },
    "message": {
      "type": "string",
      "description": "Human-readable message"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of the response"
    }
  },
  "required": ["status", "timestamp"]
}
```

### ErrorResponse

Schema for error responses.

```json
{
  "allOf": [
    { "$ref": "#/components/schemas/BaseResponse" },
    {
      "type": "object",
      "properties": {
        "error": {
          "type": "object",
          "properties": {
            "code": {
              "type": "string",
              "description": "Error code"
            },
            "details": {
              "type": "object",
              "description": "Additional error details"
            }
          },
          "required": ["code"]
        }
      },
      "required": ["error"]
    }
  ]
}
```

### PaginationParams

Common pagination parameters.

```json
{
  "type": "object",
  "properties": {
    "page": {
      "type": "integer",
      "minimum": 1,
      "default": 1,
      "description": "Page number"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20,
      "description": "Number of items per page"
    }
  }
}
```

### PaginatedResponse

Schema for paginated responses.

```json
{
  "allOf": [
    { "$ref": "#/components/schemas/BaseResponse" },
    {
      "type": "object",
      "properties": {
        "pagination": {
          "type": "object",
          "properties": {
            "total": {
              "type": "integer",
              "description": "Total number of items"
            },
            "pages": {
              "type": "integer",
              "description": "Total number of pages"
            },
            "page": {
              "type": "integer",
              "description": "Current page number"
            },
            "limit": {
              "type": "integer",
              "description": "Items per page"
            },
            "hasNext": {
              "type": "boolean",
              "description": "Whether there is a next page"
            },
            "hasPrev": {
              "type": "boolean",
              "description": "Whether there is a previous page"
            }
          },
          "required": ["total", "pages", "page", "limit", "hasNext", "hasPrev"]
        },
        "data": {
          "type": "array",
          "description": "Array of data items"
        }
      },
      "required": ["pagination", "data"]
    }
  ]
}
```

## Memory Schemas

### MemoryItem

Base schema for all memory items.

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for the memory item"
    },
    "content": {
      "type": "string",
      "description": "The content of the memory"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "When the memory was created"
    },
    "last_accessed": {
      "type": "string",
      "format": "date-time",
      "description": "When the memory was last accessed"
    },
    "metadata": {
      "type": "object",
      "description": "Additional metadata about the memory"
    }
  },
  "required": ["id", "content", "created_at"]
}
```

### Working Memory

#### WorkingMemoryItem

```json
{
  "allOf": [
    { "$ref": "#/components/schemas/MemoryItem" },
    {
      "type": "object",
      "properties": {
        "priority": {
          "type": "integer",
          "minimum": 1,
          "maximum": 10,
          "description": "Priority level of the item in working memory"
        },
        "expiration": {
          "type": "string",
          "format": "date-time",
          "description": "When this item will expire from working memory"
        }
      },
      "required": ["priority"]
    }
  ]
}
```

#### WorkingMemoryState

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/WorkingMemoryItem" },
      "description": "Current items in working memory"
    },
    "capacity": {
      "type": "integer",
      "description": "Maximum capacity of working memory"
    },
    "current_load": {
      "type": "integer",
      "description": "Current number of items in working memory"
    },
    "load_percentage": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 100,
      "description": "Percentage of working memory capacity in use"
    }
  },
  "required": ["items", "capacity", "current_load", "load_percentage"]
}
```

### Short-Term Memory

#### ShortTermMemoryItem

```json
{
  "allOf": [
    { "$ref": "#/components/schemas/MemoryItem" },
    {
      "type": "object",
      "properties": {
        "importance": {
          "type": "number",
          "format": "float",
          "minimum": 0,
          "maximum": 1,
          "description": "Importance score for consolidation decisions"
        },
        "access_count": {
          "type": "integer",
          "minimum": 0,
          "description": "Number of times this memory has been accessed"
        },
        "context": {
          "type": "string",
          "description": "Context in which this memory was formed"
        }
      },
      "required": ["importance"]
    }
  ]
}
```

#### ShortTermMemoryState

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/ShortTermMemoryItem" },
      "description": "Current items in short-term memory"
    },
    "capacity": {
      "type": "integer",
      "description": "Maximum capacity of short-term memory"
    },
    "current_load": {
      "type": "integer",
      "description": "Current number of items in short-term memory"
    },
    "consolidation_queue": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/ShortTermMemoryItem" },
      "description": "Items queued for consolidation to long-term memory"
    }
  },
  "required": ["items", "capacity", "current_load"]
}
```

### Long-Term Memory

#### LongTermMemoryItem

```json
{
  "allOf": [
    { "$ref": "#/components/schemas/MemoryItem" },
    {
      "type": "object",
      "properties": {
        "strength": {
          "type": "number",
          "format": "float",
          "minimum": 0,
          "maximum": 1,
          "description": "Strength of the memory (affects recall probability)"
        },
        "category": {
          "type": "string",
          "description": "Category or type of memory"
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Tags associated with this memory for retrieval"
        },
        "connections": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uuid"
          },
          "description": "IDs of related memory items"
        },
        "embedding": {
          "type": "array",
          "items": {
            "type": "number",
            "format": "float"
          },
          "description": "Vector embedding of the memory content"
        }
      },
      "required": ["strength", "category"]
    }
  ]
}
```

#### LongTermMemoryQuery

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Natural language query for semantic search"
    },
    "category": {
      "type": "string",
      "description": "Optional category filter"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Optional tags to filter by"
    },
    "min_strength": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 1,
      "description": "Minimum memory strength to include in results"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 10,
      "description": "Maximum number of results to return"
    }
  },
  "required": ["query"]
}
```

## Health Schemas

### HealthStatus

```json
{
  "type": "object",
  "properties": {
    "energy": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 100,
      "description": "Current energy level"
    },
    "fatigue": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 100,
      "description": "Current fatigue level"
    },
    "stress": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 100,
      "description": "Current stress level"
    },
    "cognitive_load": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 100,
      "description": "Current cognitive load"
    },
    "status": {
      "type": "string",
      "enum": ["optimal", "normal", "degraded", "critical"],
      "description": "Overall health status"
    }
  },
  "required": ["energy", "fatigue", "stress", "cognitive_load", "status"]
}
```

### HealthEvent

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for the health event"
    },
    "type": {
      "type": "string",
      "enum": ["energy_change", "fatigue_change", "stress_change", "cognitive_load_change", "status_change"],
      "description": "Type of health event"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "When the event occurred"
    },
    "previous_value": {
      "type": "number",
      "format": "float",
      "description": "Previous value before the change"
    },
    "new_value": {
      "type": "number",
      "format": "float",
      "description": "New value after the change"
    },
    "cause": {
      "type": "string",
      "description": "What caused this health event"
    }
  },
  "required": ["id", "type", "timestamp", "previous_value", "new_value"]
}
```

## Cognitive Function Schemas

### AttentionState

```json
{
  "type": "object",
  "properties": {
    "focus_target": {
      "type": "string",
      "description": "Current focus of attention"
    },
    "focus_level": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 1,
      "description": "Level of focus (0-1)"
    },
    "distractions": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Current distractions"
    }
  },
  "required": ["focus_target", "focus_level"]
}
```

### ReasoningTask

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for the reasoning task"
    },
    "problem": {
      "type": "string",
      "description": "Problem statement"
    },
    "context": {
      "type": "string",
      "description": "Context information"
    },
    "reasoning_type": {
      "type": "string",
      "enum": ["deductive", "inductive", "abductive", "analogical"],
      "description": "Type of reasoning required"
    },
    "steps": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Reasoning steps"
    },
    "conclusion": {
      "type": "string",
      "description": "Reasoning conclusion"
    }
  },
  "required": ["id", "problem", "reasoning_type"]
}
```

## System Schemas

### SystemStatus

```json
{
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "description": "NCA system version"
    },
    "uptime": {
      "type": "integer",
      "description": "System uptime in seconds"
    },
    "health": {
      "$ref": "#/components/schemas/HealthStatus"
    },
    "memory_stats": {
      "type": "object",
      "properties": {
        "working_memory_usage": {
          "type": "number",
          "format": "float",
          "description": "Working memory usage percentage"
        },
        "short_term_memory_usage": {
          "type": "number",
          "format": "float",
          "description": "Short-term memory usage percentage"
        },
        "long_term_memory_count": {
          "type": "integer",
          "description": "Number of items in long-term memory"
        }
      }
    },
    "current_tasks": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Currently executing tasks"
    }
  },
  "required": ["version", "uptime", "health"]
}
```

## Integration Schemas

### LLMRequest

```json
{
  "type": "object",
  "properties": {
    "model": {
      "type": "string",
      "description": "LLM model identifier"
    },
    "prompt": {
      "type": "string",
      "description": "Input prompt"
    },
    "max_tokens": {
      "type": "integer",
      "minimum": 1,
      "description": "Maximum tokens to generate"
    },
    "temperature": {
      "type": "number",
      "format": "float",
      "minimum": 0,
      "maximum": 2,
      "description": "Sampling temperature"
    },
    "context": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/MemoryItem"
      },
      "description": "Memory context to include"
    },
    "system_message": {
      "type": "string",
      "description": "System message for the LLM"
    }
  },
  "required": ["model", "prompt"]
}
```

### LLMResponse

```json
{
  "type": "object",
  "properties": {
    "model": {
      "type": "string",
      "description": "LLM model used"
    },
    "response": {
      "type": "string",
      "description": "Generated response"
    },
    "tokens_used": {
      "type": "object",
      "properties": {
        "prompt": {
          "type": "integer",
          "description": "Tokens used in the prompt"
        },
        "completion": {
          "type": "integer",
          "description": "Tokens used in the completion"
        },
        "total": {
          "type": "integer",
          "description": "Total tokens used"
        }
      }
    },
    "finish_reason": {
      "type": "string",
      "enum": ["stop", "length", "content_filter"],
      "description": "Reason why the generation finished"
    },
    "memory_items_created": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "description": "IDs of memory items created from this response"
    }
  },
  "required": ["model", "response", "tokens_used"]
}
```

---

This document defines the core schemas used throughout the NCA API. All API endpoints should reference these schemas for request and response validation. The schemas are designed to be extensible as the system evolves.

For implementation details of specific endpoints that use these schemas, refer to the [API Reference](../api/reference.md) documentation.