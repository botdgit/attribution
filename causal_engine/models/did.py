"""Difference-in-Differences causal model implementation."""
import pandas as pd
import numpy as np
import uuid
import logging
from typing import Dict, Any, Optional
from google.cloud import bigquery
import statsmodels.api as sm

from causal_engine.base import CausalModelBase
from common.settings import get_bq_table_spec


logger = logging.getLogger(__name__)


class DifferenceInDifferencesModel(CausalModelBase):
    """
    Difference-in-Differences (DiD) causal model.
    
    This model estimates causal effects by comparing treatment and control groups
    before and after an intervention. It's particularly useful for:
    - Marketing campaign lift analysis
    - A/B test validation
    - Natural experiment analysis
    """
    
    def __init__(self, client_id: str, model_params: Dict[str, Any]):
        """Initialize DID model with specific parameters."""
        super().__init__(client_id, model_params)
        
        # DID-specific parameters
        self.campaign_id = model_params.get("campaign_id")
        self.split_date = model_params.get("split_date")
        self.treatment_channel = model_params.get("treatment_channel", "paid_search")
        self.outcome_metric = model_params.get("outcome_metric", "conversion")
        
        if not self.campaign_id:
            raise ValueError("campaign_id is required for DID analysis")
        
        logger.info(f"DID model initialized for campaign {self.campaign_id}")

    def load_data(self) -> pd.DataFrame:
        """
        Load data from the canonical standard_events table.
        
        Returns:
            DataFrame with events filtered by campaign_id and required fields
        """
        try:
            table_spec = get_bq_table_spec(self.project, self.dataset, self.table)
            
            query = f"""
            SELECT 
                event_id,
                timestamp,
                event_type,
                revenue_usd,
                marketing_channel,
                campaign_id,
                user_anonymous_id
            FROM `{table_spec}` 
            WHERE campaign_id = @campaign_id
            ORDER BY timestamp
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("campaign_id", "STRING", self.campaign_id)
                ]
            )
            
            query_job = self.bq_client.query(query, job_config=job_config)
            df = query_job.to_dataframe()
            
            logger.info(f"Loaded {len(df)} events for campaign {self.campaign_id}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise

    def _prepare_did_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for DID analysis by creating treatment and post flags.
        
        Args:
            data: Raw event data
            
        Returns:
            DataFrame with is_treatment and is_post flags
        """
        if data.empty:
            return data
        
        # Create treatment flag based on marketing channel
        data["is_treatment"] = (
            data["marketing_channel"].notna() & 
            (data["marketing_channel"] == self.treatment_channel)
        )
        
        # Create post-treatment flag
        if self.split_date:
            split_datetime = pd.to_datetime(self.split_date)
            data["is_post"] = pd.to_datetime(data["timestamp"]) >= split_datetime
        else:
            # Default: use median timestamp as split
            median_time = pd.to_datetime(data["timestamp"]).median()
            data["is_post"] = pd.to_datetime(data["timestamp"]) >= median_time
            logger.info(f"Using median timestamp as split: {median_time}")
        
        # Create outcome variable
        if self.outcome_metric == "conversion":
            data["outcome"] = (data["event_type"] == "conversion").astype(int)
        elif self.outcome_metric == "revenue":
            data["outcome"] = data["revenue_usd"].fillna(0)
        else:
            data["outcome"] = 1  # Default: count all events
        
        return data

    def run_analysis(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Perform the Difference-in-Differences analysis.
        
        Args:
            data: Prepared data with treatment and control groups
            
        Returns:
            DataFrame with DID results
        """
        try:
            if data.empty:
                return pd.DataFrame([{
                    "campaign_id": self.campaign_id,
                    "effect_size": None,
                    "confidence_interval_lower": None,
                    "confidence_interval_upper": None,
                    "p_value": None,
                    "standard_error": None,
                    "error": "no data"
                }])
            
            # Prepare DID data
            did_data = self._prepare_did_data(data)
            
            if did_data.empty:
                return pd.DataFrame([{
                    "campaign_id": self.campaign_id,
                    "effect_size": None,
                    "error": "no data after preparation"
                }])
            
            # Aggregate data for DID regression
            agg_data = did_data.groupby(["is_treatment", "is_post"]).agg({
                "outcome": ["sum", "count"],
                "user_anonymous_id": "nunique"
            }).reset_index()
            
            # Flatten column names
            agg_data.columns = ["is_treatment", "is_post", "outcome_sum", "event_count", "unique_users"]
            
            # If we have fewer than 4 cells (2x2), can't run DID
            if len(agg_data) < 4:
                return pd.DataFrame([{
                    "campaign_id": self.campaign_id,
                    "effect_size": None,
                    "error": "insufficient data for DID (need treatment/control x pre/post)"
                }])
            
            # Create regression variables
            agg_data["interaction"] = agg_data["is_treatment"] * agg_data["is_post"]
            
            # Run OLS regression
            # Outcome rate = α + β₁(Treatment) + β₂(Post) + β₃(Treatment × Post) + ε
            y = agg_data["outcome_sum"] / agg_data["event_count"]  # Outcome rate
            X = sm.add_constant(agg_data[["is_treatment", "is_post", "interaction"]])
            
            model = sm.OLS(y, X).fit()
            
            # Extract DID estimate (interaction coefficient)
            did_estimate = model.params.get("interaction", 0)
            did_stderr = model.bse.get("interaction", 0)
            did_pvalue = model.pvalues.get("interaction", 1)
            
            # Calculate confidence interval
            conf_int = model.conf_int().loc["interaction"] if "interaction" in model.conf_int().index else [0, 0]
            
            # Prepare results
            result = {
                "campaign_id": self.campaign_id,
                "effect_size": float(did_estimate),
                "standard_error": float(did_stderr),
                "p_value": float(did_pvalue),
                "confidence_interval_lower": float(conf_int[0]),
                "confidence_interval_upper": float(conf_int[1]),
                "r_squared": float(model.rsquared),
                "n_observations": int(len(agg_data)),
                "treatment_pre_mean": float(agg_data[
                    (agg_data["is_treatment"] == 1) & (agg_data["is_post"] == 0)
                ]["outcome_sum"].sum() / agg_data[
                    (agg_data["is_treatment"] == 1) & (agg_data["is_post"] == 0)
                ]["event_count"].sum()) if len(agg_data[
                    (agg_data["is_treatment"] == 1) & (agg_data["is_post"] == 0)
                ]) > 0 else 0,
                "control_pre_mean": float(agg_data[
                    (agg_data["is_treatment"] == 0) & (agg_data["is_post"] == 0)
                ]["outcome_sum"].sum() / agg_data[
                    (agg_data["is_treatment"] == 0) & (agg_data["is_post"] == 0)
                ]["event_count"].sum()) if len(agg_data[
                    (agg_data["is_treatment"] == 0) & (agg_data["is_post"] == 0)
                ]) > 0 else 0,
                "diagnostics": {
                    "model_summary": str(model.summary()),
                    "data_hash": self.get_data_hash(did_data)
                }
            }
            
            logger.info(f"DID analysis complete. Effect size: {did_estimate:.4f}, p-value: {did_pvalue:.4f}")
            
            return pd.DataFrame([result])
            
        except Exception as e:
            logger.error(f"DID analysis failed: {e}")
            return pd.DataFrame([{
                "campaign_id": self.campaign_id,
                "effect_size": None,
                "error": str(e)
            }])

    def write_results(self, results: pd.DataFrame):
        """Write DID results to BigQuery with proper schema."""
        try:
            # Ensure required fields exist
            if "analysis_id" not in results.columns:
                results["analysis_id"] = self.analysis_id
            if "analysis_timestamp" not in results.columns:
                results["analysis_timestamp"] = self.analysis_timestamp
            
            # Convert diagnostics dict to JSON string for BigQuery
            if "diagnostics" in results.columns:
                import json
                results["diagnostics"] = results["diagnostics"].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else str(x)
                )
            
            # Call parent method to handle the actual writing
            super().write_results(results)
            
        except Exception as e:
            logger.error(f"Failed to write DID results: {e}")
            raise