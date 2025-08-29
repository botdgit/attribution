from fastapi import FastAPI, Request, HTTPException, Depends
import base64
import json
import os
import logging
from typing import Any, Dict
from common.firebase_auth import verify_firebase_token

logger = logging.getLogger("ingestion_subscriber")
logger.setLevel(logging.INFO)

app = FastAPI(title="CFAP Ingestion Subscriber")
BQ_TABLE = os.getenv("TARGET_TABLE")  # e.g. my-project:cfap_analytics.standard_events
MAX_BATCH = int(os.getenv("SUBSCRIBER_MAX_BATCH", "50"))


def get_bigquery_client():
    try:
        from google.cloud import bigquery

        return bigquery.Client()
    except Exception:
        logger.exception("google-cloud-bigquery not installed or misconfigured")
        raise HTTPException(status_code=500, detail="BigQuery client unavailable")


def _normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event_id": event.get("event_id") or event.get("id"),
        "user_anonymous_id": event.get("user_anonymous_id"),
        "user_id": event.get("user_id"),
        "timestamp": event.get("timestamp"),
        "event_type": event.get("event_type"),
        "source_platform": event.get("source_platform"),
        "marketing_channel": event.get("marketing_channel"),
        "campaign_id": event.get("campaign_id"),
        "revenue_usd": event.get("revenue_usd"),
        "properties": json.dumps(event.get("properties", {})) if event.get("properties") is not None else None,
    }


@app.post("/pubsub/push")
async def pubsub_push(req: Request, bq=Depends(get_bigquery_client), _auth=Depends(verify_firebase_token)):
    """Cloud Run push endpoint for Pub/Sub push subscriptions.

    This endpoint performs minimal validation and writes the canonical row to BigQuery.
    It should be idempotent if the BigQuery table has an insert-id or dedupe logic downstream.
    """
    payload = await req.json()
    msg = payload.get("message")
    if not msg:
        raise HTTPException(status_code=400, detail="No message in request")

    data_b64 = msg.get("data", "")
    if not data_b64:
        raise HTTPException(status_code=400, detail="No data in Pub/Sub message")

    try:
        raw = base64.b64decode(data_b64).decode("utf-8")
        event = json.loads(raw)
    except Exception as exc:
        logger.exception("Invalid message payload: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid payload")

    row = _normalize_event(event)
    # Attach insertId for idempotency (currently reuse event_id)
    insert_id = row.get("event_id")

    if not BQ_TABLE:
        logger.error("TARGET_TABLE not configured")
        raise HTTPException(status_code=500, detail="Server not configured")

    try:
        # For now single-row insert with insertId list; can extend to batch accumulation.
        errors = bq.insert_rows_json(BQ_TABLE, [row], row_ids=[insert_id] if insert_id else None)
        if errors:
            logger.error("BigQuery insert errors: %s", errors)
            # 409-like errors should be handled idempotently by downstream logic; surface a server error here
            raise HTTPException(status_code=500, detail="BigQuery insert error")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed writing to BigQuery: %s", exc)
        raise HTTPException(status_code=502, detail="BigQuery write failed")

    return {"status": "ok"}
