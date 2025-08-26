from fastapi import FastAPI, Request, HTTPException
import base64
import json
import os
import logging
from google.cloud import bigquery

logger = logging.getLogger("ingestion_subscriber")
logger.setLevel(logging.INFO)

app = FastAPI()
BQ_TABLE = os.getenv("TARGET_TABLE")  # e.g. my-project:cfap_analytics.standard_events

bq = bigquery.Client()


@app.post("/pubsub/push")
async def pubsub_push(req: Request):
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

    row = {
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

    if not BQ_TABLE:
        logger.error("TARGET_TABLE not configured")
        raise HTTPException(status_code=500, detail="Server not configured")

    try:
        errors = bq.insert_rows_json(BQ_TABLE, [row])
        if errors:
            logger.error("BigQuery insert errors: %s", errors)
            raise HTTPException(status_code=500, detail="BigQuery insert error")
    except Exception as exc:
        logger.exception("Failed writing to BigQuery: %s", exc)
        raise HTTPException(status_code=502, detail="BigQuery write failed")

    return {"status": "ok"}
