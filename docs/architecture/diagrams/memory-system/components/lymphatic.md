# Lymphatic System

Details of the Lymphatic System responsible for memory maintenance and cleaning.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#242424', 'primaryTextColor': '#fff', 'primaryBorderColor': '#555', 'lineColor': '#f8f8f8', 'secondaryColor': '#2b2b2b', 'tertiaryColor': '#1a1a1a'}}}%%
graph TB
    classDef main fill:#1a1a1a,stroke:#555,color:#fff
    classDef component fill:#242424,stroke:#555,color:#fff
    classDef subcomponent fill:#2b2b2b,stroke:#555,color:#fff
    classDef lymphatic fill:#203020,stroke:#555,color:#fff

    subgraph LymphaticSystem["Lymphatic System"]
        direction TB
        class LymphaticSystem main
        
        Scheduler[Maintenance<br>Scheduler]:::component
        
        subgraph Cleaning["Memory Cleaning"]
            direction TB
            class Cleaning lymphatic
            ObsoleteDetection[Obsolete<br>Detection] --- RedundancyCheck[Redundancy<br>Check]
            IrrelevanceMarking[Irrelevance<br>Marking] --- DecayApplication[Decay<br>Application]
            class ObsoleteDetection,RedundancyCheck,IrrelevanceMarking,DecayApplication subcomponent
        end
        
        subgraph Pruning["Memory Pruning"]
            direction TB
            class Pruning lymphatic
            WeakLinkRemoval[Weak Link<br>Removal] --- LowImportance[Low Importance<br>Removal]
            AgeBasedPruning[Age-Based<br>Pruning] --- CapacityMgmt[Capacity<br>Management]
            class WeakLinkRemoval,LowImportance,AgeBasedPruning,CapacityMgmt subcomponent
        end
        
        subgraph Maintenance["Health Maintenance"]
            direction TB
            class Maintenance lymphatic
            IntegrityCheck[Integrity<br>Check] --- ConsistencyCheck[Consistency<br>Check]
            IndexRebuild[Index<br>Rebuild] --- StatUpdate[Statistics<br>Update]
            class IntegrityCheck,ConsistencyCheck,IndexRebuild,StatUpdate subcomponent
        end
        
        subgraph Repair["Memory Repair"]
            direction TB
            class Repair lymphatic
            CorruptionDetection[Corruption<br>Detection] --- DataRecovery[Data<br>Recovery]
            LinkReconstruction[Link<br>Reconstruction] --- ErrorCorrection[Error<br>Correction]
            class CorruptionDetection,DataRecovery,LinkReconstruction,ErrorCorrection subcomponent
        end
    end
    
    %% Connections
    Scheduler --> Cleaning
    Scheduler --> Pruning
    Scheduler --> Maintenance
    Scheduler --> Repair
    
    MemoryManager[Memory<br>Manager] --> Scheduler
    HealthSystem[Health<br>System] --> Scheduler
    
    Cleaning --> Pruning
    Maintenance --> Repair
    
    class MemoryManager,HealthSystem subcomponent
```

## Lymphatic System Components

Inspired by the brain's glymphatic system, the NCA's Lymphatic System performs background maintenance tasks to keep the memory system healthy and efficient.

### Maintenance Scheduler
- Orchestrates the execution of cleaning, pruning, maintenance, and repair tasks, often during periods of low cognitive load (simulated "sleep").

### Memory Cleaning
- **Obsolete Detection**: Identifies memory items that are no longer valid or relevant.
- **Redundancy Check**: Finds and marks duplicate or redundant information.
- **Irrelevance Marking**: Flags items that have become irrelevant based on current goals or context.
- **Decay Application**: Applies decay mechanisms to reduce the strength or salience of unused items.

### Memory Pruning
- **Weak Link Removal**: Removes weak connections between memory items.
- **Low Importance Removal**: Deletes items deemed unimportant based on metadata or usage.
- **Age-Based Pruning**: Removes old items that haven't been accessed recently (configurable).
- **Capacity Management**: Prunes items to stay within storage capacity limits.

### Health Maintenance
- **Integrity Check**: Verifies the structural integrity of memory data.
- **Consistency Check**: Ensures consistency across related memory items and indexes.
- **Index Rebuild**: Rebuilds search indexes for optimal performance.
- **Statistics Update**: Updates metadata and statistics about memory usage.

### Memory Repair
- **Corruption Detection**: Identifies corrupted or damaged memory data.
- **Data Recovery**: Attempts to recover data from backups or redundant sources.
- **Link Reconstruction**: Tries to repair broken links between memory items.
- **Error Correction**: Corrects errors in memory content where possible.

The Lymphatic System is triggered by the Memory Manager, potentially influenced by the Health System's state (e.g., running more intensively during low-load periods). Its goal is to prevent memory clutter, maintain performance, and ensure data integrity.
