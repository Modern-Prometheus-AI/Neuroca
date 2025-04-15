# Development Environment Setup

This document provides comprehensive instructions for setting up and configuring a development environment for the NeuroCognitive Architecture (NCA) project. Following these guidelines ensures consistency across development environments and helps new contributors get started quickly.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Environment Configuration](#environment-configuration)
- [Development Tools](#development-tools)
- [Docker Environment](#docker-environment)
- [Local Development](#local-development)
- [Testing Environment](#testing-environment)
- [Debugging](#debugging)
- [Common Issues](#common-issues)
- [Environment Maintenance](#environment-maintenance)

## Prerequisites

Before setting up the development environment, ensure you have the following installed:

- **Python**: Version 3.10 or higher
- **Git**: Latest stable version
- **Docker**: Latest stable version
- **Docker Compose**: Latest stable version
- **Poetry**: Version 1.4 or higher (Python dependency management)
- **Make**: For running Makefile commands (optional but recommended)

### Operating System Recommendations

- **Linux**: Ubuntu 22.04 LTS or newer
- **macOS**: Monterey (12) or newer
- **Windows**: Windows 10/11 with WSL2 (Ubuntu 22.04 LTS)

## Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-organization/neuroca.git
   cd neuroca
   ```

2. **Set up Git hooks**:
   ```bash
   pre-commit install
   ```

3. **Install dependencies using Poetry**:
   ```bash
   poetry install
   ```

4. **Create local environment file**:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file to configure your local environment variables.

## Environment Configuration

### Environment Variables

The NCA project uses environment variables for configuration. Key variables include:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NCA_ENV` | Environment (development, testing, production) | `development` | Yes |
| `NCA_LOG_LEVEL` | Logging level | `INFO` | No |
| `NCA_DB_URI` | Database connection URI | - | Yes |
| `NCA_API_KEY` | API key for external services | - | Depends |
| `NCA_LLM_PROVIDER` | LLM provider to use | `openai` | Yes |
| `NCA_LLM_API_KEY` | API key for LLM provider | - | Yes |

See `.env.example` for a complete list of configurable environment variables.

### Configuration Files

Configuration files are located in the `config/` directory:

- `config/default.yaml`: Default configuration values
- `config/development.yaml`: Development-specific overrides
- `config/testing.yaml`: Testing-specific overrides
- `config/production.yaml`: Production-specific overrides

## Development Tools

### Code Editor Setup

#### Visual Studio Code

Recommended extensions:
- Python
- Pylance
- Docker
- YAML
- EditorConfig
- GitLens
- Python Test Explorer

Recommended settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### PyCharm

Recommended plugins:
- Poetry
- Docker
- Makefile Support

### Linting and Formatting

The project uses the following tools:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **mypy**: Type checking

Run all checks:
```bash
make lint
```

Format code:
```bash
make format
```

## Docker Environment

The project includes Docker configuration for consistent development environments.

### Starting the Docker Environment

```bash
docker-compose up -d
```

This will start all required services:
- PostgreSQL database
- Redis cache
- Development server
- Monitoring services

### Accessing Services

- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Monitoring Dashboard**: http://localhost:9090

### Rebuilding Containers

After dependency changes:
```bash
docker-compose build
docker-compose up -d
```

## Local Development

### Activating the Virtual Environment

```bash
poetry shell
```

### Running the Application Locally

```bash
# Start required services
docker-compose up -d db redis

# Run the application
python -m neuroca.api.main
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Testing Environment

### Running Tests

```bash
# Run all tests
make test

# Run specific test module
pytest tests/path/to/test_module.py

# Run with coverage report
make test-coverage
```

### Test Database

Tests use a separate database instance to avoid affecting development data:

```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d
```

## Debugging

### Logging

Logs are written to:
- Console (during development)
- `logs/` directory
- Centralized logging service in containerized environments

Configure log level in `.env` file or via `NCA_LOG_LEVEL` environment variable.

### Debugging with VS Code

Launch configurations are provided in `.vscode/launch.json` for:
- API server
- CLI tools
- Test debugging

### Debugging with PyCharm

Run/Debug configurations are included for:
- API server
- Common test scenarios

## Common Issues

### Database Connection Issues

If you encounter database connection problems:
1. Ensure the database container is running: `docker-compose ps`
2. Check database logs: `docker-compose logs db`
3. Verify connection settings in `.env`

### Dependency Conflicts

If you encounter dependency conflicts:
1. Update Poetry lock file: `poetry update`
2. Recreate virtual environment: `poetry env remove python && poetry install`

### Docker Memory Issues

If Docker containers crash due to memory constraints:
1. Increase Docker memory allocation in Docker Desktop settings
2. For Linux, check system memory limits

## Environment Maintenance

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update specific dependency
poetry update package-name
```

### Cleaning Environment

```bash
# Remove unused containers and volumes
docker-compose down -v

# Clean Python cache files
make clean
```

### Keeping Environment in Sync

Regularly run these commands to keep your environment up to date:

```bash
git pull
poetry install
alembic upgrade head
```

---

For additional help or to report environment setup issues, please contact the development team or create an issue in the project repository.