# Development Workflow

This document outlines the development workflow for the NeuroCognitive Architecture (NCA) project. It provides guidelines for code development, testing, review, and deployment processes to ensure consistent, high-quality contributions across the team.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Branching Strategy](#branching-strategy)
- [Development Lifecycle](#development-lifecycle)
- [Code Quality Standards](#code-quality-standards)
- [Testing Guidelines](#testing-guidelines)
- [Code Review Process](#code-review-process)
- [Continuous Integration](#continuous-integration)
- [Deployment Process](#deployment-process)
- [Documentation Requirements](#documentation-requirements)
- [Issue and Bug Tracking](#issue-and-bug-tracking)
- [Release Management](#release-management)

## Development Environment Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Git
- Poetry (for dependency management)
- Make (optional, for running Makefile commands)

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/neuroca.git
   cd neuroca
   ```

2. Set up the environment:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your local configuration
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

5. Start the development environment:
   ```bash
   docker-compose up -d
   ```

## Branching Strategy

We follow a Git Flow-inspired branching strategy:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features or enhancements
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent fixes for production
- `release/*`: Release preparation

### Branch Naming Conventions

- Feature branches: `feature/issue-number-short-description`
- Bug fix branches: `bugfix/issue-number-short-description`
- Hotfix branches: `hotfix/issue-number-short-description`
- Release branches: `release/vX.Y.Z`

## Development Lifecycle

1. **Issue Creation**: All work begins with an issue in the issue tracker
2. **Branch Creation**: Create a branch from `develop` using the appropriate naming convention
3. **Development**: Implement the feature or fix
4. **Testing**: Write and run tests locally
5. **Code Review**: Submit a pull request and address feedback
6. **Integration**: Merge into `develop` after approval
7. **Release**: Merge into `main` as part of a release
8. **Deployment**: Deploy to production

### Commit Guidelines

- Use conventional commit messages:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `style:` for formatting changes
  - `refactor:` for code refactoring
  - `test:` for adding or modifying tests
  - `chore:` for maintenance tasks

- Include the issue number in the commit message: `feat(memory): Implement working memory system (#123)`

## Code Quality Standards

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable and function names

### Linting and Formatting

The following tools are configured in the pre-commit hooks:

- Black for code formatting
- isort for import sorting
- Flake8 for linting
- mypy for type checking

Run checks manually:
```bash
poetry run pre-commit run --all-files
```

## Testing Guidelines

### Test Coverage Requirements

- Minimum test coverage: 80%
- All core functionality must have unit tests
- Integration tests for component interactions
- End-to-end tests for critical user flows

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=neuroca

# Run specific test file
poetry run pytest tests/path/to/test_file.py
```

## Code Review Process

1. **Pull Request Creation**:
   - Create a pull request from your feature branch to `develop`
   - Fill out the PR template with details about the changes
   - Link the relevant issue(s)

2. **Review Requirements**:
   - At least one approval from a core team member
   - All CI checks must pass
   - No unresolved comments

3. **Merge Process**:
   - Squash and merge for feature branches
   - Rebase and merge for hotfixes

## Continuous Integration

Our CI pipeline includes:

1. Linting and code style checks
2. Unit and integration tests
3. Test coverage reporting
4. Security scanning
5. Build validation

## Deployment Process

### Environments

- **Development**: Automatic deployment from the `develop` branch
- **Staging**: Manual deployment from release branches
- **Production**: Manual deployment from the `main` branch

### Deployment Steps

1. Create a release branch from `develop`: `release/vX.Y.Z`
2. Perform final testing and fixes on the release branch
3. Create a pull request to merge into `main`
4. After approval, merge to `main` and tag the release
5. Deploy to production using the CI/CD pipeline

## Documentation Requirements

### Code Documentation

- All modules, classes, and functions must have docstrings
- Use Google-style docstrings format
- Document parameters, return values, and exceptions

### Project Documentation

- Architecture documentation in `/docs/architecture/`
- API documentation in `/docs/api/`
- User guides in `/docs/guides/`
- Development documentation in `/docs/development/`

## Issue and Bug Tracking

- Use GitHub Issues for tracking bugs and features
- Label issues appropriately (bug, enhancement, documentation, etc.)
- Include steps to reproduce for bug reports
- Link issues to relevant pull requests

## Release Management

### Versioning

We follow Semantic Versioning (SemVer):
- **Major version**: Incompatible API changes
- **Minor version**: Backward-compatible new features
- **Patch version**: Backward-compatible bug fixes

### Release Notes

- Document all significant changes in CHANGELOG.md
- Categorize changes (Added, Changed, Fixed, Removed)
- Include contributor acknowledgments

### Release Process

1. Update version numbers in relevant files
2. Update CHANGELOG.md with release notes
3. Create a release branch: `release/vX.Y.Z`
4. Create a pull request to `main`
5. After merging, tag the release in Git
6. Create a GitHub Release with release notes

## Troubleshooting

### Common Issues

- **Environment setup problems**: Check the `.env` file and Docker logs
- **Dependency conflicts**: Update Poetry lock file with `poetry update`
- **Pre-commit hook failures**: Run hooks manually to see detailed errors

### Getting Help

- Check the project wiki for common solutions
- Ask in the development Slack channel
- Create an issue with the "question" label

---

This workflow document is a living guide and will be updated as our processes evolve. All team members are encouraged to suggest improvements through pull requests.