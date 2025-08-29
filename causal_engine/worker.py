import os
import json
import time
import logging
from datetime import datetime, timezone
from google.cloud import pubsub_v1, bigquery
from causal_engine.models.did import DifferenceInDifferencesModel
from causal_engine.utils.bq import insert_rows_json_with_retries
import uuid
import traceback

logger = logging.getLogger("causal_engine_worker")
logger.setLevel(logging.INFO)


def write_job_status(bq_client: bigquery.Client, dataset: str, table: str, row: dict):
    table_id = f"{bq_client.project}.{dataset}.job_status" if bq_client.project else f"{dataset}.job_status"
    rows_to_insert = [row]
    insert_rows_json_with_retries(bq_client, table_id, rows_to_insert)


def process_message(message: pubsub_v1.subscriber.message.Message, bq_client: bigquery.Client, dataset: str):
    try:
        payload = json.loads(message.data.decode("utf-8"))
        job_id = payload.get("job_id") or str(uuid.uuid4())
        model = payload.get("model")
        params = payload.get("params", {})

        started_dt = datetime.now(timezone.utc)
        write_job_status(
            bq_client,
            dataset,
            "job_status",
            {
                "job_id": job_id,
                "model_name": model,
                "params": json.dumps(params),
                "status": "RUNNING",
                "started_at": started_dt.isoformat(),
            },
        )

        # instantiate model
        if model == "did":
            m = DifferenceInDifferencesModel(client_id=params.get("client_id", "default"), model_params={"project": os.environ.get("GCP_PROJECT"), "campaign_id": params.get("campaign_id"), "dataset": params.get("dataset", "cfap_analytics"), "table": params.get("table", "standard_events"), **params})
        else:
            raise RuntimeError(f"Unknown model: {model}")

        # run model
        m.run()

        # Write model registry metadata (lightweight) to bigquery table causal_model_registry if exists
        try:
            registry_table = f"{bq_client.project}.{dataset}.causal_model_registry"
            registry_row = {
                "registry_id": str(uuid.uuid4()),
                "job_id": job_id,
                "model_name": model,
                "campaign_id": params.get("campaign_id"),
                "params_hash": str(hash(json.dumps(params, sort_keys=True))) if params else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            insert_rows_json_with_retries(bq_client, registry_table, [registry_row])
        except Exception:
            logger.warning("Model registry write failed", exc_info=True)

        finished_dt = datetime.now(timezone.utc)
        write_job_status(
            bq_client,
            dataset,
            "job_status",
            {
                "job_id": job_id,
                "model_name": model,
                "params": json.dumps(params),
                "status": "SUCCEEDED",
                "started_at": started_dt.isoformat(),
                "finished_at": finished_dt.isoformat(),
            },
        )
        message.ack()
    except Exception as e:
        logger.exception("Processing message failed: %s", e)
        try:
            now_dt = datetime.now(timezone.utc)
            write_job_status(
                bq_client,
                dataset,
                "job_status",
                {
                    "job_id": payload.get("job_id") if 'payload' in locals() else str(uuid.uuid4()),
                    "model_name": payload.get("model") if 'payload' in locals() else None,
                    "params": json.dumps(payload.get("params")) if 'payload' in locals() else None,
                    "status": "FAILED",
                    "error": str(e),
                    "started_at": now_dt.isoformat(),
                    "finished_at": now_dt.isoformat(),
                },
            )
        except Exception:
            logger.exception("Failed writing failure status")
        message.nack()


def run_worker():
    project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    subscription_name = os.environ.get("ANALYSIS_RUN_SUBSCRIPTION", "run-analysis-worker")
    dataset = os.environ.get("RESULT_DATASET", "cfap_analytics")

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project, subscription_name)
    bq_client = bigquery.Client()

    logger.info("Starting causal engine worker, subscription=%s", subscription_path)

    def callback(message):
        process_message(message, bq_client, dataset)

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()


if __name__ == "__main__":
    run_worker()
