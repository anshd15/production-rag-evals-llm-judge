#!/usr/bin/env bash
# Deploy the triage service to Cloud Run.
#
# Cloud Run, not a VM, for two reasons: the free tier does not expire (a trial
# credit does, and a dead demo link is worse than no link), and there is no host
# to patch.
#
#   export PROJECT_ID=...
#   ./deploy/cloudrun.sh
#
# Credentials: with LLM_PROVIDER=vertex the runtime service account IS the
# credential. Application Default Credentials resolve to it automatically inside
# Cloud Run, so there is no API key, no Secret Manager entry and no secret to
# rotate or leak. That is the main reason this path is preferred over AI Studio.
#
# Retrieval: numpy by default. The serving index (history_index_*.npy) ships in
# the image via .gcloudignore, so a cold start loads it in ~1s rather than
# re-embedding 33.8k rows. Set QDRANT_URL to use Qdrant instead, which is worth
# doing once the index needs incremental updates rather than a rebuild.
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-rag-triage}"
REPO="${REPO:-rag-triage}"
# Least privilege at runtime: aiplatform.user and nothing else it does not need.
RUNTIME_SA="${RUNTIME_SA:-rag-evals-agent@${PROJECT_ID}.iam.gserviceaccount.com}"
# "global", not a region: the Gemini 3.x publisher models 404 on us-central1.
GCP_LOCATION="${GCP_LOCATION:-global}"
AGENT_MODEL="${VERTEX_AGENT_MODEL:-gemini-3.5-flash-lite}"
# Public identifier, not a secret: it is served in the page, and the token it
# produces is verified server-side before it means anything. Unset simply means
# the sign-in button never appears and everyone gets the anonymous allowance.
GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/app:$(date +%Y%m%d-%H%M%S)"

echo "==> ensuring the Artifact Registry repository exists"
gcloud artifacts repositories describe "$REPO" \
  --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "$REPO" \
    --repository-format=docker --location "$REGION" --project "$PROJECT_ID" \
    --description="Triage service images"

RETRIEVAL_ENV="RETRIEVAL_BACKEND=numpy"
SECRET_ARGS=()
if [[ -n "${QDRANT_URL:-}" ]]; then
  echo "==> QDRANT_URL set, deploying against Qdrant"
  gcloud secrets describe qdrant-api-key --project "$PROJECT_ID" >/dev/null 2>&1 || \
    gcloud secrets create qdrant-api-key --replication-policy=automatic --project "$PROJECT_ID"
  printf '%s' "${QDRANT_API_KEY:-}" | \
    gcloud secrets versions add qdrant-api-key --data-file=- --project "$PROJECT_ID"
  RETRIEVAL_ENV="RETRIEVAL_BACKEND=qdrant,QDRANT_EXACT=1,QDRANT_URL=${QDRANT_URL}"
  SECRET_ARGS=(--set-secrets "QDRANT_API_KEY=qdrant-api-key:latest")
fi

echo "==> building $IMAGE"
gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID"

echo "==> deploying $SERVICE"
# A public demo endpoint is a public LLM endpoint someone else is paying for.
# The rate limit is PER INSTANCE, so max-instances is part of the spend cap and
# not just a scaling knob: the real ceiling is max-instances x RATE_LIMIT_PER_MIN.
# LLM_MAX_CALLS is the hard per-instance stop underneath both.
# max-instances is 1, not 3: the rate limiter and LLM_MAX_CALLS are per process,
# so three instances meant three independent budgets and three times the real
# ceiling. One instance makes both numbers mean what they say.
#
# Nothing in the command below may carry a comment. A `#` line inside a
# backslash-continued command ENDS the continuation: bash ran `gcloud run deploy`
# without every flag after it -- including --set-env-vars -- and then tried to run
# `--max-instances` as a command. The deploy still reported success, because Cloud
# Run keeps the previous revision's environment when none is supplied, so the
# service came up healthy with stale config and no sign-in configured.
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --service-account "$RUNTIME_SA" \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --cpu-boost \
  --concurrency 8 \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars "LLM_OFFLINE=0,LLM_PROVIDER=vertex,GCP_PROJECT=${PROJECT_ID},GCP_LOCATION=${GCP_LOCATION},VERTEX_AGENT_MODEL=${AGENT_MODEL},${RETRIEVAL_ENV},RATE_LIMIT_PER_MIN=${RATE_LIMIT_PER_MIN:-12},LLM_MAX_CALLS=${LLM_MAX_CALLS:-2000},GEMINI_RPM=${GEMINI_RPM:-10},GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID},ANON_FREE_MESSAGES=${ANON_FREE_MESSAGES:-3},USER_DAILY_MESSAGES=${USER_DAILY_MESSAGES:-30}" \
  "${SECRET_ARGS[@]}"

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)')
echo
echo "deployed: $URL"
echo "demo:     $URL/"
echo "review:   $URL/review"
echo
echo "Before sharing the link, confirm the budget alert exists:"
echo "  gcloud billing budgets list --billing-account=\$(gcloud billing projects describe $PROJECT_ID --format='value(billingAccountName)' | cut -d/ -f2)"
