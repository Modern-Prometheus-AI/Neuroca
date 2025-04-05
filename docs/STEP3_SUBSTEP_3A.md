
# NeuroCognitive Architecture (NCA) - Directory Structure

This document outlines the complete directory structure for the NeuroCognitive Architecture (NCA) project, designed to support the three-tiered memory system, health dynamics, and advanced biological-inspired components.

## 1. Root Directory Structure

```
neuroca/                          # Project root directory
├── src/                          # Source code
│   ├── api/                      # API interfaces
│   ├── application/              # Application layer
│   ├── domain/                   # Domain layer
│   ├── infrastructure/           # Infrastructure layer
│   └── interface/                # Interface layer
├── tests/                        # Test code
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── system/                   # System tests
│   ├── performance/              # Performance tests
│   └── fixtures/                 # Test fixtures
├── docs/                         # Documentation
│   ├── architecture/             # Architecture documentation
│   ├── api/                      # API documentation
│   ├── development/              # Development guides
│   ├── deployment/               # Deployment guides
│   └── diagrams/                 # System diagrams
├── scripts/                      # Utility scripts
│   ├── setup/                    # Setup scripts
│   ├── deployment/               # Deployment scripts
│   ├── monitoring/               # Monitoring scripts
│   └── maintenance/              # Maintenance scripts
├── config/                       # Configuration files
│   ├── development/              # Development configuration
│   ├── testing/                  # Testing configuration
│   ├── staging/                  # Staging configuration
│   └── production/               # Production configuration
├── deploy/                       # Deployment configurations
│   ├── docker/                   # Docker configurations
│   ├── kubernetes/               # Kubernetes configurations
│   ├── terraform/                # Terraform configurations
│   └── ansible/                  # Ansible configurations
├── examples/                     # Example code and usage
├── tools/                        # Development tools
├── .github/                      # GitHub configurations
│   ├── workflows/                # GitHub Actions workflows
│   └── ISSUE_TEMPLATE/           # Issue templates
├── .vscode/                      # VS Code configurations
├── .gitignore                    # Git ignore file
├── .dockerignore                 # Docker ignore file
├── pyproject.toml                # Python project configuration
├── poetry.lock                   # Poetry lock file
├── README.md                     # Project README
├── CONTRIBUTING.md               # Contribution guidelines
├── LICENSE                       # License file
└── CHANGELOG.md                  # Change log
```

## 2. Detailed Directory Structure

### 2.1. Source Code (`src/`)

The `src/` directory follows a layered architecture pattern, separating concerns according to the hexagonal (ports and adapters) architecture.

```
src/
├── api/                          # API interfaces
│   ├── rest/                     # REST API
│   │   ├── controllers/          # API controllers
│   │   ├── middleware/           # API middleware
│   │   ├── schemas/              # API schemas
│   │   ├── routes/               # API routes
│   │   └── errors/               # API error handlers
│   ├── websocket/                # WebSocket API
│   │   ├── handlers/             # WebSocket handlers
│   │   ├── middleware/           # WebSocket middleware
│   │   └── schemas/              # WebSocket schemas
│   ├── graphql/                  # GraphQL API (future expansion)
│   └── __init__.py               # Package initialization
├── application/                  # Application layer
│   ├── services/                 # Application services
│   │   ├── memory_service.py     # Memory service
│   │   ├── health_service.py     # Health service
│   │   ├── context_service.py    # Context service
│   │   └── system_service.py     # System service
│   ├── commands/                 # Command handlers
│   │   ├── memory_commands.py    # Memory commands
│   │   ├── health_commands.py    # Health commands
│   │   └── system_commands.py    # System commands
│   ├── queries/                  # Query handlers
│   │   ├── memory_queries.py     # Memory queries
│   │   ├── health_queries.py     # Health queries
│   │   └── system_queries.py     # System queries
│   ├── dtos/                     # Data transfer objects
│   │   ├── memory_dtos.py        # Memory DTOs
│   │   ├── health_dtos.py        # Health DTOs
│   │   └── system_dtos.py        # System DTOs
│   ├── mappers/                  # Object mappers
│   │   ├── memory_mappers.py     # Memory mappers
│   │   ├── health_mappers.py     # Health mappers
│   │   └── system_mappers.py     # System mappers
│   ├── exceptions/               # Application exceptions
│   └── __init__.py               # Package initialization
├── domain/                       # Domain layer
│   ├── memory/                   # Memory domain
│   │   ├── models/               # Memory models
│   │   │   ├── memory_item.py    # Memory item model
│   │   │   ├── memory_tier.py    # Memory tier model
│   │   │   └── memory_health.py  # Memory health model
│   │   ├── services/             # Memory domain services
│   │   │   ├── memory_factory.py # Memory factory
│   │   │   └── memory_manager.py # Memory manager
│   │   ├── repositories/         # Memory repositories (interfaces)
│   │   │   ├── stm_repository.py # STM repository interface
│   │   │   ├── mtm_repository.py # MTM repository interface
│   │   │   └── ltm_repository.py # LTM repository interface
│   │   ├── events/               # Memory domain events
│   │   │   ├── memory_created.py # Memory created event
│   │   │   ├── memory_updated.py # Memory updated event
│   │   │   └── memory_deleted.py # Memory deleted event
│   │   ├── exceptions/           # Memory domain exceptions
│   │   └── __init__.py           # Package initialization
│   ├── health/                   # Health domain
│   │   ├── models/               # Health models
│   │   ├── services/             # Health domain services
│   │   ├── repositories/         # Health repositories (interfaces)
│   │   ├── events/               # Health domain events
│   │   ├── exceptions/           # Health domain exceptions
│   │   └── __init__.py           # Package initialization
│   ├── lymphatic/                # Lymphatic system domain
│   │   ├── models/               # Lymphatic models
│   │   ├── services/             # Lymphatic domain services
│   │   ├── repositories/         # Lymphatic repositories (interfaces)
│   │   ├── events/               # Lymphatic domain events
│   │   ├── exceptions/           # Lymphatic domain exceptions
│   │   └── __init__.py           # Package initialization
│   ├── neural_tubules/           # Neural tubules domain
│   │   ├── models/               # Neural tubules models
│   │   ├── services/             # Neural tubules domain services
│   │   ├── repositories/         # Neural tubules repositories (interfaces)
│   │   ├── events/               # Neural tubules domain events
│   │   ├── exceptions/           # Neural tubules domain exceptions
│   │   └── __init__.py           # Package initialization
│   ├── temporal_annealing/       # Temporal annealing domain
│   │   ├── models/               # Temporal annealing models
│   │   ├── services/             # Temporal annealing domain services
│   │   ├── repositories/         # Temporal annealing repositories (interfaces)
│   │   ├── events/               # Temporal annealing domain events
│   │   ├── exceptions/           # Temporal annealing domain exceptions
│   │   └── __init__.py           # Package initialization
│   ├── common/                   # Common domain components
│   │   ├── models/               # Common models
│   │   ├── services/             # Common domain services
│   │   ├── events/               # Common domain events
│   │   ├── exceptions/           # Common domain exceptions
│   │   └── __init__.py           # Package initialization
│   └── __init__.py               # Package initialization
├── infrastructure/               # Infrastructure layer
│   ├── persistence/              # Persistence infrastructure
│   │   ├── redis/                # Redis implementation
│   │   │   ├── repositories/     # Redis repositories
│   │   │   ├── models/           # Redis models
│   │   │   ├── connection.py     # Redis connection
│   │   │   └── __init__.py       # Package initialization
│   │   ├── mongodb/              # MongoDB implementation
│   │   │   ├── repositories/     # MongoDB repositories
│   │   │   ├── models/           # MongoDB models
│   │   │   ├── connection.py     # MongoDB connection
│   │   │   └── __init__.py       # Package initialization
│   │   ├── postgresql/           # PostgreSQL implementation
│   │   │   ├── repositories/     # PostgreSQL repositories
│   │   │   ├── models/           # PostgreSQL models
│   │   │   ├── connection.py     # PostgreSQL connection
│   │   │   └── __init__.py       # Package initialization
│   │   └── __init__.py           # Package initialization
│   ├── messaging/                # Messaging infrastructure
│   │   ├── event_bus/            # Event bus implementation
│   │   ├── task_queue/           # Task queue implementation
│   │   ├── scheduler/            # Scheduler implementation
│   │   └── __init__.py           # Package initialization
│   ├── embedding/                # Embedding infrastructure
│   │   ├── providers/            # Embedding providers
│   │   ├── models/               # Embedding models
│   │   ├── cache/                # Embedding cache
│   │   └── __init__.py           # Package initialization
│   ├── security/                 # Security infrastructure
│   │   ├── authentication/       # Authentication implementation
│   │   ├── authorization/        # Authorization implementation
│   │   ├── encryption/           # Encryption implementation
│   │   └── __init__.py           # Package initialization
│   ├── monitoring/               # Monitoring infrastructure
│   │   ├── logging/              # Logging implementation
│   │   ├── metrics/              # Metrics implementation
│   │   ├── tracing/              # Tracing implementation
│   │   └── __init__.py           # Package initialization
│   ├── llm/                      # LLM infrastructure
│   │   ├── adapters/             # LLM adapters
│   │   ├── models/               # LLM models
│   │   ├── cache/                # LLM cache
│   │   └── __init__.py           # Package initialization
│   ├── config/                   # Configuration infrastructure
│   │   ├── providers/            # Configuration providers
│   │   ├── models/               # Configuration models
│   │   └── __init__.py           # Package initialization
│   └── __init__.py               # Package initialization
├── interface/                    # Interface layer
│   ├── llm/                      # LLM interfaces
│   │   ├── adapters/             # LLM adapter interfaces
│   │   ├── models/               # LLM interface models
│   │   └── __init__.py           # Package initialization
│   ├── cli/                      # CLI interfaces
│   │   ├── commands/             # CLI commands
│   │   ├── helpers/              # CLI helpers
│   │   └── __init__.py           # Package initialization
│   ├── web/                      # Web interfaces (future expansion)
│   │   ├── controllers/          # Web controllers
│   │   ├── views/                # Web views
│   │   └── __init__.py           # Package initialization
│   └── __init__.py               # Package initialization
└── __init__.py                   # Package initialization
```

### 2.2. Tests (`tests/`)

The `tests/` directory follows a structured approach to testing, separating different types of tests.

```
tests/
├── unit/                         # Unit tests
│   ├── api/                      # API unit tests
│   ├── application/              # Application unit tests
│   ├── domain/                   # Domain unit tests
│   ├── infrastructure/           # Infrastructure unit tests
│   └── interface/                # Interface unit tests
├── integration/                  # Integration tests
│   ├── api/                      # API integration tests
│   ├── application/              # Application integration tests
│   ├── domain/                   # Domain integration tests
│   ├── infrastructure/           # Infrastructure integration tests
│   └── interface/                # Interface integration tests
├── system/                       # System tests
│   ├── memory_flow/              # Memory flow tests
│   ├── health_flow/              # Health flow tests
│   ├── lymphatic_flow/           # Lymphatic flow tests
│   └── neural_tubules_flow/      # Neural tubules flow tests
├── performance/                  # Performance tests
│   ├── memory_performance/       # Memory performance tests
│   ├── health_performance/       # Health performance tests
│   ├── lymphatic_performance/    # Lymphatic performance tests
│   └── neural_tubules_performance/ # Neural tubules performance tests
├── fixtures/                     # Test fixtures
│   ├── memory_fixtures/          # Memory fixtures
│   ├── health_fixtures/          # Health fixtures
│   ├── lymphatic_fixtures/       # Lymphatic fixtures
│   └── neural_tubules_fixtures/  # Neural tubules fixtures
├── conftest.py                   # Pytest configuration
└── __init__.py                   # Package initialization
```

### 2.3. Documentation (`docs/`)

The `docs/` directory contains comprehensive documentation for the project.

```
docs/
├── architecture/                 # Architecture documentation
│   ├── overview.md               # Architecture overview
│   ├── components.md             # Component documentation
│   ├── patterns.md               # Architectural patterns
│   ├── decisions.md              # Architecture decisions
│   └── constraints.md            # Architecture constraints
├── api/                          # API documentation
│   ├── rest/                     # REST API documentation
│   ├── websocket/                # WebSocket API documentation
│   └── graphql/                  # GraphQL API documentation
├── development/                  # Development guides
│   ├── setup.md                  # Setup guide
│   ├── workflow.md               # Development workflow
│   ├── testing.md                # Testing guide
│   ├── style.md                  # Style guide
│   └── contributing.md           # Contribution guide
├── deployment/                   # Deployment guides
│   ├── docker.md                 # Docker deployment
│   ├── kubernetes.md             # Kubernetes deployment
│   ├── terraform.md              # Terraform deployment
│   └── ansible.md                # Ansible deployment
├── diagrams/                     # System diagrams
│   ├── architecture/             # Architecture diagrams
│   ├── sequence/                 # Sequence diagrams
│   ├── class/                    # Class diagrams
│   └── deployment/               # Deployment diagrams
├── user/                         # User documentation
│   ├── getting_started.md        # Getting started guide
│   ├── configuration.md          # Configuration guide
│   ├── api_usage.md              # API usage guide
│   └── troubleshooting.md        # Troubleshooting guide
└── index.md                      # Documentation index
```

### 2.4. Configuration (`config/`)

The `config/` directory contains configuration files for different environments.

```
config/
├── development/                  # Development configuration
│   ├── app.yaml                  # Application configuration
│   ├── logging.yaml              # Logging configuration
│   ├── database.yaml             # Database configuration
│   └── security.yaml             # Security configuration
├── testing/                      # Testing configuration
│   ├── app.yaml                  # Application configuration
│   ├── logging.yaml              # Logging configuration
│   ├── database.yaml             # Database configuration
│   └── security.yaml             # Security configuration
├── staging/                      # Staging configuration
│   ├── app.yaml                  # Application configuration
│   ├── logging.yaml              # Logging configuration
│   ├── database.yaml             # Database configuration
│   └── security.yaml             # Security configuration
├── production/                   # Production configuration
│   ├── app.yaml                  # Application configuration
│   ├── logging.yaml              # Logging configuration
│   ├── database.yaml             # Database configuration
│   └── security.yaml             # Security configuration
└── schema/                       # Configuration schemas
    ├── app.schema.json           # Application schema
    ├── logging.schema.json       # Logging schema
    ├── database.schema.json      # Database schema
    └── security.schema.json      # Security schema
```

### 2.5. Deployment (`deploy/`)

The `deploy/` directory contains deployment configurations for different platforms.

```
deploy/
├── docker/                       # Docker configurations
│   ├── Dockerfile                # Main Dockerfile
│   ├── docker-compose.yml        # Docker Compose file
│   ├── docker-compose.dev.yml    # Development Docker Compose
│   ├── docker-compose.test.yml   # Testing Docker Compose
│   └── docker-compose.prod.yml   # Production Docker Compose
├── kubernetes/                   # Kubernetes configurations
│   ├── base/                     # Base configurations
│   │   ├── deployment.yaml       # Deployment configuration
│   │   ├── service.yaml          # Service configuration
│   │   ├── configmap.yaml        # ConfigMap configuration
│   │   └── secret.yaml           # Secret configuration
│   ├── overlays/                 # Environment overlays
│   │   ├── development/          # Development overlay
│   │   ├── staging/              # Staging overlay
│   │   └── production/           # Production overlay
│   └── kustomization.yaml        # Kustomization file
├── terraform/                    # Terraform configurations
│   ├── modules/                  # Terraform modules
│   │   ├── vpc/                  # VPC module
│   │   ├── rds/                  # RDS module
│   │   ├── elasticache/          # ElastiCache module
│   │   └── eks/                  # EKS module
│   ├── environments/             # Environment configurations
│   │   ├── development/          # Development environment
│   │   ├── staging/              # Staging environment
│   │   └── production/           # Production environment
│   └── variables.tf              # Terraform variables
└── ansible/                      # Ansible configurations
    ├── inventory/                # Ansible inventory
    │   ├── development           # Development inventory
    │   ├── staging               # Staging inventory
    │   └── production            # Production inventory
    ├── playbooks/                # Ansible playbooks
    │   ├── setup.yml             # Setup playbook
    │   ├── deploy.yml            # Deployment playbook
    │   └── maintenance.yml       # Maintenance playbook
    └── roles/                    # Ansible roles
        ├── common/               # Common role
        ├── database/             # Database role
        ├── application/          # Application role
        └── monitoring/           # Monitoring role
```

### 2.6. Scripts (`scripts/`)

The `scripts/` directory contains utility scripts for various operations.

```
scripts/
├── setup/                        # Setup scripts
│   ├── install_dependencies.sh   # Install dependencies
│   ├── setup_databases.sh        # Setup databases
│   └── generate_secrets.sh       # Generate secrets
├── deployment/                   # Deployment scripts
│   ├── build.sh                  # Build script
│   ├── deploy.sh                 # Deploy script
│   └── rollback.sh               # Rollback script
├── monitoring/                   # Monitoring scripts
│   ├── check_health.sh           # Health check script
│   ├── collect_metrics.sh        # Metrics collection script
│   └── generate_report.sh        # Report generation script
├── maintenance/                  # Maintenance scripts
│   ├── backup.sh                 # Backup script
│   ├── restore.sh                # Restore script
│   └── cleanup.sh                # Cleanup script
└── development/                  # Development scripts
    ├── lint.sh                   # Linting script
    ├── format.sh                 # Formatting script
    └── generate_docs.sh          # Documentation generation script
```

## 3. Directory Organization Patterns

### 3.1. Layered Architecture Pattern

The source code is organized according to a layered architecture pattern, with clear separation between:

- **Interface Layer**: External interfaces (API, CLI, LLM)
- **Application Layer**: Application services, commands, and queries
- **Domain Layer**: Core domain models, services, and repositories
- **Infrastructure Layer**: Technical implementations of repositories, messaging, etc.

This pattern ensures:

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Dependency Inversion**: Higher layers depend on abstractions, not implementations
3. **Testability**: Each layer can be tested in isolation
4. **Maintainability**: Changes in one layer don't affect other layers

### 3.2. Feature-Based Organization

Within each layer, code is organized by feature or domain concept:

- Memory
- Health
- Lymphatic System
- Neural Tubules
- Temporal Annealing

This organization makes it easy to:

1. **Locate Code**: Find all code related to a specific feature
2. **Understand Boundaries**: Clearly see the boundaries between features
3. **Assign Ownership**: Assign ownership of features to specific teams
4. **Scale Development**: Allow multiple teams to work on different features simultaneously

### 3.3. Package-by-Layer Pattern

Within each feature, code is organized by layer:

- Models
- Services
- Repositories
- Events
- Exceptions

This organization makes it easy to:

1. **Understand Responsibilities**: Clearly see the responsibilities of each component
2. **Follow Conventions**: Apply consistent patterns across features
3. **Reuse Patterns**: Reuse architectural patterns across features
4. **Enforce Boundaries**: Enforce layer boundaries through package structure

### 3.4. Environment-Based Configuration

Configuration is organized by environment:

- Development
- Testing
- Staging
- Production

This organization makes it easy to:

1. **Switch Environments**: Easily switch between environments
2. **Isolate Changes**: Make environment-specific changes without affecting other environments
3. **Ensure Consistency**: Ensure consistent configuration across environments
4. **Manage Secrets**: Manage secrets separately for each environment

### 3.5. Test Organization Pattern

Tests are organized by test type:

- Unit Tests
- Integration Tests
- System Tests
- Performance Tests

This organization makes it easy to:

1. **Run Specific Tests**: Run only specific types of tests
2. **Understand Test Purpose**: Clearly understand the purpose of each test
3. **Enforce Test Boundaries**: Enforce boundaries between test types
4. **Optimize Test Execution**: Optimize test execution for different test types

## 4. Future Expansion Considerations

### 4.1. New Features

The directory structure is designed to accommodate new features:

1. **Add New Domain Components**: Add new directories under `src/domain/` for new domain components
2. **Add New Infrastructure Components**: Add new directories under `src/infrastructure/` for new infrastructure components
3. **Add New Interfaces**: Add new directories under `src/interface/` for new interfaces

Example for adding a new "Semantic Network" feature:

```
src/domain/semantic_network/
├── models/
├── services/
├── repositories/
├── events/
├── exceptions/
└── __init__.py
```

### 4.2. New Integrations

The directory structure is designed to accommodate new integrations:

1. **Add New LLM Providers**: Add new adapters under `src/infrastructure/llm/adapters/`
2. **Add New Database Providers**: Add new implementations under `src/infrastructure/persistence/`
3. **Add New Messaging Providers**: Add new implementations under `src/infrastructure/messaging/`

Example for adding a new LLM provider:

```
src/infrastructure/llm/adapters/
├── openai_adapter.py
├── anthropic_adapter.py
├── new_provider_adapter.py  # New provider
└── __init__.py
```

### 4.3. Scaling Considerations

The directory structure is designed to scale:

1. **Microservices Split**: The layered architecture makes it easy to split into microservices if needed
2. **Module Extraction**: Features can be extracted into separate modules or packages
3. **Team Organization**: Teams can be organized around features or layers

Example for splitting into microservices:

```
neuroca-memory-service/
neuroca-health-service/
neuroca-lymphatic-service/
neuroca-neural-tubules-service/
neuroca-temporal-annealing-service/
neuroca-api-gateway/
```

### 4.4. Technology Evolution

The directory structure is designed to accommodate technology evolution:

1. **Framework Independence**: The core domain is independent of frameworks
2. **Infrastructure Abstraction**: Infrastructure implementations can be replaced
3. **Interface Flexibility**: New interfaces can be added without affecting the core

Example for replacing Redis with another in-memory database:

```
src/infrastructure/persistence/
├── redis/                # Current implementation
├── memcached/            # New implementation
└── __init__.py
```

## 5. Build and Deployment Considerations

### 5.1. Containerization

The directory structure supports containerization:

1. **Dockerfile**: Located at `deploy/docker/Dockerfile`
2. **Docker Compose**: Located at `deploy/docker/docker-compose.yml`
3. **Docker Ignore**: Located at `.dockerignore`

The Docker setup can build different images for different components:

```dockerfile
# Base image
FROM python:3.11-slim AS base

# Development image
FROM base AS development
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Production image
FROM base AS production
COPY requirements.txt .
RUN pip install -r requirements.txt
```

### 5.2. Continuous Integration/Continuous Deployment (CI/CD)

The directory structure supports CI/CD:

1. **GitHub Actions**: Located at `.github/workflows/`
2. **Jenkins Pipeline**: Can be added as `Jenkinsfile`
3. **GitLab CI**: Can be added as `.gitlab-ci.yml`

Example GitHub Actions workflow:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install
      - name: Run tests
        run: poetry run pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t neuroca:latest .
```

### 5.3. Infrastructure as Code (IaC)

The directory structure supports Infrastructure as Code:

1. **Terraform**: Located at `deploy/terraform/`
2. **Kubernetes**: Located at `deploy/kubernetes/`
3. **Ansible**: Located at `deploy/ansible/`

These configurations can be used to deploy the application to different environments:

```
deploy/terraform/environments/
├── development/
├── staging/
└── production/
```

### 5.4. Configuration Management

The directory structure supports configuration management:

1. **Environment Variables**: Can be defined in `.env` files
2. **Configuration Files**: Located at `config/`
3. **Secrets Management**: Can be integrated with tools like HashiCorp Vault

Example configuration loading:

```python
import os
import yaml
from pathlib import Path

def load_config():
    env = os.getenv("ENVIRONMENT", "development")
    config_path = Path(f"config/{env}/app.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
```

## 6. Conclusion

The proposed directory structure for the NeuroCognitive Architecture (NCA) project follows best practices for a production-ready system:

1. **Layered Architecture**: Clear separation of concerns
2. **Feature-Based Organization**: Easy to locate and understand code
3. **Environment-Based Configuration**: Easy to switch between environments
4. **Comprehensive Testing**: Different types of tests for different purposes
5. **Deployment Flexibility**: Support for different deployment strategies
6. **Future-Proof Design**: Easy to extend and evolve

This structure provides a solid foundation for building a complex system like the NCA, with considerations for scalability, maintainability, and extensibility.