"""
Tests for data quality framework
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from utils.data_quality import DataQualityFramework

class TestDataQualityFramework(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_id = "test-project"
        
        with patch('utils.data_quality.bigquery.Client'):
            self.dq_framework = DataQualityFramework(self.project_id)
    
    @patch('utils.data_quality.bigquery.Client')
    def test_check_completeness(self, mock_bq_client):
        """Test completeness checking functionality"""
        
        # Mock BigQuery response
        mock_result = Mock()
        mock_result.total_rows = 1000
        mock_result.column1_nulls = 50
        mock_result.column2_nulls = 0
        
        mock_bq_client.return_value.query.return_value = [mock_result]
        self.dq_framework.client = mock_bq_client.return_value
        
        # Test completeness check
        result = self.dq_framework.check_completeness(
            "test_dataset", 
            "test_table", 
            ["column1", "column2"]
        )
        
        # Verify results
        self.assertEqual(result['total_rows'], 1000)
        self.assertEqual(result['completeness_scores']['column1'], 0.95)  # 950/1000
        self.assertEqual(result['completeness_scores']['column2'], 1.0)   # 1000/1000
        self.assertEqual(result['overall_score'], 0.975)  # Average of 0.95 and 1.0
    
    @patch('utils.data_quality.bigquery.Client')
    def test_check_uniqueness(self, mock_bq_client):
        """Test uniqueness checking functionality"""
        
        # Mock BigQuery responses for different columns
        mock_results = {
            'column1': Mock(total_rows=1000, unique_values=950),  # Some duplicates
            'column2': Mock(total_rows=1000, unique_values=1000)  # All unique
        }
        
        def mock_query(query):
            if 'column1' in query:
                return [mock_results['column1']]
            elif 'column2' in query:
                return [mock_results['column2']]
            return []
        
        mock_bq_client.return_value.query.side_effect = mock_query
        self.dq_framework.client = mock_bq_client.return_value
        
        # Test uniqueness check
        result = self.dq_framework.check_uniqueness(
            "test_dataset", 
            "test_table", 
            ["column1", "column2"]
        )
        
        # Verify results
        self.assertEqual(result['column1']['uniqueness_score'], 0.95)
        self.assertEqual(result['column2']['uniqueness_score'], 1.0)
    
    @patch('utils.data_quality.bigquery.Client')
    def test_check_timeliness(self, mock_bq_client):
        """Test timeliness checking functionality"""
        
        # Mock BigQuery response
        mock_result = Mock()
        mock_result.latest_date = "2024-01-15 10:00:00"
        mock_result.hours_delay = 12
        
        mock_bq_client.return_value.query.return_value = [mock_result]
        self.dq_framework.client = mock_bq_client.return_value
        
        # Test timeliness check
        result = self.dq_framework.check_timeliness(
            "test_dataset", 
            "test_table", 
            "created_date",
            max_delay_hours=24
        )
        
        # Verify results
        self.assertEqual(result['hours_delay'], 12)
        self.assertTrue(result['is_timely'])  # 12 hours < 24 hours
    
    @patch('utils.data_quality.bigquery.Client')
    def test_execute_quality_suite(self, mock_bq_client):
        """Test complete quality suite execution"""
        
        # Mock different check results
        def mock_query(query):
            if 'COUNT(*)' in query and 'NULL' in query:
                # Completeness query
                result = Mock()
                result.total_rows = 1000
                result.id_nulls = 0
                result.name_nulls = 10
                return [result]
            elif 'COUNT(DISTINCT' in query:
                # Uniqueness query  
                result = Mock()
                result.total_rows = 1000
                result.unique_values = 990
                return [result]
            elif 'MAX(' in query and 'DATETIME_DIFF' in query:
                # Timeliness query
                result = Mock()
                result.latest_date = "2024-01-15 10:00:00"
                result.hours_delay = 6
                return [result]
            return []
        
        mock_bq_client.return_value.query.side_effect = mock_query
        self.dq_framework.client = mock_bq_client.return_value
        
        # Configure quality checks
        config = {
            'required_columns': ['id', 'name'],
            'unique_columns': ['id'],
            'date_column': 'created_date',
            'max_delay_hours': 24
        }
        
        # Execute quality suite
        result = self.dq_framework.execute_quality_suite(
            "test_dataset", 
            "test_table", 
            config
        )
        
        # Verify overall structure
        self.assertIn('completeness', result)
        self.assertIn('uniqueness', result)
        self.assertIn('timeliness', result)
        self.assertIn('overall_quality_score', result)
        
        # Verify overall score calculation
        self.assertGreater(result['overall_quality_score'], 0.8)
        self.assertLessEqual(result['overall_quality_score'], 1.0)

class TestDataQualityRules(unittest.TestCase):
    """Test specific data quality rules and validations"""
    
    def test_financial_amount_validation(self):
        """Test financial amount validation rules"""
        
        # Valid amounts
        valid_amounts = [0.01, 100.00, 9999.99, 0.1]
        for amount in valid_amounts:
            self.assertGreater(amount, 0)
            self.assertIsInstance(amount, (int, float))
        
        # Invalid amounts for revenue transactions
        invalid_revenue_amounts = [-100.00, 0.00, None]
        for amount in invalid_revenue_amounts:
            if amount is not None:
                self.assertLessEqual(amount, 0)
    
    def test_date_validation(self):
        """Test date validation rules"""
        from datetime import datetime, date
        
        # Valid dates
        valid_dates = [
            datetime.now().date(),
            date(2024, 1, 1),
            date(2023, 12, 31)
        ]
        
        for test_date in valid_dates:
            self.assertIsInstance(test_date, date)
            self.assertGreaterEqual(test_date, date(2020, 1, 1))  # Reasonable minimum
            self.assertLessEqual(test_date, datetime.now().date())  # Not in future
    
    def test_customer_id_validation(self):
        """Test customer ID validation rules"""
        
        # Valid customer IDs
        valid_ids = ['CUST_001', 'CUST_9999', 'ENTERPRISE_001']
        for cid in valid_ids:
            self.assertIsInstance(cid, str)
            self.assertTrue(len(cid) >= 6)  # Minimum length
            self.assertTrue(cid.startswith(('CUST_', 'ENTERPRISE_')))
        
        # Invalid customer IDs
        invalid_ids = ['', '123', 'INVALID', None]
        for cid in invalid_ids:
            if cid is not None:
                self.assertFalse(
                    len(cid) >= 6 and cid.startswith(('CUST_', 'ENTERPRISE_'))
                )

class TestDataQualityIntegration(unittest.TestCase):
    """Integration tests for data quality framework"""
    
    @patch('utils.data_quality.bigquery.Client')
    def test_real_world_scenario(self, mock_bq_client):
        """Test realistic data quality scenario"""
        
        with patch('utils.data_quality.bigquery.Client'):
            dq_framework = DataQualityFramework("test-project")
        
        # Simulate realistic data quality issues
        def mock_quality_query(query):
            if 'completeness' in query.lower():
                # 95% completeness
                result = Mock()
                result.total_rows = 10000
                result.customer_id_nulls = 500  # 5% null
                result.amount_nulls = 0
                return [result]
            elif 'uniqueness' in query.lower():
                # 99% uniqueness  
                result = Mock()
                result.total_rows = 10000
                result.unique_values = 9900
                return [result]
            elif 'timeliness' in query.lower():
                # 8 hours delay
                result = Mock()
                result.latest_date = "2024-01-15 02:00:00"
                result.hours_delay = 8
                return [result]
            return []
        
        mock_bq_client.return_value.query.side_effect = mock_quality_query
        dq_framework.client = mock_bq_client.return_value
        
        # Define realistic quality checks
        config = {
            'required_columns': ['customer_id', 'amount'],
            'unique_columns': ['transaction_id'],
            'date_column': 'transaction_date',
            'max_delay_hours': 12
        }
        
        # Execute quality suite
        result = dq_framework.execute_quality_suite(
            "warehouse", 
            "financial_transactions", 
            config
        )
        
        # Verify realistic expectations
        self.assertGreater(result['overall_quality_score'], 0.85)  # Good but not perfect
        self.assertLess(result['overall_quality_score'], 1.0)      # Has some issues
        
        # Check individual components
        self.assertGreater(result['completeness']['overall_score'], 0.9)
        self.assertTrue(result['timeliness']['is_timely'])

if __name__ == '__main__':
    unittest.main()