{{ config(
    materialized='table',
    partition_by={'field': 'month_year', 'data_type': 'date'},
    cluster_by=['business_unit']
) }}

SELECT
    month_year,
    business_unit,
    SUM(revenue_amount) as total_revenue,
    SUM(expense_amount) as total_expenses,
    SUM(revenue_amount) - SUM(expense_amount) as net_profit,
    COUNT(DISTINCT CASE WHEN transaction_type = 'REVENUE' THEN transaction_id END) as revenue_transactions,
    COUNT(DISTINCT CASE WHEN transaction_type = 'EXPENSE' THEN transaction_id END) as expense_transactions,
    COUNT(DISTINCT customer_id) as unique_customers,
    AVG(CASE WHEN transaction_type = 'REVENUE' THEN amount END) as avg_revenue_per_transaction,
    CURRENT_TIMESTAMP() as updated_at
FROM {{ ref('int_financial_transactions') }}
GROUP BY 1, 2