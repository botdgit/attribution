FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (reuse backend requirements for now)
COPY backend/requirements.txt ./requirements.txt

# Add additional ML and causal inference dependencies
RUN echo "pandas-gbq" >> requirements.txt && \
    echo "numpy" >> requirements.txt && \
    echo "scipy" >> requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY causal_engine ./causal_engine
COPY common ./common

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default environment variables (can be overridden at deploy time)
ENV GCP_PROJECT=cfap-platform-dev
ENV BIGQUERY_DATASET=cfap_analytics
ENV ANALYSIS_SUBSCRIPTION=run-analysis-worker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import causal_engine; print('OK')" || exit 1

# Default command runs the worker
CMD ["python", "-m", "causal_engine.worker"]