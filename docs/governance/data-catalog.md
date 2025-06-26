# Data Catalog

## Overview
This catalog provides a comprehensive overview of all data assets in the ITP Data Platform, including their sources, transformations, and business definitions.

## Datasets

### Raw Data Layer

#### `dev_raw.financial_transactions_raw`
**Source:** ERP System API  
**Refresh Frequency:** Real-time via Pub/Sub  
**Owner:** Data Engineering Team  
**Business Owner:** Finance Team  

**Description:** Raw financial transaction data before any transformations.

| Column | Type | Description | Business Rules |
|--------|------|-------------|----------------|
| transaction_id | STRING | Unique transaction identifier | Primary key, format: TXN_XXXXXX |
| source_system | STRING | Originating system | ERP, ACCOUNTING, MANUAL |
| raw_amount | NUMERIC | Original transaction amount | Can be negative for reversals |
| currency | STRING | Transaction currency | ISO 4217 codes |
| raw_date | TIMESTAMP | Original transaction timestamp | UTC timezone |
| raw_payload | JSON | Complete API response | Full source data for audit |

#### `dev_raw.crm_contacts_raw`
**Source:** HubSpot API  
**Refresh Frequency:** Daily at 06:00 UTC  
**Owner:** Data Engineering Team  
**Business Owner:** Sales Team  

**Description:** Raw contact data from CRM system.

| Column | Type | Description | Business Rules |
|--------|------|-------------|----------------|
| contact_id | STRING | HubSpot contact ID | Primary key |
| email | STRING | Contact email address | Unique identifier |
| company_id | STRING | Associated company ID | Foreign key to companies |
| properties | JSON | All contact properties | Dynamic schema |
| created_at | TIMESTAMP | Contact creation date | UTC timezone |
| updated_at | TIMESTAMP | Last modification date | UTC timezone |

### Staging Data Layer

#### `dev_staging.financial_transactions`
**Source:** `dev_raw.financial_transactions_raw`  
**Transformation:** Data cleaning and standardization  
**Refresh Frequency:** Every 15 minutes  

**Description:** Cleaned and standardized financial transactions.

| Column | Type | Description | Data Quality Rules |
|--------|------|-------------|-------------------|
| transaction_id | STRING | Unique transaction identifier | NOT NULL, UNIQUE |
| transaction_date | DATE | Transaction date (converted to date) | NOT NULL, >= 2020-01-01 |
| business_unit | STRING | Standardized business unit | NOT NULL, IN ('Digital Products', 'Consulting', 'Innovation') |
| transaction_type | STRING | Transaction type | NOT NULL, IN ('REVENUE', 'EXPENSE', 'TRANSFER') |
| amount | NUMERIC | Amount in EUR (converted) | NOT NULL, > 0 |
| customer_id | STRING | Customer identifier | NULL for internal transactions |
| source_system | STRING | Originating system | NOT NULL |
| created_at | TIMESTAMP | Record creation timestamp | NOT NULL |

#### `dev_staging.customers`
**Source:** `dev_raw.crm_contacts_raw`  
**Transformation:** Contact deduplication and enrichment  
**Refresh Frequency:** Daily at 07:00 UTC  

**Description:** Cleaned and deduplicated customer records.

| Column | Type | Description | Data Quality Rules |
|--------|------|-------------|-------------------|
| customer_id | STRING | Unique customer identifier | NOT NULL, UNIQUE |
| customer_name | STRING | Customer company name | NOT NULL |
| email_address | STRING | Primary email (lowercase) | NOT NULL, VALID EMAIL FORMAT |
| phone_number | STRING | Standardized phone number | E.164 format |
| industry | STRING | Customer industry | Standardized industry codes |
| company_size | STRING | Employee count range | '1-10', '11-50', '51-200', '200+' |
| country | STRING | Customer country | ISO 3166-1 alpha-2 codes |
| created_date | DATE | Customer creation date | NOT NULL |
| last_updated | TIMESTAMP | Last modification timestamp | NOT NULL |

### Warehouse Data Layer

#### `dev_warehouse.financial_transactions`
**Source:** `dev_staging.financial_transactions`  
**Transformation:** Business rule application and enrichment  
**Refresh Frequency:** Every 30 minutes  
**Partitioning:** Daily by transaction_date  
**Clustering:** business_unit, transaction_type  

**Description:** Production-ready financial transaction data with business logic applied.

**Business Rules Applied:**
- Revenue recognition rules for different service types
- Currency conversion to EUR using daily rates
- Business unit mapping based on project codes
- Customer attribution for multi-touch transactions

#### `dev_warehouse.customers`
**Source:** `dev_staging.customers`  
**Transformation:** Customer master data with enrichment  
**Refresh Frequency:** Daily at 08:00 UTC  

**Description:** Single source of truth for customer information.

**Business Rules Applied:**
- Customer deduplication across email and company name
- Industry standardization using NAICS codes
- Customer tier assignment based on revenue history
- Territory assignment based on geographic rules

### Analytics Data Layer

#### `dev_analytics.monthly_revenue`
**Source:** `dev_warehouse.financial_transactions`  
**Transformation:** Monthly aggregation with KPIs  
**Refresh Frequency:** Daily at 09:00 UTC  
**Partitioning:** Monthly by month_year  

**Description:** Monthly revenue metrics by business unit.

**Key Metrics:**
- Total revenue and expenses
- Net profit and profit margin
- Customer count and average transaction value
- Growth rates (MoM, YoY)

#### `dev_analytics.customer_analytics`
**Source:** `dev_warehouse.customers`, `dev_warehouse.financial_transactions`  
**Transformation:** Customer lifetime value and segmentation  
**Refresh Frequency:** Daily at 10:00 UTC  

**Description:** Customer analytics including segmentation and lifetime value.

**Key Metrics:**
- Customer lifetime value (CLV)
- Customer acquisition cost (CAC)
- Churn risk score
- Customer segments (VIP, High Value, etc.)
- Purchase behavior patterns

#### `dev_analytics.executive_summary`
**Source:** Multiple warehouse tables  
**Transformation:** Executive-level KPIs and trends  
**Refresh Frequency:** Daily at 11:00 UTC  

**Description:** High-level business metrics for executive reporting.

**Key Metrics:**
- Revenue and growth metrics
- Customer acquisition and retention
- Project success rates
- Marketing effectiveness
- Operational efficiency indicators

## Data Lineage

### Financial Data Flow
```
ERP System API → Pub/Sub → Cloud Function → 
dev_raw.financial_transactions_raw → 
dev_staging.financial_transactions → 
dev_warehouse.financial_transactions → 
dev_analytics.monthly_revenue
```

### Customer Data Flow
```
HubSpot API → Cloud Function → 
dev_raw.crm_contacts_raw → 
dev_staging.customers → 
dev_warehouse.customers → 
dev_analytics.customer_analytics
```

## Data Quality Standards

### Completeness
- Critical fields must be 100% complete
- Important fields must be 95%+ complete
- Optional fields monitored but no threshold

### Accuracy
- Financial amounts validated against source systems
- Customer information cross-referenced with external data
- Regular reconciliation with upstream systems

### Timeliness
- Critical data: < 4 hours from source
- Important data: < 24 hours from source
- Reference data: < 7 days from source

### Consistency
- Standardized codes and formats across all datasets
- Referential integrity enforced
- Business rules consistently applied

## Access Controls

### Role-Based Access

#### Data Engineers
- Full access to all datasets
- Can modify schemas and transformations
- Responsible for data quality

#### Data Analysts
- Read access to warehouse and analytics layers
- Can create views and temporary tables
- Cannot access raw PII data

#### Finance Team
- Read access to financial datasets
- Can export data for reporting
- Access to customer revenue data

#### Executive Team
- Read access to analytics layer only
- Access to aggregated metrics
- No access to individual customer records

### Data Classification

#### Public
- Aggregated business metrics
- Industry benchmarks
- Non-sensitive operational data

#### Internal
- Customer names and company information
- Project details and budgets
- Team and resource allocation

#### Confidential
- Individual customer financial data
- Personal contact information
- Detailed transaction records

#### Restricted
- Payment information
- Authentication credentials
- Audit logs and security data

## Retention Policies

### Raw Data
- Financial transactions: 7 years (regulatory requirement)
- Customer data: 3 years after last interaction
- Marketing data: 2 years

### Processed Data
- Warehouse tables: 5 years
- Analytics aggregates: 10 years
- Audit logs: 7 years

### Backup and Archive
- Daily backups retained for 30 days
- Monthly backups retained for 1 year
- Annual archives retained for 7 years

## Change Management

### Schema Changes
1. Submit change request via GitHub PR
2. Impact assessment by data team
3. Stakeholder approval for breaking changes
4. Implementation during maintenance window
5. Documentation update required

### New Data Sources
1. Business case and requirements
2. Data quality assessment
3. Privacy and security review
4. Integration design and approval
5. Testing and validation
6. Production deployment

### Deprecation Process
1. 90-day advance notice to users
2. Migration path documentation
3. Support during transition period
4. Final removal after confirmation

## Glossary

**Business Unit:** Organizational division responsible for specific service offerings (Digital Products, Consulting, Innovation).

**Customer Lifetime Value (CLV):** Predicted total value a customer will generate over their entire relationship with ITP.

**Churn Risk Score:** Predictive score (0-100) indicating likelihood of customer churning within 90 days.

**Net Revenue Retention:** Percentage of revenue retained from existing customers, including expansion and contraction.

**Transaction Type:** Classification of financial activity (REVENUE for customer payments, EXPENSE for costs, TRANSFER for internal movements).

**Data Freshness:** Time elapsed since data was last updated from its source system.

**Partition:** Method of dividing large tables by date for improved query performance and cost optimization.

**Clustering:** Organization of table data by frequently queried columns for faster retrieval.