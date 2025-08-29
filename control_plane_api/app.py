from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
import json
import uuid
import logging
from typing import Optional

def get_bq_client():
    try:
        from google.cloud import bigquery

        return bigquery.Client()
    except Exception:
        return None

logger = logging.getLogger("control_plane_api")
logger.setLevel(logging.INFO)

app = FastAPI(title="CFAP Control Plane API")


class AnalysisRunRequest(BaseModel):
    model_name: str
    params: dict = {}


def get_publisher_and_topic():
    try:
        from google.cloud import pubsub_v1
    except Exception:
        return None, None

    project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    topic_name = os.environ.get("ANALYSIS_RUN_TOPIC", "run-analysis-jobs")
    pub = pubsub_v1.PublisherClient()
    topic_path = pub.topic_path(project, topic_name) if project else None
    return pub, topic_path


@app.post("/v1/analysis/run", status_code=202)
def run_analysis(req: AnalysisRunRequest):
    pub, topic = get_publisher_and_topic()
    if not pub or not topic:
        raise HTTPException(status_code=500, detail="Pub/Sub not configured")

    job_id = str(uuid.uuid4())
    payload = {"job_id": job_id, "model": req.model_name, "params": req.params}
    try:
        future = pub.publish(topic, json.dumps(payload).encode("utf-8"), job_id=job_id)
        future.result(timeout=10)
        logger.info("Published analysis job %s to %s", job_id, topic)
        return {"job_id": job_id}
    except Exception as e:
        logger.exception("Failed publishing analysis job: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/analysis/status/{job_id}")
def get_job_status(job_id: str):
    client = get_bq_client()
    if not client:
        raise HTTPException(status_code=500, detail="BigQuery client unavailable")
    dataset = os.environ.get("RESULT_DATASET", "cfap_analytics")
    table = os.environ.get("JOB_STATUS_TABLE", "job_status")
    sql = f"SELECT * FROM `{client.project}.{dataset}.{table}` WHERE job_id = @job_id ORDER BY started_at DESC LIMIT 1"
    from google.cloud import bigquery as _bq

    job_config = _bq.QueryJobConfig(query_parameters=[_bq.ScalarQueryParameter("job_id", "STRING", job_id)])
    try:
        job = client.query(sql, job_config=job_config)
        rows = [dict(r) for r in job]
        if not rows:
            raise HTTPException(status_code=404, detail="job not found")
        return rows[0]
    except Exception as e:
        logger.exception("Failed fetching job status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
