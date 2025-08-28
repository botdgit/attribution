from fastapi import FastAPI, Depends
from pydantic import BaseModel

from auth import get_current_user
import os
import json
import httpx
from fastapi import Request, HTTPException

app = FastAPI()


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
async def shopify_callback(request: Request):
    """
    Shopify OAuth callback handler.
    Expects query params: code, shop
    Exchanges code for access token and stores it locally (dev).
    """
    code = request.query_params.get("code")
    shop = request.query_params.get("shop")
    if not code or not shop:
        raise HTTPException(status_code=400, detail="Missing code or shop parameter")

    client_id = os.environ.get("SHOPIFY_API_KEY")
    client_secret = os.environ.get("SHOPIFY_API_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Shopify API credentials not configured on the server")

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

    # Persist token locally for development. In production, store securely (DB or secret manager).
    tokens_path = os.path.join(os.path.dirname(__file__), ".shopify_tokens.json")
    try:
        if os.path.exists(tokens_path):
            with open(tokens_path, "r") as f:
                tokens = json.load(f)
        else:
            tokens = {}
        tokens[shop] = data
        with open(tokens_path, "w") as f:
            json.dump(tokens, f, indent=2)
    except Exception:
        # non-fatal; proceed
        pass

    # Return token info (be careful in production)
    return {"shop": shop, "token": data}
