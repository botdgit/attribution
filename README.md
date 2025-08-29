docker build -t cfap-backend:local -f backend/Dockerfile backend
docker run -p 8080:8080 cfap-backend:local

# CFAP (Causal Funnel Attribution Platform)

Unified ingestion, causal experimentation & attribution, and actionable reporting for growth & marketing teams.


## 1. Product Overview

CFAP lets teams CONNECT event & commerce data, ANALYSE causal lift & attribution using transparent models, and ACT on insights via dashboards & downstream activations. The platform emphasises:
- Trust (open, reproducible causal models)
- Speed (streaming ingestion + incremental analysis)
- Actionability (clear lift & ROI surfaces, export + API)
- Extensibility (plugin model registry & model interface)

## 2. High‑Level Architecture

Flow (left → right):
Clients & Sources → Ingestion API / Pub/Sub → Dataflow (Beam) normalization → BigQuery canonical tables → Control Plane (run requests) → Causal Engine Worker (models) → Results / Registry Tables → Reporting API → Frontend UI.

Main Pillars:
1. Ingestion Layer: authenticated JSON events + batch uploads; idempotent BigQuery writes.
2. Data Processing: Beam pipeline to standard events schema; enrichment hooks (extensible).
3. Causal Engine: pluggable model interface (`causal_engine.models.*`) with current DID implementation.
4. Control Plane API: schedules/queues analyses; stores job status.
5. Reporting API: read-only aggregation & surfacing of model outcomes / metrics.
6. Frontend: Vite/React app with Firebase auth and reporting & run triggers.
7. Infrastructure as Code: Terraform for topics, subscriptions, datasets, tables, service accounts.

## 3. Core Data Assets (BigQuery)
- `standard_events` (canonical raw events)
- `lift_analysis_results` (per model run outputs: effect, confidence, metadata)
- `job_status` (orchestration lifecycle + timestamps)
- `causal_model_registry` (planned: model definitions, versions, lineage)

## 4. Key Services & Packages
| Component | Path | Purpose |
|-----------|------|---------|
| Ingestion API | `ingestion_api/` | Accept client events, batch publish to Pub/Sub, signed upload URLs |
| Ingestion Subscriber | `ingestion_subscriber/` | Pub/Sub push → BigQuery (idempotent) |
| Dataflow Pipeline | `dataflow/` | Beam transforms / enrichment (batch & streaming) |
| Control Plane API | `control_plane_api/` | `POST /v1/analysis/run` enqueue model runs |
| Causal Engine Worker | `causal_engine/worker.py` | Consume run jobs, execute model, persist results & status |
| Causal Models | `causal_engine/models/` | Implement model contract (currently DID) |
| Reporting API | `reporting_api/` or `backend/reporting_api/` | Read & aggregate results |
| Frontend | `frontend/` | React UI, auth, dashboards, run controls |
| Common Auth & Settings | `common/` | Firebase token verification & centralized settings |
| Infra | `terraform/` | Topics, subs, datasets, tables, service accounts |

## 5. Data & Job Lifecycle
1. Client emits event to Ingestion API (Firebase auth) OR uploads batch to GCS (signed URL).
2. API publishes normalized message to Pub/Sub with `insertId` for idempotency.
3. Subscriber writes rows to `standard_events` (dedup by insertId). (Beam pipeline may also feed/enrich.)
4. User (or schedule) hits Control Plane `POST /v1/analysis/run` specifying `model_name` + params.
5. Pub/Sub delivers job to Worker. Worker loads config & parameters, runs model (DID).
6. Worker writes lift metrics to `lift_analysis_results`, metadata to `job_status` (+ model registry soon).
7. Reporting API exposes aggregated metrics / health; Frontend renders charts and run status.

## 6. Getting Started (Local)
Prereqs: Python 3.12, Node 18+, gcloud auth (for GCP resources), Docker (optional), Firebase CLI (optional).

### 6.1 Create & Activate Virtualenv
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 6.2 Run Ingestion & Control Plane (Example)
```bash
pip install -r ingestion_api/requirements.txt || true  # if separate
uvicorn ingestion_api.app:app --port 8085 --reload &
pip install -r control_plane_api/requirements.txt
uvicorn control_plane_api.app:app --port 8082 --reload &
```

### 6.3 Run Worker
```bash
export GCP_PROJECT=your-project
pip install -r backend/requirements.txt
python -m causal_engine.worker
```

### 6.4 Trigger a Model Run
```bash
curl -X POST localhost:8082/v1/analysis/run \
  -H 'Content-Type: application/json' \
  -d '{"model_name":"did","params":{"campaign_id":"xyz-123"}}'
```

### 6.5 Frontend Dev
```bash
cd frontend
npm ci
npm run dev
```
If using Firebase auth create `frontend/.env` with the `VITE_FIREBASE_*` variables (see below).

### 6.6 Terraform (Provision Core Infra)
```bash
cd terraform
terraform init
terraform apply -var="project_id=cfap-platform-dev"
```

## 7. Configuration & Environment
Centralized via `common/settings.py` (Pydantic). Key variables:
- `GCP_PROJECT` / `GOOGLE_CLOUD_PROJECT`
- `RESULT_DATASET` (default `cfap_analytics`)
- `ANALYSIS_RUN_TOPIC`, `ANALYSIS_RUN_SUBSCRIPTION`
- `FIREBASE_PROJECT_ID` (auth checks)
- `CFAP_TEST_MODE` (enables local fallbacks / synthetic data)

Frontend Firebase `.env` template:
```
VITE_FIREBASE_API_KEY=xxx
VITE_FIREBASE_AUTH_DOMAIN=xxx.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=xxx
VITE_FIREBASE_STORAGE_BUCKET=xxx.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
VITE_FIREBASE_MEASUREMENT_ID=...
```

## 8. Causal Models
Model contract (simplified):
- Input: parameter dict, BigQuery client handle, project & dataset, time bounds / identifiers.
- Output: effect size(s), confidence interval(s), diagnostics metadata, persisted row(s) in `lift_analysis_results`.
- Registration: (planned) `causal_model_registry` row with model_name, version, hyperparams, code ref.

Current implemented: Difference‑in‑Differences (DID) using statsmodels OLS.

Planned additions: CUPED uplift, Bayesian hierarchical lift, Synthetic Control, Shapley multi-touch attribution.

## 9. Security & Auth
- Primary auth: Firebase ID token (all ingestion & control operations).
- API key fallback: legacy path (will be disabled in production mode).
- Idempotency: `insertId` per event row.
- Principle of Least Privilege: separate service accounts for worker vs ingestion.
- To do: signed model artifacts, HMAC option, audit logging, structured log & metrics exporter.

## 10. Observability (Current / Planned)
Current: basic Python logging.
Planned: structured JSON logs, Prometheus metrics endpoint, BigQuery cost guardrails (query bytes), run SLA dashboards.

## 11. CI/CD
GitHub Actions workflow (skeleton) will cover:
- Lint & Format (ruff / black)
- Type Check (mypy)
- Tests (pytest)
- Frontend build & artifact upload
- Terraform plan (manual apply gate)

## 12. Directory Map (Selected)
```
backend/                FastAPI legacy backend & analysis helpers
control_plane_api/      Run scheduling API
causal_engine/          Model base + worker + implementations
ingestion_api/          Client event ingestion
ingestion_subscriber/   Pub/Sub push → BigQuery writer
dataflow/               Beam pipeline transforms & tests
reporting_api/          Read-only analytics service
frontend/               React + Vite app
terraform/              IaC definitions & table schemas
schemas/                (Legacy) raw schema references (to be consolidated)
common/                 Shared auth + settings
connectors/             Source connectors (e.g., Shopify)
retraining_job/         Batch retraining / scheduled job scaffold
```

## 13. Local Firebase Login
Interactive:
```bash
./scripts/firebase_login.sh
```
CI token (store in `FIREBASE_TOKEN` secret):
```bash
./scripts/firebase_login.sh --ci
```

## 14. Roadmap Snapshot
Phase 0 Hardening (WIP): auth enforcement everywhere, structured logging, model registry table, CI pipeline.
Phase 1 Attribution Expansion: multi-touch path modeling, experiment grouping, partial funnel attribution.
Phase 2 Experiment Intelligence: automated power calculation, pre-check guardrails, sequential monitoring.
Phase 3 Activation: push segments / lift outcomes to ad platforms & CRM, real-time audiences.

## 15. Contributing
See `CONTRIBUTING.md` (environment setup, style, commit conventions). PRs should include: description, test coverage (or rationale), and update docs if public behavior changes.

## 16. Support / Questions
Open an issue with detailed context (component, expected vs actual, logs). Include model name + job id for analysis questions.

---
This repository is an evolving reference implementation; adapt the Terraform & IAM to your org’s security and data governance standards before production use.