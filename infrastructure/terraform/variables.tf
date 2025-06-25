variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
}

variable "bigquery_datasets" {
  description = "BigQuery datasets configuration"
  type = map(object({
    location                    = string
    delete_contents_on_destroy  = bool
    default_table_expiration_ms = number
  }))
  default = {
    raw = {
      location                    = "EU"
      delete_contents_on_destroy  = true
      default_table_expiration_ms = null
    }
    staging = {
      location                    = "EU"
      delete_contents_on_destroy  = true
      default_table_expiration_ms = 2592000000 # 30 days
    }
    warehouse = {
      location                    = "EU"
      delete_contents_on_destroy  = false
      default_table_expiration_ms = null
    }
    analytics = {
      location                    = "EU"
      delete_contents_on_destroy  = false
      default_table_expiration_ms = null
    }
  }
}

variable "storage_buckets" {
  description = "Cloud Storage buckets configuration"
  type = map(object({
    location      = string
    storage_class = string
    lifecycle_rules = list(object({
      condition = object({
        age = number
      })
      action = object({
        type = string
      })
    }))
  }))
  default = {
    data-lake = {
      location      = "EU"
      storage_class = "STANDARD"
      lifecycle_rules = [
        {
          condition = { age = 30 }
          action    = { type = "SetStorageClass" }
        }
      ]
    }
    temp = {
      location      = "EU"
      storage_class = "STANDARD"
      lifecycle_rules = [
        {
          condition = { age = 7 }
          action    = { type = "Delete" }
        }
      ]
    }
  }
}