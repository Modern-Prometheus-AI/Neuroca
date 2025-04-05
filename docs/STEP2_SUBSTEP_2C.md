# NeuroCognitive Architecture (NCA) - Interface Design

This document outlines the comprehensive interface design for the NeuroCognitive Architecture (NCA) system, including API contracts, communication protocols, interface patterns, error handling, and versioning strategies.

## Table of Contents
1. [API Contracts](#1-api-contracts)
2. [Communication Protocols](#2-communication-protocols)
3. [Interface Patterns](#3-interface-patterns)
4. [Error Handling](#4-error-handling)
5. [Versioning Strategy](#5-versioning-strategy)

## 1. API Contracts

### 1.1 Core API Design Principles

The NCA system follows these API design principles:

- **Resource-Oriented**: APIs are organized around resources and standard HTTP methods
- **Consistent Naming**: Consistent naming conventions across all endpoints
- **Stateless**: Each request contains all information needed to process it
- **Idempotent Operations**: Safe to retry operations without side effects
- **Granular Permissions**: Fine-grained access control at the endpoint level
- **Comprehensive Documentation**: OpenAPI/Swagger specifications for all endpoints
- **Performance Optimized**: Designed for minimal latency and maximum throughput

### 1.2 Memory Management API

#### 1.2.1 Memory Creation

```http
POST /api/v1/memories
Content-Type: application/json
Authorization: Bearer {token}

{
  "content": "User expressed interest in machine learning applications",
  "contentType": "TEXT",
  "source": "USER_INPUT",
  "conversationId": "conv_123abc",
  "importance": 5,
  "tags": ["machine_learning", "user_interest"],
  "metadata": {
    "userContext": "Initial consultation",
    "confidenceScore": 0.95
  }
}
```

**Response (201 Created):**

```json
{
  "id": "mem_456def",
  "content": "User expressed interest in machine learning applications",
  "contentType": "TEXT",
  "createdAt": "2023-06-15T14:30:00Z",
  "tier": "STM",
  "healthScore": 85,
  "embedding": {
    "model": "text-embedding-ada-002",
    "dimensions": 1536,
    "truncated": true
  },
  "_links": {
    "self": {"href": "/api/v1/memories/mem_456def"},
    "health": {"href": "/api/v1/memories/mem_456def/health"},
    "related": {"href": "/api/v1/memories/mem_456def/related"}
  }
}
```

#### 1.2.2 Memory Retrieval

```http
GET /api/v1/memories/{memoryId}
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "id": "mem_456def",
  "content": "User expressed interest in machine learning applications",
  "contentType": "TEXT",
  "createdAt": "2023-06-15T14:30:00Z",
  "updatedAt": "2023-06-15T14:30:00Z",
  "lastAccessedAt": "2023-06-15T15:45:00Z",
  "accessCount": 3,
  "tier": "STM",
  "healthScore": 85,
  "tags": ["machine_learning", "user_interest"],
  "source": "USER_INPUT",
  "conversationId": "conv_123abc",
  "importance": 5,
  "metadata": {
    "userContext": "Initial consultation",
    "confidenceScore": 0.95
  },
  "_links": {
    "self": {"href": "/api/v1/memories/mem_456def"},
    "health": {"href": "/api/v1/memories/mem_456def/health"},
    "related": {"href": "/api/v1/memories/mem_456def/related"}
  }
}
```

#### 1.2.3 Semantic Memory Search

```http
POST /api/v1/memories/search
Content-Type: application/json
Authorization: Bearer {token}

{
  "query": "What topics is the user interested in?",
  "searchType": "SEMANTIC",
  "tiers": ["STM", "MTM", "LTM"],
  "limit": 10,
  "minRelevance": 0.7,
  "includeContent": true,
  "filters": {
    "tags": ["user_interest"],
    "minHealthScore": 50,
    "timeRange": {
      "start": "2023-06-01T00:00:00Z",
      "end": "2023-06-15T23:59:59Z"
    }
  }
}
```

**Response (200 OK):**

```json
{
  "results": [
    {
      "id": "mem_456def",
      "content": "User expressed interest in machine learning applications",
      "relevanceScore": 0.92,
      "tier": "STM",
      "healthScore": 85,
      "createdAt": "2023-06-15T14:30:00Z",
      "_links": {
        "self": {"href": "/api/v1/memories/mem_456def"}
      }
    },
    {
      "id": "mem_789ghi",
      "content": "User mentioned wanting to learn about natural language processing",
      "relevanceScore": 0.87,
      "tier": "STM",
      "healthScore": 78,
      "createdAt": "2023-06-14T10:15:00Z",
      "_links": {
        "self": {"href": "/api/v1/memories/mem_789ghi"}
      }
    }
    // Additional results...
  ],
  "metadata": {
    "totalResults": 15,
    "returnedResults": 10,
    "executionTimeMs": 45,
    "queryEmbeddingModel": "text-embedding-ada-002"
  },
  "_links": {
    "next": {"href": "/api/v1/memories/search?page=2&query=..."}
  }
}
```

#### 1.2.4 Memory Update

```http
PATCH /api/v1/memories/{memoryId}
Content-Type: application/json
Authorization: Bearer {token}

{
  "content": "User expressed strong interest in machine learning applications, particularly for NLP",
  "importance": 7,
  "tags": ["machine_learning", "user_interest", "nlp"]
}
```

**Response (200 OK):**

```json
{
  "id": "mem_456def",
  "content": "User expressed strong interest in machine learning applications, particularly for NLP",
  "contentType": "TEXT",
  "updatedAt": "2023-06-15T16:20:00Z",
  "importance": 7,
  "tags": ["machine_learning", "user_interest", "nlp"],
  "healthScore": 88,
  "_links": {
    "self": {"href": "/api/v1/memories/mem_456def"}
  }
}
```

#### 1.2.5 Memory Deletion

```http
DELETE /api/v1/memories/{memoryId}
Authorization: Bearer {token}
```

**Response (204 No Content)**

#### 1.2.6 Batch Memory Operations

```http
POST /api/v1/memories/batch
Content-Type: application/json
Authorization: Bearer {token}

{
  "operations": [
    {
      "operation": "CREATE",
      "memory": {
        "content": "First new memory",
        "contentType": "TEXT",
        "tags": ["tag1", "tag2"]
      }
    },
    {
      "operation": "UPDATE",
      "memoryId": "mem_456def",
      "changes": {
        "importance": 8
      }
    },
    {
      "operation": "DELETE",
      "memoryId": "mem_123abc"
    }
  ]
}
```

**Response (200 OK):**

```json
{
  "results": [
    {
      "operation": "CREATE",
      "status": "SUCCESS",
      "memoryId": "mem_901jkl",
      "_links": {
        "memory": {"href": "/api/v1/memories/mem_901jkl"}
      }
    },
    {
      "operation": "UPDATE",
      "status": "SUCCESS",
      "memoryId": "mem_456def",
      "_links": {
        "memory": {"href": "/api/v1/memories/mem_456def"}
      }
    },
    {
      "operation": "DELETE",
      "status": "SUCCESS",
      "memoryId": "mem_123abc"
    }
  ],
  "summary": {
    "total": 3,
    "successful": 3,
    "failed": 0
  }
}
```

### 1.3 Health Management API

#### 1.3.1 Get Memory Health

```http
GET /api/v1/memories/{memoryId}/health
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "memoryId": "mem_456def",
  "currentTier": "STM",
  "baseHealthScore": 85,
  "lastCalculatedAt": "2023-06-15T16:30:00Z",
  
  "healthFactors": {
    "recencyFactor": 0.95,
    "relevanceScore": 82,
    "accessFrequency": 0.75,
    "importanceFlag": 7
  },
  
  "tierTransition": {
    "promotionThreshold": 90,
    "demotionThreshold": 40,
    "forgettingThreshold": 20,
    "promotionEligibility": 0.85,
    "estimatedTimeToPromotion": "2 days"
  },
  
  "history": {
    "snapshots": [
      {
        "timestamp": "2023-06-15T14:30:00Z",
        "healthScore": 80,
        "tier": "STM",
        "reason": "Initial creation"
      },
      {
        "timestamp": "2023-06-15T15:45:00Z",
        "healthScore": 83,
        "tier": "STM",
        "reason": "Access boost"
      },
      {
        "timestamp": "2023-06-15T16:20:00Z",
        "healthScore": 85,
        "tier": "STM",
        "reason": "Content update"
      }
    ],
    "_links": {
      "fullHistory": {"href": "/api/v1/memories/mem_456def/health/history"}
    }
  },
  
  "_links": {
    "self": {"href": "/api/v1/memories/mem_456def/health"},
    "memory": {"href": "/api/v1/memories/mem_456def"}
  }
}
```

#### 1.3.2 Update Memory Health

```http
PATCH /api/v1/memories/{memoryId}/health
Content-Type: application/json
Authorization: Bearer {token}

{
  "importanceFlag": 9,
  "manualHealthAdjustment": 5,
  "adjustmentReason": "Critical information for current task",
  "preventDemotion": true,
  "preventForgetting": true,
  "durationHours": 24
}
```

**Response (200 OK):**

```json
{
  "memoryId": "mem_456def",
  "currentTier": "STM",
  "baseHealthScore": 90,
  "lastCalculatedAt": "2023-06-15T16:45:00Z",
  "adjustmentApplied": true,
  "newHealthFactors": {
    "importanceFlag": 9
  },
  "protectionStatus": {
    "demotionProtected": true,
    "forgettingProtected": true,
    "protectionExpires": "2023-06-16T16:45:00Z"
  },
  "_links": {
    "self": {"href": "/api/v1/memories/mem_456def/health"},
    "memory": {"href": "/api/v1/memories/mem_456def"}
  }
}
```

#### 1.3.3 Force Memory Tier Transition

```http
POST /api/v1/memories/{memoryId}/transition
Content-Type: application/json
Authorization: Bearer {token}

{
  "targetTier": "MTM",
  "reason": "Information needs longer retention",
  "preserveOriginal": false
}
```

**Response (200 OK):**

```json
{
  "memoryId": "mem_456def",
  "previousTier": "STM",
  "newTier": "MTM",
  "transitionTimestamp": "2023-06-15T16:50:00Z",
  "healthScore": 90,
  "reason": "Information needs longer retention",
  "_links": {
    "memory": {"href": "/api/v1/memories/mem_456def"},
    "health": {"href": "/api/v1/memories/mem_456def/health"}
  }
}
```

### 1.4 Neural Tubule Network API

#### 1.4.1 Get Memory Relationships

```http
GET /api/v1/memories/{memoryId}/relationships
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "memoryId": "mem_456def",
  "relationships": [
    {
      "targetMemoryId": "mem_789ghi",
      "relationshipType": "SIMILAR",
      "strength": 0.85,
      "createdAt": "2023-06-15T14:35:00Z",
      "lastReinforced": "2023-06-15T15:45:00Z",
      "bidirectional": true,
      "tubuleId": "tub_123abc",
      "_links": {
        "targetMemory": {"href": "/api/v1/memories/mem_789ghi"}
      }
    },
    {
      "targetMemoryId": "mem_012mno",
      "relationshipType": "PARENT",
      "strength": 0.72,
      "createdAt": "2023-06-15T14:40:00Z",
      "lastReinforced": "2023-06-15T14:40:00Z",
      "bidirectional": false,
      "tubuleId": "tub_456def",
      "_links": {
        "targetMemory": {"href": "/api/v1/memories/mem_012mno"}
      }
    }
  ],
  "metadata": {
    "totalRelationships": 2,
    "strongestType": "SIMILAR",
    "averageStrength": 0.785
  },
  "_links": {
    "self": {"href": "/api/v1/memories/mem_456def/relationships"},
    "memory": {"href": "/api/v1/memories/mem_456def"},
    "graph": {"href": "/api/v1/memories/mem_456def/graph?depth=2"}
  }
}
```

#### 1.4.2 Create Relationship

```http
POST /api/v1/tubules
Content-Type: application/json
Authorization: Bearer {token}

{
  "sourceMemoryId": "mem_456def",
  "targetMemoryId": "mem_345pqr",
  "relationshipType": "CONTRADICTS",
  "strength": 0.65,
  "bidirectional": true,
  "metadata": {
    "createdBy": "manual_annotation",
    "confidence": 0.9
  }
}
```

**Response (201 Created):**

```json
{
  "tubuleId": "tub_789ghi",
  "sourceMemoryId": "mem_456def",
  "targetMemoryId": "mem_345pqr",
  "relationshipType": "CONTRADICTS",
  "strength": 0.65,
  "createdAt": "2023-06-15T17:00:00Z",
  "lastActivatedAt": "2023-06-15T17:00:00Z",
  "activationCount": 1,
  "bidirectional": true,
  "_links": {
    "self": {"href": "/api/v1/tubules/tub_789ghi"},
    "sourceMemory": {"href": "/api/v1/memories/mem_456def"},
    "targetMemory": {"href": "/api/v1/memories/mem_345pqr"}
  }
}
```

#### 1.4.3 Update Relationship

```http
PATCH /api/v1/tubules/{tubuleId}
Content-Type: application/json
Authorization: Bearer {token}

{
  "strength": 0.80,
  "relationshipType": "STRONGLY_CONTRADICTS"
}
```

**Response (200 OK):**

```json
{
  "tubuleId": "tub_789ghi",
  "sourceMemoryId": "mem_456def",
  "targetMemoryId": "mem_345pqr",
  "relationshipType": "STRONGLY_CONTRADICTS",
  "strength": 0.80,
  "updatedAt": "2023-06-15T17:15:00Z",
  "lastActivatedAt": "2023-06-15T17:15:00Z",
  "activationCount": 2,
  "_links": {
    "self": {"href": "/api/v1/tubules/tub_789ghi"}
  }
}
```

#### 1.4.4 Get Memory Graph

```http
GET /api/v1/memories/{memoryId}/graph?depth=2&minStrength=0.5
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "nodes": [
    {
      "id": "mem_456def",
      "label": "User expressed interest in machine learning applications",
      "type": "MEMORY",
      "tier": "STM",
      "healthScore": 90,
      "isRoot": true
    },
    {
      "id": "mem_789ghi",
      "label": "User mentioned wanting to learn about natural language processing",
      "type": "MEMORY",
      "tier": "STM",
      "healthScore": 78
    },
    {
      "id": "mem_345pqr",
      "label": "User stated they have no background in programming",
      "type": "MEMORY",
      "tier": "MTM",
      "healthScore": 65
    }
    // Additional nodes...
  ],
  "edges": [
    {
      "source": "mem_456def",
      "target": "mem_789ghi",
      "type": "SIMILAR",
      "strength": 0.85,
      "tubuleId": "tub_123abc"
    },
    {
      "source": "mem_456def",
      "target": "mem_345pqr",
      "type": "STRONGLY_CONTRADICTS",
      "strength": 0.80,
      "tubuleId": "tub_789ghi"
    }
    // Additional edges...
  ],
  "metadata": {
    "rootMemory": "mem_456def",
    "depth": 2,
    "nodeCount": 8,
    "edgeCount": 12,
    "averageStrength": 0.72
  },
  "_links": {
    "self": {"href": "/api/v1/memories/mem_456def/graph?depth=2&minStrength=0.5"},
    "expandedGraph": {"href": "/api/v1/memories/mem_456def/graph?depth=3&minStrength=0.5"}
  }
}
```

### 1.5 Memory Lymphatic System API

#### 1.5.1 Get Consolidation Jobs

```http
GET /api/v1/consolidation/jobs?status=PENDING&limit=10
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "jobs": [
    {
      "jobId": "job_123abc",
      "status": "PENDING",
      "jobType": "REDUNDANCY_CHECK",
      "targetMemoryIds": ["mem_123abc", "mem_456def"],
      "priority": 75,
      "scheduledFor": "2023-06-16T02:00:00Z",
      "createdAt": "2023-06-15T14:40:00Z",
      "_links": {
        "self": {"href": "/api/v1/consolidation/jobs/job_123abc"},
        "cancel": {"href": "/api/v1/consolidation/jobs/job_123abc/cancel"}
      }
    },
    {
      "jobId": "job_456def",
      "status": "PENDING",
      "jobType": "ABSTRACTION",
      "targetMemoryIds": ["mem_789ghi", "mem_012jkl", "mem_345mno"],
      "priority": 60,
      "scheduledFor": "2023-06-16T02:30:00Z",
      "createdAt": "2023-06-15T15:10:00Z",
      "_links": {
        "self": {"href": "/api/v1/consolidation/jobs/job_456def"},
        "cancel": {"href": "/api/v1/consolidation/jobs/job_456def/cancel"}
      }
    }
    // Additional jobs...
  ],
  "metadata": {
    "totalJobs": 45,
    "returnedJobs": 10,
    "pendingJobs": 32,
    "processingJobs": 8,
    "completedJobs": 5,
    "failedJobs": 0
  },
  "_links": {
    "self": {"href": "/api/v1/consolidation/jobs?status=PENDING&limit=10"},
    "next": {"href": "/api/v1/consolidation/jobs?status=PENDING&limit=10&page=2"}
  }
}
```

#### 1.5.2 Create Consolidation Job

```http
POST /api/v1/consolidation/jobs
Content-Type: application/json
Authorization: Bearer {token}

{
  "jobType": "REDUNDANCY_CHECK",
  "targetMemoryIds": ["mem_123abc", "mem_456def"],
  "priority": 75,
  "scheduledFor": "2023-06-16T02:00:00Z",
  "parameters": {
    "similarityThreshold": 0.85,
    "maxMergeCount": 5,
    "preserveOriginals": false
  },
  "resourceLimits": {
    "maxRuntime": 300,
    "maxMemoryMB": 512
  }
}
```

**Response (201 Created):**

```json
{
  "jobId": "job_123abc",
  "status": "PENDING",
  "jobType": "REDUNDANCY_CHECK",
  "targetMemoryIds": ["mem_123abc", "mem_456def"],
  "priority": 75,
  "scheduledFor": "2023-06-16T02:00:00Z",
  "createdAt": "2023-06-15T14:40:00Z",
  "_links": {
    "self": {"href": "/api/v1/consolidation/jobs/job_123abc"},
    "cancel": {"href": "/api/v1/consolidation/jobs/job_123abc/cancel"}
  }
}
```

#### 1.5.3 Get Consolidation Results

```http
GET /api/v1/consolidation/jobs/{jobId}/results
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "jobId": "job_123abc",
  "status": "COMPLETED",
  "startedAt": "2023-06-16T02:00:05Z",
  "completedAt": "2023-06-16T02:00:35Z",
  "processingDuration": 30000,
  
  "resourceConsumption": {
    "cpuTimeMs": 25000,
    "memoryBytesUsed": 128000000,
    "dbOperations": 42
  },
  
  "resultSummary": "Merged 3 similar memories about machine learning interests",
  
  "memoriesCreated": [
    {
      "memoryId": "mem_789ghi",
      "content": "User has consistent interest in machine learning applications, particularly NLP",
      "tier": "MTM",
      "_links": {
        "memory": {"href": "/api/v1/memories/mem_789ghi"}
      }
    }
  ],
  
  "memoriesModified": [
    {
      "memoryId": "mem_123abc",
      "changes": ["Added relationship to consolidated memory"],
      "_links": {
        "memory": {"href": "/api/v1/memories/mem_123abc"}
      }
    }
  ],
  
  "memoriesDeleted": [
    {
      "memoryId": "mem_456def",
      "reason": "Redundant information consolidated into mem_789ghi"
    }
  ],
  
  "_links": {
    "self": {"href": "/api/v1/consolidation/jobs/job_123abc/results"},
    "job": {"href": "/api/v1/consolidation/jobs/job_123abc"}
  }
}
```

### 1.6 Temporal Annealing Scheduler API

#### 1.6.1 Get Annealing Schedules

```http
GET /api/v1/annealing/schedules
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "schedules": [
    {
      "id": "sched_123abc",
      "scheduleType": "DAILY",
      "targetTier": "STM",
      "processingIntensity": 70,
      "cronExpression": "0 2 * * *",
      "maxDuration": 3600,
      "cooldownPeriod": 21600,
      "maxCpuPercent": 50,
      "maxMemoryPercent": 70,
      "lastRunAt": "2023-06-15T02:00:00Z",
      "nextRunAt": "2023-06-16T02:00:00Z",
      "isActive": true,
      "_links": {
        "self": {"href": "/api/v1/annealing/schedules/sched_123abc"},
        "runs": {"href": "/api/v1/annealing/schedules/sched_123abc/runs"}
      }
    },
    {
      "id": "sched_456def",
      "scheduleType": "WEEKLY",
      "targetTier": "MTM",
      "processingIntensity": 90,
      "cronExpression": "0 3 * * 0",
      "maxDuration": 7200,
      "cooldownPeriod": 86400,
      "maxCpuPercent": 70,
      "maxMemoryPercent": 80,
      "lastRunAt": "2023-06-11T03:00:00Z",
      "nextRunAt": "2023-06-18T03:00:00Z",
      "isActive": true,
      "_links": {
        "self": {"href": "/api/v1/annealing/schedules/sched_456def"},
        "runs": {"href": "/api/v1/annealing/schedules/sched_456def/runs"}
      }
    }
    // Additional schedules...
  ],
  "_links": {
    "self": {"href": "/api/v1/annealing/schedules"}
  }
}
```

#### 1.6.2 Create Annealing Schedule

```http
POST /api/v1/annealing/schedules
Content-Type: application/json
Authorization: Bearer {token}

{
  "scheduleType": "DAILY",
  "targetTier": "STM",
  "processingIntensity": 70,
  "cronExpression": "0 2 * * *",
  "maxDuration": 3600,
  "cooldownPeriod": 21600,
  "maxCpuPercent": 50,
  "maxMemoryPercent": 70,
  "isActive": true
}
```

**Response (201 Created):**

```json
{
  "id": "sched_123abc",
  "scheduleType": "DAILY",
  "targetTier": "STM",
  "processingIntensity": 70,
  "cronExpression": "0 2 * * *",
  "maxDuration": 3600,
  "cooldownPeriod": 21600,
  "maxCpuPercent": 50,
  "maxMemoryPercent": 70,
  "nextRunAt": "2023-06-16T02:00:00Z",
  "isActive": true,
  "_links": {
    "self": {"href": "/api/v1/annealing/schedules/sched_123abc"},
    "runs": {"href": "/api/v1/annealing/schedules/sched_123abc/runs"}
  }
}
```

#### 1.6.3 Get Annealing Run History

```http
GET /api/v1/annealing/schedules/{scheduleId}/runs
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "scheduleId": "sched_123abc",
  "runs": [
    {
      "id": "run_123abc",
      "startTime": "2023-06-15T02:00:03Z",
      "endTime": "2023-06-15T02:45:12Z",
      "status": "COMPLETED",
      "durationSeconds": 2709,
      "memoriesProcessed": 12458,
      "cpuPercentAvg": 45.2,
      "memoryPercentAvg": 62.8,
      "jobsCreated": 87,
      "successRate": 0.98,
      "_links": {
        "self": {"href": "/api/v1/annealing/runs/run_123abc"},
        "jobs": {"href": "/api/v1/consolidation/jobs?runId=run_123abc"}
      }
    },
    {
      "id": "run_456def",
      "startTime": "2023-06-14T02:00:01Z",
      "endTime": "2023-06-14T02:38:45Z",
      "status": "COMPLETED",
      "durationSeconds": 2324,
      "memoriesProcessed": 10982,
      "cpuPercentAvg": 42.7,
      "memoryPercentAvg": 58.3,
      "jobsCreated": 72,
      "successRate": 1.0,
      "_links": {
        "self": {"href": "/api/v1/annealing/runs/run_456def"},
        "jobs": {"href": "/api/v1/consolidation/jobs?runId=run_456def"}
      }
    }
    // Additional runs...
  ],
  "metadata": {
    "totalRuns": 15,
    "averageDuration": 2517,
    "averageMemoriesProcessed": 11720,
    "overallSuccessRate": 0.99
  },
  "_links": {
    "self": {"href": "/api/v1/annealing/schedules/sched_123abc/runs"},
    "schedule": {"href": "/api/v1/annealing/schedules/sched_123abc"}
  }
}
```

### 1.7 LLM Integration API

#### 1.7.1 Retrieve Context for LLM

```http
POST /api/v1/llm/context
Content-Type: application/json
Authorization: Bearer {token}

{
  "query": "What topics has the user shown interest in?",
  "conversationId": "conv_123abc",
  "maxTokens": 1024,
  "relevanceThreshold": 0.7,
  "recencyWeight": 0.8,
  "importanceWeight": 0.6,
  "includeTiers": ["STM", "MTM"],
  "excludeTags": ["system_internal"],
  "retrievalStrategy": "HYBRID"
}
```

**Response (200 OK):**

```json
{
  "contextId": "ctx_123abc",
  "memories": [
    {
      "memoryId": "mem_456def",
      "content": "User expressed strong interest in machine learning applications, particularly for NLP",
      "contextRelevance": 0.92,
      "tokenCount": 18,
      "tier": "STM",
      "createdAt": "2023-06-15T14:30:00Z"
    },
    {
      "memoryId": "mem_789ghi",
      "content": "User mentioned wanting to learn about natural language processing",
      "contextRelevance": 0.87,
      "tokenCount": 12,
      "tier": "STM",
      "createdAt": "2023-06-14T10:15:00Z"
    }
    // Additional memories...
  ],
  "metadata": {
    "totalTokens": 245,
    "maxTokens": 1024,
    "remainingTokens": 779,
    "retrievalLatencyMs": 42,
    "memoryCount": 8,
    "averageRelevance": 0.83
  },
  "formattedContext": "The user has expressed strong interest in machine learning applications, particularly for NLP. They mentioned wanting to learn about natural language processing...",
  "_links": {
    "self": {"href": "/api/v1/llm/context/ctx_123abc"},
    "update": {"href": "/api/v1/llm/context/ctx_123abc"}
  }
}
```

#### 1.7.2 Store LLM Output as Memory

```http
POST /api/v1/llm/memories
Content-Type: application/json
Authorization: Bearer {token}

{
  "content": "The system explained the basics of neural networks to the user, covering activation functions, backpropagation, and gradient descent.",
  "conversationId": "conv_123abc",
  "contextId": "ctx_123abc",
  "source": "LLM_OUTPUT",
  "llmProvider": "openai",
  "llmModel": "gpt-4",
  "importance": 6,
  "tags": ["neural_networks", "explanation", "machine_learning"],
  "relatedUserQuery": "Can you explain how neural networks work?"
}
```

**Response (201 Created):**

```json
{
  "memoryId": "mem_567stu",
  "content": "The system explained the basics of neural networks to the user, covering activation functions, backpropagation, and gradient descent.",
  "tier": "STM",
  "healthScore": 80,
  "createdAt": "2023-06-15T17:30:00Z",
  "metadata": {
    "source": "LLM_OUTPUT",
    "llmProvider": "openai",
    "llmModel": "gpt-4"
  },
  "_links": {
    "self": {"href": "/api/v1/memories/mem_567stu"},
    "conversation": {"href": "/api/v1/conversations/conv_123abc"}
  }
}
```

#### 1.7.3 Update Context with Feedback

```http
PATCH /api/v1/llm/context/{contextId}
Content-Type: application/json
Authorization: Bearer {token}

{
  "relevanceFeedback": [
    {
      "memoryId": "mem_456def",
      "relevanceScore": 0.95,
      "wasUseful": true
    },
    {
      "memoryId": "mem_789ghi",
      "relevanceScore": 0.60,
      "wasUseful": false
    }
  ],
  "additionalQuery": "Tell me more about neural networks",
  "adjustRetrievalStrategy": {
    "increaseRecencyWeight": true,
    "decreaseImportanceWeight": true
  }
}
```

**Response (200 OK):**

```json
{
  "contextId": "ctx_123abc",
  "feedbackApplied": true,
  "memoryHealthUpdates": [
    {
      "memoryId": "mem_456def",
      "healthScoreChange": 3,
      "newHealthScore": 88
    },
    {
      "memoryId": "mem_789ghi",
      "healthScoreChange": -2,
      "newHealthScore": 76
    }
  ],
  "updatedRetrievalStrategy": {
    "recencyWeight": 0.9,
    "importanceWeight": 0.5
  },
  "newMemories": [
    {
      "memoryId": "mem_678vwx",
      "contextRelevance": 0.94,
      "tokenCount": 22,
      "tier": "MTM"
    }
    // Additional new memories...
  ],
  "_links": {
    "self": {"href": "/api/v1/llm/context/ctx_123abc"}
  }
}
```

### 1.8 System Management API

#### 1.8.1 Get System Health

```http
GET /api/v1/system/health
Authorization: Bearer {token}
```

**Response (200 OK):**

```json
{
  "status": "HEALTHY",
  "timestamp": "2023-06-15T17:45:00Z",
  
  "components": [
    {
      "name": "STM_Redis",
      "status": "HEALTHY",
      "latencyMs": 2.3,
      "metrics": {
        "memoryUsage": "65%",
        "connections": 42,
        "operationsPerSecond": 1250
      }
    },
    {
      "name": "MTM_MongoDB",
      "status": "HEALTHY",
      "latencyMs": 15.7,
      "metrics": {
        "cpuUsage": "45%",
        "memoryUsage": "58%",
        "operationsPerSecond": 320
      }
    },
    {
      "name": "LTM_PostgreSQL",
      "status": "HEALTHY",
      "latencyMs": 28.4,
      "metrics": {
        "cpuUsage": "38%",
        "memoryUsage": "62%",
        "connections": 18,
        "activeQueries": 5
      }
    },
    {
      "name": "NTN_Neo4j",
      "status": "HEALTHY",
      "latencyMs": 18.2,
      "metrics": {
        "cpuUsage": "32%",
        "memoryUsage": "48%",
        "activeTransactions": 3
      }
    },
    {
      "name": "MLS_RabbitMQ",
      "status": "HEALTHY",
      "latencyMs": 5.1,
      "metrics": {
        "queuedJobs": 28,
        "processingJobs": 3,
        "messagesPerSecond": 45
      }
    }
  ],
  
  "memoryStats": {
    "STM": {
      "count": 12458,
      "averageHealthScore": 72.5,
      "promotionCandidates": 215
    },
    "MTM": {
      "count": 45872,
      "averageHealthScore": 68.3,
      "promotionCandidates": 1245,
      "demotionCandidates": 320
    },
    "LTM": {
      "count": 128954,
      "averageHealthScore": 81.2,
      "demotionCandidates": 450
    }
  },
  
  "performanceMetrics": {
    "averageApiLatencyMs": 45.2,
    "p95ApiLatencyMs": 120.5,
    "p99ApiLatencyMs": 250.8,
    "requestsPerMinute": 350,
    "errorRate": 0.002
  },
  
  "_links": {
    "self": {"href": "/api/v1/system/health"},
    "metrics": {"href": "/api/v1/system/metrics"},
    "logs": {"href": "/api/v1/system/logs"}
  }
}
```

#### 1.8.2 Configure System Parameters

```http
PATCH /api/v1/system/config
Content-Type: application/json
Authorization: Bearer {token}

{
  "healthParameters": {
    "STM": {
      "baseDecayRate": 0.05,
      "promotionThreshold": 85,
      "forgettingThreshold": 15
    },
    "MTM": {
      "baseDecayRate": 0.02,
      "promotionThreshold": 90,
      "demotionThreshold": 30
    },
    "LTM": {
      "baseDecayRate": 0.005,
      "demotionThreshold": 25
    }
  },
  "retrievalParameters": {
    "defaultRelevanceThreshold": 0.65,
    "defaultRecencyWeight": 0.7,
    "defaultImportanceWeight": 0.8,
    "maxTokensPerMemory": 100
  },
  "consolidationParameters": {
    "redundancySimilarityThreshold": 0.8,
    "abstractionMinMemories": 3,
    "maxDailyConsolidationJobs": 500
  }
}
```

**Response (200 OK):**

```json
{
  "status": "UPDATED",
  "timestamp": "2023-06-15T18:00:00Z",
  "updatedParameters": [
    "healthParameters.STM.baseDecayRate",
    "healthParameters.STM.promotionThreshold",
    "healthParameters.STM.forgettingThreshold",
    "healthParameters.MTM.baseDecayRate",
    "healthParameters.MTM.promotionThreshold",
    "healthParameters.MTM.demotionThreshold",
    "healthParameters.LTM.baseDecayRate",
    "healthParameters.LTM.demotionThreshold",
    "retrievalParameters.defaultRelevanceThreshold",
    "retrievalParameters.defaultRecencyWeight",
    "retrievalParameters.defaultImportanceWeight",
    "retrievalParameters.maxTokensPerMemory",
    "consolidationParameters.redundancySimilarityThreshold",
    "consolidationParameters.abstractionMinMemories",
    "consolidationParameters.maxDailyConsolidationJobs"
  ],
  "requiresRestart": false,
  "effectiveFrom": "2023-06-15T18:00:00Z",
  "_links": {
    "self": {"href": "/api/v1/system/config"},
    "history": {"href": "/api/v1/system/config/history"}
  }
}
```

## 2. Communication Protocols

### 2.1 Synchronous Communication

#### 2.1.1 REST API

The primary interface for external systems to interact with the NCA is a RESTful API with the following characteristics:

```yaml
Protocol: HTTPS
Authentication: OAuth 2.0 with JWT
Content-Type: application/json (primary), application/x-www-form-urlencoded (supported)
Compression: gzip, deflate
Rate Limiting: Token bucket algorithm with tiered limits
Caching: ETags and conditional requests
```

**Implementation Details:**

- **HTTP Status Codes**: Standard usage (200, 201, 204, 400, 401, 403, 404, 409, 429, 500)
- **Pagination**: Cursor-based for large collections with Link headers
- **Filtering**: Query parameters with standardized syntax
- **Sorting**: Multiple field support with direction indicators
- **Field Selection**: Sparse fieldsets to reduce payload size
- **HATEOAS**: Hypermedia links for resource discovery
- **Bulk Operations**: Batch endpoints for high-throughput scenarios
- **Idempotency**: Idempotency keys for safe retries

**Example Request with Pagination, Filtering, and Sorting:**

```http
GET /api/v1/memories?tier=STM&minHealthScore=70&sort=-createdAt,healthScore&fields=id,content,healthScore&limit=50&cursor=eyJpZCI6Im1lbV80NTZkZWYifQ==
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
Accept-Encoding: gzip
Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000
```

#### 2.1.2 GraphQL API

For complex, nested queries and operations, a GraphQL API is provided:

```yaml
Endpoint: /graphql
Protocol: HTTPS
Authentication: Same as REST API
Introspection: Enabled in non-production environments
Batching: Supported for multiple operations
Caching: Apollo Cache Control directives
```

**Example GraphQL Query:**

```graphql
query GetMemoryWithRelationships {
  memory(id: "mem_456def") {
    id
    content
    contentType
    createdAt
    healthScore
    tier
    relationships(first: 5) {
      edges {
        node {
          targetMemory {
            id
            content
            healthScore
          }
          relationshipType
          strength
        }
      }
    }
    health {
      baseHealthScore
      recencyFactor
      relevanceScore
      tierTransition {
        promotionThreshold
        estimatedTimeToPromotion
      }
    }
  }
}
```

**Example GraphQL Mutation:**

```graphql
mutation CreateMemoryAndRelationships {
  createMemory(input: {
    content: "User expressed interest in machine learning applications",
    contentType: TEXT,
    source: USER_INPUT,
    conversationId: "conv_123abc",
    importance: 5,
    tags: ["machine_learning", "user_interest"]
  }) {
    memory {
      id
      content
      healthScore
    }
    relationships {
      id
      targetMemoryId
      relationshipType
    }
  }
}
```

### 2.2 Asynchronous Communication

#### 2.2.1 Event Streaming

For real-time updates and event-driven architectures, the system provides event streams:

```yaml
Protocol: WebSockets, Server-Sent Events (SSE)
Format: JSON
Authentication: Same token-based auth as REST API
Compression: Per-message deflate (WebSockets)
```

**Event Types:**

1. **Memory Events**:
   - `memory.created`
   - `memory.updated`
   - `memory.deleted`
   - `memory.health.changed`
   - `memory.tier.changed`

2. **Relationship Events**:
   - `relationship.created`
   - `relationship.updated`
   - `relationship.deleted`
   - `relationship.reinforced`

3. **System Events**:
   - `system.health.changed`
   - `system.config.updated`
   - `system.maintenance.started`
   - `system.maintenance.completed`

**Example Event:**

```json
{
  "eventType": "memory.tier.changed",
  "timestamp": "2023-06-15T16:50:00Z",
  "data": {
    "memoryId": "mem_456def",
    "previousTier": "STM",
    "newTier": "MTM",
    "reason": "Promotion due to high health score",
    "healthScore": 92
  },
  "metadata": {
    "eventId": "evt_123abc",
    "correlationId": "corr_456def"
  }
}
```

#### 2.2.2 Message Queue Integration

For background processing and integration with external systems:

```yaml
Protocol: AMQP 0-9-1 (RabbitMQ), Kafka Protocol
Format: JSON, Avro, Protocol Buffers
Authentication: SASL, TLS client certificates
Delivery Guarantees: At-least-once with idempotent consumers
```

**Exchange/Topic Structure:**

```
nca.memories.created
nca.memories.updated
nca.memories.deleted
nca.memories.health.changed
nca.memories.tier.changed
nca.relationships.changed
nca.consolidation.jobs.status
nca.annealing.runs.status
nca.system.alerts
```

**Example Message (AMQP):**

```json
{
  "messageType": "memory.created",
  "version": "1.0",
  "timestamp": "2023-06-15T14:30:00Z",
  "payload": {
    "memoryId": "mem_456def",
    "content": "User expressed interest in machine learning applications",
    "contentType": "TEXT",
    "tier": "STM",
    "healthScore": 85,
    "createdAt": "2023-06-15T14:30:00Z"
  },
  "metadata": {
    "messageId": "msg_123abc",
    "correlationId": "corr_456def",
    "source": "nca-api-server-1"
  }
}
```

#### 2.2.3 Webhook Notifications

For integrating with external systems that prefer HTTP callbacks:

```yaml
Protocol: HTTPS
Method: POST
Format: JSON
Authentication: HMAC signature in headers
Retry Policy: Exponential backoff with maximum 5 retries
```

**Webhook Registration:**

```http
POST /api/v1/webhooks
Content-Type: application/json
Authorization: Bearer {token}

{
  "url": "https://example.com/nca-webhook",
  "secret": "whsec_abcdefghijklmnopqrstuvwxyz",
  "events": [
    "memory.created",
    "memory.tier.changed",
    "system.health.changed"
  ],
  "description": "Integration with Example CRM",
  "isActive": true
}
```

**Example Webhook Payload:**

```json
{
  "eventType": "memory.created",
  "timestamp": "2023-06-15T14:30:00Z",
  "data": {
    "memoryId": "mem_456def",
    "content": "User expressed interest in machine learning applications",
    "contentType": "TEXT",
    "tier": "STM",
    "healthScore": 85
  },
  "metadata": {
    "eventId": "evt_123abc",
    "webhookId": "wh_456def",
    "attemptNumber": 1
  }
}
```

**Webhook Security Headers:**

```
X-NCA-Webhook-ID: wh_456def
X-NCA-Webhook-Timestamp: 1623766200
X-NCA-Webhook-Signature: v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd
```

### 2.3 Internal Communication

#### 2.3.1 Service-to-Service Communication

For internal microservices communication:

```yaml
Protocol: gRPC
Format: Protocol Buffers
Authentication: mTLS with service accounts
Load Balancing: Client-side with service discovery
Circuit Breaking: Implemented with configurable thresholds
```

**Example Protocol Buffer Definition:**

```protobuf
syntax = "proto3";

package nca.memory;

service MemoryService {
  rpc CreateMemory(CreateMemoryRequest) returns (Memory);
  rpc GetMemory(GetMemoryRequest) returns (Memory);
  rpc UpdateMemory(UpdateMemoryRequest) returns (Memory);
  rpc DeleteMemory(DeleteMemoryRequest) returns (DeleteMemoryResponse);
  rpc SearchMemories(SearchMemoriesRequest) returns (SearchMemoriesResponse);
}

message Memory {
  string id = 1;
  string content = 2;
  string content_type = 3;
  int64 created_at = 4;
  int64 updated_at = 5;
  int64 last_accessed_at = 6;
  int32 access_count = 7;
  string tier = 8;
  int32 health_score = 9;
  repeated string tags = 10;
  // Additional fields...
}

message CreateMemoryRequest {
  string content = 1;
  string content_type = 2;
  string source = 3;
  string conversation_id = 4;
  int32 importance = 5;
  repeated string tags = 6;
  map<string, string> metadata = 7;
}

// Additional messages...
```

#### 2.3.2 Database Communication

```yaml
STM (Redis):
  Protocol: Redis Protocol (RESP)
  Connection Pooling: Yes, with min/max settings
  Pipelining: Enabled for batch operations
  Scripting: Lua scripts for atomic operations
  
MTM (MongoDB):
  Protocol: MongoDB Wire Protocol
  Connection Pooling: Yes, with min/max settings
  Bulk Operations: Used for batch processing
  Read Preference: primaryPreferred
  
LTM (PostgreSQL):
  Protocol: PostgreSQL Protocol
  Connection Pooling: PgBouncer in transaction mode
  Prepared Statements: Used for repetitive queries
  Transaction Isolation: READ COMMITTED (default)
  
NTN (Neo4j):
  Protocol: Bolt Protocol
  Connection Pooling: Yes, with min/max settings
  Transaction Batching: Used for relationship operations
  Result Streaming: Enabled for large result sets
```

## 3. Interface Patterns

### 3.1 Command Query Responsibility Segregation (CQRS)

The NCA system implements CQRS to separate read and write operations:

#### 3.1.1 Command (Write) Interfaces

```yaml
Characteristics:
  - Optimized for data consistency and integrity
  - Strict validation rules
  - Transaction support
  - Event generation
  - Idempotency guarantees

Primary Endpoints:
  - POST /api/v1/memories
  - PATCH /api/v1/memories/{memoryId}
  - DELETE /api/v1/memories/{memoryId}
  - POST /api/v1/tubules
  - PATCH /api/v1/memories/{memoryId}/health
```

**Command Handler Pattern:**

```typescript
interface CommandHandler<T extends Command, R> {
  execute(command: T): Promise<R>;
  validate(command: T): Promise<ValidationResult>;
}

class CreateMemoryCommandHandler implements CommandHandler<CreateMemoryCommand, Memory> {
  constructor(
    private memoryRepository: MemoryRepository,
    private embeddingService: EmbeddingService,
    private eventPublisher: EventPublisher
  ) {}
  
  async validate(command: CreateMemoryCommand): Promise<ValidationResult> {
    // Validation logic
    return { isValid: true };
  }
  
  async execute(command: CreateMemoryCommand): Promise<Memory> {
    // Validation
    const validationResult = await this.validate(command);
    if (!validationResult.isValid) {
      throw new ValidationError(validationResult.errors);
    }
    
    // Processing
    const embedding = await this.embeddingService.generateEmbedding(command.content);
    const memory = await this.memoryRepository.create({
      ...command,
      embedding,
      tier: 'STM',
      createdAt: new Date(),
      updatedAt: new Date(),
      lastAccessedAt: new Date(),
      accessCount: 0,
      healthScore: this.calculateInitialHealth(command)
    });
    
    // Event publishing
    await this.eventPublisher.publish('memory.created', memory);
    
    return memory;
  }
  
  private calculateInitialHealth(command: CreateMemoryCommand): number {
    // Health calculation logic
    return 85;
  }
}
```

#### 3.1.2 Query (Read) Interfaces

```yaml
Characteristics:
  - Optimized for performance and scalability
  - Denormalized data structures
  - Caching support
  - Read-specific indexes
  - Pagination and filtering

Primary Endpoints:
  - GET /api/v1/memories/{memoryId}
  - GET /api/v1/memories
  - POST /api/v1/memories/search
  - GET /api/v1/memories/{memoryId}/relationships
  - GET /api/v1/memories/{memoryId}/graph
```

**Query Handler Pattern:**

```typescript
interface QueryHandler<T extends Query, R> {
  execute(query: T): Promise<R>;
}

class SearchMemoriesQueryHandler implements QueryHandler<SearchMemoriesQuery, SearchMemoriesResult> {
  constructor(
    private searchService: SearchService,
    private cacheService: CacheService
  ) {}
  
  async execute(query: SearchMemoriesQuery): Promise<SearchMemoriesResult> {
    // Cache check
    const cacheKey = this.generateCacheKey(query);
    const cachedResult = await this.cacheService.get(cacheKey);
    if (cachedResult) {
      return cachedResult;
    }
    
    // Execute search
    const searchResult = await this.searchService.search({
      queryText: query.query,
      searchType: query.searchType,
      tiers: query.tiers,
      limit: query.limit,
      minRelevance: query.minRelevance,
      includeContent: query.includeContent,
      filters: query.filters
    });
    
    // Cache result
    await this.cacheService.set(cacheKey, searchResult, 60); // 60 second TTL
    
    return searchResult;
  }
  
  private generateCacheKey(query: SearchMemoriesQuery): string {
    // Generate deterministic cache key from query
    return `search:${hash(JSON.stringify(query))}`;
  }
}
```

### 3.2 Event-Driven Architecture

The NCA system uses events for loose coupling between components:

#### 3.2.1 Event Production

```yaml
Event Sources:
  - Memory operations (create, update, delete)
  - Health changes
  - Tier transitions
  - Relationship changes
  - Consolidation processes
  - System configuration changes

Event Structure:
  - Type identifier
  - Timestamp
  - Payload data
  - Metadata (correlation ID, source, etc.)
  - Schema version
```

**Event Publisher Implementation:**

```typescript
interface EventPublisher {
  publish<T>(eventType: string, payload: T, metadata?: EventMetadata): Promise<void>;
}

class RabbitMQEventPublisher implements EventPublisher {
  constructor(
    private connection: amqp.Connection,
    private exchange: string = 'nca.events'
  ) {}
  
  async publish<T>(eventType: string, payload: T, metadata: EventMetadata = {}): Promise<void> {
    const channel = await this.connection.createChannel();
    
    const eventMessage = {
      eventType,
      timestamp: new Date().toISOString(),
      data: payload,
      metadata: {
        eventId: uuidv4(),
        correlationId: metadata.correlationId || uuidv4(),
        source: metadata.source || 'nca-api',
        ...metadata
      }
    };
    
    const routingKey = eventType.replace(/\./g, '/');
    
    await channel.publish(
      this.exchange,
      routingKey,
      Buffer.from(JSON.stringify(eventMessage)),
      {
        contentType: 'application/json',
        persistent: true,
        headers: {
          'x-event-type': eventType,
          'x-event-version': '1.0'
        }
      }
    );
    
    await channel.close();
  }
}
```

#### 3.2.2 Event Consumption

```yaml
Consumer Types:
  - Memory health updaters
  - Tier transition processors
  - Relationship managers
  - Consolidation job schedulers
  - Analytics processors
  - External integrations

Processing Guarantees:
  - At-least-once delivery
  - Idempotent processing
  - Dead-letter queues for failed processing
  - Retry with exponential backoff
```

**Event Consumer Implementation:**

```typescript
interface EventConsumer<T> {
  eventType: string;
  handle(event: Event<T>): Promise<void>;
}

class MemoryHealthUpdateConsumer implements EventConsumer<MemoryAccessedEvent> {
  eventType = 'memory.accessed';
  
  constructor(
    private healthService: HealthService,
    private eventPublisher: EventPublisher
  ) {}
  
  async handle(event: Event<MemoryAccessedEvent>): Promise<void> {
    try {
      // Extract data
      const { memoryId, accessType, contextRelevance } = event.data;
      
      // Process event
      const healthUpdate = await this.healthService.updateHealthAfterAccess(
        memoryId,
        accessType,
        contextRelevance
      );
      
      // Check for tier transition
      if (healthUpdate.tierTransition) {
        await this.eventPublisher.publish('memory.tier.transition.recommended', {
          memoryId,
          currentTier: healthUpdate.currentTier,
          recommendedTier: healthUpdate.recommendedTier,
          healthScore: healthUpdate.newHealthScore,
          reason: 'Health score change after access'
        }, {
          correlationId: event.metadata.correlationId
        });
      }
    } catch (error) {
      // Error handling
      console.error(`Error processing memory.accessed event: ${error.message}`, {
        eventId: event.metadata.eventId,
        memoryId: event.data.memoryId
      });
      
      // Rethrow to trigger retry or DLQ
      throw error;
    }
  }
}
```

### 3.3 Adapter Pattern

The NCA system uses adapters to integrate with different LLM providers and storage backends:

#### 3.3.1 LLM Provider Adapters

```yaml
Supported Providers:
  - OpenAI
  - Anthropic
  - Cohere
  - Hugging Face
  - Custom/Self-hosted models

Adapter Responsibilities:
  - Authentication
  - Request formatting
  - Response parsing
  - Error handling
  - Rate limiting
  - Fallback strategies
```

**LLM Adapter Interface:**

```typescript
interface LLMAdapter {
  getProviderName(): string;
  getSupportedModels(): string[];
  generateEmbedding(text: string, options?: EmbeddingOptions): Promise<number[]>;
  generateCompletion(prompt: string, options?: CompletionOptions): Promise<CompletionResult>;
  generateChat(messages: ChatMessage[], options?: ChatOptions): Promise<ChatResult>;
  estimateTokenCount(text: string): number;
}

class OpenAIAdapter implements LLMAdapter {
  constructor(
    private apiKey: string,
    private defaultModel: string = 'gpt-4',
    private embeddingModel: string = 'text-embedding-ada-002'
  ) {}
  
  getProviderName(): string {
    return 'openai';
  }
  
  getSupportedModels(): string[] {
    return ['gpt-4', 'gpt-3.5-turbo', 'text-embedding-ada-002'];
  }
  
  async generateEmbedding(text: string, options?: EmbeddingOptions): Promise<number[]> {
    const model = options?.model || this.embeddingModel;
    
    const response = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        input: text,
        model
      })
    });
    
    if (!response.ok) {
      throw new Error(`OpenAI embedding error: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result.data[0].embedding;
  }
  
  // Additional methods implementation...
}
```

#### 3.3.2 Storage Adapters

```yaml
Storage Types:
  - STM (Redis, Memcached)
  - MTM (MongoDB, Elasticsearch)
  - LTM (PostgreSQL, Neo4j)
  - Health History (TimescaleDB)
  - Job Queue (RabbitMQ, Kafka)

Adapter Responsibilities:
  - Connection management
  - Query construction
  - Result mapping
  - Transaction handling
  - Error recovery
  - Performance optimization
```

**Storage Adapter Interface:**

```typescript
interface MemoryStorageAdapter<T> {
  getStorageType(): string;
  create(memory: T): Promise<T>;
  findById(id: string): Promise<T | null>;
  update(id: string, updates: Partial<T>): Promise<T>;
  delete(id: string): Promise<boolean>;
  search(query: SearchQuery): Promise<SearchResult<T>>;
  healthCheck(): Promise<HealthStatus>;
}

class RedisSTMAdapter implements MemoryStorageAdapter<STMemory> {
  constructor(
    private redisClient: Redis,
    private searchClient: RediSearch
  ) {}
  
  getStorageType(): string {
    return 'redis-stm';
  }
  
  async create(memory: STMemory): Promise<STMemory> {
    const id = memory.id || `mem_${uuidv4()}`;
    const key = `memory:${id}`;
    
    // Store main memory object
    await this.redisClient.json.set(key, '$', {
      ...memory,
      id,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastAccessedAt: new Date().toISOString()
    });
    
    // Set expiration if specified
    if (memory.expiresAt) {
      const ttlSeconds = Math.floor((new Date(memory.expiresAt).getTime() - Date.now()) / 1000);
      if (ttlSeconds > 0) {
        await this.redisClient.expire(key, ttlSeconds);
      }
    }
    
    return this.findById(id);
  }
  
  async findById(id: string): Promise<STMemory | null> {
    const key = `memory:${id}`;
    const memory = await this.redisClient.json.get(key);
    
    if (!memory) {
      return null;
    }
    
    // Update access metadata
    await this.redisClient.json.set(key, '$.lastAccessedAt', new Date().toISOString());
    await this.redisClient.json.numIncrBy(key, '$.accessCount', 1);
    
    return memory as STMemory;
  }
  
  // Additional methods implementation...
}
```

### 3.4 Strategy Pattern

The NCA system uses strategy patterns for configurable behaviors:

#### 3.4.1 Memory Retrieval Strategies

```yaml
Strategy Types:
  - Semantic (vector similarity)
  - Keyword (text matching)
  - Temporal (time-based)
  - Relational (graph traversal)
  - Hybrid (combined approaches)

Strategy Selection:
  - Query characteristics
  - Available context
  - Performance requirements
  - Tier-specific optimizations
```

**Retrieval Strategy Implementation:**

```typescript
interface MemoryRetrievalStrategy {
  getName(): string;
  retrieve(query: RetrievalQuery, context: RetrievalContext): Promise<RetrievalResult>;
  estimatePerformance(query: RetrievalQuery): PerformanceEstimate;
}

class SemanticRetrievalStrategy implements MemoryRetrievalStrategy {
  constructor(
    private embeddingService: EmbeddingService,
    private storageAdapters: StorageAdapterRegistry
  ) {}
  
  getName(): string {
    return 'semantic';
  }
  
  async retrieve(query: RetrievalQuery, context: RetrievalContext): Promise<RetrievalResult> {
    // Generate embedding for query
    const queryEmbedding = await this.embeddingService.generateEmbedding(query.query);
    
    // Determine which tiers to search
    const tiers = query.tiers || ['STM', 'MTM', 'LTM'];
    
    // Execute vector search across tiers
    const results = await Promise.all(
      tiers.map(async (tier) => {
        const adapter = this.storageAdapters.getAdapterForTier(tier);
        return adapter.search({
          type: 'vector',
          vector: queryEmbedding,
          limit: query.limit || 10,
          minScore: query.minRelevance || 0.7,
          filters: query.filters
        });
      })
    );
    
    // Merge and rank results
    const mergedResults = this.mergeResults(results, query.limit || 10);
    
    return {
      memories: mergedResults,
      metadata: {
        strategy: 'semantic',
        tiers,
        queryEmbeddingModel: this.embeddingService.getModelName(),
        executionTimeMs: Date.now() - context.startTime
      }
    };
  }
  
  estimatePerformance(query: RetrievalQuery): PerformanceEstimate {
    // Estimate performance characteristics
    return {
      expectedLatencyMs: query.tiers?.includes('LTM') ? 200 : 50,
      expectedRelevance: 0.85,
      confidenceScore: 0.9
    };
  }
  
  private mergeResults(results: SearchResult<Memory>[], limit: number): Memory[] {
    // Merge and deduplicate results from different tiers
    // Rank by relevance score
    // Return top results up to limit
    // ...implementation...
    return [];
  }
}
```

#### 3.4.2 Health Calculation Strategies

```yaml
Strategy Types:
  - Standard (balanced approach)
  - Recency-focused (emphasizes recent access)
  - Importance-focused (emphasizes flagged importance)
  - Relevance-focused (emphasizes contextual relevance)
  - Custom (configurable weights)

Strategy Selection:
  - Memory tier
  - Content type
  - User preferences
  - Application domain
```

**Health Calculation Strategy Implementation:**

```typescript
interface HealthCalculationStrategy {
  getName(): string;
  calculateHealth(memory: Memory, context: HealthContext): Promise<HealthResult>;
  getDecayRate(tier: MemoryTier): number;
}

class StandardHealthCalculationStrategy implements HealthCalculationStrategy {
  constructor(
    private configService: ConfigService
  ) {}
  
  getName(): string {
    return 'standard';
  }
  
  async calculateHealth(memory: Memory, context: HealthContext): Promise<HealthResult> {
    // Get tier-specific configuration
    const config = this.configService.getHealthConfig(memory.tier);
    
    // Calculate recency factor
    const recencyFactor = this.calculateRecencyFactor(
      memory.lastAccessedAt,
      config.recencyDecayRate
    );
    
    // Calculate access frequency factor
    const accessFrequency = this.normalizeAccessFrequency(
      memory.accessCount,
      memory.createdAt,
      config.accessFrequencyNormalization
    );
    
    // Calculate relevance score
    const relevanceScore = context.relevanceScore || memory.relevanceScore || 50;
    
    // Calculate importance factor
    const importanceFactor = memory.importanceFlag / 10; // Normalize to 0-1
    
    // Calculate composite health score
    const baseHealthScore = Math.round(
      recencyFactor * config.weights.recency +
      accessFrequency * config.weights.accessFrequency +
      relevanceScore / 100 * config.weights.relevance +
      importanceFactor * config.weights.importance
    );
    
    // Determine tier transition recommendations
    const tierTransition = this.evaluateTierTransition(
      memory.tier,
      baseHealthScore,
      config.promotionThreshold,
      config.demotionThreshold,
      config.forgettingThreshold
    );
    
    return {
      memoryId: memory.id,
      baseHealthScore: Math.min(100, Math.max(0, baseHealthScore)),
      healthFactors: {
        recencyFactor,
        accessFrequency,
        relevanceScore,
        importanceFactor
      },
      tierTransition,
      calculatedAt: new Date().toISOString()
    };
  }
  
  getDecayRate(tier: MemoryTier): number {
    const config = this.configService.getHealthConfig(tier);
    return config.baseDecayRate;
  }
  
  private calculateRecencyFactor(lastAccessedAt: string, decayRate: number): number {
    const hoursSinceAccess = (Date.now() - new Date(lastAccessedAt).getTime()) / (1000 * 60 * 60);
    return Math.exp(-decayRate * hoursSinceAccess);
  }
  
  private normalizeAccessFrequency(accessCount: number, createdAt: string, normalization: number): number {
    const daysSinceCreation = (Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60 * 24);
    const dailyRate = accessCount / Math.max(1, daysSinceCreation);
    return Math.min(1, dailyRate / normalization);
  }
  
  private evaluateTierTransition(
    currentTier: MemoryTier,
    healthScore: number,
    promotionThreshold: number,
    demotionThreshold: number,
    forgettingThreshold: number
  ): TierTransition | null {
    if (currentTier === 'STM' && healthScore >= promotionThreshold) {
      return {
        recommendedTier: 'MTM',
        reason: 'Health score exceeds promotion threshold',
        confidence: (healthScore - promotionThreshold) / (100 - promotionThreshold)
      };
    }
    
    if (currentTier === 'MTM' && healthScore >= promotionThreshold) {
      return {
        recommendedTier: 'LTM',
        reason: 'Health score exceeds promotion threshold',
        confidence: (healthScore - promotionThreshold) / (100 - promotionThreshold)
      };
    }
    
    if (currentTier === 'MTM' && healthScore <= demotionThreshold) {
      return {
        recommendedTier: 'STM',
        reason: 'Health score below demotion threshold',
        confidence: (demotionThreshold - healthScore) / demotionThreshold
      };
    }
    
    if (currentTier === 'LTM' && healthScore <= demotionThreshold) {
      return {
        recommendedTier: 'MTM',
        reason: 'Health score below demotion threshold',
        confidence: (demotionThreshold - healthScore) / demotionThreshold
      };
    }
    
    if (currentTier === 'STM' && healthScore <= forgettingThreshold) {
      return {
        recommendedTier: null, // Indicates forgetting
        reason: 'Health score below forgetting threshold',
        confidence: (forgettingThreshold - healthScore) / forgettingThreshold
      };
    }
    
    return null;
  }
}
```

### 3.5 Facade Pattern

The NCA system uses facades to simplify complex subsystems:

#### 3.5.1 Memory Management Facade

```typescript
class MemoryManagementFacade {
  constructor(
    private memoryCommandHandlers: CommandHandlerRegistry,
    private memoryQueryHandlers: QueryHandlerRegistry,
    private healthService: HealthService,
    private relationshipService: RelationshipService,
    private eventPublisher: EventPublisher
  ) {}
  
  async createMemory(request: CreateMemoryRequest): Promise<Memory> {
    // Create memory
    const createCommand = this.mapToCreateCommand(request);
    const memory = await this.memoryCommandHandlers.get(CreateMemoryCommand).execute(createCommand);
    
    // Establish initial relationships if specified
    if (request.relatedMemoryIds && request.relatedMemoryIds.length > 0) {
      await Promise.all(
        request.relatedMemoryIds.map(relatedId => 
          this.relationshipService.createRelationship({
            sourceMemoryId: memory.id,
            targetMemoryId: relatedId,
            relationshipType: 'RELATED',
            strength: 0.5,
            bidirectional: true
          })
        )
      );
    }
    
    // Publish event
    await this.eventPublisher.publish('memory.created', memory);
    
    return memory;
  }
  
  async findSimilarMemories(memoryId: string, options: SimilarityOptions = {}): Promise<Memory[]> {
    // Get the memory
    const memory = await this.memoryQueryHandlers.get(GetMemoryQuery).execute({ memoryId });
    if (!memory) {
      throw new NotFoundError(`Memory with ID ${memoryId} not found`);
    }
    
    // Find similar memories via vector search
    const searchQuery = {
      vector: memory.embedding,
      excludeIds: [memoryId],
      limit: options.limit || 10,
      minRelevance: options.minRelevance || 0.7,
      tiers: options.tiers || ['STM', 'MTM', 'LTM']
    };
    
    const searchResult = await this.memoryQueryHandlers.get(VectorSearchQuery).execute(searchQuery);
    
    // Update relationships based on similarity
    if (options.updateRelationships !== false) {
      await Promise.all(
        searchResult.memories.map(similar => 
          this.relationshipService.createOrUpdateRelationship({
            sourceMemoryId: memoryId,
            targetMemoryId: similar.id,
            relationshipType: 'SIMILAR',
            strength: similar.relevanceScore,
            bidirectional: true
          })
        )
      );
    }
    
    return searchResult.memories;
  }
  
  // Additional facade methods...
  
  private mapToCreateCommand(request: CreateMemoryRequest): CreateMemoryCommand {
    // Map API request to command
    return {
      content: request.content,
      contentType: request.contentType,
      source: request.source,
      conversationId: request.conversationId,
      importance: request.importance,
      tags: request.tags,
      metadata: request.metadata
    };
  }
}
```

#### 3.5.2 LLM Integration Facade

```typescript
class LLMIntegrationFacade {
  constructor(
    private memoryService: MemoryManagementFacade,
    private contextService: ContextService,
    private llmAdapterRegistry: LLMAdapterRegistry,
    private configService: ConfigService
  ) {}
  
  async retrieveContextForLLM(request: RetrieveContextRequest): Promise<LLMContext> {
    // Get configuration
    const config = this.configService.getLLMIntegrationConfig();
    
    // Create context container
    const contextId = `ctx_${uuidv4()}`;
    const context: LLMContext = {
      id: contextId,
      llmProvider: request.llmProvider || config.defaultProvider,
      maxTokens: request.maxTokens || config.defaultMaxTokens,
      usedTokens: 0,
      activeMemories: [],
      recentlyEvictedMemories: [],
      relevanceThreshold: request.relevanceThreshold || config.defaultRelevanceThreshold,
      recencyWeight: request.recencyWeight || config.defaultRecencyWeight,
      importanceWeight: request.importanceWeight || config.defaultImportanceWeight,
      retrievalLatencyMs: 0,
      injectionLatencyMs: 0
    };
    
    // Start timing
    const retrievalStart = Date.now();
    
    // Retrieve relevant memories
    const memories = await this.memoryService.searchMemories({
      query: request.query,
      searchType: request.retrievalStrategy || 'HYBRID',
      tiers: request.includeTiers || ['STM', 'MTM'],
      limit: config.maxMemoriesPerContext,
      minRelevance: context.relevanceThreshold,
      filters: {
        tags: request.includeTags,
        excludeTags: request.excludeTags,
        timeRange: request.timeRange
      }
    });
    
    // Calculate token counts and select memories to include
    const llmAdapter = this.llmAdapterRegistry.getAdapter(context.llmProvider);
    let remainingTokens = context.maxTokens;
    
    const selectedMemories = [];
    for (const memory of memories.results) {
      const tokenCount = llmAdapter.estimateTokenCount(memory.content);
      if (tokenCount <= remainingTokens) {
        selectedMemories.push({
          memoryId: memory.id,
          contextRelevance: memory.relevanceScore,
          tokenCount,
          injectedAt: new Date().toISOString(),
          source: 'RETRIEVAL'
        });
        remainingTokens -= tokenCount;
      } else {
        context.recentlyEvictedMemories.push(memory.id);
      }
    }
    
    context.activeMemories = selectedMemories;
    context.usedTokens = context.maxTokens - remainingTokens;
    context.retrievalLatencyMs = Date.now() - retrievalStart;
    
    // Format context for LLM
    const injectionStart = Date.now();
    const formattedContext = this.formatContextForLLM(selectedMemories, request.formatTemplate);
    context.injectionLatencyMs = Date.now() - injectionStart;
    
    // Store context for later reference
    await this.contextService.saveContext(context);
    
    return {
      ...context,
      formattedContext
    };
  }
  
  async storeMemoryFromLLMOutput(request: StoreLLMOutputRequest): Promise<Memory> {
    // Create memory from LLM output
    const memory = await this.memoryService.createMemory({
      content: request.content,
      contentType: 'TEXT',
      source: 'LLM_OUTPUT',
      conversationId: request.conversationId,
      importance: request.importance || 5,
      tags: request.tags || [],
      metadata: {
        llmProvider: request.llmProvider,
        llmModel: request.llmModel,
        contextId: request.contextId,
        relatedUserQuery: request.relatedUserQuery
      }
    });
    
    // If context ID is provided, update context with this memory
    if (request.contextId) {
      await this.contextService.addMemoryToContext(request.contextId, {
        memoryId: memory.id,
        contextRelevance: 1.0, // Maximum relevance for LLM's own output
        tokenCount: this.llmAdapterRegistry.getAdapter(request.llmProvider).estimateTokenCount(request.content),
        injectedAt: new Date().toISOString(),
        source: 'LLM_OUTPUT'
      });
    }
    
    return memory;
  }
  
  private formatContextForLLM(memories: ContextMemory[], template?: string): string {
    // Default template if none provided
    const contextTemplate = template || this.configService.getLLMIntegrationConfig().defaultContextTemplate;
    
    // Get full memory objects
    const memoryContents = memories.map(m => this.memoryService.getMemory(m.memoryId).content);
    
    // Apply template
    return contextTemplate
      .replace('{{memories}}', memoryContents.join('\n\n'))
      .replace('{{memory_count}}', memories.length.toString());
  }
}
```

## 4. Error Handling

### 4.1 Error Classification

The NCA system classifies errors into the following categories:

```yaml
ValidationErrors:
  - Invalid input format
  - Missing required fields
  - Value out of allowed range
  - Logical constraints violated
  
ResourceErrors:
  - Resource not found
  - Resource already exists
  - Resource locked
  - Resource in invalid state
  
AuthenticationErrors:
  - Invalid credentials
  - Expired token
  - Missing token
  - Invalid token format
  
AuthorizationErrors:
  - Insufficient permissions
  - Action forbidden
  - Rate limit exceeded
  - Quota exceeded
  
SystemErrors:
  - Database connection failure
  - External service unavailable
  - Internal processing error
  - Unexpected exception
  
IntegrationErrors:
  - LLM provider error
  - Embedding generation failure
  - External API failure
  - Protocol mismatch
```

### 4.2 Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "MEMORY_NOT_FOUND",
    "message": "Memory with ID mem_123abc could not be found",
    "details": "The requested memory may have been deleted or never existed",
    "status": 404,
    "timestamp": "2023-06-15T18:30:00Z",
    "requestId": "req_456def",
    "path": "/api/v1/memories/mem_123abc",
    "validationErrors": [
      {
        "field": "memoryId",
        "message": "Invalid format",
        "code": "INVALID_FORMAT"
      }
    ]
  },
  "documentation": "https://docs.nca-system.com/errors/MEMORY_NOT_FOUND"
}
```

### 4.3 Error Handling Strategies

#### 4.3.1 API Layer Error Handling

```typescript
// Global error handler middleware
function errorHandlerMiddleware(err: any, req: Request, res: Response, next: NextFunction) {
  // Generate request ID if not present
  const requestId = req.headers['x-request-id'] || uuidv4();
  
  // Log error with context
  logger.error(`Error processing request: ${err.message}`, {
    requestId,
    path: req.path,
    method: req.method,
    statusCode: err.statusCode || 500,
    errorCode: err.code,
    stack: err.stack
  });
  
  // Map error to appropriate response
  let statusCode = 500;
  let errorCode = 'INTERNAL_ERROR';
  let errorMessage = 'An unexpected error occurred';
  let errorDetails = undefined;
  let validationErrors = undefined;
  
  if (err instanceof ValidationError) {
    statusCode = 400;
    errorCode = err.code || 'VALIDATION_ERROR';
    errorMessage = err.message;
    validationErrors = err.validationErrors;
  } else if (err instanceof ResourceNotFoundError) {
    statusCode = 404;
    errorCode = err.code || 'RESOURCE_NOT_FOUND';
    errorMessage = err.message;
  } else if (err instanceof AuthenticationError) {
    statusCode = 401;
    errorCode = err.code || 'AUTHENTICATION_ERROR';
    errorMessage = err.message;
  } else if (err instanceof AuthorizationError) {
    statusCode = 403;
    errorCode = err.code || 'AUTHORIZATION_ERROR';
    errorMessage = err.message;
  } else if (err instanceof RateLimitError) {
    statusCode = 429;
    errorCode = 'RATE_LIMIT_EXCEEDED';
    errorMessage = err.message;
    // Add retry-after header
    res.set('Retry-After', err.retryAfter.toString());
  } else if (err instanceof IntegrationError) {
    statusCode = 502;
    errorCode = err.code || 'INTEGRATION_ERROR';
    errorMessage = err.message;
    errorDetails = err.details;
  }
  
  // Send error response
  res.status(statusCode).json({
    error: {
      code: errorCode,
      message: errorMessage,
      details: errorDetails,
      status: statusCode,
      timestamp: new Date().toISOString(),
      requestId,
      path: req.path,
      validationErrors
    },
    documentation: `https://docs.nca-system.com/errors/${errorCode}`
  });
}
```

#### 4.3.2 Service Layer Error Handling

```typescript
class MemoryService {
  constructor(
    private memoryRepository: MemoryRepository,
    private healthService: HealthService,
    private embeddingService: EmbeddingService
  ) {}
  
  async createMemory(data: CreateMemoryData): Promise<Memory> {
    try {
      // Validate input
      this.validateMemoryData(data);
      
      // Generate embedding
      let embedding;
      try {
        embedding = await this.embeddingService.generateEmbedding(data.content);
      } catch (error) {
        throw new IntegrationError(
          'Failed to generate embedding for memory content',
          'EMBEDDING_GENERATION_FAILED',
          { cause: error }
        );
      }
      
      // Create memory
      const memory = await this.memoryRepository.create({
        ...data,
        embedding,
        tier: 'STM',
        createdAt: new Date(),
        updatedAt: new Date(),
        lastAccessedAt: new Date(),
        accessCount: 0
      });
      
      // Initialize health
      await this.healthService.initializeHealth(memory.id);
      
      return memory;
    } catch (error) {
      // Rethrow known errors
      if (
        error instanceof ValidationError ||
        error instanceof IntegrationError ||
        error instanceof ResourceError
      ) {
        throw error;
      }
      
      // Log and wrap unknown errors
      logger.error(`Unexpected error in createMemory: ${error.message}`, {
        service: 'MemoryService',
        method: 'createMemory',
        error
      });
      
      throw new SystemError(
        'Failed to create memory due to an internal error',
        'MEMORY_CREATION_FAILED',
        { cause: error }
      );
    }
  }
  
  private validateMemoryData(data: CreateMemoryData): void {
    const errors = [];
    
    if (!data.content) {
      errors.push({
        field: 'content',
        message: 'Content is required',
        code: 'REQUIRED_FIELD'
      });
    }
    
    if (data.content && data.content.length > 10000) {
      errors.push({
        field: 'content',
        message: 'Content exceeds maximum length of 10000 characters',
        code: 'FIELD_TOO_LONG'
      });
    }
    
    if (!data.contentType) {
      errors.push({
        field: 'contentType',
        message: 'Content type is required',
        code: 'REQUIRED_FIELD'
      });
    }
    
    if (data.importance !== undefined && (data.importance < 0 || data.importance > 10)) {
      errors.push({
        field: 'importance',
        message: 'Importance must be between 0 and 10',
        code: 'VALUE_OUT_OF_RANGE'
      });
    }
    
    if (errors.length > 0) {
      throw new ValidationError(
        'Invalid memory data',
        'INVALID_MEMORY_DATA',
        errors
      );
    }
  }
}
```

#### 4.3.3 Database Error Handling

```typescript
class PostgresLTMRepository implements MemoryRepository<LTMemory> {
  constructor(
    private pool: Pool,
    private retryConfig: RetryConfig = {
      maxRetries: 3,
      initialDelayMs: 100,
      maxDelayMs: 1000
    }
  ) {}
  
  async findById(id: string): Promise<LTMemory | null> {
    return this.withRetry(async () => {
      const client = await this.pool.connect();
      try {
        const result = await client.query(
          'SELECT * FROM long_term_memories WHERE memory_id = $1',
          [id]
        );
        
        if (result.rows.length === 0) {
          return null;
        }
        
        // Update access metadata
        await client.query(
          'UPDATE long_term_memories SET last_accessed_at = NOW(), access_count = access_count + 1 WHERE memory_id = $1',
          [id]
        );
        
        return this.mapRowToMemory(result.rows[0]);
      } catch (error) {
        this.handleDatabaseError(error, 'findById', { id });
      } finally {
        client.release();
      }
    });
  }
  
  private async withRetry<T>(operation: () => Promise<T>): Promise<T> {
    let lastError;
    let delay = this.retryConfig.initialDelayMs;
    
    for (let attempt = 1; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        
        // Only retry on connection or transient errors
        if (!this.isRetryableError(error)) {
          throw error;
        }
        
        // Log retry attempt
        logger.warn(`Database operation failed, retrying (${attempt}/${this.retryConfig.maxRetries})`, {
          error: error.message,
          attempt,
          delay
        });
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Exponential backoff with jitter
        delay = Math.min(
          delay * 2 * (0.9 + Math.random() * 0.2),
          this.retryConfig.maxDelayMs
        );
      }
    }
    
    // If we get here, all retries failed
    throw lastError;
  }
  
  private isRetryableError(error: any): boolean {
    // PostgreSQL error codes for connection and transient errors
    const retryableCodes = [
      '08000', // connection_exception
      '08003', // connection_does_not_exist
      '08006', // connection_failure
      '08001', // sqlclient_unable_to_establish_sqlconnection
      '08004', // sqlserver_rejected_establishment_of_sqlconnection
      '40001', // serialization_failure
      '40P01', // deadlock_detected
      '55P03', // lock_not_available
      '57P01', // admin_shutdown
      '57P02', // crash_shutdown
      '57P03'  // cannot_connect_now
    ];
    
    return error.code && retryableCodes.includes(error.code);
  }
  
  private handleDatabaseError(error: any, operation: string, params: any): never {
    // Log detailed error
    logger.error(`Database error in ${operation}`, {
      operation,
      params,
      errorCode: error.code,
      errorMessage: error.message,
      detail: error.detail,
      hint: error.hint,
      position: error.position
    });
    
    // Map to appropriate error type
    if (error.code === '23505') { // unique_violation
      throw new ResourceError(
        'Resource already exists',
        'RESOURCE_ALREADY_EXISTS',
        { cause: error }
      );
    }
    
    if (error.code === '23503') { // foreign_key_violation
      throw new ResourceError(
        'Referenced resource does not exist',
        'REFERENCED_RESOURCE_NOT_FOUND',
        { cause: error }
      );
    }
    
    if (error.code === '42P01') { // undefined_table
      throw new SystemError(
        'Database schema error',
        'DATABASE_SCHEMA_ERROR',
        { cause: error }
      );
    }
    
    // Default to system error
    throw new SystemError(
      'Database operation failed',
      'DATABASE_ERROR',
      { cause: error }
    );
  }
  
  private mapRowToMemory(row: any): LTMemory {
    // Map database row to memory object
    return {
      id: row.memory_id,
      content: row.content,
      contentType: row.content_type,
      createdAt: row.created_at.toISOString(),
      updatedAt: row.updated_at.toISOString(),
      lastAccessedAt: row.last_accessed_at.toISOString(),
      accessCount: row.access_count,
      baseHealthScore: row.base_health_score,
      relevanceScore: row.relevance_score,
      importanceFlag: row.importance_flag,
      tags: row.tags,
      stabilityScore: row.stability_score,
      abstractionLevel: row.abstraction_level,
      lastReinforcedAt: row.last_reinforced_at?.toISOString(),
      factuality: row.factuality,
      domainCategories: row.domain_categories,
      isCoreConcept: row.is_core_concept
    };
  }
}
```

### 4.4 Circuit Breaker Pattern

The NCA system implements circuit breakers for external dependencies:

```typescript
class CircuitBreaker {
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private successCount: number = 0;
  
  constructor(
    private readonly service: string,
    private readonly failureThreshold: number = 5,
    private readonly resetTimeoutMs: number = 30000,
    private readonly halfOpenSuccessThreshold: number = 3,
    private readonly onStateChange?: (service: string, oldState: string, newState: string) => void
  ) {}
  
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime >= this.resetTimeoutMs) {
        this.transitionTo('HALF_OPEN');
      } else {
        throw new ServiceUnavailableError(
          `Service ${this.service} is unavailable`,
          'CIRCUIT_OPEN'
        );
      }
    }
    
    try {
      const result = await operation();
      
      if (this.state === 'HALF_OPEN') {
        this.successCount++;
        if (this.successCount >= this.halfOpenSuccessThreshold) {
          this.transitionTo('CLOSED');
        }
      } else {
        // Reset failure count on success in CLOSED state
        this.failureCount = 0;
      }
      
      return result;
    } catch (error) {
      this.lastFailureTime = Date.now();
      this.failureCount++;
      
      if (this.state === 'CLOSED' && this.failureCount >= this.failureThreshold) {
        this.transitionTo('OPEN');
      } else if (this.state === 'HALF_OPEN') {
        this.transitionTo('OPEN');
      }
      
      throw error;
    }
  }
  
  private transitionTo(newState: 'CLOSED' | 'OPEN' | 'HALF_OPEN'): void {
    const oldState = this.state;
    this.state = newState;
    
    if (newState === 'CLOSED') {
      this.failureCount = 0;
      this.successCount = 0;
    } else if (newState === 'HALF_OPEN') {
      this.successCount = 0;
    }
    
    // Log state change
    logger.info(`Circuit breaker for ${this.service} transitioned from ${oldState} to ${newState}`);
    
    // Notify state change if callback provided
    if (this.onStateChange) {
      this.onStateChange(this.service, oldState, newState);
    }
  }
  
  getState(): string {
    return this.state;
  }
  
  getMetrics(): CircuitBreakerMetrics {
    return {
      service: this.service,
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime > 0 ? new Date(this.lastFailureTime).toISOString() : null,
      timeInCurrentState: this.lastFailureTime > 0 ? Date.now() - this.lastFailureTime : 0
    };
  }
}

// Usage example
class OpenAIEmbeddingService implements EmbeddingService {
  private circuitBreaker: CircuitBreaker;
  
  constructor(
    private apiKey: string,
    private model: string = 'text-embedding-ada-002',
    private circuitBreakerConfig: CircuitBreakerConfig = {
      failureThreshold: 5,
      resetTimeoutMs: 30000,
      halfOpenSuccessThreshold: 3
    }
  ) {
    this.circuitBreaker = new CircuitBreaker(
      'openai-embedding',
      circuitBreakerConfig.failureThreshold,
      circuitBreakerConfig.resetTimeoutMs,
      circuitBreakerConfig.halfOpenSuccessThreshold,
      this.onCircuitStateChange.bind(this)
    );
  }
  
  async generateEmbedding(text: string): Promise<number[]> {
    return this.circuitBreaker.execute(async () => {
      try {
        const response = await fetch('https://api.openai.com/v1/embeddings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`
          },
          body: JSON.stringify({
            input: text,
            model: this.model
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new IntegrationError(
            `OpenAI API error: ${response.statusText}`,
            'OPENAI_API_ERROR',
            {
              statusCode: response.status,
              errorData
            }
          );
        }
        
        const result = await response.json();
        return result.data[0].embedding;
      } catch (error) {
        if (error instanceof IntegrationError) {
          throw error;
        }
        
        throw new IntegrationError(
          `Failed to generate embedding: ${error.message}`,
          'EMBEDDING_GENERATION_FAILED',
          { cause: error }
        );
      }
    });
  }
  
  private onCircuitStateChange(service: string, oldState: string, newState: string): void {
    if (newState === 'OPEN') {
      // Send alert
      logger.warn(`Circuit breaker for ${service} opened due to multiple failures`);
      
      // Publish event
      eventPublisher.publish('system.integration.degraded', {
        service,
        previousState: oldState,
        newState,
        timestamp: new Date().toISOString()
      });
    } else if (oldState === 'OPEN' && newState === 'CLOSED') {
      // Service recovered
      logger.info(`Circuit breaker for ${service} closed, service recovered`);
      
      // Publish event
      eventPublisher.publish('system.integration.recovered', {
        service,
        previousState: oldState,
        newState,
        timestamp: new Date().toISOString()
      });
    }
  }
}
```

### 4.5 Graceful Degradation

The NCA system implements graceful degradation strategies:

```typescript
class MemoryRetrievalService {
  constructor(
    private stmAdapter: MemoryStorageAdapter<STMemory>,
    private mtmAdapter: MemoryStorageAdapter<MTMemory>,
    private ltmAdapter: MemoryStorageAdapter<LTMemory>,
    private embeddingService: EmbeddingService,
    private configService: ConfigService,
    private healthCheckService: HealthCheckService
  ) {}
  
  async retrieveMemories(query: RetrievalQuery): Promise<RetrievalResult> {
    // Check component health
    const healthStatus = await this.healthCheckService.getComponentsHealth();
    
    // Determine available tiers based on health
    const availableTiers = this.getAvailableTiers(query.tiers || ['STM', 'MTM', 'LTM'], healthStatus);
    
    // If no tiers are available, fail gracefully
    if (availableTiers.length === 0) {
      logger.error('All memory tiers are unavailable, retrieval failed');
      throw new SystemError(
        'Memory retrieval is currently unavailable',
        'RETRIEVAL_UNAVAILABLE'
      );
    }
    
    // Log if some tiers are unavailable
    if (availableTiers.length < (query.tiers || ['STM', 'MTM', 'LTM']).length) {
      logger.warn(`Some memory tiers are unavailable, proceeding with: ${availableTiers.join(', ')}`);
    }
    
    // Determine retrieval strategy based on available components
    let retrievalStrategy = query.searchType || 'SEMANTIC';
    let queryEmbedding = null;
    
    // If semantic search is requested but embedding service is down, fall back to keyword search
    if (retrievalStrategy === 'SEMANTIC' && !healthStatus.embeddingService.healthy) {
      logger.warn('Embedding service unavailable, falling back to keyword search');
      retrievalStrategy = 'KEYWORD';
    }
    
    // Generate embedding if needed and available
    if (retrievalStrategy === 'SEMANTIC' || retrievalStrategy === 'HYBRID') {
      try {
        queryEmbedding = await this.embeddingService.generateEmbedding(query.query);
      } catch (error) {
        logger.warn(`Failed to generate embedding, falling back to keyword search: ${error.message}`);
        retrievalStrategy = 'KEYWORD';
      }
    }
    
    // Execute retrieval with available tiers and strategy
    const results = await this.executeRetrieval(
      query,
      availableTiers,
      retrievalStrategy,
      queryEmbedding
    );
    
    return {
      memories: results,
      metadata: {
        requestedTiers: query.tiers || ['STM', 'MTM', 'LTM'],
        availableTiers,
        requestedStrategy: query.searchType || 'SEMANTIC',
        actualStrategy: retrievalStrategy,
        degraded: availableTiers.length < (query.tiers || ['STM', 'MTM', 'LTM']).length || 
                 retrievalStrategy !== (query.searchType || 'SEMANTIC')
      }
    };
  }
  
  private getAvailableTiers(requestedTiers: MemoryTier[], healthStatus: ComponentsHealth): MemoryTier[] {
    return requestedTiers.filter(tier => {
      switch (tier) {
        case 'STM':
          return healthStatus.stmStorage.healthy;
        case 'MTM':
          return healthStatus.mtmStorage.healthy;
        case 'LTM':
          return healthStatus.ltmStorage.healthy;
        default:
          return false;
      }
    });
  }
  
  private async executeRetrieval(
    query: RetrievalQuery,
    availableTiers: MemoryTier[],
    strategy: SearchType,
    embedding: number[] | null
  ): Promise<Memory[]> {
    // Execute search based on strategy
    const tierResults = await Promise.allSettled(
      availableTiers.map(tier => this.searchTier(tier, query, strategy, embedding))
    );
    
    // Collect successful results
    const successfulResults = tierResults
      .filter((result): result is PromiseFulfilledResult<Memory[]> => result.status === 'fulfilled')
      .map(result => result.value)
      .flat();
    
    // Log failed tier searches
    tierResults
      .filter((result): result is PromiseRejectedResult => result.status === 'rejected')
      .forEach((result, index) => {
        logger.error(`Search failed for tier ${availableTiers[index]}: ${result.reason.message}`);
      });
    
    // Deduplicate and rank results
    return this.rankAndDeduplicate(successfulResults, query.limit || 10);
  }
  
  private async searchTier(
    tier: MemoryTier,
    query: RetrievalQuery,
    strategy: SearchType,
    embedding: number[] | null
  ): Promise<Memory[]> {
    const adapter = this.getAdapterForTier(tier);
    
    const searchQuery: StorageSearchQuery = {
      limit: query.limit || 10,
      filters: query.filters || {}
    };
    
    if (strategy === 'SEMANTIC' || strategy === 'HYBRID') {
      searchQuery.vector = embedding;
      searchQuery.minScore = query.minRelevance || 0.7;
    }
    
    if (strategy === 'KEYWORD' || strategy === 'HYBRID') {
      searchQuery.text = query.query;
    }
    
    return adapter.search(searchQuery);
  }
  
  private getAdapterForTier(tier: MemoryTier): MemoryStorageAdapter<any> {
    switch (tier) {
      case 'STM':
        return this.stmAdapter;
      case 'MTM':
        return this.mtmAdapter;
      case 'LTM':
        return this.ltmAdapter;
      default:
        throw new Error(`Unknown tier: ${tier}`);
    }
  }
  
  private rankAndDeduplicate(memories: Memory[], limit: number): Memory[] {
    // Remove duplicates by ID
    const uniqueMemories = Array.from(
      new Map(memories.map(memory => [memory.id, memory])).values()
    );
    
    // Sort by relevance score
    const sortedMemories = uniqueMemories.sort((a, b) => {
      // Primary sort by relevance score
      const relevanceDiff = (b.relevanceScore || 0) - (a.relevanceScore || 0);
      if (relevanceDiff !== 0) return relevanceDiff;
      
      // Secondary sort by health score
      const healthDiff = (b.healthScore || 0) - (a.healthScore || 0);
      if (healthDiff !== 0) return healthDiff;
      
      // Tertiary sort by recency
      return new Date(b.lastAccessedAt).getTime() - new Date(a.lastAccessedAt).getTime();
    });
    
    // Return top results
    return sortedMemories.slice(0, limit);
  }
}
```

## 5. Versioning Strategy

### 5.1 API Versioning

The NCA system implements a comprehensive API versioning strategy:

```yaml
VersioningApproach: URI Path Versioning
Format: /api/v{major}/resource
CurrentVersion: v1
SupportPolicy:
  - Support at least 2 major versions simultaneously
  - 6-month deprecation period before removing old versions
  - Clear migration guides for version transitions
```

#### 5.1.1 Version Compatibility

```typescript
// Version compatibility middleware
function apiVersionMiddleware(req: Request, res: Response, next: NextFunction) {
  // Extract version from path
  const versionMatch = req.path.match(/^\/api\/v(\d+)\//);
  if (!versionMatch) {
    return res.status(400).json({
      error: {
        code: 'INVALID_API_VERSION',
        message: 'API version not specified',
        details: 'API requests must include version in the path, e.g., /api/v1/resource'
      }
    });
  }
  
  const version = parseInt(versionMatch[1], 10);
  
  // Check if version is supported
  const supportedVersions = [1, 2]; // Current supported versions
  if (!supportedVersions.includes(version)) {
    return res.status(400).json({
      error: {
        code: 'UNSUPPORTED_API_VERSION',
        message: `API version v${version} is not supported`,
        details: `Supported versions are: ${supportedVersions.map(v => `v${v}`).join(', ')}`
      }
    });
  }
  
  // Check if version is deprecated
  const deprecatedVersions = [1]; // Currently deprecated versions
  if (deprecatedVersions.includes(version)) {
    // Add deprecation headers
    res.set('Deprecation', 'true');
    res.set('Sunset', '2023-12-31'); // End-of-life date
    res.set('Link', '<https://docs.nca-system.com/migration/v1-to-v2>; rel="deprecation"');
  }
  
  // Store version for route handlers
  req.apiVersion = version;
  
  next();
}
```

#### 5.1.2 Version-Specific Routes

```typescript
// Router setup with version-specific handlers
function setupMemoryRoutes(app: Express) {
  // v1 routes
  app.get('/api/v1/memories/:id', (req, res, next) => {
    if (req.apiVersion === 1) {
      return memoryControllerV1.getMemory(req, res, next);
    }
    next();
  });
  
  // v2 routes
  app.get('/api/v2/memories/:id', (req, res, next) => {
    if (req.apiVersion === 2) {
      return memoryControllerV2.getMemory(req, res, next);
    }
    next();
  });
  
  // Shared route handling with version-specific logic
  app.post('/api/v:version/memories', (req, res, next) => {
    if (req.apiVersion === 1) {
      return memoryControllerV1.createMemory(req, res, next);
    } else if (req.apiVersion === 2) {
      return memoryControllerV2.createMemory(req, res, next);
    }
    next();
  });
}
```

### 5.2 Data Schema Versioning

The NCA system implements schema versioning for data evolution:

```yaml
SchemaVersioningApproach: 
  - Explicit schema version field in all data models
  - Migration scripts for version transitions
  - Backward compatibility for reading older schemas
  - Forward compatibility where possible

CompatibilityRules:
  - Never remove fields from existing schemas
  - Always provide defaults for new required fields
  - Use nullable types for new optional fields
  - Maintain semantic meaning of existing fields
```

#### 5.2.1 Schema Version Tracking

```typescript
interface VersionedEntity {
  schemaVersion: number;
}

interface Memory extends VersionedEntity {
  id: string;
  content: string;
  // Other fields...
}

// Version-aware repository
class VersionedMemoryRepository {
  constructor(
    private dataStore: DataStore,
    private migrationService: MigrationService
  ) {}
  
  async findById(id: string): Promise<Memory | null> {
    const rawMemory = await this.dataStore.get(`memory:${id}`);
    if (!rawMemory) {
      return null;
    }
    
    // Check if migration is needed
    if (rawMemory.schemaVersion < CURRENT_SCHEMA_VERSION) {
      return this.migrationService.migrateMemory(
        rawMemory,
        rawMemory.schemaVersion,
        CURRENT_SCHEMA_VERSION
      );
    }
    
    return rawMemory;
  }
  
  async create(memory: Omit<Memory, 'schemaVersion'>): Promise<Memory> {
    // Always create with current schema version
    const versionedMemory: Memory = {
      ...memory,
      schemaVersion: CURRENT_SCHEMA_VERSION
    };
    
    await this.dataStore.set(`memory:${memory.id}`, versionedMemory);
    return versionedMemory;
  }
  
  async update(id: string, updates: Partial<Memory>): Promise<Memory> {
    const existingMemory = await this.findById(id);
    if (!existingMemory) {
      throw new ResourceNotFoundError(`Memory with ID ${id} not found`);
    }
    
    // Ensure we don't downgrade schema version
    if (updates.schemaVersion && updates.schemaVersion < existingMemory.schemaVersion) {
      throw new ValidationError(
        'Cannot downgrade schema version',
        'INVALID_SCHEMA_VERSION'
      );
    }
    
    const updatedMemory = {
      ...existingMemory,
      ...updates,
      // Always update to current schema version on modification
      schemaVersion: CURRENT_SCHEMA_VERSION,
      updatedAt: new Date().toISOString()
    };
    
    await this.dataStore.set(`memory:${id}`, updatedMemory);
    return updatedMemory;
  }
}
```

#### 5.2.2 Schema Migration Service

```typescript
class MigrationService {
  private migrations: Map<string, Migration[]> = new Map();
  
  constructor() {
    // Register migrations for each entity type
    this.registerMigrations('memory', [
      {
        fromVersion: 1,
        toVersion: 2,
        migrate: this.migrateMemoryV1ToV2.bind(this)
      },
      {
        fromVersion: 2,
        toVersion: 3,
        migrate: this.migrateMemoryV2ToV3.bind(this)
      }
    ]);
  }
  
  registerMigrations(entityType: string, migrations: Migration[]): void {
    this.migrations.set(entityType, migrations);
  }
  
  async migrateMemory<T extends VersionedEntity>(
    entity: T,
    fromVersion: number,
    toVersion: number
  ): Promise<T> {
    return this.migrateEntity('memory', entity, fromVersion, toVersion);
  }
  
  private async migrateEntity<T extends VersionedEntity>(
    entityType: string,
    entity: T,
    fromVersion: number,
    toVersion: number
  ): Promise<T> {
    if (fromVersion === toVersion) {
      return entity;
    }
    
    const migrations = this.migrations.get(entityType);
    if (!migrations) {
      throw new Error(`No migrations registered for entity type: ${entityType}`);
    }
    
    let currentEntity = { ...entity };
    let currentVersion = fromVersion;
    
    // Apply migrations in sequence
    while (currentVersion < toVersion) {
      const migration = migrations.find(m => m.fromVersion === currentVersion);
      if (!migration) {
        throw new Error(
          `No migration path from version ${currentVersion} to ${currentVersion + 1} for ${entityType}`
        );
      }
      
      // Apply migration
      currentEntity = await migration.migrate(currentEntity);
      currentVersion = migration.toVersion;
      
      // Update schema version
      currentEntity.schemaVersion = currentVersion;
    }
    
    return currentEntity;
  }
  
  private async migrateMemoryV1ToV2(memory: any): Promise<any> {
    // Example migration from v1 to v2
    return {
      ...memory,
      // Add new fields with defaults
      relevanceScore: memory.relevanceScore || 50,
      // Transform existing fields
      tags: Array.isArray(memory.tags) ? memory.tags : (memory.tags ? [memory.tags] : []),
      // Remove deprecated fields (by not including them)
      // oldField: memory.oldField, // This field is not copied over
    };
  }
  
  private async migrateMemoryV2ToV3(memory: any): Promise<any> {
    // Example migration from v2 to v3
    return {
      ...memory,
      // Add new nested structure
      healthMetadata: {
        baseHealthScore: memory.healthScore || 50,
        recencyFactor: memory.recencyFactor || 1.0,
        relevanceScore: memory.relevanceScore || 50,
        importanceFlag: memory.importanceFlag || 5
      },
      // Keep old fields for backward compatibility
      healthScore: memory.healthScore || 50,
      // Transform data structures
      metadata: {
        ...(memory.metadata || {}),
        migrationDate: new Date().toISOString(),
        previousVersion: 2
      }
    };
  }
}

interface Migration {
  fromVersion: number;
  toVersion: number;
  migrate: <T>(entity: T) => Promise<T>;
}
```

### 5.3 Event Versioning

The NCA system implements versioning for events:

```yaml
EventVersioningApproach:
  - Explicit version field in event schema
  - Event schema registry
  - Backward compatibility for event consumers
  - Event upcasting for handling older versions

CompatibilityRules:
  - Never remove fields from existing event schemas
  - Always provide defaults for new required fields
  - Maintain semantic meaning of existing fields
  - Support multiple versions of event handlers
```

#### 5.3.1 Event Schema Registry

```typescript
class EventSchemaRegistry {
  private schemas: Map<string, Map<number, JsonSchema>> = new Map();
  
  registerSchema(eventType: string, version: number, schema: JsonSchema): void {
    if (!this.schemas.has(eventType)) {
      this.schemas.set(eventType, new Map());
    }
    
    this.schemas.get(eventType).set(version, schema);
  }
  
  getSchema(eventType: string, version: number): JsonSchema | null {
    if (!this.schemas.has(eventType)) {
      return null;
    }
    
    return this.schemas.get(eventType).get(version) || null;
  }
  
  getLatestVersion(eventType: string): number {
    if (!this.schemas.has(eventType)) {
      return 1; // Default to version 1
    }
    
    const versions = Array.from(this.schemas.get(eventType).keys());
    return Math.max(...versions);
  }
  
  validateEvent(event: Event<any>): ValidationResult {
    const { eventType, version } = event;
    const schema = this.getSchema(eventType, version);
    
    if (!schema) {
      return {
        valid: false,
        errors: [{
          message: `No schema registered for event type ${eventType} version ${version}`
        }]
      };
    }
    
    // Validate against schema
    const ajv = new Ajv();
    const validate = ajv.compile(schema);
    const valid = validate(event);
    
    if (valid) {
      return { valid: true };
    }
    
    return {
      valid: false,
      errors: validate.errors
    };
  }
}
```

#### 5.3.2 Versioned Event Publishing

```typescript
class VersionedEventPublisher {
  constructor(
    private messageBroker: MessageBroker,
    private schemaRegistry: EventSchemaRegistry
  ) {}
  
  async publish<T>(eventType: string, data: T, options: PublishOptions = {}): Promise<void> {
    // Determine version
    const version = options.version || this.schemaRegistry.getLatestVersion(eventType);
    
    // Create event envelope
    const event: Event<T> = {
      eventType,
      version,
      timestamp: new Date().toISOString(),
      data,
      metadata: {
        eventId: uuidv4(),
        correlationId: options.correlationId || uuidv4(),
        causationId: options.causationId,
        source: options.source || 'nca-system'
      }
    };
    
    // Validate against schema
    const validationResult = this.schemaRegistry.validateEvent(event);
    if (!validationResult.valid) {
      throw new ValidationError(
        'Event validation failed',
        'INVALID_EVENT',
        validationResult.errors
      );
    }
    
    // Publish to message broker
    await this.messageBroker.publish(
      eventType,
      event,
      {
        headers: {
          'x-event-type': eventType,
          'x-event-version': version.toString(),
          'x-correlation-id': event.metadata.correlationId
        }
      }
    );
  }
}
```

#### 5.3.3 Versioned Event Consumption

```typescript
class VersionedEventConsumer {
  private handlers: Map<string, Map<number, EventHandler<any>>> = new Map();
  private upcasters: Map<string, Map<number, EventUpcaster<any, any>>> = new Map();
  
  constructor(
    private messageBroker: MessageBroker,
    private schemaRegistry: EventSchemaRegistry
  ) {}
  
  registerHandler<T>(
    eventType: string,
    version: number,
    handler: EventHandler<T>
  ): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Map());
    }
    
    this.handlers.get(eventType).set(version, handler);
  }
  
  registerUpcaster<T, U>(
    eventType: string,
    fromVersion: number,
    toVersion: number,
    upcaster: (event: Event<T>) => Event<U>
  ): void {
    if (!this.upcasters.has(eventType)) {
      this.upcasters.set(eventType, new Map());
    }
    
    this.upcasters.get(eventType).set(fromVersion, {
      fromVersion,
      toVersion,
      upcast: upcaster
    });
  }
  
  async start(): Promise<void> {
    // Subscribe to all event types
    const eventTypes = Array.from(this.handlers.keys());
    
    for (const eventType of eventTypes) {
      await this.messageBroker.subscribe(
        eventType,
        this.handleEvent.bind(this)
      );
    }
  }
  
  private async handleEvent(event: Event<any>): Promise<void> {
    const { eventType, version } = event;
    
    // Find appropriate handler
    const eventHandlers = this.handlers.get(eventType);
    if (!eventHandlers) {
      logger.warn(`No handlers registered for event type: ${eventType}`);
      return;
    }
    
    // Check if we have a direct handler for this version
    const directHandler = eventHandlers.get(version);
    if (directHandler) {
      await directHandler.handle(event);
      return;
    }
    
    // Find the highest version we can handle
    const handlerVersions = Array.from(eventHandlers.keys());
    const highestVersion = Math.max(...handlerVersions);
    
    // If event version is higher than what we can handle, log warning and skip
    if (version > highestVersion) {
      logger.warn(
        `Received event version ${version} but highest supported version is ${highestVersion} for type ${eventType}`
      );
      return;
    }
    
    // If event version is lower, try to upcast
    let currentEvent = event;
    let currentVersion = version;
    
    while (currentVersion < highestVersion) {
      const eventUpcasters = this.upcasters.get(eventType);
      if (!eventUpcasters) {
        logger.error(`No upcasters registered for event type: ${eventType}`);
        return;
      }
      
      const upcaster = eventUpcasters.get(currentVersion);
      if (!upcaster) {
        logger.error(
          `No upcaster registered for event type ${eventType} from version ${currentVersion} to ${currentVersion + 1}`
        );
        return;
      }
      
      // Upcast the event
      currentEvent = upcaster.upcast(currentEvent);
      currentVersion = upcaster.toVersion;
    }
    
    // Handle the upcasted event
    const handler = eventHandlers.get(currentVersion);
    if (handler) {
      await handler.handle(currentEvent);
    }
  }
}

interface EventHandler<T> {
  handle(event: Event<T>): Promise<void>;
}

interface EventUpcaster<T, U> {
  fromVersion: number;
  toVersion: number;
  upcast(event: Event<T>): Event<U>;
}
```

### 5.4 Database Schema Versioning

The NCA system implements database schema versioning:

```yaml
DatabaseVersioningApproach:
  - Migration-based schema evolution
  - Version tracking table in each database
  - Automated migration on startup
  - Backward compatible changes only

MigrationTypes:
  - Additive changes (new tables, columns)
  - Index modifications
  - Data transformations
  - Constraint modifications
```

#### 5.4.1 Migration Framework

```typescript
class DatabaseMigrationManager {
  constructor(
    private dataSource: DataSource,
    private migrationScripts: MigrationScript[],
    private schemaVersionTable: string = 'schema_version'
  ) {}
  
  async initialize(): Promise<void> {
    // Ensure version table exists
    await this.ensureVersionTableExists();
    
    // Get current version
    const currentVersion = await this.getCurrentVersion();
    
    // Get migrations that need to be applied
    const pendingMigrations = this.migrationScripts
      .filter(script => script.version > currentVersion)
      .sort((a, b) => a.version - b.version);
    
    if (pendingMigrations.length === 0) {
      logger.info(`Database schema is up to date at version ${currentVersion}`);
      return;
    }
    
    logger.info(`Found ${pendingMigrations.length} pending migrations. Current version: ${currentVersion}`);
    
    // Apply migrations in order
    for (const migration of pendingMigrations) {
      logger.info(`Applying migration to version ${migration.version}: ${migration.description}`);
      
      const connection = await this.dataSource.getConnection();
      let transaction = null;
      
      try {
        // Start transaction
        transaction = await connection.beginTransaction();
        
        // Apply migration
        await migration.up(connection);
        
        // Update version
        await this.updateVersion(connection, migration.version, migration.description);
        
        // Commit transaction
        await transaction.commit();
        
        logger.info(`Successfully applied migration to version ${migration.version}`);
      } catch (error) {
        // Rollback on error
        if (transaction) {
          await transaction.rollback();
        }
        
        logger.error(`Migration to version ${migration.version} failed: ${error.message}`, {
          error,
          migration: migration.description
        });
        
        throw new Error(`Migration failed: ${error.message}`);
      } finally {
        connection.release();
      }
    }
    
    logger.info(`Database schema updated to version ${pendingMigrations[pendingMigrations.length - 1].version}`);
  }
  
  private async ensureVersionTableExists(): Promise<void> {
    const connection = await this.dataSource.getConnection();
    
    try {
      // Check if table exists
      const tableExists = await this.tableExists(connection, this.schemaVersionTable);
      
      if (!tableExists) {
        // Create version table
        await connection.query(`
          CREATE TABLE ${this.schemaVersionTable} (
            version INT NOT NULL PRIMARY KEY,
            description VARCHAR(200) NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms INT NOT NULL
          )
        `);
        
        // Insert initial version
        await connection.query(`
          INSERT INTO ${this.schemaVersionTable} (version, description, execution_time_ms)
          VALUES (0, 'Initial version', 0)
        `);
        
        logger.info(`Created schema version table: ${this.schemaVersionTable}`);
      }
    } finally {
      connection.release();
    }
  }
  
  private async tableExists(connection: Connection, tableName: string): Promise<boolean> {
    // Implementation depends on database type
    // This example is for PostgreSQL
    const result = await connection.query(`
      SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = $1
      )
    `, [tableName]);
    
    return result.rows[0].exists;
  }
  
  private async getCurrentVersion(): Promise<number> {
    const connection = await this.dataSource.getConnection();
    
    try {
      const result = await connection.query(`
        SELECT MAX(version) as current_version
        FROM ${this.schemaVersionTable}
      `);
      
      return result.rows[0].current_version || 0;
    } finally {
      connection.release();
    }
  }
  
  private async updateVersion(
    connection: Connection,
    version: number,
    description: string
  ): Promise<void> {
    await connection.query(`
      INSERT INTO ${this.schemaVersionTable} (version, description, execution_time_ms)
      VALUES ($1, $2, $3)
    `, [version, description, 0]);
  }
}

interface MigrationScript {
  version: number;
  description: string;
  up(connection: Connection): Promise<void>;
  down(connection: Connection): Promise<void>;
}
```

#### 5.4.2 Example Migration Script

```typescript
const migration_20230615_01: MigrationScript = {
  version: 1,
  description: 'Add health_score column to memories table',
  
  async up(connection: Connection): Promise<void> {
    // Add new column
    await connection.query(`
      ALTER TABLE memories
      ADD COLUMN health_score SMALLINT
    `);
    
    // Set default value for existing records
    await connection.query(`
      UPDATE memories
      SET health_score = 50
      WHERE health_score IS NULL
    `);
    
    // Make column not nullable
    await connection.query(`
      ALTER TABLE memories
      ALTER COLUMN health_score SET NOT NULL
    `);
    
    // Add index
    await connection.query(`
      CREATE INDEX idx_memories_health_score ON memories(health_score)
    `);
  },
  
  async down(connection: Connection): Promise<void> {
    // Remove index
    await connection.query(`
      DROP INDEX IF EXISTS idx_memories_health_score
    `);
    
    // Remove column
    await connection.query(`
      ALTER TABLE memories
      DROP COLUMN IF EXISTS health_score
    `);
  }
};
```

### 5.5 Client Library Versioning

The NCA system implements versioning for client libraries:

```yaml
ClientLibraryVersioningApproach:
  - Semantic versioning (MAJOR.MINOR.PATCH)
  - Backward compatibility within major versions
  - Deprecation notices before breaking changes
  - Comprehensive migration guides

VersioningRules:
  - MAJOR: Breaking changes to public API
  - MINOR: New features, non-breaking changes
  - PATCH: Bug fixes, performance improvements
```

#### 5.5.1 Client Library Implementation

```typescript
/**
 * NCA Client Library v2.3.1
 * 
 * This client provides access to the NeuroCognitive Architecture API.
 */
class NCAClient {
  private baseUrl: string;
  private apiKey: string;
  private version: string = 'v1';
  
  /**
   * Create a new NCA client instance
   * 
   * @param options Configuration options
   */
  constructor(options: NCAClientOptions) {
    this.baseUrl = options.baseUrl || 'https://api.nca-system.com';
    this.apiKey = options.apiKey;
    this.version = options.version || 'v1';
    
    // Warn about deprecated version
    if (this.version === 'v1') {
      console.warn(
        'WARNING: API v1 is deprecated and will be removed on 2023-12-31. ' +
        'Please migrate to v2: https://docs.nca-system.com/migration/v1-to-v2'
      );
    }
  }
  
  /**
   * Create a new memory
   * 
   * @param data Memory data
   * @returns Created memory
   */
  async createMemory(data: CreateMemoryRequest): Promise<Memory> {
    return this.post(`/api/${this.version}/memories`, data);
  }
  
  /**
   * Get a memory by ID
   * 
   * @param id Memory ID
   * @returns Memory or null if not found
   */
  async getMemory(id: string): Promise<Memory | null> {
    try {
      return await this.get(`/api/${this.version}/memories/${id}`);
    } catch (error) {
      if (error.status === 404) {
        return null;
      }
      throw error;
    }
  }
  
  /**
   * Search memories
   * 
   * @param query Search query
   * @returns Search results
   * @deprecated Use semanticSearch or keywordSearch instead
   */
  async searchMemories(query: SearchQuery): Promise<SearchResult> {
    console.warn(
      'WARNING: searchMemories is deprecated and will be removed in v3.0.0. ' +
      'Use semanticSearch or keywordSearch instead.'
    );
    
    return this.post(`/api/${this.version}/memories/search`, query);
  }
  
  /**
   * Search memories using semantic similarity
   * 
   * @param query Search query
   * @returns Search results
   * @since 2.0.0
   */
  async semanticSearch(query: SemanticSearchQuery): Promise<SearchResult> {
    return this.post(`/api/${this.version}/memories/search`, {
      ...query,
      searchType: 'SEMANTIC'
    });
  }
  
  /**
   * Search memories using keyword matching
   * 
   * @param query Search query
   * @returns Search results
   * @since 2.0.0
   */
  async keywordSearch(query: KeywordSearchQuery): Promise<SearchResult> {
    return this.post(`/api/${this.version}/memories/search`, {
      ...query,
      searchType: 'KEYWORD'
    });
  }
  
  /**
   * Update a memory
   * 
   * @param id Memory ID
   * @param updates Fields to update
   * @returns Updated memory
   */
  async updateMemory(id: string, updates: Partial<UpdateMemoryRequest>): Promise<Memory> {
    return this.patch(`/api/${this.version}/memories/${id}`, updates);
  }
  
  /**
   * Delete a memory
   * 
   * @param id Memory ID
   * @returns True if deleted, false if not found
   */
  async deleteMemory(id: string): Promise<boolean> {
    try {
      await this.delete(`/api/${this.version}/memories/${id}`);
      return true;
    } catch (error) {
      if (error.status === 404) {
        return false;
      }
      throw error;
    }
  }
  
  // Private helper methods
  
  private async get<T>(path: string): Promise<T> {
    return this.request('GET', path);
  }
  
  private async post<T>(path: string, data: any): Promise<T> {
    return this.request('POST', path, data);
  }
  
  private async patch<T>(path: string, data: any): Promise<T> {
    return this.request('PATCH', path, data);
  }
  
  private async delete<T>(path: string): Promise<T> {
    return this.request('DELETE', path);
  }
  
  private async request<T>(method: string, path: string, data?: any): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${this.apiKey}`,
      'User-Agent': `nca-client-js/2.3.1`,
      'Accept': 'application/json'
    };
    
    if (data) {
      headers['Content-Type'] = 'application/json';
    }
    
    const response = await fetch(url, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      throw new NCAApiError(
        errorData.error?.message || `API request failed with status ${response.status}`,
        response.status,
        errorData.error?.code || 'API_ERROR',
        errorData.error
      );
    }
    
    if (response.status === 204) {
      return null as T;
    }
    
    return response.json();
  }
}

class NCAApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code: string,
    public details: any
  ) {
    super(message);
    this.name = 'NCAApiError';
  }
}

interface NCAClientOptions {
  baseUrl?: string;
  apiKey: string;
  version?: string;
}
```

This comprehensive interface design provides a solid foundation for implementing the NeuroCognitive Architecture (NCA) system, with careful consideration of API contracts, communication protocols, interface patterns, error handling, and versioning strategies. The design balances flexibility, performance, and maintainability while providing clear guidelines for implementation.