# Data Analyst User Guide

## Overview
This guide helps data analysts navigate and use the In The Pocket data platform effectively.

## Accessing Data

### BigQuery Access
1. Navigate to BigQuery console
2. Available datasets:
   - `dev_warehouse`: Main analytical data
   - `dev_staging`: Intermediate processing data
   - `dev_analytics`: Pre-built analytical models

### Key Tables
- `financial_transactions`: Raw financial data
- `monthly_revenue`: Aggregated monthly revenue metrics
- `customer_analytics`: Customer behavior metrics

## Common Queries

### Monthly Revenue by Business Unit
```sql
SELECT 
    month_year,
    business_unit,
    total_revenue,
    total_expenses,
    net_profit
FROM `itp-data-platform-dev.dev_marts.monthly_revenue`
WHERE month_year >= '2024-01-01'
ORDER BY month_year DESC, total_revenue DESC
```

### Customer Metrics
```sql
SELECT 
    customer_id,
    COUNT(*) as transaction_count,
    SUM(amount) as total_spent,
    AVG(amount) as avg_transaction_value
FROM `itp-data-platform-dev.dev_warehouse.financial_transactions`
WHERE transaction_type = 'REVENUE'
GROUP BY customer_id
ORDER BY total_spent DESC
```

## Best Practices
1. Always use partitioned tables for time-based queries
2. Use clustering columns for frequently filtered dimensions
3. Limit result sets with appropriate WHERE clauses
4. Use LIMIT for exploratory analysis

## Getting Help
- Contact: data-engineering@inthepocket.com
- Slack: #data-platform
- Documentation: [Internal Wiki Link]
