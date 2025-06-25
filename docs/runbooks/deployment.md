# Deployment Runbook

## Prerequisites
- GCP Project access
- Terraform installed
- gcloud CLI configured
- Repository access

## Infrastructure Deployment

### Initial Setup
```bash
# Clone repository
git clone 
cd itp-data-platform

# Setup GCP authentication
gcloud auth application-default login

# Initialize Terraform
cd infrastructure/terraform/environments/dev
terraform init
```

### Deploy Infrastructure
```bash
# Plan deployment
terraform plan -var-file="terraform.tfvars"

# Apply changes
terraform apply -var-file="terraform.tfvars"
```

### Deploy Data Models
```bash
# Install dbt dependencies
cd ../../../../dbt-models
dbt deps

# Run models
dbt run --target dev

# Run tests
dbt test --target dev
```

## Rollback Procedures

### Infrastructure Rollback
```bash
# Revert to previous Terraform state
terraform apply -var-file="terraform.tfvars" -target=
```

### Data Model Rollback
```bash
# Revert to previous dbt state
git checkout 
dbt run --target dev
```

## Monitoring
- Check Cloud Monitoring dashboards
- Verify data freshness in BigQuery
- Monitor Cloud Function logs
- Review cost reports

## Troubleshooting
- Check Terraform state for resource conflicts
- Verify IAM permissions
- Review Cloud Function error logs
- Validate dbt model compilation
