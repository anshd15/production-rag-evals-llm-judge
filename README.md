# Production RAG with Evals and LLM as a Judge

A retrieval-augmented customer-support agent that knows when **not** to answer — and the
evaluation harness that proves it. Built on the Kaggle *Customer Support on Twitter* dataset
(SpotifyCares subset, ~40k real conversations). For every incoming customer message it:

1. **classifies the intent** into one of 11 intents derived from the data,
2. **drafts a reply grounded in how SpotifyCares actually resolved similar tweets** (retrieval
   over ~34k historical replies), and
3. **decides auto-handle vs. escalate**, with one of 6 named reasons.

Most of the work is in the **evaluation**: a 200-message hand-labelled golden set, two baselines,
an LLM-as-judge rubric checked against human ratings, bootstrap confidence intervals, and leakage
checks that run in CI.

| | Agent | TF-IDF baseline | Canned reply |
|---|---|---|---|
| Intent accuracy | **75.5%** [69–81] | 51.5% | 23.0% |
| Escalations caught | **81.8%** [72–91] | 57.6% | 0% |
| Replies a reviewer would send † | **81.4%** [76–86] | 44.5% | 7.0% |
| Auto-handled | 66.0% | 75.0% | 100% |
| **Auto-sent when a human was needed** | **6.0%** | 14.0% | 33.0% |

Gemini 3.5 Flash Lite on Vertex AI, scored against 200 messages labelled by hand. Reproducible
offline from the committed cache: `python -m src.evaluate --split golden --run final_vertex`.

† **The routing rows are scored against human labels. The reply row is not** — it is an
LLM judge, and judge-vs-human agreement is not yet established (2 of 60 blinded ratings).
Read 81.4% as provisional. `reports/judge_robustness.md` measures this judge approving the
agent's own longer drafts +8pp more often, and it is now the same model family as the agent,
so the bias runs toward flattery.

### The stand-in was not a neutral proxy

Development ran against a stand-in model. Swapping in the real one moved the numbers in
**both** directions, which is the reason the swap is reported rather than quietly applied:

| | Stand-in | Gemini (Vertex) | |
|---|---|---|---|
| Escalations caught | 86.4% | **81.8%** | safety was **overstated** |
| Auto-sent when a human was needed | 4.5% | **6.0%** | safety was **overstated** |
| Intent accuracy | 71.5% | **75.5%** | quality was understated |
| Replies a reviewer would send † | 73.0% | **81.4%** | quality was understated |

The same model run through AI Studio instead of Vertex (`runs/final_gemini`) reproduces
81.8% escalation recall and 6.0% unsafe-auto exactly, so the gap is the model, not the transport.

> 📄 Report: [`reports/REPORT.md`](reports/REPORT.md) · Decision log: [`reports/DECISION_LOG.md`](reports/DECISION_LOG.md)

## Status

| | |
|---|---|
| Pipeline, baselines, evaluation harness, 4 measured iterations | done |
| 200-message golden set, hand-labelled | done |
| Guardrails: injection screening, PII redaction, unverifiable-claim blocking | done |
| Service, container, feedback capture, deploy gate | done |
| **Judge-vs-human agreement (60 blinded ratings)** | **2/60 rated** — κ not reportable yet |
| Final numbers on a live model | done — Gemini 3.5 Flash Lite on Vertex AI (`runs/final_vertex`) |
| Cloud Run demo endpoint | not deployed |

## Run it as a service

```bash
pip install fastapi "uvicorn[standard]"
uvicorn src.service:app --port 8000          # or: docker compose up
curl -X POST localhost:8000/triage -H "Content-Type: application/json"      -d '{"text": "charged twice for premium this month, sort it out"}'
python -m src.smoke --n 20 --concurrency 4   # contract + latency check, non-zero exit on failure
```

| Endpoint | Purpose |
|---|---|
| `POST /triage` | intent, routing decision + reason, drafted reply, request id, latency |
| `GET /review` | the review console: queued drafts, why each routed that way, the past cases behind it, accept / edit / reject |
| `POST /feedback` | what the human did with the draft: accepted / edited / rejected |
| `GET /feedback/report` | live accept rate and the intents whose drafts get edited most |
| `GET /metrics` | automation rate, escalation rate, guardrail fires, average latency |
| `GET /healthz`, `/readyz` | liveness, and whether the retrieval index is warm |

The index builds on first request (~2 min), so `/readyz` reports cold until then.
Guardrails run on the way in (instruction-override attempts, PII redaction with Luhn-checked
card numbers) and on the way out (unverifiable claims, legal/self-harm keywords, 280-char cap).

## Reproduce the headline results (< 15 min, no API key)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt   # ~3-5 min (PyTorch CPU)
set LLM_OFFLINE=1                 # export LLM_OFFLINE=1 on macOS/Linux: cache only, no API calls
python -m src.evaluate --split golden --run final   # ~3 min: embeds the retrieval index, replays cached LLM calls
python -m src.check_results       # leakage + "metrics match predictions" checks
```

`data/processed/` (the SpotifyCares subsample, frozen eval sets, labels) and `llm_cache/`
(every LLM response, keyed by a hash of model + prompt) are committed, so the numbers above
are reproduced exactly without downloading the 500 MB raw dump or calling any model.

## Full pipeline

| Step | Command | Output |
|---|---|---|
| 1. Build brand conversations | `python -m src.data_prep` (needs `data/raw/twcs/twcs.csv`) | `data/processed/messages.parquet` |
| 2. Intent discovery | `python -m src.discover_intents` | `reports/intent_discovery.md` → `src/taxonomy.py` |
| 3. Sample eval sets (frozen) | `python -m src.make_eval_sets` | `golden_set.jsonl` (200), `dev_set.jsonl` (250) |
| 4. Silver-label the dev set | `python -m src.silver_label dev` | `dev_silver_labels.jsonl` |
| 5. Hand-label golden + rate replies | `python -m src.label_app` → http://localhost:8765 | `golden_labels.jsonl`, `human_reply_ratings.jsonl` |
| 6. Evaluate | `python -m src.evaluate --split dev\|golden --run NAME` | `runs/NAME/<split>/` |
| 7. Failure analysis | `python -m src.analyze --run NAME --split dev` | `runs/NAME/<split>/failures.md` |
| 8. Judge vs human | `python -m src.judge_agreement make\|score --run NAME` | `reports/judge_agreement.md` |
| 9. Red-team the guardrails | `python -m src.redteam` | `reports/redteam.md` (runs in CI) |
| 10. Retrieval quality | `python -m src.retrieval_eval` | `reports/retrieval_quality.md` |
| 11. Judge bias checks | `python -m src.judge_robustness --run final` | `reports/judge_robustness.md` |

Raw data: download `twcs.zip` from
[Kaggle](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) and unzip to
`data/raw/twcs/twcs.csv`.

## LLM providers

Set in `.env` (see `.env.example`):

| `LLM_PROVIDER` | What happens on a cache miss |
|---|---|
| `gemini` | calls Google Gemini (`GEMINI_API_KEY`; models via `GEMINI_AGENT_MODEL` / `GEMINI_JUDGE_MODEL`, rate via `GEMINI_RPM`) |
| `standin` | writes the prompt to `llm_queue/` to be answered offline by a separate model session, then `python -m src.llm ingest` |

`LLM_OFFLINE=1` forbids new calls entirely. Cache files are per provider+model, so results from
different models never mix. See decision 19 in the log for why a stand-in provider exists.

## How the agent works

```
customer tweet (+ up to 4 previous turns)
   │
   ├─► retrieval: MiniLM embeddings over 33.8k SpotifyCares (tweet → reply) pairs sent
   │   before 2017-11-25, excluding every customer in the eval sets  → top-5 similar cases
   │
   ├─► one LLM call: taxonomy + escalation policy + reply rules + 5 cases
   │   → {intent, confidence, escalate, escalation_reason, reason, reply}
   │
   └─► output guardrails: invalid JSON → escalate · legal/self-harm keywords → escalate
                          · unverifiable claims ("we've replied to your DM") → escalate
                          · reply ≤ 280 chars
```

Input is screened **before the prompt is built** (`src/guardrails/input.py`): an
instruction-override attempt never reaches the model at all, and PII (Luhn-checked card numbers,
emails, phone numbers) is redacted, so it cannot enter a prompt, a cache file or a log.

## Repo layout

```
src/            offline pipeline (data_prep, taxonomy, prompts, llm, retrieval, agent, baselines,
                evaluate, metrics, analyze, judge_agreement, label_app, check_results)
                serving (service, observability, feedback, input_guards, smoke)
tests/          unit tests (pytest), run in CI
labelling/      offline labelling + rating packs (questions, guidelines, importers)
data/processed/ brand subsample, frozen eval sets, labels (committed)
llm_cache/      every LLM response (committed; makes results reproducible)
runs/           predictions, judgements, metrics and failure analyses per run
reports/        REPORT.md, DECISION_LOG.md, intent discovery, judge agreement
```

## Credits & borrowed pieces

- Dataset: *Customer Support on Twitter*, Thought Vector, Kaggle — CC BY-NC-SA 4.0. This repo
  redistributes a SpotifyCares subsample for non-commercial evaluation, with attribution.
- Embeddings: [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (Apache-2.0).
- Libraries: pandas, scikit-learn (TF-IDF, logistic regression, KMeans, Cohen's κ), PyTorch,
  sentence-transformers, google-genai.
- Techniques (standard, not code): retrieval-augmented generation; LLM-as-judge with a binary
  rubric; percentile bootstrap and paired bootstrap for confidence intervals.
- Built with an AI coding assistant (Claude Code); all design decisions are in the decision log.
