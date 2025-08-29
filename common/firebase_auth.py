"""Shared Firebase JWT verification helper.

Provides a FastAPI dependency that validates Firebase ID tokens using the
firebase_admin SDK. If no token is provided and RUNNING_LOCAL=true, the
dependency will allow access for local development.
"""
from fastapi import Request, HTTPException
import os
import logging

logger = logging.getLogger("firebase_auth")


def _ensure_firebase_initialized():
    try:
        import firebase_admin
        from firebase_admin import auth as _auth
    except Exception as e:
        logger.exception("firebase_admin not available: %s", e)
        raise HTTPException(status_code=500, detail="Authentication subsystem unavailable")

    if not firebase_admin._apps:
        try:
            # initialize with default credentials (ADC). In CI/prod, ensure service account via Workload Identity.
            firebase_admin.initialize_app()
        except Exception as e:
            logger.exception("Failed to initialize firebase_admin: %s", e)
            raise HTTPException(status_code=500, detail="Authentication initialization failed")
    return _auth


def verify_firebase_token(request: Request):
    """FastAPI dependency to verify Firebase ID tokens.

    Usage: add as Depends(verify_firebase_token) to require authentication.
    """
    # Allow bypass in local dev for convenience
    if os.environ.get("RUNNING_LOCAL", "false").lower() in ("1", "true"):
        return {"uid": "local-dev"}

    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")
    token = auth_header.split(None, 1)[1].strip()

    auth = _ensure_firebase_initialized()
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token")
    except Exception as e:
        logger.exception("Failed verifying Firebase token: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
