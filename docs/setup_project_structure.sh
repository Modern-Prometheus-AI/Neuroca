#!/bin/bash

# Script to create NeuroCognitive Architecture (NCA) project structure

# Function to create directory if it doesn't exist
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo "Created directory: $1"
    fi
}

# Function to create file if it doesn't exist
create_file() {
    if [ ! -f "$1" ]; then
        touch "$1"
        echo "Created file: $1"
    fi
}

# Create base directory
BASE_DIR="neuroca"
create_dir "$BASE_DIR"

# Create top-level directories
echo "Creating top-level directories..."
create_dir "$BASE_DIR/api"
create_dir "$BASE_DIR/cli"
create_dir "$BASE_DIR/config"
create_dir "$BASE_DIR/core"
create_dir "$BASE_DIR/db"
create_dir "$BASE_DIR/docs"
create_dir "$BASE_DIR/infrastructure"
create_dir "$BASE_DIR/integration"
create_dir "$BASE_DIR/memory"
create_dir "$BASE_DIR/monitoring"
create_dir "$BASE_DIR/scripts"
create_dir "$BASE_DIR/tests"
create_dir "$BASE_DIR/tools"

# Create API layer structure
echo "Creating API layer structure..."
create_dir "$BASE_DIR/api/middleware"
create_dir "$BASE_DIR/api/routes"
create_dir "$BASE_DIR/api/schemas"
create_dir "$BASE_DIR/api/websockets"

create_file "$BASE_DIR/api/__init__.py"
create_file "$BASE_DIR/api/app.py"
create_file "$BASE_DIR/api/dependencies.py"

create_file "$BASE_DIR/api/middleware/__init__.py"
create_file "$BASE_DIR/api/middleware/authentication.py"
create_file "$BASE_DIR/api/middleware/logging.py"
create_file "$BASE_DIR/api/middleware/tracing.py"

create_file "$BASE_DIR/api/routes/__init__.py"
create_file "$BASE_DIR/api/routes/health.py"
create_file "$BASE_DIR/api/routes/memory.py"
create_file "$BASE_DIR/api/routes/metrics.py"
create_file "$BASE_DIR/api/routes/system.py"

create_file "$BASE_DIR/api/schemas/__init__.py"
create_file "$BASE_DIR/api/schemas/common.py"
create_file "$BASE_DIR/api/schemas/memory.py"
create_file "$BASE_DIR/api/schemas/requests.py"
create_file "$BASE_DIR/api/schemas/responses.py"

create_file "$BASE_DIR/api/websockets/__init__.py"
create_file "$BASE_DIR/api/websockets/events.py"
create_file "$BASE_DIR/api/websockets/handlers.py"

# Create CLI structure
echo "Creating CLI structure..."
create_dir "$BASE_DIR/cli/commands"
create_dir "$BASE_DIR/cli/utils"

create_file "$BASE_DIR/cli/__init__.py"
create_file "$BASE_DIR/cli/main.py"

create_file "$BASE_DIR/cli/commands/__init__.py"
create_file "$BASE_DIR/cli/commands/db.py"
create_file "$BASE_DIR/cli/commands/memory.py"
create_file "$BASE_DIR/cli/commands/system.py"

create_file "$BASE_DIR/cli/utils/__init__.py"
create_file "$BASE_DIR/cli/utils/formatting.py"
create_file "$BASE_DIR/cli/utils/validation.py"

# Create Configuration structure
echo "Creating Configuration structure..."
create_file "$BASE_DIR/config/__init__.py"
create_file "$BASE_DIR/config/default.py"
create_file "$BASE_DIR/config/development.py"
create_file "$BASE_DIR/config/production.py"
create_file "$BASE_DIR/config/settings.py"
create_file "$BASE_DIR/config/testing.py"

# Create Core Domain Logic structure
echo "Creating Core Domain Logic structure..."
create_dir "$BASE_DIR/core/events"
create_dir "$BASE_DIR/core/health"
create_dir "$BASE_DIR/core/models"
create_dir "$BASE_DIR/core/utils"

create_file "$BASE_DIR/core/__init__.py"
create_file "$BASE_DIR/core/constants.py"
create_file "$BASE_DIR/core/enums.py"
create_file "$BASE_DIR/core/errors.py"

create_file "$BASE_DIR/core/events/__init__.py"
create_file "$BASE_DIR/core/events/handlers.py"
create_file "$BASE_DIR/core/events/memory.py"
create_file "$BASE_DIR/core/events/system.py"

create_file "$BASE_DIR/core/health/__init__.py"
create_file "$BASE_DIR/core/health/calculator.py"
create_file "$BASE_DIR/core/health/dynamics.py"
create_file "$BASE_DIR/core/health/metadata.py"
create_file "$BASE_DIR/core/health/thresholds.py"

create_file "$BASE_DIR/core/models/__init__.py"
create_file "$BASE_DIR/core/models/base.py"
create_file "$BASE_DIR/core/models/memory.py"
create_file "$BASE_DIR/core/models/relationships.py"

create_file "$BASE_DIR/core/utils/__init__.py"
create_file "$BASE_DIR/core/utils/security.py"
create_file "$BASE_DIR/core/utils/serialization.py"
create_file "$BASE_DIR/core/utils/validation.py"

# Create Database structure
echo "Creating Database structure..."
create_dir "$BASE_DIR/db/alembic"
create_dir "$BASE_DIR/db/alembic/versions"
create_dir "$BASE_DIR/db/connections"
create_dir "$BASE_DIR/db/migrations"
create_dir "$BASE_DIR/db/migrations/mongo"
create_dir "$BASE_DIR/db/migrations/neo4j"
create_dir "$BASE_DIR/db/repositories"
create_dir "$BASE_DIR/db/schemas"

create_file "$BASE_DIR/db/__init__.py"

create_file "$BASE_DIR/db/alembic/env.py"
create_file "$BASE_DIR/db/alembic/README"
create_file "$BASE_DIR/db/alembic/script.py.mako"

create_file "$BASE_DIR/db/connections/__init__.py"
create_file "$BASE_DIR/db/connections/mongo.py"
create_file "$BASE_DIR/db/connections/neo4j.py"
create_file "$BASE_DIR/db/connections/postgres.py"
create_file "$BASE_DIR/db/connections/redis.py"

create_file "$BASE_DIR/db/migrations/__init__.py"

create_file "$BASE_DIR/db/repositories/__init__.py"
create_file "$BASE_DIR/db/repositories/base.py"
create_file "$BASE_DIR/db/repositories/ltm.py"
create_file "$BASE_DIR/db/repositories/mtm.py"
create_file "$BASE_DIR/db/repositories/stm.py"

create_file "$BASE_DIR/db/schemas/__init__.py"
create_file "$BASE_DIR/db/schemas/ltm.py"
create_file "$BASE_DIR/db/schemas/mtm.py"
create_file "$BASE_DIR/db/schemas/stm.py"

# Create Documentation structure
echo "Creating Documentation structure..."
create_dir "$BASE_DIR/docs/api"
create_dir "$BASE_DIR/docs/architecture"
create_dir "$BASE_DIR/docs/architecture/decisions"
create_dir "$BASE_DIR/docs/architecture/diagrams"
create_dir "$BASE_DIR/docs/development"
create_dir "$BASE_DIR/docs/operations"
create_dir "$BASE_DIR/docs/operations/runbooks"
create_dir "$BASE_DIR/docs/user"

create_file "$BASE_DIR/docs/api/endpoints.md"
create_file "$BASE_DIR/docs/api/examples.md"
create_file "$BASE_DIR/docs/api/schemas.md"

create_file "$BASE_DIR/docs/architecture/components.md"
create_file "$BASE_DIR/docs/architecture/data_flow.md"

create_file "$BASE_DIR/docs/architecture/decisions/adr-001-memory-tiers.md"
create_file "$BASE_DIR/docs/architecture/decisions/adr-002-health-system.md"
create_file "$BASE_DIR/docs/architecture/decisions/adr-003-integration-approach.md"

create_file "$BASE_DIR/docs/architecture/diagrams/component.png"
create_file "$BASE_DIR/docs/architecture/diagrams/deployment.png"
create_file "$BASE_DIR/docs/architecture/diagrams/sequence.png"

create_file "$BASE_DIR/docs/development/contributing.md"
create_file "$BASE_DIR/docs/development/environment.md"
create_file "$BASE_DIR/docs/development/standards.md"
create_file "$BASE_DIR/docs/development/workflow.md"

create_file "$BASE_DIR/docs/operations/deployment.md"
create_file "$BASE_DIR/docs/operations/monitoring.md"

create_file "$BASE_DIR/docs/operations/runbooks/backup-restore.md"
create_file "$BASE_DIR/docs/operations/runbooks/incident-response.md"
create_file "$BASE_DIR/docs/operations/runbooks/scaling.md"

create_file "$BASE_DIR/docs/operations/troubleshooting.md"

create_file "$BASE_DIR/docs/user/configuration.md"
create_file "$BASE_DIR/docs/user/examples.md"
create_file "$BASE_DIR/docs/user/getting-started.md"
create_file "$BASE_DIR/docs/user/integration.md"

create_file "$BASE_DIR/docs/index.md"
create_file "$BASE_DIR/docs/mkdocs.yml"

# Create Infrastructure structure
echo "Creating Infrastructure structure..."
create_dir "$BASE_DIR/infrastructure/kubernetes/base"
create_dir "$BASE_DIR/infrastructure/kubernetes/overlays/development"
create_dir "$BASE_DIR/infrastructure/kubernetes/overlays/production"
create_dir "$BASE_DIR/infrastructure/kubernetes/overlays/staging"
create_dir "$BASE_DIR/infrastructure/monitoring/dashboards"
create_dir "$BASE_DIR/infrastructure/terraform/environments/development"
create_dir "$BASE_DIR/infrastructure/terraform/environments/production"
create_dir "$BASE_DIR/infrastructure/terraform/environments/staging"
create_dir "$BASE_DIR/infrastructure/terraform/modules/database"
create_dir "$BASE_DIR/infrastructure/terraform/modules/kubernetes"
create_dir "$BASE_DIR/infrastructure/terraform/modules/networking"
create_dir "$BASE_DIR/infrastructure/terraform/modules/security"
create_dir "$BASE_DIR/infrastructure/docker/api"
create_dir "$BASE_DIR/infrastructure/docker/background"
create_dir "$BASE_DIR/infrastructure/docker/dev"
create_dir "$BASE_DIR/infrastructure/docker/test"

create_file "$BASE_DIR/infrastructure/kubernetes/base/api.yaml"
create_file "$BASE_DIR/infrastructure/kubernetes/base/background.yaml"
create_file "$BASE_DIR/infrastructure/kubernetes/base/databases.yaml"
create_file "$BASE_DIR/infrastructure/kubernetes/base/monitoring.yaml"

create_file "$BASE_DIR/infrastructure/monitoring/alerts.yaml"
create_file "$BASE_DIR/infrastructure/monitoring/prometheus.yaml"

# Create LLM Integration structure
echo "Creating LLM Integration structure..."
create_dir "$BASE_DIR/integration/adapters"
create_dir "$BASE_DIR/integration/context"
create_dir "$BASE_DIR/integration/langchain"
create_dir "$BASE_DIR/integration/prompts"

create_file "$BASE_DIR/integration/__init__.py"

create_file "$BASE_DIR/integration/adapters/__init__.py"
create_file "$BASE_DIR/integration/adapters/anthropic.py"
create_file "$BASE_DIR/integration/adapters/base.py"
create_file "$BASE_DIR/integration/adapters/openai.py"
create_file "$BASE_DIR/integration/adapters/vertexai.py"

create_file "$BASE_DIR/integration/context/__init__.py"
create_file "$BASE_DIR/integration/context/injection.py"
create_file "$BASE_DIR/integration/context/manager.py"
create_file "$BASE_DIR/integration/context/retrieval.py"

create_file "$BASE_DIR/integration/langchain/__init__.py"
create_file "$BASE_DIR/integration/langchain/chains.py"
create_file "$BASE_DIR/integration/langchain/memory.py"
create_file "$BASE_DIR/integration/langchain/tools.py"

create_file "$BASE_DIR/integration/prompts/__init__.py"
create_file "$BASE_DIR/integration/prompts/memory.py"
create_file "$BASE_DIR/integration/prompts/reasoning.py"
create_file "$BASE_DIR/integration/prompts/templates.py"

# Create Memory System structure
echo "Creating Memory System structure..."
create_dir "$BASE_DIR/memory/ltm"
create_dir "$BASE_DIR/memory/mtm"
create_dir "$BASE_DIR/memory/stm"
create_dir "$BASE_DIR/memory/lymphatic"
create_dir "$BASE_DIR/memory/tubules"
create_dir "$BASE_DIR/memory/annealing"

create_file "$BASE_DIR/memory/__init__.py"
create_file "$BASE_DIR/memory/factory.py"
create_file "$BASE_DIR/memory/manager.py"

create_file "$BASE_DIR/memory/ltm/__init__.py"
create_file "$BASE_DIR/memory/ltm/manager.py"
create_file "$BASE_DIR/memory/ltm/operations.py"
create_file "$BASE_DIR/memory/ltm/storage.py"

create_file "$BASE_DIR/memory/mtm/__init__.py"
create_file "$BASE_DIR/memory/mtm/manager.py"
create_file "$BASE_DIR/memory/mtm/operations.py"
create_file "$BASE_DIR/memory/mtm/storage.py"

create_file "$BASE_DIR/memory/stm/__init__.py"
create_file "$BASE_DIR/memory/stm/manager.py"
create_file "$BASE_DIR/memory/stm/operations.py"
create_file "$BASE_DIR/memory/stm/storage.py"

create_file "$BASE_DIR/memory/lymphatic/__init__.py"
create_file "$BASE_DIR/memory/lymphatic/abstractor.py"
create_file "$BASE_DIR/memory/lymphatic/consolidator.py"
create_file "$BASE_DIR/memory/lymphatic/scheduler.py"

create_file "$BASE_DIR/memory/tubules/__init__.py"
create_file "$BASE_DIR/memory/tubules/connections.py"
create_file "$BASE_DIR/memory/tubules/pathways.py"
create_file "$BASE_DIR/memory/tubules/weights.py"

create_file "$BASE_DIR/memory/annealing/__init__.py"
create_file "$BASE_DIR/memory/annealing/optimizer.py"
create_file "$BASE_DIR/memory/annealing/phases.py"
create_file "$BASE_DIR/memory/annealing/scheduler.py"

# Create Monitoring structure
echo "Creating Monitoring structure..."
create_dir "$BASE_DIR/monitoring/health"
create_dir "$BASE_DIR/monitoring/logging"
create_dir "$BASE_DIR/monitoring/metrics"
create_dir "$BASE_DIR/monitoring/tracing"

create_file "$BASE_DIR/monitoring/__init__.py"

create_file "$BASE_DIR/monitoring/health/__init__.py"
create_file "$BASE_DIR/monitoring/health/checks.py"
create_file "$BASE_DIR/monitoring/health/probes.py"

create_file "$BASE_DIR/monitoring/logging/__init__.py"
create_file "$BASE_DIR/monitoring/logging/formatters.py"
create_file "$BASE_DIR/monitoring/logging/handlers.py"

create_file "$BASE_DIR/monitoring/metrics/__init__.py"
create_file "$BASE_DIR/monitoring/metrics/collectors.py"
create_file "$BASE_DIR/monitoring/metrics/exporters.py"
create_file "$BASE_DIR/monitoring/metrics/registry.py"

create_file "$BASE_DIR/monitoring/tracing/__init__.py"
create_file "$BASE_DIR/monitoring/tracing/middleware.py"
create_file "$BASE_DIR/monitoring/tracing/spans.py"

# Create Scripts structure
echo "Creating Scripts structure..."
create_dir "$BASE_DIR/scripts/db"
create_dir "$BASE_DIR/scripts/deployment"
create_dir "$BASE_DIR/scripts/development"
create_dir "$BASE_DIR/scripts/operations"

create_file "$BASE_DIR/scripts/db/backup.sh"
create_file "$BASE_DIR/scripts/db/initialize.sh"
create_file "$BASE_DIR/scripts/db/restore.sh"

create_file "$BASE_DIR/scripts/deployment/deploy.sh"
create_file "$BASE_DIR/scripts/deployment/rollback.sh"
create_file "$BASE_DIR/scripts/deployment/validate.sh"

create_file "$BASE_DIR/scripts/development/lint.sh"
create_file "$BASE_DIR/scripts/development/setup.sh"
create_file "$BASE_DIR/scripts/development/test.sh"

create_file "$BASE_DIR/scripts/operations/cleanup.sh"
create_file "$BASE_DIR/scripts/operations/monitor.sh"
create_file "$BASE_DIR/scripts/operations/scale.sh"

# Create Tests structure
echo "Creating Tests structure..."
create_dir "$BASE_DIR/tests/factories"
create_dir "$BASE_DIR/tests/integration/api"
create_dir "$BASE_DIR/tests/integration/db"
create_dir "$BASE_DIR/tests/integration/memory"
create_dir "$BASE_DIR/tests/performance"
create_dir "$BASE_DIR/tests/unit/api"
create_dir "$BASE_DIR/tests/unit/core"
create_dir "$BASE_DIR/tests/unit/health"
create_dir "$BASE_DIR/tests/unit/integration"
create_dir "$BASE_DIR/tests/unit/memory"
create_dir "$BASE_DIR/tests/utils"

create_file "$BASE_DIR/tests/__init__.py"
create_file "$BASE_DIR/tests/conftest.py"

create_file "$BASE_DIR/tests/factories/__init__.py"
create_file "$BASE_DIR/tests/factories/memory.py"
create_file "$BASE_DIR/tests/factories/users.py"

create_file "$BASE_DIR/tests/integration/__init__.py"

create_file "$BASE_DIR/tests/performance/__init__.py"
create_file "$BASE_DIR/tests/performance/benchmarks.py"
create_file "$BASE_DIR/tests/performance/locustfile.py"

create_file "$BASE_DIR/tests/unit/__init__.py"

create_file "$BASE_DIR/tests/utils/__init__.py"
create_file "$BASE_DIR/tests/utils/assertions.py"
create_file "$BASE_DIR/tests/utils/helpers.py"
create_file "$BASE_DIR/tests/utils/mocks.py"

# Create Tools structure
echo "Creating Tools structure..."
create_dir "$BASE_DIR/tools/analysis"
create_dir "$BASE_DIR/tools/development"
create_dir "$BASE_DIR/tools/migration"
create_dir "$BASE_DIR/tools/visualization"

create_file "$BASE_DIR/tools/analysis/memory_analyzer.py"
create_file "$BASE_DIR/tools/analysis/performance_analyzer.py"

create_file "$BASE_DIR/tools/development/code_generator.py"
create_file "$BASE_DIR/tools/development/schema_generator.py"

create_file "$BASE_DIR/tools/migration/data_migrator.py"
create_file "$BASE_DIR/tools/migration/schema_migrator.py"

create_file "$BASE_DIR/tools/visualization/memory_visualizer.py"
create_file "$BASE_DIR/tools/visualization/relationship_visualizer.py"

# Create root files
echo "Creating root files..."
create_file "$BASE_DIR/.dockerignore"
create_file "$BASE_DIR/.editorconfig"
create_file "$BASE_DIR/.env.example"
create_file "$BASE_DIR/.gitignore"
create_file "$BASE_DIR/.pre-commit-config.yaml"
create_file "$BASE_DIR/docker-compose.yml"
create_file "$BASE_DIR/Dockerfile"
create_file "$BASE_DIR/LICENSE"
create_file "$BASE_DIR/Makefile"
create_file "$BASE_DIR/poetry.lock"
create_file "$BASE_DIR/pyproject.toml"
create_file "$BASE_DIR/README.md"

echo "Project structure creation complete!"