"""Base classes for causal models in the CFAP platform."""
from abc import ABC, abstractmethod
import pandas as pd
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from google.cloud import bigquery
from common.settings import settings, get_bq_table_spec


logger = logging.getLogger(__name__)


class CausalModelBase(ABC):
    """
    Abstract base class for all causal models in the CFAP platform.
    
    This implements the plugin architecture described in the vision:
    - Standardized interface for all models
    - Automatic result persistence
    - Metadata tracking for reproducibility
    - Error handling and logging
    """
    
    def __init__(self, client_id: str, model_params: Dict[str, Any]):
        """
        Initialize the causal model.
        
        Args:
            client_id: Unique identifier for the client
            model_params: Dictionary of model-specific parameters
        """
        self.client_id = client_id
        self.params = model_params or {}
        self.model_name = self.__class__.__name__.lower().replace('model', '')
        
        # Core settings
        self.project = self.params.get("project", settings.gcp_project)
        self.dataset = self.params.get("dataset", settings.bigquery_dataset)
        self.table = self.params.get("table", "standard_events")
        
        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=self.project)
        
        # Generate unique analysis ID for reproducibility
        self.analysis_id = str(uuid.uuid4())
        self.analysis_timestamp = datetime.utcnow().isoformat()
        
        logger.info(f"Initialized {self.model_name} model for client {client_id}, analysis_id: {self.analysis_id}")

    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """
        Load and prepare data for the causal analysis.
        
        This should query the canonical standard_events table and return
        a DataFrame ready for analysis.
        
        Returns:
            DataFrame with the data needed for analysis
        """
        pass

    @abstractmethod
    def run_analysis(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Perform the causal analysis on the prepared data.
        
        Args:
            data: DataFrame from load_data()
            
        Returns:
            DataFrame with analysis results including:
            - effect_size: The estimated causal effect
            - confidence_interval_lower: Lower bound of confidence interval
            - confidence_interval_upper: Upper bound of confidence interval
            - p_value: Statistical significance
            - diagnostics: Model-specific diagnostic information
        """
        pass

    def write_results(self, results: pd.DataFrame):
        """
        Write results to BigQuery with standardized schema.
        
        This method is implemented in the base class to ensure consistency
        across all models, supporting the vision's reproducibility pillar.
        
        Args:
            results: DataFrame with analysis results
        """
        try:
            # Ensure required metadata fields exist
            if "analysis_id" not in results.columns:
                results["analysis_id"] = self.analysis_id
            if "analysis_timestamp" not in results.columns:
                results["analysis_timestamp"] = self.analysis_timestamp
            if "model_name" not in results.columns:
                results["model_name"] = self.model_name
            if "client_id" not in results.columns:
                results["client_id"] = self.client_id
            if "model_version" not in results.columns:
                results["model_version"] = "1.0.0"  # TODO: Get from model registry
            if "model_parameters" not in results.columns:
                results["model_parameters"] = str(self.params)
            
            # Write to BigQuery
            destination_table = f"{self.dataset}.{settings.results_table}"
            
            from pandas_gbq import to_gbq
            to_gbq(
                results, 
                destination_table, 
                project_id=self.project, 
                if_exists="append",
                progress_bar=False
            )
            
            logger.info(f"Successfully wrote {len(results)} results to {destination_table}")
            
        except Exception as e:
            logger.error(f"Failed to write results: {e}")
            raise

    def run(self) -> Dict[str, Any]:
        """
        Execute the complete analysis workflow.
        
        This orchestrates the three main steps:
        1. Load data
        2. Run analysis  
        3. Write results
        
        Returns:
            Dictionary with execution summary
        """
        try:
            logger.info(f"Starting {self.model_name} analysis for client {self.client_id}")
            
            # Step 1: Load data
            data = self.load_data()
            logger.info(f"Loaded {len(data)} rows of data")
            
            # Step 2: Run analysis
            results = self.run_analysis(data)
            logger.info(f"Analysis complete, generated {len(results)} result rows")
            
            # Step 3: Write results
            self.write_results(results)
            
            return {
                "status": "success",
                "analysis_id": self.analysis_id,
                "model_name": self.model_name,
                "client_id": self.client_id,
                "data_rows": len(data),
                "result_rows": len(results),
                "timestamp": self.analysis_timestamp
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "status": "error",
                "analysis_id": self.analysis_id,
                "model_name": self.model_name,
                "client_id": self.client_id,
                "error": str(e),
                "timestamp": self.analysis_timestamp
            }

    def get_data_hash(self, data: pd.DataFrame) -> str:
        """
        Generate hash of input data for reproducibility tracking.
        
        Args:
            data: Input DataFrame
            
        Returns:
            SHA256 hash of the data
        """
        import hashlib
        return hashlib.sha256(pd.util.hash_pandas_object(data).values).hexdigest()


class ModelRegistry:
    """
    Registry for managing causal models.
    
    This supports the vision's modularity pillar by providing
    a central registry for model discovery and versioning.
    """
    
    def __init__(self):
        self.models = {}
        self._register_builtin_models()
    
    def _register_builtin_models(self):
        """Register built-in models."""
        # Import here to avoid circular imports
        try:
            from causal_engine.models.did import DifferenceInDifferencesModel
            self.register("did", DifferenceInDifferencesModel)
        except ImportError:
            logger.warning("DID model not available")
    
    def register(self, name: str, model_class: type):
        """Register a model class."""
        if not issubclass(model_class, CausalModelBase):
            raise ValueError(f"Model {name} must inherit from CausalModelBase")
        
        self.models[name] = model_class
        logger.info(f"Registered model: {name}")
    
    def get_model(self, name: str) -> Optional[type]:
        """Get a model class by name."""
        return self.models.get(name)
    
    def list_models(self) -> list:
        """List all registered models."""
        return list(self.models.keys())


# Global model registry instance
model_registry = ModelRegistry()