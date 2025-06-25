# Monitoring Utility

"""
Pipeline Monitoring and Alerting Utilities
Handles monitoring, logging, and alerting for data pipelines
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.cloud import monitoring_v3, bigquery
from google.cloud.monitoring_dashboard import v1 as dashboard_v1
import pandas as pd

class PipelineMonitor:
    """Pipeline monitoring and alerting system"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.bq_client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger(__name__)
        
    def create_custom_metric(self, metric_name: str, metric_type: str, description: str) -> bool:
        """Create custom metric for pipeline monitoring"""
        try:
            project_name = f"projects/{self.project_id}"
            
            descriptor = monitoring_v3.MetricDescriptor()
            descriptor.type = f"custom.googleapis.com/{metric_name}"
            descriptor.metric_kind = monitoring_v3.MetricDescriptor.MetricKind.GAUGE
            descriptor.value_type = monitoring_v3.MetricDescriptor.ValueType.DOUBLE
            descriptor.description = description
            
            descriptor = self.monitoring_client.create_metric_descriptor(
                name=project_name, metric_descriptor=descriptor
            )
            
            self.logger.info(f"Created metric: {descriptor.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create metric {metric_name}: {str(e)}")
            return False
    
    def write_metric_value(self, metric_name: str, value: float, labels: Dict[str, str] = None) -> bool:
        """Write value to custom metric"""
        try:
            project_name = f"projects/{self.project_id}"
            
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{metric_name}"
            
            if labels:
                for key, val in labels.items():
                    series.metric.labels[key] = val
            
            series.resource.type = "gce_instance"
            series.resource.labels["instance_id"] = "pipeline-monitor"
            series.resource.labels["zone"] = "europe-west1-b"
            
            now = datetime.utcnow()
            seconds = int(now.timestamp())
            nanos = int((now.timestamp() - seconds) * 10**9)
            
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point(
                {"interval": interval, "value": {"double_value": value}}
            )
            series.points = [point]
            
            self.monitoring_client.create_time_series(
                name=project_name, time_series=[series]
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write metric {metric_name}: {str(e)}")
            return False
    
    def check_data_freshness(self, dataset: str, table: str, max_delay_hours: int = 24) -> Dict[str, Any]:
        """Check data freshness and return status"""
        try:
            query = f"""
            SELECT 
                MAX(_PARTITIONTIME) as latest_partition,
                DATETIME_DIFF(CURRENT_DATETIME(), MAX(_PARTITIONTIME), HOUR) as hours_delay
            FROM `{self.project_id}.{dataset}.{table}`
            """
            
            result = list(self.bq_client.query(query))[0]
            
            status = {
                'table': f"{dataset}.{table}",
                'latest_partition': result.latest_partition,
                'hours_delay': result.hours_delay,
                'is_fresh': result.hours_delay <= max_delay_hours,
                'check_time': datetime.utcnow()
            }
            
            # Write metric
            self.write_metric_value(
                "data_freshness_hours",
                float(result.hours_delay),
                {"dataset": dataset, "table": table}
            )
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to check freshness for {dataset}.{table}: {str(e)}")
            return {}
    
    def check_pipeline_health(self, pipeline_name: str) -> Dict[str, Any]:
        """Check overall pipeline health"""
        try:
            # Query pipeline execution logs
            query = f"""
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_runs,
                AVG(duration_seconds) as avg_duration,
                MAX(execution_time) as last_execution
            FROM `{self.project_id}.monitoring.pipeline_executions`
            WHERE pipeline_name = '{pipeline_name}'
                AND execution_time >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
            """
            
            result = list(self.bq_client.query(query))[0]
            
            success_rate = result.successful_runs / result.total_runs if result.total_runs > 0 else 0
            
            health_status = {
                'pipeline_name': pipeline_name,
                'total_runs': result.total_runs,
                'successful_runs': result.successful_runs,
                'success_rate': success_rate,
                'avg_duration': result.avg_duration,
                'last_execution': result.last_execution,
                'is_healthy': success_rate >= 0.95,
                'check_time': datetime.utcnow()
            }
            
            # Write metrics
            self.write_metric_value(
                "pipeline_success_rate",
                success_rate,
                {"pipeline": pipeline_name}
            )
            
            self.write_metric_value(
                "pipeline_avg_duration",
                float(result.avg_duration or 0),
                {"pipeline": pipeline_name}
            )
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Failed to check health for {pipeline_name}: {str(e)}")
            return {}
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily monitoring report"""
        try:
            report = {
                'report_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'data_freshness': [],
                'pipeline_health': [],
                'summary': {}
            }
            
            # Check data freshness for key tables
            key_tables = [
                ('dev_warehouse', 'financial_transactions'),
                ('dev_warehouse', 'customers'),
                ('dev_warehouse', 'projects')
            ]
            
            for dataset, table in key_tables:
                freshness = self.check_data_freshness(dataset, table)
                if freshness:
                    report['data_freshness'].append(freshness)
            
            # Check pipeline health
            pipelines = ['financial_ingestion', 'crm_sync', 'marketing_sync']
            for pipeline in pipelines:
                health = self.check_pipeline_health(pipeline)
                if health:
                    report['pipeline_health'].append(health)
            
            # Generate summary
            fresh_tables = sum(1 for f in report['data_freshness'] if f.get('is_fresh', False))
            healthy_pipelines = sum(1 for h in report['pipeline_health'] if h.get('is_healthy', False))
            
            report['summary'] = {
                'fresh_tables': fresh_tables,
                'total_tables': len(report['data_freshness']),
                'healthy_pipelines': healthy_pipelines,
                'total_pipelines': len(report['pipeline_health']),
                'overall_health_score': (fresh_tables + healthy_pipelines) / (len(report['data_freshness']) + len(report['pipeline_health']))
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate daily report: {str(e)}")
            return {}
    
    def send_alert(self, alert_type: str, message: str, severity: str = "warning") -> bool:
        """Send alert notification"""
        try:
            alert = {
                'timestamp': datetime.utcnow().isoformat(),
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'project_id': self.project_id
            }
            
            # Log the alert
            if severity == "critical":
                self.logger.critical(json.dumps(alert))
            elif severity == "warning":
                self.logger.warning(json.dumps(alert))
            else:
                self.logger.info(json.dumps(alert))
            
            # Here you would integrate with your alerting system
            # (Slack, PagerDuty, email, etc.)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {str(e)}")
            return False

class DataQualityMonitor:
    """Data quality monitoring and validation"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger(__name__)
    
    def validate_schema(self, dataset: str, table: str, expected_schema: List[Dict]) -> bool:
        """Validate table schema against expected schema"""
        try:
            table_ref = self.bq_client.get_table(f"{self.project_id}.{dataset}.{table}")
            actual_schema = [{'name': field.name, 'type': field.field_type} for field in table_ref.schema]
            
            for expected_field in expected_schema:
                if expected_field not in actual_schema:
                    self.logger.error(f"Schema mismatch in {dataset}.{table}: missing {expected_field}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Schema validation failed for {dataset}.{table}: {str(e)}")
            return False
    
    def check_data_completeness(self, dataset: str, table: str, required_columns: List[str]) -> Dict[str, float]:
        """Check data completeness for required columns"""
        try:
            null_checks = []
            for col in required_columns:
                null_checks.append(f"SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) as {col}_nulls")
            
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                {', '.join(null_checks)}
            FROM `{self.project_id}.{dataset}.{table}`
            """
            
            result = list(self.bq_client.query(query))[0]
            
            completeness = {}
            total_rows = result.total_rows
            
            for col in required_columns:
                null_count = getattr(result, f'{col}_nulls')
                completeness[col] = (total_rows - null_count) / total_rows if total_rows > 0 else 0
            
            return completeness
            
        except Exception as e:
            self.logger.error(f"Completeness check failed for {dataset}.{table}: {str(e)}")
            return {}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    monitor = PipelineMonitor("itp-data-platform-dev")
    
    # Generate daily report
    report = monitor.generate_daily_report()
    print(json.dumps(report, indent=2, default=str))
