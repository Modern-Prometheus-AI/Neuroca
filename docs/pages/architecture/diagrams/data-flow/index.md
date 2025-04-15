# Data Flow Architecture

Overview of data flows in the NeuroCognitive Architecture.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#242424', 'primaryTextColor': '#fff', 'primaryBorderColor': '#555', 'lineColor': '#f8f8f8', 'secondaryColor': '#2b2b2b', 'tertiaryColor': '#1a1a1a'}}}%%
graph LR
    classDef main fill:#1a1a1a,stroke:#555,color:#fff
    classDef component fill:#242424,stroke:#555,color:#fff
    classDef subcomponent fill:#2b2b2b,stroke:#555,color:#fff
    classDef flow fill:#302030,stroke:#555,color:#fff

    subgraph DataFlow["NCA Data Flow"]
        direction TB
        class DataFlow main
        
        Input[External<br>Input]:::flow --> APILayer[API<br>Layer]:::flow
        APILayer --> InputProcessing[Input<br>Processing]:::flow
        InputProcessing --> MemorySystem[Memory<br>System]:::flow
        
        MemorySystem --> CognitiveSystem[Cognitive<br>System]:::flow
        CognitiveSystem --> ReasoningEngine[Reasoning<br>Engine]:::flow
        ReasoningEngine --> DecisionMaking[Decision<br>Making]:::flow
        
        DecisionMaking --> ActionSelection[Action<br>Selection]:::flow
        ActionSelection --> OutputFormation[Output<br>Formation]:::flow
        OutputFormation --> APILayer
        APILayer --> Output[External<br>Output]:::flow
        
        %% Memory Flows
        MemorySystem --> WorkingMemory[Working<br>Memory]:::flow
        MemorySystem --> EpisodicMemory[Episodic<br>Memory]:::flow
        MemorySystem --> SemanticMemory[Semantic<br>Memory]:::flow
        
        %% LLM Integration Flows
        InputProcessing --> LLMIntegration[LLM<br>Integration]:::flow
        LLMIntegration --> SemanticMemory
        LLMIntegration --> CognitiveSystem
        
        %% Health System Flows
        HealthSystem[Health<br>System]:::flow --> CognitiveSystem
        HealthSystem --> MemorySystem
        CognitiveSystem --> HealthSystem
        
        class WorkingMemory,EpisodicMemory,SemanticMemory,LLMIntegration,HealthSystem flow
    end
```

## Data Flow Architecture Components

The Data Flow Architecture shows how information moves through the NeuroCognitive Architecture system, from input to output.

### Main Data Flow
- **External Input**: Information entering the system from external sources
- **API Layer**: Entry and exit point for external interactions
- **Input Processing**: Initial processing of incoming information
- **Memory System**: Storage and retrieval of information in the three-tiered memory
- **Cognitive System**: Core cognitive processing components
- **Reasoning Engine**: Applies reasoning methods to information
- **Decision Making**: Makes decisions based on reasoning and goals
- **Action Selection**: Selects actions based on decisions
- **Output Formation**: Formats the selected actions for output
- **External Output**: Information leaving the system to external recipients

### Memory Flows
- Information flows between the Memory System and its three tiers: Working Memory, Episodic Memory, and Semantic Memory
- Each tier has different storage characteristics and retrieval patterns

### LLM Integration Flows
- The LLM Integration component receives processed input
- It provides processed information to both the Semantic Memory and Cognitive System
- This enables embeddings for memory storage and semantic understanding for reasoning

### Health System Flows
- The Health System monitors and regulates both the Cognitive System and Memory System
- It receives feedback from the Cognitive System to update health metrics
- This creates a feedback loop that maintains system health and performance

The flow architecture ensures that information is processed in a structured way, moving from input through processing and memory systems, to cognitive components, and finally to output, with health monitoring throughout.
