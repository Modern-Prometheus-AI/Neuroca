# NeuroCognitive Architecture (NCA) API Endpoints

## Overview

This document provides detailed specifications for all API endpoints in the NeuroCognitive Architecture (NCA) system. The API follows RESTful principles and uses JSON for request and response payloads. All endpoints are versioned to ensure backward compatibility as the system evolves.

## Base URL

```
https://api.neuroca.ai/v1
```

## Authentication

All API requests require authentication using JWT (JSON Web Tokens). Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

To obtain a token, use the authentication endpoints described in the [Authentication](#authentication-endpoints) section.

## Response Format

All responses follow a standard format:

```json
{
  "status": "success|error",
  "data": { ... },  // Present on successful requests
  "error": {        // Present on failed requests
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }  // Optional additional error details
  },
  "meta": {         // Optional metadata
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

## Rate Limiting

API requests are subject to rate limiting to ensure system stability. Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1620000000
```

When rate limits are exceeded, the API returns a 429 Too Many Requests status code.

## API Endpoints

### Authentication Endpoints

#### POST /auth/login

Authenticates a user and returns a JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2023-12-31T23:59:59Z",
    "user": {
      "id": "usr_123456789",
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
}
```

**Status Codes:**
- 200: Success
- 401: Invalid credentials
- 422: Validation error

#### POST /auth/refresh

Refreshes an existing JWT token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2023-12-31T23:59:59Z"
  }
}
```

**Status Codes:**
- 200: Success
- 401: Invalid refresh token

#### POST /auth/logout

Invalidates the current JWT token.

**Response:**
```json
{
  "status": "success",
  "data": {
    "message": "Successfully logged out"
  }
}
```

**Status Codes:**
- 200: Success
- 401: Unauthorized

### Memory System Endpoints

#### GET /memory/working

Retrieves the current state of working memory.

**Query Parameters:**
- `limit` (optional): Maximum number of memory items to return (default: 20)
- `offset` (optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "status": "success",
  "data": {
    "memories": [
      {
        "id": "mem_123456789",
        "content": "User asked about project timeline",
        "importance": 0.85,
        "created_at": "2023-10-15T14:30:00Z",
        "expires_at": "2023-10-15T14:40:00Z",
        "metadata": {
          "source": "conversation",
          "context": "project_planning"
        }
      },
      // Additional memory items...
    ]
  },
  "meta": {
    "pagination": {
      "limit": 20,
      "offset": 0,
      "total": 45
    }
  }
}
```

**Status Codes:**
- 200: Success
- 401: Unauthorized
- 403: Forbidden

#### POST /memory/working

Creates a new working memory item.

**Request:**
```json
{
  "content": "User mentioned deadline is next Friday",
  "importance": 0.75,
  "ttl": 600,  // Time to live in seconds
  "metadata": {
    "source": "conversation",
    "context": "project_planning"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "mem_123456789",
    "content": "User mentioned deadline is next Friday",
    "importance": 0.75,
    "created_at": "2023-10-15T14:35:00Z",
    "expires_at": "2023-10-15T14:45:00Z",
    "metadata": {
      "source": "conversation",
      "context": "project_planning"
    }
  }
}
```

**Status Codes:**
- 201: Created
- 400: Bad request
- 401: Unauthorized
- 422: Validation error

#### GET /memory/short-term

Retrieves short-term memory items.

**Query Parameters:**
- `limit` (optional): Maximum number of memory items to return (default: 50)
- `offset` (optional): Offset for pagination (default: 0)
- `query` (optional): Search query to filter memories
- `start_date` (optional): Filter memories created after this date
- `end_date` (optional): Filter memories created before this date
- `importance_min` (optional): Minimum importance score (0-1)
- `importance_max` (optional): Maximum importance score (0-1)

**Response:**
```json
{
  "status": "success",
  "data": {
    "memories": [
      {
        "id": "stm_123456789",
        "content": "User prefers visual explanations over text",
        "importance": 0.65,
        "created_at": "2023-10-14T10:30:00Z",
        "metadata": {
          "source": "observation",
          "context": "user_preferences",
          "confidence": 0.82
        }
      },
      // Additional memory items...
    ]
  },
  "meta": {
    "pagination": {
      "limit": 50,
      "offset": 0,
      "total": 120
    }
  }
}
```

**Status Codes:**
- 200: Success
- 401: Unauthorized
- 403: Forbidden

#### POST /memory/short-term

Creates a new short-term memory item.

**Request:**
```json
{
  "content": "User prefers visual explanations over text",
  "importance": 0.65,
  "metadata": {
    "source": "observation",
    "context": "user_preferences",
    "confidence": 0.82
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "stm_123456789",
    "content": "User prefers visual explanations over text",
    "importance": 0.65,
    "created_at": "2023-10-15T14:38:00Z",
    "metadata": {
      "source": "observation",
      "context": "user_preferences",
      "confidence": 0.82
    }
  }
}
```

**Status Codes:**
- 201: Created
- 400: Bad request
- 401: Unauthorized
- 422: Validation error

#### GET /memory/long-term

Retrieves long-term memory items.

**Query Parameters:**
- `limit` (optional): Maximum number of memory items to return (default: 50)
- `offset` (optional): Offset for pagination (default: 0)
- `query` (optional): Search query to filter memories
- `category` (optional): Filter by memory category
- `importance_min` (optional): Minimum importance score (0-1)
- `semantic_search` (optional): Perform semantic search with this query

**Response:**
```json
{
  "status": "success",
  "data": {
    "memories": [
      {
        "id": "ltm_123456789",
        "content": "User has a background in cognitive psychology",
        "importance": 0.92,
        "created_at": "2023-09-05T08:15:00Z",
        "last_accessed": "2023-10-14T16:20:00Z",
        "access_count": 5,
        "category": "user_background",
        "metadata": {
          "source": "explicit_statement",
          "confidence": 0.98,
          "related_memories": ["ltm_987654321", "ltm_456789123"]
        }
      },
      // Additional memory items...
    ]
  },
  "meta": {
    "pagination": {
      "limit": 50,
      "offset": 0,
      "total": 350
    }
  }
}
```

**Status Codes:**
- 200: Success
- 401: Unauthorized
- 403: Forbidden

#### POST /memory/long-term

Creates a new long-term memory item.

**Request:**
```json
{
  "content": "User has a background in cognitive psychology",
  "importance": 0.92,
  "category": "user_background",
  "metadata": {
    "source": "explicit_statement",
    "confidence": 0.98,
    "related_memories": ["ltm_987654321", "ltm_456789123"]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "ltm_123456789",
    "content": "User has a background in cognitive psychology",
    "importance": 0.92,
    "created_at": "2023-10-15T14:40:00Z",
    "last_accessed": "2023-10-15T14:40:00Z",
    "access_count": 1,
    "category": "user_background",
    "metadata": {
      "source": "explicit_statement",
      "confidence": 0.98,
      "related_memories": ["ltm_987654321", "ltm_456789123"]
    }
  }
}
```

**Status Codes:**
- 201: Created
- 400: Bad request
- 401: Unauthorized
- 422: Validation error

### Health System Endpoints

#### GET /health/status

Retrieves the current health status of the NCA system.

**Response:**
```json
{
  "status": "success",
  "data": {
    "energy": 0.85,
    "attention": 0.72,
    "mood": 0.65,
    "stress": 0.30,
    "last_updated": "2023-10-15T14:42:00Z",
    "status": "optimal",
    "metrics": {
      "memory_utilization": 0.45,
      "processing_load": 0.38,
      "response_time_avg": 1.2
    }
  }
}
```

**Status Codes:**
- 200: Success
- 401: Unauthorized
- 403: Forbidden

#### POST /health/adjust

Adjusts health parameters of the NCA system.

**Request:**
```json
{
  "energy": 0.90,
  "attention": 0.80,
  "mood": 0.70,
  "stress": 0.25,
  "reason": "System maintenance and optimization"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "energy": 0.90,
    "attention": 0.80,
    "mood": 0.70,
    "stress": 0.25,
    "last_updated": "2023-10-15T14:45:00Z",
    "status": "optimal",
    "adjustment_id": "adj_123456789"
  }
}
```

**Status Codes:**
- 200: Success
- 400: Bad request
- 401: Unauthorized
- 403: Forbidden
- 422: Validation error

### LLM Integration Endpoints

#### POST /llm/query

Sends a query to the integrated LLM with NCA context.

**Request:**
```json
{
  "query": "What's the project timeline?",
  "context_level": "comprehensive",
  "include_memory_types": ["working", "short_term", "long_term"],
  "max_tokens": 500,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "response": "Based on our previous discussions, the project timeline has three major milestones...",
    "memory_context": {
      "working": 3,
      "short_term": 5,
      "long_term": 2
    },
    "tokens_used": 320,
    "processing_time": 1.2,
    "confidence": 0.85
  }
}
```

**Status Codes:**
- 200: Success
- 400: Bad request
- 401: Unauthorized
- 422: Validation error
- 429: Too many requests
- 503: LLM service unavailable

#### POST /llm/conversation

Initiates or continues a conversation with the NCA-enhanced LLM.

**Request:**
```json
{
  "message": "Can you explain how the memory system works?",
  "conversation_id": "conv_123456789",  // Optional, omit for new conversation
  "context_level": "detailed",
  "max_tokens": 800,
  "temperature": 0.8
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "conversation_id": "conv_123456789",
    "response": "The NeuroCognitive Architecture uses a three-tiered memory system inspired by human cognition...",
    "memory_updates": {
      "working_memory_added": 2,
      "short_term_memory_accessed": 3
    },
    "tokens_used": 650,
    "processing_time": 1.8,
    "next_actions": ["provide_examples", "ask_for_clarification"]
  }
}
```

**Status Codes:**
- 200: Success
- 400: Bad request
- 401: Unauthorized
- 404: Conversation not found
- 422: Validation error
- 429: Too many requests
- 503: LLM service unavailable

### System Management Endpoints

#### GET /system/status

Retrieves the overall system status.

**Response:**
```json
{
  "status": "success",
  "data": {
    "system_status": "operational",
    "version": "1.2.3",
    "uptime": 345600,  // In seconds
    "memory_usage": {
      "working_memory_count": 15,
      "short_term_memory_count": 245,
      "long_term_memory_count": 1250
    },
    "health_metrics": {
      "energy": 0.85,
      "attention": 0.72,
      "response_time_avg": 1.2
    },
    "llm_integration": {
      "status": "connected",
      "model": "gpt-4",
      "requests_today": 1250
    }
  }
}
```

**Status Codes:**
- 200: Success
- 401: Unauthorized
- 403: Forbidden

#### POST /system/maintenance

Initiates system maintenance tasks.

**Request:**
```json
{
  "tasks": ["memory_consolidation", "health_optimization"],
  "schedule": "immediate",
  "priority": "normal"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "maintenance_id": "maint_123456789",
    "tasks_scheduled": ["memory_consolidation", "health_optimization"],
    "estimated_completion": "2023-10-15T15:00:00Z",
    "status": "in_progress"
  }
}
```

**Status Codes:**
- 202: Accepted
- 400: Bad request
- 401: Unauthorized
- 403: Forbidden
- 422: Validation error

## Webhook Endpoints

### POST /webhooks/register

Registers a new webhook for event notifications.

**Request:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["memory.created", "health.critical", "system.maintenance.completed"],
  "description": "Production monitoring webhook",
  "secret": "your_webhook_secret"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "webhook_id": "wh_123456789",
    "url": "https://example.com/webhook",
    "events": ["memory.created", "health.critical", "system.maintenance.completed"],
    "created_at": "2023-10-15T14:50:00Z",
    "status": "active"
  }
}
```

**Status Codes:**
- 201: Created
- 400: Bad request
- 401: Unauthorized
- 422: Validation error

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_INVALID_CREDENTIALS` | Invalid username or password |
| `AUTH_EXPIRED_TOKEN` | Authentication token has expired |
| `AUTH_INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `VALIDATION_ERROR` | Request validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `MEMORY_STORAGE_FULL` | Memory storage capacity reached |
| `LLM_SERVICE_UNAVAILABLE` | LLM service is currently unavailable |
| `SYSTEM_MAINTENANCE` | System is in maintenance mode |
| `INTERNAL_SERVER_ERROR` | Unexpected server error |

## Versioning and Deprecation

API versions follow semantic versioning. When a new version is released, previous versions remain supported for at least 6 months. Deprecated endpoints will return a warning header:

```
X-API-Warning: This endpoint is deprecated and will be removed on YYYY-MM-DD. Please use /v2/new-endpoint instead.
```

## Support

For API support, please contact:
- Email: api-support@neuroca.ai
- Documentation: https://docs.neuroca.ai
- Status page: https://status.neuroca.ai