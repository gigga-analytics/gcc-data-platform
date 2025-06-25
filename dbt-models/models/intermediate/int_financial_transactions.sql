{{ config(
    materialized='view'
) }}

SELECT
    transaction_id,
    transaction_date,
    business_unit,
    transaction_type,
    amount,
    customer_id,
    EXTRACT(YEAR FROM transaction_date) as transaction_year,
    EXTRACT(MONTH FROM transaction_date) as transaction_month,
    DATE_TRUNC(transaction_date, MONTH) as month_year,
    DATE_TRUNC(transaction_date, QUARTER) as quarter_year,
    CASE 
        WHEN transaction_type = 'REVENUE' THEN amount
        ELSE 0
    END as revenue_amount,
    CASE 
        WHEN transaction_type = 'EXPENSE' THEN amount
        ELSE 0
    END as expense_amount
FROM {{ ref('stg_financial_transactions') }}