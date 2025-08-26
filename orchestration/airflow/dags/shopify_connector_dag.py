from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os

from connectors.shopify import ShopifyConnector


def run_shopify_connector(**kwargs):
    conn = ShopifyConnector(api_key=os.getenv("SHOPIFY_API_KEY", "FAKE"), shop=os.getenv("SHOPIFY_SHOP", "example.myshopify.com"))
    rows = list(conn.run())
    # Placeholder: publish rows to Pub/Sub or write to GCS
    print(f"Connector produced {len(rows)} rows")


default_args = {
    'owner': 'cfap',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG('shopify_connector', default_args=default_args, schedule_interval='@daily', catchup=False) as dag:
    run_connector = PythonOperator(
        task_id='run_shopify_connector',
        python_callable=run_shopify_connector,
    )
