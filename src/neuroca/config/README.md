# Neuroca Configuration

This directory manages the configuration settings for the NeuroCognitive Architecture. It allows for flexible setup of various components like memory tiers, backends, LLM integrations, and health parameters.

## Structure

- **`settings.py` (or similar)**: Often contains the main configuration loading logic, potentially using libraries like Pydantic's `BaseSettings` to load from environment variables or `.env` files.
- **Default Configuration Files**: May include base YAML or JSON files providing default values for different components (e.g., `config/backends/in_memory_config.yaml`).
- **Schema Definitions**: Pydantic models defining the structure and validation rules for different configuration sections.

## Usage

Configuration values are typically loaded at application startup and injected into the relevant components. This allows customizing the behavior of the NCA without changing the core code. Common configuration points include:

- API keys and endpoints for external services (LLMs, databases).
- Parameters for memory tiers (e.g., STM TTL, MTM capacity).
- Selection of storage backends for different memory tiers.
- Thresholds and intervals for health monitoring and memory maintenance.

## Maintenance

- Keep configuration schemas (`settings.py`) updated as new configurable parameters are added.
- Ensure default configuration files are present and reflect reasonable defaults.
- Update the `.env.example` file in the project root to include any new environment variables required for configuration.
- Avoid hardcoding configuration values directly in the application code; always load them through the configuration system.
