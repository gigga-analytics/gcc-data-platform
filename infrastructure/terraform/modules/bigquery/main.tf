resource "google_bigquery_dataset" "datasets" {
  for_each = var.datasets

  dataset_id                  = "${var.environment}_${each.key}"
  friendly_name              = "${title(var.environment)} ${title(each.key)} Dataset"
  description                = "Dataset for ${each.key} data in ${var.environment}"
  location                   = each.value.location
  delete_contents_on_destroy = each.value.delete_contents_on_destroy
  default_table_expiration_ms = each.value.default_table_expiration_ms

  labels = {
    env = var.environment
  }
}

# Financial tables
resource "google_bigquery_table" "financial_transactions" {
  dataset_id = google_bigquery_dataset.datasets["warehouse"].dataset_id
  table_id   = "financial_transactions"

  time_partitioning {
    type  = "DAY"
    field = "transaction_date"
  }

  clustering = ["business_unit", "transaction_type"]

  schema = jsonencode([
    {
      name = "transaction_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "transaction_date"
      type = "DATE"
      mode = "REQUIRED"
    },
    {
      name = "business_unit"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "transaction_type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "amount"
      type = "NUMERIC"
      mode = "REQUIRED"
    },
    {
      name = "customer_id"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}