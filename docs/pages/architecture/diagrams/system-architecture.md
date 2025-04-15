# NCA System Architecture

This diagram provides a high-level overview of the complete NeuroCognitive Architecture (NCA) system, based on the actual codebase structure.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#242424', 'primaryTextColor': '#fff', 'primaryBorderColor': '#555', 'lineColor': '#f8f8f8', 'secondaryColor': '#2b2b2b', 'tertiaryColor': '#1a1a1a'}}}%%
graph TB
    classDef main fill:#1a1a1a,stroke:#555,color:#fff
    classDef component fill:#242424,stroke:#555,color:#fff
    classDef subcomponent fill:#2b2b2b,stroke:#555,color:#fff
    classDef memory fill:#203040,stroke:#555,color:#fff
    classDef core fill:#303020,stroke:#555,color:#fff
    classDef integration fill:#302030,stroke:#555,color:#fff
    classDef infrastructure fill:#203020,stroke:#555,color:#fff
    
    subgraph NCA["NeuroCognitive Architecture"]
        direction TB
        class NCA main
        
        subgraph API["API Layer"]
            direction TB
            class API component
            REST[REST API] --- GraphQL[GraphQL API]
            Schemas[API Schemas] --- Endpoints[API Endpoints]
            class REST,GraphQL,Schemas,Endpoints subcomponent
        end
        
        subgraph CLI["Command Line Interface"]
            direction TB
            class CLI component
            CLICommands[CLI Commands]
            class CLICommands subcomponent
        end
        
        subgraph Config["Configuration System"]
            direction TB
            class Config component
            Settings[Settings Manager] --- EnvVars[Environment Variables]
            ConfigFiles[Config Files] --- Validation[Config Validation]
            class Settings,EnvVars,ConfigFiles,Validation subcomponent
        end
        
        subgraph Core["Core Components"]
            direction TB
            class Core component
            
            subgraph CognitiveControl["Cognitive Control"]
                direction TB
                class CognitiveControl core
                Attention[Attention<br>Controller] --- Reasoning[Reasoning<br>Engine]
                Executive[Executive<br>Function] --- MetaCog[Meta<br>Cognition]
                class Attention,Reasoning,Executive,MetaCog subcomponent
            end
            
            subgraph HealthSystem["Health System"]
                direction TB
                class HealthSystem core
                Monitors[Health<br>Monitors] --- Metrics[Health<br>Metrics]
                Regulation[Regulation<br>System] --- Alerting[Alerting<br>System]
                class Monitors,Metrics,Regulation,Alerting subcomponent
            end
            
            subgraph CoreModels["Core Models"]
                direction TB
                class CoreModels core
                BaseModels[Base<br>Models] --- Types[Type<br>Definitions]
                Constants[System<br>Constants] --- Events[Event<br>System]
                class BaseModels,Types,Constants,Events subcomponent
            end
            
            CognitiveControl --- HealthSystem
            HealthSystem --- CoreModels
        end
        
        subgraph Memory["Memory System"]
            direction TB
            class Memory component
            
            subgraph Tiers["Memory Tiers"]
                direction LR
                class Tiers memory
                Working[Working<br>Memory] --> Episodic[Episodic<br>Memory]
                Episodic --> Semantic[Semantic<br>Memory]
                class Working,Episodic,Semantic subcomponent
            end
            
            subgraph Backends["Memory Backends"]
                direction LR
                class Backends memory
                InMemory[In-Memory] --- SQLite[SQLite]
                Redis[Redis] --- Vector[Vector<br>Storage]
                class InMemory,SQLite,Redis,Vector subcomponent
            end
            
            subgraph MemoryManager["Memory Manager"]
                direction TB
                class MemoryManager memory
                Storage[Storage<br>Manager] --- Retrieval[Retrieval<br>System]
                Consolidation[Memory<br>Consolidation] --- Lymphatic[Lymphatic<br>System]
                Tubules[Memory<br>Tubules] --- Annealing[Memory<br>Annealing]
                class Storage,Retrieval,Consolidation,Lymphatic,Tubules,Annealing subcomponent
            end
            
            Tiers --- MemoryManager
            MemoryManager --- Backends
        end
        
        subgraph Integration["External Integrations"]
            direction TB
            class Integration component
            
            subgraph LangChain["LangChain Integration"]
                direction TB
                class LangChain integration
                Chains[LangChain<br>Chains] --- MemInt[Memory<br>Integration]
                Tools[LangChain<br>Tools] --- Adapters[LangChain<br>Adapters]
                class Chains,MemInt,Tools,Adapters subcomponent
            end
            
            subgraph LLMs["LLM Integration"]
                direction TB
                class LLMs integration
                Connectors[LLM<br>Connectors] --- Providers[LLM<br>Providers]
                Models[Model<br>Management] --- Embeddings[Embedding<br>Models]
                class Connectors,Providers,Models,Embeddings subcomponent
            end
            
            subgraph ExtTools["External Tools"]
                direction TB
                class ExtTools integration
                APIClients[API<br>Clients] --- Plugins[Plugin<br>System]
                class APIClients,Plugins subcomponent
            end
            
            LangChain --- LLMs
            LLMs --- ExtTools
        end
        
        subgraph DB["Database Layer"]
            direction TB
            class DB component
            Models[DB Models] --- ORM[ORM System]
            Migrations[Migrations] --- Connections[Connection<br>Pool]
            class Models,ORM,Migrations,Connections subcomponent
        end
        
        subgraph Infrastructure["Infrastructure"]
            direction TB
            class Infrastructure component
            Logging[Logging<br>System] --- Metrics[Metrics<br>Collection]
            Telemetry[Telemetry] --- Security[Security<br>Layer]
            class Logging,Metrics,Telemetry,Security subcomponent
        end
        
        subgraph Monitoring["Monitoring"]
            direction TB
            class Monitoring component
            Performance[Performance<br>Monitoring] --- HealthChecks[Health<br>Checks]
            Alerts[Alerting<br>System] --- Dashboard[Monitoring<br>Dashboard]
            class Performance,HealthChecks,Alerts,Dashboard subcomponent
        end
        
        subgraph Utils["Utilities"]
            direction TB
            class Utils component
            Helpers[Helper<br>Functions] --- IO[I/O<br>Utilities]
            Formatting[Formatting<br>Utilities] --- Time[Time<br>Utilities]
            class Helpers,IO,Formatting,Time subcomponent
        end
    end
    
    Client[Client Applications] --> API
    ExtLLMs[External LLMs] --> LLMs
    
    API --> Core
    API --> Memory
    CLI --> Core
    CLI --> Config
    
    Core --> Memory
    Core --> Integration
    Core --> DB
    
    Memory --> DB
    Integration --> Memory
    
    Infrastructure --> Monitoring
    
    class Client,ExtLLMs subcomponent
```

## Key Components

1. **API Layer**: Exposes NCA functionality through REST and GraphQL interfaces, with defined schemas and endpoints
2. **CLI**: Command-line interface for interacting with the system
3. **Configuration System**: Manages settings, environment variables, and configuration files
4. **Core Components**:
   - **Cognitive Control**: Manages attention, reasoning, executive function, and metacognition
   - **Health System**: Monitors and regulates system health, fatigue, and cognitive load
   - **Core Models**: Defines base models, types, constants, and event system
5. **Memory System**:
   - **Memory Tiers**: Working, episodic, and semantic memory tiers
   - **Memory Manager**: Manages storage, retrieval, consolidation, and includes specialized subsystems like lymphatic system, tubules, and annealing
   - **Memory Backends**: Various storage backends including in-memory, SQLite, Redis, and vector storage
6. **External Integrations**:
   - **LangChain Integration**: Connects with LangChain framework through chains, memory integration, tools, and adapters
   - **LLM Integration**: Interfaces with various language models through connectors, providers, model management, and embedding models
   - **External Tools**: API clients and plugin system for external tools
7. **Database Layer**: Models, ORM system, migrations, and connection pool
8. **Infrastructure**: Logging, metrics collection, telemetry, and security
9. **Monitoring**: Performance monitoring, health checks, alerting system, and dashboard
10. **Utilities**: Helper functions, I/O utilities, formatting utilities, and time utilities

The architecture follows a modular design with clear separation of concerns, allowing for flexible integration with external systems while maintaining the cognitive architecture's biological inspiration.
