# LangChain Integration Documentation

This directory contains documentation for the LangChain integration with the NeuroCognitive Architecture (NCA).

## Overview

The LangChain integration allows seamless interaction between NCA's cognitive architecture and LangChain's framework for building LLM applications. This integration enables the use of NCA's advanced memory systems, health dynamics, and cognitive processes within LangChain workflows.

## Key Components

1. **Chains Integration (`chains.py`):** Provides custom chain implementations that integrate NCA's memory and health monitoring with LangChain's chain functionality.
2. **Memory Integration (`memory.py`):** Contains adapters that connect NCA's three-tiered memory system (working, episodic, semantic) with LangChain's memory interface.
3. **Tools Integration (`tools.py`):** Implements LangChain tools that allow LLMs to interact with NCA's memory, health monitoring, and cognitive processes.

## Usage Examples

### Using NCA Memory with LangChain

```python
from neuroca.integration.langchain.memory import MemoryFactory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Create an NCA memory instance
memory = MemoryFactory.create_memory(memory_type="working")

# Use in a LangChain chain
prompt = PromptTemplate(input_variables=["input"], template="Respond to: {input}")
chain = LLMChain(llm=your_llm, prompt=prompt, memory=memory)
```

### Using NCA Cognitive Chains

```python
from neuroca.integration.langchain.chains import create_cognitive_chain

# Create a cognitive chain with NCA integration
chain = create_cognitive_chain(
    llm=your_llm,
    memory_manager=your_memory_manager,
    health_monitor=your_health_monitor
)

# Run the chain
result = chain.run("Process this information")
```

## Available Tools

The integration provides the following LangChain tools:
- `MemoryStorageTool`: Store information in NCA's memory system
- `MemoryRetrievalTool`: Retrieve information from NCA's memory
- `HealthMonitorTool`: Interact with NCA's health monitoring system
- `CognitiveProcessTool`: Trigger NCA's cognitive processes

## Detailed Documentation

For more detailed information, see the source code documentation in:
- [chains.py](../../src/neuroca/integration/langchain/chains.py)
- [memory.py](../../src/neuroca/integration/langchain/memory.py)
- [tools.py](../../src/neuroca/integration/langchain/tools.py)
