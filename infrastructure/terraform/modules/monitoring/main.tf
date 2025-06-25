#Monitoring and alerting module
# Data freshness monitoring
resource "google_monitoring_alert_policy" "data_freshness" {
  display_name = "${var.environment} - Data Freshness Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "Financial data is stale"
    
    condition_threshold {
      filter          = "resource.type=\"bigquery_table\" AND resource.labels.table_id=\"financial_transactions\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 86400  # 24 hours in seconds
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "86400s"  # 24 hours
  }
}

# Pipeline failure monitoring
resource "google_monitoring_alert_policy" "pipeline_failures" {
  display_name = "${var.environment} - Pipeline Failure Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Function errors"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/execution_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 5
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

# Cost monitoring
resource "google_monitoring_alert_policy" "cost_alert" {
  display_name = "${var.environment} - Cost Alert"
  combiner     = "OR"
  
  conditions {
    display_name = "BigQuery costs exceeding budget"
    
    condition_threshold {
      filter          = "metric.type=\"billing.googleapis.com/billing/total_cost\" AND resource.labels.service=\"BigQuery\""
      duration        = "86400s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 1000  # $1000 per day
      
      aggregations {
        alignment_period   = "86400s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

# Email notification channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "${var.environment} Data Platform Alerts"
  type         = "email"
  
  labels = {
    email_address = "data-engineering@inthepocket.com"
  }
}

# Dashboard for operational metrics
resource "google_monitoring_dashboard" "data_platform" {
  dashboard_json = jsonencode({
    displayName = "${var.environment} Data Platform Dashboard"
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "BigQuery Query Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"bigquery.googleapis.com/slots/total_allocated\""
                  }
                  unitOverride = "1"
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Slots"
                scale = "LINEAR"
              }
            }
          }
        }
        {
          width  = 6
          height = 4
          xPos   = 6
          widget = {
            title = "Cloud Functions Executions"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"cloudfunctions.googleapis.com/function/execution_count\""
                  }
                  unitOverride = "1"
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Executions"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}