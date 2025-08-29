"""Pub/Sub worker for causal engine."""
import json
import logging
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from google.cloud import pubsub_v1
from google.cloud import bigquery

from causal_engine.base import model_registry
from common.settings import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CausalEngineWorker:
    """
    Pub/Sub worker for processing causal analysis jobs.
    
    This implements the event-driven architecture described in the vision,
    allowing the causal engine to be triggered asynchronously.
    """
    
    def __init__(self):
        self.project_id = settings.gcp_project
        self.subscription_path = f"projects/{self.project_id}/subscriptions/{settings.analysis_subscription}"
        
        # Initialize Pub/Sub subscriber
        self.subscriber = pubsub_v1.SubscriberClient()
        
        # Initialize BigQuery for job status tracking
        self.bq_client = bigquery.Client(project=self.project_id)
        
        # Executor for handling messages
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Shutdown flag
        self.shutdown = False
        
        logger.info(f"Worker initialized for subscription: {self.subscription_path}")

    def process_message(self, message):
        """
        Process a single analysis job message.
        
        Args:
            message: Pub/Sub message with job parameters
        """
        try:
            # Parse message
            data = json.loads(message.data.decode('utf-8'))
            job_id = data.get('job_id')
            client_id = data.get('client_id')
            model_name = data.get('model_name')
            params = data.get('params', {})
            
            logger.info(f"Processing job {job_id}: {model_name} for client {client_id}")
            
            # Update job status to running
            self._update_job_status(job_id, "running", {"started_at": "CURRENT_TIMESTAMP()"})
            
            # Get model class
            model_class = model_registry.get_model(model_name)
            if not model_class:
                error_msg = f"Unknown model: {model_name}"
                logger.error(error_msg)
                self._update_job_status(job_id, "failed", {"error": error_msg})
                message.ack()
                return
            
            # Run analysis
            model = model_class(client_id, params)
            result = model.run()
            
            # Update job status based on result
            if result["status"] == "success":
                self._update_job_status(job_id, "completed", {
                    "completed_at": "CURRENT_TIMESTAMP()",
                    "analysis_id": result["analysis_id"],
                    "result_rows": result["result_rows"]
                })
                logger.info(f"Job {job_id} completed successfully")
            else:
                self._update_job_status(job_id, "failed", {
                    "error": result.get("error", "Unknown error"),
                    "failed_at": "CURRENT_TIMESTAMP()"
                })
                logger.error(f"Job {job_id} failed: {result.get('error')}")
            
            # Acknowledge message
            message.ack()
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            message.ack()  # Ack to avoid reprocessing
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Don't ack - let it retry
            message.nack()

    def _update_job_status(self, job_id: str, status: str, additional_fields: Dict[str, Any] = None):
        """Update job status in BigQuery."""
        try:
            fields = {"status": status}
            if additional_fields:
                fields.update(additional_fields)
            
            # Build SET clause
            set_clauses = []
            for key, value in fields.items():
                if value == "CURRENT_TIMESTAMP()":
                    set_clauses.append(f"{key} = CURRENT_TIMESTAMP()")
                else:
                    set_clauses.append(f"{key} = '{value}'")
            
            query = f"""
            UPDATE `{self.project_id}.{settings.bigquery_dataset}.{settings.job_status_table}`
            SET {', '.join(set_clauses)}
            WHERE job_id = '{job_id}'
            """
            
            self.bq_client.query(query).result()
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")

    def start(self):
        """Start the worker to listen for messages."""
        logger.info("Starting causal engine worker...")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Configure flow control
        flow_control = pubsub_v1.types.FlowControl(max_messages=10)
        
        try:
            # Start pulling messages
            streaming_pull_future = self.subscriber.subscribe(
                self.subscription_path,
                callback=self.process_message,
                flow_control=flow_control
            )
            
            logger.info(f"Listening for messages on {self.subscription_path}")
            
            # Keep the main thread alive
            try:
                streaming_pull_future.result()
            except KeyboardInterrupt:
                streaming_pull_future.cancel()
                
        except Exception as e:
            logger.error(f"Error in worker: {e}")
            sys.exit(1)
        finally:
            self.shutdown = True
            self.executor.shutdown(wait=True)
            logger.info("Worker shutdown complete")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown = True


def main():
    """Main entry point for the worker."""
    worker = CausalEngineWorker()
    worker.start()


if __name__ == "__main__":
    main()