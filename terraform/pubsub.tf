resource "google_pubsub_topic" "raw_events" {
  name    = "raw-events"
  project = var.project_id
  labels = {
    env = "cfap"
  }
}

resource "google_service_account" "ingestion_api" {
  account_id   = "ingestion-api-sa"
  display_name = "CFAP Ingestion API service account"
}

resource "google_pubsub_topic_iam_member" "ingestion_publisher" {
  topic  = google_pubsub_topic.raw_events.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.ingestion_api.email}"
}

output "pubsub_topic_full_name" {
  value = google_pubsub_topic.raw_events.id
}

output "ingestion_service_account_email" {
  value = google_service_account.ingestion_api.email
}

resource "google_pubsub_subscription" "raw_events_push" {
  count = var.ingestion_push_endpoint != "" ? 1 : 0

  name  = "raw-events-push"
  topic = google_pubsub_topic.raw_events.id

  push_config {
    push_endpoint = var.ingestion_push_endpoint

    # Optionally configure OIDC token to authenticate push to Cloud Run
    dynamic "oidc_token" {
      for_each = var.ingestion_push_service_account != "" ? [1] : []
      content {
        service_account_email = var.ingestion_push_service_account
      }
    }
  }

  ack_deadline_seconds = 30
}

# GCS uploads bucket for CSV uploads
resource "google_storage_bucket" "uploads_bucket" {
  name     = "${var.project_id}-cfap-uploads"
  project  = var.project_id
  location = "US"
  force_destroy = true
}

# Notification to send new object events to Pub/Sub topic (raw-events)
resource "google_storage_notification" "uploads_to_pubsub" {
  bucket      = google_storage_bucket.uploads_bucket.name
  payload_format = "JSON_API_V1"
  topic        = google_pubsub_topic.raw_events.id
}

# Bucket to store function source / staging
resource "google_storage_bucket" "functions_source" {
  name     = "${var.project_id}-cfap-functions"
  project  = var.project_id
  location = "US"
  force_destroy = true
}

# Service account for Cloud Functions
resource "google_service_account" "functions_sa" {
  account_id   = "cfap-functions-sa"
  display_name = "CFAP Cloud Functions service account"
}

# Cloud Function for CSV ingest (deployed from source in functions/*)
resource "google_cloudfunctions_function" "csv_ingest" {
  name        = "csv-ingest"
  project     = var.project_id
  region      = var.region
  runtime     = "python312"
  entry_point = "gcs_csv_to_bq"

  # source archive should be uploaded to functions_source bucket prior to apply
  source_archive_bucket = google_storage_bucket.functions_source.name
  source_archive_object = "csv_ingest_source.zip"

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.uploads_bucket.name
  }

  service_account_email = google_service_account.functions_sa.email

  environment_variables = {
    TARGET_TABLE = "${var.project_id}:cfap_analytics.standard_events"
  }
}

# Grant BigQuery Data Editor to function SA
resource "google_project_iam_member" "function_bq_insert" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}



