# Snowflake Backup and Recovery Options

## Overview

Snowflake provides multiple layers of data protection and recovery mechanisms to address different scenarios from user errors to regional disasters. This document outlines all available backup and recovery options with implementation steps for production environments.

## 1. Time Travel (Primary Recovery Option)

**Purpose**: Query and restore historical data within a defined period (1-90 days)

**Use Cases**:
- Recovering from accidental row deletions
- Restoring dropped tables (`UNDROP`)
- Data validation and auditing
- Creating point-in-time clones

**Production Setup Steps**:
```sql
-- Enable extended Time Travel (Enterprise Edition+)
ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 90;

-- Set retention at database level
CREATE DATABASE my_db DATA_RETENTION_TIME_IN_DAYS = 90;

-- Set retention at table level  
CREATE TABLE my_table (col1 NUMBER) DATA_RETENTION_TIME_IN_DAYS = 90;

-- Check retention settings
SHOW TABLES LIKE 'my_table' ->> SELECT "name", "retention_time" FROM $1;
```

**Recovery Operations**:
```sql
-- Query historical data
SELECT * FROM my_table AT(TIMESTAMP => '2025-01-20 10:00:00'::timestamp_tz);

-- Clone historical table
CREATE TABLE restored_table CLONE my_table AT(OFFSET => -3600);

-- Restore dropped table
UNDROP TABLE my_table;

-- Restore dropped database
UNDROP DATABASE my_db;
```

**Key Considerations**:
- Standard retention: 1 day (all editions)
- Extended retention: Up to 90 days (Enterprise Edition+)
- Storage costs apply for retained data
- Cannot be completely disabled (can be set to 0 days)

## 2. Snowflake Backups (Long-term Retention)

**Purpose**: Immutable snapshots for regulatory compliance and long-term retention (up to 10 years)

**Use Cases**:
- Regulatory compliance (SEC 17a-4, FINRA, CFTC)
- Cyber resilience against ransomware
- Long-term data archiving
- Business continuity

**Production Setup Steps**:
```sql
-- Create backup policy
CREATE BACKUP POLICY daily_backup_policy
  SCHEDULE = '1440 MINUTE'  -- Daily
  EXPIRE_AFTER_DAYS = 2555  -- 7 years
  COMMENT = 'Daily backups for compliance';

-- Create backup set with policy
CREATE BACKUP SET critical_db_backups
  FOR DATABASE critical_db
  WITH BACKUP POLICY daily_backup_policy;

-- Enable retention lock (Business Critical Edition)
CREATE BACKUP POLICY immutable_backup_policy
  WITH RETENTION LOCK
  SCHEDULE = '1440 MINUTE'
  EXPIRE_AFTER_DAYS = 3650;  -- 10 years
```

**Recovery Operations**:
```sql
-- List available backups
SHOW BACKUPS IN BACKUP SET critical_db_backups;

-- Restore from specific backup
CREATE DATABASE restored_critical_db 
  FROM BACKUP SET critical_db_backups 
  IDENTIFIER 'backup_id_from_show_command';

-- Restore table from backup
CREATE TABLE restored_table 
  FROM BACKUP SET table_backups 
  IDENTIFIER 'backup_id';
```

**Key Features**:
- Zero-copy mechanism (storage-efficient)
- Retention lock prevents deletion
- Legal hold support for litigation
- Available for tables, schemas, and databases
- Automatic scheduling and expiration

## 3. Fail-safe (Final Recovery Layer)

**Purpose**: Disaster recovery managed by Snowflake (7 days after Time Travel expires)

**Use Cases**:
- Catastrophic data loss
- Final safety net after Time Travel expires

**Setup**: Automatically enabled, no configuration required

**Recovery**: Contact Snowflake Support - only available for catastrophic data loss scenarios

**Key Considerations**:
- 7-day retention period
- Managed entirely by Snowflake
- No user access to data
- Final recovery option

## 4. Account Replication & Failover

**Purpose**: Cross-region/cross-cloud disaster recovery

**Use Cases**:
- Regional outages
- Cloud provider failures
- Geographic redundancy
- Business continuity planning

**Production Setup Steps**:
```sql
-- Create failover group (Business Critical Edition)
CREATE FAILOVER GROUP my_failover_group
  OBJECT_TYPES = DATABASES, WAREHOUSES, USERS, ROLES
  ALLOWED_ACCOUNTS = 'org_name.target_account'
  REPLICATION_SCHEDULE = '60 MINUTE';

-- Add databases to failover group
ALTER FAILOVER GROUP my_failover_group ADD DATABASE critical_db;

-- Perform initial refresh
ALTER FAILOVER GROUP my_failover_group REFRESH;
```

**Failover Operations**:
```sql
-- Promote secondary to primary
ALTER FAILOVER GROUP my_failover_group PRIMARY;

-- Fail back to original
ALTER FAILOVER GROUP my_failover_group FAILOVER TO ACCOUNT org_name.source_account;
```

**Key Features**:
- Cross-region and cross-cloud support
- Point-in-time consistency
- Read-write access after promotion
- Automatic refresh scheduling

## 5. Zero-Copy Cloning (Additional Recovery)

**Purpose**: Point-in-time copies for testing and recovery validation

**Use Cases**:
- Development environment refresh
- Recovery testing
- Data analysis without impacting production
- Quick rollback scenarios

**Setup Steps**:
```sql
-- Clone entire database
CREATE DATABASE test_clone CLONE production_db;

-- Clone specific schema
CREATE SCHEMA prod_schema_clone CLONE production_db.public;

-- Clone table at specific time
CREATE TABLE table_backup CLONE production_table AT(TIMESTAMP => '2025-01-20 12:00:00');
```

**Key Benefits**:
- Instant creation
- Storage-efficient (metadata only)
- Independent objects after cloning
- Useful for testing recovery procedures

## Production Best Practices

### 1. Layered Recovery Strategy
- **Time Travel**: Operational recovery (minutes to hours)
- **Backups**: Long-term retention and compliance (days to years)
- **Replication**: Geographic disaster recovery (hours)
- **Fail-safe**: Final safety net (Snowflake-managed)

### 2. Retention Planning
```sql
-- Recommended production settings
ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 30;  -- Time Travel
-- Backups: 1-7 years for compliance
-- Replication: Continuous with hourly refresh
```

### 3. Cost Management
- Monitor storage usage: `TABLE_STORAGE_METRICS` view
- Track backup costs: `BACKUP_STORAGE_USAGE` view
- Optimize retention periods based on RPO/RTO requirements

### 4. Security and Compliance
- Use retention locks for immutable compliance data
- Apply legal holds for litigation requirements
- Implement role-based access control for recovery operations

### 5. Testing and Validation
```sql
-- Regular recovery testing using clones
CREATE DATABASE recovery_test CLONE production_db AT(OFFSET => -86400);
-- Validate recovery procedures monthly
```

### 6. Monitoring and Alerting
```sql
-- Monitor backup operations
SELECT * FROM ACCOUNT_USAGE.BACKUP_OPERATION_HISTORY 
WHERE OPERATION_TYPE = 'BACKUP_CREATION'
ORDER BY START_TIME DESC LIMIT 10;

-- Check replication status
SELECT * FROM ACCOUNT_USAGE.REPLICATION_USAGE_HISTORY;
```

## Implementation Checklist

### Pre-Implementation
- [ ] Assess RPO/RTO requirements
- [ ] Determine compliance retention periods
- [ ] Choose appropriate Snowflake edition
- [ ] Design replication topology

### Configuration
- [ ] Set Time Travel retention periods
- [ ] Create backup policies and sets
- [ ] Configure replication/failover groups
- [ ] Set up monitoring and alerting

### Testing
- [ ] Test Time Travel queries and restores
- [ ] Validate backup creation and restoration
- [ ] Perform failover testing
- [ ] Document recovery procedures

### Ongoing Maintenance
- [ ] Monitor storage costs
- [ ] Review retention policies quarterly
- [ ] Update disaster recovery plans
- [ ] Conduct regular recovery drills

## Cost Considerations

| Feature | Storage Cost | Compute Cost | Notes |
|---------|-------------|-------------|-------|
| Time Travel | Yes | No | Billed for retained bytes |
| Backups | Yes | Yes | Backup compute + storage |
| Replication | Yes | Yes | Data transfer + compute |
| Fail-safe | Yes | No | Included in standard pricing |
| Cloning | Minimal | No | Zero-copy until diverged |

## Support and Troubleshooting

**Common Issues**:
- Insufficient privileges for recovery operations
- Storage quota exceeded
- Replication lag in disaster scenarios
- Backup retention policy conflicts

**Escalation Path**:
1. Check ACCOUNT_USAGE views for diagnostics
2. Review Snowflake status page
3. Contact Snowflake Support for Fail-safe recovery
4. Engage account team for compliance requirements

## Conclusion

Snowflake provides a comprehensive, multi-layered backup and recovery solution that addresses scenarios from simple user errors to regional disasters. By implementing a combination of Time Travel, Backups, Replication, and proper monitoring, organizations can achieve robust data protection while meeting regulatory requirements and managing costs effectively.

The key to success is proper planning, regular testing, and ongoing optimization of retention policies based on business requirements and cost considerations.