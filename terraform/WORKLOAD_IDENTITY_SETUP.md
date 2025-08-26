# Workload Identity Federation setup (high level)

1. Create the service account for CI if not already created by terraform:

```bash
gcloud iam service-accounts create ci-cd-deployer --display-name="CI/CD Deployer"
```

2. Create a Workload Identity Pool and Provider (replace PROJECT_ID):

```bash
gcloud iam workload-identity-pools create github-pool --project=PROJECT_ID --location="global" --display-name="GitHub Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project=PROJECT_ID --location="global" \
  --workload-identity-pool=github-pool \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

3. Allow the provider to impersonate the service account:

```bash
gcloud iam service-accounts add-iam-policy-binding ci-cd-deployer@PROJECT_ID.iam.gserviceaccount.com \
  --project=PROJECT_ID \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.actor/*"
```

4. In GitHub, add these repository secrets:
- GCP_PROJECT: your GCP project id
- WORKLOAD_IDENTITY_PROVIDER: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
- SERVICE_ACCOUNT_EMAIL: ci-cd-deployer@PROJECT_ID.iam.gserviceaccount.com
- ARTIFACT_REGISTRY_REPO: repo id (e.g. cfap-repo)
- FIREBASE_TOKEN: (optional) for Firebase Hosting deployments

Replace PROJECT_NUMBER and PROJECT_ID with your project values.
