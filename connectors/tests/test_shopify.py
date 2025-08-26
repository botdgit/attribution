from connectors.shopify import ShopifyConnector


def test_shopify_connector_transforms():
    conn = ShopifyConnector(api_key="FAKE", shop="example.myshopify.com", state_store=".test_state.json")
    results = list(conn.run())
    assert len(results) >= 1
    assert results[0]["event_type"] == "purchase"
    assert "event_id" in results[0]
