#!/usr/bin/env bash
set -euo pipefail

# Smoke test: signs in to Firebase using email/password via REST API,
# optionally uploads a sample file to /api/ingest, then calls /api/analysis/did.
# Requires env vars: FIREBASE_API_KEY, TEST_EMAIL, TEST_PASSWORD, BACKEND_URL

if [ -z "${FIREBASE_API_KEY:-}" ] || [ -z "${TEST_EMAIL:-}" ] || [ -z "${TEST_PASSWORD:-}" ] || [ -z "${BACKEND_URL:-}" ]; then
  echo "Usage: FIREBASE_API_KEY=... TEST_EMAIL=... TEST_PASSWORD=... BACKEND_URL=... $0 [sample_file]"
  exit 2
fi

API_KEY="$FIREBASE_API_KEY"
EMAIL="$TEST_EMAIL"
PASS="$TEST_PASSWORD"
BACKEND_URL="$BACKEND_URL"

echo "Signing in to Firebase (REST)..."
TOKEN_RESPONSE=$(curl -s -X POST "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\",\"returnSecureToken\":true}")

ID_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r .idToken)
if [ "$ID_TOKEN" = "null" ] || [ -z "$ID_TOKEN" ]; then
  echo "Failed to sign in: $TOKEN_RESPONSE"
  exit 1
fi

echo "Signed in, obtained idToken (truncated): ${ID_TOKEN:0:20}..."

SAMPLE_FILE=${1:-}
if [ -n "$SAMPLE_FILE" ] && [ -f "$SAMPLE_FILE" ]; then
  echo "Uploading sample file to ${BACKEND_URL}/api/ingest"
  curl -s -X POST "${BACKEND_URL}/api/ingest" -H "Authorization: Bearer ${ID_TOKEN}" -F file=@"${SAMPLE_FILE}" -o /dev/stdout -w "\nHTTP STATUS: %{http_code}\n"
else
  echo "No sample file provided or not found; skipping ingest upload"
fi

echo "Calling /api/analysis/did"
curl -s -X POST "${BACKEND_URL}/api/analysis/did" \
  -H "Authorization: Bearer ${ID_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id":"smoke-test-campaign"}' -o /dev/stdout -w "\nHTTP STATUS: %{http_code}\n"

echo "Smoke test complete"
