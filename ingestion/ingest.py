from google.cloud import storage, secretmanager
from datetime import datetime


def access_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")


def ingest_data_to_gcs(project_id: str, bucket_name: str, data: str):
    """Uploads data (JSON string) to a GCS bucket with a timestamped filename."""
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"ga4-sessions-{datetime.utcnow().isoformat()}.json")
    blob.upload_from_string(data, content_type="application/json")
    print(f"File uploaded to {blob.name}.")
