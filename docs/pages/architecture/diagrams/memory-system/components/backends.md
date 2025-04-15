# Memory Backends

Details of the storage backend implementations for the NCA memory system.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#242424', 'primaryTextColor': '#fff', 'primaryBorderColor': '#555', 'lineColor': '#f8f8f8', 'secondaryColor': '#2b2b2b', 'tertiaryColor': '#1a1a1a'}}}%%
graph TB
    classDef main fill:#1a1a1a,stroke:#555,color:#fff
    classDef component fill:#242424,stroke:#555,color:#fff
    classDef subcomponent fill:#2b2b2b,stroke:#555,color:#fff
    classDef backend fill:#302030,stroke:#555,color:#fff

    subgraph Backends["Storage Backends"]
        direction TB
        class Backends main
        
        BackendInterface[Backend<br>Interface]:::component
        
        subgraph InMemory["In-Memory Backend"]
            direction TB
            class InMemory backend
            RAMStore[RAM<br>Storage] --- DictStore[Dictionary<br>Store]
            Volatile[Volatile<br>Nature] --- FastAccess[Fast<br>Access]
            class RAMStore,DictStore,Volatile,FastAccess subcomponent
        end
        
        subgraph SQLite["SQLite Backend"]
            direction TB
            class SQLite backend
            FileDB[File-based<br>Database] --- SQLOps[SQL<br>Operations]
            SchemaMgmt[Schema<br>Management] --- Indexing[DB<br>Indexing]
            class FileDB,SQLOps,SchemaMgmt,Indexing subcomponent
        end
        
        subgraph Redis["Redis Backend"]
            direction TB
            class Redis backend
            KeyValue[Key-Value<br>Store] --- Caching[Caching<br>Layer]
            Persistence[Persistence<br>Options] --- DataStructures[Redis Data<br>Structures]
            class KeyValue,Caching,Persistence,DataStructures subcomponent
        end
        
        subgraph Vector["Vector Storage Backend"]
            direction TB
            class Vector backend
            VectorDB[Vector<br>Database<br>(e.g., LanceDB)] --- SimilaritySearch[Similarity<br>Search]
            EmbeddingStore[Embedding<br>Storage] --- Indexing[Vector<br>Indexing]
            class VectorDB,SimilaritySearch,EmbeddingStore,Indexing subcomponent
        end
    end
    
    %% Connections
    BackendInterface --> InMemory
    BackendInterface --> SQLite
    BackendInterface --> Redis
    BackendInterface --> Vector
    
    MemoryManager[Memory<br>Manager] --> BackendInterface
    
    class MemoryManager subcomponent
```

## Memory Backend Components

The NCA memory system supports multiple storage backends, allowing flexibility in deployment and performance characteristics. All backends adhere to a common `BackendInterface`.

### In-Memory Backend
- **RAM Storage**: Stores data directly in system memory.
- **Dictionary Store**: Often implemented using Python dictionaries.
- **Volatile Nature**: Data is lost when the system restarts unless persistence is separately managed.
- **Fast Access**: Provides the fastest access speeds. Suitable for Working Memory.

### SQLite Backend
- **File-based Database**: Stores data in a local file.
- **SQL Operations**: Uses standard SQL for data manipulation.
- **Schema Management**: Defines table structures for memory items.
- **DB Indexing**: Uses database indexes for faster querying. Suitable for persistent storage on single nodes.

### Redis Backend
- **Key-Value Store**: Stores data primarily as key-value pairs.
- **Caching Layer**: Can be used as a fast cache in front of other backends.
- **Persistence Options**: Offers configurable persistence mechanisms (RDB, AOF).
- **Redis Data Structures**: Leverages Redis's advanced data structures (hashes, lists, sets). Suitable for distributed caching or session storage.

### Vector Storage Backend
- **Vector Database**: Specialized database for storing and querying high-dimensional vectors (e.g., LanceDB, Milvus, Pinecone).
- **Similarity Search**: Enables efficient searching based on vector similarity (e.g., cosine similarity, dot product).
- **Embedding Storage**: Stores vector embeddings generated from memory content.
- **Vector Indexing**: Uses specialized indexing techniques (e.g., HNSW, IVF) for fast vector search. Crucial for Semantic Memory retrieval based on meaning.
