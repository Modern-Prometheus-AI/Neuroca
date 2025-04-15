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

## Integrating the Memory System

The `ConversationalAgent` class in `test_memory_with_llm.py` provides a template for integrating the Neuroca memory system into your own Python applications. Here are the key steps:

1.  **Import necessary components**:
    ```python
    import asyncio
    from neuroca.memory.manager.core import MemoryManager
    from neuroca.memory.backends import BackendType
    # Import other necessary models like MemoryItem, MemorySearchOptions if needed
    ```

2.  **Initialize the MemoryManager**:
    Create an instance of `MemoryManager`, providing configuration for memory tiers and specifying the storage backends.
    ```python
    # Example configuration (adjust as needed)
    memory_config = {
        "stm": {"default_ttl": 3600},
        "mtm": {"max_capacity": 1000},
        "ltm": {"maintenance_interval": 86400}
    }

    # Choose backend types (e.g., MEMORY, SQLITE)
    mtm_backend = BackendType.MEMORY
    ltm_backend = BackendType.MEMORY
    vector_backend = BackendType.MEMORY # Or another vector-supported backend

    memory_manager = MemoryManager(
        config=memory_config,
        mtm_storage_type=mtm_backend,
        ltm_storage_type=ltm_backend,
        vector_storage_type=vector_backend
    )

    # Initialize asynchronously
    await memory_manager.initialize()
    ```

3.  **Add Memories**:
    Use `add_memory` to store information. Provide content, summary, importance, tags, metadata, and the initial tier.
    ```python
    memory_id = await memory_manager.add_memory(
        content="User mentioned their favorite color is blue.",
        summary="User favorite color",
        importance=0.8,
        tags=["user_preference", "color"],
        metadata={"source": "conversation", "timestamp": time.time()},
        initial_tier="stm"
    )
    ```

4.  **Search Memories**:
    Use `search_memories` to retrieve relevant information based on a query.
    ```python
    search_results_obj = await memory_manager.search_memories(
        query="What is the user's favorite color?",
        limit=5,
        min_relevance=0.5
    )

    if search_results_obj.results:
        for result in search_results_obj.results:
            print(f"Found memory: {result.memory.get_text()} (Relevance: {result.relevance:.2f})")
    ```

5.  **Shutdown Gracefully**:
    Ensure the memory manager is shut down properly when your application exits.
    ```python
    await memory_manager.shutdown()
    ```

By following these steps, you can incorporate the Neuroca memory system's capabilities into various applications, such as chatbots, agents, or data processing pipelines. Remember to handle the asynchronous nature of the memory operations using `async` and `await`.
