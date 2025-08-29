from fastapi import FastAPI, Depends, Response
from pydantic import BaseModel

from auth import get_current_user
import os
import json
import httpx
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, Integer, String, DateTime, create_engine, select
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

Base = declarative_base()


class ShopifyToken(Base):
    __tablename__ = "shopify_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_domain = Column(String(255), unique=True, nullable=False)
    access_token = Column(String(255), nullable=False)
    scope = Column(String(1024), nullable=True)
    user_id = Column(String(255), nullable=True)  # firebase uid if available
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _get_engine():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Fallback to local sqlite for development
        db_path = os.path.join(os.path.dirname(__file__), "shopify.db")
        db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, future=True)
    return engine


ENGINE = _get_engine()
try:
    Base.metadata.create_all(ENGINE)
except Exception:
    pass

app = FastAPI()

# Simple in-memory state store for Shopify OAuth (dev only)
_SHOPIFY_OAUTH_STATES: set[str] = set()


@app.get("/health")
def health():
    return {"status": "ok"}


class DIDRequest(BaseModel):
    campaign_id: str


@app.post("/api/analysis/did", dependencies=[Depends(get_current_user)])
def execute_did(request: DIDRequest):
    # import inside function to avoid heavy imports at module import time
    from analysis import run_did_analysis
    result = run_did_analysis("cfap-platform-dev", request.campaign_id)
    return result


@app.get("/shopify/callback")
async def shopify_callback(request: Request, response: Response):
    """
    Shopify OAuth callback handler.
    Expects query params: code, shop
    Exchanges code for access token and stores it locally (dev).
    """
    code = request.query_params.get("code")
    shop = request.query_params.get("shop")
    state = request.query_params.get("state")
    if not code or not shop:
        raise HTTPException(status_code=400, detail="Missing code or shop parameter")
    if state and state not in _SHOPIFY_OAUTH_STATES:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    if state in _SHOPIFY_OAUTH_STATES:
        _SHOPIFY_OAUTH_STATES.discard(state)

    client_id = os.environ.get("SHOPIFY_API_KEY")
    client_secret = os.environ.get("SHOPIFY_API_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Shopify API credentials not configured on the server")

    test_mode = os.environ.get("SHOPIFY_TEST_MODE") == "1"
    if test_mode:
        data = {"access_token": "test_access_token", "scope": "read_orders,read_customers"}
    else:
        token_url = f"https://{shop}/admin/oauth/access_token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, json=payload, timeout=30.0)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Failed to exchange code: {resp.status_code} {resp.text}")
        data = resp.json()

    # Optional user association via Authorization header (Firebase id token)
    user_id = None
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            from firebase_admin import auth as fb_auth
            decoded = fb_auth.verify_id_token(token)
            user_id = decoded.get("uid")
        except Exception:
            pass

    # Upsert token in DB
    with Session(ENGINE) as session:
        existing = session.execute(select(ShopifyToken).where(ShopifyToken.shop_domain == shop)).scalar_one_or_none()
        if existing:
            existing.access_token = data.get("access_token")
            existing.scope = data.get("scope")
            if user_id:
                existing.user_id = user_id
        else:
            session.add(ShopifyToken(
                shop_domain=shop,
                access_token=data.get("access_token"),
                scope=data.get("scope"),
                user_id=user_id,
            ))
        session.commit()

    frontend_base = os.environ.get("FRONTEND_BASE_URL")
    if frontend_base:
        success_url = f"{frontend_base.rstrip('/')}/shopify/connected?shop={shop}"
        return RedirectResponse(success_url)
    return {"shop": shop, "token": {"access_token": data.get("access_token"), "scope": data.get("scope")}}


@app.get("/api/integrations/shopify", dependencies=[Depends(get_current_user)])
def get_shopify_integration(user=Depends(get_current_user)):
    uid = user.get("uid") if isinstance(user, dict) else None
    with Session(ENGINE) as session:
        rec = session.execute(select(ShopifyToken).where(ShopifyToken.user_id == uid)).scalar_one_or_none()
        if not rec:
            return {"connected": False}
        return {"connected": True, "shop": rec.shop_domain, "scope": rec.scope}


@app.get("/shopify/install")
def shopify_install(shop: str, request: Request):
    """Initiate Shopify OAuth install flow.
    /shopify/install?shop=your-store.myshopify.com
    Requires env: SHOPIFY_API_KEY, (optional) SHOPIFY_SCOPES, BACKEND_PUBLIC_URL
    """
    client_id = os.environ.get("SHOPIFY_API_KEY")
    if not client_id:
        raise HTTPException(status_code=500, detail="SHOPIFY_API_KEY not configured")
    scopes = os.environ.get("SHOPIFY_SCOPES", "read_orders,read_customers")
    backend_base = os.environ.get("BACKEND_PUBLIC_URL") or str(request.base_url).rstrip('/')
    redirect_uri = f"{backend_base}/shopify/callback"
    state = secrets.token_urlsafe(16)
    _SHOPIFY_OAUTH_STATES.add(state)
    authorize_url = (
        f"https://{shop}/admin/oauth/authorize?client_id={client_id}"
        f"&scope={scopes}&redirect_uri={redirect_uri}&state={state}"
    )
    return RedirectResponse(authorize_url)
