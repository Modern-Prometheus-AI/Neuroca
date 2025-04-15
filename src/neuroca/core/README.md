# Neuroca Core

This directory houses the central domain logic, data models, and core services of the NeuroCognitive Architecture. It represents the heart of the system, orchestrating the interactions between different cognitive components like memory, health, and processing.

## Structure

- **Models**: Contains the primary data structures used throughout the application (e.g., `MemoryItem`, `HealthState`, `CognitiveEvent`). These models define the fundamental entities the system works with.
- **Services**: Implements the core business logic and use cases (e.g., `ProcessingService`, `MemoryConsolidationService`, `HealthMonitor`). Services often interact with multiple components (like memory tiers or external integrations).
- **Interfaces/Ports**: Defines abstract interfaces for interacting with external systems or infrastructure components (following hexagonal architecture principles, if applicable).
- **Exceptions**: Custom exception classes specific to the core domain logic.
- **Sub-domains**: May contain subdirectories for major functional areas like `health`, `attention`, or `learning` if the complexity warrants further organization.

## Usage

Components outside the `core` directory (like `api`, `cli`, or `integration`) interact with the core services to perform cognitive tasks. The core layer aims to be independent of specific delivery mechanisms (like HTTP API or CLI) and infrastructure details (like specific database implementations).

## Maintenance

- Changes to core business rules or fundamental data structures belong here.
- Strive to keep the core domain logic clean and decoupled from infrastructure concerns.
- Ensure core models are well-defined and validated (e.g., using Pydantic).
- When adding significant new cognitive capabilities, consider organizing them within appropriate sub-domains.
