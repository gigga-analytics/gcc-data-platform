{{ config(
    materialized='view'
) }}

SELECT
    transaction_id,
    CAST(transaction_date AS DATE) as transaction_date,
    business_unit,
    transaction_type,
    CAST(amount AS NUMERIC) as amount,
    customer_id,
    CURRENT_TIMESTAMP() as loaded_at
FROM {{ source('warehouse', 'financial_transactions') }}
WHERE transaction_date >= '{{ var("start_date") }}'
  AND transaction_date <= '{{ var("end_date") }}'