import json
from dataflow.beam_pipeline import to_canonical, is_valid_row


def test_to_canonical_basic():
    raw = json.dumps({
        "event_id": "e1",
        "user_anonymous_id": "anon-1",
        "user_id": "user-1",
        "timestamp": "2025-01-01T00:00:00Z",
        "event_type": "purchase",
        "source_platform": "web",
        "properties": {"price": 10},
    })
    row = to_canonical(raw)
    assert row["event_id"] == "e1"
    assert row["properties"] == json.dumps({"price": 10})


def test_is_valid_row():
    good = {"event_id": "e1", "timestamp": "t", "event_type": "x", "source_platform": "web"}
    bad = {"event_id": None, "timestamp": None}
    assert is_valid_row(good)
    assert not is_valid_row(bad)
