from typing import Any, Dict, List, Optional
import os
import json
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from google.cloud import pubsub_v1

logger = logging.getLogger("ingestion_api")
logger.setLevel(logging.INFO)

PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "raw-events")

publisher = pubsub_v1.PublisherClient()
if PROJECT_ID:
    topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
else:
    topic_path = None

app = FastAPI(title="CFAP Ingestion API")


class CFAPEvent(BaseModel):
    event_id: str = Field(..., description="Unique event id")
    user_anonymous_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: str
    event_type: str
    source_platform: str
    marketing_channel: Optional[str] = None
    campaign_id: Optional[str] = None
    revenue_usd: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None

    @validator("event_type", "source_platform")
    def not_empty(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError("must be a non-empty string")
        return v


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/events", status_code=202)
async def ingest_events(events: List[CFAPEvent]):
    if not PROJECT_ID or not topic_path:
        logger.error("GCP project or topic not configured (GCP_PROJECT/PUBSUB_TOPIC)")
        raise HTTPException(status_code=500, detail="Server Pub/Sub not configured")

    publish_futures = []
    published = 0
    try:
        for ev in events:
            payload = json.dumps(ev.dict(), default=str).encode("utf-8")
            attrs = {
                "event_type": ev.event_type,
                "source_platform": ev.source_platform,
            }
            future = publisher.publish(topic_path, payload, **attrs)
            publish_futures.append(future)
            published += 1

        for fut in publish_futures:
            fut.result(timeout=30)

        logger.info("Published %d events to %s", published, topic_path)
        return {"accepted": published}
    except Exception as exc:
        logger.exception("Failed to publish events: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to publish events to Pub/Sub")
