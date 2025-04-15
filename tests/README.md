# Neuroca Tests

This directory contains the automated tests for the NeuroCognitive Architecture project. The goal is to ensure the correctness, robustness, and performance of the system through various types of testing.

## Structure

The tests are organized by type:

- **`unit/`**: Unit tests focus on isolating and testing individual components (classes, functions) in the `neuroca` source code. They typically use mocks to isolate the component under test from its dependencies.
    - Subdirectories often mirror the structure of `src/neuroca` (e.g., `tests/unit/memory/` tests components in `src/neuroca/memory/`).
- **`integration/`**: Integration tests verify the interactions between multiple components or subsystems. They might involve testing the connection between the API layer and core services, or interactions between different memory tiers and their backends. These tests use fewer mocks than unit tests, often requiring real dependencies like databases (potentially in-memory versions or test instances).
- **`end_to_end/` (or `e2e/`)**: End-to-end tests simulate real user scenarios, testing the entire system flow from input (e.g., API request) to output. These are the highest-level tests and typically involve minimal mocking.
- **`performance/`**: Performance tests measure the speed, scalability, and resource usage of the system under different loads. This might include benchmarks for specific operations or load tests using tools like Locust.
- **`factories/`**: Contains test data factories (e.g., using `factory_boy`) to generate consistent and reusable test data objects (like `MemoryItem` instances).
- **`utils/`**: Shared testing utilities, helper functions, custom assertions, or mock setups used across different tests.
- **`conftest.py`**: Contains fixtures and hooks shared across multiple test files within the `tests` directory and its subdirectories, managed by `pytest`.

## Running Tests

Tests are typically run using `pytest` from the project root directory.

```bash
# Run all tests
pytest

# Run tests in a specific directory
pytest tests/unit/memory/

# Run tests in a specific file
pytest tests/integration/api/test_process_endpoint.py

# Run a specific test function
pytest tests/unit/core/test_services.py::test_processing_logic

# Run tests with coverage reporting
pytest --cov=neuroca --cov-report=html
```

Refer to `pytest.ini` for specific configurations and markers.

## Maintenance

- Write new tests for any new features or bug fixes.
- Keep tests organized according to their type (unit, integration, etc.).
- Ensure tests are independent and do not rely on the state left by previous tests.
- Use fixtures (`conftest.py`) for setting up reusable test contexts or resources.
- Regularly review and refactor tests to keep them maintainable and efficient.
