# Incident Response Runbook

## Incident Classification

### Severity Levels

**P0 - Critical**
- Complete data platform outage
- Data corruption affecting business decisions
- Security breach or data leak
- Financial data accuracy issues

**P1 - High**
- Pipeline failures affecting critical reports
- Significant performance degradation
- Data freshness beyond SLA (>24 hours for critical data)

**P2 - Medium**
- Non-critical pipeline failures
- Data quality issues in non-critical datasets
- Performance issues not affecting end users

**P3 - Low**
- Minor data quality issues
- Documentation updates needed
- Feature requests

## Response Procedures

### P0 - Critical Incidents

1. **Immediate Response (0-15 minutes)**
   - Alert on-call engineer via PagerDuty
   - Create incident in Slack: `#incidents`
   - Notify stakeholders: Leadership, Finance team
   - Begin initial assessment

2. **Assessment Phase (15-30 minutes)**
   - Identify scope of impact
   - Determine root cause
   - Estimate time to resolution
   - Communicate status to stakeholders

3. **Resolution Phase**
   - Implement immediate fixes
   - Monitor system stability
   - Document all actions taken
   - Prepare communication for stakeholders

4. **Post-Incident (24-48 hours)**
   - Conduct post-mortem meeting
   - Document lessons learned
   - Implement preventive measures
   - Update runbooks and procedures

### P1 - High Incidents

1. **Response (0-30 minutes)**
   - Alert data engineering team
   - Create incident in Slack: `#data-platform`
   - Begin investigation

2. **Resolution**
   - Fix within 4 hours
   - Update stakeholders every hour
   - Document resolution steps

### Common Incident Scenarios

#### Pipeline Failure

**Symptoms:**
- Pipeline monitoring alerts
- Data freshness alerts
- Missing data in reports

**Investigation Steps:**
1. Check Cloud Function logs
2. Verify source system connectivity
3. Check BigQuery job history
4. Review Dataflow job status

**Common Fixes:**
- Restart failed Cloud Functions
- Reprocess data for specific date ranges
- Update API credentials
- Increase resource allocation

#### Data Quality Issues

**Symptoms:**
- Data quality alerts
- Unusual patterns in reports
- Stakeholder reports of incorrect data

**Investigation Steps:**
1. Run data quality checks
2. Compare with source systems
3. Check recent pipeline changes
4. Review data transformation logic

**Common Fixes:**
- Reprocess affected data
- Update data validation rules
- Fix transformation logic
- Implement additional quality checks

#### Performance Issues

**Symptoms:**
- Slow dashboard loading
- Query timeouts
- High BigQuery costs

**Investigation Steps:**
1. Check BigQuery job performance
2. Review query execution plans
3. Analyze slot utilization
4. Check data partitioning

**Common Fixes:**
- Optimize queries
- Add clustering/partitioning
- Schedule heavy queries for off-peak hours
- Implement query result caching

## Contact Information

### On-Call Rotation
- Primary: Data Engineering Team Lead
- Secondary: Senior Data Engineer
- Escalation: CTO

### Stakeholder Contacts
- Finance Team: finance@inthepocket.com
- Management: management@inthepocket.com
- IT Support: support@inthepocket.com

### External Vendors
- Google Cloud Support: [Support Case Portal]
- Third-party API Support: [Vendor contacts]

## Tools and Resources

### Monitoring
- Cloud Monitoring: [Dashboard URL]
- Slack Alerts: #data-platform, #incidents
- PagerDuty: [On-call schedule]

### Logging
- Cloud Logging: [Log viewer URL]
- BigQuery Logs: [Query history]
- Application Logs: [Cloud Functions logs]

### Documentation
- Architecture Docs: /docs/architecture/
- API Documentation: [Internal wiki]
- Vendor Documentation: [External links]

## Templates

### Incident Communication Template

```
🚨 INCIDENT ALERT - [SEVERITY]

**Incident:** [Brief description]
**Impact:** [Who/what is affected]
**Status:** [Investigating/Identified/Resolving/Resolved]
**ETA:** [Estimated resolution time]
**Updates:** Will provide updates every [frequency]

**Actions Taken:**
- [List of actions]

**Next Steps:**
- [Planned actions]

**Incident Commander:** [Name]
```

### Post-Mortem Template

```
# Post-Mortem: [Incident Title]

## Incident Summary
- **Date:** [Date]
- **Duration:** [Start - End time]
- **Severity:** [P0/P1/P2/P3]
- **Root Cause:** [Brief description]

## Timeline
- [Time]: [Event description]

## Impact
- **Systems Affected:** [List]
- **Users Affected:** [Number/description]
- **Business Impact:** [Description]

## Root Cause Analysis
[Detailed explanation]

## Resolution
[What was done to fix the issue]

## Lessons Learned
- **What went well:**
- **What could be improved:**

## Action Items
- [ ] [Action item 1] - Owner: [Name] - Due: [Date]
- [ ] [Action item 2] - Owner: [Name] - Due: [Date]
```
