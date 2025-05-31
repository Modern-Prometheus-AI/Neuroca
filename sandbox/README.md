# Neuroca Sandbox - Advanced LLM Client

This sandbox contains an advanced LLM client that demonstrates the full power of Neuroca's cognitive architecture.

## Features Demonstrated

### 🧠 Core Cognitive Architecture
- **3-Tier Memory System**: STM → MTM → LTM with automatic consolidation
- **Cognitive Control**: Attention management, goal setting, planning, decision making
- **Metacognitive Monitoring**: Self-reflection and performance tracking
- **Context-Aware Processing**: Rich context building from memory and state
- **Health Monitoring**: System health tracking and optimization

### 🎯 Advanced Capabilities
- **10-Phase Cognitive Pipeline**: Complete processing workflow for each user input
- **Memory Consolidation**: Automatic movement of memories between tiers
- **Relationship Management**: Semantic connections between memories
- **Response Inhibition**: Safety checks before generating responses
- **Session Persistence**: Saves cognitive state and conversation history

## Files

- `advanced_nca_llm_client.py` - Main advanced client demonstrating all NCA features
- `README.md` - This documentation
- `session_*.json` - Session summaries (generated during runtime)

## Usage

### Basic Usage
```bash
cd sandbox
python advanced_nca_llm_client.py
```

### Interactive Commands
- Type any message to process through the full cognitive pipeline
- `demo` - Run comprehensive cognitive features demonstration
- `status` - Show current cognitive state and performance metrics
- `quit` - Exit gracefully with session summary

### Example Session
```
🎮 Starting Interactive NCA Session
Type 'quit' to exit, 'demo' for feature demo, 'status' for cognitive state
------------------------------------------------------------

👤 You: Hello, what can you do?

🎤 Processing User Input: 'Hello, what can you do?...'
  🎯 Phase 1: Attention Management
    → Focus: {'focus': 'demo'}
  💭 Phase 2: Memory and Context Retrieval
    → Retrieved 0 relevant memories
  🎪 Phase 3: Goal Management
    → Active goals: 0
  📋 Phase 4: Cognitive Planning
    → Plan created: demo_plan
  🤔 Phase 5: Decision Making
    → Decision: proceed (confidence: 0.80)
  🛡️ Phase 6: Response Inhibition
    → Inhibition check: ALLOWED
  💬 Phase 7: Response Generation
  💾 Phase 8: Memory Storage
    → Stored interaction in STM: abc123...
  🔍 Phase 9: Metacognitive Reflection
    → Reflection: good
  ❤️ Phase 10: Health Monitoring
✅ Processing Complete! (0.45s)

🧠 NCA: I'm confident I can help with that. Based on my cognitive processing, here's my response to your input: 'Hello, what can you do?'
   💭 Processed in 0.45s using 0 memories
```

## Architecture Overview

The client implements a complete cognitive architecture with:

```
┌─────────────────────────────────────┐
│          User Input                 │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│     10-Phase Cognitive Pipeline     │
│                                     │
│ 1. Attention Management             │
│ 2. Memory & Context Retrieval       │
│ 3. Goal Management                  │
│ 4. Cognitive Planning               │
│ 5. Decision Making                  │
│ 6. Response Inhibition              │
│ 7. Response Generation              │
│ 8. Memory Storage                   │
│ 9. Metacognitive Reflection         │
│ 10. Health Monitoring               │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      Enriched Response              │
│   + Cognitive State                 │
│   + Performance Metrics             │
│   + Session Data                    │
└─────────────────────────────────────┘
```

## Memory System

### Three-Tier Architecture
- **STM (Short-Term Memory)**: Working memory for immediate context
- **MTM (Medium-Term Memory)**: Intermediate consolidation layer
- **LTM (Long-Term Memory)**: Permanent semantic storage with relationships

### Memory Operations
- **Store**: Add new memories with rich metadata
- **Retrieve**: Get specific memories by ID
- **Search**: Find relevant memories across all tiers
- **Consolidate**: Move memories between tiers based on importance

## Cognitive Control Components

### Attention Manager
- Focus management for incoming stimuli
- Context-aware attention allocation
- Attention state tracking

### Goal Manager
- Dynamic goal setting and tracking
- Priority-based goal management
- Goal-driven behavior

### Decision Maker
- Multi-option decision making
- Confidence scoring
- Context-informed decisions

### Cognitive Planner
- Task planning and decomposition
- Goal-oriented plan generation
- Adaptive planning strategies

### Response Inhibitor
- Safety checks for generated responses
- Content filtering and appropriateness
- Risk assessment

### Metacognitive Monitor
- Performance reflection and analysis
- Error logging and pattern recognition
- Self-optimization recommendations

## Health Monitoring

- System performance tracking
- Operation timing and success rates
- Health score calculation
- Resource utilization monitoring

## Error Handling

The client includes robust error handling with:
- Graceful degradation for missing components
- Stub implementations for unavailable features
- Comprehensive logging
- Metacognitive error reflection

## Session Management

- Unique session IDs
- Conversation history tracking
- Cognitive state persistence
- Session summary generation

## Requirements

- Python 3.9+
- Neuroca package installed
- Poetry environment (recommended)

## Running the Demo

To see all cognitive features in action:

```bash
python advanced_nca_llm_client.py
# Then type: demo
```

This will run through demonstrations of:
1. Multi-tier memory system
2. Cognitive control components
3. Metacognitive monitoring
4. Context-aware processing
5. Health monitoring

## Extending the Client

The client is designed to be extensible. You can:

- Add new cognitive components
- Implement custom memory backends
- Extend the response generation logic
- Add new metacognitive capabilities
- Integrate with external LLM APIs

## Performance

The client tracks comprehensive performance metrics:
- Processing time per cognitive phase
- Memory retrieval efficiency
- Decision confidence scores
- Health monitoring scores
- Session statistics

All metrics are available via the `status` command during interactive sessions.
