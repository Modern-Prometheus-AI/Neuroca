# NeuroCognitive Architecture (NCA) Scaling Runbook

## Overview

This runbook provides comprehensive guidance for scaling the NeuroCognitive Architecture (NCA) system in production environments. It covers horizontal and vertical scaling strategies, capacity planning, performance monitoring, and troubleshooting procedures to ensure the system maintains optimal performance under varying loads.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Scaling Indicators](#scaling-indicators)
3. [Horizontal Scaling Procedures](#horizontal-scaling-procedures)
4. [Vertical Scaling Procedures](#vertical-scaling-procedures)
5. [Memory Tier Scaling](#memory-tier-scaling)
6. [Database Scaling](#database-scaling)
7. [Load Balancing Configuration](#load-balancing-configuration)
8. [Auto-scaling Setup](#auto-scaling-setup)
9. [Capacity Planning](#capacity-planning)
10. [Performance Monitoring](#performance-monitoring)
11. [Troubleshooting](#troubleshooting)
12. [Rollback Procedures](#rollback-procedures)

## System Architecture Overview

The NCA system consists of several key components that may require scaling:

- **API Layer**: Handles external requests and orchestrates system operations
- **Memory Tiers**: Working, episodic, and semantic memory systems
- **LLM Integration Layer**: Manages communication with external LLM services
- **Database Layer**: Stores persistent data across the system
- **Processing Nodes**: Handles cognitive processing tasks

Each component can be scaled independently based on specific performance requirements.

## Scaling Indicators

Monitor the following metrics to determine when scaling is necessary:

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|-------------------|-------------------|--------|
| CPU Utilization | >70% for 15 minutes | >85% for 5 minutes | Scale processing nodes |
| Memory Usage | >75% for 15 minutes | >90% for 5 minutes | Scale memory or add nodes |
| Request Latency | >500ms average | >1s average | Scale API layer |
| Queue Depth | >1000 items | >5000 items | Scale processing nodes |
| Database Connections | >80% of max | >90% of max | Scale database |
| Error Rate | >1% of requests | >5% of requests | Investigate and scale affected component |

## Horizontal Scaling Procedures

### API Layer Scaling

1. **Prerequisites**:
   - Ensure load balancer is properly configured
   - Verify health check endpoints are operational

2. **Procedure**:
   ```bash
   # Scale API nodes using Kubernetes
   kubectl scale deployment nca-api --replicas=<new_count> -n neuroca
   
   # Alternatively, using Docker Swarm
   docker service scale neuroca_api=<new_count>
   ```

3. **Verification**:
   - Monitor request distribution across new nodes
   - Verify latency improvements
   - Check error rates for any deployment issues

### Processing Node Scaling

1. **Prerequisites**:
   - Ensure sufficient cluster resources
   - Verify node configuration is current

2. **Procedure**:
   ```bash
   # Scale processing nodes using Kubernetes
   kubectl scale deployment nca-processing --replicas=<new_count> -n neuroca
   
   # Update processing capacity in configuration
   kubectl apply -f updated-processing-config.yaml
   ```

3. **Post-scaling Tasks**:
   - Adjust load balancing weights if necessary
   - Update monitoring thresholds
   - Document new capacity in system inventory

## Vertical Scaling Procedures

### Resource Allocation Increase

1. **Prerequisites**:
   - Schedule maintenance window if service disruption is expected
   - Create backup of current configuration

2. **Procedure for Kubernetes**:
   ```bash
   # Update resource requests and limits
   kubectl edit deployment <component-name> -n neuroca
   
   # Verify changes
   kubectl describe deployment <component-name> -n neuroca
   ```

3. **Procedure for VM-based Deployments**:
   - Stop the service: `systemctl stop neuroca-<component>`
   - Resize VM resources through cloud provider console
   - Start the service: `systemctl start neuroca-<component>`
   - Verify service health: `systemctl status neuroca-<component>`

4. **Verification**:
   - Monitor resource utilization for 15 minutes
   - Verify performance improvements
   - Check for any errors in logs

## Memory Tier Scaling

### Working Memory Scaling

1. **Indicators for Scaling**:
   - High cache miss rate (>10%)
   - Increased latency in cognitive operations
   - Memory pressure alerts

2. **Scaling Procedure**:
   ```bash
   # Update memory allocation
   kubectl edit deployment nca-working-memory -n neuroca
   
   # Apply memory configuration changes
   kubectl apply -f updated-memory-config.yaml
   ```

3. **Verification**:
   - Monitor cache hit rates
   - Verify memory usage patterns
   - Check cognitive operation latency

### Episodic and Semantic Memory Scaling

1. **Scaling Database Backend**:
   - Follow [Database Scaling](#database-scaling) procedures
   
2. **Scaling Memory Services**:
   ```bash
   # Scale memory services
   kubectl scale deployment nca-episodic-memory --replicas=<new_count> -n neuroca
   kubectl scale deployment nca-semantic-memory --replicas=<new_count> -n neuroca
   ```

3. **Update Memory Indexing**:
   - Adjust indexing parameters in configuration
   - Rebuild indexes if necessary

## Database Scaling

### Vertical Scaling

1. **Prerequisites**:
   - Schedule maintenance window
   - Create full database backup
   - Notify stakeholders of potential downtime

2. **Procedure**:
   - For managed databases (e.g., RDS, Cloud SQL):
     - Use provider console to resize instance
     - Monitor migration progress
   
   - For self-managed databases:
     ```bash
     # Stop database service
     systemctl stop postgresql
     
     # Resize VM/container resources
     # [Cloud-specific commands]
     
     # Start database service
     systemctl start postgresql
     ```

3. **Verification**:
   - Run database health checks
   - Verify application connectivity
   - Monitor query performance

### Horizontal Scaling (Sharding/Replication)

1. **Read Replicas Addition**:
   - Create read replica through provider console or:
   ```bash
   # Example for PostgreSQL
   pg_basebackup -h primary -D /var/lib/postgresql/data -U replication -P -v -R -X stream -C
   ```
   
   - Update application configuration to use connection pooling:
   ```yaml
   database:
     write_endpoint: "primary.db.neuroca.internal"
     read_endpoints:
       - "read1.db.neuroca.internal"
       - "read2.db.neuroca.internal"
     connection_pool_size: 50
   ```

2. **Database Sharding**:
   - Implement according to data access patterns
   - Update application configuration with shard map
   - Migrate data to new sharding scheme during maintenance window

## Load Balancing Configuration

1. **Update Load Balancer Configuration**:
   ```bash
   # Example for updating nginx load balancer
   kubectl apply -f updated-ingress.yaml
   
   # Example for cloud load balancer
   gcloud compute forwarding-rules update neuroca-lb --backend-service=neuroca-backend
   ```

2. **Configure Health Checks**:
   - Ensure health check endpoints reflect true service health
   - Set appropriate thresholds for removing unhealthy instances

3. **Adjust Session Affinity**:
   - Configure based on application requirements
   - Consider sticky sessions for stateful components

## Auto-scaling Setup

### Kubernetes HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nca-api-autoscaler
  namespace: neuroca
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nca-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
    scaleUp:
      stabilizationWindowSeconds: 60
```

### Cloud Provider Auto-scaling

For cloud-specific environments, configure auto-scaling groups:

- **AWS**:
  ```bash
  aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name nca-processing-asg \
    --min-size 3 \
    --max-size 10 \
    --desired-capacity 3 \
    --launch-template LaunchTemplateId=lt-0123456789abcdef0
  ```

- **GCP**:
  ```bash
  gcloud compute instance-groups managed set-autoscaling nca-processing-group \
    --max-num-replicas=10 \
    --min-num-replicas=3 \
    --target-cpu-utilization=0.7
  ```

## Capacity Planning

### Resource Estimation

Use the following formulas to estimate resource requirements:

- **CPU Cores** = (peak_requests_per_second × avg_processing_time_seconds) / target_utilization
- **Memory** = (concurrent_users × avg_memory_per_user) + base_system_memory
- **Storage** = (daily_data_growth × retention_period) × 1.5 (buffer)

### Growth Forecasting

1. Collect historical usage data for:
   - User growth rate
   - Request volume trends
   - Data storage growth
   
2. Project future requirements using:
   - Linear regression for steady growth
   - Exponential models for viral growth patterns
   
3. Plan capacity increases:
   - Schedule incremental scaling based on projections
   - Maintain 30% headroom for unexpected spikes

## Performance Monitoring

### Key Metrics to Monitor

1. **System-level Metrics**:
   - CPU, Memory, Disk I/O, Network I/O
   - Container/VM health status
   
2. **Application-level Metrics**:
   - Request latency (p50, p95, p99)
   - Error rates by endpoint
   - Queue depths
   - Cache hit/miss ratios
   
3. **Business Metrics**:
   - Active users
   - Cognitive operations completed
   - Memory retrieval success rates

### Monitoring Tools Configuration

1. **Prometheus Setup**:
   ```yaml
   # Example scrape configuration
   scrape_configs:
     - job_name: 'nca-api'
       kubernetes_sd_configs:
         - role: pod
       relabel_configs:
         - source_labels: [__meta_kubernetes_pod_label_app]
           regex: nca-api
           action: keep
   ```

2. **Grafana Dashboards**:
   - Import NCA dashboard templates from `/monitoring/dashboards/`
   - Set up alerts for scaling indicators

3. **Log Aggregation**:
   - Configure log shipping to centralized platform
   - Set up log-based alerts for error patterns

## Troubleshooting

### Common Scaling Issues

1. **Database Connection Exhaustion**
   - **Symptoms**: Connection timeouts, "too many connections" errors
   - **Resolution**:
     - Increase max_connections in database configuration
     - Implement connection pooling
     - Check for connection leaks in application code

2. **Memory Pressure After Scaling**
   - **Symptoms**: OOM errors, performance degradation
   - **Resolution**:
     - Check memory limits in container configuration
     - Analyze memory usage patterns with profiling tools
     - Consider implementing circuit breakers for high-memory operations

3. **Uneven Load Distribution**
   - **Symptoms**: Some nodes at high utilization while others idle
   - **Resolution**:
     - Check load balancer configuration
     - Verify health check endpoints are accurate
     - Implement consistent hashing for workload distribution

### Diagnostic Commands

```bash
# Check pod resource usage
kubectl top pods -n neuroca

# View detailed pod information
kubectl describe pod <pod-name> -n neuroca

# Check logs for errors
kubectl logs -f <pod-name> -n neuroca

# Database connection status
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Memory tier diagnostics
curl -X GET http://nca-api/internal/diagnostics/memory-tiers
```

## Rollback Procedures

If scaling operations cause system instability:

1. **Horizontal Scaling Rollback**:
   ```bash
   # Revert to previous replica count
   kubectl scale deployment <component-name> --replicas=<previous_count> -n neuroca
   ```

2. **Vertical Scaling Rollback**:
   - Reapply previous resource configuration
   - Restart affected services
   
3. **Database Scaling Rollback**:
   - For major issues, restore from pre-scaling backup
   - For connection issues, revert connection pool settings

4. **Monitoring After Rollback**:
   - Verify system stability for at least 30 minutes
   - Document issues encountered for future scaling attempts

---

## Document Information

- **Last Updated**: YYYY-MM-DD
- **Version**: 1.0
- **Authors**: NeuroCognitive Architecture Team
- **Review Cycle**: Quarterly or after major architecture changes

## Related Documents

- [Monitoring Runbook](./monitoring.md)
- [Disaster Recovery Procedures](./disaster_recovery.md)
- [Performance Tuning Guide](./performance_tuning.md)