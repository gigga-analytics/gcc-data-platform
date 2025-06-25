# ITP Data Platform

Enterprise-Grade Data Platform on GCP/BigQuery.



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
