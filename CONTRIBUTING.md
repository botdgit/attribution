# Contributing to CFAP

Thanks for your interest in contributing! This guide explains the development workflow.

## Quick Start

1. Clone and create a virtual env:
```
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```
2. Copy `.env.example` to `.env` and adjust values.
3. Run services:
   - Backend: `uvicorn backend.main:app --reload --port 8080`
   - Control Plane: `uvicorn control_plane_api.app:app --port 8082`
   - Reporting API (mock mode): `RUNNING_LOCAL=true uvicorn backend.reporting_api.app:app --port 8081`
   - Worker: `python -m causal_engine.worker`
4. Frontend:
```
cd frontend
npm ci
npm run dev
```

## Tests
Run all tests with:
```
CFAP_TEST_MODE=1 pytest -q
```

Add tests for new modules; keep external calls behind feature flags or environment checks.

## Code Style
- Prefer small, composable functions.
- Avoid hard-coding project IDs; use env vars.
- Keep network / cloud dependencies lazy-imported so local dev & tests stay fast.

## Adding a New Causal Model
1. Create `causal_engine/models/<model_name>.py` implementing `CausalModelBase`.
2. Wire into `worker.py` model dispatch.
3. Add schema updates / Terraform if new result table needed.
4. Add unit tests for `run_analysis` logic with synthetic data.

## Security
Do not commit secrets. Use Secret Manager or GitHub Actions secrets.

## Releases
CI builds containers and deploys (see `.github/workflows`). Tag versions using semantic versioning.

Happy building!
