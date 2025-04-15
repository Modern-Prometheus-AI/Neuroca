# Chains Integration Documentation

This document provides detailed information about the LangChain chains integration with the NeuroCognitive Architecture (NCA).

## Overview

The chains integration module (`chains.py`) provides custom chain implementations that leverage NCA's memory systems, health dynamics, and cognitive processes within LangChain workflows.

## Key Classes

1. **`NCACallbackHandler`:** A callback handler that monitors and logs chain execution, updating NCA's health metrics.
2. **`NCAMemoryAdapter`:** An adapter connecting LangChain's memory interface with NCA's multi-tiered memory system.
3. **`NCACognitiveChain`:** A chain that incorporates NCA's cognitive architecture components, including memory and health monitoring.
4. **`NCAReflectiveChain`:** Extends `NCACognitiveChain` with reflective capabilities, allowing metacognition during chain execution.
5. **`NCASequentialChain`:** Extends LangChain's `SequentialChain` with NCA-specific features like health monitoring and memory integration.

## Usage

```python
from neuroca.integration.langchain.chains import create_cognitive_chain

# Create a cognitive chain
chain = create_cognitive_chain(
    llm=your_llm,
    memory_manager=your_memory_manager,
    health_monitor=your_health_monitor
)

# Run the chain
result = chain.run("Process this information")
```

## Detailed Implementation

For implementation details, refer to the source code in `chains.py`.
