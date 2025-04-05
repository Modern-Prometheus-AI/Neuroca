# NeuroCognitive Architecture (NCA) Makefile
# 
# This Makefile provides standardized commands for development, testing,
# deployment, and maintenance of the NeuroCognitive Architecture project.
#
# Usage:
#   make help              # Show this help message
#   make setup             # Set up development environment
#   make test              # Run all tests
#   make lint              # Run linting checks
#   make format            # Format code according to project standards
#   make build             # Build the project
#   make clean             # Clean build artifacts
#   make docs              # Generate documentation
#   make run               # Run the application locally
#   make docker-build      # Build Docker image
#   make docker-run        # Run Docker container
#   make deploy            # Deploy to target environment

# Configuration
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# Project variables
PROJECT_NAME := neuroca
PYTHON := python
PIP := pip
POETRY := poetry
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PYTEST := pytest
PYTEST_ARGS := -xvs
FLAKE8 := flake8
BLACK := black
ISORT := isort
MYPY := mypy
SPHINX_BUILD := sphinx-build
COVERAGE := coverage

# Directories
SRC_DIR := .
CORE_DIR := core
API_DIR := api
CLI_DIR := cli
MEMORY_DIR := memory
INTEGRATION_DIR := integration
TEST_DIR := tests
DOCS_DIR := docs
BUILD_DIR := build
DIST_DIR := dist

# Docker variables
DOCKER_IMAGE := $(PROJECT_NAME)
DOCKER_TAG := latest
DOCKER_FILE := Dockerfile

# Environment variables
ENV_FILE := .env
ENV_EXAMPLE := .env.example

# Default target
.PHONY: help
help:
	@echo "NeuroCognitive Architecture (NCA) Makefile"
	@echo ""
	@echo "Usage:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
.PHONY: setup
setup: ## Set up development environment
	@echo "Setting up development environment..."
	$(POETRY) install
	$(POETRY) run pre-commit install
	@if [ ! -f $(ENV_FILE) ]; then \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "Created $(ENV_FILE) from example. Please update with your settings."; \
	fi
	@echo "Setup complete."

.PHONY: update
update: ## Update dependencies
	$(POETRY) update

# Code quality
.PHONY: lint
lint: ## Run linting checks
	@echo "Running linters..."
	$(POETRY) run $(FLAKE8) $(SRC_DIR)
	$(POETRY) run $(MYPY) $(SRC_DIR)
	$(POETRY) run $(ISORT) --check --diff $(SRC_DIR)
	$(POETRY) run $(BLACK) --check $(SRC_DIR)
	@echo "Linting complete."

.PHONY: format
format: ## Format code according to project standards
	@echo "Formatting code..."
	$(POETRY) run $(ISORT) $(SRC_DIR)
	$(POETRY) run $(BLACK) $(SRC_DIR)
	@echo "Formatting complete."

# Testing
.PHONY: test
test: ## Run all tests
	@echo "Running tests..."
	$(POETRY) run $(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)
	@echo "Tests complete."

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	$(POETRY) run $(COVERAGE) run -m $(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)
	$(POETRY) run $(COVERAGE) report -m
	$(POETRY) run $(COVERAGE) html
	@echo "Coverage report generated."

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	$(POETRY) run $(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)/unit
	@echo "Unit tests complete."

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	$(POETRY) run $(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)/integration
	@echo "Integration tests complete."

# Building and running
.PHONY: build
build: clean ## Build the project
	@echo "Building project..."
	$(POETRY) build
	@echo "Build complete."

.PHONY: clean
clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR) $(DIST_DIR) .coverage htmlcov .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete."

.PHONY: run
run: ## Run the application locally
	@echo "Running application..."
	$(POETRY) run $(PYTHON) -m $(PROJECT_NAME)
	@echo "Application stopped."

# Documentation
.PHONY: docs
docs: ## Generate documentation
	@echo "Generating documentation..."
	$(POETRY) run $(SPHINX_BUILD) -b html $(DOCS_DIR)/source $(DOCS_DIR)/build/html
	@echo "Documentation generated in $(DOCS_DIR)/build/html"

.PHONY: docs-serve
docs-serve: docs ## Generate and serve documentation
	@echo "Serving documentation at http://localhost:8000..."
	cd $(DOCS_DIR)/build/html && $(PYTHON) -m http.server 8000

# Docker operations
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	$(DOCKER) build -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f $(DOCKER_FILE) .
	@echo "Docker image built."

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "Running Docker container..."
	$(DOCKER) run --rm -it -p 8000:8000 --env-file $(ENV_FILE) $(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "Docker container stopped."

.PHONY: docker-compose-up
docker-compose-up: ## Start all services with docker-compose
	@echo "Starting services with docker-compose..."
	$(DOCKER_COMPOSE) up -d
	@echo "Services started."

.PHONY: docker-compose-down
docker-compose-down: ## Stop all services with docker-compose
	@echo "Stopping services with docker-compose..."
	$(DOCKER_COMPOSE) down
	@echo "Services stopped."

# Deployment
.PHONY: deploy
deploy: ## Deploy to target environment
	@echo "Deploying to target environment..."
	@echo "This command should be customized based on your deployment strategy."
	@echo "Deployment complete."

# Database operations
.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	$(POETRY) run alembic upgrade head
	@echo "Migrations complete."

.PHONY: db-rollback
db-rollback: ## Rollback last database migration
	@echo "Rolling back last database migration..."
	$(POETRY) run alembic downgrade -1
	@echo "Rollback complete."

# Utility targets
.PHONY: check-env
check-env: ## Verify environment setup
	@echo "Checking environment setup..."
	$(POETRY) run $(PYTHON) -c "import sys; print(f'Python version: {sys.version}')"
	$(POETRY) env info
	@echo "Environment check complete."

.PHONY: security-check
security-check: ## Run security checks
	@echo "Running security checks..."
	$(POETRY) run safety check
	$(POETRY) run bandit -r $(SRC_DIR)
	@echo "Security checks complete."

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	@echo "Running pre-commit hooks..."
	$(POETRY) run pre-commit run --all-files
	@echo "Pre-commit hooks complete."

# CI/CD targets
.PHONY: ci-test
ci-test: lint test ## Run CI tests (linting and testing)
	@echo "CI tests complete."

.PHONY: ci-build
ci-build: build docker-build ## Run CI build (build and docker build)
	@echo "CI build complete."

# Default target when just running 'make'
.DEFAULT_GOAL := help