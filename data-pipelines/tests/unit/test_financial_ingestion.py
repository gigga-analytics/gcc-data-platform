"""
Unit tests for financial ingestion pipeline
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from ingestion.financial_systems.financial_ingestion import FinancialDataIngestion

class TestFinancialDataIngestion(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_id = "test-project"
        self.dataset_id = "test_dataset"
        
        # Mock BigQuery and Storage clients
        with patch('ingestion.financial_systems.financial_ingestion.bigquery.Client'):
            with patch('ingestion.financial_systems.financial_ingestion.storage.Client'):
                self.ingestion = FinancialDataIngestion(self.project_id, self.dataset_id)
    
    def test_extract_financial_data(self):
        """Test financial data extraction"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        result = self.ingestion.extract_financial_data("TEST_SYSTEM", start_date, end_date)
        
        # Verify DataFrame structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(len(result) > 0)
        
        # Verify required columns
        required_columns = ['transaction_id', 'transaction_date', 'business_unit', 
                          'transaction_type', 'amount', 'customer_id']
        for col in required_columns:
            self.assertIn(col, result.columns)
    
    def test_validate_data_quality_valid_data(self):
        """Test data quality validation with valid data"""
        # Create valid test data
        test_data = pd.DataFrame({
            'transaction_id': ['TXN_001', 'TXN_002'],
            'transaction_date': [datetime.now(), datetime.now()],
            'amount': [100.0, 200.0],
            'business_unit': ['Digital Products', 'Consulting'],
            'transaction_type': ['REVENUE', 'REVENUE']
        })
        
        result = self.ingestion.validate_data_quality(test_data)
        self.assertTrue(result)
    
    def test_validate_data_quality_invalid_data(self):
        """Test data quality validation with invalid data"""
        # Create invalid test data (negative amounts)
        test_data = pd.DataFrame({
            'transaction_id': ['TXN_001', 'TXN_002'],
            'transaction_date': [datetime.now(), None],  # Null date
            'amount': [100.0, -50.0],  # Negative amount
            'business_unit': ['Digital Products', 'Consulting'],
            'transaction_type': ['REVENUE', 'REVENUE']
        })
        
        result = self.ingestion.validate_data_quality(test_data)
        self.assertFalse(result)
    
    def test_validate_data_quality_duplicate_ids(self):
        """Test data quality validation with duplicate transaction IDs"""
        test_data = pd.DataFrame({
            'transaction_id': ['TXN_001', 'TXN_001'],  # Duplicate IDs
            'transaction_date': [datetime.now(), datetime.now()],
            'amount': [100.0, 200.0],
            'business_unit': ['Digital Products', 'Consulting'],
            'transaction_type': ['REVENUE', 'REVENUE']
        })
        
        result = self.ingestion.validate_data_quality(test_data)
        self.assertFalse(result)
    
    @patch('ingestion.financial_systems.financial_ingestion.bigquery.Client')
    def test_load_to_bigquery_success(self, mock_bq_client):
        """Test successful BigQuery loading"""
        # Mock successful job
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_bq_client.return_value.load_table_from_dataframe.return_value = mock_job
        
        self.ingestion.bq_client = mock_bq_client.return_value
        
        test_data = pd.DataFrame({
            'transaction_id': ['TXN_001'],
            'transaction_date': [datetime.now()],
            'amount': [100.0],
            'business_unit': ['Digital Products'],
            'transaction_type': ['REVENUE']
        })
        
        result = self.ingestion.load_to_bigquery(test_data, "test_table")
        self.assertTrue(result)
    
    @patch('ingestion.financial_systems.financial_ingestion.bigquery.Client')
    def test_load_to_bigquery_failure(self, mock_bq_client):
        """Test BigQuery loading failure"""
        # Mock failed job
        mock_bq_client.return_value.load_table_from_dataframe.side_effect = Exception("BigQuery error")
        
        self.ingestion.bq_client = mock_bq_client.return_value
        
        test_data = pd.DataFrame({
            'transaction_id': ['TXN_001'],
            'transaction_date': [datetime.now()],
            'amount': [100.0]
        })
        
        result = self.ingestion.load_to_bigquery(test_data, "test_table")
        self.assertFalse(result)
    
    @patch.object(FinancialDataIngestion, 'extract_financial_data')
    @patch.object(FinancialDataIngestion, 'validate_data_quality')
    @patch.object(FinancialDataIngestion, 'load_to_bigquery')
    def test_run_daily_ingestion_success(self, mock_load, mock_validate, mock_extract):
        """Test successful daily ingestion run"""
        # Mock successful pipeline
        mock_extract.return_value = pd.DataFrame({'test': [1, 2, 3]})
        mock_validate.return_value = True
        mock_load.return_value = True
        
        result = self.ingestion.run_daily_ingestion()
        self.assertTrue(result)
        
        # Verify methods were called
        mock_extract.assert_called_once()
        mock_validate.assert_called_once()
        mock_load.assert_called_once()
    
    @patch.object(FinancialDataIngestion, 'extract_financial_data')
    @patch.object(FinancialDataIngestion, 'validate_data_quality')
    def test_run_daily_ingestion_validation_failure(self, mock_validate, mock_extract):
        """Test daily ingestion with validation failure"""
        # Mock validation failure
        mock_extract.return_value = pd.DataFrame({'test': [1, 2, 3]})
        mock_validate.return_value = False
        
        result = self.ingestion.run_daily_ingestion()
        self.assertFalse(result)

class TestDataValidation(unittest.TestCase):
    """Test data validation utilities"""
    
    def test_amount_validation(self):
        """Test amount validation rules"""
        valid_amounts = [0.01, 100.00, 9999.99]
        invalid_amounts = [-1.00, 0.00, None]
        
        for amount in valid_amounts:
            self.assertGreater(amount, 0)
        
        for amount in invalid_amounts:
            if amount is not None:
                self.assertLessEqual(amount, 0)
    
    def test_business_unit_validation(self):
        """Test business unit validation"""
        valid_units = ['Digital Products', 'Consulting', 'Innovation']
        invalid_units = ['Unknown', '', None, 'Marketing']
        
        for unit in valid_units:
            self.assertIn(unit, ['Digital Products', 'Consulting', 'Innovation'])
        
        for unit in invalid_units:
            self.assertNotIn(unit, ['Digital Products', 'Consulting', 'Innovation'])
    
    def test_transaction_type_validation(self):
        """Test transaction type validation"""
        valid_types = ['REVENUE', 'EXPENSE', 'TRANSFER']
        invalid_types = ['CREDIT', 'DEBIT', '', None]
        
        for t_type in valid_types:
            self.assertIn(t_type, ['REVENUE', 'EXPENSE', 'TRANSFER'])
        
        for t_type in invalid_types:
            self.assertNotIn(t_type, ['REVENUE', 'EXPENSE', 'TRANSFER'])

if __name__ == '__main__':
    unittest.main()