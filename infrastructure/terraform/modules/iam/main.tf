# Service account for data pipelines
# This Terraform module sets up IAM roles and service accounts for a data platform on Google Cloud Platform (GCP).
# It includes service accounts for data pipelines and dbt, along with the necessary permissions for BigQuery and Cloud Storage.
# It also creates a custom role for financial data access and assigns it to the analysts group.
# It is designed to be reusable and configurable for different environments, such as development, staging, and production.
# The module requires the GCP provider to be configured with the necessary credentials and project information.





resource "google_service_account" "data_pipeline_sa" {
  account_id   = "${var.environment}-data-pipeline"
  display_name = "${var.environment} Data Pipeline Service Account"
}

# Service account for dbt
resource "google_service_account" "dbt_sa" {
  account_id   = "${var.environment}-dbt"
  display_name = "${var.environment} dbt Service Account"
}

# BigQuery permissions for data pipeline SA
resource "google_project_iam_member" "data_pipeline_bigquery" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.data_pipeline_sa.email}"
}

# Storage permissions for data pipeline SA
resource "google_project_iam_member" "data_pipeline_storage" {
  for_each = toset([
    "roles/storage.objectAdmin"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.data_pipeline_sa.email}"
}

# BigQuery permissions for dbt SA
resource "google_project_iam_member" "dbt_bigquery" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.dbt_sa.email}"
}

# Custom role for financial data access
resource "google_project_iam_custom_role" "financial_data_viewer" {
  role_id     = "${var.environment}_financial_data_viewer"
  title       = "${var.environment} Financial Data Viewer"
  description = "View access to financial datasets"
  
  permissions = [
    "bigquery.datasets.get",
    "bigquery.tables.get",
    "bigquery.tables.getData",
    "bigquery.jobs.create"
  ]
}

# Analysts group
resource "google_project_iam_member" "analysts_financial_access" {
  project = var.project_id
  role    = google_project_iam_custom_role.financial_data_viewer.id
  member  = "group:analysts@inthepocket.com"
}

# Finance team access
resource "google_project_iam_member" "finance_team_access" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "group:finance@inthepocket.com"
}

# Data engineering admin access
resource "google_project_iam_member" "data_eng_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "group:data-engineering@inthepocket.com"
}