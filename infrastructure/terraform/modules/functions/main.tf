# Cloud Functions source bucket
resource "google_storage_bucket" "functions_source" {
  name     = "${var.project_id}-${var.environment}-functions-source"
  location = var.region

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    purpose     = "functions-source"
  }
}

# Financial data ingestion function
resource "google_cloudfunctions_function" "financial_ingestion" {
  name        = "${var.environment}-financial-ingestion"
  description = "Daily financial data ingestion function"
  runtime     = "python39"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.functions_source.name
  source_archive_object = "financial-ingestion.zip"
  trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = "projects/${var.project_id}/topics/${var.environment}-financial-trigger"
  }
  entry_point = "main"

  environment_variables = {
    PROJECT_ID  = var.project_id
    ENVIRONMENT = var.environment
    DATASET_ID  = "${var.environment}_warehouse"
  }

  labels = {
    environment = var.environment
    function    = "financial-ingestion"
  }
}

# Data quality monitoring function
resource "google_cloudfunctions_function" "data_quality_monitor" {
  name        = "${var.environment}-data-quality-monitor"
  description = "Data quality monitoring function"
  runtime     = "python39"

  available_memory_mb   = 512
  source_archive_bucket = google_storage_bucket.functions_source.name
  source_archive_object = "data-quality-monitor.zip"
  
  trigger {
    event_type = "providers/cloud.firestore/eventTypes/document.write"
    resource   = "projects/${var.project_id}/databases/(default)/documents/data_quality/{document}"
  }
  entry_point = "monitor_data_quality"

  environment_variables = {
    PROJECT_ID  = var.project_id
    ENVIRONMENT = var.environment
  }

  labels = {
    environment = var.environment
    function    = "data-quality"
  }
}

# Cloud Scheduler job for daily ingestion
resource "google_cloud_scheduler_job" "daily_financial_ingestion" {
  name     = "${var.environment}-daily-financial-ingestion"
  schedule = "0 6 * * *"  # Daily at 6 AM
  time_zone = "Europe/Brussels"

  pubsub_target {
    topic_name = "projects/${var.project_id}/topics/${var.environment}-financial-trigger"
    data       = base64encode("{\"trigger\": \"daily_ingestion\"}")
  }
}