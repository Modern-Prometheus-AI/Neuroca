# NeuroCognitive Architecture (NCA) Incident Response Runbook

This runbook provides a structured approach for responding to incidents that may occur in the NCA production environment. It outlines the steps for identifying, responding to, and resolving incidents while minimizing impact on users.

## Incident Severity Levels

Incidents are classified by severity level to determine appropriate response procedures:

| Level | Description | Examples | Response Time | Escalation |
|-------|-------------|----------|--------------|------------|
| P1 | Critical service outage | - API completely down<br>- Data loss<br>- Security breach | Immediate | Leadership + On-call team |
| P2 | Partial service disruption | - High latency<br>- Feature failure<br>- Degraded performance | < 30 minutes | On-call team |
| P3 | Minor service impact | - Non-critical bugs<br>- Isolated errors<br>- Minor performance issues | < 4 hours | Primary on-call |
| P4 | No user impact | - Warning signs<br>- Potential future issues | Next business day | Team aware |

## Incident Response Workflow

### 1. Detection

* **Automated Detection**
  * System health alerts from Prometheus
  * Latency spikes detected by ServiceMonitor
  * Error rate increases in logs
  * Memory/CPU utilization alerts

* **Manual Detection**
  * User-reported issues
  * Regular system health checks
  * Deployment observations

### 2. Assessment & Classification

When an incident is detected:

1. **Determine the scope**
   * Which components are affected?
   * Is it impacting users?
   * Is it affecting all users or only specific segments?

2. **Classify severity** based on the level definitions above

3. **Initial documentation** in the incident management system
   * Incident ID
   * Severity level
   * Brief description
   * Affected components
   * Detection method
   * Initial responder(s)

### 3. Response

#### For P1 (Critical) Incidents:

1. **Activate incident management**
   * Notify on-call team via PagerDuty
   * Create incident channel in Slack
   * Designate Incident Commander (IC)

2. **Immediate mitigation**
   * Consider emergency rollback to last known good version
   * Implement circuit breakers if applicable
   * Scale up resources if resource-related

3. **Client communication**
   * Post to status page
   * Send initial notification to affected clients
   * Establish communication cadence

#### For P2 (Major) Incidents:

1. **Notify on-call team**
   * Primary responder to lead
   * Escalate if necessary

2. **Implement mitigation**
   * Apply fixes from playbooks if available
   * Isolate affected components if possible

3. **Client communication**
   * Update status page if user-visible
   * Prepare client communication

#### For P3/P4 (Minor) Incidents:

1. **Assign to primary on-call or team**
2. **Implement mitigation during business hours**
3. **Document in tracking system**

### 4. Investigation

1. **Gather diagnostic information**
   ```bash
   # Get pod logs
   kubectl logs -n neuroca -l app=neuroca --tail=500
   
   # Check pod status
   kubectl get pods -n neuroca
   
   # Check memory usage
   kubectl top pod -n neuroca
   
   # Watch metrics
   kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
   ```

2. **Examine logs and traces**
   * Check application logs
   * Review Prometheus metrics
   * Analyze request traces in Jaeger

3. **Perform root cause analysis**
   * Memory leak checks
   * API throttling issues
   * Database connection problems
   * External dependency failures
   * Changes or deployments

### 5. Resolution

1. **Implement permanent fix**
   * Deploy hotfix if needed
   * Validate fix in production
   * Verify monitoring confirms resolution

2. **Document resolution**
   * Update incident report
   * Note fixed version
   * Document workarounds used

3. **Client communication**
   * Notify of resolution
   * Update status page
   * Provide explanation if appropriate

### 6. Post-incident Follow-up

1. **Conduct post-mortem**
   * Schedule within 24-48 hours of resolution
   * Include all participants
   * Document timeline
   * Identify root causes
   * No blame approach

2. **Generate action items**
   * Preventative measures
   * Detection improvements
   * Response enhancements
   * Documentation updates

3. **Knowledge sharing**
   * Update runbooks with new findings
   * Share lessons learned with team
   * Improve monitoring if gaps identified

## Common Incident Scenarios

### API Latency Spike

1. **Check CPU/Memory usage**
   ```bash
   kubectl top pods -n neuroca
   ```

2. **Check database connection pool**
   * Query the database metrics
   * Look for connection limits

3. **Check external API dependencies**
   * Review Redis, OpenAI, etc.

4. **Examine recent deployments**
   * Any recent code changes?
   * New dependencies?

5. **Actions**
   * Scale horizontally if resource-bound
   * Increase connection pool if DB-related
   * Implement circuit breakers if dependency issues

### Memory Leak

1. **Verify with increasing memory trend**
   * Check Prometheus graphs for memory growth pattern

2. **Collect heap dumps**
   ```bash
   # Get pod name
   POD=$(kubectl get pod -n neuroca -l app=neuroca -o jsonpath='{.items[0].metadata.name}')
   
   # Execute heap dump
   kubectl exec -n neuroca $POD -- python -m memory_profiler dump_mem.py > heap.dump
   ```

3. **Analyze memory usage**
   * Look for large object allocations
   * Check for unbounded caches

4. **Actions**
   * Rolling restart if immediate mitigation needed
   * Deploy fix addressing memory leak
   * Add memory bounds to caches

### Database Performance Issues

1. **Check query performance**
   ```sql
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;
   ```

2. **Examine index usage**

3. **Check connection pool**
   * Look for maxed out connections
   * Connection leaks

4. **Actions**
   * Add needed indexes
   * Optimize slow queries
   * Increase connection timeouts if needed

## Emergency Contacts

| Role | Primary | Secondary | Contact Method |
|------|---------|-----------|----------------|
| Database Admin | [NAME] | [NAME] | Slack @dbadmin, Phone |
| Infrastructure Lead | [NAME] | [NAME] | Slack @infrateam, Phone |
| Security Officer | [NAME] | [NAME] | Slack @security, Phone |
| Engineering Lead | [NAME] | [NAME] | Slack @eng-lead, Phone |

## Rollback Procedure

If a deployment needs to be rolled back:

```bash
# Check deployment history
kubectl rollout history deployment/neuroca -n neuroca

# Roll back to previous version
kubectl rollout undo deployment/neuroca -n neuroca

# Roll back to specific version
kubectl rollout undo deployment/neuroca -n neuroca --to-revision=<revision_number>

# Monitor rollback
kubectl rollout status deployment/neuroca -n neuroca
```

## Helpful Commands

### Kubernetes

```bash
# Get pod logs
kubectl logs -n neuroca <pod-name>

# Get pod logs for all containers in a pod
kubectl logs -n neuroca <pod-name> --all-containers

# Describe pod for detailed information
kubectl describe pod -n neuroca <pod-name>

# Get events
kubectl get events -n neuroca --sort-by='.lastTimestamp'

# Exec into container
kubectl exec -it -n neuroca <pod-name> -- /bin/bash

# Port forward to service
kubectl port-forward -n neuroca svc/neuroca 8000:80
```

### Monitoring

```bash
# Check Prometheus alerts
curl -s http://prometheus:9090/api/v1/alerts | jq

# Check service health
curl -s http://neuroca-service/health/readiness

# Get recent logs
kubectl logs -n neuroca -l app=neuroca --tail=100
```

### Database

```bash
# Connect to database
kubectl exec -it -n neuroca <postgres-pod> -- psql -U postgres -d neuroca

# Check connection count
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

# Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

## Regular Drills

Schedule regular incident response drills to ensure the team is prepared:

1. **Quarterly Gameday exercises**
   * Simulate P1 incidents
   * Practice coordination
   * Test communication channels

2. **Monthly Runbook reviews**
   * Update with new information
   * Add newly discovered issues
   * Remove obsolete information

3. **On-call readiness check**
   * Verify access to all systems
   * Review escalation procedures
   * Update contact information
