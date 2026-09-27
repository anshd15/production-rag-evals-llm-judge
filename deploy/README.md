# Deploying the demo

The demo exists so someone can see the routing decision, the evidence behind it and the
guardrails firing, without cloning anything. It is not the product.

## Why Cloud Run and Qdrant Cloud, not a VM

| | Chosen | Rejected | Reason |
|---|---|---|---|
| Compute | Cloud Run | Compute Engine VM | The always-free tier does not expire. A trial credit runs out in ~90 days, and a dead demo link on a CV is worse than no link. No host to patch either. |
| Vectors | Qdrant Cloud free tier | Qdrant on the same VM | ~52 MB of vectors (33.8k × 384 × 4 bytes) fits the free tier many times over, and it is what makes scale-to-zero possible at all. |
| Index | persisted in Qdrant | rebuilt at boot | The numpy backend re-embeds the corpus on first request (~2 min). On a scale-to-zero host that bill is paid after every idle period. |

## One-time setup

```bash
# 1. Qdrant Cloud: create a free cluster, copy its URL and API key.
export QDRANT_URL=https://xyz.cloud.qdrant.io:6333
export QDRANT_API_KEY=...

# 2. Load the vectors (runs locally, reads the committed embedding cache).
RETRIEVAL_BACKEND=qdrant python -m src.retrieval_qdrant upsert
python -m src.retrieval_qdrant status        # expect 33,838 points

# 3. Confirm exact search still returns what numpy returned. If this reports
#    anything below 100% parity, the committed golden numbers are void.
python -m src.retrieval_backend_eval --backends numpy qdrant-exact

# 4. Deploy.
export PROJECT_ID=... GEMINI_API_KEY=...
./deploy/cloudrun.sh
```

## Before you share the link

A public demo endpoint is a public LLM endpoint someone else is paying for.

- **Budget alert** on the GCP project, and a quota cap on the Gemini key.
- `LLM_MAX_CALLS` is a hard per-instance stop, and `--max-instances 3` bounds how many
  instances can be spending at once. Those two together are the spend cap.
- `RATE_LIMIT_PER_MIN` is per instance, not global. With 3 instances the real ceiling is
  3× what it says. It is a speed bump, not a guarantee.
- The input guardrails stop being a test suite the moment the endpoint is public. That is
  the point, and it is worth saying out loud in an interview.

## Rolling back

Cloud Run keeps every revision. `gcloud run services update-traffic rag-triage
--to-revisions REVISION=100` reverts without a rebuild.
