from typing import Optional
import os
import time
from google.api_core import retry as gcp_retry
from google.api_core.exceptions import GoogleAPICallError


def get_bq_table_spec(project: Optional[str], dataset: str, table: str) -> str:
    proj = project or os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    return f"{proj}.{dataset}.{table}"


def insert_rows_json_with_retries(client, table_id: str, rows: list, max_attempts: int = 3, initial_wait: float = 1.0):
    """Insert rows using BigQuery insert_rows_json with simple retries.

    table_id must be in the form 'project.dataset.table' or 'dataset.table' if client has project.
    """
    attempt = 0
    wait = initial_wait
    while attempt < max_attempts:
        try:
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                raise GoogleAPICallError(str(errors))
            return None
        except Exception as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            time.sleep(wait)
            wait *= 2
