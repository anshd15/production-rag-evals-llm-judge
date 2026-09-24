# Handoff — a support agent that knows when to step aside

A retrieval-augmented support agent for **SpotifyCares**, built from the Kaggle *Customer Support on Twitter*
dataset. For every incoming customer tweet it:

1. **classifies the intent** into one of 11 intents derived from the data,
2. **drafts a reply grounded in how SpotifyCares actually resolved similar tweets** (retrieval
   over ~34k historical replies), and
3. **decides auto-handle vs. escalate**, with one of 6 named reasons.

Most of the work is in the **evaluation**: a hand-labelled golden set, two baselines, an
LLM-as-judge rubric checked against a human, bootstrap confidence intervals, and leakage checks.

> 📄 Report: [`reports/REPORT.md`](reports/REPORT.md) · Decision log: [`reports/DECISION_LOG.md`](reports/DECISION_LOG.md)

## Status

| | |
|---|---|
| Pipeline, baselines, evaluation harness, 4 improvement iterations | done |
| Golden-set predictions + judge verdicts for all 3 systems | done (committed) |
| **Hand-labelling the 200 golden messages** | **pending** — `python -m src.label_app`, tab 1 |
| **Rating 60 replies for judge agreement** | **pending** — same tool, tab 2 |
| Final numbers, judge κ, label-noise check | one command after the above: `python -m src.finish` |

Reply-quality results (golden, n=200) are already measurable without labels: the agent's drafts
are approved by the judge **73.0%** of the time vs **44.5%** for a TF-IDF nearest-neighbour reply
and **11.0%** for the most common canned reply (+28.5pp over the simple baseline, 95% CI
[+21.0, +36.5]).

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
   └─► guardrails: invalid output → escalate · legal/self-harm keywords → escalate
                   · reply ≤ 280 chars
```

## Repo layout

```
src/            pipeline (data_prep, taxonomy, prompts, llm, retrieval, agent, baselines,
                evaluate, metrics, analyze, judge_agreement, label_app, check_results)
tests/          unit tests (pytest), run in CI
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
