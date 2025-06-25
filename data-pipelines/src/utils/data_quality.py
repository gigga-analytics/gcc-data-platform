"""
Data Quality Framework
Comprehensive data quality checks and monitoring
"""

import logging
from typing import Dict, List, Any
from google.cloud import bigquery
import pandas as pd

class DataQualityFramework:
    """Framework for data quality monitoring and validation"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger(__name__)
        
    def check_completeness(self, dataset: str, table: str, required_columns: List[str]) -> Dict[str, Any]:
        """Check data completeness"""
        query = f"""
        SELECT 
          COUNT(*) as total_rows,
          {', '.join([f'SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) as {col}_nulls' for col in required_columns])}
        FROM `{self.project_id}.{dataset}.{table}`
        """
        
        result = list(self.client.query(query))[0]
        
        completeness_scores = {}
        total_rows = result.total_rows
        
        for col in required_columns:
            null_count = getattr(result, f'{col}_nulls')
            completeness_scores[col] = (total_rows - null_count) / total_rows if total_rows > 0 else 0
            
        return {
            'total_rows': total_rows,
            'completeness_scores': completeness_scores,
            'overall_score': sum(completeness_scores.values()) / len(completeness_scores)
        }
    
    def check_uniqueness(self, dataset: str, table: str, unique_columns: List[str]) -> Dict[str, Any]:
        """Check data uniqueness"""
        results = {}
        
        for col in unique_columns:
            query = f"""
            SELECT 
              COUNT(*) as total_rows,
              COUNT(DISTINCT {col}) as unique_values
            FROM `{self.project_id}.{dataset}.{table}`
            """
            
            result = list(self.client.query(query))[0]
            uniqueness_score = result.unique_values / result.total_rows if result.total_rows > 0 else 0
            
            results[col] = {
                'total_rows': result.total_rows,
                'unique_values': result.unique_values,
                'uniqueness_score': uniqueness_score
            }
            
        return results
    
    def check_timeliness(self, dataset: str, table: str, date_column: str, max_delay_hours: int = 24) -> Dict[str, Any]:
        """Check data timeliness"""
        query = f"""
        SELECT 
          MAX({date_column}) as latest_date,
          DATETIME_DIFF(CURRENT_DATETIME(), MAX({date_column}), HOUR) as hours_delay
        FROM `{self.project_id}.{dataset}.{table}`
        """
        
        result = list(self.client.query(query))[0]
        
        return {
            'latest_date': result.latest_date,
            'hours_delay': result.hours_delay,
            'is_timely': result.hours_delay <= max_delay_hours
        }
    
    def execute_quality_suite(self, dataset: str, table: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive data quality suite"""
        results = {
            'timestamp': pd.Timestamp.now(),
            'dataset': dataset,
            'table': table
        }
        
        # Completeness checks
        if 'required_columns' in config:
            results['completeness'] = self.check_completeness(
                dataset, table, config['required_columns']
            )
        
        # Uniqueness checks
        if 'unique_columns' in config:
            results['uniqueness'] = self.check_uniqueness(
                dataset, table, config['unique_columns']
            )
        
        # Timeliness checks
        if 'date_column' in config:
            results['timeliness'] = self.check_timeliness(
                dataset, table, config['date_column'], 
                config.get('max_delay_hours', 24)
            )
        
        # Overall quality score
        scores = []
        if 'completeness' in results:
            scores.append(results['completeness']['overall_score'])
        if 'uniqueness' in results:
            avg_uniqueness = sum(r['uniqueness_score'] for r in results['uniqueness'].values()) / len(results['uniqueness'])
            scores.append(avg_uniqueness)
        if 'timeliness' in results:
            scores.append(1.0 if results['timeliness']['is_timely'] else 0.0)
            
        results['overall_quality_score'] = sum(scores) / len(scores) if scores else 0.0
        
        return results