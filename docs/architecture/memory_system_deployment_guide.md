# Memory System Deployment Guide

**Last Updated:** April 14, 2025  
**Status:** Complete

This document provides comprehensive guidance for deploying the Neuroca memory system in various environments. It covers initial setup, configuration, performance tuning, and maintenance procedures.

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
   - [Development Environment](#development-environment)
   - [Testing Environment](#testing-environment)
   - [Production Environment](#production-environment)
4. [Backend-Specific Deployment](#backend-specific-deployment)
   - [In-Memory Backend](#in-memory-backend)
   - [SQLite Backend](#sqlite-backend)
   - [Redis Backend](#redis-backend)
   - [SQL Backend](#sql-backend)
   - [Vector Backend](#vector-backend)
5. [Configuration Management](#configuration-management)
6. [Performance Tuning](#performance-tuning)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)
10. [Upgrading and Migration](#upgrading-and-migration)

## Introduction

The Neuroca memory system is a modular, tiered memory architecture designed for cognitive AI applications. It consists of multiple memory tiers (STM, MTM, LTM) that can be configured to use different storage backends. This guide provides instructions for deploying and maintaining the memory system in various environments.

## Prerequisites

Before deploying the memory system, ensure you have the following:

- Python 3.10 or higher
- Pip package manager
- Git for version control
- Docker and Docker Compose (optional, for containerized deployment)
- Access to required backend services (Redis, PostgreSQL, etc., if applicable)
- Sufficient system resources (memory, disk space, CPU) based on expected load

## Environment Setup

### Development Environment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/organization/neuroca.git
   cd neuroca
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up configuration:**

   ```bash
   mkdir -p config/dev/backends
   cp config/backends/*.yaml config/dev/backends/
   ```

5. **Modify development configuration files as needed:**

   Edit files in `config/dev/backends/` to adjust settings for development.

6. **Set environment variables:**

   ```bash
   export NEUROCA_ENV=development
   export NEUROCA_CONFIG_DIR=config/dev/backends
   ```

7. **Run tests to verify setup:**

   ```bash
   pytest tests/unit/memory
   ```

### Testing Environment

1. **Set up a clean test environment:**

   ```bash
   mkdir -p config/test/backends
   cp config/backends/*.yaml config/test/backends/
   ```

2. **Modify test configuration files:**

   Edit files in `config/test/backends/` to use appropriate test settings:
   - Use in-memory databases where possible
   - Use isolated test instances for persistent backends
   - Configure shorter timeouts and smaller cache sizes

3. **Set up CI/CD configuration:**

   Create a `.github/workflows/memory-tests.yml` file (if using GitHub Actions) with:

   ```yaml
   name: Memory System Tests
   
   on:
     push:
       branches: [ main, develop ]
       paths:
         - 'src/neuroca/memory/**'
         - 'tests/unit/memory/**'
         - 'tests/integration/memory/**'
     pull_request:
       branches: [ main, develop ]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       services:
         redis:
           image: redis:7
           ports:
             - 6379:6379
         postgres:
           image: postgres:15
           env:
             POSTGRES_USER: test
             POSTGRES_PASSWORD: test
             POSTGRES_DB: test
           ports:
             - 5432:5432
       
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -e ".[dev]"
         - name: Run tests
           env:
             NEUROCA_ENV: testing
             NEUROCA_CONFIG_DIR: config/test/backends
           run: |
             pytest tests/unit/memory tests/integration/memory
   ```

4. **Run integration tests:**

   ```bash
   export NEUROCA_ENV=testing
   export NEUROCA_CONFIG_DIR=config/test/backends
   pytest tests/integration/memory
   ```

### Production Environment

1. **Prepare configuration files:**

   ```bash
   mkdir -p config/prod/backends
   cp config/backends/*.yaml config/prod/backends/
   ```

2. **Modify production configuration files:**

   Edit files in `config/prod/backends/` to optimize for production:
   - Increase cache sizes
   - Optimize performance settings
   - Configure proper connection pooling
   - Set up logging level to WARNING/ERROR
   - Configure security settings

3. **Set up environment variables:**

   ```bash
   export NEUROCA_ENV=production
   export NEUROCA_CONFIG_DIR=/path/to/config/prod/backends
   ```

4. **Use a process manager:**

   For production deployments, use a process manager like systemd, Supervisor, or PM2.

   Example systemd service file (`/etc/systemd/system/neuroca.service`):

   ```ini
   [Unit]
   Description=Neuroca AI Service
   After=network.target

   [Service]
   User=neuroca
   Group=neuroca
   WorkingDirectory=/path/to/neuroca
   Environment="NEUROCA_ENV=production"
   Environment="NEUROCA_CONFIG_DIR=/path/to/config/prod/backends"
   ExecStart=/path/to/neuroca/venv/bin/python -m neuroca.server
   Restart=on-failure
   RestartSec=5s

   [Install]
   WantedBy=multi-user.target
   ```

5. **Enable and start the service:**

   ```bash
   sudo systemctl enable neuroca
   sudo systemctl start neuroca
   ```

## Backend-Specific Deployment

### In-Memory Backend

The in-memory backend is the simplest to deploy but has limitations in terms of persistence and scale.

1. **Configuration:**

   Modify `in_memory_config.yaml` to set appropriate limits:

   ```yaml
   in_memory:
     memory:
       initial_capacity: 10000  # Start with enough capacity
       auto_expand: true
       max_capacity: 1000000  # Set based on available system memory
     
     persistence:
       enabled: true  # Enable persistence for production
       file_path: "/path/to/data/memory_dump.json"
       auto_save_interval_seconds: 300
       save_on_shutdown: true
   ```

2. **System Requirements:**

   - Ensure sufficient RAM for both the application and the memory backend
   - Configure swap space as a backup
   - Monitor memory usage to prevent OOM errors

3. **Scaling Considerations:**

   - The in-memory backend runs in the application process and doesn't support clustering
   - For higher loads, consider using Redis or SQL backends
   - Shard memory by implementing multiple backend instances for different data types

### SQLite Backend

SQLite is a lightweight, file-based database suitable for smaller deployments.

1. **Configuration:**

   Modify `sqlite_config.yaml` to optimize for your environment:

   ```yaml
   sqlite:
     connection:
       database_path: "/path/to/data/memory_store.db"
       create_if_missing: true
     
     performance:
       journal_mode: "WAL"  # Write-Ahead Logging for better concurrency
       synchronous: "NORMAL"  # Balance between safety and performance
       cache_size: 10000  # Adjust based on available memory
   ```

2. **System Requirements:**

   - Fast SSD storage for database file
   - Regular filesystem backups
   - File permissions allowing application read/write access

3. **Deployment Steps:**

   ```bash
   # Create data directory
   mkdir -p /path/to/data
   
   # Set permissions
   chown -R neuroca:neuroca /path/to/data
   chmod 750 /path/to/data
   
   # Initialize database (if needed)
   python -m neuroca.memory.tools.init_sqlite_db
   ```

4. **Scaling Considerations:**

   - SQLite supports concurrent reads but not concurrent writes
   - For higher concurrency, consider using PostgreSQL or MySQL
   - Monitor file size and implement pruning/archiving for large datasets

### Redis Backend

Redis provides in-memory storage with persistence and cluster support, suitable for medium to large deployments.

1. **Installation:**

   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install redis-server
   
   # Configure Redis
   sudo nano /etc/redis/redis.conf
   
   # Enable Redis to start at boot
   sudo systemctl enable redis-server
   ```

2. **Configuration:**

   Modify `redis_config.yaml`:

   ```yaml
   redis:
     connection:
       host: "redis.example.com"  # Use hostname or IP
       port: 6379
       database: 0
       password: "your_redis_password"  # Ensure Redis is password-protected
       use_ssl: true  # Enable for production
     
     performance:
       use_connection_pool: true
       max_connections: 20  # Adjust based on concurrency needs
   ```

3. **Redis Server Configuration (`redis.conf`):**

   ```
   # Memory management
   maxmemory 4gb
   maxmemory-policy allkeys-lru
   
   # Persistence
   appendonly yes
   appendfsync everysec
   
   # Network
   bind 127.0.0.1  # Restrict to localhost or internal network
   protected-mode yes
   requirepass your_redis_password
   
   # Performance
   tcp-keepalive 300
   ```

4. **Security Considerations:**

   - Never expose Redis directly to the internet
   - Use strong passwords
   - Consider Redis auth
   - Use SSL/TLS for encryption
   - Configure proper firewalls

5. **Scaling Options:**

   - Redis Cluster for horizontal scaling
   - Redis Sentinel for high availability
   - Redis Enterprise for managed solutions

### SQL Backend

SQL backends (PostgreSQL, MySQL) provide robust storage with advanced query capabilities, suitable for large-scale deployments.

1. **PostgreSQL Installation:**

   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   
   # Create database and user
   sudo -u postgres psql
   postgres=# CREATE USER neuroca WITH PASSWORD 'your_password';
   postgres=# CREATE DATABASE neuroca_memory;
   postgres=# GRANT ALL PRIVILEGES ON DATABASE neuroca_memory TO neuroca;
   ```

2. **Configuration:**

   Modify `sql_config.yaml`:

   ```yaml
   sql:
     connection:
       driver: "postgresql"
       host: "db.example.com"
       port: 5432
       database: "neuroca_memory"
       username: "neuroca"
       password: "your_password"
     
     pool:
       min_connections: 5
       max_connections: 20
     
     performance:
       use_batch_inserts: true
       max_batch_size: 1000
   ```

3. **PostgreSQL Configuration (`postgresql.conf`):**

   ```
   # Memory configuration
   shared_buffers = 1GB
   work_mem = 32MB
   maintenance_work_mem = 256MB
   
   # Write-ahead log
   wal_level = replica
   
   # Query optimization
   effective_cache_size = 3GB
   random_page_cost = 1.1  # For SSD storage
   
   # Concurrency
   max_connections = 100
   ```

4. **Database Migration:**

   ```bash
   # Run migrations 
   python -m neuroca.memory.tools.run_migrations
   ```

5. **Scaling Options:**

   - Connection pooling with PgBouncer
   - Read replicas for query scaling
   - Table partitioning for large datasets
   - PostgreSQL clustering with tools like Patroni

### Vector Backend

The vector backend is optimized for semantic search and similarity queries, essential for LTM memory implementation.

1. **Configuration:**

   Modify `vector_config.yaml`:

   ```yaml
   vector:
     storage:
       type: "hybrid"  # Use hybrid for both in-memory and file-based
       file_path: "/path/to/data/vector_store.bin"
     
     vector:
       dimension: 1536  # Match your embedding model
       distance_metric: "cosine"
     
     index:
       type: "hnsw"  # Hierarchical Navigable Small World graphs
       use_gpu: false  # Set to true if GPU is available
     
     performance:
       use_multithreading: true
       num_threads: 4  # Adjust based on CPU cores
   ```

2. **System Requirements:**

   - Sufficient RAM for vector index (depends on vector count and dimensions)
   - Fast CPU for vector operations
   - GPU support is optional but recommended for large indexes
   - SSD storage for vector persistence

3. **GPU Acceleration (Optional):**

   Install GPU support packages:

   ```bash
   pip install faiss-gpu
   ```

   Modify configuration to use GPU:

   ```yaml
   vector:
     index:
       use_gpu: true
       gpu_id: 0  # Use specific GPU if multiple are available
   ```

4. **Scaling Considerations:**

   - Vector search is CPU/GPU intensive
   - Consider load distribution for large vector databases
   - Implement parallel processing for batch operations
   - Use vector compression for large collections

## Configuration Management

For effective configuration management across environments:

1. **Use Environment Variables for Sensitive Data:**

   ```bash
   export NEUROCA_REDIS_PASSWORD="your_secure_password"
   export NEUROCA_DB_PASSWORD="your_database_password"
   ```

   In configuration files, use placeholder values:

   ```yaml
   redis:
     connection:
       password: "${NEUROCA_REDIS_PASSWORD}"
   ```

2. **Version Control for Configuration:**

   - Store template configurations in version control
   - Use `.gitignore` to exclude environment-specific configurations
   - Document required configuration variables

3. **Configuration Validation:**

   ```bash
   # Validate configuration
   python -m neuroca.memory.tools.validate_config config/prod/backends/
   ```

4. **Dynamic Configuration Reloading:**

   Implement a configuration watcher for runtime updates:

   ```bash
   # Check for configuration changes
   python -m neuroca.memory.tools.config_watcher
   ```

## Performance Tuning

For optimal memory system performance:

1. **Memory Tier Allocation:**

   - STM: Use in-memory backend for fastest access
   - MTM: Use Redis or SQLite for balance of speed and persistence
   - LTM: Use Vector backend for semantic search capabilities

2. **Cache Configuration:**

   Adjust cache sizes based on available system memory:

   ```yaml
   common:
     cache:
       max_size: 10000  # Increase for production
   ```

3. **Batch Operations:**

   Use batch operations for bulk data processing:

   ```yaml
   common:
     batch:
       max_batch_size: 1000  # Increase for better throughput
   ```

4. **Connection Pooling:**

   For database backends, configure connection pools:

   ```yaml
   pool:
     min_connections: 5
     max_connections: 20
   ```

5. **Indexing Strategy:**

   Optimize index types for query patterns:

   ```yaml
   index:
     type: "hnsw"  # For vector search
     ef_search: 100  # Higher for better recall, lower for speed
   ```

6. **Memory Pruning:**

   Configure automatic pruning to manage memory growth:

   ```yaml
   pruning:
     enabled: true
     max_items: 10000
     strategy: "importance"  # Prune by importance/relevance
   ```

7. **Performance Monitoring:**

   ```bash
   # Run performance benchmarks
   python -m neuroca.memory.performance.benchmark
   ```

## Monitoring and Maintenance

1. **Health Checks:**

   ```bash
   # Check memory system health
   python -m neuroca.memory.tools.health_check
   ```

2. **Metrics Collection:**

   ```yaml
   common:
     metrics:
       enabled: true
       collection_interval_seconds: 60
       export_prometheus: true
   ```

3. **Log Rotation:**

   Configure log rotation to manage log growth:

   ```
   /var/log/neuroca/*.log {
       daily
       missingok
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 neuroca neuroca
   }
   ```

4. **Regular Maintenance:**

   Schedule routine maintenance tasks:

   ```bash
   # Add to crontab
   0 2 * * * /path/to/neuroca/scripts/memory_maintenance.sh
   ```

5. **Database Vacuuming (PostgreSQL):**

   ```sql
   -- Run regularly
   VACUUM ANALYZE;
   ```

## Backup and Recovery

1. **Backup Strategy:**

   ```bash
   # Backup script
   #!/bin/bash
   
   # Stop service or put in maintenance mode
   systemctl stop neuroca
   
   # Backup configuration
   cp -r /path/to/config/prod /path/to/backup/config-$(date +%Y%m%d)
   
   # Backup data
   cp -r /path/to/data /path/to/backup/data-$(date +%Y%m%d)
   
   # For SQL backend, perform database dump
   pg_dump -U neuroca neuroca_memory > /path/to/backup/memory-$(date +%Y%m%d).sql
   
   # Restart service
   systemctl start neuroca
   ```

2. **Recovery Procedure:**

   ```bash
   # Recovery script
   #!/bin/bash
   
   # Stop service
   systemctl stop neuroca
   
   # Restore configuration
   cp -r /path/to/backup/config-20250414 /path/to/config/prod
   
   # Restore data
   cp -r /path/to/backup/data-20250414 /path/to/data
   
   # For SQL backend, restore database
   psql -U neuroca neuroca_memory < /path/to/backup/memory-20250414.sql
   
   # Restart service
   systemctl start neuroca
   ```

3. **Disaster Recovery Testing:**

   Regularly test recovery procedures to ensure they work as expected.

## Troubleshooting

Common issues and solutions:

1. **Connection Failures:**

   - Check network connectivity
   - Verify credentials and connection parameters
   - Check firewall rules
   - Inspect service logs

2. **Performance Degradation:**

   - Check system resources (CPU, memory, disk)
   - Review backend-specific metrics
   - Analyze query patterns
   - Check for index fragmentation

3. **Memory Leaks:**

   - Monitor memory usage over time
   - Check for growing cache sizes
   - Verify proper resource cleanup
   - Implement memory profiling

4. **Data Consistency Issues:**

   - Verify transaction settings
   - Check for concurrent write conflicts
   - Review error logs
   - Implement data validation

5. **Logging:**

   Enable detailed logging for troubleshooting:

   ```yaml
   common:
     logging:
       level: "DEBUG"
       log_queries: true
   ```

6. **Diagnostic Tools:**

   ```bash
   # Check backend status
   python -m neuroca.memory.tools.diagnostic --backend in_memory
   
   # Run consistency check
   python -m neuroca.memory.tools.verify_consistency
   ```

## Upgrading and Migration

1. **Version Compatibility:**

   - Review release notes for breaking changes
   - Check configuration format changes
   - Verify backend compatibility

2. **Upgrade Procedure:**

   ```bash
   # Backup first
   ./backup_memory_system.sh
   
   # Stop service
   systemctl stop neuroca
   
   # Update code
   git pull origin main
   
   # Install dependencies
   pip install -e ".[prod]"
   
   # Run migrations
   python -m neuroca.memory.tools.run_migrations
   
   # Start service
   systemctl start neuroca
   ```

3. **Rollback Plan:**

   ```bash
   # If upgrade fails, rollback
   git checkout v1.2.3  # Previous stable version
   
   # Restore from backup
   ./restore_memory_system.sh 20250414
   
   # Start service
   systemctl start neuroca
   ```

4. **Backend Migration:**

   For migrating between backend types:

   ```bash
   # Export data from source backend
   python -m neuroca.memory.tools.export --backend sqlite --output memory_data.json
   
   # Import data to target backend
   python -m neuroca.memory.tools.import --backend redis --input memory_data.json
   ```

5. **Data Format Migration:**

   For handling data format changes:

   ```bash
   # Transform data format
   python -m neuroca.memory.tools.transform --input old_format.json --output new_format.json
   ```

---

This deployment guide covers the essential aspects of deploying and maintaining the Neuroca memory system. For detailed information about specific backend configurations, refer to the [Memory System Backend Configuration](memory_system_backend_configuration.md) document.
