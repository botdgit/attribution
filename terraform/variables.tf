variable "artifact_repo" {
  description = "Artifact Registry repository id to create"
  type        = string
  default     = "cfap-repo"
}

variable "ingestion_push_endpoint" {
  description = "Optional push endpoint URL for Pub/Sub push subscription (Cloud Run URL). Leave empty to create a pull subscription instead."
  type        = string
  default     = ""
}

variable "ingestion_push_service_account" {
  description = "Optional service account email to authenticate push requests. If empty, no push auth is set."
  type        = string
  default     = ""
}
