# NeuroCognitive Architecture (NCA) for LLMs
# Production Dockerfile
# 
# This Dockerfile implements a multi-stage build process for the NeuroCognitive Architecture,
# optimizing for security, performance, and maintainability.
#
# Features:
# - Multi-stage build to minimize final image size
# - Non-root user for security
# - Proper dependency caching
# - Health checks
# - Optimized for Python performance
# - Proper signal handling

# -----------------------------------------------------------------------------
# Base stage with common dependencies
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.5.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    # Install Poetry
    && curl -sSL https://install.python-poetry.org | python3 - \
    # Create a non-root user
    && groupadd -g 1000 neuroca \
    && useradd -u 1000 -g neuroca -s /bin/bash -m neuroca \
    # Create necessary directories with proper permissions
    && mkdir -p /app /app/data /app/logs \
    && chown -R neuroca:neuroca /app

# -----------------------------------------------------------------------------
# Development stage - includes development tools
# -----------------------------------------------------------------------------
FROM base AS development

WORKDIR $PYSETUP_PATH

# Copy project dependency files
COPY --chown=neuroca:neuroca poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry install --no-root --with dev

# Set working directory
WORKDIR /app

# Copy the rest of the application
COPY --chown=neuroca:neuroca . .

USER neuroca

# Command to run the application in development mode
CMD ["poetry", "run", "python", "-m", "neuroca.cli.main"]

# -----------------------------------------------------------------------------
# Builder stage - for compiling and building dependencies
# -----------------------------------------------------------------------------
FROM base AS builder

WORKDIR $PYSETUP_PATH

# Copy project dependency files
COPY --chown=neuroca:neuroca poetry.lock pyproject.toml ./

# Install runtime dependencies only
RUN poetry install --no-root --only main

# Copy the rest of the application
COPY --chown=neuroca:neuroca . .

# Build the application (if needed)
RUN poetry build

# -----------------------------------------------------------------------------
# Production stage - minimal image for running the application
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    VENV_PATH="/opt/pysetup/.venv" \
    PATH="/opt/pysetup/.venv/bin:$PATH"

# Install system runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    # Create a non-root user
    && groupadd -g 1000 neuroca \
    && useradd -u 1000 -g neuroca -s /bin/bash -m neuroca \
    # Create necessary directories with proper permissions
    && mkdir -p /app /app/data /app/logs \
    && chown -R neuroca:neuroca /app /app/data /app/logs

# Copy virtual environment from builder
COPY --from=builder --chown=neuroca:neuroca $VENV_PATH $VENV_PATH

# Copy application code
COPY --from=builder --chown=neuroca:neuroca /app /app

WORKDIR /app

# Switch to non-root user
USER neuroca

# Set up health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -m neuroca.monitoring.health_check || exit 1

# Use tini as init to handle signals properly
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default command
CMD ["python", "-m", "neuroca.api.main"]

# Expose API port
EXPOSE 8000

# Label the image with metadata
LABEL maintainer="NeuroCognitive Architecture Team" \
      description="NeuroCognitive Architecture (NCA) for LLMs" \
      version="0.1.0"