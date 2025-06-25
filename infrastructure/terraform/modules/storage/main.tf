resource "google_storage_bucket" "buckets" {
  for_each = var.buckets

  name     = "${var.project_id}-${var.environment}-${each.key}"
  location = each.value.location
  
  storage_class = each.value.storage_class
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }

  dynamic "lifecycle_rule" {
    for_each = each.value.lifecycle_rules
    content {
      condition {
        age = lifecycle_rule.value.condition.age
      }
      action {
        type          = lifecycle_rule.value.action.type
        storage_class = try(lifecycle_rule.value.action.storage_class, null)
      }
    }
  }

  labels = {
    environment = var.environment
    purpose     = each.key
  }
}

# Data lake bucket for raw data
resource "google_storage_bucket_iam_member" "data_lake_readers" {
  for_each = var.buckets

  bucket = google_storage_bucket.buckets[each.key].name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.project_id}@appspot.gserviceaccount.com"
}