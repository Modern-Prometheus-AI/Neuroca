
# NeuroCognitive Architecture (NCA) for LLMs - Project Structure

## Introduction

This document outlines the comprehensive project structure for the NeuroCognitive Architecture (NCA) system. The structure is designed to support the three-tiered memory system, health dynamics, advanced biological-inspired components, and seamless LLM integration while adhering to best practices for maintainability, scalability, and security.

The project structure follows a modular, domain-driven design approach that separates concerns while facilitating collaboration among team members. It is organized to support the phased implementation strategy outlined in the technology stack document, allowing for incremental development and testing of components.

## 1. Top-Level Directory Structure

```
neuroca/
├── api/                  # API layer and endpoints
├── cli/                  # Command-line interface tools
├── config/               # Configuration files and settings
├── core/                 # Core domain logic and models
├── db/                   # Database migrations and schemas
├── docs/                 # Documentation
├── infrastructure/       # Infrastructure as code
├── integration/          # LLM integration components
├── memory/               # Memory tier implementations
├── monitoring/           # Monitoring and observability
├── scripts/              # Utility scripts
├── tests/                # Test suite
├── tools/                # Development and operational tools
├── .dockerignore         # Docker ignore file
├── .editorconfig         # Editor configuration
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── docker-compose.yml    # Local development environment
├── Dockerfile            # Main application Dockerfile
├── LICENSE               # Project license
├── Makefile              # Common commands and operations
├── poetry.lock           # Locked dependencies
├── pyproject.toml        # Project metadata and dependencies
└── README.md             # Project overview and quick start
```

## 2. Detailed Directory Structure and Key Files

### 2.1. API Layer (`/api`)

The API layer provides external interfaces to the NCA system, including RESTful endpoints and WebSocket connections.

```
api/
├── __init__.py
├── app.py                # FastAPI application instance
├── dependencies.py       # Dependency injection components
├── middleware/           # API middleware components
│   ├── __init__.py
│   ├── authentication.py # Authentication middleware
│   ├── logging.py        # Request logging middleware
│   └── tracing.py        # Distributed tracing middleware
├── routes/               # API route definitions
│   ├── __init__.py
│   ├── health.py         # Health check endpoints
│   ├── memory.py         # Memory operation endpoints
│   ├── metrics.py        # Metrics and monitoring endpoints
│   └── system.py         # System management endpoints
├── schemas/              # Pydantic models for API
│   ├── __init__.py
│   ├── common.py         # Shared schema components
│   ├── memory.py         # Memory-related schemas
│   ├── requests.py       # Request schemas
│   └── responses.py      # Response schemas
└── websockets/           # WebSocket handlers
    ├── __init__.py
    ├── events.py         # Event definitions
    └── handlers.py       # WebSocket connection handlers
```

#### Key Files:

- **app.py**: Initializes and configures the FastAPI application, including middleware, routes, and exception handlers.
- **dependencies.py**: Defines dependency injection components for routes, such as database connections and authentication.
- **routes/*.py**: Defines API endpoints organized by domain area, with clear input validation and error handling.
- **schemas/*.py**: Pydantic models for request/response validation and documentation.

### 2.2. Command-Line Interface (`/cli`)

The CLI provides administrative and operational tools for managing the NCA system.

```
cli/
├── __init__.py
├── commands/             # CLI command implementations
│   ├── __init__.py
│   ├── db.py             # Database management commands
│   ├── memory.py         # Memory operations commands
│   └── system.py         # System management commands
├── main.py               # CLI entry point
└── utils/                # CLI utilities
    ├── __init__.py
    ├── formatting.py     # Output formatting utilities
    └── validation.py     # Input validation utilities
```

#### Key Files:

- **main.py**: Entry point for the CLI, using Click or Typer for command definition.
- **commands/*.py**: Implementation of specific CLI commands, organized by domain area.
- **utils/*.py**: Helper utilities for the CLI, such as output formatting and input validation.

### 2.3. Configuration (`/config`)

The configuration directory contains settings and configuration management for the NCA system.

```
config/
├── __init__.py
├── default.py            # Default configuration values
├── development.py        # Development environment configuration
├── production.py         # Production environment configuration
├── settings.py           # Settings management using Pydantic
└── testing.py            # Testing environment configuration
```

#### Key Files:

- **settings.py**: Defines the configuration schema using Pydantic BaseSettings, with environment variable loading and validation.
- **default.py**: Default configuration values that apply across environments.
- **[environment].py**: Environment-specific configuration overrides.

### 2.4. Core Domain Logic (`/core`)

The core directory contains the central domain logic and models for the NCA system.

```
core/
├── __init__.py
├── constants.py          # System-wide constants
├── enums.py              # Enumeration definitions
├── errors.py             # Custom exception classes
├── events/               # Event definitions and handlers
│   ├── __init__.py
│   ├── handlers.py       # Event handler implementations
│   ├── memory.py         # Memory-related events
│   └── system.py         # System-related events
├── health/               # Health system implementation
│   ├── __init__.py
│   ├── calculator.py     # Health score calculation
│   ├── dynamics.py       # Health dynamics implementation
│   ├── metadata.py       # Health metadata structures
│   └── thresholds.py     # Promotion/demotion thresholds
├── models/               # Domain models
│   ├── __init__.py
│   ├── base.py           # Base model definitions
│   ├── memory.py         # Memory item models
│   └── relationships.py  # Relationship models
└── utils/                # Core utilities
    ├── __init__.py
    ├── security.py       # Security-related utilities
    ├── serialization.py  # Serialization utilities
    └── validation.py     # Validation utilities
```

#### Key Files:

- **models/base.py**: Defines base classes for domain models, including common attributes and behaviors.
- **models/memory.py**: Defines the memory item models, including attributes and methods for all memory tiers.
- **health/calculator.py**: Implements the health score calculation algorithms for memory items.
- **health/dynamics.py**: Implements the health dynamics, including decay, reinforcement, and forgetting.
- **events/*.py**: Defines domain events and their handlers for system-wide communication.

### 2.5. Database (`/db`)

The database directory contains database migrations, schemas, and connection management.

```
db/
├── __init__.py
├── alembic/               # Alembic migrations for PostgreSQL
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
├── connections/           # Database connection management
│   ├── __init__.py
│   ├── mongo.py           # MongoDB connection
│   ├── neo4j.py           # Neo4j connection
│   ├── postgres.py        # PostgreSQL connection
│   └── redis.py           # Redis connection
├── migrations/            # Custom migrations for non-SQL databases
│   ├── __init__.py
│   ├── mongo/
│   └── neo4j/
├── repositories/          # Data access repositories
│   ├── __init__.py
│   ├── base.py            # Base repository pattern
│   ├── ltm.py             # Long-term memory repository
│   ├── mtm.py             # Medium-term memory repository
│   └── stm.py             # Short-term memory repository
└── schemas/               # Database schemas
    ├── __init__.py
    ├── ltm.py             # Long-term memory schemas
    ├── mtm.py             # Medium-term memory schemas
    └── stm.py             # Short-term memory schemas
```

#### Key Files:

- **connections/*.py**: Manages database connections, including connection pooling, retry logic, and health checks.
- **repositories/*.py**: Implements the repository pattern for data access, abstracting database operations.
- **schemas/*.py**: Defines database schemas, including indexes, constraints, and relationships.
- **alembic/versions/**: Contains versioned database migrations for PostgreSQL.

### 2.6. Documentation (`/docs`)

The documentation directory contains comprehensive documentation for the NCA system.

```
docs/
├── api/                  # API documentation
│   ├── endpoints.md
│   ├── examples.md
│   └── schemas.md
├── architecture/         # Architecture documentation
│   ├── components.md
│   ├── data_flow.md
│   ├── decisions/        # Architecture Decision Records (ADRs)
│   │   ├── adr-001-memory-tiers.md
│   │   ├── adr-002-health-system.md
│   │   └── adr-003-integration-approach.md
│   └── diagrams/         # Architecture diagrams
│       ├── component.png
│       ├── deployment.png
│       └── sequence.png
├── development/          # Development documentation
│   ├── contributing.md
│   ├── environment.md
│   ├── standards.md
│   └── workflow.md
├── operations/           # Operations documentation
│   ├── deployment.md
│   ├── monitoring.md
│   ├── runbooks/         # Operational runbooks
│   │   ├── backup-restore.md
│   │   ├── incident-response.md
│   │   └── scaling.md
│   └── troubleshooting.md
├── user/                 # User documentation
│   ├── configuration.md
│   ├── examples.md
│   ├── getting-started.md
│   └── integration.md
├── index.md              # Documentation home page
└── mkdocs.yml            # MkDocs configuration
```

#### Key Files:

- **architecture/decisions/**: Contains Architecture Decision Records (ADRs) documenting key design decisions.
- **architecture/diagrams/**: Contains architecture diagrams in various formats (component, deployment, sequence).
- **operations/runbooks/**: Contains operational runbooks for common maintenance tasks and incident response.
- **user/**: Contains user-facing documentation for system configuration and integration.
- **mkdocs.yml**: Configuration for the MkDocs documentation generator.

### 2.7. Infrastructure (`/infrastructure`)

The infrastructure directory contains Infrastructure as Code (IaC) definitions for deploying the NCA system.

```
infrastructure/
├── kubernetes/           # Kubernetes manifests
│   ├── base/             # Base Kubernetes configurations
│   │   ├── api.yaml
│   │   ├── background.yaml
│   │   ├── databases.yaml
│   │   └── monitoring.yaml
│   └── overlays/         # Environment-specific overlays
│       ├── development/
│       ├── production/
│       └── staging/
├── monitoring/           # Monitoring infrastructure
│   ├── dashboards/       # Grafana dashboards
│   ├── alerts.yaml       # Alerting rules
│   └── prometheus.yaml   # Prometheus configuration
├── terraform/            # Terraform IaC
│   ├── environments/     # Environment-specific configurations
│   │   ├── development/
│   │   ├── production/
│   │   └── staging/
│   └── modules/          # Reusable Terraform modules
│       ├── database/
│       ├── kubernetes/
│       ├── networking/
│       └── security/
└── docker/               # Docker configurations
    ├── api/              # API service Dockerfile
    ├── background/       # Background worker Dockerfile
    ├── dev/              # Development environment Dockerfile
    └── test/             # Testing environment Dockerfile
```

#### Key Files:

- **kubernetes/base/**: Contains base Kubernetes manifests for all components.
- **kubernetes/overlays/**: Contains environment-specific Kubernetes configuration overlays.
- **terraform/modules/**: Contains reusable Terraform modules for infrastructure components.
- **terraform/environments/**: Contains environment-specific Terraform configurations.
- **docker/**: Contains Dockerfiles for various services and environments.

### 2.8. LLM Integration (`/integration`)

The integration directory contains components for integrating with LLM providers.

```
integration/
├── __init__.py
├── adapters/             # LLM provider adapters
│   ├── __init__.py
│   ├── anthropic.py      # Anthropic Claude adapter
│   ├── base.py           # Base adapter interface
│   ├── openai.py         # OpenAI GPT adapter
│   └── vertexai.py       # Google Vertex AI adapter
├── context/              # Context management
│   ├── __init__.py
│   ├── injection.py      # Context injection strategies
│   ├── manager.py        # Context window management
│   └── retrieval.py      # Context-aware retrieval
├── langchain/            # LangChain integration
│   ├── __init__.py
│   ├── chains.py         # Custom chain definitions
│   ├── memory.py         # Custom memory components
│   └── tools.py          # Custom tool definitions
└── prompts/              # Prompt templates
    ├── __init__.py
    ├── memory.py         # Memory-related prompts
    ├── reasoning.py      # Reasoning-related prompts
    └── templates.py      # Reusable prompt templates
```

#### Key Files:

- **adapters/*.py**: Implements adapters for different LLM providers, with a common interface.
- **context/injection.py**: Implements strategies for injecting memory into LLM context windows.
- **context/retrieval.py**: Implements context-aware memory retrieval strategies.
- **langchain/*.py**: Implements custom LangChain components for integration.
- **prompts/*.py**: Defines prompt templates for different use cases.

### 2.9. Memory System (`/memory`)

The memory directory contains the implementation of the three-tiered memory system and advanced components.

```
memory/
├── __init__.py
├── factory.py            # Memory factory for creating memory items
├── ltm/                  # Long-term memory implementation
│   ├── __init__.py
│   ├── manager.py        # LTM management operations
│   ├── operations.py     # LTM-specific operations
│   └── storage.py        # LTM storage implementation
├── mtm/                  # Medium-term memory implementation
│   ├── __init__.py
│   ├── manager.py        # MTM management operations
│   ├── operations.py     # MTM-specific operations
│   └── storage.py        # MTM storage implementation
├── stm/                  # Short-term memory implementation
│   ├── __init__.py
│   ├── manager.py        # STM management operations
│   ├── operations.py     # STM-specific operations
│   └── storage.py        # STM storage implementation
├── lymphatic/            # Memory Lymphatic System
│   ├── __init__.py
│   ├── abstractor.py     # Abstraction mechanisms
│   ├── consolidator.py   # Memory consolidation
│   └── scheduler.py      # Consolidation scheduling
├── tubules/              # Neural Tubule Networks
│   ├── __init__.py
│   ├── connections.py    # Connection management
│   ├── pathways.py       # Pathway definition and traversal
│   └── weights.py        # Connection weight management
├── annealing/            # Temporal Annealing Scheduler
│   ├── __init__.py
│   ├── optimizer.py      # Processing optimization
│   ├── phases.py         # Processing phase definitions
│   └── scheduler.py      # Scheduling implementation
└── manager.py            # Unified memory manager
```

#### Key Files:

- **factory.py**: Implements the factory pattern for creating memory items with appropriate metadata.
- **[tier]/manager.py**: Implements management operations for each memory tier.
- **[tier]/storage.py**: Implements storage operations for each memory tier.
- **lymphatic/consolidator.py**: Implements memory consolidation processes.
- **tubules/connections.py**: Implements dynamic connection management between memory items.
- **annealing/scheduler.py**: Implements the temporal scheduling of memory processing.
- **manager.py**: Provides a unified interface to all memory operations across tiers.

### 2.10. Monitoring (`/monitoring`)

The monitoring directory contains components for system monitoring and observability.

```
monitoring/
├── __init__.py
├── health/               # System health monitoring
│   ├── __init__.py
│   ├── checks.py         # Health check implementations
│   └── probes.py         # Kubernetes probe endpoints
├── logging/              # Logging configuration
│   ├── __init__.py
│   ├── formatters.py     # Log formatters
│   └── handlers.py       # Log handlers
├── metrics/              # Metrics collection
│   ├── __init__.py
│   ├── collectors.py     # Custom metric collectors
│   ├── exporters.py      # Metric exporters
│   └── registry.py       # Metric registry
└── tracing/              # Distributed tracing
    ├── __init__.py
    ├── middleware.py     # Tracing middleware
    └── spans.py          # Custom span definitions
```

#### Key Files:

- **health/checks.py**: Implements health checks for system components.
- **logging/formatters.py**: Defines log formatters for structured logging.
- **metrics/collectors.py**: Implements custom metric collectors for system monitoring.
- **tracing/spans.py**: Defines custom spans for distributed tracing.

### 2.11. Scripts (`/scripts`)

The scripts directory contains utility scripts for development, deployment, and operations.

```
scripts/
├── db/                   # Database scripts
│   ├── backup.sh         # Database backup script
│   ├── initialize.sh     # Database initialization script
│   └── restore.sh        # Database restore script
├── deployment/           # Deployment scripts
│   ├── deploy.sh         # Deployment script
│   ├── rollback.sh       # Rollback script
│   └── validate.sh       # Deployment validation script
├── development/          # Development scripts
│   ├── lint.sh           # Linting script
│   ├── setup.sh          # Development environment setup
│   └── test.sh           # Test runner script
└── operations/           # Operations scripts
    ├── cleanup.sh        # Resource cleanup script
    ├── monitor.sh        # Monitoring script
    └── scale.sh          # Scaling script
```

#### Key Files:

- **db/*.sh**: Scripts for database operations, including backup and restore.
- **deployment/*.sh**: Scripts for deployment operations, including deployment and rollback.
- **development/*.sh**: Scripts for development operations, including linting and testing.
- **operations/*.sh**: Scripts for operational tasks, including monitoring and scaling.

### 2.12. Tests (`/tests`)

The tests directory contains the comprehensive test suite for the NCA system.

```
tests/
├── __init__.py
├── conftest.py           # Pytest configuration and fixtures
├── factories/            # Test data factories
│   ├── __init__.py
│   ├── memory.py         # Memory item factories
│   └── users.py          # User factories
├── integration/          # Integration tests
│   ├── __init__.py
│   ├── api/              # API integration tests
│   ├── db/               # Database integration tests
│   └── memory/           # Memory system integration tests
├── performance/          # Performance tests
│   ├── __init__.py
│   ├── benchmarks.py     # Performance benchmarks
│   └── locustfile.py     # Locust load testing
├── unit/                 # Unit tests
│   ├── __init__.py
│   ├── api/              # API unit tests
│   ├── core/             # Core domain unit tests
│   ├── health/           # Health system unit tests
│   ├── integration/      # LLM integration unit tests
│   └── memory/           # Memory system unit tests
└── utils/                # Test utilities
    ├── __init__.py
    ├── assertions.py     # Custom test assertions
    ├── helpers.py        # Test helper functions
    └── mocks.py          # Mock implementations
```

#### Key Files:

- **conftest.py**: Defines pytest fixtures and configuration for all tests.
- **factories/*.py**: Implements factories for generating test data.
- **integration/**: Contains integration tests for system components.
- **performance/**: Contains performance tests and benchmarks.
- **unit/**: Contains unit tests for individual components.
- **utils/*.py**: Contains utilities for testing, including assertions and mocks.

### 2.13. Tools (`/tools`)

The tools directory contains development and operational tools for the NCA system.

```
tools/
├── analysis/             # Analysis tools
│   ├── memory_analyzer.py # Memory analysis tool
│   └── performance_analyzer.py # Performance analysis tool
├── development/          # Development tools
│   ├── code_generator.py # Code generation tool
│   └── schema_generator.py # Schema generation tool
├── migration/            # Migration tools
│   ├── data_migrator.py  # Data migration tool
│   └── schema_migrator.py # Schema migration tool
└── visualization/        # Visualization tools
    ├── memory_visualizer.py # Memory visualization tool
    └── relationship_visualizer.py # Relationship visualization tool
```

#### Key Files:

- **analysis/*.py**: Tools for analyzing system behavior and performance.
- **development/*.py**: Tools for development tasks, such as code and schema generation.
- **migration/*.py**: Tools for data and schema migration.
- **visualization/*.py**: Tools for visualizing system state and relationships.

## 3. Module Organization and Dependencies

### 3.1. Core Module Dependencies

The NCA system is organized into modules with clear dependencies and separation of concerns. The following diagram illustrates the high-level module dependencies:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│     API     │────▶│    Core     │◀────│ Integration │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   ▲                   │
       │                   │                   │
       │             ┌─────────────┐           │
       └────────────▶│   Memory    │◀──────────┘
                     └─────────────┘
                           │
                           ▼
                     ┌─────────────┐
                     │     DB      │
                     └─────────────┘
                           │
                           ▼
                     ┌─────────────┐
                     │  Monitoring │
                     └─────────────┘
```

### 3.2. Detailed Module Dependencies

#### 3.2.1. API Module

- **Depends on**: Core, Memory, Integration
- **Purpose**: Provides external interfaces to the NCA system
- **Key Responsibilities**:
  - Request handling and validation
  - Response formatting
  - Authentication and authorization
  - API documentation

#### 3.2.2. Core Module

- **Depends on**: None (core domain logic)
- **Purpose**: Contains the central domain logic and models
- **Key Responsibilities**:
  - Domain model definitions
  - Health system implementation
  - Event definitions and handling
  - Core utilities and constants

#### 3.2.3. Memory Module

- **Depends on**: Core, DB
- **Purpose**: Implements the three-tiered memory system
- **Key Responsibilities**:
  - Memory tier implementations
  - Advanced component implementations (Lymphatic, Tubules, Annealing)
  - Memory operations and management
  - Memory factory and unified interface

#### 3.2.4. Integration Module

- **Depends on**: Core, Memory
- **Purpose**: Provides integration with LLM providers
- **Key Responsibilities**:
  - LLM provider adapters
  - Context management
  - Prompt templates
  - LangChain integration

#### 3.2.5. DB Module

- **Depends on**: Core
- **Purpose**: Manages database connections and operations
- **Key Responsibilities**:
  - Database connection management
  - Repository implementations
  - Schema definitions
  - Migrations

#### 3.2.6. Monitoring Module

- **Depends on**: Core, Memory, DB, Integration
- **Purpose**: Provides monitoring and observability
- **Key Responsibilities**:
  - Health checks
  - Metrics collection
  - Logging configuration
  - Distributed tracing

### 3.3. Dependency Injection

The NCA system uses dependency injection to manage component dependencies and facilitate testing. The dependency injection system is implemented using FastAPI's dependency injection system for API components and a custom dependency container for non-API components.

```python
# Example dependency injection in FastAPI
from fastapi import Depends, FastAPI
from neuroca.db.connections.postgres import get_postgres_connection
from neuroca.db.repositories.ltm import LTMRepository
from neuroca.memory.ltm.manager import LTMManager

app = FastAPI()

def get_ltm_repository(db=Depends(get_postgres_connection)):
    return LTMRepository(db)

def get_ltm_manager(repo=Depends(get_ltm_repository)):
    return LTMManager(repo)

@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str, ltm_manager=Depends(get_ltm_manager)):
    return await ltm_manager.get(memory_id)
```

## 4. Naming Conventions

### 4.1. Python Code Naming Conventions

The NCA project follows PEP 8 naming conventions with some additional project-specific guidelines:

#### 4.1.1. Modules and Packages

- **Package Names**: Lowercase, short, and descriptive (e.g., `memory`, `api`, `core`)
- **Module Names**: Lowercase with underscores for readability (e.g., `memory_manager.py`, `health_calculator.py`)

#### 4.1.2. Classes

- **Class Names**: CapWords/PascalCase (e.g., `MemoryItem`, `HealthCalculator`)
- **Exception Names**: CapWords with "Error" suffix (e.g., `MemoryNotFoundError`, `InvalidHealthScoreError`)
- **Test Classes**: CapWords with "Test" prefix (e.g., `TestMemoryManager`, `TestHealthCalculator`)

#### 4.1.3. Functions and Methods

- **Function Names**: Lowercase with underscores (e.g., `calculate_health_score`, `get_memory_item`)
- **Method Names**: Lowercase with underscores (e.g., `get_by_id`, `update_health`)
- **Private Methods**: Prefixed with underscore (e.g., `_calculate_decay`, `_validate_input`)
- **Test Methods**: Lowercase with underscores, prefixed with "test_" (e.g., `test_calculate_health_score`, `test_memory_retrieval`)

#### 4.1.4. Variables and Constants

- **Variable Names**: Lowercase with underscores (e.g., `memory_item`, `health_score`)
- **Constants**: Uppercase with underscores (e.g., `DEFAULT_TTL`, `MAX_HEALTH_SCORE`)
- **Boolean Variables**: Prefixed with "is_", "has_", or similar (e.g., `is_valid`, `has_expired`)

#### 4.1.5. Type Hints

- **Type Aliases**: CapWords with descriptive names (e.g., `MemoryID`, `HealthScore`)
- **Generic Types**: Single uppercase letter or descriptive CapWords (e.g., `T`, `MemoryItemT`)

### 4.2. Database Naming Conventions

#### 4.2.1. PostgreSQL (LTM)

- **Table Names**: Plural, snake_case (e.g., `memory_items`, `relationships`)
- **Column Names**: Singular, snake_case (e.g., `id`, `creation_timestamp`)
- **Primary Keys**: Named `id` or `{table_name_singular}_id`
- **Foreign Keys**: Named `{referenced_table_singular}_id`
- **Indexes**: Named `idx_{table}_{column(s)}` (e.g., `idx_memory_items_embedding`)
- **Constraints**: Named `{constraint_type}_{table}_{column(s)}` (e.g., `pk_memory_items_id`, `fk_relationships_source_id`)

#### 4.2.2. MongoDB (MTM)

- **Collection Names**: Plural, camelCase (e.g., `memoryItems`, `synthesizedConcepts`)
- **Field Names**: Singular, camelCase (e.g., `creationTimestamp`, `healthScore`)
- **Indexes**: Named descriptively based on purpose (e.g., `ttl_index`, `embedding_vector_index`)

#### 4.2.3. Redis (STM)

- **Key Names**: Colon-separated namespaces, lowercase (e.g., `stm:item:{id}`, `stm:health:{id}`)
- **Hash Fields**: Singular, camelCase (e.g., `content`, `healthScore`)
- **Set Names**: Plural, lowercase with colons (e.g., `stm:recent:items`, `stm:tags:{tag}`)

#### 4.2.4. Neo4j (Relationships)

- **Node Labels**: Singular, PascalCase (e.g., `Memory`, `Concept`)
- **Relationship Types**: Uppercase with underscores (e.g., `RELATES_TO`, `DERIVED_FROM`)
- **Property Names**: camelCase (e.g., `createdAt`, `strengthValue`)

### 4.3. API Naming Conventions

#### 4.3.1. Endpoints

- **Resource URLs**: Plural nouns, kebab-case (e.g., `/api/memory-items`, `/api/health-scores`)
- **Action URLs**: Verb followed by resource, kebab-case (e.g., `/api/memory-items/{id}/promote`, `/api/memory-items/{id}/consolidate`)
- **Query Parameters**: camelCase (e.g., `?includeHealth=true`, `?maxResults=50`)

#### 4.3.2. Request/Response Fields

- **JSON Fields**: camelCase (e.g., `{ "memoryId": "123", "healthScore": 85 }`)
- **Error Responses**: Consistent structure with `code`, `message`, and optional `details` fields

### 4.4. File Naming Conventions

#### 4.4.1. Python Files

- **Implementation Files**: Lowercase with underscores (e.g., `memory_manager.py`, `health_calculator.py`)
- **Test Files**: Prefixed with `test_` (e.g., `test_memory_manager.py`, `test_health_calculator.py`)
- **Interface/Abstract Files**: Prefixed with `base_` or suffixed with `_interface` (e.g., `base_repository.py`, `manager_interface.py`)

#### 4.4.2. Configuration Files

- **Environment-Specific**: Named after environment (e.g., `development.py`, `production.py`)
- **Default Configuration**: Named `default.py` or `settings.py`
- **Docker-Related**: Standard names (`Dockerfile`, `docker-compose.yml`)
- **CI/CD-Related**: Standard names (`.github/workflows/ci.yml`, `Jenkinsfile`)

#### 4.4.3. Documentation Files

- **Markdown Files**: Descriptive names, kebab-case (e.g., `memory-system-overview.md`, `api-integration-guide.md`)
- **Architecture Decision Records**: Numbered sequence with descriptive name (e.g., `adr-001-memory-tiers.md`, `adr-002-health-system.md`)
- **Diagrams**: Descriptive names with type suffix, kebab-case (e.g., `memory-flow-sequence.png`, `system-architecture-component.png`)

## 5. Implementation Examples

### 5.1. Core Domain Model Example

```python
# core/models/memory.py
from datetime import datetime
from typing import Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from neuroca.core.enums import MemoryTier, ContentType
from neuroca.core.models.base import BaseEntity

class HealthMetadata(BaseModel):
    """Health metadata for memory items."""
    base_score: float = Field(default=100.0, ge=0.0, le=100.0)
    relevance_score: float = Field(default=100.0, ge=0.0, le=100.0)
    last_access_timestamp: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0, ge=0)
    importance_flag: int = Field(default=5, ge=0, le=10)
    content_type_tags: Set[ContentType] = Field(default_factory=set)
    
    def calculate_health(self, current_time: datetime = None) -> float:
        """Calculate the current health score based on all factors."""
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Calculate recency factor (decay over time)
        time_diff = (current_time - self.last_access_timestamp).total_seconds()
        recency_factor = max(0.0, 1.0 - (time_diff / (3600 * 24 * 7)))  # 7-day decay
        
        # Calculate final health score
        health_score = (
            self.base_score * 0.4 +
            self.relevance_score * 0.3 +
            recency_factor * 0.2 +
            min(1.0, self.access_count / 10) * 0.05 +
            (self.importance_flag / 10) * 0.05
        )
        
        return min(100.0, max(0.0, health_score))

class MemoryItem(BaseEntity):
    """Base memory item model for all memory tiers."""
    id: UUID = Field(default_factory=uuid4)
    content: str = Field(...)
    embedding: List[float] = Field(default_factory=list)
    tier: MemoryTier = Field(...)
    creation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_modified_timestamp: datetime = Field(default_factory=datetime.utcnow)
    health: HealthMetadata = Field(default_factory=HealthMetadata)
    metadata: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
    related_items: List[UUID] = Field(default_factory=list)
    
    def record_access(self) -> None:
        """Record an access to this memory item."""
        self.health.last_access_timestamp = datetime.utcnow()
        self.health.access_count += 1
        
    def update_relevance(self, relevance_score: float) -> None:
        """Update the relevance score of this memory item."""
        self.health.relevance_score = max(0.0, min(100.0, relevance_score))
        self.last_modified_timestamp = datetime.utcnow()
        
    def should_promote(self) -> bool:
        """Determine if this memory item should be promoted to a higher tier."""
        health_score = self.health.calculate_health()
        
        if self.tier == MemoryTier.STM and health_score >= 75.0:
            return True
        elif self.tier == MemoryTier.MTM and health_score >= 90.0:
            return True
            
        return False
        
    def should_demote(self) -> bool:
        """Determine if this memory item should be demoted to a lower tier."""
        health_score = self.health.calculate_health()
        
        if self.tier == MemoryTier.MTM and health_score < 40.0:
            return True
        elif self.tier == MemoryTier.LTM and health_score < 25.0:
            return True
            
        return False
        
    def should_forget(self) -> bool:
        """Determine if this memory item should be forgotten (removed)."""
        health_score = self.health.calculate_health()
        
        if self.tier == MemoryTier.STM and health_score < 20.0:
            return True
            
        return False
```

### 5.2. Repository Implementation Example

```python
# db/repositories/stm.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from uuid import UUID

from redis.asyncio import Redis

from neuroca.core.models.memory import MemoryItem
from neuroca.db.repositories.base import BaseRepository

class STMRepository(BaseRepository):
    """Repository for Short-Term Memory (STM) operations using Redis."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.key_prefix = "stm:item:"
        self.health_prefix = "stm:health:"
        self.recent_items_key = "stm:recent:items"
        self.default_ttl = timedelta(hours=3)
        
    async def create(self, memory_item: MemoryItem) -> MemoryItem:
        """Create a new memory item in STM."""
        # Serialize the memory item
        item_key = f"{self.key_prefix}{memory_item.id}"
        health_key = f"{self.health_prefix}{memory_item.id}"
        
        # Store the memory item
        await self.redis.hset(
            item_key,
            mapping={
                "id": str(memory_item.id),
                "content": memory_item.content,
                "tier": memory_item.tier.value,
                "creation_timestamp": memory_item.creation_timestamp.isoformat(),
                "last_modified_timestamp": memory_item.last_modified_timestamp.isoformat(),
                "metadata": str(memory_item.metadata),  # Simple serialization
                "related_items": ",".join(str(id) for id in memory_item.related_items)
            }
        )
        
        # Store the health metadata
        await self.redis.hset(
            health_key,
            mapping={
                "base_score": memory_item.health.base_score,
                "relevance_score": memory_item.health.relevance_score,
                "last_access_timestamp": memory_item.health.last_access_timestamp.isoformat(),
                "access_count": memory_item.health.access_count,
                "importance_flag": memory_item.health.importance_flag,
                "content_type_tags": ",".join(tag.value for tag in memory_item.health.content_type_tags)
            }
        )
        
        # Store the embedding separately for vector search
        if memory_item.embedding:
            await self.redis.execute_command(
                "HSET", item_key, "embedding", ",".join(str(val) for val in memory_item.embedding)
            )
        
        # Add to recent items
        await self.redis.zadd(
            self.recent_items_key,
            {str(memory_item.id): datetime.utcnow().timestamp()}
        )
        
        # Set TTL for both keys
        await self.redis.expire(item_key, int(self.default_ttl.total_seconds()))
        await self.redis.expire(health_key, int(self.default_ttl.total_seconds()))
        
        return memory_item
        
    async def get(self, id: UUID) -> Optional[MemoryItem]:
        """Get a memory item by ID."""
        item_key = f"{self.key_prefix}{id}"
        health_key = f"{self.health_prefix}{id}"
        
        # Get the memory item
        item_data = await self.redis.hgetall(item_key)
        if not item_data:
            return None
            
        # Get the health metadata
        health_data = await self.redis.hgetall(health_key)
        if not health_data:
            return None
            
        # Record access
        await self.redis.hincrby(health_key, "access_count", 1)
        await self.redis.hset(
            health_key, 
            "last_access_timestamp", 
            datetime.utcnow().isoformat()
        )
        
        # Reset TTL on access
        await self.redis.expire(item_key, int(self.default_ttl.total_seconds()))
        await self.redis.expire(health_key, int(self.default_ttl.total_seconds()))
        
        # Add to recent items with updated score
        await self.redis.zadd(
            self.recent_items_key,
            {str(id): datetime.utcnow().timestamp()}
        )
        
        # Deserialize and return the memory item
        return self._deserialize_memory_item(item_data, health_data)
        
    async def update(self, memory_item: MemoryItem) -> MemoryItem:
        """Update an existing memory item."""
        # Check if the item exists
        item_key = f"{self.key_prefix}{memory_item.id}"
        exists = await self.redis.exists(item_key)
        if not exists:
            raise KeyError(f"Memory item with ID {memory_item.id} not found")
            
        # Update the memory item (reuse create logic)
        return await self.create(memory_item)
        
    async def delete(self, id: UUID) -> bool:
        """Delete a memory item by ID."""
        item_key = f"{self.key_prefix}{id}"
        health_key = f"{self.health_prefix}{id}"
        
        # Remove from recent items
        await self.redis.zrem(self.recent_items_key, str(id))
        
        # Delete the keys
        deleted_item = await self.redis.delete(item_key)
        deleted_health = await self.redis.delete(health_key)
        
        return deleted_item > 0 and deleted_health > 0
        
    async def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get the most recently accessed memory items."""
        # Get the most recent item IDs
        recent_ids = await self.redis.zrevrange(
            self.recent_items_key, 
            0, 
            limit - 1
        )
        
        # Get the memory items
        items = []
        for id_bytes in recent_ids:
            id_str = id_bytes.decode("utf-8")
            item = await self.get(UUID(id_str))
            if item:
                items.append(item)
                
        return items
        
    async def search_by_embedding(self, embedding: List[float], limit: int = 5) -> List[MemoryItem]:
        """Search for memory items by embedding similarity."""
        # This is a simplified example - in a real implementation, 
        # you would use Redis Vector Search capabilities
        
        # For now, we'll just return recent items as a placeholder
        return await self.get_recent(limit)
        
    def _deserialize_memory_item(self, item_data: Dict, health_data: Dict) -> MemoryItem:
        """Deserialize a memory item from Redis data."""
        # Convert bytes to strings
        item_dict = {k.decode("utf-8"): v.decode("utf-8") for k, v in item_data.items()}
        health_dict = {k.decode("utf-8"): v.decode("utf-8") for k, v in health_data.items()}
        
        # Parse the embedding if it exists
        embedding = []
        if "embedding" in item_dict:
            embedding = [float(val) for val in item_dict["embedding"].split(",") if val]
            
        # Parse related items
        related_items = []
        if item_dict.get("related_items"):
            related_items = [UUID(id_str) for id_str in item_dict["related_items"].split(",") if id_str]
            
        # Parse content type tags
        content_type_tags = set()
        if health_dict.get("content_type_tags"):
            from neuroca.core.enums import ContentType
            content_type_tags = {
                ContentType(tag) 
                for tag in health_dict["content_type_tags"].split(",") 
                if tag
            }
            
        # Create and return the memory item
        from neuroca.core.enums import MemoryTier
        from neuroca.core.models.memory import HealthMetadata
        
        health = HealthMetadata(
            base_score=float(health_dict["base_score"]),
            relevance_score=float(health_dict["relevance_score"]),
            last_access_timestamp=datetime.fromisoformat(health_dict["last_access_timestamp"]),
            access_count=int(health_dict["access_count"]),
            importance_flag=int(health_dict["importance_flag"]),
            content_type_tags=content_type_tags
        )
        
        return MemoryItem(
            id=UUID(item_dict["id"]),
            content=item_dict["content"],
            embedding=embedding,
            tier=MemoryTier(item_dict["tier"]),
            creation_timestamp=datetime.fromisoformat(item_dict["creation_timestamp"]),
            last_modified_timestamp=datetime.fromisoformat(item_dict["last_modified_timestamp"]),
            health=health,
            metadata=eval(item_dict["metadata"]),  # Simple deserialization (not secure for production)
            related_items=related_items
        )
```

### 5.3. Memory Manager Example

```python
# memory/manager.py
from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import UUID

from neuroca.core.enums import MemoryTier
from neuroca.core.models.memory import MemoryItem
from neuroca.db.repositories.ltm import LTMRepository
from neuroca.db.repositories.mtm import MTMRepository
from neuroca.db.repositories.stm import STMRepository
from neuroca.memory.factory import MemoryFactory

class MemoryManager:
    """Unified manager for all memory tiers."""
    
    def __init__(
        self, 
        stm_repository: STMRepository,
        mtm_repository: MTMRepository,
        ltm_repository: LTMRepository,
        memory_factory: MemoryFactory
    ):
        self.stm_repo = stm_repository
        self.mtm_repo = mtm_repository
        self.ltm_repo = ltm_repository
        self.memory_factory = memory_factory
        
    async def create_memory(
        self, 
        content: str, 
        tier: MemoryTier = MemoryTier.STM,
        importance: int = 5,
        metadata: Dict = None,
        related_items: List[UUID] = None
    ) -> MemoryItem:
        """Create a new memory item in the specified tier."""
        # Create the memory item using the factory
        memory_item = self.memory_factory.create_memory_item(
            content=content,
            tier=tier,
            importance=importance,
            metadata=metadata or {},
            related_items=related_items or []
        )
        
        # Store in the appropriate repository
        if tier == MemoryTier.STM:
            return await self.stm_repo.create(memory_item)
        elif tier == MemoryTier.MTM:
            return await self.mtm_repo.create(memory_item)
        elif tier == MemoryTier.LTM:
            return await self.ltm_repo.create(memory_item)
        else:
            raise ValueError(f"Invalid memory tier: {tier}")
            
    async def get_memory(self, id: UUID) -> Optional[MemoryItem]:
        """Get a memory item by ID from any tier."""
        # Try to get from STM first (fastest)
        memory_item = await self.stm_repo.get(id)
        if memory_item:
            return memory_item
            
        # Try MTM next
        memory_item = await self.mtm_repo.get(id)
        if memory_item:
            return memory_item
            
        # Finally, try LTM
        memory_item = await self.ltm_repo.get(id)
        return memory_item
        
    async def update_memory(self, memory_item: MemoryItem) -> MemoryItem:
        """Update a memory item in its current tier."""
        if memory_item.tier == MemoryTier.STM:
            return await self.stm_repo.update(memory_item)
        elif memory_item.tier == MemoryTier.MTM:
            return await self.mtm_repo.update(memory_item)
        elif memory_item.tier == MemoryTier.LTM:
            return await self.ltm_repo.update(memory_item)
        else:
            raise ValueError(f"Invalid memory tier: {memory_item.tier}")
            
    async def delete_memory(self, id: UUID) -> bool:
        """Delete a memory item from all tiers."""
        # Try to delete from all tiers
        stm_deleted = await self.stm_repo.delete(id)
        mtm_deleted = await self.mtm_repo.delete(id)
        ltm_deleted = await self.ltm_repo.delete(id)
        
        # Return True if deleted from any tier
        return stm_deleted or mtm_deleted or ltm_deleted
        
    async def promote_memory(self, id: UUID) -> Optional[MemoryItem]:
        """Promote a memory item to a higher tier."""
        # Get the memory item
        memory_item = await self.get_memory(id)
        if not memory_item:
            return None
            
        # Check if promotion is needed
        if not memory_item.should_promote():
            return memory_item
            
        # Determine the target tier
        if memory_item.tier == MemoryTier.STM:
            target_tier = MemoryTier.MTM
        elif memory_item.tier == MemoryTier.MTM:
            target_tier = MemoryTier.LTM
        else:
            # Already in LTM, no promotion needed
            return memory_item
            
        # Delete from current tier
        if memory_item.tier == MemoryTier.STM:
            await self.stm_repo.delete(id)
        elif memory_item.tier == MemoryTier.MTM:
            await self.mtm_repo.delete(id)
            
        # Update tier and create in target tier
        memory_item.tier = target_tier
        memory_item.last_modified_timestamp = datetime.utcnow()
        
        if target_tier == MemoryTier.MTM:
            return await self.mtm_repo.create(memory_item)
        else:  # target_tier == MemoryTier.LTM
            return await self.ltm_repo.create(memory_item)
            
    async def demote_memory(self, id: UUID) -> Optional[MemoryItem]:
        """Demote a memory item to a lower tier."""
        # Get the memory item
        memory_item = await self.get_memory(id)
        if not memory_item:
            return None
            
        # Check if demotion is needed
        if not memory_item.should_demote():
            return memory_item
            
        # Determine the target tier
        if memory_item.tier == MemoryTier.LTM:
            target_tier = MemoryTier.MTM
        elif memory_item.tier == MemoryTier.MTM:
            target_tier = MemoryTier.STM
        else:
            # Already in STM, check if it should be forgotten
            if memory_item.should_forget():
                await self.stm_repo.delete(id)
                return None
            return memory_item
            
        # Delete from current tier
        if memory_item.tier == MemoryTier.LTM:
            await self.ltm_repo.delete(id)
        elif memory_item.tier == MemoryTier.MTM:
            await self.mtm_repo.delete(id)
            
        # Update tier and create in target tier
        memory_item.tier = target_tier
        memory_item.last_modified_timestamp = datetime.utcnow()
        
        if target_tier == MemoryTier.MTM:
            return await self.mtm_repo.create(memory_item)
        else:  # target_tier == MemoryTier.STM
            return await self.stm_repo.create(memory_item)
            
    async def search_by_content(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Search for memory items by content across all tiers."""
        # Search in each tier
        stm_results = await self.stm_repo.search_by_content(query, limit)
        mtm_results = await self.mtm_repo.search_by_content(query, limit)
        ltm_results = await self.ltm_repo.search_by_content(query, limit)
        
        # Combine and deduplicate results
        all_results = {}
        for item in stm_results + mtm_results + ltm_results:
            all_results[item.id] = item
            
        # Sort by health score (descending)
        sorted_results = sorted(
            all_results.values(),
            key=lambda item: item.health.calculate_health(),
            reverse=True
        )
        
        return sorted_results[:limit]
        
    async def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[MemoryItem]:
        """Search for memory items by embedding similarity across all tiers."""
        # Search in each tier
        stm_results = await self.stm_repo.search_by_embedding(embedding, limit)
        mtm_results = await self.mtm_repo.search_by_embedding(embedding, limit)
        ltm_results = await self.ltm_repo.search_by_embedding(embedding, limit)
        
        # Combine and deduplicate results
        all_results = {}
        for item in stm_results + mtm_results + ltm_results:
            all_results[item.id] = item
            
        # Sort by health score (descending)
        sorted_results = sorted(
            all_results.values(),
            key=lambda item: item.health.calculate_health(),
            reverse=True
        )
        
        return sorted_results[:limit]
        
    async def get_recent_memories(self, limit: int = 10) -> List[MemoryItem]:
        """Get the most recently accessed memory items across all tiers."""
        # Get recent items from each tier
        stm_recent = await self.stm_repo.get_recent(limit)
        mtm_recent = await self.mtm_repo.get_recent(limit)
        ltm_recent = await self.ltm_repo.get_recent(limit)
        
        # Combine and sort by last access timestamp (descending)
        all_recent = sorted(
            stm_recent + mtm_recent + ltm_recent,
            key=lambda item: item.health.last_access_timestamp,
            reverse=True
        )
        
        return all_recent[:limit]
```

### 5.4. API Endpoint Example

```python
# api/routes/memory.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional
from uuid import UUID

from neuroca.api.dependencies import get_memory_manager
from neuroca.api.schemas.memory import (
    MemoryItemCreate,
    MemoryItemResponse,
    MemoryItemUpdate,
    MemorySearchResponse
)
from neuroca.core.enums import MemoryTier
from neuroca.memory.manager import MemoryManager

router = APIRouter(prefix="/memory-items", tags=["memory"])

@router.post("/", response_model=MemoryItemResponse, status_code=201)
async def create_memory_item(
    memory_item: MemoryItemCreate,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Create a new memory item."""
    try:
        created_item = await memory_manager.create_memory(
            content=memory_item.content,
            tier=memory_item.tier,
            importance=memory_item.importance,
            metadata=memory_item.metadata,
            related_items=memory_item.related_items
        )
        return MemoryItemResponse.from_domain_model(created_item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memory item: {str(e)}")

@router.get("/{memory_id}", response_model=MemoryItemResponse)
async def get_memory_item(
    memory_id: UUID,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get a memory item by ID."""
    memory_item = await memory_manager.get_memory(memory_id)
    if not memory_item:
        raise HTTPException(status_code=404, detail=f"Memory item with ID {memory_id} not found")
    return MemoryItemResponse.from_domain_model(memory_item)

@router.put("/{memory_id}", response_model=MemoryItemResponse)
async def update_memory_item(
    memory_id: UUID,
    memory_update: MemoryItemUpdate,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Update a memory item."""
    # Get the existing memory item
    memory_item = await memory_manager.get_memory(memory_id)
    if not memory_item:
        raise HTTPException(status_code=404, detail=f"Memory item with ID {memory_id} not found")
    
    # Update the memory item
    if memory_update.content is not None:
        memory_item.content = memory_update.content
    if memory_update.importance is not None:
        memory_item.health.importance_flag = memory_update.importance
    if memory_update.metadata is not None:
        memory_item.metadata.update(memory_update.metadata)
    if memory_update.related_items is not None:
        memory_item.related_items = memory_update.related_items
    
    # Save the updated memory item
    updated_item = await memory_manager.update_memory(memory_item)
    return MemoryItemResponse.from_domain_model(updated_item)

@router.delete("/{memory_id}", status_code=204)
async def delete_memory_item(
    memory_id: UUID,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Delete a memory item."""
    deleted = await memory_manager.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory item with ID {memory_id} not found")
    return None

@router.post("/{memory_id}/promote", response_model=MemoryItemResponse)
async def promote_memory_item(
    memory_id: UUID,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Promote a memory item to a higher tier."""
    promoted_item = await memory_manager.promote_memory(memory_id)
    if not promoted_item:
        raise HTTPException(status_code=404, detail=f"Memory item with ID {memory_id} not found")
    return MemoryItemResponse.from_domain_model(promoted_item)

@router.post("/{memory_id}/demote", response_model=Optional[MemoryItemResponse])
async def demote_memory_item(
    memory_id: UUID,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Demote a memory item to a lower tier."""
    demoted_item = await memory_manager.demote_memory(memory_id)
    if demoted_item is None:
        # Item might have been forgotten (deleted)
        return None
    return MemoryItemResponse.from_domain_model(demoted_item)

@router.get("/search/content", response_model=MemorySearchResponse)
async def search_memories_by_content(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Search for memory items by content."""
    results = await memory_manager.search_by_content(query, limit)
    return MemorySearchResponse(
        query=query,
        results=[MemoryItemResponse.from_domain_model(item) for item in results],
        count=len(results)
    )

@router.get("/recent", response_model=List[MemoryItemResponse])
async def get_recent_memories(
    limit: int = Query(10, ge=1, le=100),
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get recently accessed memory items."""
    recent_items = await memory_manager.get_recent_memories(limit)
    return [MemoryItemResponse.from_domain_model(item) for item in recent_items]
```

## 6. Deployment and Environment Considerations

### 6.1. Development Environment

The development environment is configured using Docker Compose to provide a consistent and isolated environment for all developers. The `docker-compose.yml` file defines services for all required components:

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: infrastructure/docker/dev/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - ENVIRONMENT=development
      - REDIS_HOST=redis
      - MONGO_URI=mongodb://mongo:27017/neuroca
      - POSTGRES_URI=postgresql://postgres:postgres@postgres:5432/neuroca
      - NEO4J_URI=neo4j://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
    depends_on:
      - redis
      - mongo
      - postgres
      - neo4j
    command: uvicorn neuroca.api.app:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: infrastructure/docker/dev/Dockerfile
    volumes:
      - .:/app
    environment:
      - ENVIRONMENT=development
      - REDIS_HOST=redis
      - MONGO_URI=mongodb://mongo:27017/neuroca
      - POSTGRES_URI=postgresql://postgres:postgres@postgres:5432/neuroca
      - NEO4J_URI=neo4j://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
    depends_on:
      - redis
      - mongo
      - postgres
      - neo4j
    command: celery -A neuroca.core.tasks worker --loglevel=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  mongo:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=neuroca
    volumes:
      - postgres-data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j-data:/data

  kafka:
    image: confluentinc/cp-kafka:7.3.0
    ports:
      - "9092:9092"
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      - KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.3.0
    ports:
      - "2181:2181"
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181

volumes:
  redis-data:
  mongo-data:
  postgres-data:
  neo4j-data:
```

### 6.2. Production Environment

The production environment is deployed using Kubernetes for scalability, reliability, and manageability. The Kubernetes manifests are organized using Kustomize for environment-specific configurations:

```yaml
# infrastructure/kubernetes/base/api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neuroca-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: neuroca-api
  template:
    metadata:
      labels:
        app: neuroca-api
    spec:
      containers:
      - name: api
        image: neuroca/api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: environment
        - name: REDIS_HOST
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: redis_host
        - name: MONGO_URI
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: mongo_uri
        - name: POSTGRES_URI
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: postgres_uri
        - name: NEO4J_URI
          valueFrom:
            configMapKeyRef:
              name: neuroca-config
              key: neo4j_uri
        - name: NEO4J_USER
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: neo4j_user
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neuroca-secrets
              key: neo4j_password
---
apiVersion: v1
kind: Service
metadata:
  name: neuroca-api
spec:
  selector:
    app: neuroca-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### 6.3. CI/CD Pipeline

The CI/CD pipeline is implemented using GitHub Actions for continuous integration and ArgoCD for continuous deployment:

```yaml
# .github/workflows/ci.yml
name: NeuroCognitive Architecture CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry install
    - name: Lint with flake8
      run: |
        poetry run flake8 neuroca tests
    - name: Type check with mypy
      run: |
        poetry run mypy neuroca
    - name: Test with pytest
      run: |
        poetry run pytest tests/unit
    - name: Run integration tests
      run: |
        docker-compose up -d redis mongo postgres neo4j
        poetry run pytest tests/integration
        docker-compose down

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')
    steps:
    - uses: actions/checkout@v3
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    - name: Login to DockerHub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    - name: Build and push API image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: infrastructure/docker/api/Dockerfile
        push: true
        tags: neuroca/api:latest,neuroca/api:${{ github.sha }}
    - name: Build and push Worker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: infrastructure/docker/background/Dockerfile
        push: true
        tags: neuroca/worker:latest,neuroca/worker:${{ github.sha }}
```

## 7. Conclusion

The project structure outlined in this document provides a comprehensive foundation for implementing the NeuroCognitive Architecture (NCA) system. The structure follows best practices for Python projects, with a clear separation of concerns, modular organization, and consistent naming conventions.

Key aspects of the project structure include:

1. **Modular Organization**: The project is organized into modules based on domain areas, with clear dependencies and separation of concerns.

2. **Domain-Driven Design**: The core domain logic is separated from infrastructure concerns, with clear models and interfaces.

3. **Repository Pattern**: Data access is abstracted through repositories, providing a consistent interface across different database technologies.

4. **Dependency Injection**: Components are loosely coupled through dependency injection, facilitating testing and flexibility.

5. **Consistent Naming Conventions**: Clear and consistent naming conventions are established for all project elements, from files to database entities.

6. **Comprehensive Testing**: The structure supports unit, integration, and performance testing, with appropriate fixtures and utilities.

7. **Documentation**: Extensive documentation is included, from architecture decisions to API references and operational runbooks.

8. **Infrastructure as Code**: Deployment configurations are included for both development and production environments.

This structure supports the phased implementation approach outlined in the technology stack document, allowing for incremental development and testing of components. It also provides a solid foundation for future enhancements and optimizations.