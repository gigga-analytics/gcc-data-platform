terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# BigQuery module
module "bigquery" {
  source = "./modules/bigquery"
  
  project_id   = var.project_id
  environment  = var.environment
  datasets     = var.bigquery_datasets
}

# Storage module
module "storage" {
  source = "./modules/storage"
  
  project_id  = var.project_id
  environment = var.environment
  buckets     = var.storage_buckets
}

# Dataflow module
module "dataflow" {
  source = "./modules/dataflow"
  
  project_id  = var.project_id
  environment = var.environment
  region      = var.region
}

# Cloud Functions module
module "functions" {
  source = "./modules/functions"
  
  project_id  = var.project_id
  environment = var.environment
  region      = var.region
}

# Monitoring module
module "monitoring" {
  source = "./modules/monitoring"
  
  project_id  = var.project_id
  environment = var.environment
}

# IAM module
module "iam" {
  source = "./modules/iam"
  
  project_id  = var.project_id
  environment = var.environment
}