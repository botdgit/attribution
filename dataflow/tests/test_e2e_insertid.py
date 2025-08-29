"""E2E-like unit test: verify insertId handling for BigQuery payload builder.

This test avoids running Dataflow and BigQuery. It exercises the helper that
constructs the insert payload so we can assert insertId mapping.
"""
import os
import sys

# Ensure repo root is on sys.path for test discovery when pytest runs from different CWD
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dataflow.beam_pipeline import build_bq_insert_payload


def test_build_payload_with_insertid():
    element = {
        "event_id": "e1",
        "timestamp": "2025-08-28T00:00:00Z",
        "event_type": "purchase",
        "source_platform": "web",
        "_insert_id": "insert-123",
    }

    rows, row_ids = build_bq_insert_payload(element)
    assert isinstance(rows, list)
    assert rows[0]["event_id"] == "e1"
    assert row_ids == ["insert-123"]


def test_build_payload_without_insertid():
    element = {
        "event_id": "e2",
        "timestamp": "2025-08-28T00:00:00Z",
        "event_type": "signup",
        "source_platform": "mobile",
    }

    rows, row_ids = build_bq_insert_payload(element)
    assert isinstance(rows, list)
    assert rows[0]["event_id"] == "e2"
    assert row_ids is None
