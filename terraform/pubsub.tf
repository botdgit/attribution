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
