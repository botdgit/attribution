from fastapi import FastAPI, HTTPException, Depends
from common.firebase_auth import verify_firebase_token
from typing import Optional, Dict, Any, List
import os
import time
import logging

try:
    import redis
except Exception:
    redis = None

app = FastAPI(title="CFAP Reporting API")

logger = logging.getLogger("reporting_api")
logger.setLevel(logging.INFO)

# Simple in-memory TTL cache for small result sets. In production, use Memorystore/Redis.
_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = int(os.environ.get("REPORT_CACHE_TTL", "30"))  # seconds


def get_redis_client():
    host = os.environ.get("REDIS_HOST")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    if not host or not redis:
        return None
    try:
        rc = redis.Redis(host=host, port=port, socket_connect_timeout=2)
        rc.ping()
        return rc
    except Exception:
        logger.exception("Failed to connect to Redis at %s:%s", host, port)
        return None


def get_bq_client():
    try:
        from google.cloud import bigquery

        return bigquery.Client()
    except Exception:
        logger.exception("BigQuery client unavailable")
        raise HTTPException(status_code=500, detail="BigQuery client unavailable")


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    rc = get_redis_client()
    if rc:
        try:
            val = rc.get(key)
            if val is None:
                return None
            import json

            return json.loads(val)
        except Exception:
            logger.exception("Redis get failed, falling back to in-memory cache")

    rec = _CACHE.get(key)
    if not rec:
        return None
    if time.time() - rec["ts"] > CACHE_TTL:
        del _CACHE[key]
        return None
    return rec["value"]


def _cache_set(key: str, value: Dict[str, Any]):
    rc = get_redis_client()
    if rc:
        try:
            import json

            rc.setex(key, CACHE_TTL, json.dumps(value))
            return
        except Exception:
            logger.exception("Redis set failed, falling back to in-memory cache")

    _CACHE[key] = {"ts": time.time(), "value": value}


def _mock_response() -> Dict[str, List[Dict[str, Any]]]:
    return {"rows": [{"event_type": "purchase", "count": 42, "revenue_usd": 420.0}]}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/metrics/events")
def events(start_date: Optional[str] = None, end_date: Optional[str] = None, client=Depends(get_bq_client), _auth=Depends(verify_firebase_token)) -> Dict[str, List[Dict[str, Any]]]:
    """Return pre-aggregated metrics from result tables.

    This endpoint reads only from pre-computed result tables (e.g., attribution_daily)
    to avoid expensive ad-hoc queries. For local dev, set RUNNING_LOCAL=true.
    """
    if os.environ.get("RUNNING_LOCAL", "false").lower() in ("1", "true"):
        return _mock_response()

    cache_key = f"events:{start_date}:{end_date}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        project = client.project
        dataset = os.environ.get("RESULT_DATASET", "cfap_results")
        table = os.environ.get("RESULT_TABLE_EVENTS", "attribution_daily")

        # Use partitioned / clustered result tables. Query only small time window if provided.
        sql = f"SELECT event_type, count, revenue_usd FROM `{project}.{dataset}.{table}` ORDER BY count DESC LIMIT 100"
        job = client.query(sql)
        rows = [dict(r) for r in job]
        out = {"rows": rows}
        _cache_set(cache_key, out)
        return out
    except Exception as e:
        logger.exception("Reporting query failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/analysis/lift")
def lift_analysis(limit: int = 50, client=Depends(get_bq_client), _auth=Depends(verify_firebase_token)) -> Dict[str, List[Dict[str, Any]]]:
    """Return recent lift analysis results from the causal engine."""
    if os.environ.get("RUNNING_LOCAL", "false").lower() in ("1", "true"):
        return {"rows": [{"campaign_id": "xyz", "lift_estimate": 0.42}]}

    cache_key = f"lift:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        project = client.project
        dataset = os.environ.get("RESULT_DATASET", "cfap_analytics")
        table = os.environ.get("RESULT_TABLE_LIFT", "lift_analysis_results")
        sql = f"SELECT analysis_id, model_name, campaign_id, lift_estimate, confidence_interval_low, confidence_interval_high, analysis_timestamp FROM `{project}.{dataset}.{table}` ORDER BY analysis_timestamp DESC LIMIT @limit"
        job_config = None
        try:
            from google.cloud import bigquery

            job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("limit", "INT64", limit)])
        except Exception:
            job_config = None

        job = client.query(sql, job_config=job_config) if job_config else client.query(sql)
        rows = [dict(r) for r in job]
        out = {"rows": rows}
        _cache_set(cache_key, out)
        return out
    except Exception as e:
        logger.exception("Lift analysis query failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
