"""Connector package for CFAP ingestion layer.

Exports available connector implementations. Adding this file makes the
`connectors` directory a proper Python package so tests and applications can
`import connectors.shopify` without manipulating `PYTHONPATH`.
"""

from .shopify import ShopifyConnector  # noqa: F401
from .base import Connector  # noqa: F401
