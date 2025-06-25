{{ config(
    materialized='table',
    cluster_by=['customer_segment', 'business_unit']
) }}

WITH customer_transactions AS (
    SELECT
        customer_id,
        business_unit,
        MIN(transaction_date) as first_transaction_date,
        MAX(transaction_date) as last_transaction_date,
        COUNT(*) as total_transactions,
        SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as total_revenue,
        AVG(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE NULL END) as avg_transaction_value,
        COUNT(DISTINCT DATE_TRUNC(transaction_date, MONTH)) as active_months,
        DATE_DIFF(CURRENT_DATE(), MAX(transaction_date), DAY) as days_since_last_transaction
    FROM {{ ref('int_financial_transactions') }}
    WHERE customer_id IS NOT NULL
    GROUP BY 1, 2
),

customer_projects AS (
    SELECT
        customer_id,
        COUNT(*) as total_projects,
        SUM(project_budget) as total_project_budget,
        AVG(project_budget) as avg_project_budget,
        MIN(project_start_date) as first_project_date,
        MAX(project_start_date) as last_project_date,
        COUNT(CASE WHEN project_status = 'COMPLETED' THEN 1 END) as completed_projects,
        COUNT(CASE WHEN project_status = 'ACTIVE' THEN 1 END) as active_projects
    FROM {{ ref('stg_projects') }}
    GROUP BY 1
),

customer_base AS (
    SELECT
        customer_id,
        customer_name,
        email_address,
        created_date,
        last_updated
    FROM {{ ref('stg_customers') }}
),

customer_metrics AS (
    SELECT
        cb.customer_id,
        cb.customer_name,
        cb.email_address,
        cb.created_date,
        cb.last_updated,
        ct.business_unit,
        
        -- Transaction metrics
        COALESCE(ct.total_transactions, 0) as total_transactions,
        COALESCE(ct.total_revenue, 0) as total_revenue,
        COALESCE(ct.avg_transaction_value, 0) as avg_transaction_value,
        ct.first_transaction_date,
        ct.last_transaction_date,
        COALESCE(ct.active_months, 0) as active_months,
        COALESCE(ct.days_since_last_transaction, 9999) as days_since_last_transaction,
        
        -- Project metrics
        COALESCE(cp.total_projects, 0) as total_projects,
        COALESCE(cp.total_project_budget, 0) as total_project_budget,
        COALESCE(cp.avg_project_budget, 0) as avg_project_budget,
        cp.first_project_date,
        cp.last_project_date,
        COALESCE(cp.completed_projects, 0) as completed_projects,
        COALESCE(cp.active_projects, 0) as active_projects,
        
        -- Derived metrics
        DATE_DIFF(CURRENT_DATE(), cb.created_date, DAY) as customer_age_days,
        CASE 
            WHEN ct.last_transaction_date IS NOT NULL 
            THEN DATE_DIFF(ct.last_transaction_date, ct.first_transaction_date, DAY)
            ELSE 0
        END as customer_lifetime_days,
        
        CASE 
            WHEN ct.active_months > 0 
            THEN ct.total_revenue / ct.active_months
            ELSE 0
        END as monthly_revenue,
        
        CASE 
            WHEN cp.total_projects > 0 
            

        