# Neuroca Test Scripts

This directory contains test scripts to demonstrate the functionality of the Neuroca system.

## Memory System with LLM Integration

The `test_memory_with_llm.py` script demonstrates how to use the Neuroca memory system with an LLM to create a conversational agent that can remember previous interactions.

### Setup

1. **Install dependencies**:
   ```bash
   pip install openai python-dotenv
   ```

2. **Set up the environment**:
   
   Copy the `.env.example` file to `.env` in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

### Usage

Run the script from the project root directory:

```bash
python scripts/test_memory_with_llm.py
```

The script will:
1. Initialize the memory system with the specified backend (SQLite by default)
2. Start an interactive conversation loop
3. Store user inputs and agent responses in the memory system
4. Use the memory system to retrieve relevant context for each interaction
5. Generate responses using the OpenAI API (if available) or a fallback response
6. Periodically run memory maintenance to consolidate short-term memories

### Testing Different Backends

The script supports two memory backends:

1. **SQLite** (default): More persistent storage, slower but data persists between runs
2. **In-Memory**: Faster but data is lost when the script ends

To switch between backends, edit the `use_sqlite` variable in the `main()` function:

```python
# To use SQLite (persistent)
use_sqlite = True

# To use In-Memory (faster, non-persistent)
use_sqlite = False
```

### Expected Behavior

1. The script will start a conversational interface
2. You can type messages and the agent will respond
3. The agent will remember previous exchanges and use them in context for future responses
4. Over time, as you add more information, the agent should be able to refer back to it
5. Type 'exit', 'quit', or 'bye' to end the conversation

### Thread Safety

This script demonstrates the thread-safe nature of our recently updated memory system. The SQLite backend now uses thread-local storage for connections, ensuring that each thread gets its own database connection. This makes it safe to use in asynchronous contexts.

### Testing Tips

1. **Test Memory Recall**: Try mentioning information from earlier in the conversation and see if the agent can recall it.
2. **Test Context Maintenance**: Conduct a complex conversation and see if the agent maintains a coherent understanding.
3. **Test Memory Consolidation**: Have a long conversation (10+ exchanges) to trigger memory maintenance and see if memories are properly consolidated.
4. **Test Persistence**: If using the SQLite backend, exit and restart the script to verify that memories persist between sessions.
