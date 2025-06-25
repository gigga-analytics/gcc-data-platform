# Notifications Utility

"""
Notification and Alerting Utilities
Handles Slack, email, and other notification channels
"""

import logging
import json
import smtplib
from datetime import datetime
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

class NotificationManager:
    """Manages various notification channels"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_slack_message(self, webhook_url: str, message: str, channel: str = None, username: str = "Data Platform") -> bool:
        """Send message to Slack"""
        try:
            payload = {
                "text": message,
                "username": username
            }
            
            if channel:
                payload["channel"] = channel
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Slack message sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack message: {str(e)}")
            return False
    
    def send_email(self, to_emails: List[str], subject: str, body: str, smtp_config: Dict[str, str]) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config['from_email']
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                
                if smtp_config.get('username') and smtp_config.get('password'):
                    server.login(smtp_config['username'], smtp_config['password'])
                
                server.send_message(msg)
            
            self.logger.info(f"Email sent to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def format_pipeline_alert(self, pipeline_name: str, status: str, details: Dict[str, Any]) -> str:
        """Format pipeline alert message"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        if status == "FAILED":
            emoji = "🚨"
            color = "danger"
        elif status == "WARNING":
            emoji = "⚠️"
            color = "warning"
        else:
            emoji = "✅"
            color = "good"
        
        message = f"""
{emoji} **Pipeline Alert: {pipeline_name}**

**Status:** {status}
**Time:** {timestamp}
**Environment:** {details.get('environment', 'unknown')}

**Details:**
• Duration: {details.get('duration', 'N/A')}
• Records Processed: {details.get('records_processed', 'N/A')}
• Error Message: {details.get('error_message', 'N/A')}

**Next Steps:**
{details.get('next_steps', 'Review pipeline logs and contact data engineering team')}
        """
        
        return message
    
    def format_data_quality_alert(self, table_name: str, quality_score: float, issues: List[str]) -> str:
        """Format data quality alert"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        if quality_score < 0.8:
            emoji = "🚨"
            severity = "CRITICAL"
        elif quality_score < 0.9:
            emoji = "⚠️"
            severity = "WARNING"
        else:
            emoji = "ℹ️"
            severity = "INFO"
        
        message = f"""
{emoji} **Data Quality Alert: {table_name}**

**Severity:** {severity}
**Quality Score:** {quality_score:.2%}
**Time:** {timestamp}

**Issues Found:**
"""
        
        for issue in issues:
            message += f"• {issue}\n"
        
        message += f"""
**Recommendations:**
• Review data ingestion pipelines
• Check source system data quality
• Contact data engineering team if issues persist
        """
        
        return message
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily data platform summary"""
        try:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Calculate overall health
            health_score = summary_data.get('overall_health_score', 0)
            
            if health_score >= 0.95:
                emoji = "🟢"
                status = "HEALTHY"
            elif health_score >= 0.85:
                emoji = "🟡"
                status = "WARNING"
            else:
                emoji = "🔴"
                status = "CRITICAL"
            
            message = f"""
{emoji} **Daily Data Platform Summary - {timestamp}**

**Overall Status:** {status} ({health_score:.1%})

**Pipeline Health:**
• Total Pipelines: {summary_data.get('total_pipelines', 0)}
• Healthy Pipelines: {summary_data.get('healthy_pipelines', 0)}
• Success Rate: {summary_data.get('pipeline_success_rate', 0):.1%}

**Data Freshness:**
• Total Tables: {summary_data.get('total_tables', 0)}
• Fresh Tables: {summary_data.get('fresh_tables', 0)}
• Average Delay: {summary_data.get('avg_delay_hours', 0):.1f} hours

**Cost Summary:**
• Total Spend: €{summary_data.get('total_cost', 0):.2f}
• BigQuery: €{summary_data.get('bigquery_cost', 0):.2f}
• Storage: €{summary_data.get('storage_cost', 0):.2f}

**Top Insights:**
"""
            
            insights = summary_data.get('insights', [])
            for insight in insights[:3]:  # Top 3 insights
                message += f"• {insight}\n"
            
            # Send to Slack
            slack_sent = False
            if self.config.get('slack_webhook_url'):
                slack_sent = self.send_slack_message(
                    self.config['slack_webhook_url'],
                    message,
                    channel=self.config.get('slack_channel', '#data-platform')
                )
            
            # Send email to stakeholders
            email_sent = False
            if self.config.get('stakeholder_emails') and self.config.get('smtp_config'):
                html_message = message.replace('\n', '').replace('**', '').replace('**', '')
                email_sent = self.send_email(
                    self.config['stakeholder_emails'],
                    f"Data Platform Daily Summary - {timestamp}",
                    html_message,
                    self.config['smtp_config']
                )
            
            return slack_sent or email_sent
            
        except Exception as e:
            self.logger.error(f"Failed to send daily summary: {str(e)}")
            return False
    
    def send_incident_alert(self, incident_type: str, severity: str, details: Dict[str, Any]) -> bool:
        """Send incident alert to multiple channels"""
        try:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            severity_config = {
                "critical": {"emoji": "🚨", "channels": ["#incidents", "#data-platform"]},
                "warning": {"emoji": "⚠️", "channels": ["#data-platform"]},
                "info": {"emoji": "ℹ️", "channels": ["#data-platform"]}
            }
            
            config = severity_config.get(severity.lower(), severity_config["info"])
            
            message = f"""
{config['emoji']} **INCIDENT ALERT**

**Type:** {incident_type}
**Severity:** {severity.upper()}
**Time:** {timestamp}

**Description:**
{details.get('description', 'No description provided')}

**Impact:**
{details.get('impact', 'Unknown impact')}

**Affected Systems:**
{details.get('affected_systems', 'Unknown systems')}

**Incident ID:** {details.get('incident_id', 'N/A')}
**Assigned To:** {details.get('assigned_to', 'Data Engineering Team')}

**Action Required:**
{details.get('action_required', 'Investigation and resolution needed')}
            """
            
            # Send to appropriate channels based on severity
            success = True
            for channel in config['channels']:
                if self.config.get('slack_webhook_url'):
                    success &= self.send_slack_message(
                        self.config['slack_webhook_url'],
                        message,
                        channel=channel
                    )
            
            # For critical incidents, also send email
            if severity.lower() == "critical" and self.config.get('oncall_emails'):
                html_message = message.replace('\n', '').replace('**', '').replace('**', '')
                success &= self.send_email(
                    self.config['oncall_emails'],
                    f"CRITICAL INCIDENT: {incident_type}",
                    html_message,
                    self.config['smtp_config']
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send incident alert: {str(e)}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration
    config = {
        'slack_webhook_url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
        'slack_channel': '#data-platform',
        'stakeholder_emails': ['data-team@inthepocket.com', 'management@inthepocket.com'],
        'oncall_emails': ['oncall@inthepocket.com'],
        'smtp_config': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'from_email': 'data-platform@inthepocket.com',
            'username': 'your-email@inthepocket.com',
            'password': 'your-app-password',
            'use_tls': True
        }
    }
    
    notifier = NotificationManager(config)
    
    # Example daily summary
    summary = {
        'overall_health_score': 0.95,
        'total_pipelines': 5,
        'healthy_pipelines': 5,
        'pipeline_success_rate': 0.98,
        'total_tables': 8,
        'fresh_tables': 8,
        'avg_delay_hours': 2.3,
        'total_cost': 1250.00,
        'bigquery_cost': 800.00,
        'storage_cost': 150.00,
        'insights': [
            'All pipelines running smoothly',
            'Cost optimization opportunities in BigQuery queries',
            'Data freshness improved by 15% this week'
        ]
    }
    
    notifier.send_daily_summary(summary)


