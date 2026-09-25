# Runbook

## Deploy

```bash
docker compose up --build            # offline: answers from the committed cache
API_KEY=... GEMINI_API_KEY=... LLM_OFFLINE=0 docker compose up --build   # live model
python -m src.smoke --url http://localhost:8000 --n 20   # gate: contract + p50/p95, exit 1 on failure
```

The retrieval index builds on first request (~2 min). `/readyz` reports `cold` until then —
that is why the container healthcheck has a 180s start period. Do not wire `/readyz` to a
liveness probe; it will kill the container during startup.

## Dashboards

`GET /metrics` (Prometheus text). The numbers worth alerting on:

| Metric | Watch for | Why |
|---|---|---|
| `rag_automation_rate` | sudden rise | the agent auto-handling more usually means it stopped escalating, not that it got smarter |
| `rag_guardrail_prompt_injection` | any spike | someone is probing the bot |
| `rag_breaker_opened` | > 0 | the model provider is failing; the service is shedding load |
| `rag_errors` / `rag_pending` | rising | model errors, or stand-in mode left on in production |
| `rag_latency_ms_avg` | > 3000 | retrieval or the provider is degrading |
| `rag_rate_limited`, `rag_auth_rejected` | rising | abuse, or a client misconfigured after a key rotation |

Quality does not appear here, by design: it comes from `GET /feedback/report` (accept rate per
intent, the intents whose drafts get edited most). A falling accept rate is the earliest signal
that traffic has shifted away from what the agent was evaluated on.

## Incidents

**Model provider down.** The breaker opens after `BREAKER_THRESHOLD` consecutive failures and
`/triage` returns 503 with `Retry-After`. Nothing is silently answered wrong. Degraded mode is
"everything goes to a human", which a support team can absorb; wrong auto-replies they cannot.

**Latency climbing.** Check `/readyz` first — a restarted container rebuilds the index. If it is
warm, the provider is slow: lower `GEMINI_RPM`, or raise `LLM_TIMEOUT_S` only if you would rather
wait than shed.

**A bad reply reached a customer.** Find it by `request_id` in the logs (`event=triage`), then in
`data/feedback/decisions.jsonl` — the stored decision carries the retrieved cases that produced
it, so you can tell a retrieval failure from a model failure without re-running anything. Add the
message to `eval/redteam/cases.jsonl` if a guardrail should have caught it.

**Quality drifting.** Re-run the offline suite (`python -m src.evaluate --split golden --run <name>`)
and `python -m src.gate`. The gate's floors sit ~5pp under the committed run, wide enough to
ignore resampling noise and tight enough to catch a real regression.

## Rotating the API key

`API_KEY` is read once at import, so change it and restart. Clients send `X-API-Key`. With it
unset the service is open — fine locally, not on a public port.

## What this service does not do

No account lookups, no refunds, no DM handling. It classifies, drafts, and routes. Every action
that touches a customer's account is a human's, by design — see `reports/DECISION_LOG.md`.
