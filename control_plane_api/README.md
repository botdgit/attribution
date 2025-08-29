Control Plane API

Endpoints:
- POST /v1/analysis/run: Publishes an analysis job to Pub/Sub topic `run-analysis-jobs`. Requires `GCP_PROJECT` env var and appropriate Pub/Sub permissions.

Environment variables:
- GCP_PROJECT or GOOGLE_CLOUD_PROJECT
- ANALYSIS_RUN_TOPIC (default: run-analysis-jobs)
