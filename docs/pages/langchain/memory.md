# Memory Integration Documentation

This document provides detailed information about the LangChain memory integration with the NeuroCognitive Architecture (NCA).

## Overview

The memory integration module (`memory.py`) contains adapters that connect NCA's three-tiered memory system (working, episodic, semantic) with LangChain's memory interface.

## Key Classes

1. **`NCAMemory`:** Base memory class implementing LangChain's `BaseMemory` interface.
2. **`WorkingMemoryAdapter`:** Adapter for NCA's working memory.
3. **`EpisodicMemoryAdapter`:** Adapter for NCA's episodic memory.
4. **`SemanticMemoryAdapter`:** Adapter for NCA's semantic memory.
5. **`MemoryFactory`:** Factory for creating appropriate memory instances.

## Usage

```python
from neuroca.integration.langchain.memory import MemoryFactory

# Create a working memory instance
memory = MemoryFactory.create_memory(memory_type="working")

# Use in a LangChain chain
chain = LLMChain(llm=your_llm, prompt=prompt, memory=memory)
```

## Detailed Implementation

For implementation details, refer to the source code in `memory.py`.
