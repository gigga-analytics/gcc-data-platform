"""
End-to-end integration tests for the data platform
"""

import unittest
import os
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

class TestEndToEndPipeline(unittest.TestCase):
    """Test complete data pipeline from ingestion to analytics"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.project_id = os.getenv('TEST_PROJECT_ID', 'itp-data-platform-dev')
        cls.dataset_id = 'test_integration'
        cls.bq_client = bigquery.Client(project=cls.project_id)
        
        # Create test dataset
        dataset = bigquery.Dataset(f"{cls.project_id}.{cls.dataset_id}")
        dataset.location = "EU"
        
        try:
            cls.bq_client.create_dataset(dataset, exists_ok=True)
        except Exception as e:
            print(f"Warning: Could not create test dataset: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        try:
            cls.bq_client.delete_dataset(
                f"{cls.project_id}.{cls.dataset_id}", 
                delete_contents=True, 
                not_found_ok=True
            )
        except Exception as e:
            print(f"Warning: Could not clean up test dataset: {e}")
    
    def test_financial_data_pipeline(self):
        """Test complete financial data pipeline"""
        
        # Step 1: Create test data
        test_data = pd.DataFrame({
            'transaction_id': ['TEST_001', 'TEST_002', 'TEST_003'],
            'transaction_date': [
                datetime.now().date(),
                datetime.now().date(),
                datetime.now().date()
            ],
            'business_unit': ['Digital Products', 'Consulting', 'Innovation'],
            'transaction_type': ['REVENUE', 'REVENUE', 'EXPENSE'],
            'amount': [1000.00, 2000.00, 500.00],
            'customer_id': ['CUST_001', 'CUST_002', None]
        })
        
        # Step 2: Load test data to BigQuery
        table_id = f"{self.project_id}.{self.dataset_id}.financial_transactions"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.bq_client.load_table_from_dataframe(
            test_data, table_id, job_config=job_config
        )
        job.result()  # Wait for job to complete
        
        # Step 3: Verify data was loaded
        query = f"SELECT COUNT(*) as row_count FROM `{table_id}`"
        result = list(self.bq_client.query(query))[0]
        self.assertEqual(result.row_count, 3)
        
        # Step 4: Test data transformations
        transform_query = f"""
        SELECT 
            business_unit,
            SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN transaction_type = 'EXPENSE' THEN amount ELSE 0 END) as total_expenses
        FROM `{table_id}`
        GROUP BY business_unit
        """
        
        results = list(self.bq_client.query(transform_query))
        
        # Verify aggregations
        revenue_totals = {row.business_unit: row.total_revenue for row in results}
        self.assertEqual(revenue_totals['Digital Products'], 1000.00)
        self.assertEqual(revenue_totals['Consulting'], 2000.00)
        
    def test_data_quality_validation(self):
        """Test data quality validation across pipeline"""
        
        # Create data with quality issues
        bad_data = pd.DataFrame({
            'transaction_id': ['TEST_001', 'TEST_001', 'TEST_003'],  # Duplicate
            'transaction_date': [
                datetime.now().date(),
                None,  # Missing date
                datetime.now().date()
            ],
            'business_unit': ['Digital Products', 'Unknown', 'Innovation'],  # Invalid unit
            'transaction_type': ['REVENUE', 'REVENUE', 'INVALID'],  # Invalid type
            'amount': [1000.00, -500.00, 0.00],  # Negative and zero amounts
            'customer_id': ['CUST_001', 'CUST_002', 'CUST_003']
        })
        
        # Load bad data
        table_id = f"{self.project_id}.{self.dataset_id}.bad_financial_data"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.bq_client.load_table_from_dataframe(
            bad_data, table_id, job_config=job_config
        )
        job.result()
        
        # Run quality checks
        quality_checks = {
            'duplicate_transactions': f"""
                SELECT transaction_id, COUNT(*) as count
                FROM `{table_id}`
                GROUP BY transaction_id
                HAVING COUNT(*) > 1
            """,
            'null_dates': f"""
                SELECT COUNT(*) as null_count
                FROM `{table_id}`
                WHERE transaction_date IS NULL
            """,
            'invalid_business_units': f"""
                SELECT COUNT(*) as invalid_count
                FROM `{table_id}`
                WHERE business_unit NOT IN ('Digital Products', 'Consulting', 'Innovation')
            """,
            'negative_amounts': f"""
                SELECT COUNT(*) as negative_count
                FROM `{table_id}`
                WHERE amount <= 0 AND transaction_type = 'REVENUE'
            """
        }
        
        # Verify quality issues are detected
        for check_name, query in quality_checks.items():
            result = list(self.bq_client.query(query))[0]
            
            if check_name == 'duplicate_transactions':
                self.assertGreater(result.count, 1)
            elif check_name == 'null_dates':
                self.assertGreater(result.null_count, 0)
            elif check_name == 'invalid_business_units':
                self.assertGreater(result.invalid_count, 0)
            elif check_name == 'negative_amounts':
                self.assertGreater(result.negative_count, 0)
    
    def test_analytics_pipeline(self):
        """Test analytics layer calculations"""
        
        # Create test data spanning multiple months
        test_data = []
        base_date = datetime(2024, 1, 1)
        
        for month in range(3):  # 3 months of data
            for day in range(1, 6):  # 5 days per month
                date = base_date.replace(month=month+1, day=day)
                test_data.extend([
                    {
                        'transaction_id': f'TXN_{month}_{day}_001',
                        'transaction_date': date.date(),
                        'business_unit': 'Digital Products',
                        'transaction_type': 'REVENUE',
                        'amount': 1000.00,
                        'customer_id': 'CUST_001'
                    },
                    {
                        'transaction_id': f'TXN_{month}_{day}_002',
                        'transaction_date': date.date(),
                        'business_unit': 'Digital Products',
                        'transaction_type': 'EXPENSE',
                        'amount': 200.00,
                        'customer_id': None
                    }
                ])
        
        df = pd.DataFrame(test_data)
        
        # Load to BigQuery
        table_id = f"{self.project_id}.{self.dataset_id}.analytics_test_data"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.bq_client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()
        
        # Test monthly aggregation
        monthly_query = f"""
        SELECT 
            DATE_TRUNC(transaction_date, MONTH) as month_year,
            business_unit,
            SUM(CASE WHEN transaction_type = 'REVENUE' THEN amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN transaction_type = 'EXPENSE' THEN amount ELSE 0 END) as total_expenses,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM `{table_id}`
        WHERE customer_id IS NOT NULL OR transaction_type = 'EXPENSE'
        GROUP BY month_year, business_unit
        ORDER BY month_year
        """
        
        results = list(self.bq_client.query(monthly_query))
        
        # Verify calculations
        for result in results:
            # Each month should have 5 revenue transactions of 1000 each = 5000
            self.assertEqual(result.total_revenue, 5000.00)
            # Each month should have 5 expense transactions of 200 each = 1000
            self.assertEqual(result.total_expenses, 1000.00)
            # Should have 1 unique customer per month
            self.assertEqual(result.unique_customers, 1)

class TestDataPipelineMonitoring(unittest.TestCase):
    """Test monitoring and alerting functionality"""
    
    def setUp(self):
        self.project_id = os.getenv('TEST_PROJECT_ID', 'itp-data-platform-dev')
        self.bq_client = bigquery.Client(project=self.project_id)
    
    def test_data_freshness_monitoring(self):
        """Test data freshness monitoring query"""
        
        # This would typically check against real tables
        # For testing, we'll verify the query structure
        freshness_query = """
        SELECT 
            'financial_transactions' as table_name,
            MAX(transaction_date) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(transaction_date), DAY) as days_delay
        FROM `itp-data-platform-dev.warehouse.financial_transactions`
        """
        
        # Verify query is valid (doesn't test actual freshness)
        try:
            job = self.bq_client.query(freshness_query)
            # Don't execute in test, just validate syntax
            job.dry_run = True
            job.result()
            syntax_valid = True
        except Exception:
            syntax_valid = False
        
        self.assertTrue(syntax_valid)
    
    def test_cost_monitoring(self):
        """Test cost monitoring calculations"""
        
        cost_query = """
        SELECT 
            DATE_TRUNC(creation_time, DAY) as date,
            SUM(total_bytes_processed) / 1024 / 1024 / 1024 / 1024 as tb_processed,
            COUNT(*) as job_count
        FROM `{project}.region-eu.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        AND statement_type = 'SELECT'
        GROUP BY date
        ORDER BY date DESC
        """.format(project=self.project_id)
        
        # Verify query syntax
        try:
            job = self.bq_client.query(cost_query)
            job.dry_run = True
            job.result()
            syntax_valid = True
        except Exception:
            syntax_valid = False
        
        self.assertTrue(syntax_valid)

if __name__ == '__main__':
    # Set up test environment variables
    if not os.getenv('TEST_PROJECT_ID'):
        print("Warning: TEST_PROJECT_ID not set, using default")
    
    unittest.main()