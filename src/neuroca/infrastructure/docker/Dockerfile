FROM python:3.9-slim AS builder

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.4.2

# Copy only dependency files first to leverage Docker caching
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies without development dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p /app/data/long_term /app/cache /app/logs

# Copy application code
COPY src /app/src

# Set environment variables
ENV PYTHONPATH=/app
ENV NEUROCA_ENV=production
ENV NEUROCA_CONFIG_PATH=/app/config/config.yaml

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/liveness || exit 1

# Expose the API port
EXPOSE 8000

# Create non-root user
RUN groupadd -g 1000 neuroca && \
    useradd -u 1000 -g neuroca -s /bin/bash -m neuroca

# Set permissions
RUN chown -R neuroca:neuroca /app

# Switch to non-root user
USER neuroca

# Set the entry point
CMD ["uvicorn", "src.neuroca.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
