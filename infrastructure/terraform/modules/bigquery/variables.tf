variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "datasets" {
  description = "BigQuery datasets configuration"
  type = map(object({
    location                    = string
    delete_contents_on_destroy  = bool
    default_table_expiration_ms = number
  }))
}