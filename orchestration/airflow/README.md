Airflow / Composer deployment notes

1) Packaging DAGs for Cloud Composer

- Composer (or managed Airflow) expects DAGs to live in a GCS bucket. You can package your DAGs directory and upload them to the Composer DAGs bucket.

Example steps:

```bash
# create an archive of DAGs
cd orchestration/airflow/dags
zip -r ../dags.zip .

# upload to composer DAGs bucket
gsutil cp ../dags.zip gs://YOUR_COMPOSER_DAGS_BUCKET/
```

2) Dockerized DAG runner (optional)

- If you prefer to run Airflow in Kubernetes (e.g., Cloud Composer 2 or your own), you can build a simple image containing the DAGs and a small entrypoint that copies them into the Airflow worker image at startup.

See `orchestration/airflow/Dockerfile` for an example.
