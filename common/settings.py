"""Centralized application settings using Pydantic BaseSettings.

Provides normalized environment variable handling across services.
"""
from functools import lru_cache
from pydantic import BaseSettings, Field
from typing import Optional


class Settings(BaseSettings):
    gcp_project: Optional[str] = Field(None, env=["GCP_PROJECT", "GOOGLE_CLOUD_PROJECT"])  # unify
    pubsub_topic_raw: str = Field("raw-events", env="PUBSUB_TOPIC")
    uploads_bucket: Optional[str] = Field(None, env="UPLOADS_BUCKET")
    ingestion_api_key: Optional[str] = Field(None, env="INGESTION_API_KEY")
    result_dataset: str = Field("cfap_analytics", env="RESULT_DATASET")
    analysis_run_topic: str = Field("run-analysis-jobs", env="ANALYSIS_RUN_TOPIC")
    analysis_run_subscription: str = Field("run-analysis-worker", env="ANALYSIS_RUN_SUBSCRIPTION")

    class Config:
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
