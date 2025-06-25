# ITP Data Platform

Enterprise-Grade Data Platform on GCP/BigQuery.



# In The Pocket - Data Platform

## 🎯 Overview
Modern, cloud-native data platform designed to accelerate financial reporting and strategic decision-making at In The Pocket.

## 🏗️ Architecture
Built on Google Cloud Platform with BigQuery as the core analytical engine, providing scalable, cost-effective data processing with enterprise-grade governance.

## 🚀 Quick Start

### Prerequisites
- Google Cloud SDK
- Terraform >= 1.0
- Python >= 3.9
- dbt-bigquery
- Docker

### Setup
```bash
# Clone and setup
git clone 
cd itp-data-platform

# Initialize infrastructure
cd infrastructure/terraform/environments/dev
terraform init
terraform plan
terraform apply

# Setup data pipelines
cd ../../../../data-pipelines
pip install -r requirements.txt

# Initialize dbt
cd ../dbt-models
dbt deps
dbt run
```

## 📁 Repository Structure
```
itp-data-platform/
├── infrastructure/          # Terraform IaC
├── data-pipelines/         # Python ETL/ELT pipelines
├── dbt-models/             # Data transformation models
├── monitoring/             # Dashboards and alerts
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

## 🔧 Development
- [Architecture Documentation](docs/architecture/)
- [Deployment Guide](docs/runbooks/deployment.md)
- [User Guides](docs/user-guides/)

## 🤝 Contributing
1. Create feature branch
2. Make changes
3. Run tests: `make test`
4. Submit PR

## 📞 Support
For questions or issues, contact the Data Engineering team.


```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │────│  Ingestion      │────│  Storage &      │
│                 │    │  Layer          │    │  Processing     │
│ • Financial     │    │ • Cloud         │    │ • BigQuery      │
│   Systems       │    │   Functions     │    │ • Cloud         │
│ • CRM/ERP       │    │ • Pub/Sub       │    │   Storage       │
│ • Marketing     │    │ • Dataflow      │    │ • Dataform      │
│ • Operations    │    │ • Cloud         │    │                 │
│                 │    │   Composer      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐            │
│  Visualization  │────│  Analytics      │────────────┘
│                 │    │  Layer          │
│ • Looker Studio │    │ • BigQuery ML   │
│ • Tableau       │    │ • Dataform      │
│ • Custom Apps   │    │ • dbt Cloud     │
└─────────────────┘    └─────────────────┘
```
