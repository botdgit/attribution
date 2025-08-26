output "artifact_registry_repo" {
  value = google_artifact_registry_repository.container_repo.repository_id
}

output "ci_cd_service_account_email" {
  value = google_service_account.ci_cd_deployer.email
}

output "workload_identity_provider" {
  value = "projects/${data.google_project.project.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.pool.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.provider.provider_id}"
}

output "project_number" {
  value = data.google_project.project.number
}
