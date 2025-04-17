# Contributing to NeuroCognitive Architecture (NCA)

Thank you for your interest in contributing to the NeuroCognitive Architecture (NCA) project! This document provides guidelines and instructions for contributing to make the process smooth and effective for everyone involved.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Project Setup](#project-setup)
  - [Development Environment](#development-environment)
- [Development Workflow](#development-workflow)
  - [Branching Strategy](#branching-strategy)
  - [Commit Guidelines](#commit-guidelines)
  - [Pull Request Process](#pull-request-process)
- [Package Building and Distribution](#package-building-and-distribution)
  - [Building the Package](#building-the-package)
  - [Testing Installation](#testing-installation)
  - [Publishing to PyPI](#publishing-to-pypi)
- [Coding Standards](#coding-standards)
  - [Python Style Guide](#python-style-guide)
  - [Documentation Guidelines](#documentation-guidelines)
  - [Testing Requirements](#testing-requirements)
- [Architecture Guidelines](#architecture-guidelines)
- [Review Process](#review-process)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)
- [Community Communication](#community-communication)
- [License](#license)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and follow our [Code of Conduct](../community/code_of_conduct.md).

## Getting Started

### Project Setup

1. **Fork the repository**: Start by forking the main repository to your GitHub account.

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/neuroca.git
   cd neuroca
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-org/neuroca.git
   ```

### Development Environment

1. **Install dependencies**:
   We use Poetry for dependency management:
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python3 -

   # Install dependencies
   poetry install
   ```

2. **Set up pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Docker environment** (optional but recommended):
   ```bash
   docker-compose up -d
   ```

## Development Workflow

### Branching Strategy

We follow a modified GitFlow workflow:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features or enhancements
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent fixes for production
- `release/*`: Release preparation

Always create new branches from `develop` unless you're working on a hotfix.

### Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) for clear and structured commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types include:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Example:
```
feat(memory): implement working memory decay function

Add time-based decay to working memory items based on the
forgetting curve algorithm.

Closes #123
```

### Pull Request Process

1. **Create a focused PR**: Each PR should address a single concern.
2. **Update documentation**: Include updates to relevant documentation.
3. **Add tests**: Include tests for new functionality or bug fixes.
4. **Ensure CI passes**: All tests, linting, and other checks must pass.
5. **Request review**: Assign reviewers once your PR is ready.
6. **Address feedback**: Respond to all review comments and make necessary changes.
7. **Squash commits**: Before merging, squash commits into logical units.

## Package Building and Distribution

The NeuroCognitive Architecture (NCA) is distributed as a Python package. This section provides guidelines for building, testing, and publishing the package.

### Building the Package

We use Poetry for package management and building:

```bash
# Ensure your poetry.toml and pyproject.toml are properly configured
# Increment version in pyproject.toml according to semantic versioning

# Build the package (creates both wheel and sdist)
poetry build
```

Alternatively, you can use the standard Python build tools:

```bash
# Install build if not already installed
pip install build

# Build the package
python -m build
```

This will create distribution packages in the `dist/` directory.

### Testing Installation

Before publishing, test the installation of your package locally:

```bash
# Create a temporary virtual environment
python -m venv .venv-test-pkg

# Activate the environment
# On Windows:
.\.venv-test-pkg\Scripts\activate
# On Unix/MacOS:
source .venv-test-pkg/bin/activate

# Install the package from the local build
pip install dist/*.whl  # or dist/*.tar.gz for the source distribution

# Test basic import
python -c "import neuroca; print('Successfully imported neuroca')"

# Deactivate when done
deactivate
```

### Publishing to PyPI

Only maintainers with appropriate permissions should publish to PyPI:

```bash
# Ensure you have TestPyPI and PyPI credentials configured
# First, test with TestPyPI
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish --repository testpypi

# If everything looks good on TestPyPI, publish to PyPI
poetry publish

# Alternatively, using twine
pip install twine
twine upload dist/*
```

Remember to create a Git tag for each published version:

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

## Coding Standards

### Python Style Guide

- We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications.
- Maximum line length is 100 characters.
- Use type hints for all function parameters and return values.
- Use docstrings for all modules, classes, and functions.

We use the following tools to enforce standards:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

### Documentation Guidelines

- Use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
- Document all public APIs, classes, and functions.
- Include examples in docstrings where appropriate.
- Keep documentation up-to-date with code changes.
- Add inline comments for complex logic.

Example:
```python
def process_memory_item(item: MemoryItem, decay_factor: float = 0.5) -> MemoryItem:
    """
    Process a memory item with decay based on time elapsed.
    
    Args:
        item: The memory item to process
        decay_factor: Factor controlling decay rate (0.0-1.0)
        
    Returns:
        Processed memory item with updated activation
        
    Raises:
        ValueError: If decay_factor is outside valid range
    
    Example:
        >>> item = MemoryItem(content="test", activation=1.0, timestamp=time.time()-3600)
        >>> processed = process_memory_item(item)
        >>> processed.activation < 1.0
        True
    """
```

### Testing Requirements

- All new code should have corresponding tests.
- Aim for at least 80% test coverage for new code.
- Include unit tests, integration tests, and where appropriate, end-to-end tests.
- Test edge cases and error conditions.
- Use pytest for writing and running tests.

## Architecture Guidelines

- Follow the domain-driven design principles established in the project.
- Maintain separation of concerns between layers.
- Respect the three-tiered memory system architecture.
- Use dependency injection to make components testable.
- Follow the SOLID principles.
- Document architectural decisions that deviate from the established patterns.

## Review Process

- All code changes require at least one review before merging.
- Reviewers should check for:
  - Correctness
  - Test coverage
  - Code quality and style
  - Documentation
  - Performance considerations
  - Security implications
- Be respectful and constructive in reviews.
- Address all review comments before requesting re-review.

## Issue Reporting

When reporting issues, please use the issue templates provided and include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. Environment details (OS, Python version, etc.)
6. Screenshots or logs if applicable

## Feature Requests

For feature requests, please:

1. Check existing issues and discussions to avoid duplicates
2. Use the feature request template
3. Clearly describe the problem the feature would solve
4. Suggest an approach if you have one in mind
5. Be open to discussion and refinement

## Community Communication

- **GitHub Discussions**: For general questions and discussions
- **Issue Tracker**: For bugs and feature requests
- **Slack/Discord**: For real-time communication (links provided in project README)
- **Regular Community Calls**: Schedule posted in the README

## License

By contributing to NeuroCognitive Architecture, you agree that your contributions will be licensed under the project's license. See the [LICENSE](../../LICENSE) file for details.

---

Thank you for contributing to NeuroCognitive Architecture! Your efforts help build a more robust and innovative cognitive architecture for LLMs.
