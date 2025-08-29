from causal_engine.base import CausalModelBase
import pandas as pd
from google.cloud import bigquery
import statsmodels.api as sm
from causal_engine.utils.bq import get_bq_table_spec
import uuid


class DifferenceInDifferencesModel(CausalModelBase):
    def __init__(self, client_id: str, model_params: dict):
        super().__init__(client_id, model_params)
        self.project = model_params.get("project")
        self.dataset = model_params.get("dataset", "cfap_analytics")
        self.table = model_params.get("table", "standard_events")
        self.campaign_id = model_params.get("campaign_id")
        self.bq_client = bigquery.Client(project=self.project) if self.project else bigquery.Client()

    def load_data(self) -> pd.DataFrame:
        # Query the canonical standard_events table filtered by campaign_id and required fields
        table_spec = get_bq_table_spec(self.project, self.dataset, self.table)
        query = f"SELECT event_id, timestamp, event_type, revenue_usd, marketing_channel, campaign_id, user_anonymous_id FROM `{table_spec}` WHERE campaign_id = @campaign_id"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("campaign_id", "STRING", self.campaign_id)]
        )
        query_job = self.bq_client.query(query, job_config=job_config)
        df = query_job.to_dataframe()
        return df

    def run_analysis(self, data: pd.DataFrame) -> pd.DataFrame:
        # Expecting prepared data with is_treatment and is_post flags; if not present, attempt a naive construction
        if data.empty:
            return pd.DataFrame([{"campaign_id": self.campaign_id, "lift_estimate": None, "error": "no data"}])

        # For simplicity, expect event_type == 'conversion' to be counted as conversions
        # Build an aggregated table by (is_treatment, is_post)
        # NOTE: This is a simplification; production should use prepared rollups.
        data["is_treatment"] = data.get("marketing_channel", "").notnull()
        # Create a naive is_post flag based on timestamp relative to a supplied split_date param
        split_date = self.params.get("split_date")
        if split_date:
            data["is_post"] = pd.to_datetime(data["timestamp"]) >= pd.to_datetime(split_date)
        else:
            # default: last 50% of time as post period
            ts_sorted = pd.to_datetime(data["timestamp"]).sort_values()
            median_ts = ts_sorted.iloc[len(ts_sorted) // 2]
            data["is_post"] = pd.to_datetime(data["timestamp"]) >= median_ts

        data["conversions"] = data["event_type"].apply(lambda x: 1 if x == "purchase" or x == "conversion" else 0)
        df = data[["conversions", "is_treatment", "is_post"]].copy()
        df["interaction"] = df["is_treatment"] * df["is_post"]
        X = sm.add_constant(df[["is_treatment", "is_post", "interaction"]])
        y = df["conversions"]
        model = sm.OLS(y, X).fit()
        lift = model.params.get("interaction") if "interaction" in model.params else None

        # Confidence interval for the interaction term (95%)
        ci_low = None
        ci_high = None
        try:
            ci = model.conf_int(alpha=0.05)
            if "interaction" in ci.index:
                ci_low = float(ci.loc["interaction"][0])
                ci_high = float(ci.loc["interaction"][1])
        except Exception:
            # leave CI as None if computation fails
            pass

        out = {
            "analysis_id": str(uuid.uuid4()),
            "campaign_id": self.campaign_id,
            "lift_estimate": float(lift) if lift is not None else None,
            "confidence_interval_low": ci_low,
            "confidence_interval_high": ci_high,
            "model_name": "did",
            "analysis_timestamp": pd.Timestamp.utcnow().isoformat(),
        }
        return pd.DataFrame([out])

    def write_results(self, results: pd.DataFrame):
        # Append to BigQuery lift_analysis_results table
        from pandas_gbq import to_gbq

        # destination_table expected by pandas_gbq is dataset.table; pass project_id separately
        destination_table = f"{self.dataset}.lift_analysis_results"

        # Ensure required fields exist
        if "analysis_id" not in results.columns:
            results["analysis_id"] = results.apply(lambda _: str(uuid.uuid4()), axis=1)
        if "analysis_timestamp" not in results.columns:
            results["analysis_timestamp"] = pd.Timestamp.utcnow().isoformat()

        to_gbq(results, destination_table, project_id=self.project, if_exists="append")
