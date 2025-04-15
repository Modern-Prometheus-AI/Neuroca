# Memory System Backend Configuration

**Last Updated:** April 14, 2025  
**Status:** Complete

This document describes the configuration system for memory storage backends in the Neuroca memory system. It covers the configuration file structure, available options for each backend type, and how to use the configuration API.

## Overview

The memory system uses a centralized YAML-based configuration system to manage backend settings. This approach:

- Separates configuration from code
- Allows for environment-specific configurations
- Enables easy adjustment of performance parameters
- Supports multiple backend types with different configuration needs

Configuration files are stored in the `config/backends/` directory at the project root.

## Configuration File Structure

The configuration system uses two types of files:

1. **Base Configuration**: `base_config.yaml` - Contains common settings shared by all backends
2. **Backend-Specific Configuration**: `{backend_type}_config.yaml` - Contains settings specific to a particular backend type

When a backend is created, the relevant configuration files are loaded and merged, with backend-specific settings taking precedence over base settings.

### Base Configuration

The base configuration file (`base_config.yaml`) defines common settings across all backends:

```yaml
# Common settings for all backends
common:
  # Cache settings
  cache:
    enabled: true
    max_size: 1000
    ttl_seconds: 300  # 5 minutes

  # Batch operation settings
  batch:
    max_batch_size: 100
    auto_commit: true

  # Performance settings
  performance:
    connection_pool_size: 5
    connection_timeout_seconds: 10
    operation_timeout_seconds: 30

  # Logging settings
  logging:
    enabled: true
    level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_queries: false

  # Health check settings
  health_check:
    enabled: true
    interval_seconds: 60
    timeout_seconds: 5
    max_retries: 3

  # Metrics settings
  metrics:
    enabled: true
    collect_detailed_stats: false

# Default backend to use if not specified
default_backend: "in_memory"
```

## Backend-Specific Configurations

### In-Memory Backend

Configuration file: `in_memory_config.yaml`

```yaml
in_memory:
  # Memory allocation settings
  memory:
    initial_capacity: 1000
    auto_expand: true
    expansion_factor: 2
    max_capacity: 100000

  # Data structure settings
  data_structure:
    index_type: "hashmap"  # Options: hashmap, btree
    enable_secondary_indices: true
    
  # Persistence settings
  persistence:
    enabled: false
    file_path: "data/in_memory_backup.json"
    auto_save_interval_seconds: 300  # 5 minutes
    save_on_shutdown: true

  # Pruning settings
  pruning:
    enabled: true
    max_items: 10000
    strategy: "lru"  # Options: lru, lfu, fifo, lifo, random
    trigger_threshold: 0.9  # Pruning starts when capacity reaches 90%

  # Performance settings
  performance:
    use_concurrent_map: true
    lock_timeout_ms: 1000
```

### SQLite Backend

Configuration file: `sqlite_config.yaml`

```yaml
sqlite:
  # Connection settings
  connection:
    database_path: "data/memory_store.db"
    create_if_missing: true
    timeout_seconds: 5
    foreign_keys: true

  # Performance settings
  performance:
    page_size: 4096
    cache_size: 2000  # Pages in memory
    journal_mode: "WAL"  # Options: DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF
    synchronous: "NORMAL"  # Options: OFF, NORMAL, FULL, EXTRA
    temp_store: "MEMORY"  # Options: DEFAULT, FILE, MEMORY
    mmap_size: 0  # 0 to disable

  # Schema settings
  schema:
    auto_migrate: true
    migration_table: "_schema_migrations"
    enable_triggers: true
    enable_fts: true  # Full-text search

  # Query settings
  query:
    max_query_length: 10000
    max_parameters: 999
    enforce_foreign_keys: true
    explain_query_threshold_ms: 100
    
  # Transaction settings
  transaction:
    auto_vacuum: "INCREMENTAL"  # Options: NONE, FULL, INCREMENTAL
    auto_commit: true
    isolation_level: "IMMEDIATE"  # Options: DEFERRED, IMMEDIATE, EXCLUSIVE
    
  # Backup settings
  backup:
    enabled: true
    interval_hours: 24
    keep_backups: 7
    backup_path: "data/backups/"
```

### Redis Backend

Configuration file: `redis_config.yaml`

```yaml
redis:
  # Connection settings
  connection:
    host: "localhost"
    port: 6379
    database: 0
    username: ""
    password: ""
    use_ssl: false
    timeout_seconds: 5

  # Key settings
  keys:
    prefix: "neuroca:memory:"
    separator: ":"
    encoding: "utf-8"
    expire_ttl_seconds: 0  # 0 means no expiration

  # Performance settings
  performance:
    use_connection_pool: true
    max_connections: 10
    socket_keepalive: true
    socket_timeout_seconds: 5
    retry_on_timeout: true
    retry_on_error: true
    max_retries: 3
    
  # Data structure settings
  data_structure:
    use_hash_for_metadata: true
    use_sorted_sets_for_indexing: true
    use_lists_for_ordered_data: true
    use_sets_for_tags: true
    
  # Serialization settings
  serialization:
    format: "json"  # Options: json, msgpack, pickle
    compress: false
    compression_threshold_bytes: 1024
    compression_level: 6

  # Pub/Sub settings
  pubsub:
    enabled: false
    channel_prefix: "neuroca:events:"
    
  # Lua scripts
  lua_scripts:
    enabled: true
    cache_scripts: true
    
  # Sentinel settings (if using Redis Sentinel)
  sentinel:
    enabled: false
    master_name: "mymaster"
    sentinels:
      - host: "sentinel-1"
        port: 26379
      - host: "sentinel-2"
        port: 26379
```

### SQL Backend

Configuration file: `sql_config.yaml`

```yaml
sql:
  # Connection settings
  connection:
    driver: "postgresql"  # Options: postgresql, mysql, mssql, oracle
    host: "localhost"
    port: 5432
    database: "neuroca_memory"
    username: "neuroca_user"
    password: ""
    schema: "public"
    ssl_mode: "disable"  # Options: disable, allow, prefer, require, verify-ca, verify-full
    
  # Connection pool settings
  pool:
    min_connections: 2
    max_connections: 10
    max_idle_time_seconds: 300
    max_lifetime_seconds: 3600
    connection_timeout_seconds: 5
    
  # Schema settings
  schema:
    table_prefix: "mem_"
    metadata_table: "memory_metadata"
    content_table: "memory_content"
    tags_table: "memory_tags"
    relations_table: "memory_relations"
    use_jsonb_for_metadata: true
    auto_create_tables: true
    auto_migrate: true
    migrations_table: "_migrations"
    
  # Query settings
  query:
    max_query_length: 10000
    max_parameters: 1000
    query_timeout_seconds: 30
    use_prepared_statements: true
    enable_query_logging: false
    explain_query_threshold_ms: 100
    
  # Transaction settings
  transaction:
    isolation_level: "READ COMMITTED"  # Options: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE
    auto_commit: false
    
  # Performance settings
  performance:
    use_batch_inserts: true
    max_batch_size: 1000
    use_upsert: true
    enable_statement_cache: true
    statement_cache_size: 100
    
  # PostgreSQL specific settings
  postgresql:
    enable_ssl: false
    application_name: "neuroca_memory"
    statement_timeout_ms: 30000
    use_advisory_locks: true
    enable_unaccent: true
    enable_pg_trgm: true
    
  # MySQL specific settings
  mysql:
    charset: "utf8mb4"
    collation: "utf8mb4_unicode_ci"
    enable_local_infile: false
    sql_mode: "STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"
```

### Vector Backend

Configuration file: `vector_config.yaml`

```yaml
vector:
  # Storage settings
  storage:
    type: "memory"  # Options: memory, file, hybrid
    file_path: "data/vector_store.bin"
    auto_save: true
    save_interval_seconds: 300  # 5 minutes
    
  # Vector settings
  vector:
    dimension: 1536  # Default embedding dimension
    distance_metric: "cosine"  # Options: cosine, l2, dot, jaccard, hamming
    normalize_vectors: true
    
  # Index settings
  index:
    type: "hnsw"  # Options: hnsw, flat, ivf_flat, pq, ivf_pq, ivf_sq
    creation_threshold: 1000  # Create index after this many vectors
    build_on_creation: true
    use_gpu: false
    
  # HNSW index settings
  hnsw_index:
    ef_construction: 200
    ef_search: 50
    m: 16  # Number of connections per layer
    max_elements: 1000000
    
  # IVF index settings
  ivf_index:
    nlist: 100  # Number of clusters
    nprobe: 10  # Number of clusters to search
    
  # PQ index settings
  pq_index:
    code_size: 8  # Number of bytes per vector
    nbits: 8  # Number of bits per component
    
  # Search settings
  search:
    default_top_k: 10
    max_top_k: 1000
    pre_filter_enabled: true
    post_filter_enabled: true
    min_score_threshold: 0.5
    max_search_time_ms: 50
    
  # Clustering settings
  clustering:
    enabled: false
    algorithm: "kmeans"  # Options: kmeans, dbscan, hdbscan
    min_cluster_size: 5
    max_clusters: 100
    
  # Metadata filtering
  metadata:
    enable_filtering: true
    metadata_fields:
      - "source"
      - "timestamp"
      - "importance"
      - "tags"
    
  # Performance settings
  performance:
    use_multithreading: true
    num_threads: 4
    batch_size: 100
    cache_size_mb: 128
```

## Configuration Loading API

The memory system provides a configuration loading API to access configuration values from code. This API is defined in the `neuroca.memory.config.loader` module.

### Loading Configuration Files

To load configuration for a specific backend:

```python
from neuroca.memory.config.loader import get_backend_config

# Load configuration for the in-memory backend
config = get_backend_config("in_memory")

# Access configuration values
cache_enabled = config["common"]["cache"]["enabled"]
initial_capacity = config["in_memory"]["memory"]["initial_capacity"]
```

### Accessing Configuration Values

To access individual configuration values:

```python
from neuroca.memory.config.loader import get_config_value

# Get a specific configuration value for a backend
cache_enabled = get_config_value("common.cache.enabled", "in_memory")

# Get a value with a default if not found
ttl = get_config_value("common.cache.ttl_seconds", "in_memory", default=300)
```

### Custom Configuration Loader

For more control over configuration loading, you can create a `ConfigurationLoader` instance:

```python
from neuroca.memory.config.loader import ConfigurationLoader

# Create a loader with a custom configuration directory
loader = ConfigurationLoader("/path/to/config/dir")

# Load configuration for a specific backend
config = loader.load_config("in_memory")

# Access values using dot notation
cache_enabled = loader.get_value("common.cache.enabled")
```

## Backend Configuration in Factory

Backend instances are created using the `StorageBackendFactory`, which automatically loads the appropriate configuration for each backend type:

```python
from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory

# Create an in-memory backend with default configuration
backend = StorageBackendFactory.create_backend(BackendType.MEMORY)

# Create a SQLite backend with default configuration
sqlite_backend = StorageBackendFactory.create_backend(BackendType.SQLITE)
```

## Environment-Specific Configuration

To use different configurations for different environments (development, testing, production), place environment-specific configuration files in separate directories and specify the directory when creating the `ConfigurationLoader` instance:

```python
from neuroca.memory.config.loader import ConfigurationLoader

# Development environment
dev_loader = ConfigurationLoader("config/dev/backends")
dev_config = dev_loader.load_config("in_memory")

# Production environment
prod_loader = ConfigurationLoader("config/prod/backends")
prod_config = prod_loader.load_config("in_memory")
```

## Configuration Best Practices

1. **Keep Configuration Separate**: Avoid hardcoding configuration values in code. Use the configuration system instead.
2. **Use Reasonable Defaults**: Set reasonable default values for all configuration options.
3. **Document Configuration Options**: Document all configuration options and their allowed values.
4. **Use Environment Variables**: For sensitive configuration values (e.g., database passwords), use environment variables.
5. **Validate Configuration**: Validate configuration values at startup to catch errors early.
6. **Use Different Configurations for Different Environments**: Use different configuration files for development, testing, and production environments.

## Memory Tier Configuration

Each memory tier can use a different backend type with a specific configuration:

```python
from neuroca.memory.backends.factory.backend_type import BackendType
from neuroca.memory.backends.factory.memory_tier import MemoryTier
from neuroca.memory.backends.factory.storage_factory import StorageBackendFactory

# Short-term memory using in-memory backend
stm_backend = StorageBackendFactory.create_storage(MemoryTier.STM, BackendType.MEMORY)

# Medium-term memory using SQLite backend
mtm_backend = StorageBackendFactory.create_storage(MemoryTier.MTM, BackendType.SQLITE)

# Long-term memory using vector backend
ltm_backend = StorageBackendFactory.create_storage(MemoryTier.LTM, BackendType.VECTOR)
```

Each tier can have tier-specific configuration options by adding a tier-specific section to the configuration file:

```yaml
# Example: in_memory_config.yaml with tier-specific settings
in_memory:
  # General settings...
  
  # STM-specific settings
  stm:
    max_items: 200
    
  # MTM-specific settings
  mtm:
    max_items: 5000
```

These tier-specific settings can be accessed using the configuration API:

```python
from neuroca.memory.config.loader import get_config_value

# Get STM-specific setting
stm_max_items = get_config_value("in_memory.stm.max_items", "in_memory")
```

## Conclusion

The backend configuration system provides a flexible and centralized way to manage configuration options for memory backends. By separating configuration from code, it allows for easy adjustment of backend behavior without code changes.
