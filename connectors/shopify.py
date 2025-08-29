from __future__ import annotations
import time
from typing import Any, Dict, Iterable, List, Optional
from .base import Connector
import requests
try:
    from google.cloud import secretmanager  # type: ignore
except Exception:  # pragma: no cover - optional dependency for offline tests
    secretmanager = None


def get_secret(secret_name: str, project_id: Optional[str] = None) -> Optional[str]:
    if not secretmanager:
        return None
    try:  # pragma: no cover - network call avoided in tests
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest" if project_id else secret_name
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8")
    except Exception:
        return None


class ShopifyConnector(Connector):
    def __init__(self, api_key: Optional[str], shop: str, state_store: str = ".shopify_state.json", project_id: Optional[str] = None):
        super().__init__(state_store=state_store)
        self.project_id = project_id
        if not api_key:
            # treat api_key as secret resource name in Secret Manager
            secret_val = get_secret(api_key, project_id=project_id) if api_key else None
            self.api_key = secret_val
        else:
            self.api_key = api_key
        self.shop = shop

    def fetch(self) -> Iterable[Dict[str, Any]]:
        # Call Shopify Orders API (public REST). This implementation expects an API key
        # in the form of a private app or access token placed in Authorization header.
        # Test / offline mode: if api_key is a known placeholder value (e.g. "FAKE") or
        # environment variable CFAP_TEST_MODE is set, emit a single synthetic order so
        # unit tests don't perform network I/O.
        import os
        if (self.api_key in {None, "FAKE"}) and os.environ.get("CFAP_TEST_MODE", "false").lower() in ("1", "true"):
            yield {
                "id": 1234567890,
                "created_at": "2025-01-01T00:00:00Z",
                "total_price": "10.50",
                "customer": {"id": 987654321},
            }
            return

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Shopify-Access-Token"] = self.api_key

        url = f"https://{self.shop}/admin/api/2023-10/orders.json"
        params = {"limit": 50, "status": "any"}
        # If we have a cursor in state, we could use since_id or page_info; keep simple with paging by since_id
        since_id = self.state.get("since_id")
        if since_id:
            params["since_id"] = since_id

        while True:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            orders = data.get("orders", [])
            if not orders:
                break
            for order in orders:
                yield order
            # set since_id to last order id
            last_id = orders[-1].get("id")
            if last_id:
                self.state["since_id"] = last_id
            else:
                break
            # Shopify API rate limits; be kind
            time.sleep(0.2)

    def transform(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        # Map Shopify order to canonical CFAP event (purchase)
        return {
            "event_id": raw.get("id"),
            "user_anonymous_id": None,
            "user_id": raw.get("customer", {}).get("id"),
            "timestamp": raw.get("created_at"),
            "event_type": "purchase",
            "source_platform": "shopify",
            "marketing_channel": None,
            "campaign_id": None,
            "revenue_usd": float(raw.get("total_price", 0.0)),
            "properties": {"raw": raw},
        }
