import csv
import json
import os
from google.cloud import bigquery
from google.cloud import storage

BQ_TABLE = os.getenv('TARGET_TABLE', '')
CLIENT = bigquery.Client()


def validate_headers(headers):
    expected = [
        'event_id','user_anonymous_id','user_id','timestamp','event_type','source_platform','marketing_channel','campaign_id','revenue_usd','properties'
    ]
    return all(h in headers for h in expected)


def gcs_csv_to_bq(event, context):
    bucket_name = event['bucket']
    name = event['name']
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(name)
    content = blob.download_as_text()
    reader = csv.DictReader(content.splitlines())

    if not validate_headers(reader.fieldnames):
        raise ValueError('CSV headers do not match canonical schema')

    rows = []
    for row in reader:
        # Convert properties string to JSON if present
        if row.get('properties'):
            try:
                row['properties'] = json.loads(row['properties'])
            except Exception:
                row['properties'] = {}
        # BigQuery expects proper types; minimal casting here
        if row.get('revenue_usd'):
            try:
                row['revenue_usd'] = float(row['revenue_usd'])
            except Exception:
                row['revenue_usd'] = None
        rows.append(row)

    if not BQ_TABLE:
        raise RuntimeError('TARGET_TABLE not configured')

    errors = CLIENT.insert_rows_json(BQ_TABLE, rows)
    if errors:
        raise RuntimeError(f'BigQuery insert errors: {errors}')
