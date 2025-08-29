"""Control Plane API for CFAP - Analysis orchestration and job management."""
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google.cloud import pubsub_v1, bigquery

from common.auth import verify_firebase_token
from common.settings import settings
from causal_engine.base import model_registry


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CFAP Control Plane API",
    description="Orchestration and job management for causal analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize GCP clients
publisher = pubsub_v1.PublisherClient()
bq_client = bigquery.Client(project=settings.gcp_project)
topic_path = publisher.topic_path(settings.gcp_project, settings.analysis_topic)


# Pydantic models
class AnalysisRequest(BaseModel):
    """Request model for analysis job."""
    model_name: str = Field(..., description="Name of the causal model to run")
    params: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    priority: int = Field(default=5, ge=1, le=10, description="Job priority (1=highest)")
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "did",
                "params": {
                    "campaign_id": "campaign_123",
                    "split_date": "2024-01-15",
                    "treatment_channel": "paid_search"
                },
                "priority": 5
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for analysis job."""
    job_id: str
    status: str
    message: str
    analysis_id: Optional[str] = None


class JobStatus(BaseModel):
    """Job status model."""
    job_id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error: Optional[str] = None
    analysis_id: Optional[str] = None
    result_rows: Optional[int] = None


# Auth dependency
async def get_current_user(token: str = Depends(verify_firebase_token)):
    """Verify Firebase token and get current user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "CFAP Control Plane API",
        "version": "1.0.0",
        "status": "healthy",
        "available_models": model_registry.list_models()
    }


@app.get("/v1/models")
async def list_models():
    """List available causal models."""
    return {
        "models": model_registry.list_models(),
        "count": len(model_registry.list_models())
    }


@app.post("/v1/analysis/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    user: dict = Depends(get_current_user)
):
    """
    Submit a new causal analysis job.
    
    This endpoint publishes a job to the Pub/Sub topic for processing
    by the causal engine workers.
    """
    try:
        # Validate model exists
        if request.model_name not in model_registry.list_models():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown model: {request.model_name}. Available: {model_registry.list_models()}"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job record in BigQuery
        job_data = {
            "job_id": job_id,
            "client_id": user["uid"],
            "model_name": request.model_name,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "priority": request.priority,
            "parameters": json.dumps(request.params)
        }
        
        # Insert job status
        table_id = f"{settings.gcp_project}.{settings.bigquery_dataset}.{settings.job_status_table}"
        errors = bq_client.insert_rows_json(table_id, [job_data])
        
        if errors:
            logger.error(f"Failed to insert job record: {errors}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create job record"
            )
        
        # Publish message to Pub/Sub
        message_data = {
            "job_id": job_id,
            "client_id": user["uid"],
            "model_name": request.model_name,
            "params": request.params,
            "priority": request.priority
        }
        
        message = json.dumps(message_data).encode('utf-8')
        future = publisher.publish(topic_path, message)
        
        # Wait for publish to complete
        message_id = future.result()
        
        logger.info(f"Published job {job_id} to {topic_path}, message_id: {message_id}")
        
        return AnalysisResponse(
            job_id=job_id,
            status="queued",
            message=f"Analysis job submitted successfully. Job ID: {job_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit analysis job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}"
        )


@app.get("/v1/analysis/{job_id}/status", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """Get the status of a specific analysis job."""
    try:
        query = f"""
        SELECT 
            job_id,
            status,
            created_at,
            started_at,
            completed_at,
            failed_at,
            error,
            analysis_id,
            result_rows
        FROM `{settings.gcp_project}.{settings.bigquery_dataset}.{settings.job_status_table}`
        WHERE job_id = @job_id AND client_id = @client_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("job_id", "STRING", job_id),
                bigquery.ScalarQueryParameter("client_id", "STRING", user["uid"])
            ]
        )
        
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        row = results[0]
        return JobStatus(
            job_id=row.job_id,
            status=row.status,
            created_at=row.created_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
            failed_at=row.failed_at,
            error=row.error,
            analysis_id=row.analysis_id,
            result_rows=row.result_rows
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@app.get("/v1/analysis/jobs")
async def list_jobs(
    status_filter: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List analysis jobs for the current user."""
    try:
        where_clause = "WHERE client_id = @client_id"
        params = [bigquery.ScalarQueryParameter("client_id", "STRING", user["uid"])]
        
        if status_filter:
            where_clause += " AND status = @status"
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status_filter))
        
        query = f"""
        SELECT 
            job_id,
            model_name,
            status,
            created_at,
            started_at,
            completed_at,
            failed_at,
            error,
            analysis_id
        FROM `{settings.gcp_project}.{settings.bigquery_dataset}.{settings.job_status_table}`
        {where_clause}
        ORDER BY created_at DESC
        LIMIT @limit
        """
        
        params.append(bigquery.ScalarQueryParameter("limit", "INT64", limit))
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        query_job = bq_client.query(query, job_config=job_config)
        
        results = []
        for row in query_job:
            results.append({
                "job_id": row.job_id,
                "model_name": row.model_name,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "failed_at": row.failed_at.isoformat() if row.failed_at else None,
                "error": row.error,
                "analysis_id": row.analysis_id
            })
        
        return {
            "jobs": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8082,
        reload=True
    )