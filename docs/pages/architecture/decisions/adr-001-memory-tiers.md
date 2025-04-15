# ADR-001: Three-Tiered Memory System Architecture

## Status

Accepted

## Date

2023-11-15

## Context

The NeuroCognitive Architecture (NCA) requires a memory system that mimics human cognitive processes while providing practical functionality for Large Language Models (LLMs). Current LLM architectures lack sophisticated memory management that can differentiate between immediate context, working knowledge, and long-term storage. This limitation restricts their ability to maintain contextual awareness across interactions, learn from experiences, and develop a persistent knowledge base.

We need to design a memory architecture that:

1. Supports different types of information retention based on importance and recency
2. Enables efficient retrieval of relevant information during interactions
3. Allows for dynamic learning and knowledge consolidation
4. Scales effectively with increasing amounts of data
5. Maintains performance under high load conditions
6. Integrates seamlessly with existing LLM capabilities

## Decision

We will implement a three-tiered memory system inspired by human cognitive architecture:

### 1. Short-Term Memory (STM)

**Purpose**: Maintain immediate context and recent interactions.

**Characteristics**:
- High-speed access with limited capacity
- Volatile storage with automatic decay
- Recency-biased retention
- Direct integration with LLM context window

**Implementation Details**:
- In-memory data structures (priority queues, circular buffers)
- Time-based expiration policies
- Importance scoring for retention decisions
- Context window management algorithms

**Capacity**: Configurable, defaulting to approximately 10-15 conversation turns or equivalent information units

**Decay Rate**: Exponential decay with half-life of 5-10 interaction cycles

### 2. Working Memory (WM)

**Purpose**: Store actively used information and facilitate reasoning processes.

**Characteristics**:
- Medium-term persistence
- Structured organization by topic/domain
- Bidirectional flow with STM and LTM
- Support for active manipulation and reasoning

**Implementation Details**:
- Distributed cache system (Redis, Memcached)
- Graph-based knowledge representation
- Attention mechanisms for focus management
- Chunking algorithms for information organization

**Capacity**: Larger than STM but still constrained (configurable based on deployment resources)

**Persistence**: Hours to days, with activity-based reinforcement

**Retrieval Mechanism**: Associative retrieval with relevance scoring

### 3. Long-Term Memory (LTM)

**Purpose**: Persistent knowledge storage and retrieval.

**Characteristics**:
- Durable, high-capacity storage
- Semantic organization and indexing
- Consolidation processes from working memory
- Multiple retrieval pathways

**Implementation Details**:
- Vector database (Pinecone, Weaviate, or Milvus)
- Document database for unstructured content (MongoDB)
- Embedding models for semantic representation
- Hierarchical categorization system
- Periodic consolidation processes

**Capacity**: Effectively unlimited, constrained only by infrastructure resources

**Persistence**: Permanent until explicitly removed or deprecated

**Retrieval Efficiency**: Optimized for semantic similarity and relevance

## Memory Transfer Mechanisms

### STM → WM Transfer
- Importance-based promotion
- Repetition reinforcement
- Explicit marking by system or user
- Contextual relevance threshold crossing

### WM → LTM Consolidation
- Scheduled consolidation processes
- Usage frequency analysis
- Knowledge graph integration
- Semantic clustering and abstraction

### LTM → WM Activation
- Query-based retrieval during interactions
- Associative activation based on current context
- Explicit recall requests
- Predictive pre-loading for anticipated topics

## Technical Implementation Considerations

### Data Structures
- STM: Priority queues, circular buffers with time-based expiration
- WM: Graph databases, distributed caches with TTL
- LTM: Vector stores, document databases with semantic indexing

### Scaling Strategy
- Horizontal scaling for LTM components
- Vertical scaling for WM performance
- Sharding strategies based on knowledge domains
- Read replicas for high-demand knowledge areas

### Persistence Layers
- STM: In-memory with optional persistence for recovery
- WM: Cache with background persistence
- LTM: Durable storage with backup and replication

### Query Optimization
- Embedding-based similarity search
- Hierarchical filtering
- Parallel query execution across memory tiers
- Caching frequently accessed patterns

## Consequences

### Positive

1. Enhanced contextual awareness across interactions
2. Improved information retention and recall capabilities
3. More natural conversation flow with appropriate memory references
4. Ability to learn and adapt from past interactions
5. Reduced redundancy in information processing
6. Better handling of complex, multi-session tasks

### Negative

1. Increased system complexity
2. Higher resource requirements for memory management
3. Potential privacy concerns with persistent memory
4. Need for sophisticated memory management policies
5. Challenges in determining optimal memory transfer thresholds

### Neutral

1. Requires ongoing tuning of memory parameters
2. Necessitates clear policies for memory retention and deletion
3. May require user controls for memory management

## Compliance and Privacy Considerations

- All memory tiers must implement configurable retention policies
- Personal or sensitive information must be clearly marked and handled according to privacy requirements
- Users must have the ability to request memory deletion across all tiers
- Audit trails for memory access and modification must be maintained
- Memory contents must be encrypted at rest and in transit

## Performance Metrics

We will measure the effectiveness of this memory architecture using:

1. Retrieval latency across tiers
2. Contextual relevance of retrieved information
3. Memory utilization efficiency
4. Consolidation processing overhead
5. User-perceived continuity in multi-session interactions
6. Knowledge retention accuracy over time

## Implementation Phases

1. **Phase 1**: Core STM implementation with basic decay mechanisms
2. **Phase 2**: WM implementation with STM integration
3. **Phase 3**: LTM storage and basic retrieval
4. **Phase 4**: Advanced memory transfer mechanisms
5. **Phase 5**: Optimization and scaling improvements

## Alternatives Considered

1. **Single unified memory store**: Rejected due to inefficiency in handling different memory requirements
2. **Two-tier system (short/long only)**: Rejected due to lack of intermediate processing capabilities
3. **External knowledge base only**: Rejected due to inability to maintain conversation context
4. **Pure neural storage approach**: Rejected due to current limitations in retrieval precision

## References

1. Baddeley, A. D., & Hitch, G. (1974). Working memory. Psychology of Learning and Motivation, 8, 47-89.
2. Atkinson, R. C., & Shiffrin, R. M. (1968). Human memory: A proposed system and its control processes. Psychology of Learning and Motivation, 2, 89-195.
3. Tulving, E. (1985). How many memory systems are there? American Psychologist, 40(4), 385-398.
4. Miller, G. A. (1956). The magical number seven, plus or minus two: Some limits on our capacity for processing information. Psychological Review, 63(2), 81-97.
5. Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental storage capacity. Behavioral and Brain Sciences, 24(1), 87-114.

## Related Decisions

- ADR-002: Health Dynamics System (Pending)
- ADR-003: LLM Integration Architecture (Pending)
- ADR-004: Knowledge Representation Format (Pending)
- ADR-005: Privacy and Data Retention Policies (Pending)

## Notes

This ADR establishes the foundational memory architecture for the NCA system. Implementation details will be refined in subsequent technical specifications and component designs. Regular review of memory performance metrics will inform ongoing optimization efforts.