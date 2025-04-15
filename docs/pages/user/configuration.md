# NeuroCognitive Architecture Configuration Guide

## Overview

This document provides comprehensive guidance on configuring the NeuroCognitive Architecture (NCA) system. The configuration system is designed to be flexible, allowing customization of all aspects of the NCA while maintaining sensible defaults for quick deployment.

## Configuration Methods

NCA supports multiple configuration methods, applied in the following order of precedence (highest to lowest):

1. Command-line arguments
2. Environment variables
3. Configuration files
4. Default values

This hierarchical approach allows for flexible deployment across different environments while maintaining the ability to override settings as needed.

## Configuration File

### Locations

The system searches for configuration files in the following locations:

1. Path specified via `--config` command-line argument
2. Path specified via `NEUROCA_CONFIG` environment variable
3. `./neuroca.yaml` (current working directory)
4. `~/.neuroca/config.yaml` (user's home directory)
5. `/etc/neuroca/config.yaml` (system-wide configuration)

### Format

NCA supports configuration files in YAML, JSON, and TOML formats. YAML is recommended for human readability and is used in all examples.

Example `neuroca.yaml`:

```yaml
# NeuroCognitive Architecture Configuration

# System-wide settings
system:
  log_level: "info"  # debug, info, warning, error, critical
  log_format: "json"  # text, json
  temp_directory: "/tmp/neuroca"
  max_threads: 8

# Memory system configuration
memory:
  # Working Memory
  working:
    capacity: 7  # Miller's Law default
    decay_rate: 0.05
    priority_threshold: 0.7
    
  # Short-Term Memory
  short_term:
    capacity: 100
    retention_period: "1h"  # 1 hour
    consolidation_interval: "5m"  # 5 minutes
    
  # Long-Term Memory
  long_term:
    storage_path: "./data/long_term_memory"
    vector_dimensions: 1536
    similarity_threshold: 0.75
    max_storage: "10GB"
    
  # Database settings
  database:
    type: "sqlite"  # sqlite, postgres
    connection_string: "./data/neuroca.db"
    pool_size: 5
    timeout: 30

# LLM Integration
llm:
  provider: "openai"  # openai, anthropic, local, etc.
  model: "gpt-4"
  api_key_env: "OPENAI_API_KEY"  # Name of environment variable containing API key
  temperature: 0.7
  max_tokens: 2000
  timeout: 60
  retry_attempts: 3
  retry_delay: 2

# Health System
health:
  enabled: true
  initial_values:
    energy: 100
    stability: 100
    coherence: 100
  decay_rates:
    energy: 0.01
    stability: 0.005
    coherence: 0.008
  recovery_rates:
    energy: 0.02
    stability: 0.01
    coherence: 0.015
  thresholds:
    critical: 20
    warning: 40
    normal: 70

# API Configuration
api:
  host: "127.0.0.1"
  port: 8000
  cors_origins: ["http://localhost:3000"]
  rate_limit: 100  # requests per minute
  timeout: 30  # seconds
  enable_docs: true
```

## Environment Variables

All configuration options can be set using environment variables with the prefix `NEUROCA_`. Nested configuration is represented using underscores.

Examples:

```bash
# System settings
export NEUROCA_SYSTEM_LOG_LEVEL=debug
export NEUROCA_SYSTEM_MAX_THREADS=4

# Memory settings
export NEUROCA_MEMORY_WORKING_CAPACITY=5
export NEUROCA_MEMORY_LONG_TERM_SIMILARITY_THRESHOLD=0.8

# LLM settings
export NEUROCA_LLM_PROVIDER=anthropic
export NEUROCA_LLM_MODEL=claude-2
export NEUROCA_LLM_TEMPERATURE=0.5
```

## Command-Line Arguments

The most common configuration options can be set via command-line arguments:

```bash
neuroca --log-level debug --memory-working-capacity 5 --llm-provider anthropic
```

Run `neuroca --help` for a complete list of available command-line options.

## Configuration Validation

NCA validates all configuration settings at startup. Invalid configurations will cause the system to exit with an error message detailing the issue.

Common validation checks include:

- Type checking (string, integer, float, boolean, etc.)
- Range validation (minimum/maximum values)
- Enum validation (allowed values)
- Path existence and permissions
- Dependency validation (ensuring required configurations are present)

## Sensitive Configuration

For sensitive information like API keys, we recommend using environment variables rather than configuration files. The system will look for environment variables like:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `NEUROCA_DATABASE_PASSWORD`

Never commit sensitive information to version control.

## Dynamic Configuration

Some configuration settings can be changed at runtime through the API:

```bash
curl -X PATCH http://localhost:8000/api/v1/config/llm \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.8, "max_tokens": 1500}'
```

Changes to dynamic configuration are temporary and will revert to the configured values on system restart unless persisted to a configuration file.

## Configuration Profiles

NCA supports configuration profiles for different use cases:

```yaml
# In neuroca.yaml
profiles:
  development:
    system:
      log_level: "debug"
    memory:
      database:
        type: "sqlite"
        
  production:
    system:
      log_level: "info"
    memory:
      database:
        type: "postgres"
        connection_string: "postgresql://user:password@localhost/neuroca"
```

Activate a profile using:

```bash
neuroca --profile production
# or
export NEUROCA_PROFILE=production
```

## Advanced Configuration

### Memory Tuning

Fine-tune memory parameters based on your use case:

- Increase `working.capacity` for complex reasoning tasks
- Adjust `short_term.retention_period` based on conversation length
- Modify `long_term.similarity_threshold` to control memory retrieval precision

### Health System Customization

The health system can be customized to model different cognitive states:

```yaml
health:
  custom_metrics:
    creativity:
      initial: 80
      decay_rate: 0.01
      recovery_rate: 0.02
      affects:
        - component: "llm"
          parameter: "temperature"
          mapping: "linear"
          min_value: 0.5
          max_value: 1.2
```

### Logging Configuration

Detailed logging configuration:

```yaml
system:
  logging:
    level: "info"
    format: "json"
    output: "file"  # console, file, both
    file_path: "./logs/neuroca.log"
    rotation: "10MB"
    retention: "7d"
    components:
      memory: "debug"
      llm: "info"
      api: "warning"
```

## Troubleshooting

### Common Configuration Issues

1. **Permission Denied**: Ensure the process has read/write access to configured directories
2. **Missing API Keys**: Check environment variables for required API keys
3. **Database Connection Failures**: Verify connection strings and network access
4. **Resource Limitations**: Adjust thread counts and memory settings based on hardware

### Configuration Debugging

Enable debug logging to see detailed configuration information:

```bash
neuroca --log-level debug --debug-config
```

This will output the complete, merged configuration with sources for each setting.

## Reference

For a complete reference of all configuration options, see the [Configuration Reference](../reference/configuration.md) document.