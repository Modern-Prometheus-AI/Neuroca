# NeuroCognitive Architecture (NCA) for LLMs - Project Structure

## Project Organization

The NeuroCognitive Architecture project follows a modular, domain-driven design approach to ensure maintainability, scalability, and clear separation of concerns. The structure is organized to support both Python and Rust components, with a focus on testability and clean architecture principles.

## Directory Structure

```
neurocognitive-architecture/
├── .github/                      # GitHub-specific files
│   ├── workflows/                # CI/CD pipeline definitions
│   └── ISSUE_TEMPLATE/           # Issue and PR templates
├── docs/                         # Documentation
│   ├── architecture/             # Architecture diagrams and descriptions
│   ├── api/                      # API documentation
│   ├── guides/                   # User and developer guides
│   └── examples/                 # Usage examples and tutorials
├── src/                          # Main source code
│   ├── nca/                      # Python package root
│   │   ├── __init__.py           # Package initialization
│   │   ├── api/                  # API and service interfaces
│   │   ├── config/               # Configuration management
│   │   ├── core/                 # Core domain logic
│   │   ├── memory/               # Memory tier implementations
│   │   ├── health/               # Health system implementation
│   │   ├── lymphatic/            # Memory Lymphatic System
│   │   ├── tubules/              # Neural Tubule Networks
│   │   ├── scheduler/            # Temporal Annealing Scheduler
│   │   ├── llm/                  # LLM integration components
│   │   ├── utils/                # Utility functions and helpers
│   │   └── monitoring/           # Monitoring and observability
│   └── rust/                     # Rust components
│       ├── lymphatic/            # Rust implementation of Memory Lymphatic System
│       └── tubules/              # Rust implementation of Neural Tubule Networks
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── performance/              # Performance and benchmark tests
│   └── fixtures/                 # Test fixtures and data
├── scripts/                      # Utility scripts
│   ├── setup/                    # Setup and installation scripts
│   ├── migration/                # Database migration scripts
│   └── benchmarks/               # Benchmark scripts
├── examples/                     # Example implementations
│   ├── openai/                   # OpenAI integration examples
│   ├── huggingface/              # Hugging Face integration examples
│   └── anthropic/                # Anthropic integration examples
├── deployment/                   # Deployment configurations
│   ├── docker/                   # Docker configurations
│   ├── kubernetes/               # Kubernetes manifests
│   └── terraform/                # Infrastructure as code
├── notebooks/                    # Jupyter notebooks for demos and exploration
├── .gitignore                    # Git ignore file
├── .pre-commit-config.yaml       # Pre-commit hooks configuration
├── pyproject.toml                # Python project configuration (Poetry)
├── Cargo.toml                    # Rust project configuration
├── README.md                     # Project overview
└── LICENSE                       # License information
```

## Key Files and Their Purposes

### Core Configuration Files

- `pyproject.toml`: Defines Python project metadata, dependencies, and build configuration using Poetry
- `Cargo.toml`: Defines Rust project metadata and dependencies
- `.pre-commit-config.yaml`: Configuration for pre-commit hooks to ensure code quality
- `README.md`: Project overview, quick start guide, and basic documentation
- `LICENSE`: Project license information

### Python Package Structure

#### Package Initialization

- `src/nca/__init__.py`: Package version, public API exports, and initialization

#### API Layer

- `src/nca/api/router.py`: FastAPI router definitions
- `src/nca/api/endpoints/`: Individual API endpoint implementations
- `src/nca/api/schemas.py`: Pydantic models for API request/response validation
- `src/nca/api/dependencies.py`: FastAPI dependency injection components

#### Configuration Management

- `src/nca/config/settings.py`: Application settings using Pydantic BaseSettings
- `src/nca/config/logging.py`: Logging configuration
- `src/nca/config/constants.py`: System-wide constants

#### Core Domain Logic

- `src/nca/core/models.py`: Core domain models
- `src/nca/core/exceptions.py`: Custom exception definitions
- `src/nca/core/interfaces.py`: Abstract base classes and interfaces

#### Memory Tier Implementations

- `src/nca/memory/base.py`: Base memory tier interface
- `src/nca/memory/stm/`: Short-Term Memory implementation
- `src/nca/memory/mtm/`: Medium-Term Memory implementation
- `src/nca/memory/ltm/`: Long-Term Memory implementation
- `src/nca/memory/factory.py`: Factory for creating memory tier instances

#### Health System

- `src/nca/health/metadata.py`: Health metadata structure definitions
- `src/nca/health/calculator.py`: Health score calculation algorithms
- `src/nca/health/dynamics.py`: Promotion/demotion logic between tiers
- `src/nca/health/forgetting.py`: Strategic forgetting mechanisms

#### Memory Lymphatic System

- `src/nca/lymphatic/consolidation.py`: Memory consolidation processes
- `src/nca/lymphatic/abstraction.py`: Concept abstraction logic
- `src/nca/lymphatic/deduplication.py`: Redundancy detection and merging

#### Neural Tubule Networks

- `src/nca/tubules/network.py`: Network structure implementation
- `src/nca/tubules/connections.py`: Connection management
- `src/nca/tubules/weights.py`: Relationship weighting algorithms
- `src/nca/tubules/traversal.py`: Network traversal and exploration

#### Temporal Annealing Scheduler

- `src/nca/scheduler/scheduler.py`: Main scheduler implementation
- `src/nca/scheduler/phases.py`: Processing phase definitions
- `src/nca/scheduler/policies.py`: Scheduling policies

#### LLM Integration

- `src/nca/llm/base.py`: Base LLM integration interface
- `src/nca/llm/openai.py`: OpenAI-specific integration
- `src/nca/llm/huggingface.py`: Hugging Face integration
- `src/nca/llm/anthropic.py`: Anthropic integration
- `src/nca/llm/context.py`: Context window management
- `src/nca/llm/retrieval.py`: Memory retrieval for LLM context

### Rust Components

- `src/rust/lymphatic/src/lib.rs`: Rust implementation of Memory Lymphatic System
- `src/rust/tubules/src/lib.rs`: Rust implementation of Neural Tubule Networks

### Deployment Files

- `deployment/docker/Dockerfile`: Main application Dockerfile
- `deployment/docker/docker-compose.yml`: Development environment setup
- `deployment/kubernetes/helm/`: Helm charts for Kubernetes deployment

## Module Organization

The project follows a domain-driven design approach with the following key modules:

1. **API Layer**: Handles external communication, request validation, and response formatting
2. **Memory Tier Modules**: Implements the three memory tiers with their specific storage backends
3. **Health System**: Manages memory item health, promotion/demotion, and forgetting
4. **Advanced Components**: Implements the Memory Lymphatic System, Neural Tubule Networks, and Temporal Annealing Scheduler
5. **LLM Integration**: Provides seamless integration with various LLM providers
6. **Core Domain**: Contains shared domain models and business logic
7. **Utilities**: Provides helper functions and common utilities
8. **Monitoring**: Implements observability, metrics, and logging

## Naming Conventions

### Python Conventions

- **Packages and Modules**: Lowercase with underscores (snake_case)
  - Example: `memory_tier.py`, `health_calculator.py`

- **Classes**: CapitalizedWords (PascalCase)
  - Example: `MemoryItem`, `HealthCalculator`, `NeuralTubuleNetwork`

- **Functions and Methods**: Lowercase with underscores (snake_case)
  - Example: `calculate_health()`, `retrieve_memory()`, `update_connections()`

- **Constants**: All uppercase with underscores
  - Example: `DEFAULT_HEALTH_THRESHOLD`, `MAX_STM_SIZE`

- **Private Methods/Attributes**: Prefixed with underscore
  - Example: `_calculate_internal_score()`, `_connection_cache`

### Rust Conventions

- **Crates and Modules**: Lowercase with underscores (snake_case)
  - Example: `memory_lymphatic`, `neural_tubules`

- **Structs and Enums**: CapitalizedWords (PascalCase)
  - Example: `MemoryNode`, `ConnectionType`

- **Functions and Methods**: Lowercase with underscores (snake_case)
  - Example: `process_batch()`, `calculate_similarity()`

- **Constants**: All uppercase with underscores
  - Example: `MAX_BATCH_SIZE`, `DEFAULT_THRESHOLD`

### File Organization Conventions

- **Implementation Files**: Named after the primary class or functionality they contain
  - Example: `health_calculator.py` contains the `HealthCalculator` class

- **Interface Files**: Named with descriptive terms or suffixed with `_interface`
  - Example: `memory_interface.py`, `llm_provider.py`

- **Test Files**: Prefixed with `test_` followed by the name of the module being tested
  - Example: `test_health_calculator.py`, `test_stm_storage.py`

## Development Workflow

The project uses a feature-based development workflow:

1. Each feature or component is developed in a separate branch
2. Unit tests are written alongside the implementation
3. Integration tests verify component interactions
4. Performance tests ensure the system meets latency requirements
5. Code reviews enforce quality standards and architectural consistency
6. CI/CD pipelines automate testing and deployment

This structure provides a solid foundation for implementing the NeuroCognitive Architecture while maintaining code quality, testability, and scalability throughout the development process.