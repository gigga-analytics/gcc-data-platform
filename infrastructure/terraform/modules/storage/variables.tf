variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "buckets" {
  description = "Cloud Storage buckets configuration"
  type = map(object({
    location      = string
    storage_class = string
    lifecycle_rules = list(object({
      condition = object({
        age = number
      })
      action = object({
        type          = string
        storage_class = optional(string)
      })
    }))
  }))
}