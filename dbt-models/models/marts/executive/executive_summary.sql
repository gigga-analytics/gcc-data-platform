{{ config(
    materialized='table',
    partition_by={'field': 'month_year', 'data_type': 'date'},
    cluster_by=['business_unit']
) }}

WITH financial_metrics AS (
    SELECT
        month_year,
        business_unit,
        total_revenue,
        total_expenses,
        net_profit,
        unique_customers,
        revenue_transactions
    FROM {{ ref('monthly_revenue') }}
),

customer_metrics AS (
    SELECT
        DATE_TRUNC(created_date, MONTH) as month_year,
        COUNT(DISTINCT customer_id) as new_customers,
        COUNT(DISTINCT CASE WHEN last_updated > created_date THEN customer_id END) as returning_customers
    FROM {{ ref('stg_customers') }}
    GROUP BY 1
),

project_metrics AS (
    SELECT
        DATE_TRUNC(project_start_date, MONTH) as month_year,
        COUNT(*) as new_projects,
        SUM(project_budget) as total_project_budget,
        AVG(project_budget) as avg_project_budget,
        COUNT(CASE WHEN project_status = 'COMPLETED' THEN 1 END) as completed_projects
    FROM {{ ref('stg_projects') }}
    GROUP BY 1
),

marketing_metrics AS (
    SELECT
        DATE_TRUNC(date, MONTH) as month_year,
        SUM(sessions) as total_sessions,
        SUM(users) as total_users,
        SUM(conversions) as total_conversions,
        AVG(bounce_rate) as avg_bounce_rate
    FROM {{ ref('stg_google_analytics') }}
    GROUP BY 1
),

social_metrics AS (
    SELECT
        DATE_TRUNC(date, MONTH) as month_year,
        SUM(impressions) as total_impressions,
        SUM(engagements) as total_engagements,
        AVG(impressions) as avg_daily_impressions
    FROM {{ ref('stg_social_media') }}
    GROUP BY 1
)

SELECT
    f.month_year,
    f.business_unit,
    
    -- Financial KPIs
    f.total_revenue,
    f.total_expenses,
    f.net_profit,
    SAFE_DIVIDE(f.net_profit, f.total_revenue) as profit_margin,
    f.revenue_transactions,
    SAFE_DIVIDE(f.total_revenue, f.revenue_transactions) as avg_revenue_per_transaction,
    
    -- Customer KPIs
    f.unique_customers,
    c.new_customers,
    c.returning_customers,
    SAFE_DIVIDE(f.total_revenue, f.unique_customers) as revenue_per_customer,
    
    -- Project KPIs
    p.new_projects,
    p.total_project_budget,
    p.avg_project_budget,
    p.completed_projects,
    SAFE_DIVIDE(p.completed_projects, p.new_projects) as project_completion_rate,
    
    -- Marketing KPIs
    m.total_sessions,
    m.total_users,
    m.total_conversions,
    SAFE_DIVIDE(m.total_conversions, m.total_sessions) as conversion_rate,
    m.avg_bounce_rate,
    
    -- Social Media KPIs
    s.total_impressions,
    s.total_engagements,
    SAFE_DIVIDE(s.total_engagements, s.total_impressions) as engagement_rate,
    s.avg_daily_impressions,
    
    -- Growth Metrics (MoM)
    LAG(f.total_revenue) OVER (PARTITION BY f.business_unit ORDER BY f.month_year) as prev_month_revenue,
    SAFE_DIVIDE(
        f.total_revenue - LAG(f.total_revenue) OVER (PARTITION BY f.business_unit ORDER BY f.month_year),
        LAG(f.total_revenue) OVER (PARTITION BY f.business_unit ORDER BY f.month_year)
    ) as revenue_growth_rate,
    
    LAG(f.unique_customers) OVER (PARTITION BY f.business_unit ORDER BY f.month_year) as prev_month_customers,
    SAFE_DIVIDE(
        f.unique_customers - LAG(f.unique_customers) OVER (PARTITION BY f.business_unit ORDER BY f.month_year),
        LAG(f.unique_customers) OVER (PARTITION BY f.business_unit ORDER BY f.month_year)
    ) as customer_growth_rate,
    
    CURRENT_TIMESTAMP() as updated_at

FROM financial_metrics f
LEFT JOIN customer_metrics c ON f.month_year = c.month_year
LEFT JOIN project_metrics p ON f.month_year = p.month_year
LEFT JOIN marketing_metrics m ON f.month_year = m.month_year
LEFT JOIN social_metrics s ON f.month_year = s.month_year
WHERE f.month_year >= '2023-01-01'