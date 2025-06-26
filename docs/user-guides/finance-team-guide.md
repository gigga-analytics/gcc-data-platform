# Finance Team User Guide

## Overview
This guide provides the finance team with comprehensive instructions for accessing, analyzing, and reporting on financial data within the ITP Data Platform.

## Quick Start

### Daily Tasks
1. **Morning Data Check** (09:00)
   - Verify data freshness
   - Review overnight transactions
   - Check for anomalies or errors

2. **Revenue Recognition** (10:00)
   - Process daily transactions
   - Apply revenue recognition rules
   - Update monthly forecasts

3. **Reporting Preparation** (16:00)
   - Prepare daily flash reports
   - Update executive dashboards
   - Respond to ad-hoc requests

### Weekly Tasks
- Monthly closing preparation
- Budget vs. actual analysis
- Customer credit assessments
- Vendor payment processing

## Data Access and Navigation

### BigQuery Console Access
**URL:** https://console.cloud.google.com/bigquery  
**Project:** itp-data-platform-[environment]  

### Key Datasets
- **`warehouse`:** Production financial data
- **`analytics`:** Pre-built financial reports
- **`staging`:** Data quality validation

### Essential Tables

#### Financial Transactions
```sql
SELECT 
    transaction_date,
    business_unit,
    transaction_type,
    amount,
    customer_id,
    description
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE transaction_date >= '2024-01-01'
ORDER BY transaction_date DESC
```

#### Monthly Revenue Summary
```sql
SELECT 
    month_year,
    business_unit,
    total_revenue,
    total_expenses,
    net_profit,
    profit_margin
FROM `itp-data-platform-prod.analytics.monthly_revenue`
WHERE month_year >= '2024-01-01'
ORDER BY month_year DESC, business_unit
```

## Common Financial Reports

### 1. Daily Flash Report

#### Revenue by Business Unit
```sql
SELECT 
    business_unit,
    SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as daily_revenue,
    COUNT(DISTINCT customer_id) as customers_transacted,
    AVG(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE NULL END) as avg_transaction
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE transaction_date = CURRENT_DATE()
GROUP BY business_unit
ORDER BY daily_revenue DESC
```

#### Daily Revenue Trend (Last 30 Days)
```sql
SELECT 
    transaction_date,
    SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as daily_revenue,
    AVG(SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END)) 
        OVER (ORDER BY transaction_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as rolling_7day_avg
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY transaction_date
ORDER BY transaction_date
```

### 2. Monthly Financial Package

#### P&L Summary
```sql
SELECT 
    DATE_TRUNC(transaction_date, MONTH) as month,
    SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as revenue,
    SUM(CASE WHEN transaction_type = 'EXPENSE' THEN amount ELSE 0 END) as expenses,
    SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount 
             WHEN transaction_type = 'EXPENSE' THEN -amount 
             ELSE 0 END) as net_profit
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE transaction_date >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH), MONTH)
GROUP BY month
ORDER BY month DESC
```

#### Customer Revenue Analysis
```sql
SELECT 
    c.customer_name,
    c.industry,
    SUM(CASE WHEN t.transaction_type = 'REVENUE' THEN t.amount ELSE 0 END) as total_revenue,
    COUNT(DISTINCT DATE_TRUNC(t.transaction_date, MONTH)) as active_months,
    MIN(t.transaction_date) as first_transaction,
    MAX(t.transaction_date) as last_transaction
FROM `itp-data-platform-prod.warehouse.financial_transactions` t
JOIN `itp-data-platform-prod.warehouse.customers` c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
GROUP BY c.customer_name, c.industry
HAVING total_revenue > 10000
ORDER BY total_revenue DESC
```

### 3. Budget vs. Actual Reports

#### Monthly Budget Variance
```sql
WITH actual_revenue AS (
    SELECT 
        DATE_TRUNC(transaction_date, MONTH) as month,
        business_unit,
        SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as actual
    FROM `itp-data-platform-prod.warehouse.financial_transactions`
    GROUP BY month, business_unit
),
budget_data AS (
    SELECT 
        month,
        business_unit,
        budgeted_revenue as budget
    FROM `itp-data-platform-prod.analytics.budget_targets`
)
SELECT 
    a.month,
    a.business_unit,
    a.actual,
    b.budget,
    a.actual - b.budget as variance,
    SAFE_DIVIDE(a.actual - b.budget, b.budget) * 100 as variance_percent
FROM actual_revenue a
LEFT JOIN budget_data b ON a.month = b.month AND a.business_unit = b.business_unit
WHERE a.month >= DATE_TRUNC(CURRENT_DATE(), YEAR)
ORDER BY a.month DESC, a.business_unit
```

## Revenue Recognition

### Subscription Revenue
```sql
-- Monthly recurring revenue calculation
SELECT 
    customer_id,
    subscription_start_date,
    subscription_end_date,
    monthly_amount,
    DATE_DIFF(subscription_end_date, subscription_start_date, MONTH) as contract_months,
    monthly_amount * DATE_DIFF(subscription_end_date, subscription_start_date, MONTH) as total_contract_value
FROM `itp-data-platform-prod.warehouse.subscriptions`
WHERE subscription_status = 'ACTIVE'
```

### Project Revenue Recognition
```sql
-- Percentage of completion method
SELECT 
    p.project_id,
    p.project_name,
    p.total_budget,
    SUM(t.hours_worked) as total_hours,
    p.estimated_hours,
    SAFE_DIVIDE(SUM(t.hours_worked), p.estimated_hours) as completion_percentage,
    p.total_budget * SAFE_DIVIDE(SUM(t.hours_worked), p.estimated_hours) as recognized_revenue
FROM `itp-data-platform-prod.warehouse.projects` p
LEFT JOIN `itp-data-platform-prod.warehouse.timesheets` t ON p.project_id = t.project_id
WHERE p.project_status IN ('ACTIVE', 'COMPLETED')
GROUP BY p.project_id, p.project_name, p.total_budget, p.estimated_hours
```

## Cash Flow Analysis

### Accounts Receivable Aging
```sql
SELECT 
    customer_name,
    invoice_date,
    due_date,
    amount,
    CURRENT_DATE() as today,
    DATE_DIFF(CURRENT_DATE(), due_date, DAY) as days_overdue,
    CASE 
        WHEN DATE_DIFF(CURRENT_DATE(), due_date, DAY) <= 0 THEN 'Current'
        WHEN DATE_DIFF(CURRENT_DATE(), due_date, DAY) <= 30 THEN '1-30 days'
        WHEN DATE_DIFF(CURRENT_DATE(), due_date, DAY) <= 60 THEN '31-60 days'
        WHEN DATE_DIFF(CURRENT_DATE(), due_date, DAY) <= 90 THEN '61-90 days'
        ELSE '90+ days'
    END as aging_bucket
FROM `itp-data-platform-prod.warehouse.invoices`
WHERE payment_status = 'OUTSTANDING'
ORDER BY days_overdue DESC
```

### Monthly Cash Flow Forecast
```sql
WITH monthly_inflows AS (
    SELECT 
        DATE_TRUNC(expected_payment_date, MONTH) as month,
        SUM(amount) as expected_receipts
    FROM `itp-data-platform-prod.warehouse.invoices`
    WHERE payment_status = 'OUTSTANDING'
    GROUP BY month
),
monthly_outflows AS (
    SELECT 
        DATE_TRUNC(due_date, MONTH) as month,
        SUM(amount) as expected_payments
    FROM `itp-data-platform-prod.warehouse.payables`
    WHERE payment_status = 'PENDING'
    GROUP BY month
)
SELECT 
    COALESCE(i.month, o.month) as month,
    COALESCE(i.expected_receipts, 0) as inflows,
    COALESCE(o.expected_payments, 0) as outflows,
    COALESCE(i.expected_receipts, 0) - COALESCE(o.expected_payments, 0) as net_cash_flow
FROM monthly_inflows i
FULL OUTER JOIN monthly_outflows o ON i.month = o.month
WHERE COALESCE(i.month, o.month) >= DATE_TRUNC(CURRENT_DATE(), MONTH)
ORDER BY month
```

## Cost Management

### Expense Analysis by Category
```sql
SELECT 
    expense_category,
    DATE_TRUNC(transaction_date, MONTH) as month,
    SUM(amount) as total_expenses,
    COUNT(*) as transaction_count,
    AVG(amount) as avg_expense
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE transaction_type = 'EXPENSE'
AND transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
GROUP BY expense_category, month
ORDER BY month DESC, total_expenses DESC
```

### Vendor Spend Analysis
```sql
SELECT 
    vendor_name,
    COUNT(*) as transactions,
    SUM(amount) as total_spend,
    AVG(amount) as avg_transaction,
    MIN(transaction_date) as first_transaction,
    MAX(transaction_date) as last_transaction
FROM `itp-data-platform-prod.warehouse.financial_transactions` t
JOIN `itp-data-platform-prod.warehouse.vendors` v ON t.vendor_id = v.vendor_id
WHERE t.transaction_type = 'EXPENSE'
AND t.transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
GROUP BY vendor_name
HAVING total_spend > 5000
ORDER BY total_spend DESC
```

## Key Performance Indicators

### Financial Health Metrics
```sql
-- Key financial ratios and metrics
WITH monthly_metrics AS (
    SELECT 
        DATE_TRUNC(transaction_date, MONTH) as month,
        SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as revenue,
        SUM(CASE WHEN transaction_type = 'EXPENSE' THEN amount ELSE 0 END) as expenses
    FROM `itp-data-platform-prod.warehouse.financial_transactions`
    GROUP BY month
)
SELECT 
    month,
    revenue,
    expenses,
    revenue - expenses as net_profit,
    SAFE_DIVIDE(revenue - expenses, revenue) * 100 as profit_margin_percent,
    LAG(revenue) OVER (ORDER BY month) as prev_month_revenue,
    SAFE_DIVIDE(revenue - LAG(revenue) OVER (ORDER BY month), 
                LAG(revenue) OVER (ORDER BY month)) * 100 as revenue_growth_percent
FROM monthly_metrics
WHERE month >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
ORDER BY month DESC
```

## Data Quality and Validation

### Daily Data Quality Checks
```sql
-- Run these queries daily to ensure data integrity

-- 1. Check for missing transaction dates
SELECT COUNT(*) as records_with_null_dates
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE transaction_date IS NULL;

-- 2. Check for negative revenue amounts
SELECT COUNT(*) as negative_revenue_records
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE transaction_type = 'REVENUE' AND amount < 0;

-- 3. Check for duplicate transactions
SELECT 
    transaction_id,
    COUNT(*) as duplicate_count
FROM `itp-data-platform-prod.warehouse.financial_transactions`
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- 4. Verify data freshness
SELECT 
    MAX(transaction_date) as latest_transaction,
    DATE_DIFF(CURRENT_DATE(), MAX(transaction_date), DAY) as days_behind
FROM `itp-data-platform-prod.warehouse.financial_transactions`;
```

### Reconciliation Queries
```sql
-- Monthly reconciliation with source systems
SELECT 
    'BigQuery' as source,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as total_revenue
FROM `itp-data-platform-prod.warehouse.financial_transactions`
WHERE DATE_TRUNC(transaction_date, MONTH) = DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH)

UNION ALL

SELECT 
    'ERP System' as source,
    -- Add actual ERP reconciliation data here
    0 as transaction_count,
    0 as total_revenue;
```

## Troubleshooting Common Issues

### Data Discrepancies
**Problem:** Numbers don't match between systems  
**Solution:**
1. Check data freshness indicators
2. Verify currency conversion rates
3. Confirm time zone handling
4. Review business rule applications

### Missing Transactions
**Problem:** Expected transactions not appearing  
**Solution:**
1. Check source system API connectivity
2. Review pipeline logs for errors
3. Verify customer ID mapping
4. Contact data engineering team

### Performance Issues
**Problem:** Queries running slowly  
**Solution:**
1. Add date range filters to queries
2. Use partition columns in WHERE clauses
3. Limit result sets with appropriate filters
4. Contact data team for query optimization

## Reporting Calendar

### Daily Reports (Due by 10:00 AM)
- Daily flash revenue report
- Cash position update
- Accounts receivable status

### Weekly Reports (Due Monday by 2:00 PM)
- Weekly P&L summary
- Budget variance analysis
- Customer payment status

### Monthly Reports (Due by 5th business day)
- Complete financial package
- Customer revenue analysis
- Vendor spend summary
- Cash flow forecast

### Quarterly Reports (Due by 10th business day)
- Comprehensive financial review
- Customer lifetime value analysis
- Profitability by business unit
- Annual budget planning

## Emergency Procedures

### Data Issues
1. **Immediate:** Note the issue and time discovered
2. **Assessment:** Determine impact on critical reports
3. **Communication:** Inform stakeholders of potential delays
4. **Escalation:** Contact data engineering team
5. **Workaround:** Use manual processes if needed

### System Outages
1. **Backup Access:** Use read-only financial system
2. **Manual Processes:** Activate emergency procedures
3. **Communication:** Update leadership on status
4. **Recovery:** Resume normal operations when systems restored

## Contact Information

### Data Engineering Support
- **Email:** data-engineering@inthepocket.com
- **Slack:** #data-platform
- **Emergency:** +32 XXX XXX XXX

### Finance Team
- **Finance Director:** finance-director@inthepocket.com
- **Accounts Receivable:** ar@inthepocket.com
- **Accounts Payable:** ap@inthepocket.com

### IT Support
- **General Support:** support@inthepocket.com
- **Database Issues:** dba@inthepocket.com
- **Emergency IT:** emergency-it@inthepocket.com
