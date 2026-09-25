# Data card — SpotifyCares support triage (golden v1.0)

## What this is

200 real customer messages sent to `@SpotifyCares` on Twitter, each labelled by hand with an
intent (11 classes) and a routing decision (auto-handle, or escalate with one of 6 reasons).
It exists to answer one question honestly: **how often does the agent agree with a person?**

Alongside it: a 250-message dev set with LLM ("silver") labels used for all tuning, and 60
blinded reply drafts used to check the LLM judge against a human.

| File | Rows | Role |
|---|---|---|
| `data/processed/golden_set.jsonl` | 200 | test messages |
| `data/processed/golden_labels.jsonl` | 200 | human labels |
| `data/processed/dev_set.jsonl` | 250 | tuning messages |
| `data/processed/dev_silver_labels.jsonl` | 250 | LLM labels |
| `data/processed/rating_set.jsonl` | 60 | drafts for judge agreement |

Checksums and row counts are pinned in `data/golden/v1/manifest.json`; `python -m src.dataset
verify` runs in CI, so an accidental re-sample or a hand-edited label fails the build instead of
silently moving every number in the report.

## Where it comes from

Kaggle *Customer Support on Twitter* (Thought Vector), CC BY-NC-SA 4.0 — 2.8M tweets, of which
40,161 are SpotifyCares conversations after cleaning. Redistributed here as a non-commercial
subsample with attribution, under the same licence.

Handles are already pseudonymised upstream (`@115888`), emails appear as `__email__`, and URLs
are replaced with `[link]` during cleaning. No message in either split trips the PII screen.

## How the splits were drawn

**By time, not at random.** Threads starting on or after 2017-11-25 form the evaluation pool;
everything earlier is the retrieval corpus. A random split would let the agent retrieve the reply
to the very message it is answering.

Golden = 150 sampled at random from that pool (so headline rates reflect the real class mix) plus
50 drawn from the smallest embedding clusters (so rare intents have enough support for per-class
metrics). The `stratum` field records which is which. One message per thread; no thread and no
customer appears in both golden and dev.

## How it was labelled

One annotator, 200 messages, labelling from exactly what the agent sees — the reply SpotifyCares
actually sent is **hidden** during labelling, so the escalation label cannot be copied from the
brand's behaviour.

The protocol changed mid-way, and the reason matters:

1. The first 50 were labelled blind in a purpose-built tool.
2. The next 94 were labelled with an AI suggestion pre-filled. The annotator accepted **94 of
   94** — while on the blind 50 they disagreed with that same model on 36% of intents. At a true
   disagreement rate of ~36%, 94 consecutive agreements has probability ~1e-18, so those labels
   were not independent judgements. **They were discarded.**
3. All 200 were then labelled from an offline JSON pack containing no model suggestions
   (`labelling/questions.json`, `labelling/HOW_TO_LABEL.md`).

This is why the blind control group existed at all, and it is the honest reason the set can be
called hand-labelled.

## Label quality

Against the LLM's independent labels on the same 200 messages: **83% intent agreement (κ 0.80)**
and **91% agreement on escalate (κ 0.79)**. So roughly a sixth of this task is genuinely
contested — the agent's 71.5% intent accuracy should not be read against a ceiling of 100%.

There is **no second human annotator**, so the inter-annotator ceiling is unknown. That is the
single biggest gap in this dataset and the first thing to fix with more time.

## Known limitations

- **One brand, two months, one language.** Late-2017 Spotify traffic includes a Wrapped season and
  specific outages; class mix will not transfer to another brand or period.
- **One annotator**, who is also the system's author — a conflict of interest that blinding and
  the frozen-set rule reduce but do not remove.
- **Public tweets only.** Everything after "please DM us" is invisible, so no label describes
  whether the case was actually resolved.
- **Two non-English messages** remain (Indonesian, Dutch), labelled `other`. Realistic traffic,
  but the set cannot measure multilingual quality.
- **No outcome signal**: no CSAT, no re-contact rate, no resolution flag. "Would a team lead send
  this?" is the strongest proxy available here.

## Appropriate use

Built for evaluating routing and reply quality in this repo. Reasonable for benchmarking a
similar triage system; **not** suitable as training data for a production classifier (too small,
single-annotator), and **not** for commercial use (upstream licence).
