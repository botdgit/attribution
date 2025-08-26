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
from typing import Dict, Any

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions


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


def to_canonical(raw: str) -> Dict[str, Any]:
    """Map raw event JSON (string) to canonical row dict for BigQuery."""
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


class ParsePubSubMessage(beam.DoFn):
    def process(self, element, *args, **kwargs):
        try:
            if isinstance(element, (bytes, bytearray)):
                payload = element.decode("utf-8")
            elif isinstance(element, dict) and "data" in element:
                import base64
                payload = base64.b64decode(element["data"]).decode("utf-8")
            else:
                payload = str(element)
            yield to_canonical(payload)
        except Exception as e:
            logger.exception("Failed parsing message: %s", e)


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--input_topic", required=True, help="Pub/Sub topic full path e.g. projects/PROJECT/topics/raw-events")
    parser.add_argument("--output_table", required=True, help="BigQuery table PROJECT:dataset.table")
    parser.add_argument("--runner", default="DataflowRunner", help="DataflowRunner or DirectRunner")
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--temp_location", default=None)
    parser.add_argument("--staging_location", default=None)

    known_args, pipeline_args = parser.parse_known_args(argv)
    options = PipelineOptions(pipeline_args, save_main_session=True, streaming=True, project=known_args.project, runner=known_args.runner)
    if known_args.temp_location:
        options.view_as(SetupOptions).save_main_session = True

    table_spec = known_args.output_table
    table_schema = {
        "fields": [
            {"name": name, "type": typ, "mode": "NULLABLE"} for name, typ in CANONICAL_SCHEMA
        ]
    }

    with beam.Pipeline(options=options) as p:
        (
            p
            | "ReadFromPubSub" >> beam.io.ReadFromPubSub(topic=known_args.input_topic).with_output_types(bytes)
            | "ParseToCanonical" >> beam.ParDo(ParsePubSubMessage())
            | "WriteToBQ" >> beam.io.WriteToBigQuery(
                table_spec,
                schema=table_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS,
            )
        )


if __name__ == "__main__":
    run()
