from typing import Any, Dict, List, Optional
import os
import json
import logging
import uuid
import time
from fastapi import FastAPI, HTTPException, Request, Depends
from common.firebase_auth import verify_firebase_token
from pydantic import BaseModel, Field, validator

from google.api_core.exceptions import GoogleAPICallError
from common.settings import get_settings

# NOTE: publisher client is lazily created and injected via app.state to allow
# better testability and to avoid heavy initialization at import time.

logger = logging.getLogger("ingestion_api")
logger.setLevel(logging.INFO)

settings = get_settings()
PROJECT_ID = settings.gcp_project
PUBSUB_TOPIC = settings.pubsub_topic_raw
UPLOADS_BUCKET = settings.uploads_bucket
INGESTION_API_KEY = settings.ingestion_api_key or ""

app = FastAPI(title="CFAP Ingestion API")


class CFAPEvent(BaseModel):
    """Canonical event model accepted by ingestion endpoints.

    Lightweight validation only. Transformations are deferred to Dataflow.
    """

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


def get_publisher_and_topic():
    """Lazily create a Pub/Sub publisher client and compute topic_path.

    Returns (publisher, topic_path) or (None, None) if PROJECT_ID is not configured.
    """
    try:
        from google.cloud import pubsub_v1
    except Exception:
        logger.exception("google-cloud-pubsub not installed")
        return None, None

    publisher = getattr(app.state, "publisher", None)
    if publisher is None:
        publisher = pubsub_v1.PublisherClient()
        app.state.publisher = publisher

    if PROJECT_ID:
        topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
    else:
        topic_path = None
    return publisher, topic_path


def verify_api_key(request: Request):
    """Basic API key check for ingestion endpoints.

    Uses X-API-KEY header and value from INGESTION_API_KEY env var.
    For production, prefer Firebase Authentication / IAM.
    """
    if not INGESTION_API_KEY:
        # no key configured -> open endpoint (use with caution)
        return True
    header = request.headers.get("x-api-key") or request.headers.get("X-API-KEY")
    if header != INGESTION_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def verify_firebase_or_api_key(request: Request):
    """Allow access if either a valid Firebase ID token is present or a valid API key header is provided.

    This supports device-level API keys during migration while preferring Firebase Auth for users.
    """
    # First, try Firebase token (uses common helper which raises HTTPException on failure)
    try:
        # note: verify_firebase_token expects a Request and will raise HTTPException if invalid
        from common.firebase_auth import verify_firebase_token as _verify_fb

        # If RUNNING_LOCAL, the Firebase helper allows access; call it to respect that behavior.
        _verify_fb(request)
        return True
    except HTTPException:
        # Next, try API key
        return verify_api_key(request)
    except Exception:
        # Any other error -> deny
        raise HTTPException(status_code=401, detail="Authentication failed")


def _publish_with_retries(publisher, topic_path: str, payload: bytes, attrs: Dict[str, str], max_attempts: int = 3):
    """Publish a single message with simple exponential backoff retries.

    Raises Exception on final failure.
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            future = publisher.publish(topic_path, payload, **attrs)
            # wait for result with a timeout; will raise if publish fails
            future.result(timeout=30)
            return
        except Exception as exc:
            attempt += 1
            wait = 2 ** attempt
            logger.warning("Publish attempt %d failed, retrying in %ds: %s", attempt, wait, exc)
            time.sleep(wait)
    raise RuntimeError("Failed to publish message after retries")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/events", status_code=202)
async def ingest_events(events: List[CFAPEvent], _auth=Depends(verify_firebase_or_api_key)) -> Dict[str, int]:
    """Accept a batch of CFAPEvent, validate, and publish to Pub/Sub.

    This handler performs only validation and publishing. No transformation.
    """
    publisher, topic_path = get_publisher_and_topic()
    if not PROJECT_ID or not topic_path or not publisher:
        logger.error("GCP project or topic not configured (GCP_PROJECT/PUBSUB_TOPIC)")
        raise HTTPException(status_code=500, detail="Server Pub/Sub not configured")

    published = 0
    try:
        for ev in events:
            payload = json.dumps(ev.dict(), default=str).encode("utf-8")
            insert_id = ev.event_id or uuid.uuid4().hex
            attrs = {"event_type": ev.event_type, "source_platform": ev.source_platform, "insert_id": insert_id}
            _publish_with_retries(publisher, topic_path, payload, attrs)
            published += 1

        logger.info("Published %d events to %s", published, topic_path)
        return {"accepted": published}
    except GoogleAPICallError as exc:
        logger.exception("Pub/Sub API error publishing events: %s", exc)
        raise HTTPException(status_code=502, detail="Pub/Sub API error")
    except Exception as exc:
        logger.exception("Failed to publish events: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to publish events to Pub/Sub")


class UploadRequest(BaseModel):
    filename: str = Field(..., description="Filename including extension (e.g. data.csv)")


@app.post("/v1/uploads/url")
def generate_signed_upload_url(req: UploadRequest, _auth=Depends(verify_firebase_or_api_key)):
    """Return a V4 signed PUT URL for direct upload to GCS.

    Keeps server-side load minimal; clients PUT directly to GCS.
    """
    if not UPLOADS_BUCKET:
        raise HTTPException(status_code=500, detail="Uploads bucket not configured")

    try:
        from google.cloud import storage

        storage_client = storage.Client()
        bucket = storage_client.bucket(UPLOADS_BUCKET)
        object_name = f"uploads/{uuid.uuid4().hex}-{req.filename}"
        blob = bucket.blob(object_name)
        url = blob.generate_signed_url(version="v4", expiration=3600, method="PUT", content_type="application/octet-stream")
        return {"url": url, "object": object_name, "method": "PUT"}
    except Exception as exc:
        logger.exception("Failed to generate signed URL: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate signed URL")
