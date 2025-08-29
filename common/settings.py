"""Centralized settings and configuration."""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings."""
    
    # GCP Settings
    gcp_project: str = os.getenv("GCP_PROJECT", "cfap-platform-dev")
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "cfap_analytics")
    
    # Pub/Sub Settings
    analysis_topic: str = os.getenv("ANALYSIS_TOPIC", "run-analysis-jobs")
    analysis_subscription: str = os.getenv("ANALYSIS_SUBSCRIPTION", "run-analysis-worker")
    
    # Firebase Settings
    firebase_project: str = os.getenv("FIREBASE_PROJECT", "cfap-platform-dev")
    
    # Database Settings
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "cfap")
    db_user: str = os.getenv("DB_USER", "cfap")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    # Model Registry Settings
    model_registry_table: str = "causal_model_registry"
    results_table: str = "lift_analysis_results"
    job_status_table: str = "job_status"
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def database_url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# Global settings instance
settings = Settings()


def get_bq_table_spec(project: str, dataset: str, table: str) -> str:
    """Get fully qualified BigQuery table specification."""
    return f"{project}.{dataset}.{table}"