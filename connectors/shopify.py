from __future__ import annotations
import time
from typing import Any, Dict, Iterable, List
from .base import Connector


class ShopifyConnector(Connector):
    def __init__(self, api_key: str, shop: str, state_store: str = ".shopify_state.json"):
        super().__init__(state_store=state_store)
        self.api_key = api_key
        self.shop = shop

    def fetch(self) -> Iterable[Dict[str, Any]]:
        # This is a stubbed fetch method. Replace with real requests to Shopify.
        # Use self.state to store last processed timestamp or cursor.
        dummy = [
            {"id": "order_1", "created_at": "2025-08-01T12:00:00Z", "total_price": 29.99, "customer": {"id": "cust_1"}},
            {"id": "order_2", "created_at": "2025-08-02T15:00:00Z", "total_price": 49.5, "customer": {"id": "cust_2"}},
        ]
        for item in dummy:
            time.sleep(0.01)
            yield item

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
