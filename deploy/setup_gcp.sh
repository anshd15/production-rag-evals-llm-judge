#!/usr/bin/env bash
# One-shot GCP setup for running the evaluation on Vertex AI.
#
# Run this in YOUR terminal (not Claude's) — two of these steps open a browser
# and need you to click "Allow", which is why they cannot be automated.
#
#   bash deploy/setup_gcp.sh
#
# What it does and why: Vertex AI authenticates with Application Default
# Credentials instead of an API key, so no secret is ever written to a file or
# pasted into a chat. It also bills the project, which lifts the AI Studio free
# tier's 500-requests-per-day-per-model cap that stalled the first run.
set -e

ACCOUNT="${ACCOUNT:-anshdoshi.d17@gmail.com}"

echo
echo "=== 1/5  Sign in as $ACCOUNT (a browser will open) ==="
gcloud auth login "$ACCOUNT"

echo
echo "=== 2/5  Your projects ==="
gcloud projects list

echo
read -rp "Paste the PROJECT_ID that has the trial credit: " PROJECT_ID
gcloud config set project "$PROJECT_ID"

echo
echo "=== 3/5  Credentials for the Python SDK (a browser will open again) ==="
gcloud auth application-default login

echo
echo "=== 4/5  Enabling APIs (takes a minute) ==="
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

echo
echo "=== 5/5  Writing the project into .env ==="
cd "$(dirname "$0")/.."
touch .env
grep -v '^GCP_PROJECT=' .env > .env.tmp 2>/dev/null || true
mv .env.tmp .env
{
  echo "GCP_PROJECT=$PROJECT_ID"
  # "global", not a region. The Gemini 3.x publisher models return 404 NOT_FOUND
  # on us-central1; they are only served from the global endpoint.
  echo "GCP_LOCATION=global"
} >> .env

echo
echo "Done. Project: $PROJECT_ID"
echo "Now tell Claude: \"gcp is set up, project is $PROJECT_ID\""
