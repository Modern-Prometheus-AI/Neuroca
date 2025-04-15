# NeuroCognitive Architecture - Table of Contents

This document provides a central navigation point for all documentation in the NeuroCognitive Architecture (NCA) project.

## Main Project Documentation

- [**Project Overview (README.md)**](README.md) - Main project description and entry point

## Core Documentation

### User Documentation
- [Getting Started](docs/user/getting-started.md) - Quick start guide for new users
- [Configuration](docs/user/configuration.md) - Configuration options and settings
- [Examples](docs/user/examples.md) - Usage examples and patterns
- [Advanced Usage](docs/user/advanced-usage.md) - Advanced features and techniques
- [Extensions](docs/user/extensions.md) - Building custom extensions
- [Integration](docs/user/integration.md) - Integrating with other systems

### Architecture Documentation
- [Components](docs/architecture/components.md) - Core system components
- [Data Flow](docs/architecture/data_flow.md) - Information flow between components
- [Architecture Decisions](docs/architecture/architecture_decisions.md) - Key architecture decisions

#### Memory System Architecture
- [Component Interactions](docs/architecture/memory_system_component_interactions.md) - How memory components work together
- [Backend Configuration](docs/architecture/memory_system_backend_configuration.md) - Configuring memory backends
- [Directory Structure](docs/architecture/memory_system_directory_structure.md) - Memory system codebase organization
- [Deployment Guide](docs/architecture/memory_system_deployment_guide.md) - Deploying memory systems
- [Refactoring](docs/architecture/memory_system_refactoring.md) - Memory system refactoring plans
- [Test Plan](docs/architecture/memory_system_test_plan.md) - Testing the memory system
- [Thread Safety Fixes](docs/architecture/memory_system_thread_safety_fixes.md) - Thread safety improvements

#### Architecture Decision Records (ADRs)
- [ADR-001: Memory Tiers](docs/architecture/decisions/adr-001-memory-tiers.md) - Memory tier architecture decisions
- [ADR-002: Health System](docs/architecture/decisions/adr-002-health-system.md) - Health system architecture decisions
- [ADR-003: Integration Approach](docs/architecture/decisions/adr-003-integration-approach.md) - Integration architecture decisions

### API Documentation
- [API Reference](docs/api/reference.md) - Complete API reference
- [Endpoints](docs/api/endpoints.md) - REST API endpoints
- [Schemas](docs/api/schemas.md) - API data schemas
- [Examples](docs/api/examples.md) - API usage examples

### Health System Documentation
- [Health System Overview](docs/health_system/README.md) - Introduction to the Health System
- [Technical Benefits](docs/health_system/technical_benefits.md) - Benefits of the Health System
- [Implementation Guide](docs/health_system/implementation_guide.md) - Implementing the Health System

### LangChain Integration
- [LangChain Overview](docs/langchain/index.md) - Introduction to LangChain integration
- [Chains](docs/langchain/chains.md) - Using LangChain chains
- [Memory](docs/langchain/memory.md) - LangChain memory components
- [Tools](docs/langchain/tools.md) - Using LangChain tools

### Development Documentation
- [Contributing](docs/development/contributing.md) - How to contribute to NCA
- [Environment Setup](docs/development/environment.md) - Setting up development environment
- [Coding Standards](docs/development/standards.md) - NCA coding standards
- [Development Workflow](docs/development/workflow.md) - Development process

### Operations Documentation
- [Deployment](docs/operations/deployment.md) - Deployment instructions
- [Monitoring](docs/operations/monitoring.md) - Monitoring the system
- [Troubleshooting](docs/operations/troubleshooting.md) - Troubleshooting guide

#### Operations Runbooks
- [Backup & Restore](docs/operations/runbooks/backup-restore.md) - Backup and restoration procedures
- [Incident Response](docs/operations/runbooks/incident-response.md) - Handling incidents
- [Scaling](docs/operations/runbooks/scaling.md) - Scaling the system

## Architecture Diagrams

### System-Level Diagrams
- [Diagram Index](docs/architecture/diagrams/index.md) - All architecture diagrams
- [System Architecture](docs/architecture/diagrams/system-architecture.md) - High-level system architecture

### Component Diagrams

#### Cognitive Control
- [Cognitive Control Overview](docs/architecture/diagrams/cognitive-control/overview.md) - Cognitive control system overview
- [Cognitive Control Index](docs/architecture/diagrams/cognitive-control/index.md) - Cognitive control diagrams
- [Goals Component](docs/architecture/diagrams/cognitive-control/components/goals.md) - Goal management system
- [Inhibition Component](docs/architecture/diagrams/cognitive-control/components/inhibition.md) - Inhibition system
- [Metacognition Component](docs/architecture/diagrams/cognitive-control/components/metacognition.md) - Metacognition system
- [Planning Component](docs/architecture/diagrams/cognitive-control/components/planning.md) - Planning system

#### Memory System
- [Memory System Overview](docs/architecture/diagrams/memory-system/overview.md) - Memory system overview
- [Memory System Index](docs/architecture/diagrams/memory-system/index.md) - Memory system diagrams
- [Memory Tiers](docs/architecture/diagrams/memory-system/tiers.md) - Memory tier architecture
- [Memory Backends](docs/architecture/diagrams/memory-system/components/backends.md) - Storage backends
- [Lymphatic System](docs/architecture/diagrams/memory-system/components/lymphatic.md) - Memory maintenance system

#### Health System
- [Health System Overview](docs/architecture/diagrams/health-system/overview.md) - Health system overview
- [Health System Index](docs/architecture/diagrams/health-system/index.md) - Health system diagrams
- [Monitoring Component](docs/architecture/diagrams/health-system/components/monitoring.md) - Health monitoring
- [Dynamics Component](docs/architecture/diagrams/health-system/components/dynamics.md) - Health dynamics
- [Registry Component](docs/architecture/diagrams/health-system/components/registry.md) - Component registry

#### Integration
- [Integration Index](docs/architecture/diagrams/integration/index.md) - Integration diagrams
- [LangChain Integration](docs/architecture/diagrams/integration/langchain.md) - LangChain integration
- [LLM Integration](docs/architecture/diagrams/integration/components/llm.md) - LLM integration
- [API Integration](docs/architecture/diagrams/integration/components/apis.md) - API integration

#### Infrastructure & Data Flow
- [Infrastructure Overview](docs/architecture/diagrams/infrastructure/index.md) - Infrastructure architecture
- [Data Flow Overview](docs/architecture/diagrams/data-flow/index.md) - Data flow architecture

## Source Code Documentation

### Core Modules
- [API Module](src/neuroca/api/README.md) - API implementation
- [Assets Module](src/neuroca/assets/README.md) - Static assets
- [Config Module](src/neuroca/config/README.md) - Configuration system
- [Core Module](src/neuroca/core/README.md) - Core domain logic
- [Integration Module](src/neuroca/integration/README.md) - External integrations
- [Memory Module](src/neuroca/memory/README.md) - Memory system

### Tools & Scripts
- [Scripts Overview](scripts/README.md) - Utility scripts
- [Plutonium Tool](plutonium_tool/README.md) - Project analysis tool
- [Tests Overview](tests/README.md) - Testing documentation

## References & Guidelines
- [MkDocs Configuration](docs/mkdocs.yml) - Documentation site configuration
- [Docs Overview](docs/README.md) - Documentation organization

---

*Note: For a browsable documentation site, run `mkdocs serve` in the Neuroca/docs directory.*
