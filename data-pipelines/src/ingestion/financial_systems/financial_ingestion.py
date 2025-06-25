"""
Financial Systems Data Ingestion Pipeline
Handles extraction and loading of financial data from various sources
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound
import pandas as pd

class FinancialDataIngestion:
    """Main class for financial data ingestion"""
    
    def __init__(self, project_id: str, dataset_id: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.bq_client = bigquery.Client(project=project_id)
        self.storage_client = storage.Client(project=project_id)
        self.logger = logging.getLogger(__name__)
        
    def extract_financial_data(self, source_system: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Extract financial data from source system"""
        self.logger.info(f"Extracting financial data from {source_system} for {start_date} to {end_date}")
        
        # Mock data extraction - replace with actual API calls
        mock_data = {
            'transaction_id': [f'TXN_{i:06d}' for i in range(1000)],
            'transaction_date': pd.date_range(start_date, end_date, periods=1000),
            'business_unit': ['Digital Products', 'Consulting', 'Innovation'] * 334,
            'transaction_type': ['REVENUE', 'EXPENSE'] * 500,
            'amount': pd.Series(range(1000)).apply(lambda x: round(x * 10.5, 2)),
            'customer_id': [f'CUST_{i:04d}' for i in range(1000)]
        }
        
        return pd.DataFrame(mock_data)
    
    def validate_data_quality(self, df: pd.DataFrame) -> bool:
        """Validate data quality before loading"""
        checks = {
            'no_nulls_in_required': df[['transaction_id', 'transaction_date', 'amount']].isnull().sum().sum() == 0,
            'positive_amounts': (df['amount'] > 0).all(),
            'valid_dates': df['transaction_date'].notna().all(),
            'unique_transaction_ids': df['transaction_id'].is_unique
        }
        
        for check_name, result in checks.items():
            if not result:
                self.logger.error(f"Data quality check failed: {check_name}")
                return False
            
        self.logger.info("All data quality checks passed")
        return True
    
    def load_to_bigquery(self, df: pd.DataFrame, table_name: str) -> bool:
        """Load data to BigQuery"""
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                time_partitioning=bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="transaction_date"
                )
            )
            
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for job to complete
            
            self.logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load data to BigQuery: {str(e)}")
            return False
    
    def run_daily_ingestion(self) -> bool:
        """Run daily financial data ingestion"""
        try:
            yesterday = datetime.now() - timedelta(days=1)
            today = datetime.now()
            
            # Extract data
            data = self.extract_financial_data("ERP_SYSTEM", yesterday, today)
            
            # Validate data
            if not self.validate_data_quality(data):
                raise ValueError("Data quality validation failed")
            
            # Load to BigQuery
            if not self.load_to_bigquery(data, "financial_transactions"):
                raise ValueError("Failed to load data to BigQuery")
            
            self.logger.info("Daily financial ingestion completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Daily ingestion failed: {str(e)}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    ingestion = FinancialDataIngestion(
        project_id="itp-data-platform-dev",
        dataset_id="dev_warehouse"
    )
    
    ingestion.run_daily_ingestion()