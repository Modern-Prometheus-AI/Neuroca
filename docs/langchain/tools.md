# Tools Integration Documentation

This document provides detailed information about the LangChain tools integration with the NeuroCognitive Architecture (NCA).

## Overview

The tools integration module (`tools.py`) implements LangChain tools that allow LLMs to interact with NCA's memory, health monitoring, and cognitive processes.

## Available Tools

1. **`MemoryStorageTool`:** Store information in NCA's memory system.
2. **`MemoryRetrievalTool`:** Retrieve information from NCA's memory.
3. **`HealthMonitorTool`:** Interact with NCA's health monitoring system.
4. **`CognitiveProcessTool`:** Trigger NCA's cognitive processes.

## Usage

```python
from neuroca.integration.langchain.tools import get_all_tools

# Get all available NCA tools
tools = get_all_tools()

# Use in a LangChain agent
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
```

## Detailed Implementation

For implementation details, refer to the source code in `tools.py`.
