# NeuroCognitive Architecture (NCA)

Welcome to the official documentation for the NeuroCognitive Architecture (NCA) - a biologically-inspired cognitive framework designed to give Large Language Models (LLMs) **persistent, dynamic, and human-like memory**.

## Beyond Retrieval - Enabling Automatic Memory

NeuroCognitive Architecture (NCA) represents a fundamental shift away from common techniques like Retrieval-Augmented Generation (RAG), GraphRAG, PathRAG, and similar approaches. While those methods enhance LLMs by using external tools to **retrieve** information from vector databases or knowledge graphs at query time to augment a limited context window, **NCA enables the LLM itself to genuinely remember...** and not just remember, but remember persistently.

Instead of relying on external lookups, NCA integrates a **dynamic, multi-tiered internal memory system** (Working, Episodic, Semantic) inspired by human cognition. Information isn't just fetched; it's processed, consolidated, prioritized, and even decays naturally over time based on relevance and interaction frequency, all managed by automatic background cognitive processes.

This allows an LLM equipped with NCA to:

* **Organically Recall Context:** Access relevant past interactions, learned facts, user preferences, and evolving goals without explicit retrieval calls.
* **Learn and Adapt:** Truly evolve its understanding over time based on its "experiences" stored within its memory system.
* **Maintain Coherence:** Overcome the limitations of fixed context windows, enabling stable, long-term conversational understanding and task execution.

In essence, NCA focuses on building **intrinsic memory capabilities**, allowing the model to simply *remember*, rather than augmenting it with external data retrieval tools. This core memory function is supported by integrated cognitive control mechanisms and health dynamics, creating a more adaptive and contextually aware AI system.

## Key Features

- **Three-Tiered Memory System**
  - Working Memory with capacity constraints and activation decay
  - Episodic Memory with temporal context and emotional salience
  - Semantic Memory as a knowledge graph with concept relationships

- **Cognitive Control Mechanisms**
  - Executive functions for goal-directed behavior
  - Metacognition for self-monitoring and optimization
  - Attention management with focus and distraction handling

- **Health Dynamics**
  - Energy management and resource allocation
  - Simulated fatigue and recovery processes
  - Homeostatic regulation with adaptive responses

- **LLM Integration**
  - Provider-agnostic interfaces (OpenAI, Anthropic, Ollama)
  - Memory-enhanced prompting and context management
  - Health-aware response processing

- **Production-Ready Infrastructure**
  - Kubernetes deployment with auto-scaling
  - Comprehensive monitoring and alerting
  - Backup and restore procedures
  - Incident response runbooks

## Quick Navigation

### User Documentation

- [Getting Started](user/getting-started.md) - Setup and first steps
- [Configuration](user/configuration.md) - Configuration options
- [Examples](user/examples.md) - Example use cases
- [Integration](user/integration.md) - Integrating with existing systems

### Technical Documentation

- [Architecture Overview](architecture/components.md) - System components and interactions
- [API Reference](api/endpoints.md) - API endpoints and schemas
- [Memory Systems](architecture/decisions/adr-001-memory-tiers.md) - Memory implementation details
- [Health System](architecture/decisions/adr-002-health-system.md) - Health dynamics implementation

### Developer Documentation

- [Development Environment](development/environment.md) - Setting up the development environment
- [Contributing Guidelines](development/contributing.md) - How to contribute
- [Coding Standards](development/standards.md) - Code style and practices
- [Workflow](development/workflow.md) - Development workflow

### Operations Documentation

- [Deployment](operations/deployment.md) - Deployment procedures
- [Monitoring](operations/monitoring.md) - Monitoring and observability
- [Incident Response](operations/runbooks/incident-response.md) - Handling incidents
- [Backup and Restore](operations/runbooks/backup-restore.md) - Data protection procedures

## Project Status

The NeuroCognitive Architecture has completed its implementation roadmap and is now considered production-ready. All major components have been implemented, tested, and optimized for performance:

- ✅ Package structure and dependency resolution
- ✅ Three-tiered memory system (Working, Episodic, Semantic)
- ✅ Health dynamics system with homeostatic mechanisms
- ✅ Cognitive control components for executive functions
- ✅ LLM integration layer with provider adapters
- ✅ Performance optimization with profiling and caching
- ✅ Production deployment with Kubernetes

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Acknowledgments

The NeuroCognitive Architecture draws inspiration from neuroscience research on human cognition and memory systems. We acknowledge the contributions of researchers in cognitive science, neuroscience, and artificial intelligence that have made this work possible.
