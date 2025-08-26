from google.cloud import bigquery
import pandas as pd
import statsmodels.api as sm


def run_did_analysis(project_id: str, campaign_id: str) -> dict:
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

    if df.empty:
        return {"campaign_id": campaign_id, "lift": None, "error": "no data"}

    df["interaction"] = df["is_treatment"] * df["is_post"]
    X = sm.add_constant(df[["is_treatment", "is_post", "interaction"]])
    y = df["conversions"]
    model = sm.OLS(y, X).fit()
    lift_estimate = model.params.get("interaction")
    return {"campaign_id": campaign_id, "lift": float(lift_estimate)}
