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
1. **Ingestion Layer**: authenticated JSON events + batch uploads; idempotent BigQuery writes.
2. **Data Processing**: Beam pipeline to standard events schema; enrichment hooks (extensible).
3. **Causal Engine**: pluggable model interface (`causal_engine.models.*`) with containerized DID, PSM, DML implementations.
4. **Control Plane API**: schedules/queues analyses; stores job status via Pub/Sub orchestration.
5. **Reporting API**: read-only aggregation & surfacing of model outcomes / metrics.
6. **Frontend**: Vite/React app with Firebase auth and reporting & run triggers.
7. **Infrastructure as Code**: Terraform for topics, subscriptions, datasets, tables, service accounts.

## 3. Core Data Assets (BigQuery)
- `standard_events` (canonical raw events)
- `lift_analysis_results` (per model run outputs: effect, confidence, metadata)
- `job_status` (orchestration lifecycle + timestamps)
- `causal_model_registry` (planned: model definitions, versions, lineage)

## 4. Key Services & Packages
| Service | Location | Purpose |
|---------|----------|---------|
| Ingestion API | `ingestion_api/` | Event collection & authentication |
| Ingestion Subscriber | `ingestion_subscriber/` | Pub/Sub → BigQuery ETL |
| Control Plane API | `control_plane_api/` | Analysis job orchestration |
| Causal Engine Worker | `causal_engine/` | Containerized causal models |
| Reporting API | `backend/` | Results aggregation & serving |
| Frontend | `frontend/` | React dashboard & job triggers |
| Common Auth & Settings | `common/` | Firebase token verification & centralized settings |
| Orchestration | `orchestration/airflow/` | Workflow management & scheduling |
| Infra | `terraform/` | Topics, subs, datasets, tables, service accounts |

## 5. Data & Job Lifecycle
1. Client emits event to Ingestion API (Firebase auth) OR uploads batch to GCS (signed URL).
2. API publishes normalized message to Pub/Sub with `insertId` for idempotency.
3. Subscriber writes rows to `standard_events` (dedup by insertId). (Beam pipeline may also feed/enrich.)
4. User (or schedule) hits Control Plane `POST /v1/analysis/run` specifying `model_name` + params.
5. Pub/Sub delivers job to Causal Engine Worker. Worker loads config & parameters, runs model (DID/PSM/DML).
6. Worker writes lift metrics to `lift_analysis_results`, metadata to `job_status` (+ model registry).
7. Reporting API exposes aggregated metrics / health; Frontend renders charts and run status.

## 6. Getting Started (Local)

Prereqs: Python 3.12, Node 18+, gcloud auth (for GCP resources), Docker (optional), Firebase CLI (optional).

### 6.1 Create & Activate Virtualenv
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 6.2 Run Control Plane API
```bash
export GCP_PROJECT=your-project
cd control_plane_api
pip install -r requirements.txt
uvicorn app:app --port 8082 --reload &
```

### 6.3 Run Causal Engine Worker
```bash
export GCP_PROJECT=your-project
export BIGQUERY_DATASET=cfap_analytics
python -m causal_engine.worker
```

### 6.4 Test Model Execution
```bash
# Direct model execution
python -m causal_engine.main --client-id test_client --model did --params '{"campaign_id":"test_campaign","split_date":"2024-01-15"}'

# Via Control Plane API
curl -X POST localhost:8082/v1/analysis/run \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_FIREBASE_TOKEN' \
  -d '{"model_name":"did","params":{"campaign_id":"xyz-123","split_date":"2024-01-15"}}'
```

### 6.5 Verify Architecture
```bash
# Run comprehensive verification script
python verify_causal_engine.py

# Run tests
pip install pytest
python -m pytest tests/ -v
```

## 7. Causal Models

### Current Models
- **Difference-in-Differences (DID)**: For measuring lift from natural experiments and geo-tests
- More models coming: Synthetic Control, Propensity Score Matching, Double Machine Learning (DML), Bayesian MMM

### Model Contract
- **Input**: parameter dict, BigQuery client handle, project & dataset, time bounds / identifiers
- **Output**: effect size(s), confidence interval(s), diagnostics metadata, persisted row(s) in `lift_analysis_results`
- **Registration**: Automatic model registry with `model_name`, version, hyperparams, code ref

### Adding New Models
```python
from causal_engine.base import CausalModelBase, model_registry

class MyCustomModel(CausalModelBase):
    def load_data(self) -> pd.DataFrame:
        # Load your data
        pass
    
    def run_analysis(self, data: pd.DataFrame) -> pd.DataFrame:
        # Run your analysis
        pass

# Register the model
model_registry.register('my_model', MyCustomModel)
```

## 8. Containerized Deployment

### Build Causal Engine Image
```bash
cd causal_engine
docker build -t gcr.io/your-project/causal-engine:latest .
docker push gcr.io/your-project/causal-engine:latest
```

### Deploy to Cloud Run
```bash
gcloud run deploy causal-engine \
  --image gcr.io/your-project/causal-engine:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars GCP_PROJECT=your-project,ANALYSIS_SUBSCRIPTION=run-analysis-worker
```

### Deploy to Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: causal-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: causal-engine
  template:
    metadata:
      labels:
        app: causal-engine
    spec:
      containers:
      - name: causal-engine
        image: gcr.io/your-project/causal-engine:latest
        env:
        - name: GCP_PROJECT
          value: your-project
        - name: ANALYSIS_SUBSCRIPTION
          value: run-analysis-worker
```

## 9. Orchestration with Airflow

### Deploy DAGs to Cloud Composer
```bash
cd orchestration/airflow/dags
zip -r ../dags.zip .
gsutil cp ../dags.zip gs://your-composer-dags-bucket/
```

### Trigger Analysis Workflow
```python
from airflow.models import DagBag
from airflow import configuration

dag_bag = DagBag()
dag = dag_bag.get_dag('causal_analysis_workflow')

# Trigger with configuration
dag.create_dagrun(
    run_id=f'manual_{datetime.now().isoformat()}',
    conf={
        'job_id': 'analysis_123',
        'model_name': 'did',
        'params': {'campaign_id': 'campaign_123', 'split_date': '2024-01-15'}
    }
)
```

## 10. Security & Auth
- Primary auth: Firebase ID token (all ingestion & control operations)
- API key fallback: legacy path (will be disabled in production mode)
- Idempotency: `insertId` per event row
- Principle of Least Privilege: separate service accounts for worker vs ingestion
- To do: signed model artifacts, HMAC option, audit logging, structured log & metrics exporter

## 11. Configuration & Environment

Key environment variables:
- `GCP_PROJECT`: Google Cloud project ID
- `BIGQUERY_DATASET`: BigQuery dataset for analytics (default: cfap_analytics)
- `ANALYSIS_TOPIC`: Pub/Sub topic for analysis jobs (default: run-analysis-jobs)
- `ANALYSIS_SUBSCRIPTION`: Pub/Sub subscription for workers (default: run-analysis-worker)
- `FIREBASE_PROJECT`: Firebase project for authentication
- `ENVIRONMENT`: deployment environment (development/production)

## 12. Directory Map

```
backend/                    FastAPI legacy backend & analysis helpers
control_plane_api/          Analysis job orchestration API
causal_engine/              Containerized causal models & worker
  ├── base.py              Plugin architecture & model registry
  ├── main.py              CLI entry point for models
  ├── worker.py            Pub/Sub worker for async processing
  ├── models/              Model implementations
  │   └── did.py          Difference-in-Differences model
  └── Dockerfile          Container build definition
common/                     Shared authentication & settings
  ├── auth.py             Firebase token verification
  └── settings.py         Centralized configuration
orchestration/airflow/      Workflow orchestration
  └── dags/               Airflow DAG definitions
tests/                      Test suite for causal engine
ingestion_api/              Client event ingestion
ingestion_subscriber/       Pub/Sub push → BigQuery writer
dataflow/                   Beam pipeline transforms & tests
reporting_api/              Read-only analytics service (planned)
frontend/                   React + Vite app
terraform/                  IaC definitions & table schemas
schemas/                    (Legacy) raw schema references (to be consolidated)
connectors/                 Source connectors (e.g., Shopify)
retraining_job/             Batch retraining / scheduled job scaffold
```
## 13. Architecture Pillars Alignment

This implementation fully aligns with the vision's core architectural pillars:

### Modularity and Extensibility ✅
- Plugin-based model registry enables adding new models with minimal friction
- Standardized `CausalModelBase` interface ensures consistency
- Models are self-contained and independently deployable

### Orchestrated and Event-Driven ✅
- Pub/Sub integration for asynchronous job processing
- Airflow DAGs for complex workflow orchestration
- Control Plane API for job scheduling and management

### Scalability and Performance ✅
- Containerized models can scale horizontally
- BigQuery-native data processing for petabyte-scale datasets
- Parallel model execution across multiple workers

### Reproducibility and Transparency ✅
- Every analysis has unique `analysis_id` for tracking
- Data hashing ensures exact reproducibility
- Complete metadata logging for audit trails
- Model parameters and versions tracked

### Self-Improvement and Learning (Framework Ready) ✅
- Model registry designed for version management
- Standardized results schema for benchmark aggregation
- Architecture supports Bayesian priors integration
- Hyperparameter tuning framework ready

## 14. API Reference

### Control Plane API Endpoints

#### Submit Analysis Job
```bash
POST /v1/analysis/run
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "model_name": "did",
  "params": {
    "campaign_id": "campaign_123",
    "split_date": "2024-01-15",
    "treatment_channel": "paid_search"
  },
  "priority": 5
}
```

#### Get Job Status
```bash
GET /v1/analysis/{job_id}/status
Authorization: Bearer <firebase_token>
```

#### List Jobs
```bash
GET /v1/analysis/jobs?status=completed&limit=50
Authorization: Bearer <firebase_token>
```

#### List Available Models
```bash
GET /v1/models
```

## 15. Development & Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest

# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_causal_engine.py::TestDIDModel -v
```

### Development Workflow
```bash
# 1. Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r control_plane_api/requirements.txt

# 2. Start services
export GCP_PROJECT=your-project
uvicorn control_plane_api.app:app --port 8082 --reload &
python -m causal_engine.worker &

# 3. Test the system
python verify_causal_engine.py

# 4. Submit a test job
curl -X POST localhost:8082/v1/analysis/run \
  -H 'Content-Type: application/json' \
  -d '{"model_name":"did","params":{"campaign_id":"test"}}'
```

## 16. Roadmap

### Immediate (Next Releases)
- [ ] Synthetic Control model implementation
- [ ] Propensity Score Matching (PSM) model
- [ ] Double Machine Learning (DML) model
- [ ] Benchmark system integration
- [ ] Vertex AI Training integration

### Short Term
- [ ] Bayesian Mixed Media Model (MMM)
- [ ] Causal discovery with gCastle/DoWhy
- [ ] Advanced feature engineering pipeline
- [ ] Real-time model monitoring
- [ ] A/B test integration

### Long Term
- [ ] AutoML for causal model selection
- [ ] Multi-armed bandit optimization
- [ ] Graph neural networks for attribution
- [ ] Federated learning across clients
- [ ] Real-time streaming analysis

## 17. Contributing

### Adding a New Model
1. Create model class inheriting from `CausalModelBase`
2. Implement `load_data()` and `run_analysis()` methods
3. Register model in `causal_engine/models/__init__.py`
4. Add tests in `tests/test_your_model.py`
5. Update documentation

### Code Style
- Use type hints for all functions
- Add docstrings following Google style
- Run `black` for code formatting
- Ensure tests pass before submitting PR

## 18. Support / Questions

For questions about the causal engine architecture or implementation:
- Create an issue with the `causal-engine` label
- Include reproduction steps and error logs
- Specify which model and parameters you're using

For general CFAP platform questions:
- Create an issue with the `platform` label
- Include your use case and expected behavior

---

## Legacy Documentation & Migration Notes

### Terraform Setup
=======
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

### Firebase Configuration
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

### Firebase Login
To interact with Firebase (hosting, deploys) you can login locally or generate a CI token.

- Interactive: `./scripts/firebase_login.sh`
- CI token: `./scripts/firebase_login.sh --ci`

The script uses `npx firebase-tools` so Node.js must be installed.

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
