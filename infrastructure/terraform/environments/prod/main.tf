# This Terraform module sets up monitoring and alerting for the data platform on Google Cloud Platform (GCP).
# It includes IAM roles and permissions necessary for the monitoring and alerting system to function correctly.
# The module is designed to be reusable and configurable for different environments.
# It is part of a larger infrastructure setup for a data platform.
# The module requires the GCP provider to be configured with the necessary credentials and project information.






terraform {
  backend "gcs" {
    bucket = "itp-terraform-state-staging"
    prefix = "terraform/state"
  }
}

module "data_platform" {
  source = "../../"
  
  project_id  = "itp-data-platform-staging"
  environment = "staging"
  region      = "europe-west1"
}