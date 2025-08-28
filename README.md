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
# Reporting API (local dev)

- The reporting API is a small FastAPI service at `backend/reporting_api`.
- To run locally for frontend development, install requirements and run:
  - `pip install -r backend/reporting_api/requirements.txt`
  - `RUNNING_LOCAL=true uvicorn backend.reporting_api.app:app --port 8081 --host 0.0.0.0`
- The frontend dev server proxies `/api/reporting` to `http://localhost:8081` by default.
# Causal Engine & Control Plane

This repository now includes a minimal Causal Engine and Control Plane to run analyses end-to-end.

Services:
- `control_plane_api` — exposes `POST /v1/analysis/run` to enqueue analysis jobs to Pub/Sub (`run-analysis-jobs`).
- `causal_engine.worker` — a worker that subscribes to `run-analysis-worker` subscription, runs requested models (currently `did`) and writes results to BigQuery (`lift_analysis_results`).

Running the control plane locally:

```bash
pip install -r control_plane_api/requirements.txt
export GCP_PROJECT=your-project-id
uvicorn control_plane_api.app:app --port 8082 --host 0.0.0.0
```

Run the worker locally (requires ADC or service account credentials with Pub/Sub and BigQuery access):

```bash
pip install -r backend/requirements.txt
python -m causal_engine.worker
```

Trigger an analysis (example):

```bash
curl -X POST localhost:8082/v1/analysis/run -H "Content-Type: application/json" -d '{"model_name":"did","params":{"campaign_id":"xyz-123"}}'
```

Terraform notes:
- The Terraform now creates:
  - `google_pubsub_topic.run-analysis-jobs` and `google_pubsub_subscription.run-analysis-worker`.
  - `google_service_account.causal_engine_worker` with Pub/Sub subscriber and BigQuery editor roles.
  - `google_bigquery_table.lift_analysis_results` and `google_bigquery_table.job_status`.

Environment variables for worker and control plane:
- `GCP_PROJECT` or `GOOGLE_CLOUD_PROJECT` — project id
- `ANALYSIS_RUN_TOPIC` / `ANALYSIS_RUN_SUBSCRIPTION` — Pub/Sub names
- `RESULT_DATASET` — BigQuery dataset name (default `cfap_analytics`)

### Firebase login

To interact with Firebase (hosting, deploys) you can login locally or generate a CI token.

- Interactive (opens a browser):

  ./scripts/firebase_login.sh

- CI token (copy the output and store in GitHub secret `FIREBASE_TOKEN`):

  ./scripts/firebase_login.sh --ci

The script uses `npx firebase-tools` so Node.js must be installed.

# attribution

Frontend Firebase configuration

The frontend reads Firebase config from Vite env variables prefixed with `VITE_` at build time. To enable Firebase analytics or auth in development, create a `.env` file in the `frontend` directory with the following values:

```
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_FIREBASE_MEASUREMENT_ID=your_measurement_id
```

Then run the frontend dev server from `frontend/`:

```bash
cd frontend
npm ci
npm run dev
```

If Vite env variables are not set, the frontend will continue to work without Firebase.

Example GitHub Actions production build snippet

Below is a minimal example showing how to inject Firebase config stored as GitHub Secrets into the frontend build step. Add the secrets `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, `VITE_FIREBASE_MESSAGING_SENDER_ID`, `VITE_FIREBASE_APP_ID`, and `VITE_FIREBASE_MEASUREMENT_ID` to your repository.

```yaml
- name: Build frontend
  working-directory: frontend
  env:
    VITE_FIREBASE_API_KEY: ${{ secrets.VITE_FIREBASE_API_KEY }}
    VITE_FIREBASE_AUTH_DOMAIN: ${{ secrets.VITE_FIREBASE_AUTH_DOMAIN }}
    VITE_FIREBASE_PROJECT_ID: ${{ secrets.VITE_FIREBASE_PROJECT_ID }}
    VITE_FIREBASE_STORAGE_BUCKET: ${{ secrets.VITE_FIREBASE_STORAGE_BUCKET }}
    VITE_FIREBASE_MESSAGING_SENDER_ID: ${{ secrets.VITE_FIREBASE_MESSAGING_SENDER_ID }}
    VITE_FIREBASE_APP_ID: ${{ secrets.VITE_FIREBASE_APP_ID }}
    VITE_FIREBASE_MEASUREMENT_ID: ${{ secrets.VITE_FIREBASE_MEASUREMENT_ID }}
  run: |
    npm ci
    npm run build
```

This ensures the built static files include the correct runtime config without checking secrets into source control.