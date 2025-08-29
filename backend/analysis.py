"""Analysis helpers.

Currently provides a simple Difference-in-Differences (DiD) analysis that
expects prepared data in BigQuery. For local development (when BigQuery is
unavailable or credentials are missing) we fall back to reading from an
optional CSV specified via DID_LOCAL_CSV or return a stub so the frontend
can still exercise the flow.
"""
try:
    from google.cloud import bigquery  # type: ignore
except Exception:  # pragma: no cover - optional for local dev
    bigquery = None
import pandas as pd
import statsmodels.api as sm


def run_did_analysis(project_id: str, campaign_id: str) -> dict:
    # Attempt BigQuery path first
    df = pd.DataFrame()
    if bigquery is not None:
        try:  # pragma: no cover - network/external
            client = bigquery.Client(project=project_id)
            query = (
                "SELECT conversions, is_treatment, is_post "
                "FROM `cfap-platform-dev.cfap_analytics.prepared_did_data` "
                "WHERE campaign_id = @campaign_id"
            )
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("campaign_id", "STRING", campaign_id)]
            )
            query_job = client.query(query, job_config=job_config)
            df = query_job.to_dataframe()
        except Exception:
            # fall back to local CSV if provided
            pass

    if df.empty:
        local_csv = os.environ.get("DID_LOCAL_CSV")
        if local_csv and os.path.exists(local_csv):
            try:
                df = pd.read_csv(local_csv)
            except Exception:
                df = pd.DataFrame()

    if df.empty or not set(["conversions", "is_treatment", "is_post"]).issubset(df.columns):
        return {"campaign_id": campaign_id, "lift": None, "error": "no data"}

    df["interaction"] = df["is_treatment"] * df["is_post"]
    X = sm.add_constant(df[["is_treatment", "is_post", "interaction"]])
    y = df["conversions"]
    model = sm.OLS(y, X).fit()
    lift_estimate = model.params.get("interaction")
    return {"campaign_id": campaign_id, "lift": float(lift_estimate)}
