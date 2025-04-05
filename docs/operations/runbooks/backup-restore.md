# NeuroCognitive Architecture (NCA) Backup and Restore Runbook

## Overview

This runbook provides comprehensive procedures for backing up and restoring the NeuroCognitive Architecture (NCA) system. Regular backups are critical to ensure data integrity, system resilience, and quick recovery in case of failures.

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Backup Components](#backup-components)
3. [Backup Procedures](#backup-procedures)
4. [Restore Procedures](#restore-procedures)
5. [Backup Verification](#backup-verification)
6. [Disaster Recovery](#disaster-recovery)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)
9. [Appendix](#appendix)

## Backup Strategy

### Backup Frequency

| Component | Frequency | Retention Period | Type |
|-----------|-----------|------------------|------|
| Database | Daily | 30 days | Full + Incremental |
| Memory Tiers | Daily | 14 days | Full |
| Configuration | After changes | 90 days | Full |
| Model Weights | Weekly | 180 days | Full |
| Logs | Daily | 90 days | Incremental |

### Backup Storage

- **Primary Storage**: Cloud object storage (AWS S3/Azure Blob/GCP Cloud Storage)
- **Secondary Storage**: Offsite backup in a different region
- **Tertiary Storage**: Cold storage for long-term archival (optional)

## Backup Components

### 1. Database Backups

The NCA system uses multiple databases that need to be backed up:

- **PostgreSQL**: Primary relational database for structured data
- **MongoDB**: Document store for episodic memory
- **Redis**: Cache and working memory storage
- **Vector Database**: For semantic memory embeddings

### 2. Memory Tier Backups

All three memory tiers require specific backup approaches:

- **Working Memory**: Redis snapshots and state exports
- **Episodic Memory**: MongoDB dumps and journal backups
- **Semantic Memory**: Vector database backups and embedding exports

### 3. Configuration Backups

- Environment configurations
- System parameters
- Integration settings
- Security configurations

### 4. Model Weights and States

- LLM fine-tuned weights
- Checkpoint states
- Training artifacts

### 5. Logs and Monitoring Data

- Application logs
- System metrics
- Audit trails
- Performance data

## Backup Procedures

### Automated Backup Setup

1. **Configure Backup Service**

   ```bash
   # Install backup agent
   sudo apt-get update
   sudo apt-get install neuroca-backup-agent
   
   # Configure backup agent
   sudo neuroca-backup configure --config-path /etc/neuroca/backup.yaml
   ```

2. **Create Backup Configuration**

   Example `backup.yaml`:

   ```yaml
   backup:
     schedule:
       database: "0 2 * * *"  # Daily at 2 AM
       memory_tiers: "0 3 * * *"  # Daily at 3 AM
       configuration: "0 1 * * 0"  # Weekly on Sunday at 1 AM
       model_weights: "0 4 * * 0"  # Weekly on Sunday at 4 AM
     storage:
       primary:
         type: "s3"
         bucket: "neuroca-backups"
         region: "us-west-2"
         path: "/backups"
       secondary:
         type: "s3"
         bucket: "neuroca-dr-backups"
         region: "eu-central-1"
         path: "/backups"
     retention:
       database: "30d"
       memory_tiers: "14d"
       configuration: "90d"
       model_weights: "180d"
       logs: "90d"
     encryption:
       enabled: true
       key_management: "kms"
       kms_key_id: "arn:aws:kms:us-west-2:123456789012:key/abcd1234-ef56-gh78-ij90-klmn1234pqrs"
   ```

3. **Enable Backup Service**

   ```bash
   sudo systemctl enable neuroca-backup
   sudo systemctl start neuroca-backup
   ```

### Manual Backup Procedures

#### Database Backup

1. **PostgreSQL Backup**

   ```bash
   # Export PostgreSQL database
   pg_dump -h <host> -U <username> -d neuroca_db -F custom -f /backup/neuroca_db_$(date +%Y%m%d).dump
   
   # Compress backup
   gzip /backup/neuroca_db_$(date +%Y%m%d).dump
   
   # Upload to storage
   aws s3 cp /backup/neuroca_db_$(date +%Y%m%d).dump.gz s3://neuroca-backups/database/
   ```

2. **MongoDB Backup**

   ```bash
   # Export MongoDB collections
   mongodump --host <host> --port <port> --db neuroca_episodic --out /backup/mongo_$(date +%Y%m%d)
   
   # Compress backup
   tar -czf /backup/mongo_$(date +%Y%m%d).tar.gz /backup/mongo_$(date +%Y%m%d)
   
   # Upload to storage
   aws s3 cp /backup/mongo_$(date +%Y%m%d).tar.gz s3://neuroca-backups/database/
   ```

3. **Redis Backup**

   ```bash
   # Trigger Redis SAVE command
   redis-cli -h <host> -p <port> SAVE
   
   # Copy RDB file
   cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb
   
   # Upload to storage
   aws s3 cp /backup/redis_$(date +%Y%m%d).rdb s3://neuroca-backups/database/
   ```

4. **Vector Database Backup**

   ```bash
   # Export vector database (example for Pinecone)
   python -m neuroca.tools.backup.vector_db_export \
     --output /backup/vector_db_$(date +%Y%m%d).jsonl
   
   # Compress backup
   gzip /backup/vector_db_$(date +%Y%m%d).jsonl
   
   # Upload to storage
   aws s3 cp /backup/vector_db_$(date +%Y%m%d).jsonl.gz s3://neuroca-backups/database/
   ```

#### Memory Tier Backup

```bash
# Export all memory tiers
python -m neuroca.tools.backup.memory_export \
  --working-memory \
  --episodic-memory \
  --semantic-memory \
  --output /backup/memory_$(date +%Y%m%d)

# Compress backup
tar -czf /backup/memory_$(date +%Y%m%d).tar.gz /backup/memory_$(date +%Y%m%d)

# Upload to storage
aws s3 cp /backup/memory_$(date +%Y%m%d).tar.gz s3://neuroca-backups/memory/
```

#### Configuration Backup

```bash
# Export all configurations
python -m neuroca.tools.backup.config_export \
  --output /backup/config_$(date +%Y%m%d).yaml

# Encrypt sensitive configuration
gpg --encrypt --recipient backup@neuroca.org /backup/config_$(date +%Y%m%d).yaml

# Upload to storage
aws s3 cp /backup/config_$(date +%Y%m%d).yaml.gpg s3://neuroca-backups/config/
```

#### Model Weights Backup

```bash
# Export model weights and checkpoints
python -m neuroca.tools.backup.model_export \
  --output /backup/models_$(date +%Y%m%d)

# Compress backup
tar -czf /backup/models_$(date +%Y%m%d).tar.gz /backup/models_$(date +%Y%m%d)

# Upload to storage
aws s3 cp /backup/models_$(date +%Y%m%d).tar.gz s3://neuroca-backups/models/
```

## Restore Procedures

### Pre-Restore Checklist

1. Identify the specific backup to restore
2. Ensure sufficient disk space for restore operations
3. Verify backup integrity
4. Stop affected services
5. Document current state before restore

### Database Restore

1. **PostgreSQL Restore**

   ```bash
   # Download backup
   aws s3 cp s3://neuroca-backups/database/neuroca_db_<date>.dump.gz /restore/
   
   # Decompress
   gunzip /restore/neuroca_db_<date>.dump.gz
   
   # Restore database
   pg_restore -h <host> -U <username> -d neuroca_db -c /restore/neuroca_db_<date>.dump
   ```

2. **MongoDB Restore**

   ```bash
   # Download backup
   aws s3 cp s3://neuroca-backups/database/mongo_<date>.tar.gz /restore/
   
   # Decompress
   tar -xzf /restore/mongo_<date>.tar.gz -C /restore/
   
   # Restore database
   mongorestore --host <host> --port <port> --db neuroca_episodic /restore/mongo_<date>/neuroca_episodic
   ```

3. **Redis Restore**

   ```bash
   # Download backup
   aws s3 cp s3://neuroca-backups/database/redis_<date>.rdb /restore/
   
   # Stop Redis
   sudo systemctl stop redis
   
   # Replace RDB file
   sudo cp /restore/redis_<date>.rdb /var/lib/redis/dump.rdb
   sudo chown redis:redis /var/lib/redis/dump.rdb
   
   # Start Redis
   sudo systemctl start redis
   ```

4. **Vector Database Restore**

   ```bash
   # Download backup
   aws s3 cp s3://neuroca-backups/database/vector_db_<date>.jsonl.gz /restore/
   
   # Decompress
   gunzip /restore/vector_db_<date>.jsonl.gz
   
   # Restore vector database
   python -m neuroca.tools.restore.vector_db_import \
     --input /restore/vector_db_<date>.jsonl
   ```

### Memory Tier Restore

```bash
# Download backup
aws s3 cp s3://neuroca-backups/memory/memory_<date>.tar.gz /restore/

# Decompress
tar -xzf /restore/memory_<date>.tar.gz -C /restore/

# Restore memory tiers
python -m neuroca.tools.restore.memory_import \
  --working-memory \
  --episodic-memory \
  --semantic-memory \
  --input /restore/memory_<date>
```

### Configuration Restore

```bash
# Download backup
aws s3 cp s3://neuroca-backups/config/config_<date>.yaml.gpg /restore/

# Decrypt
gpg --decrypt /restore/config_<date>.yaml.gpg > /restore/config_<date>.yaml

# Restore configuration
python -m neuroca.tools.restore.config_import \
  --input /restore/config_<date>.yaml
```

### Model Weights Restore

```bash
# Download backup
aws s3 cp s3://neuroca-backups/models/models_<date>.tar.gz /restore/

# Decompress
tar -xzf /restore/models_<date>.tar.gz -C /restore/

# Restore models
python -m neuroca.tools.restore.model_import \
  --input /restore/models_<date>
```

### Post-Restore Verification

1. Verify database integrity
2. Check memory tier consistency
3. Validate configuration settings
4. Test system functionality
5. Monitor system performance

## Backup Verification

### Automated Verification

The system performs automated verification of backups:

```bash
# Verify backup integrity
python -m neuroca.tools.backup.verify \
  --backup-path s3://neuroca-backups/database/neuroca_db_<date>.dump.gz

# Test restore in sandbox environment
python -m neuroca.tools.backup.test_restore \
  --backup-path s3://neuroca-backups/database/neuroca_db_<date>.dump.gz \
  --sandbox-env
```

### Manual Verification

1. **Regular Restore Testing**
   - Schedule quarterly restore tests
   - Document restore time and success rate
   - Identify and address any issues

2. **Backup Integrity Checks**
   - Verify checksums
   - Validate backup file structure
   - Test sample data retrieval

## Disaster Recovery

### Recovery Time Objectives (RTO)

| Component | RTO |
|-----------|-----|
| Database | 4 hours |
| Memory Tiers | 6 hours |
| Full System | 12 hours |

### Recovery Point Objectives (RPO)

| Component | RPO |
|-----------|-----|
| Database | 24 hours |
| Memory Tiers | 24 hours |
| Configuration | 7 days |

### Disaster Recovery Procedure

1. **Assess the Situation**
   - Identify affected components
   - Determine cause of failure
   - Estimate recovery time

2. **Activate Recovery Team**
   - Notify stakeholders
   - Assign recovery tasks
   - Establish communication channels

3. **Infrastructure Recovery**
   - Provision new infrastructure if needed
   - Configure networking and security
   - Prepare for data restoration

4. **Data Restoration**
   - Follow restore procedures for each component
   - Prioritize critical systems
   - Validate data integrity during restore

5. **System Verification**
   - Test system functionality
   - Verify integrations
   - Perform security checks

6. **Return to Normal Operations**
   - Redirect traffic to recovered system
   - Monitor system performance
   - Document lessons learned

## Troubleshooting

### Common Backup Issues

| Issue | Possible Cause | Resolution |
|-------|---------------|------------|
| Backup failure | Insufficient disk space | Free up disk space or increase volume size |
| Slow backup performance | Network congestion | Schedule backups during off-peak hours |
| Corrupted backup files | Storage issues | Verify storage health, implement checksums |
| Backup timeout | Large data volume | Increase timeout settings, implement chunking |

### Common Restore Issues

| Issue | Possible Cause | Resolution |
|-------|---------------|------------|
| Restore failure | Version mismatch | Ensure compatible versions between backup and target |
| Incomplete restore | Corrupted backup | Use previous backup, verify backup integrity |
| Permission issues | Incorrect credentials | Verify and update access permissions |
| Data inconsistency | Partial restore | Restore from consistent backup point |

## Security Considerations

1. **Encryption**
   - All backups must be encrypted at rest
   - Use KMS for key management
   - Rotate encryption keys annually

2. **Access Control**
   - Implement least privilege access
   - Use MFA for backup access
   - Audit all backup and restore operations

3. **Data Protection**
   - Sanitize sensitive data in test restores
   - Implement secure deletion for expired backups
   - Regularly review data classification

## Appendix

### Backup Size Estimates

| Component | Approximate Size |
|-----------|------------------|
| PostgreSQL Database | 50-100 GB |
| MongoDB | 200-500 GB |
| Redis | 10-20 GB |
| Vector Database | 100-300 GB |
| Model Weights | 10-50 GB per model |

### Backup Command Reference

For quick reference, all backup commands are available in the script:

```bash
/usr/local/bin/neuroca-backup-all.sh
```

### Restore Command Reference

For quick reference, all restore commands are available in the script:

```bash
/usr/local/bin/neuroca-restore-all.sh
```

### Related Documentation

- [System Architecture](../architecture/system-overview.md)
- [Database Schema](../technical/database-schema.md)
- [Monitoring Runbook](./monitoring.md)
- [Disaster Recovery Plan](../planning/disaster-recovery.md)

---

**Document Revision History**

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2023-10-01 | 1.0 | NCA Team | Initial version |
| 2023-12-15 | 1.1 | NCA Team | Added vector database backup procedures |
| 2024-02-10 | 1.2 | NCA Team | Updated restore verification steps |