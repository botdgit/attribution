"""Minimal Apache Beam pipeline (Dataflow) scaffold.
- Reads messages from a Pub/Sub topic (JSON payloads).
- Parses & maps to the canonical CFAP schema.
- Writes to BigQuery (streaming inserts / batch load).
Usage (local test):
  python beam_pipeline.py \
    --project=YOUR_PROJECT_ID \
    --runner=DirectRunner \
    --input_topic=projects/YOUR_PROJECT_ID/topics/raw-events \
    --output_table=YOUR_PROJECT_ID:cfap_analytics.standard_events
For Dataflow:
  set runner=DataflowRunner and supply --temp_location, --region, --staging_location.
"""
from __future__ import annotations
import argparse
import json
import logging
from typing import Dict, Any, Optional

# Delay importing apache_beam until run() so unit tests can import helpers without heavy deps

beam = None
PipelineOptions = None
SetupOptions = None


logger = logging.getLogger("beam_pipeline")
logger.setLevel(logging.INFO)


CANONICAL_SCHEMA = [
    ("event_id", "STRING"),
    ("user_anonymous_id", "STRING"),
    ("user_id", "STRING"),
    ("timestamp", "TIMESTAMP"),
    ("event_type", "STRING"),
    ("source_platform", "STRING"),
    ("marketing_channel", "STRING"),
    ("campaign_id", "STRING"),
    ("revenue_usd", "FLOAT"),
    ("properties", "STRING"),
]


def is_valid_row(row: Dict[str, Any]) -> bool:
    # Basic validation: must have event_id, timestamp, event_type, source_platform
    return bool(row.get("event_id") and row.get("timestamp") and row.get("event_type") and row.get("source_platform"))


def to_canonical(raw: str) -> Dict[str, Any]:
    obj = json.loads(raw)
    row = {
        "event_id": obj.get("event_id") or obj.get("id"),
        "user_anonymous_id": obj.get("user_anonymous_id"),
        "user_id": obj.get("user_id"),
        "timestamp": obj.get("timestamp"),
        "event_type": obj.get("event_type"),
        "source_platform": obj.get("source_platform"),
        "marketing_channel": obj.get("marketing_channel"),
        "campaign_id": obj.get("campaign_id"),
        "revenue_usd": obj.get("revenue_usd"),
        "properties": json.dumps(obj.get("properties", {})) if obj.get("properties") is not None else None,
    }
    return row


# ParsePubSubMessage and ToJson are defined inside run() only when apache_beam is available.


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--input_topic", required=True, help="Pub/Sub topic full path e.g. projects/PROJECT/topics/raw-events")
    parser.add_argument("--output_table", required=True, help="BigQuery table PROJECT:dataset.table")
    parser.add_argument("--runner", default="DataflowRunner", help="DataflowRunner or DirectRunner")
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--temp_location", default=None)
    parser.add_argument("--staging_location", default=None)
    parser.add_argument("--dead_letter_topic", default="")
    parser.add_argument("--dedupe", action="store_true")

    known_args, pipeline_args = parser.parse_known_args(argv)

    # Import apache_beam only when executing the pipeline.
    global beam, PipelineOptions, SetupOptions
    try:
        import apache_beam as beam
        from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
    except Exception as e:
        raise RuntimeError("apache-beam is required to run the pipeline: %s" % e)

    options = PipelineOptions(pipeline_args, save_main_session=True, streaming=True, project=known_args.project, runner=known_args.runner)
    if known_args.temp_location:
        options.view_as(SetupOptions).save_main_session = True

    # Define DoFns now that beam is available
    class ParsePubSubMessage(beam.DoFn):
        def process(self, element, *args, **kwargs):
            try:
                attrs = {}
                payload = None
                # element may be bytes (data-only) or a Pub/Sub message dict with 'data' and 'attributes'
                if isinstance(element, (bytes, bytearray)):
                    payload = element.decode("utf-8")
                elif isinstance(element, dict) and "data" in element:
                    import base64

                    payload = base64.b64decode(element["data"]).decode("utf-8")
                    attrs = element.get("attributes", {}) or {}
                else:
                    payload = str(element)

                row = to_canonical(payload)
                # attach insert_id from attributes if present
                insert_id = attrs.get("insert_id")
                if insert_id:
                    row["_insert_id"] = insert_id
                yield row
            except Exception as e:
                logger.exception("Failed parsing message: %s", e)


    class ToJson(beam.DoFn):
        def process(self, element: Dict[str, Any]):
            yield json.dumps(element).encode("utf-8")

    table_spec = known_args.output_table
    table_schema = {
        "fields": [{"name": name, "type": typ, "mode": "NULLABLE"} for name, typ in CANONICAL_SCHEMA]
    }

    with beam.Pipeline(options=options) as p:
        raw = p | "ReadFromPubSub" >> beam.io.ReadFromPubSub(topic=known_args.input_topic).with_output_types(bytes)

        parsed = raw | "ParseToCanonical" >> beam.ParDo(ParsePubSubMessage())

        # Partition into valid and invalid rows
        def _is_valid(row):
            return 0 if is_valid_row(row) else 1

        valid, invalid = parsed | "PartitionValid" >> beam.Partition(_is_valid, 2)

        # Send invalid rows to dead-letter topic if configured
        if known_args.dead_letter_topic:
            (invalid | "Invalid->JSON" >> beam.ParDo(ToJson()) | "WriteInvalidToDLQ" >> beam.io.WriteToPubSub(known_args.dead_letter_topic))

        to_write = valid

        if known_args.dedupe:
            # Deduplicate by event_id; keep the latest by timestamp
            def key_by_id(row):
                return (row.get("event_id"), row)

            def pick_latest(values):
                # values is an iterable of rows with same event_id
                latest = None
                for v in values:
                    if latest is None or v.get("timestamp", "") > latest.get("timestamp", ""):
                        latest = v
                return latest

            to_write = (
                to_write
                | "KeyByEventId" >> beam.Map(lambda r: (r.get("event_id"), r))
                | "GroupById" >> beam.GroupByKey()
                | "PickLatest" >> beam.Map(lambda kv: pick_latest(kv[1]))
            )

        # Write canonical rows to BigQuery using a DoFn that can set insertId for streaming inserts
        class BQInsertDoFn(beam.DoFn):
                def __init__(self, table_spec: str, batch_size: int = 100):
                    self.table_spec = table_spec
                    self.client = None
                    self.batch_size = int(batch_size)
                    self._batch = []  # list of rows (dict)
                    self._row_ids = []  # parallel list of row_ids or None

                def setup(self):
                    from google.cloud import bigquery

                    self.client = bigquery.Client()

                def _flush_batch(self):
                    if not self._batch:
                        return
                    try:
                        # If any row_ids are set, pass row_ids list, otherwise None
                        row_ids = None
                        if any(rid is not None for rid in self._row_ids):
                            # map None -> '' for alignment? insert_rows_json expects row_ids list or None; use None for missing
                            row_ids = [rid for rid in self._row_ids]
                        errors = self.client.insert_rows_json(self.table_spec, self._batch, row_ids=row_ids)
                        if errors:
                            logger.error("BigQuery insert errors: %s", errors)
                            # raise to let Dataflow retry/handle
                            raise RuntimeError("BigQuery insert failed")
                    finally:
                        # clear batch regardless; let retries handle failures via exception
                        self._batch = []
                        self._row_ids = []

                def process(self, element: Dict[str, Any]):
                    # element is the canonical row; optional _insert_id may be present
                    insert_id = element.pop("_insert_id", None)
                    # append to batch
                    self._batch.append(element)
                    self._row_ids.append(insert_id)

                    if len(self._batch) >= self.batch_size:
                        try:
                            self._flush_batch()
                        except Exception:
                            # re-raise to allow Dataflow retry semantics
                            raise

                def finish_bundle(self):
                    # flush any remaining rows
                    try:
                        self._flush_batch()
                    except Exception:
                        raise

        (to_write | "WriteToBQWithInsertId" >> beam.ParDo(BQInsertDoFn(table_spec)))


def build_bq_insert_payload(element: Dict[str, Any]):
    """Return (rows, row_ids) representing how we will call BigQuery's insert_rows_json.

    Used by unit tests to verify insertId handling.
    """
    elem = dict(element)
    insert_id = elem.pop("_insert_id", None)
    rows = [elem]
    row_ids = [insert_id] if insert_id else None
    return rows, row_ids


if __name__ == "__main__":
    run()
