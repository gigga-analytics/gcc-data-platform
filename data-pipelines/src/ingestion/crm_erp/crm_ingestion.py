




"""
CRM/ERP Data Ingestion Pipeline
Handles customer and project data from CRM and ERP systems
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.cloud import bigquery
import pandas as pd
import requests

class CRMERPIngestion:
    """CRM and ERP data ingestion pipeline"""
    
    def __init__(self, project_id: str, dataset_id: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.bq_client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger(__name__)
        
    def extract_customer_data(self, api_endpoint: str, api_key: str) -> pd.DataFrame:
        """Extract customer data from CRM API"""
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            response = requests.get(f"{api_endpoint}/customers", headers=headers)
            response.raise_for_status()
            
            customers = response.json()
            
            # Transform to DataFrame
            df = pd.DataFrame(customers)
            
            # Standardize columns
            df = df.rename(columns={
                'id': 'customer_id',
                'name': 'customer_name',
                'email': 'email_address',
                'created_at': 'created_date',
                'updated_at': 'last_updated'
            })
            
            # Data cleaning
            df['created_date'] = pd.to_datetime(df['created_date'])
            df['last_updated'] = pd.to_datetime(df['last_updated'])
            df['email_address'] = df['email_address'].str.lower()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to extract customer data: {str(e)}")
            return pd.DataFrame()
    
    def extract_project_data(self, api_endpoint: str, api_key: str) -> pd.DataFrame:
        """Extract project data from ERP system"""
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            response = requests.get(f"{api_endpoint}/projects", headers=headers)
            response.raise_for_status()
            
            projects = response.json()
            
            # Transform to DataFrame
            df = pd.DataFrame(projects)
            
            # Standardize columns
            df = df.rename(columns={
                'id': 'project_id',
                'name': 'project_name',
                'client_id': 'customer_id',
                'start_date': 'project_start_date',
                'end_date': 'project_end_date',
                'budget': 'project_budget',
                'status': 'project_status'
            })
            
            # Data cleaning
            df['project_start_date'] = pd.to_datetime(df['project_start_date'])
            df['project_end_date'] = pd.to_datetime(df['project_end_date'])
            df['project_budget'] = pd.to_numeric(df['project_budget'], errors='coerce')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to extract project data: {str(e)}")
            return pd.DataFrame()
    
    def load_to_bigquery(self, df: pd.DataFrame, table_name: str) -> bool:
        """Load data to BigQuery with upsert logic"""
        if df.empty:
            self.logger.warning(f"No data to load for {table_name}")
            return False
            
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            # Use WRITE_TRUNCATE for full refresh, or implement merge logic
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # Full refresh for simplicity
                create_disposition="CREATE_IF_NEEDED"
            )
            
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            self.logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load data to BigQuery: {str(e)}")
            return False
    
    def run_daily_sync(self, crm_config: Dict, erp_config: Dict) -> bool:
        """Run daily CRM/ERP data synchronization"""
        try:
            # Extract customer data
            customers_df = self.extract_customer_data(
                crm_config['api_endpoint'], 
                crm_config['api_key']
            )
            
            # Extract project data
            projects_df = self.extract_project_data(
                erp_config['api_endpoint'], 
                erp_config['api_key']
            )
            
            # Load to BigQuery
            success = True
            if not customers_df.empty:
                success &= self.load_to_bigquery(customers_df, "customers")
            
            if not projects_df.empty:
                success &= self.load_to_bigquery(projects_df, "projects")
            
            if success:
                self.logger.info("CRM/ERP daily sync completed successfully")
            else:
                self.logger.error("CRM/ERP daily sync completed with errors")
                
            return success
            
        except Exception as e:
            self.logger.error(f"CRM/ERP sync failed: {str(e)}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Mock configuration
    crm_config = {
        'api_endpoint': 'https://api.crm-system.com/v1',
        'api_key': 'your-crm-api-key'
    }
    
    erp_config = {
        'api_endpoint': 'https://api.erp-system.com/v1',
        'api_key': 'your-erp-api-key'
    }
    
    ingestion = CRMERPIngestion(
        project_id="itp-data-platform-dev",
        dataset_id="dev_warehouse"
    )
    
    ingestion.run_daily_sync(crm_config, erp_config)