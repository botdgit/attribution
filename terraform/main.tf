provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

# Data Lake / Warehouse
resource "google_storage_bucket" "raw_data" {
  name          = "cfap-data-raw-${var.project_id}"
  location      = "US"
  force_destroy = true
}

resource "google_bigquery_dataset" "cfap_analytics" {
  dataset_id = "cfap_analytics"
  location   = "US"
}

# Metadata & Benchmark Database
resource "google_sql_database_instance" "benchmark_db" {
  name             = "cfap-benchmark-db"
  database_version = "POSTGRES_14"
  region           = var.region
  settings {
    tier = "db-g1-small"
  }
}

# Artifact Registry for container images
resource "google_artifact_registry_repository" "container_repo" {
  provider = google
  location     = var.region
  repository_id = "${var.artifact_repo}"
  description  = "Artifact Registry repository for CFAP images"
  format       = "DOCKER"
}

# CI/CD service account for GitHub Actions
resource "google_service_account" "ci_cd_deployer" {
  account_id   = "ci-cd-deployer"
  display_name = "CI/CD Deployer"
}

# Grant Artifact Registry Writer and Cloud Run Admin to the CI/CD SA
resource "google_project_iam_member" "ci_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.ci_cd_deployer.email}"
}

resource "google_project_iam_member" "ci_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.ci_cd_deployer.email}"
}

# Data source for project metadata (used to build provider member strings)
data "google_project" "project" {
  project_id = var.project_id
}

# Workload Identity Pool and Provider for GitHub Actions
resource "google_iam_workload_identity_pool" "pool" {
  provider = google
  workload_identity_pool_id = "github-pool"
  display_name               = "GitHub Actions Pool"
  location                   = "global"
}

resource "google_iam_workload_identity_pool_provider" "provider" {
  provider = google
  workload_identity_pool_id = google_iam_workload_identity_pool.pool.workload_identity_pool_id
  provider_id                = "github-provider"
  display_name               = "GitHub OIDC Provider"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"     = "assertion.sub"
    "attribute.actor"    = "assertion.actor"
  }
}

# Allow the Workload Identity Provider to impersonate the CI service account
resource "google_service_account_iam_member" "ci_wif_binding" {
  service_account_id = google_service_account.ci_cd_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principal://iam.googleapis.com/projects/${data.google_project.project.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.pool.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.provider.provider_id}"
}

