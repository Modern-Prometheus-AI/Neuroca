# Memory System Component Interactions

**Last Updated:** April 14, 2025

This document outlines the key interactions between components in the Neuroca memory system. These sequence diagrams illustrate how the various interfaces and components work together to implement core operations.

## Operation 1: Memory Addition

This sequence diagram illustrates the process of adding a new memory item to the system.

```mermaid
sequenceDiagram
    participant Client
    participant MemoryManager
    participant TierFactory
    participant STMTier
    participant StorageBackend
    
    Client->>MemoryManager: add_memory(content, importance, tags, ...)
    
    Note over MemoryManager: Create MemoryItem
    
    alt initial_tier provided
        MemoryManager->>TierFactory: get_tier(initial_tier)
    else no initial_tier
        MemoryManager->>TierFactory: get_tier("stm")
    end
    
    TierFactory-->>MemoryManager: tier_instance (e.g., STMTier)
    
    MemoryManager->>STMTier: store(memory_item)
    
    Note over STMTier: Add tier-specific metadata
    
    STMTier->>StorageBackend: create(memory_id, memory_data)
    StorageBackend-->>STMTier: success (bool)
    
    alt embedding required
        MemoryManager->>MemoryManager: generate_embedding(memory_content)
        STMTier->>StorageBackend: store_embedding(memory_id, embedding)
    end
    
    STMTier-->>MemoryManager: memory_id
    MemoryManager-->>Client: memory_id
```

### Key Points:
- The MemoryManager handles validation and initial processing of the memory item
- The appropriate tier is determined (STM by default)
- The tier adds tier-specific metadata before storage
- Embeddings are generated and stored if needed
- The memory ID is returned to the client

## Operation 2: Memory Retrieval

This sequence diagram illustrates the process of retrieving a memory by ID.

```mermaid
sequenceDiagram
    participant Client
    participant MemoryManager
    participant TierRegistry
    participant STMTier
    participant MTMTier
    participant LTMTier
    participant StorageBackend
    
    Client->>MemoryManager: retrieve_memory(memory_id, tier=None)
    
    alt tier specified
        MemoryManager->>TierRegistry: get_tier(tier)
        TierRegistry-->>MemoryManager: specific_tier
        MemoryManager->>specific_tier: retrieve(memory_id)
        specific_tier->>StorageBackend: read(memory_id)
        StorageBackend-->>specific_tier: memory_data
        specific_tier-->>MemoryManager: memory_item
    else tier not specified
        MemoryManager->>TierRegistry: get_all_tiers()
        TierRegistry-->>MemoryManager: [stm_tier, mtm_tier, ltm_tier]
        
        MemoryManager->>STMTier: retrieve(memory_id)
        STMTier->>StorageBackend: read(memory_id)
        StorageBackend-->>STMTier: memory_data or None
        STMTier-->>MemoryManager: memory_item or None
        
        alt memory not found in STM
            MemoryManager->>MTMTier: retrieve(memory_id)
            MTMTier->>StorageBackend: read(memory_id)
            StorageBackend-->>MTMTier: memory_data or None
            MTMTier-->>MemoryManager: memory_item or None
            
            alt memory not found in MTM
                MemoryManager->>LTMTier: retrieve(memory_id)
                LTMTier->>StorageBackend: read(memory_id)
                StorageBackend-->>LTMTier: memory_data or None
                LTMTier-->>MemoryManager: memory_item or None
            end
        end
    end
    
    alt memory found
        MemoryManager->>MemoryManager: mark_memory_accessed(memory_item)
    end
    
    MemoryManager-->>Client: memory_item or None
```

### Key Points:
- If tier is specified, only that tier is searched
- If no tier is specified, tiers are searched in order: STM -> MTM -> LTM
- When a memory is found, it's marked as accessed (updating strength/access count)
- If not found in any tier, None is returned

## Operation 3: Memory Search

This sequence diagram illustrates searching for memories across tiers.

```mermaid
sequenceDiagram
    participant Client
    participant MemoryManager
    participant TierRegistry
    participant STMTier
    participant MTMTier
    participant LTMTier
    participant WorkingMemory
    
    Client->>MemoryManager: search_memories(query, tags, etc.)
    
    alt tiers specified in search options
        MemoryManager->>TierRegistry: get_tiers(search_options.tiers)
        TierRegistry-->>MemoryManager: specified_tiers
    else no tiers specified
        MemoryManager->>TierRegistry: get_all_tiers()
        TierRegistry-->>MemoryManager: [stm_tier, mtm_tier, ltm_tier]
    end
    
    par Search STM
        MemoryManager->>STMTier: search(query, tags, etc.)
        STMTier-->>MemoryManager: stm_results
    and Search MTM
        MemoryManager->>MTMTier: search(query, tags, etc.)
        MTMTier-->>MemoryManager: mtm_results
    and Search LTM
        MemoryManager->>LTMTier: search(query, tags, etc.)
        LTMTier-->>MemoryManager: ltm_results
    end
    
    MemoryManager->>MemoryManager: combine_and_deduplicate_results()
    MemoryManager->>MemoryManager: rank_results_by_relevance()
    MemoryManager->>MemoryManager: limit_results(options.limit)
    
    alt update working memory with results
        MemoryManager->>WorkingMemory: update_with_search_results(results)
    end
    
    MemoryManager-->>Client: search_results
```

### Key Points:
- Searches can be performed across all tiers or specific tiers
- Searches are performed in parallel across tiers
- Results are combined, deduplicated and ranked by relevance
- Results can optionally update the working memory buffer
- Final results are limited according to search options

## Operation 4: Memory Consolidation

This sequence diagram illustrates the process of consolidating memories between tiers.

```mermaid
sequenceDiagram
    participant MemoryManager
    participant ConsolidationService
    participant STMTier
    participant MTMTier
    participant LTMTier
    
    Note over MemoryManager: Run maintenance task (scheduled)
    MemoryManager->>ConsolidationService: run_consolidation_cycle()
    
    Note over ConsolidationService: Process STM -> MTM
    ConsolidationService->>STMTier: get_candidates_for_consolidation()
    STMTier-->>ConsolidationService: stm_candidates
    
    loop for each candidate
        ConsolidationService->>ConsolidationService: evaluate_consolidation_criteria(memory)
        alt should consolidate to MTM
            ConsolidationService->>STMTier: retrieve(memory_id)
            STMTier-->>ConsolidationService: memory_item
            
            ConsolidationService->>ConsolidationService: prepare_for_mtm(memory_item)
            ConsolidationService->>MTMTier: store(memory_item)
            MTMTier-->>ConsolidationService: mtm_memory_id
            
            ConsolidationService->>STMTier: update_status(memory_id, CONSOLIDATED)
        end
    end
    
    Note over ConsolidationService: Process MTM -> LTM
    ConsolidationService->>MTMTier: get_candidates_for_consolidation()
    MTMTier-->>ConsolidationService: mtm_candidates
    
    loop for each candidate
        ConsolidationService->>ConsolidationService: evaluate_consolidation_criteria(memory)
        alt should consolidate to LTM
            ConsolidationService->>MTMTier: retrieve(memory_id)
            MTMTier-->>ConsolidationService: memory_item
            
            ConsolidationService->>ConsolidationService: prepare_for_ltm(memory_item)
            ConsolidationService->>LTMTier: store(memory_item)
            LTMTier-->>ConsolidationService: ltm_memory_id
            
            ConsolidationService->>MTMTier: update_status(memory_id, CONSOLIDATED)
        end
    end
    
    ConsolidationService->>MemoryManager: consolidation_report(stats)
```

### Key Points:
- Consolidation runs as a scheduled maintenance task
- It processes memories in both directions: STM -> MTM and MTM -> LTM
- Each tier provides candidates for consolidation based on tier-specific criteria
- Candidates are evaluated against consolidation criteria (importance, access patterns, etc.)
- Consolidated memories are stored in the target tier with appropriate metadata
- Original memories are marked as CONSOLIDATED in the source tier

## Operation 5: Context Update and Working Memory Management

This sequence diagram illustrates updating the context and managing working memory.

```mermaid
sequenceDiagram
    participant Client
    participant MemoryManager
    participant WorkingMemory
    participant RelevanceCalculator
    participant TierRegistry
    participant STMTier
    participant MTMTier
    participant LTMTier
    
    Client->>MemoryManager: update_context(context_data)
    MemoryManager->>WorkingMemory: update_context(context_data)
    
    alt embedding not provided
        MemoryManager->>MemoryManager: generate_embedding(context_text)
    end
    
    Note over MemoryManager: Search across tiers
    
    par Search STM
        MemoryManager->>STMTier: search(embedding=context_embedding)
        STMTier-->>MemoryManager: stm_relevant_memories
    and Search MTM
        MemoryManager->>MTMTier: search(embedding=context_embedding)
        MTMTier-->>MemoryManager: mtm_relevant_memories
    and Search LTM
        MemoryManager->>LTMTier: search(embedding=context_embedding)
        LTMTier-->>MemoryManager: ltm_relevant_memories
    end
    
    MemoryManager->>MemoryManager: combine_relevant_memories()
    
    loop for each memory
        MemoryManager->>RelevanceCalculator: calculate_relevance(memory, context)
        RelevanceCalculator-->>MemoryManager: relevance_score
        
        MemoryManager->>WorkingMemory: add_item(memory, relevance_score)
    end
    
    WorkingMemory->>WorkingMemory: sort_by_relevance()
    WorkingMemory->>WorkingMemory: prune_to_capacity_limit()
    
    MemoryManager-->>Client: success
```

### Key Points:
- Context update triggers a search for relevant memories across all tiers
- Context can be provided with a pre-computed embedding or one will be generated
- Results from all tiers are combined and their relevance to the current context is calculated
- Relevant memories are added to the working memory buffer
- The buffer is sorted by relevance and pruned to maintain its capacity limit

## Operation 6: Getting Memories for Prompt Context

This sequence diagram illustrates retrieving memories for prompt context.

```mermaid
sequenceDiagram
    participant Client
    participant MemoryManager
    participant WorkingMemory
    
    Client->>MemoryManager: get_prompt_context_memories(max_memories, max_tokens)
    
    MemoryManager->>WorkingMemory: get_items_for_prompt(max_memories, min_relevance)
    
    WorkingMemory->>WorkingMemory: select_top_n_relevant_items()
    WorkingMemory->>WorkingMemory: format_items_for_prompt(max_tokens)
    
    WorkingMemory-->>MemoryManager: formatted_memories
    
    MemoryManager-->>Client: formatted_memories
```

### Key Points:
- Retrieving prompt context memories uses the working memory buffer
- The most relevant memories are selected based on relevance scores
- Memories are formatted appropriately for prompt inclusion
- Text content is truncated if needed to fit within token limits

## Implementation Notes

These interactions demonstrate the following design principles:

1. **Clean Separation of Concerns:**
   - MemoryManager handles orchestration
   - Tiers handle tier-specific behavior
   - Storage backends handle persistence
   - Working memory manages the context-aware buffer

2. **Async Operation:**
   - All operations are designed to be asynchronous
   - Parallel processing is used where appropriate

3. **Error Handling:**
   - Each component should propagate appropriate exceptions
   - The MemoryManager provides a clean interface with unified error handling

4. **Extensibility:**
   - New storage backends can be added without changing tiers
   - New tier implementations can be added without changing the MemoryManager
   - New consolidation or relevance algorithms can be plugged in
