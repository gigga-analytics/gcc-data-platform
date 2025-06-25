"""
Marketing Data Ingestion Pipeline
Handles data from Google Analytics, social media, and marketing platforms
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.cloud import bigquery
import pandas as pd

class MarketingDataIngestion:
    """Marketing data ingestion pipeline"""
    
    def __init__(self, project_id: str, dataset_id: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.bq_client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger(__name__)
        
    def extract_google_analytics_data(self, property_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Extract data from Google Analytics 4"""
        # Mock GA4 data - replace with actual GA4 API calls
        mock_data = {
            'date': pd.date_range(start_date, end_date),
            'sessions': [100 + i * 5 for i in range(len(pd.date_range(start_date, end_date)))],
            'users': [80 + i * 3 for i in range(len(pd.date_range(start_date, end_date)))],
            'page_views': [300 + i * 15 for i in range(len(pd.date_range(start_date, end_date)))],
            'bounce_rate': [0.45 + (i % 10) * 0.01 for i in range(len(pd.date_range(start_date, end_date)))],
            'avg_session_duration': [180 + (i % 20) * 5 for i in range(len(pd.date_range(start_date, end_date)))],
            'conversions': [5 + i // 3 for i in range(len(pd.date_range(start_date, end_date)))],
            'source': 'google_analytics'
        }
        
        return pd.DataFrame(mock_data)
    
    def extract_social_media_data(self, platforms: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Extract social media metrics"""
        all_data = []
        
        for platform in platforms:
            # Mock social media data - replace with actual API calls
            dates = pd.date_range(start_date, end_date)
            platform_data = {
                'date': dates,
                'platform': platform,
                'followers': [1000 + i * 10 for i in range(len(dates))],
                'impressions': [5000 + i * 50 for i in range(len(dates))],
                'engagements': [200 + i * 5 for i in range(len(dates))],
                'clicks': [50 + i * 2 for i in range(len(dates))],
                'shares': [10 + i // 2 for i in range(len(dates))],
                'mentions': [5 + i // 3 for i in range(len(dates))]
            }
            all_data.append(pd.DataFrame(platform_data))
        
        return pd.concat(all_data, ignore_index=True)
    
    def extract_email_campaign_data(self, campaign_ids: List[str]) -> pd.DataFrame:
        """Extract email marketing campaign data"""
        all_campaigns = []
        
        for campaign_id in campaign_ids:
            # Mock email campaign data
            campaign_data = {
                'campaign_id': [campaign_id],
                'campaign_name': [f'Campaign {campaign_id}'],
                'send_date': [datetime.now() - timedelta(days=1)],
                'emails_sent': [1000],
                'emails_delivered': [980],
                'opens': [245],
                'clicks': [67],
                'unsubscribes': [3],
                'bounces': [20],
                'open_rate': [0.25],
                'click_rate': [0.068],
                'unsubscribe_rate': [0.003]
            }
            all_campaigns.append(pd.DataFrame(campaign_data))
        
        return pd.concat(all_campaigns, ignore_index=True)
    
    def calculate_marketing_metrics(self, ga_data: pd.DataFrame, social_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate aggregated marketing metrics"""
        # Aggregate by date
        ga_daily = ga_data.groupby('date').agg({
            'sessions': 'sum',
            'users': 'sum',
            'page_views': 'sum',
            'conversions': 'sum'
        }).reset_index()
        
        social_daily = social_data.groupby('date').agg({
            'impressions': 'sum',
            'engagements': 'sum',
            'clicks': 'sum',
            'shares': 'sum'
        }).reset_index()
        
        # Merge datasets
        metrics = pd.merge(ga_daily, social_daily, on='date', how='outer').fillna(0)
        
        # Calculate derived metrics
        metrics['engagement_rate'] = metrics['engagements'] / metrics['impressions']
        metrics['conversion_rate'] = metrics['conversions'] / metrics['sessions']
        metrics['social_ctr'] = metrics['clicks'] / metrics['impressions']
        
        return metrics
    
    def load_to_bigquery(self, df: pd.DataFrame, table_name: str) -> bool:
        """Load marketing data to BigQuery"""
        if df.empty:
            self.logger.warning(f"No data to load for {table_name}")
            return False
            
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                create_disposition="CREATE_IF_NEEDED"
            )
            
            job = self.bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            self.logger.info(f"Successfully loaded {len(df)} rows to {table_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load data to BigQuery: {str(e)}")
            return False
    
    def run_daily_marketing_sync(self) -> bool:
        """Run daily marketing data synchronization"""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Extract Google Analytics data
            ga_data = self.extract_google_analytics_data(
                property_id="123456789", 
                start_date=yesterday, 
                end_date=today
            )
            
            # Extract social media data
            social_data = self.extract_social_media_data(
                platforms=['linkedin', 'twitter', 'facebook'], 
                start_date=yesterday, 
                end_date=today
            )
            
            # Extract email campaign data
            email_data = self.extract_email_campaign_data(
                campaign_ids=['newsletter_001', 'promo_002']
            )
            
            # Calculate marketing metrics
            marketing_metrics = self.calculate_marketing_metrics(ga_data, social_data)
            
            # Load to BigQuery
            success = True
            success &= self.load_to_bigquery(ga_data, "google_analytics_daily")
            success &= self.load_to_bigquery(social_data, "social_media_daily")
            success &= self.load_to_bigquery(email_data, "email_campaigns")
            success &= self.load_to_bigquery(marketing_metrics, "marketing_metrics_daily")
            
            if success:
                self.logger.info("Marketing daily sync completed successfully")
            else:
                self.logger.error("Marketing daily sync completed with errors")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Marketing sync failed: {str(e)}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    ingestion = MarketingDataIngestion(
        project_id="itp-data-platform-dev",
        dataset_id="dev_warehouse"
    )
    
    ingestion.run_daily_marketing_sync()