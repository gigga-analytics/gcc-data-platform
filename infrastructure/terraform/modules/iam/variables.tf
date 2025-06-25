# This Terraform module sets up monitoring and alerting for the data platform on Google Cloud Platform (GCP).
# It includes IAM roles and permissions necessary for the monitoring and alerting system to function correctly.
# The module is designed to be reusable and configurable for different environments.
# It is part of a larger infrastructure setup for a data platform.
# The module requires the GCP provider to be configured with the necessary credentials and project information.


variable "gcp_region" {
  description = "GCP Region"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}