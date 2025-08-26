# attribution

This repository contains a minimal scaffold for the CFAP platform described in the project plan.

What I added:
- `terraform/` - Terraform scaffold to create a storage bucket, BigQuery dataset, and a Cloud SQL instance.
- `backend/` - FastAPI app, auth, analysis, DB helper, Dockerfile and requirements.
- `ingestion/` - ingestion helper that uploads JSON to GCS and reads secrets from Secret Manager.
- `schemas/` - BigQuery schema for sessions.
- `retraining_job/` - simple retrain script and Dockerfile for Cloud Run Job.
- `.github/workflows/deploy.yml` - CI skeleton for deploying backend and frontend.

Quick start (local development):

1. Python backend (virtualenv recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8080
```

2. Build backend Docker image (for local testing):

```bash
docker build -t cfap-backend:local -f backend/Dockerfile backend
docker run -p 8080:8080 cfap-backend:local
```

3. Terraform (requires gcloud auth and a project id):

```bash
cd terraform
terraform init
terraform apply -var="project_id=cfap-platform-dev"
```

Notes:
- This scaffold implements the structural pieces in the CFAP plan. Many production details
  (workload identity federation, exact IAM bindings, Cloud Run configurations, BigQuery scheduled queries,
  and training model implementation) are intentionally left as TODOs so you can wire them to your security
  posture and data shapes.
# attribution