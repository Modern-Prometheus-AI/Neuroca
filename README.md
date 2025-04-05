# NeuroCognitive Architecture (NCA) for LLMs

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

## Overview

NeuroCognitive Architecture (NCA) is an advanced framework that enhances Large Language Models (LLMs) with biologically-inspired cognitive capabilities. By implementing a three-tiered memory system, health dynamics, and neurological processes, NCA enables LLMs to exhibit more human-like reasoning, contextual understanding, and adaptive behavior.

## Key Features

- **Three-Tiered Memory System**:
  - Working Memory: Short-term, high-accessibility storage for active processing
  - Episodic Memory: Storage of experiences and contextual information
  - Semantic Memory: Long-term storage of facts, concepts, and knowledge

- **Health Dynamics**:
  - Energy management and resource allocation
  - Attention and focus mechanisms
  - Cognitive load monitoring and adaptation

- **Biological Inspiration**:
  - Neural pathway simulation
  - Neurotransmitter-inspired state management
  - Circadian rhythm effects on performance

- **LLM Integration**:
  - Seamless integration with popular LLM frameworks
  - Prompt engineering and context management
  - Response optimization based on cognitive state

## Architecture

The NCA system is structured around modular components that work together to create a cohesive cognitive framework:

```
neuroca/
├── api/                  # API layer and endpoints
├── cli/                  # Command-line interface tools
├── config/               # Configuration files and settings
├── core/                 # Core domain logic and models
├── db/                   # Database migrations and schemas
├── docs/                 # Documentation
├── infrastructure/       # Infrastructure as code
├── integration/          # LLM integration components
├── memory/               # Memory tier implementations
├── monitoring/           # Monitoring and observability
├── scripts/              # Utility scripts
├── tests/                # Test suite
├── tools/                # Development and operational tools
```

## Installation

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized deployment)
- Access to LLM API credentials (if using external models)

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/justinlietz93/Neuro-Cognitive-Architecture.git
cd Neuro-Cognitive-Architecture

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Using Pip

```bash
# Clone the repository
git clone https://github.com/justinlietz93/Neuro-Cognitive-Architecture.git
cd Neuro-Cognitive-Architecture

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Using Docker

```bash
# Clone the repository
git clone https://github.com/justinlietz93/Neuro-Cognitive-Architecture.git
cd Neuro-Cognitive-Architecture

# Build and run with Docker Compose
docker-compose up -d
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your specific configuration:
   - LLM API credentials
   - Database connection details
   - Memory system parameters
   - Health dynamics settings

3. Additional configuration options are available in the `config/` directory.

## Usage

### API

Start the API server:

```bash
make run-api
# or
python -m neuroca.api.server
```

The API will be available at `http://localhost:8000` by default.

### CLI

The NCA system provides a command-line interface for direct interaction:

```bash
# Get help
neuroca --help

# Initialize a new cognitive session
neuroca session init

# Process input through the cognitive architecture
neuroca process "Your input text here"

# View memory contents
neuroca memory list --type=working
```

### Python Library

```python
from neuroca import NeuroCognitiveArchitecture

# Initialize the architecture
nca = NeuroCognitiveArchitecture()

# Configure memory parameters
nca.configure(
    working_memory_capacity=7,
    episodic_decay_rate=0.05,
    semantic_consolidation_threshold=0.8
)

# Process input through the cognitive architecture
response = nca.process("What is the relationship between quantum physics and consciousness?")

# Access memory components
working_memory = nca.memory.working.get_contents()
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
make test
# or
pytest

# Run specific test modules
pytest tests/memory/
```

### Code Quality

```bash
# Run linting
make lint
# or
flake8 neuroca tests

# Run type checking
make typecheck
# or
mypy neuroca
```

## Documentation

Comprehensive documentation is available in the `docs/` directory and can be built using Sphinx:

```bash
cd docs
make html
```

The built documentation will be available at `docs/_build/html/index.html`.

## Contributing

We welcome contributions to the NeuroCognitive Architecture project! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- **Phase 1**: Core memory system implementation
- **Phase 2**: Health dynamics integration
- **Phase 3**: Advanced biological components
- **Phase 4**: LLM integration optimization
- **Phase 5**: Performance tuning and scaling

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Cognitive science research that inspired this architecture
- The open-source AI community
- Contributors and early adopters

## Author

- **Justin Lietz** - *Initial work & Lead Developer*

## Contact

For questions, feedback, or collaboration opportunities, please open an issue on this repository or contact Justin Lietz.

---

**Note**: NeuroCognitive Architecture is a research project and is continuously evolving. Features and interfaces may change as the project develops.
