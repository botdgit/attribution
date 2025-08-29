FROM python:3.10-slim
WORKDIR /app
# Reuse backend dependency list for worker (contains FastAPI, GCP libs, statsmodels, etc.)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copy only what the worker needs (causal engine + common + utils + backend analysis if referenced)
COPY causal_engine ./causal_engine
COPY common ./common
# Optionally include connectors if future models use them
COPY connectors ./connectors
ENV PYTHONUNBUFFERED=1
# Default environment variables can be overridden at deploy time
ENV RESULT_DATASET=cfap_analytics
CMD ["python", "-m", "causal_engine.worker"]
