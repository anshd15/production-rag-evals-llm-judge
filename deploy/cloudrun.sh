#!/usr/bin/env bash
# Deploy the triage service to Cloud Run.
#
# Cloud Run, not a VM, for two reasons: the free tier does not expire (a trial
# credit does, and a dead demo link is worse than no link), and there is no host
# to patch. Scale-to-zero is only viable because the vectors live in Qdrant —
# with the numpy backend every cold start re-embeds 33.8k rows.
#
#   export PROJECT_ID=... QDRANT_URL=... QDRANT_API_KEY=... GEMINI_API_KEY=...
#   ./deploy/cloudrun.sh
#
# Secrets are passed through Secret Manager, never baked into the image.
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID}"
: "${QDRANT_URL:?set QDRANT_URL (Qdrant Cloud free tier is fine)}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-rag-triage}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE}/app:$(date +%Y%m%d-%H%M%S)"

echo "==> creating secrets that do not exist yet"
for name in gemini-api-key qdrant-api-key; do
  gcloud secrets describe "$name" --project "$PROJECT_ID" >/dev/null 2>&1 || \
    gcloud secrets create "$name" --replication-policy=automatic --project "$PROJECT_ID"
done
printf '%s' "${GEMINI_API_KEY:-}"  | gcloud secrets versions add gemini-api-key --data-file=- --project "$PROJECT_ID"
printf '%s' "${QDRANT_API_KEY:-}"  | gcloud secrets versions add qdrant-api-key --data-file=- --project "$PROJECT_ID"

echo "==> building $IMAGE"
gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID"

echo "==> deploying $SERVICE"
# A public demo endpoint is a public LLM endpoint. The rate limit is per
# instance, so max-instances is part of the spend cap, not just a scaling knob.
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --concurrency 8 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "LLM_OFFLINE=0,LLM_PROVIDER=gemini,RETRIEVAL_BACKEND=qdrant,QDRANT_EXACT=1,QDRANT_URL=${QDRANT_URL},RATE_LIMIT_PER_MIN=${RATE_LIMIT_PER_MIN:-12},LLM_MAX_CALLS=${LLM_MAX_CALLS:-5000},GEMINI_RPM=${GEMINI_RPM:-10}" \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,QDRANT_API_KEY=qdrant-api-key:latest"

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)')
echo
echo "deployed: $URL"
echo "demo:     $URL/"
echo "review:   $URL/review"
echo
echo "Set a budget alert before sharing the link:"
echo "  https://console.cloud.google.com/billing/budgets"
