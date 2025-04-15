# Neuroca Integrations

This directory handles the integration of the NeuroCognitive Architecture with external systems, primarily Large Language Models (LLMs) and potentially other AI services or data sources.

## Structure

- **LLM Clients/Adapters**: Contains code for interacting with specific LLM APIs (e.g., OpenAI, Anthropic, local models). This might involve wrappers or adapters to provide a consistent interface for sending prompts and receiving responses.
- **Prompt Engineering**: Modules related to constructing effective prompts that incorporate context retrieved from the NCA memory system.
- **Context Management**: Logic for selecting, formatting, and injecting relevant memories or cognitive state information into LLM prompts.
- **Framework Adapters**: Specific code to integrate NCA smoothly with frameworks like LangChain, LlamaIndex, etc. This might involve implementing custom Memory classes or other components compatible with those frameworks.

## Usage

The core processing services use components from this directory to:
- Send requests to LLMs, augmented with context from NCA's memory.
- Parse LLM responses.
- Potentially update NCA's memory based on the interaction.
- Leverage specific features of integrated frameworks (e.g., using NCA memory within a LangChain agent).

## Maintenance

- Update LLM client code when external APIs change.
- Refine prompt engineering techniques based on performance and desired behavior.
- Keep framework adapters synchronized with updates in external libraries like LangChain.
- Add new adapters or clients as support for more LLMs or frameworks is introduced.
