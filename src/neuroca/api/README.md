# Neuroca API

This directory contains the code related to the NeuroCognitive Architecture's Application Programming Interface (API). It handles incoming requests, routes them to the appropriate core services, and formats the responses.

## Structure

- **Endpoints**: Defines the specific API routes (e.g., `/process`, `/memory`, `/health`).
- **Schemas**: Contains Pydantic models for request validation and response serialization (often using shared models from `neuroca.core` or defining API-specific ones).
- **Dependencies**: Manages shared dependencies or utilities specific to the API layer (e.g., authentication, request context).
- **Server**: The main application setup (e.g., using FastAPI) that ties together the endpoints and configurations.

## Usage

The API provides the primary interface for external systems to interact with the NCA. Clients send HTTP requests to the defined endpoints to trigger cognitive processing, manage memory, or check system status.

## Maintenance

- When adding new API functionality, define new endpoints and corresponding request/response schemas.
- Ensure API schemas stay synchronized with core data models.
- Update API documentation (e.g., OpenAPI/Swagger) when changes are made.
