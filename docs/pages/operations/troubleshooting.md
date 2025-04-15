# NeuroCognitive Architecture (NCA) Troubleshooting Guide

## Introduction

This document provides comprehensive troubleshooting procedures for the NeuroCognitive Architecture (NCA) system. It covers common issues, diagnostic approaches, and resolution steps for operators and developers working with the system in production environments.

## Table of Contents

1. [General Troubleshooting Approach](#general-troubleshooting-approach)
2. [System Health Checks](#system-health-checks)
3. [Memory System Issues](#memory-system-issues)
4. [LLM Integration Problems](#llm-integration-problems)
5. [Performance Degradation](#performance-degradation)
6. [API and Service Connectivity](#api-and-service-connectivity)
7. [Database Issues](#database-issues)
8. [Logging and Monitoring](#logging-and-monitoring)
9. [Common Error Codes](#common-error-codes)
10. [Recovery Procedures](#recovery-procedures)
11. [Getting Support](#getting-support)

## General Troubleshooting Approach

When encountering issues with the NCA system, follow this structured approach:

1. **Identify the problem scope**:
   - Is it affecting a single component or the entire system?
   - Is it intermittent or persistent?
   - When did it start occurring?

2. **Check system logs**:
   - Review application logs at `/var/log/neuroca/` or via `docker logs` if containerized
   - Check system logs for resource constraints or hardware issues

3. **Verify configuration**:
   - Ensure all configuration files are correctly set up
   - Validate environment variables against `.env.example`

4. **Check system resources**:
   - Monitor CPU, memory, disk usage, and network performance
   - Use `htop`, `iostat`, or the monitoring dashboard

5. **Isolate the issue**:
   - Test individual components to identify the failure point
   - Use the health check endpoints to verify component status

## System Health Checks

### Basic Health Verification

```bash
# Check overall system health
curl -X GET http://localhost:8000/api/v1/health

# Check specific component health
curl -X GET http://localhost:8000/api/v1/health/memory
curl -X GET http://localhost:8000/api/v1/health/llm
curl -X GET http://localhost:8000/api/v1/health/database
```

### Common Health Issues

| Issue | Possible Causes | Resolution |
|-------|----------------|------------|
| System unresponsive | Resource exhaustion, deadlock | Restart service, check logs for errors |
| High CPU usage | Inefficient processing, infinite loops | Check resource-intensive operations, review recent code changes |
| Memory leaks | Unclosed resources, accumulating objects | Restart affected services, review memory management in code |
| Disk space full | Logs accumulation, database growth | Clean logs, archive data, increase storage |

## Memory System Issues

### Working Memory Problems

**Symptoms**:
- Slow response times
- Inconsistent context retention
- Error: `MEMORY_WM_CAPACITY_EXCEEDED`

**Troubleshooting Steps**:
1. Check working memory configuration in `config/memory.yaml`
2. Verify memory capacity settings match hardware capabilities
3. Review memory utilization metrics in the monitoring dashboard
4. Check for memory leaks using memory profiling tools

**Resolution**:
```bash
# Reset working memory (caution: this clears current context)
curl -X POST http://localhost:8000/api/v1/memory/working/reset

# Adjust working memory capacity (temporary until restart)
curl -X PATCH http://localhost:8000/api/v1/config/memory/working -d '{"capacity": "2GB"}'
```

### Long-Term Memory Issues

**Symptoms**:
- Failed retrievals
- Slow query performance
- Error: `MEMORY_LTM_INDEX_CORRUPTION`

**Troubleshooting Steps**:
1. Verify vector database connectivity
2. Check index integrity
3. Review recent embedding operations
4. Validate storage capacity

**Resolution**:
```bash
# Rebuild memory indices (may take time)
python -m neuroca.cli.tools rebuild_indices

# Verify index integrity
python -m neuroca.cli.tools verify_indices
```

## LLM Integration Problems

### Connection Issues

**Symptoms**:
- Timeout errors
- Error: `LLM_CONNECTION_FAILED`
- Error: `API_KEY_INVALID`

**Troubleshooting Steps**:
1. Verify API keys in configuration
2. Check network connectivity to LLM provider
3. Validate rate limits and quotas
4. Review provider status page for outages

**Resolution**:
```bash
# Test LLM connectivity
python -m neuroca.cli.tools test_llm_connection

# Rotate API keys (if configured)
python -m neuroca.cli.tools rotate_api_keys
```

### Response Quality Issues

**Symptoms**:
- Degraded output quality
- Inconsistent responses
- Error: `LLM_RESPONSE_MALFORMED`

**Troubleshooting Steps**:
1. Check prompt templates for errors
2. Verify model parameters (temperature, top_p, etc.)
3. Review recent prompt changes
4. Test with baseline prompts

**Resolution**:
- Revert to known working prompt templates
- Adjust model parameters in configuration
- Consider switching to backup LLM provider

## Performance Degradation

### Slow Response Times

**Symptoms**:
- Increasing latency
- Timeouts
- Error: `REQUEST_TIMEOUT`

**Troubleshooting Steps**:
1. Check system resource utilization
2. Review database query performance
3. Monitor network latency
4. Analyze request patterns for bottlenecks

**Resolution**:
```bash
# Enable performance debugging mode
export NEUROCA_PERF_DEBUG=1
# Restart the service
systemctl restart neuroca

# Check slow queries
python -m neuroca.cli.tools analyze_performance --last=30m
```

### Resource Contention

**Symptoms**:
- CPU/Memory spikes
- Disk I/O bottlenecks
- Error: `RESOURCE_EXHAUSTION`

**Troubleshooting Steps**:
1. Identify resource-intensive operations
2. Check for concurrent heavy processes
3. Review scaling configuration
4. Monitor background tasks

**Resolution**:
- Scale horizontally if possible
- Adjust resource limits in configuration
- Implement request throttling
- Optimize heavy operations

## API and Service Connectivity

### API Errors

**Symptoms**:
- HTTP 5xx errors
- Connection refused errors
- Error: `SERVICE_UNAVAILABLE`

**Troubleshooting Steps**:
1. Check service status
2. Verify network configuration
3. Review API gateway logs
4. Test endpoint availability

**Resolution**:
```bash
# Check service status
systemctl status neuroca-api

# Restart API service
systemctl restart neuroca-api

# Verify endpoints
curl -v http://localhost:8000/api/v1/health
```

### Authentication Issues

**Symptoms**:
- HTTP 401/403 errors
- Error: `AUTHENTICATION_FAILED`
- Error: `TOKEN_EXPIRED`

**Troubleshooting Steps**:
1. Verify authentication configuration
2. Check token validity and expiration
3. Review permission settings
4. Check for clock drift between services

**Resolution**:
```bash
# Verify auth configuration
python -m neuroca.cli.tools verify_auth_config

# Reset admin credentials (emergency use only)
python -m neuroca.cli.tools reset_admin_credentials
```

## Database Issues

### Connection Problems

**Symptoms**:
- Error: `DATABASE_CONNECTION_FAILED`
- Intermittent query failures
- Slow query responses

**Troubleshooting Steps**:
1. Check database service status
2. Verify connection strings
3. Test network connectivity
4. Review connection pool settings

**Resolution**:
```bash
# Test database connection
python -m neuroca.cli.tools test_db_connection

# Reset connection pool
curl -X POST http://localhost:8000/api/v1/admin/db/reset_pool
```

### Data Integrity Issues

**Symptoms**:
- Inconsistent query results
- Error: `DATA_INTEGRITY_VIOLATION`
- Failed transactions

**Troubleshooting Steps**:
1. Check for failed migrations
2. Verify schema integrity
3. Review recent data modifications
4. Check for constraint violations

**Resolution**:
```bash
# Verify database integrity
python -m neuroca.cli.tools verify_db_integrity

# Run data consistency checks
python -m neuroca.cli.tools check_data_consistency
```

## Logging and Monitoring

### Log Collection Issues

**Symptoms**:
- Missing logs
- Error: `LOG_WRITE_FAILED`
- Incomplete monitoring data

**Troubleshooting Steps**:
1. Check log storage capacity
2. Verify logging configuration
3. Test log rotation
4. Check file permissions

**Resolution**:
```bash
# Rotate logs manually
logrotate -f /etc/logrotate.d/neuroca

# Reset logging configuration
systemctl restart neuroca-logging
```

### Alert Storm

**Symptoms**:
- Excessive notifications
- Repeated similar alerts
- False positive alerts

**Troubleshooting Steps**:
1. Review alert thresholds
2. Check for cascading failures
3. Verify monitoring configuration
4. Temporarily silence non-critical alerts

**Resolution**:
```bash
# Temporarily adjust alert thresholds
python -m neuroca.cli.tools adjust_alert_thresholds --critical-only

# Silence alerts for maintenance (max 2 hours)
python -m neuroca.cli.tools silence_alerts --duration=2h
```

## Common Error Codes

| Error Code | Description | Troubleshooting Steps |
|------------|-------------|----------------------|
| `MEMORY_WM_CAPACITY_EXCEEDED` | Working memory capacity limit reached | Increase capacity, clear unused contexts |
| `MEMORY_LTM_INDEX_CORRUPTION` | Long-term memory index corruption | Rebuild indices, check storage integrity |
| `LLM_CONNECTION_FAILED` | Failed to connect to LLM provider | Check API keys, network, provider status |
| `LLM_RESPONSE_MALFORMED` | Malformed response from LLM | Review prompt templates, check model parameters |
| `DATABASE_CONNECTION_FAILED` | Database connection failure | Verify DB service, connection strings, network |
| `SERVICE_UNAVAILABLE` | Service endpoint not responding | Check service status, restart if needed |
| `RESOURCE_EXHAUSTION` | System resources depleted | Scale resources, optimize operations |
| `AUTHENTICATION_FAILED` | Authentication error | Verify credentials, check token validity |

## Recovery Procedures

### Emergency Restart

In case of critical system failure, follow these steps:

1. **Save diagnostic information**:
   ```bash
   python -m neuroca.cli.tools collect_diagnostics > diagnostics_$(date +%Y%m%d_%H%M%S).log
   ```

2. **Perform graceful shutdown**:
   ```bash
   systemctl stop neuroca
   # Or for containerized deployment
   docker-compose down
   ```

3. **Verify data integrity**:
   ```bash
   python -m neuroca.cli.tools verify_db_integrity
   ```

4. **Restart services**:
   ```bash
   systemctl start neuroca
   # Or for containerized deployment
   docker-compose up -d
   ```

5. **Verify system health**:
   ```bash
   curl -X GET http://localhost:8000/api/v1/health
   ```

### Data Recovery

For data corruption or loss scenarios:

1. **Assess damage scope**:
   ```bash
   python -m neuroca.cli.tools assess_data_integrity
   ```

2. **Restore from backup** (if available):
   ```bash
   python -m neuroca.cli.tools restore --backup=latest
   ```

3. **Rebuild indices**:
   ```bash
   python -m neuroca.cli.tools rebuild_indices --force
   ```

4. **Verify recovery**:
   ```bash
   python -m neuroca.cli.tools verify_recovery
   ```

## Getting Support

If you cannot resolve an issue using this guide:

1. **Collect diagnostic information**:
   ```bash
   python -m neuroca.cli.tools collect_diagnostics > support_$(date +%Y%m%d_%H%M%S).log
   ```

2. **Contact support**:
   - Email: support@neuroca.ai
   - Support portal: https://support.neuroca.ai
   - Emergency hotline: +1-555-NEUROCA

3. **Community resources**:
   - GitHub Issues: https://github.com/neuroca/neuroca/issues
   - Community forum: https://community.neuroca.ai
   - Documentation: https://docs.neuroca.ai

---

**Note**: This troubleshooting guide is regularly updated. If you encounter issues not covered here, please contribute to its improvement by submitting feedback through the support channels.

Last updated: 2023-11-15