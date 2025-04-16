# Integration System Overview

This diagram provides a comprehensive overview of the NeuroCognitive Architecture (NCA) integration system.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#242424', 'primaryTextColor': '#fff', 'primaryBorderColor': '#555', 'lineColor': '#f8f8f8', 'secondaryColor': '#2b2b2b', 'tertiaryColor': '#1a1a1a'}}}%%
graph TB
    classDef main fill:#1a1a1a,stroke:#555,color:#fff
    classDef component fill:#242424,stroke:#555,color:#fff
    classDef subcomponent fill:#2b2b2b,stroke:#555,color:#fff
    classDef adapter fill:#203040,stroke:#555,color:#fff
    classDef context fill:#302030,stroke:#555,color:#fff
    classDef prompt fill:#203020,stroke:#555,color:#fff
    classDef external fill:#302020,stroke:#555,color:#fff

    subgraph IntegrationSystem["NCA Integration System"]
        direction TB
        class IntegrationSystem main
        
        subgraph CoreComponents["Core Integration Components"]
            direction TB
            class CoreComponents component
            
            subgraph Manager["LLM Integration Manager"]
                direction TB
                class Manager adapter
                QueryProcessing[Query<br>Processing] --- ResponseProcessing[Response<br>Processing]
                ProviderSelection[Provider<br>Selection] --- Fallbacks[Fallback<br>Management]
                class QueryProcessing,ResponseProcessing,ProviderSelection,Fallbacks subcomponent
            end
            
            subgraph Adapters["LLM Adapters"]
                direction TB
                class Adapters adapter
                OpenAIAdapter[OpenAI<br>Adapter] --- AnthropicAdapter[Anthropic<br>Adapter]
                VertexAIAdapter[VertexAI<br>Adapter] --- OllamaAdapter[Ollama<br>Adapter]
                CustomAdapters[Custom<br>Adapters]
                class OpenAIAdapter,AnthropicAdapter,VertexAIAdapter,OllamaAdapter,CustomAdapters subcomponent
            end
            
            subgraph Context["Context Management"]
                direction TB
                class Context context
                ContextEnhancement[Context<br>Enhancement] --- PromptEnrichment[Prompt<br>Enrichment]
                ContextAggregation[Context<br>Aggregation] --- ContextFiltering[Context<br>Filtering]
                class ContextEnhancement,PromptEnrichment,ContextAggregation,ContextFiltering subcomponent
            end
            
            subgraph Prompts["Prompt Templates"]
                direction TB
                class Prompts prompt
                TemplateManager[Template<br>Manager] --- TemplateRenderer[Template<br>Renderer]
                TemplateCaching[Template<br>Caching] --- TemplateCompilation[Template<br>Compilation]
                class TemplateManager,TemplateRenderer,TemplateCaching,TemplateCompilation subcomponent
            end
        end
        
        subgraph Models["Integration Models"]
            direction TB
            class Models component
            LLMRequest[LLM<br>Request] --- LLMResponse[LLM<br>Response]
            RequestConfig[Request<br>Configuration] --- ResponseMetadata[Response<br>Metadata]
            class LLMRequest,LLMResponse,RequestConfig,ResponseMetadata subcomponent
        end
        
        subgraph ExternalIntegrations["External Integrations"]
            direction TB
            class ExternalIntegrations component
            LangChain[LangChain<br>Integration] --- CustomTools[Custom<br>Tools]
            Plugins[Plugin<br>System] --- ExternalAPIs[External<br>APIs]
            class LangChain,CustomTools,Plugins,ExternalAPIs subcomponent
        end
    end
    
    %% External connections
    MemorySystem[Memory<br>System] --> Context
    HealthSystem[Health<br>System] --> Manager
    GoalSystem[Goal<br>System] --> Context
    
    %% Internal connections
    Manager --> Adapters
    Context --> Manager
    Prompts --> Context
    Models --> Manager
    ExternalIntegrations --> Manager
    
    %% Provider connections
    OpenAIAdapter --> OpenAIService[OpenAI<br>Service]
    AnthropicAdapter --> AnthropicService[Anthropic<br>Service]
    VertexAIAdapter --> VertexAIService[VertexAI<br>Service]
    OllamaAdapter --> OllamaService[Ollama<br>Service]
    
    %% External system integrations
    LangChain --> LangChainFramework[LangChain<br>Framework]
    
    %% Node styling
    class MemorySystem,HealthSystem,GoalSystem,OpenAIService,AnthropicService,VertexAIService,OllamaService,LangChainFramework external
```

## Integration System Components

The NCA integration system provides a framework for connecting the cognitive architecture with external LLM providers and frameworks. It consists of the following key components:

### Core Integration Components

1. **LLM Integration Manager**:
   - **Query Processing**: Processes and enhances queries before sending to LLMs
   - **Response Processing**: Processes and filters responses from LLMs
   - **Provider Selection**: Selects appropriate LLM provider based on requirements
   - **Fallback Management**: Handles fallbacks when primary providers fail

2. **LLM Adapters**:
   - **OpenAI Adapter**: Interface for OpenAI models
   - **Anthropic Adapter**: Interface for Anthropic models
   - **VertexAI Adapter**: Interface for Google's VertexAI models
   - **Ollama Adapter**: Interface for local Ollama models
   - **Custom Adapters**: Framework for custom LLM interfaces

3. **Context Management**:
   - **Context Enhancement**: Enhances prompts with context
   - **Prompt Enrichment**: Enriches prompts with cognitive capabilities
   - **Context Aggregation**: Combines context from different sources
   - **Context Filtering**: Filters context based on relevance

4. **Prompt Templates**:
   - **Template Manager**: Manages prompt templates
   - **Template Renderer**: Renders templates with variables
   - **Template Caching**: Caches templates for performance
   - **Template Compilation**: Compiles templates for efficient rendering

### Integration Models

1. **LLM Request**: Model for representing LLM requests
2. **LLM Response**: Model for representing LLM responses
3. **Request Configuration**: Configuration for LLM requests
4. **Response Metadata**: Metadata for LLM responses

### External Integrations

1. **LangChain Integration**: Integration with LangChain framework
2. **Custom Tools**: Custom tools for LLM interactions
3. **Plugin System**: Framework for plugins
4. **External APIs**: Connections to external APIs

### External Connections

The integration system connects with:
- **Memory System**: For retrieving relevant memories
- **Health System**: For health-aware adaptations
- **Goal System**: For goal-directed prompting

### Provider Connections

The integration system connects to external LLM providers:
- **OpenAI Service**: For OpenAI models
- **Anthropic Service**: For Anthropic models
- **VertexAI Service**: For Google's VertexAI models
- **Ollama Service**: For local Ollama models

The integration system is designed to provide a unified interface for interacting with various LLM providers while enhancing the interactions with NCA's cognitive capabilities.
