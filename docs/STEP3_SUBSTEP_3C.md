
# NeuroCognitive Architecture (NCA) Build Configuration

This document outlines the complete build configuration for the NeuroCognitive Architecture (NCA) project, including build scripts, dependency management, development tools, CI/CD pipelines, and the overall build process.

## Table of Contents

1. [Overview](#1-overview)
2. [Technology Stack](#2-technology-stack)
3. [Dependency Management](#3-dependency-management)
4. [Build Scripts](#4-build-scripts)
5. [Development Tools](#5-development-tools)
6. [CI/CD Configuration](#6-cicd-configuration)
7. [Environment Configuration](#7-environment-configuration)
8. [Build Process Documentation](#8-build-process-documentation)
9. [Security Considerations](#9-security-considerations)
10. [Performance Optimization](#10-performance-optimization)
11. [Troubleshooting](#11-troubleshooting)

## 1. Overview

The NCA build system is designed to support a complex, distributed Python application with multiple components and dependencies. The build configuration prioritizes:

- **Reproducibility**: Ensuring consistent builds across environments
- **Modularity**: Supporting independent component development and testing
- **Automation**: Minimizing manual steps in build and deployment
- **Observability**: Providing clear visibility into build and deployment status
- **Security**: Implementing secure practices throughout the build pipeline

## 2. Technology Stack

The build system is based on the following core technologies:

- **Language**: Python 3.10+
- **Package Management**: Poetry
- **Containerization**: Docker and Docker Compose
- **CI/CD**: GitHub Actions
- **Testing Framework**: Pytest
- **Code Quality**: Black, isort, flake8, mypy
- **Documentation**: Sphinx with autodoc
- **Infrastructure as Code**: Terraform (for deployment)

## 3. Dependency Management

### 3.1 Poetry for Python Dependency Management

We use Poetry for Python dependency management to ensure reproducible builds and clear dependency specifications.

#### 3.1.1 Core `pyproject.toml` Configuration

```toml
[tool.poetry]
name = "neurocognitive-architecture"
version = "0.1.0"
description = "A brain-inspired three-tiered memory system for Large Language Models"
authors = ["NCA Team <team@nca-project.org>"]
readme = "README.md"
license = "MIT"
repository = "https://github.com/nca-project/neurocognitive-architecture"
documentation = "https://docs.nca-project.org"

[tool.poetry.dependencies]
python = "^3.10"
# Core dependencies
fastapi = "^0.103.1"
pydantic = "^2.4.2"
uvicorn = "^0.23.2"
httpx = "^0.25.0"
asyncio = "^3.4.3"
aiokafka = "^0.8.1"
redis = "^5.0.0"
motor = "^3.3.1"
pymongo = "^4.5.0"
sqlalchemy = {version = "^2.0.21", extras = ["asyncio"]}
asyncpg = "^0.28.0"
psycopg = {version = "^3.1.12", extras = ["binary", "pool"]}
pgvector = "^0.2.1"
numpy = "^1.26.0"
scipy = "^1.11.3"
scikit-learn = "^1.3.1"
transformers = "^4.34.0"
torch = "^2.0.1"
sentence-transformers = "^2.2.2"
openai = "^0.28.1"
anthropic = "^0.5.0"
langchain = "^0.0.300"
tenacity = "^8.2.3"
prometheus-client = "^0.17.1"
structlog = "^23.1.0"
pyjwt = "^2.8.0"
python-dotenv = "^1.0.0"
apscheduler = "^3.10.4"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.2"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
black = "^23.9.1"
isort = "^5.12.0"
flake8 = "^6.1.0"
mypy = "^1.5.1"
pre-commit = "^3.4.0"
sphinx = "^7.2.6"
sphinx-rtd-theme = "^1.3.0"
myst-parser = "^2.0.0"
docker-compose = "^1.29.2"
faker = "^19.6.2"
hypothesis = "^6.87.0"
locust = "^2.17.0"

[tool.poetry.scripts]
nca = "nca.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

# Tool configurations
[tool.black]
line-length = 88
target-version = ["py310"]
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
```

#### 3.1.2 Component-Specific Dependencies

For larger components with specific dependencies, we use Poetry's dependency groups:

```toml
# Example for specialized embedding component
[tool.poetry.group.embeddings]
optional = true

[tool.poetry.group.embeddings.dependencies]
sentence-transformers = "^2.2.2"
faiss-cpu = "^1.7.4"
onnxruntime = "^1.15.1"
```

### 3.2 Docker-Based Dependency Management

For system-level dependencies and services, we use Docker and Docker Compose.

#### 3.2.1 Base Dockerfile

```dockerfile
# Base image for development and production
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.6.1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy only dependency definition files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not use virtualenvs in Docker
RUN poetry config virtualenvs.create false

# Development image
FROM base as development

# Install all dependencies including dev
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Production image
FROM base as production

# Install only production dependencies
RUN poetry install --no-interaction --no-ansi --no-dev

# Copy the rest of the application
COPY . .

# Run as non-root user
RUN useradd -m nca
USER nca

# Command to run the application
CMD ["uvicorn", "nca.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.2.2 Docker Compose Configuration

```yaml
version: '3.8'

services:
  # API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
      - REDIS_URI=redis://redis:6379/0
      - MONGODB_URI=mongodb://mongodb:27017/nca
      - POSTGRES_URI=postgresql://postgres:postgres@postgres:5432/nca
    depends_on:
      - redis
      - mongodb
      - postgres
      - kafka
    command: uvicorn nca.api.main:app --host 0.0.0.0 --port 8000 --reload

  # Worker Service
  worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    volumes:
      - .:/app
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
      - REDIS_URI=redis://redis:6379/0
      - MONGODB_URI=mongodb://mongodb:27017/nca
      - POSTGRES_URI=postgresql://postgres:postgres@postgres:5432/nca
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - redis
      - mongodb
      - postgres
      - kafka
    command: python -m nca.workers.main

  # Redis (STM)
  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  # MongoDB (MTM)
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb-data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=nca

  # PostgreSQL with pgvector (LTM)
  postgres:
    image: ankane/pgvector:latest
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=nca

  # Kafka (Event Bus)
  kafka:
    image: bitnami/kafka:3.4
    ports:
      - "9092:9092"
    volumes:
      - kafka-data:/bitnami/kafka
    environment:
      - KAFKA_CFG_NODE_ID=1
      - KAFKA_CFG_PROCESS_ROLES=controller,broker
      - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
      - KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER
      - ALLOW_PLAINTEXT_LISTENER=yes

  # Prometheus (Monitoring)
  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'

  # Grafana (Visualization)
  grafana:
    image: grafana/grafana:10.1.0
    ports:
      - "3000:3000"
    volumes:
      - ./config/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    depends_on:
      - prometheus

volumes:
  redis-data:
  mongodb-data:
  postgres-data:
  kafka-data:
  prometheus-data:
  grafana-data:
```

### 3.3 Dependency Versioning Strategy

1. **Pinned Dependencies**: All direct dependencies have specific version constraints to ensure reproducibility.
2. **Dependency Updates**: Automated dependency updates via Dependabot with weekly PRs.
3. **Vulnerability Scanning**: Automated scanning of dependencies for security vulnerabilities.
4. **Dependency Lockfiles**: Both `poetry.lock` and `requirements.txt` (generated from Poetry) are committed to the repository.

## 4. Build Scripts

### 4.1 Makefile for Common Tasks

We use a Makefile to provide a unified interface for common development and build tasks:

```makefile
.PHONY: setup install update clean lint format test test-cov docs build run deploy help

# Default target
.DEFAULT_GOAL := help

# Environment variables
PYTHON := python3
POETRY := poetry
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PYTEST := pytest
BLACK := black
ISORT := isort
FLAKE8 := flake8
MYPY := mypy
SPHINX_BUILD := sphinx-build

# Project variables
PROJECT_NAME := neurocognitive-architecture
DOCKER_IMAGE := nca-project/$(PROJECT_NAME)
DOCKER_TAG := latest

# Help target
help:
	@echo "NeuroCognitive Architecture (NCA) Build System"
	@echo ""
	@echo "Usage:"
	@echo "  make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup         Install development dependencies"
	@echo "  install       Install project dependencies"
	@echo "  update        Update dependencies"
	@echo "  clean         Remove build artifacts"
	@echo "  lint          Run linters (flake8, mypy)"
	@echo "  format        Format code (black, isort)"
	@echo "  test          Run tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  docs          Build documentation"
	@echo "  build         Build Docker image"
	@echo "  run           Run development server"
	@echo "  deploy        Deploy to environment (dev/staging/prod)"
	@echo "  help          Show this help message"

# Setup development environment
setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install poetry==$(shell grep "POETRY_VERSION" Dockerfile | cut -d= -f2)
	$(POETRY) install

# Install dependencies
install:
	$(POETRY) install --no-dev

# Update dependencies
update:
	$(POETRY) update

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf docs/_build

# Run linters
lint:
	$(FLAKE8) nca tests
	$(MYPY) nca tests

# Format code
format:
	$(BLACK) nca tests
	$(ISORT) nca tests

# Run tests
test:
	$(PYTEST) tests

# Run tests with coverage
test-cov:
	$(PYTEST) --cov=nca tests --cov-report=html

# Build documentation
docs:
	$(SPHINX_BUILD) docs/source docs/build

# Build Docker image
build:
	$(DOCKER) build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run development server
run:
	$(DOCKER_COMPOSE) up

# Deploy to environment
deploy:
	@if [ -z "$(ENV)" ]; then \
		echo "Usage: make deploy ENV=<dev|staging|prod>"; \
		exit 1; \
	fi
	@echo "Deploying to $(ENV) environment..."
	./scripts/deploy.sh $(ENV)
```

### 4.2 Shell Scripts for Complex Operations

For more complex build and deployment operations, we use shell scripts:

#### 4.2.1 Build Script (`scripts/build.sh`)

```bash
#!/bin/bash
set -euo pipefail

# Configuration
IMAGE_NAME="nca-project/neurocognitive-architecture"
REGISTRY="ghcr.io"
VERSION=$(poetry version -s)
GIT_SHA=$(git rev-parse --short HEAD)

# Parse arguments
ENVIRONMENT="development"
PUSH=false

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Build Docker images for NCA"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Build for environment (development|staging|production)"
    echo "  -p, --push               Push images to registry"
    echo "  -h, --help               Show this help message"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "Error: Environment must be one of: development, staging, production"
    exit 1
fi

# Build Docker image
echo "Building Docker image for $ENVIRONMENT environment..."
docker build \
    --target "$ENVIRONMENT" \
    --build-arg VERSION="$VERSION" \
    --build-arg GIT_SHA="$GIT_SHA" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    -t "$IMAGE_NAME:$VERSION" \
    -t "$IMAGE_NAME:$GIT_SHA" \
    -t "$IMAGE_NAME:latest" \
    .

# Push to registry if requested
if [ "$PUSH" = true ]; then
    echo "Pushing Docker images to registry..."
    docker tag "$IMAGE_NAME:$VERSION" "$REGISTRY/$IMAGE_NAME:$VERSION"
    docker tag "$IMAGE_NAME:$GIT_SHA" "$REGISTRY/$IMAGE_NAME:$GIT_SHA"
    docker tag "$IMAGE_NAME:latest" "$REGISTRY/$IMAGE_NAME:latest"
    
    docker push "$REGISTRY/$IMAGE_NAME:$VERSION"
    docker push "$REGISTRY/$IMAGE_NAME:$GIT_SHA"
    docker push "$REGISTRY/$IMAGE_NAME:latest"
fi

echo "Build completed successfully!"
```

#### 4.2.2 Deployment Script (`scripts/deploy.sh`)

```bash
#!/bin/bash
set -euo pipefail

# Configuration
PROJECT_NAME="neurocognitive-architecture"
REGISTRY="ghcr.io"
IMAGE_NAME="$REGISTRY/nca-project/$PROJECT_NAME"
VERSION=$(poetry version -s)
GIT_SHA=$(git rev-parse --short HEAD)

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <environment> [version]"
    echo "Deploy NCA to the specified environment"
    echo ""
    echo "Arguments:"
    echo "  environment    Target environment (dev|staging|prod)"
    echo "  version        Version to deploy (default: latest git sha)"
    exit 1
fi

ENVIRONMENT="$1"
DEPLOY_VERSION="${2:-$GIT_SHA}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "Error: Environment must be one of: dev, staging, prod"
    exit 1
fi

# Map short environment names to full names
case "$ENVIRONMENT" in
    dev)
        FULL_ENV="development"
        ;;
    staging)
        FULL_ENV="staging"
        ;;
    prod)
        FULL_ENV="production"
        ;;
esac

echo "Deploying $PROJECT_NAME version $DEPLOY_VERSION to $ENVIRONMENT environment..."

# Load environment-specific variables
if [ -f ".env.$ENVIRONMENT" ]; then
    source ".env.$ENVIRONMENT"
fi

# Ensure Terraform is initialized
echo "Initializing Terraform..."
cd terraform/$ENVIRONMENT
terraform init

# Apply Terraform configuration
echo "Applying Terraform configuration..."
terraform apply -auto-approve \
    -var="image_tag=$DEPLOY_VERSION" \
    -var="environment=$FULL_ENV"

echo "Deployment completed successfully!"
```

### 4.3 Python Build Scripts

For more complex Python-specific build tasks, we use Python scripts:

#### 4.3.1 Generate API Documentation (`scripts/generate_api_docs.py`)

```python
#!/usr/bin/env python3
"""
Generate API documentation from OpenAPI schema.
"""
import json
import os
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

# Configuration
OPENAPI_JSON_PATH = "api/openapi.json"
OPENAPI_YAML_PATH = "api/openapi.yaml"
TEMPLATE_DIR = "docs/templates"
OUTPUT_DIR = "docs/source/api"
TEMPLATE_FILE = "api_doc_template.md.jinja"


def load_openapi_spec():
    """Load OpenAPI specification from JSON or YAML file."""
    if os.path.exists(OPENAPI_JSON_PATH):
        with open(OPENAPI_JSON_PATH, "r") as f:
            return json.load(f)
    elif os.path.exists(OPENAPI_YAML_PATH):
        with open(OPENAPI_YAML_PATH, "r") as f:
            return yaml.safe_load(f)
    else:
        print(f"Error: Could not find OpenAPI spec at {OPENAPI_JSON_PATH} or {OPENAPI_YAML_PATH}")
        sys.exit(1)


def generate_docs(spec):
    """Generate Markdown documentation from OpenAPI spec."""
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Set up Jinja environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_FILE)
    
    # Render template with OpenAPI spec
    output = template.render(spec=spec)
    
    # Write output to file
    output_path = os.path.join(OUTPUT_DIR, "api_reference.md")
    with open(output_path, "w") as f:
        f.write(output)
    
    print(f"API documentation generated at {output_path}")


def main():
    """Main entry point."""
    print("Generating API documentation...")
    spec = load_openapi_spec()
    generate_docs(spec)
    print("Done!")


if __name__ == "__main__":
    main()
```

## 5. Development Tools

### 5.1 Code Quality Tools

We use several tools to ensure code quality:

#### 5.1.1 Pre-commit Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-json
    -   id: check-toml
    -   id: detect-private-key
    -   id: check-merge-conflict

-   repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort

-   repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
    -   id: flake8
        additional_dependencies: [
            flake8-docstrings,
            flake8-comprehensions,
            flake8-bugbear,
            flake8-annotations,
        ]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
    -   id: mypy
        additional_dependencies: [
            types-requests,
            types-redis,
            types-PyYAML,
        ]

-   repo: https://github.com/python-poetry/poetry
    rev: 1.6.1
    hooks:
    -   id: poetry-check
    -   id: poetry-lock

-   repo: https://github.com/zricethezav/gitleaks
    rev: v8.18.0
    hooks:
    -   id: gitleaks
```

#### 5.1.2 Editor Configuration (`.editorconfig`)

```ini
# EditorConfig is awesome: https://EditorConfig.org

# top-most EditorConfig file
root = true

# Unix-style newlines with a newline ending every file
[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

# YAML files
[*.{yml,yaml}]
indent_size = 2

# Markdown files
[*.md]
trim_trailing_whitespace = false

# JSON files
[*.json]
indent_size = 2

# Shell scripts
[*.sh]
indent_size = 2
```

### 5.2 Testing Tools

#### 5.2.1 Pytest Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    api: API tests
    memory: Memory-related tests
    health: Health system tests
    lymphatic: Lymphatic system tests
    neural: Neural tubule tests
    temporal: Temporal annealing tests
addopts = --strict-markers -v
```

#### 5.2.2 Coverage Configuration (`.coveragerc`)

```ini
[run]
source = nca
omit =
    */tests/*
    */migrations/*
    */settings/*
    */wsgi.py
    */asgi.py
    */manage.py
    */setup.py
    */__init__.py
    */conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError
    except ImportError
    def __str__
    @abstractmethod
    @abc.abstractmethod
    TYPE_CHECKING
    if TYPE_CHECKING:
    if typing.TYPE_CHECKING:

[html]
directory = htmlcov
```

### 5.3 Documentation Tools

#### 5.3.1 Sphinx Configuration (`docs/source/conf.py`)

```python
# Configuration file for the Sphinx documentation builder.
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'NeuroCognitive Architecture'
copyright = f'{datetime.now().year}, NCA Team'
author = 'NCA Team'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'myst_parser',
]

# Add any paths that contain templates
templates_path = ['_templates']

# List of patterns to exclude
exclude_patterns = []

# The theme to use
html_theme = 'sphinx_rtd_theme'

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

# Add any paths that contain custom static files
html_static_path = ['_static']

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_custom_sections = None

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable', None),
    'scipy': ('https://docs.scipy.org/doc/scipy', None),
    'torch': ('https://pytorch.org/docs/stable', None),
}

# AutoDoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'
autoclass_content = 'both'

# MyST settings
myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'dollarmath',
    'fieldlist',
    'html_admonition',
    'html_image',
    'linkify',
    'replacements',
    'smartquotes',
    'substitution',
    'tasklist',
]
```

## 6. CI/CD Configuration

### 6.1 GitHub Actions Workflows

#### 6.1.1 Main CI Pipeline (`.github/workflows/ci.yml`)

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.6.1
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Load cached dependencies
        id: cached-poetry-dependencies
        uses: actions/cache@v3
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}
      
      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --no-interaction
      
      - name: Run linters
        run: |
          poetry run flake8 nca tests
          poetry run mypy nca tests
  
  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    services:
      redis:
        image: redis:7.0-alpine
        ports:
          - 6379:6379
      mongodb:
        image: mongo:6.0
        ports:
          - 27017:27017
      postgres:
        image: ankane/pgvector:latest
        ports:
          - 5432:5432
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: nca_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.6.1
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Load cached dependencies
        id: cached-poetry-dependencies
        uses: actions/cache@v3
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}
      
      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --no-interaction
      
      - name: Run tests
        run: poetry run pytest --cov=nca tests/
        env:
          REDIS_URI: redis://localhost:6379/0
          MONGODB_URI: mongodb://localhost:27017/nca_test
          POSTGRES_URI: postgresql://postgres:postgres@localhost:5432/nca_test
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          fail_ci_if_error: false
  
  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ghcr.io/nca-project/neurocognitive-architecture
          tags: |
            type=ref,event=branch
            type=sha,format=short
            type=semver,pattern={{version}}
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
  
  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: development
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.7
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Deploy to development
        run: |
          cd terraform/dev
          terraform init
          terraform apply -auto-approve \
            -var="image_tag=sha-$(git rev-parse --short HEAD)" \
            -var="environment=development"
  
  deploy-prod:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.7
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Deploy to production
        run: |
          cd terraform/prod
          terraform init
          terraform apply -auto-approve \
            -var="image_tag=sha-$(git rev-parse --short HEAD)" \
            -var="environment=production"
```

#### 6.1.2 Dependency Update Workflow (`.github/workflows/dependencies.yml`)

```yaml
name: Update Dependencies

on:
  schedule:
    - cron: '0 0 * * 1'  # Run every Monday at midnight
  workflow_dispatch:

jobs:
  update-dependencies:
    name: Update Dependencies
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.6.1
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Update dependencies
        run: poetry update
      
      - name: Run tests
        run: |
          poetry install
          poetry run pytest
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'chore: update dependencies'
          title: 'chore: update dependencies'
          body: |
            This PR updates project dependencies to their latest compatible versions.
            
            - Updated `poetry.lock`
            
            This PR was created automatically by the dependency update workflow.
          branch: update-dependencies
          base: develop
          labels: dependencies
```

#### 6.1.3 Security Scan Workflow (`.github/workflows/security.yml`)

```yaml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Run every Sunday at midnight
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  security-scan:
    name: Security Scan
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
          pip install bandit safety
      
      - name: Run Bandit
        run: bandit -r nca -f json -o bandit-results.json
      
      - name: Run Safety
        run: safety check --full-report
      
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload Trivy scan results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### 6.2 Continuous Deployment

#### 6.2.1 Terraform Configuration for AWS ECS (Example for `terraform/prod/main.tf`)

```hcl
provider "aws" {
  region = var.aws_region
}

terraform {
  backend "s3" {
    bucket = "nca-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-west-2"
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# VPC and Networking
module "vpc" {
  source = "../modules/vpc"
  
  environment = var.environment
  cidr_block  = "10.0.0.0/16"
}

# Security Groups
module "security_groups" {
  source = "../modules/security"
  
  vpc_id      = module.vpc.vpc_id
  environment = var.environment
}

# Database Resources
module "databases" {
  source = "../modules/databases"
  
  environment     = var.environment
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  security_groups = module.security_groups.database_security_group_ids
}

# ECS Cluster
module "ecs" {
  source = "../modules/ecs"
  
  environment     = var.environment
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  security_groups = module.security_groups.app_security_group_ids
  
  image_name = "ghcr.io/nca-project/neurocognitive-architecture"
  image_tag  = var.image_tag
  
  redis_endpoint     = module.databases.redis_endpoint
  mongodb_endpoint   = module.databases.mongodb_endpoint
  postgres_endpoint  = module.databases.postgres_endpoint
  
  app_count          = 2
  worker_count       = 2
  app_cpu            = 1024
  app_memory         = 2048
  worker_cpu         = 2048
  worker_memory      = 4096
}

# Load Balancer
module "load_balancer" {
  source = "../modules/load_balancer"
  
  environment     = var.environment
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.public_subnet_ids
  security_groups = module.security_groups.lb_security_group_ids
  
  ecs_service_name = module.ecs.service_name
  ecs_service_id   = module.ecs.service_id
}

# CloudWatch Monitoring
module "monitoring" {
  source = "../modules/monitoring"
  
  environment      = var.environment
  ecs_cluster_name = module.ecs.cluster_name
  ecs_service_name = module.ecs.service_name
}

# Outputs
output "api_endpoint" {
  value = module.load_balancer.dns_name
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "redis_endpoint" {
  value     = module.databases.redis_endpoint
  sensitive = true
}

output "mongodb_endpoint" {
  value     = module.databases.mongodb_endpoint
  sensitive = true
}

output "postgres_endpoint" {
  value     = module.databases.postgres_endpoint
  sensitive = true
}
```

## 7. Environment Configuration

### 7.1 Environment Variables

We use environment variables for configuration, with different files for different environments:

#### 7.1.1 Development Environment (`.env.development`)

```
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
API_LOG_LEVEL=DEBUG
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Database Configuration
REDIS_URI=redis://redis:6379/0
MONGODB_URI=mongodb://mongodb:27017/nca
POSTGRES_URI=postgresql://postgres:postgres@postgres:5432/nca

# Memory Configuration
STM_TTL=10800  # 3 hours in seconds
MTM_TTL=1209600  # 14 days in seconds
LTM_TTL=-1  # No expiration

# Health System Configuration
HEALTH_DECAY_RATE_STM=0.05
HEALTH_DECAY_RATE_MTM=0.01
HEALTH_DECAY_RATE_LTM=0.001
HEALTH_PROMOTION_THRESHOLD=80
HEALTH_DEMOTION_THRESHOLD=20

# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-dummy-key-for-development
OPENAI_MODEL=gpt-3.5-turbo
ANTHROPIC_API_KEY=dummy-key-for-development
ANTHROPIC_MODEL=claude-2

# Lymphatic System Configuration
LYMPHATIC_CONSOLIDATION_INTERVAL=300  # 5 minutes
LYMPHATIC_BATCH_SIZE=100

# Neural Tubule Configuration
NEURAL_TUBULE_STRENGTH_THRESHOLD=0.7
NEURAL_TUBULE_MAX_CONNECTIONS=50

# Temporal Annealing Configuration
TEMPORAL_ANNEALING_SCHEDULE=adaptive
TEMPORAL_ANNEALING_INTENSITY=0.5

# Security Configuration
JWT_SECRET=development-jwt-secret-do-not-use-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400  # 24 hours

# Monitoring Configuration
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
```

#### 7.1.2 Production Environment (`.env.production`)

```
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_LOG_LEVEL=INFO
API_CORS_ORIGINS=https://app.nca-project.org

# Database Configuration
# These will be populated from secrets management in production
REDIS_URI=${REDIS_URI}
MONGODB_URI=${MONGODB_URI}
POSTGRES_URI=${POSTGRES_URI}

# Memory Configuration
STM_TTL=10800  # 3 hours in seconds
MTM_TTL=1209600  # 14 days in seconds
LTM_TTL=-1  # No expiration

# Health System Configuration
HEALTH_DECAY_RATE_STM=0.05
HEALTH_DECAY_RATE_MTM=0.01
HEALTH_DECAY_RATE_LTM=0.001
HEALTH_PROMOTION_THRESHOLD=80
HEALTH_DEMOTION_THRESHOLD=20

# LLM Configuration
LLM_PROVIDER=${LLM_PROVIDER}
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_MODEL=${OPENAI_MODEL}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ANTHROPIC_MODEL=${ANTHROPIC_MODEL}

# Lymphatic System Configuration
LYMPHATIC_CONSOLIDATION_INTERVAL=600  # 10 minutes
LYMPHATIC_BATCH_SIZE=200

# Neural Tubule Configuration
NEURAL_TUBULE_STRENGTH_THRESHOLD=0.7
NEURAL_TUBULE_MAX_CONNECTIONS=100

# Temporal Annealing Configuration
TEMPORAL_ANNEALING_SCHEDULE=fixed
TEMPORAL_ANNEALING_INTENSITY=0.7

# Security Configuration
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400  # 24 hours

# Monitoring Configuration
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
```

### 7.2 Configuration Management

We use a centralized configuration system to manage environment variables and settings:

#### 7.2.1 Configuration Module (`nca/config.py`)

```python
"""
Configuration management for the NCA system.
"""
import os
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, Field, PostgresDsn, validator


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class MemoryTier(str, Enum):
    """Memory tier types."""
    STM = "stm"
    MTM = "mtm"
    LTM = "ltm"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    VERTEX = "vertex"
    HUGGINGFACE = "huggingface"


class TemporalAnnealingSchedule(str, Enum):
    """Temporal annealing schedule types."""
    FIXED = "fixed"
    ADAPTIVE = "adaptive"
    PROGRESSIVE = "progressive"


class Settings(BaseSettings):
    """
    Application settings.
    
    All settings can be overridden by environment variables.
    """
    # General settings
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = Field(False, env="API_DEBUG")
    LOG_LEVEL: str = "INFO"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("API_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    REDIS_URI: str
    MONGODB_URI: str
    POSTGRES_URI: PostgresDsn
    
    # Memory settings
    STM_TTL: int = 10800  # 3 hours in seconds
    MTM_TTL: int = 1209600  # 14 days in seconds
    LTM_TTL: int = -1  # No expiration
    
    # Health system settings
    HEALTH_DECAY_RATE_STM: float = 0.05
    HEALTH_DECAY_RATE_MTM: float = 0.01
    HEALTH_DECAY_RATE_LTM: float = 0.001
    HEALTH_PROMOTION_THRESHOLD: int = 80
    HEALTH_DEMOTION_THRESHOLD: int = 20
    
    # LLM settings
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-2"
    
    # Lymphatic system settings
    LYMPHATIC_CONSOLIDATION_INTERVAL: int = 300  # 5 minutes
    LYMPHATIC_BATCH_SIZE: int = 100
    
    # Neural tubule settings
    NEURAL_TUBULE_STRENGTH_THRESHOLD: float = 0.7
    NEURAL_TUBULE_MAX_CONNECTIONS: int = 50
    
    # Temporal annealing settings
    TEMPORAL_ANNEALING_SCHEDULE: TemporalAnnealingSchedule = TemporalAnnealingSchedule.ADAPTIVE
    TEMPORAL_ANNEALING_INTENSITY: float = 0.5
    
    # Security settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 86400  # 24 hours
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    PROMETHEUS_PORT: int = 9090
    
    class Config:
        """Pydantic config."""
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    
    Uses LRU cache to avoid loading settings multiple times.
    """
    return Settings()
```

## 8. Build Process Documentation

### 8.1 Development Setup Guide

```markdown
# NCA Development Setup Guide

This guide will help you set up your development environment for the NeuroCognitive Architecture (NCA) project.

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Git
- Make (optional, but recommended)

## Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nca-project/neurocognitive-architecture.git
   cd neurocognitive-architecture
   ```

2. Set up the development environment:
   ```bash
   # Using Make
   make setup
   
   # Manually
   python -m pip install --upgrade pip
   python -m pip install poetry==1.6.1
   poetry install
   ```

3. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

4. Create a `.env.development` file:
   ```bash
   cp .env.example .env.development
   # Edit the file to set your local configuration
   ```

## Running the Application

### Using Docker Compose

The easiest way to run the full application stack is using Docker Compose:

```bash
# Using Make
make run

# Manually
docker-compose up
```

This will start all required services:
- API server
- Worker processes
- Redis (STM)
- MongoDB (MTM)
- PostgreSQL with pgvector (LTM)
- Kafka (Event Bus)
- Prometheus and Grafana (Monitoring)

The API will be available at http://localhost:8000.

### Running Components Individually

For development, you might want to run components individually:

1. Start the databases:
   ```bash
   docker-compose up redis mongodb postgres kafka
   ```

2. Run the API server:
   ```bash
   # Using Poetry
   poetry run uvicorn nca.api.main:app --reload
   
   # Using Python directly
   python -m nca.api.main
   ```

3. Run the worker processes:
   ```bash
   poetry run python -m nca.workers.main
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and write tests.

3. Run linters and tests:
   ```bash
   # Using Make
   make lint
   make test
   
   # Manually
   poetry run flake8 nca tests
   poetry run mypy nca tests
   poetry run pytest
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

5. Push your branch and create a pull request:
   ```bash
   git push -u origin feature/your-feature-name
   ```

## Building for Production

To build the production Docker image:

```bash
# Using Make
make build

# Using the build script
./scripts/build.sh --environment production --push
```

## Documentation

To build the documentation:

```bash
# Using Make
make docs

# Manually
poetry run sphinx-build docs/source docs/build
```

The documentation will be available at `docs/build/index.html`.
```

### 8.2 Production Deployment Guide

```markdown
# NCA Production Deployment Guide

This guide outlines the process for deploying the NeuroCognitive Architecture (NCA) system to production environments.

## Deployment Architecture

The NCA system is deployed as a set of containerized services on AWS ECS (Elastic Container Service), with the following components:

- **API Service**: FastAPI application serving the REST API
- **Worker Service**: Background processing workers
- **Redis**: ElastiCache for Redis (STM)
- **MongoDB**: DocumentDB (MTM)
- **PostgreSQL**: Amazon RDS with pgvector extension (LTM)
- **Kafka**: Amazon MSK (Event Bus)
- **Load Balancer**: Application Load Balancer
- **Monitoring**: CloudWatch, Prometheus, and Grafana

## Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform 1.5.x or higher
- Docker
- Access to the GitHub Container Registry (ghcr.io)

## Deployment Process

### 1. Build and Push Docker Images

```bash
# Build and push the Docker image
./scripts/build.sh --environment production --push
```

This script:
- Builds the Docker image for production
- Tags it with the version, git SHA, and 'latest'
- Pushes it to the GitHub Container Registry

### 2. Prepare Environment Variables

Create a `.env.production` file with the production configuration. This file should not be committed to the repository, as it contains sensitive information.

For AWS deployments, these variables will be injected from AWS Secrets Manager.

### 3. Deploy Infrastructure

```bash
# Deploy to production
./scripts/deploy.sh prod
```

This script:
- Initializes Terraform
- Applies the Terraform configuration for the production environment
- Sets up all required AWS resources
- Deploys the application containers

### 4. Verify Deployment

After deployment, verify that the system is running correctly:

```bash
# Get the API endpoint
aws ecs describe-services --cluster nca-production --services nca-api-service

# Check the health endpoint
curl https://<api-endpoint>/health
```

### 5. Monitor the Deployment

Monitor the deployment using:

- AWS CloudWatch for logs and metrics
- Prometheus and Grafana for application metrics
- AWS X-Ray for distributed tracing

## Rollback Procedure

If issues are detected with the deployment, you can roll back to a previous version:

```bash
# Roll back to a specific version
./scripts/deploy.sh prod <previous-version>
```

## Scaling

The NCA system can be scaled horizontally by adjusting the number of tasks in the ECS service:

```bash
# Scale the API service
aws ecs update-service --cluster nca-production --service nca-api-service --desired-count <count>

# Scale the worker service
aws ecs update-service --cluster nca-production --service nca-worker-service --desired-count <count>
```

## Database Maintenance

### Redis (STM)

Redis is used for short-term memory and does not require regular maintenance. Data in Redis is ephemeral and will expire based on the configured TTL.

### MongoDB (MTM)

MongoDB is used for medium-term memory and requires occasional maintenance:

```bash
# Connect to MongoDB
mongo --host <mongodb-endpoint> --username <username> --password <password>

# Run database maintenance
db.runCommand({ compact: 'memories' })
```

### PostgreSQL (LTM)

PostgreSQL is used for long-term memory and requires regular maintenance:

```bash
# Connect to PostgreSQL
psql -h <postgres-endpoint> -U <username> -d nca

# Run VACUUM ANALYZE
VACUUM ANALYZE memories;
```

## Backup and Restore

### Automated Backups

Automated backups are configured for all databases:

- Redis: Daily snapshots with 7-day retention
- MongoDB: Daily snapshots with 14-day retention
- PostgreSQL: Daily snapshots with 30-day retention

### Manual Backup

To create a manual backup:

```bash
# For PostgreSQL
pg_dump -h <postgres-endpoint> -U <username> -d nca > nca_backup_$(date +%Y%m%d).sql

# For MongoDB
mongodump --host <mongodb-endpoint> --username <username> --password <password> --db nca --out nca_backup_$(date +%Y%m%d)
```

### Restore from Backup

To restore from a backup:

```bash
# For PostgreSQL
psql -h <postgres-endpoint> -U <username> -d nca < nca_backup_20231001.sql

# For MongoDB
mongorestore --host <mongodb-endpoint> --username <username> --password <password> --db nca nca_backup_20231001/nca
```

## Security Considerations

- All database connections use TLS encryption
- Secrets are managed using AWS Secrets Manager
- Network access is restricted using security groups
- API authentication is required for all endpoints
- Regular security scans are performed on the infrastructure and application
```

## 9. Security Considerations

### 9.1 Dependency Security

- **Dependency Scanning**: Automated scanning of dependencies for security vulnerabilities using Safety and Dependabot.
- **Pinned Dependencies**: All dependencies have specific version constraints to prevent unexpected updates.
- **Minimal Dependencies**: Only necessary dependencies are included to reduce the attack surface.
- **Dependency Updates**: Regular updates of dependencies to incorporate security patches.

### 9.2 Container Security

- **Minimal Base Images**: Using slim Python images to reduce the attack surface.
- **Non-Root User**: Running containers as a non-root user in production.
- **Image Scanning**: Scanning container images for vulnerabilities using Trivy.
- **No Secrets in Images**: Secrets are injected at runtime, not built into images.
- **Read-Only Filesystem**: Using read-only filesystems where possible.

### 9.3 Infrastructure Security

- **Network Isolation**: Using VPC and security groups to isolate components.
- **Encryption**: Encrypting data at rest and in transit.
- **Least Privilege**: Using IAM roles with minimal permissions.
- **Secret Management**: Using AWS Secrets Manager for sensitive configuration.
- **Security Groups**: Restricting network access to only required ports and services.

### 9.4 Application Security

- **Input Validation**: Validating all inputs using Pydantic models.
- **Authentication**: Implementing JWT-based authentication.
- **Authorization**: Implementing role-based access control.
- **Rate Limiting**: Implementing rate limiting to prevent abuse.
- **Logging**: Comprehensive logging of security events.
- **CORS**: Restricting cross-origin requests to trusted domains.

## 10. Performance Optimization

### 10.1 Build Performance

- **Docker Layer Caching**: Optimizing Dockerfile to leverage layer caching.
- **Multi-Stage Builds**: Using multi-stage builds to reduce image size.
- **Dependency Caching**: Caching dependencies in CI/CD pipelines.
- **Parallel Builds**: Running build steps in parallel where possible.

### 10.2 Runtime Performance

- **Asynchronous Processing**: Using asynchronous processing for I/O-bound operations.
- **Connection Pooling**: Implementing connection pooling for databases.
- **Caching**: Implementing caching for frequently accessed data.
- **Batch Processing**: Processing data in batches for efficiency.
- **Resource Limits**: Setting appropriate resource limits for containers.

### 10.3 Database Performance

- **Indexing**: Creating appropriate indexes for query patterns.
- **Query Optimization**: Optimizing database queries for performance.
- **Connection Management**: Properly managing database connections.
- **Sharding**: Implementing sharding for horizontal scaling.
- **Read Replicas**: Using read replicas for read-heavy workloads.

## 11. Troubleshooting

### 11.1 Build Issues

- **Dependency Conflicts**: Resolve by updating `poetry.lock` or adjusting version constraints.
- **Docker Build Failures**: Check Docker logs and ensure Docker daemon has sufficient resources.
- **CI/CD Failures**: Review GitHub Actions logs and ensure secrets are properly configured.

### 11.2 Deployment Issues

- **Infrastructure Provisioning**: Check Terraform state and AWS CloudFormation events.
- **Container Startup**: Check container logs in CloudWatch or Docker logs.
- **Service Discovery**: Verify DNS resolution and network connectivity.

### 11.3 Runtime Issues

- **Performance Problems**: Use profiling tools and monitor resource usage.
- **Memory Leaks**: Monitor memory usage and implement proper resource cleanup.
- **Database Connectivity**: Check connection strings and network connectivity.
- **API Errors**: Review logs and implement proper error handling.