# NeuroCognitive Architecture (NCA) - Architecture Decisions

## Package Structure

### Src-Layout Pattern

We've implemented the recommended src-layout pattern for Python packages, which provides several important benefits:

1. **Clean Separation**: 
   - Source code is isolated in the `src/neuroca` directory
   - Tests reside outside the package in a dedicated `tests` directory
   - Configuration files remain at the project root
   
2. **Import Clarity**: 
   - Eliminates confusion between local imports and installed package imports
   - Forces explicit imports that work correctly in all contexts
   - Prevents common pitfalls with relative imports
   
3. **Test Reliability**: 
   - Tests run against the installed package rather than source files
   - Ensures tests reflect real-world usage patterns
   - Eliminates hidden dependencies or path manipulation hacks
   
4. **Deployment Consistency**: 
   - Package behaves the same in development and production
   - Built package includes only necessary files
   - Clear boundary between package code and project tooling

The implementation follows Python packaging best practices, with this structure:

```
project_root/
├── src/
│   └── neuroca/            # Main package
│       ├── __init__.py     # Package initialization
│       ├── core/           # Core components
│       │   ├── __init__.py
│       │   ├── health/     # Health monitoring system
│       │   └── memory/     # Memory systems
│       ├── api/            # API endpoints and schemas
│       ├── cli/            # Command-line interface
│       ├── db/             # Database connections and models
│       └── ...             # Other modules
├── tests/                  # Test directory (outside package)
├── pyproject.toml          # Project configuration
└── ...                     # Other project files
```

This aligns with the recommendations from:
- pytest documentation on good practices
- Python Packaging Authority (PyPA)
- Ionel Cristian Mărieș' blog posts on Python packaging

### Namespace Structure

Our package namespace follows a hierarchical structure:

1. **Core Cognitive Components**:
   - `neuroca.core.memory`: Memory systems implementations
   - `neuroca.core.health`: Health monitoring and regulation
   - `neuroca.core.cognition`: Higher-level cognitive processes

2. **Infrastructure Components**:
   - `neuroca.api`: API endpoints and schemas
   - `neuroca.cli`: Command-line interfaces
   - `neuroca.db`: Database connections and models
   - `neuroca.monitoring`: Logging, metrics, and tracing

3. **Integration Components**:
   - `neuroca.integration`: External system integrations
   - `neuroca.utils`: Shared utilities
   - `neuroca.models`: Data models and schemas

## Design Patterns

### Interface-Based Design

To break circular dependencies and enable more modular development, we've implemented an interface-based design approach:

1. **Abstract Base Classes**: 
   - Define contracts through abstract methods and properties
   - Establish clear boundaries between components
   - Provide type safety through explicit interfaces
   
2. **Dependency Inversion**: 
   - Components depend on abstractions rather than concrete implementations
   - High-level modules are decoupled from low-level modules
   - Makes the system more testable and maintainable

Key interfaces in the memory system:

```python
class MemoryChunk(Generic[T], ABC):
    """Represents a single unit of memory content with activation level."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Get the unique identifier for this memory chunk."""
        pass
    
    @property
    @abstractmethod
    def content(self) -> T:
        """Get the content of this memory chunk."""
        pass
        
    # Additional properties and methods...
    
class MemorySystem(ABC):
    """Abstract base class for all memory systems."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this memory system."""
        pass
    
    @abstractmethod
    def store(self, content: Any, **metadata) -> str:
        """Store content in this memory system."""
        pass
        
    # Additional methods...
```

### Factory Pattern

We've implemented the Factory pattern for memory systems to:

1. **Decouple Creation from Use**: 
   - Clients use a simple factory function to create memory systems
   - Creation logic is centralized in one location
   - Implementation details are hidden from clients
   
2. **Enable Runtime Registration**: 
   - Memory system implementations register themselves with the factory
   - New systems can be added without modifying factory code
   - Simplifies dependency management

Implementation:

```python
# Registry of available memory systems
_memory_system_registry: Dict[str, Type[MemorySystem]] = {}

def register_memory_system(name: str, cls: Type[MemorySystem]) -> None:
    """Register a memory system implementation."""
    _memory_system_registry[name] = cls

def create_memory_system(memory_type: str, **config) -> MemorySystem:
    """Create a memory system of the specified type."""
    # Normalize name and create instance
    memory_type = memory_type.lower()
    memory_type = _memory_type_aliases.get(memory_type, memory_type)
    
    if memory_type not in _memory_system_registry:
        raise ValueError(f"Unknown memory system type: {memory_type}")
    
    return _memory_system_registry[memory_type](**config)
```

### Biological Fidelity Patterns

Our architecture incorporates patterns inspired by biological cognition:

1. **Tiered Memory System**: 
   - Working Memory: Limited capacity (7±2 chunks), high activation
   - Episodic Memory: Experiences with temporal and emotional context
   - Semantic Memory: Abstract knowledge in a graph structure
   
2. **Decay Mechanisms**: 
   - Time-based decay for working memory
   - Interference-based forgetting
   - Emotional salience affecting retention
   
3. **Health Dynamics**: 
   - Resource monitoring (energy, attention)
   - Homeostatic regulation
   - Adaptive responses based on system state

## Technology Stack Decisions

### Core Framework

We've chosen FastAPI for our API implementation because:

1. **Performance**: 
   - Async capability matches our concurrent processing needs
   - Minimal overhead compared to alternatives
   
2. **Type Safety**: 
   - Pydantic integration for runtime type validation
   - Automatic schema generation for API documentation
   
3. **Developer Experience**: 
   - Intuitive API for defining endpoints
   - Excellent documentation and community support

### Dependency Management

We've chosen Poetry for dependency management because:

1. **Reproducibility**: 
   - Exact dependency locking via poetry.lock
   - Consistent environment across development and deployment
   
2. **Modern Workflow**: 
   - Combined dependency and package management
   - Virtual environment handling built-in
   
3. **Publishing Support**: 
   - Simple publication to PyPI
   - Metadata management in a single location (pyproject.toml)

### Storage Strategy

Our storage architecture employs multiple specialized systems:

1. **Working Memory**: 
   - In-memory with Redis for distributed scenarios
   - Optimized for fast access and real-time operations
   
2. **Episodic Memory**: 
   - PostgreSQL with vector extension for similarity search
   - JSONB for flexible schema evolution
   
3. **Semantic Memory**: 
   - Neo4j graph database for relationship traversal
   - Property graph model for typed relationships

## Implementation Approach

### Test-Driven Development

We follow a strict TDD approach for all core components:

1. **Test First**: 
   - Write tests based on interface specifications
   - Define biological constraints in test assertions
   - Implement only what's needed to make tests pass
   
2. **Test Coverage**: 
   - Target >95% coverage for core cognitive components
   - Include boundary conditions and error cases
   - Test biologically-inspired behaviors explicitly

### Continuous Validation

Our development process includes continuous checks for:

1. **Biological Plausibility**: 
   - Verify capacity constraints
   - Test emotional effects on memory
   - Validate decay curves against cognitive models
   
2. **Performance Metrics**: 
   - Memory retrieval latency
   - Scaling under increasing cognitive load
   - Resource consumption during operation

### Incremental Implementation

We're following a phase-based implementation approach:

1. **Phase 1**: Package restructuring and interface definitions
2. **Phase 2**: Core memory system implementations
3. **Phase 3**: Health dynamics and cognitive processes
4. **Phase 4**: LLM integration and optimization
5. **Phase 5**: Production deployment and monitoring 