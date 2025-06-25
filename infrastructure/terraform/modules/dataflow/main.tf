# Dataflow templates bucket
resource "google_storage_bucket" "dataflow_templates" {
  name     = "${var.project_id}-${var.environment}-dataflow-templates"
  location = var.region

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    purpose     = "dataflow-templates"
  }
}

# Pub/Sub topic for streaming data
resource "google_pubsub_topic" "financial_stream" {
  name = "${var.environment}-financial-stream"

  labels = {
    environment = var.environment
  }
}

# Pub/Sub subscription
resource "google_pubsub_subscription" "financial_stream_sub" {
  name  = "${var.environment}-financial-stream-sub"
  topic = google_pubsub_topic.financial_stream.name

  ack_deadline_seconds = 20

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

# Dead letter topic
resource "google_pubsub_topic" "dead_letter" {
  name = "${var.environment}-dead-letter"

  labels = {
    environment = var.environment
  }
}

# Dataflow job template
resource "google_dataflow_job" "financial_streaming" {
  name              = "${var.environment}-financial-streaming"
  template_gcs_path = "gs://${google_storage_bucket.dataflow_templates.name}/templates/financial-streaming"
  temp_gcs_location = "gs://${google_storage_bucket.dataflow_templates.name}/temp"
  
  parameters = {
    inputSubscription = google_pubsub_subscription.financial_stream_sub.id
    outputTable       = "${var.project_id}:${var.environment}_warehouse.financial_transactions"
  }

  on_delete = "cancel"
}