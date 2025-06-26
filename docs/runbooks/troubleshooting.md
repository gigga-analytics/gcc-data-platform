# Troubleshooting Guide

## Common Issues and Solutions

### BigQuery Issues

#### Query Performance Problems

**Symptoms:**
- Slow-running queries
- Query timeouts
- High slot usage

**Troubleshooting Steps:**
1. **Check Query Plan:**
   ```sql
   -- Add to the beginning of your query
   SELECT * FROM `project.dataset.table`
   WHERE _PARTITIONTIME >= TIMESTAMP("2024-01-01")
   ```

2. **Optimize Partitioning:**
   ```sql
   -- Use partition filters
   WHERE DATE(transaction_date) >= "2024-01-01"
   ```

3. **Add Clustering:**
   ```sql
   -- Cluster frequently filtered columns
   CLUSTER BY customer_id, business_unit
   ```

4. **Query Optimization:**
   - Use SELECT only necessary columns
   - Filter early in subqueries
   - Use LIMIT for large result sets
   - Avoid SELECT DISTINCT when possible

#### BigQuery Job Failures

**Common Error Messages:**

1. **"Resources exceeded"**
   - Solution: Add partition filters, reduce data scanned
   - Emergency fix: Use smaller time windows

2. **"Query timeout"**
   - Solution: Optimize query, use batch processing
   - Emergency fix: Break into smaller queries

3. **"Permission denied"**
   - Solution: Check IAM roles and dataset permissions
   - Emergency fix: Use service account with proper permissions

### Cloud Functions Issues

#### Function Timeout

**Symptoms:**
- Functions timing out before completion
- Incomplete data processing

**Solutions:**
1. **Increase Timeout:**
   ```yaml
   timeout: 540s  # Max 9 minutes for HTTP, 60 minutes for background
   ```

2. **Optimize Code:**
   - Use batch processing
   - Implement checkpointing
   - Use async operations

3. **Split into Multiple Functions:**
   - Break large operations into smaller chunks
   - Use Pub/Sub for orchestration

#### Memory Issues

**Symptoms:**
- Out of memory errors
- Function crashes

**Solutions:**
1. **Increase Memory:**
   ```yaml
   memory: 2048MB  # Increase from default 256MB
   ```

2. **Optimize Memory Usage:**
   - Process data in chunks
   - Clear variables after use
   - Use generators instead of lists

#### Authentication Errors

**Common Issues:**
1. **Service Account Missing:**
   ```bash
   # Set service account
   gcloud functions deploy function-name \
     --service-account=sa-name@project.iam.gserviceaccount.com
   ```

2. **Insufficient Permissions:**
   - Check IAM roles
   - Verify BigQuery permissions
   - Test with minimal permissions

### Data Pipeline Issues

#### Data Freshness Problems

**Investigation Steps:**
1. **Check Source Systems:**
   ```bash
   # Test API connectivity
   curl -H "Authorization: Bearer $TOKEN" $API_ENDPOINT
   ```

2. **Verify Scheduler:**
   ```bash
   # Check Cloud Scheduler jobs
   gcloud scheduler jobs list
   ```

3. **Check Function Logs:**
   ```bash
   # View recent logs
   gcloud functions logs read FUNCTION_NAME --limit=50
   ```

**Common Fixes:**
- Restart failed schedulers
- Update API credentials
- Increase retry attempts
- Fix date range calculations

#### Data Quality Issues

**Detection:**
1. **Run Quality Checks:**
   ```python
   from data_quality import DataQualityFramework
   
   dq = DataQualityFramework("project-id")
   results = dq.execute_quality_suite("dataset", "table", config)
   ```

2. **Compare Row Counts:**
   ```sql
   SELECT 
     COUNT(*) as current_count,
     LAG(COUNT(*)) OVER (ORDER BY DATE(_PARTITIONTIME)) as previous_count
   FROM `project.dataset.table`
   WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)
   GROUP BY DATE(_PARTITIONTIME)
   ```

**Common Issues:**
- Duplicate records: Add deduplication logic
- Missing data: Check source system filters
- Schema changes: Update validation rules
- Data type mismatches: Add type casting

### dbt Issues

#### Model Compilation Errors

**Common Errors:**
1. **Macro not found:**
   ```bash
   dbt deps  # Install missing packages
   ```

2. **Missing reference:**
   ```sql
   -- Check model names
   {{ ref('staging_table_name') }}
   ```

3. **SQL syntax errors:**
   - Check BigQuery SQL syntax
   - Validate Jinja templating
   - Test with simpler queries

#### Model Performance Issues

**Optimization Strategies:**
1. **Incremental Models:**
   ```sql
   {{ config(
       materialized='incremental',
       unique_key='id',
       on_schema_change='fail'
   ) }}
   
   SELECT * FROM source_table
   {% if is_incremental() %}
     WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
   {% endif %}
   ```

2. **Partitioning:**
   ```sql
   {{ config(
       partition_by={'field': 'date_column', 'data_type': 'date'}
   ) }}
   ```

3. **Clustering:**
   ```sql
   {{ config(
       cluster_by=['frequently_filtered_column']
   ) }}
   ```

### Infrastructure Issues

#### Terraform State Issues

**State Lock:**
```bash
# Force unlock (use carefully)
terraform force-unlock LOCK_ID
```

**State Drift:**
```bash
# Refresh state
terraform refresh

# Import existing resources
terraform import google_bigquery_dataset.example project:dataset_id
```

**Version Conflicts:**
```bash
# Upgrade providers
terraform init -upgrade
```

#### Networking Issues

**Connectivity Problems:**
1. **Check Firewall Rules:**
   ```bash
   gcloud compute firewall-rules list
   ```

2. **Verify VPC Configuration:**
   ```bash
   gcloud compute networks list
   ```

3. **Test Internal Connectivity:**
   ```bash
   # From Cloud Shell
   telnet internal-service-ip port
   ```

### Monitoring and Alerting Issues

#### Missing Alerts

**Verification Steps:**
1. **Check Notification Channels:**
   ```bash
   gcloud alpha monitoring channels list
   ```

2. **Verify Alert Policies:**
   ```bash
   gcloud alpha monitoring policies list
   ```

3. **Test Notifications:**
   - Send test alert
   - Check Slack webhook
   - Verify email delivery

#### False Positives

**Common Causes:**
- Incorrect thresholds
- Missing filters
- Timezone issues
- Holiday/weekend patterns

**Solutions:**
- Adjust thresholds based on historical data
- Add business hours filters
- Implement smart alerting with ML
- Create separate policies for different scenarios

## Diagnostic Commands

### BigQuery Diagnostics
```bash
# Check job history
bq ls -j --max_results=10

# Get job details
bq show -j JOB_ID

# Check dataset permissions
bq show dataset_id
```

### Cloud Functions Diagnostics
```bash
# List functions
gcloud functions list

# Get function details
gcloud functions describe FUNCTION_NAME

# View logs
gcloud functions logs read FUNCTION_NAME --limit=50
```

### Storage Diagnostics
```bash
# List buckets
gsutil ls

# Check bucket permissions
gsutil iam get gs://bucket-name

# Check object lifecycle
gsutil lifecycle get gs://bucket-name
```

## Emergency Contacts

### Google Cloud Support
- Support Case Portal: [URL]
- Phone: [Support phone number]
- Emergency escalation: [Escalation process]

### Internal Escalation
1. Data Engineering Team Lead
2. CTO
3. CEO (for business-critical issues)

### External Dependencies
- API Provider 1: [Contact info]
- API Provider 2: [Contact info]
- Security Team: [Contact info]