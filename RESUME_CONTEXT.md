# Resume context — Production RAG with Evals and LLM as a Judge

Reference sheet for a resume-editing agent. **Every number here is measured and reproducible from
the repository.** Do not round up, extrapolate, or add metrics that are not in this file.
Target roles: **AI Engineer, Forward Deployed Engineer (FDE)**.

---

## 1. Identity

| Field | Value |
|---|---|
| Project name | Production RAG with Evals and LLM as a Judge |
| Short name | Production RAG Support Agent |
| Project page (link this on resumes) | https://anshd15.github.io/production-rag-evals-llm-judge/ |
| Live demo | https://rag-triage-5uebwq4ema-uc.a.run.app |
| GitHub | https://github.com/anshd15/production-rag-evals-llm-judge |
| Status | Deployed, public, working |
| Scale | 51 commits · 4,148 lines of Python · 77 tests · 84 decision-log entries |

**One-line description:** A retrieval-augmented customer-support agent that classifies intent,
drafts a reply grounded in real precedent, and decides whether a human must handle it — plus the
evaluation harness that proves it is safe to deploy.

---

## 2. What it does

For every incoming customer message:

1. **Classifies intent** into 1 of 11 categories derived from the data by KMeans clustering
2. **Retrieves 5 similar past tickets** from 33,838 historical customer→agent exchanges
3. **Drafts a reply** grounded in how the brand actually resolved those cases
4. **Decides auto-handle vs. escalate**, with 1 of 6 named escalation reasons

Dataset: Kaggle *Customer Support on Twitter*, SpotifyCares subset, ~40k real conversations.

---

## 3. Headline metrics (golden set, n=200, human-labelled)

| Metric | Agent | TF-IDF baseline | Canned-reply baseline |
|---|---|---|---|
| Intent accuracy | **75.5%** [69–81] | 51.5% | 23.0% |
| Macro-F1 | **71.5%** | 43.3% | 3.4% |
| Escalations caught | **81.8%** [72–91] | 57.6% | 0% |
| Replies a reviewer would send † | **81.4%** [76–86] | 44.5% | 7.0% |
| Auto-handled | 66.0% | 75.0% | 100% |
| Auto-sent when a human was needed | **6.0%** | 14.0% | 33.0% |

**Paired bootstrap vs. TF-IDF baseline (95% CI):**
- Intent accuracy: **+24.0pp [+15.5, +32.5]**, P(not better) = 0.000
- Would-send: **+36.7pp [+29.6, +44.7]**, P(not better) = 0.000

**Dev set (n=250, independent split):** intent 82.0%, would-send 87.2%

† Judge-scored, not human-scored. See §4.

---

## 4. Evaluation rigor — the differentiator

| Component | Detail |
|---|---|
| Golden set | **200 messages hand-labelled** by the author; intent + escalate + reason |
| Dataset versioning | sha256 manifest, row counts, schema validation — **fails CI on drift** |
| Baselines | 2 (TF-IDF + logistic regression; majority-class + canned reply) |
| Confidence intervals | Percentile + **paired** bootstrap on every headline number |
| Leakage control | Time-based split, retrieval cutoff, eval customers excluded from the index |
| LLM-as-a-judge | Binary rubric over 5 criteria + a send decision |
| **Judge validation** | **60 blinded human ratings · Cohen's κ = 0.63 · 82% agreement** |
| Judge bias probes | Verbosity, position, self-preference |
| Label quality | Human vs. LLM labels: κ 0.80 intent, κ 0.79 escalate |

### Findings worth quoting (all are negative or self-critical results)

1. **The development stand-in model overstated safety.** Swapping to the real model moved
   escalation recall 86.4% → 81.8% and unsafe-auto 4.5% → 6.0%. **Replicated on an independent
   250-message split** (−4.4pp, +1.2pp). Two samples, 450 messages, same direction.
2. **The judge is harsher than the human, not kinder.** Self-preference was predicted and did not
   appear: judge approves 53% where the human approves 62%.
3. **The judge is unreliable on groundedness** — κ = 0.18, passing 92% where a human passes 73%.
   Reported with a warning rather than quoted as a headline.
4. **AI-generated labels flattered the agent by ~10 points** (82% → 71.5%), caught by a blind
   control group: 0/94 overrides when the AI label was visible vs. 36% disagreement blind.
5. **A definition, not a model, was the biggest lever** — sharpening the escalation rule moved
   escalation precision 64% → 78% **with predictions unchanged**.
6. **Three measured iterations produced no detectable improvement**, and one prompt change was
   measurably worse and was reverted.

---

## 5. Guardrails and safety

| Guard | Implementation |
|---|---|
| Prompt-injection screening | Deterministic regex, runs **before** the model sees the text |
| PII redaction | **Luhn-validated** card detection, email + phone; redacted before the prompt |
| Risk routing | Legal/safety keywords force escalation |
| Unverifiable-claim blocking | Blocks drafts claiming actions the agent cannot have taken |
| Output policy | Hard 280-char truncation, schema validation, fallback-to-human on bad output |
| Red team | **25 adversarial cases, 4 failed on first run**, now green in CI |

Deliberately **not** LLM-based: the safety layer is the part you least want to be probabilistic.

---

## 6. Production engineering

| Area | Detail |
|---|---|
| Serving | FastAPI, Docker, **Google Cloud Run**, scale-to-zero |
| Model | Gemini 3.5 Flash Lite on **Vertex AI** |
| Auth to model | **Application Default Credentials via runtime service account — no API key anywhere** |
| Latency | **1.3s warm**, ~50s cold start |
| Resilience | Circuit breaker, jittered exponential backoff, timeouts, graceful degradation to human |
| Observability | Prometheus-format metrics, structured JSON logs, token + cost accounting |
| Rate limiting | Per-IP sliding window (`--proxy-headers` so it counts real clients) |
| Spend control | Per-process call cap, max-instances bound, GCP budget alert |
| CI | 77 tests + results integrity + red team + dataset checksums + **metric regression gate** |
| Human-in-the-loop | Review console, decision capture, outcome recording, accept-rate reporting |

### Google OAuth with graduated access
- **3 free messages, no sign-in** → then Google sign-in for a higher allowance
- Anonymous use metered by **cookie AND IP, larger wins** — clearing cookies does not reset it
- HMAC-signed session cookie (`compare_digest`), ID token verified server-side
- Consent screen published to production; privacy policy written to match what the code does

---

## 7. Retrieval details

| Item | Value |
|---|---|
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, 384-dim, L2-normalised, CPU |
| Index | 33,838 historical exchanges, exact cosine search |
| Quality | precedent@5 = 0.609, route@1 = 74.8% |
| Hybrid (dense + TF-IDF, RRF) | +0.008 — **not significant**, so not shipped |
| Qdrant backend | Implemented and measured: **450/450 identical results**, kept behind a flag |
| Bug found by the parity study | `np.argsort` is not stable — tie-breaking was non-deterministic across machines |

---

## 8. Tech stack keywords (for the skills section)

**AI/ML:** RAG · LLM-as-a-Judge · Model Evaluation · Prompt Engineering · Vertex AI · Gemini API ·
Sentence Transformers · Embeddings · Vector Search · scikit-learn · KMeans · TF-IDF · Cohen's Kappa ·
Bootstrap Confidence Intervals

**Backend:** Python · FastAPI · REST APIs · Pydantic · pytest

**Cloud & DevOps:** Google Cloud Platform · Cloud Run · Docker · Artifact Registry · Cloud Build ·
IAM · Service Accounts · CI/CD (GitHub Actions)

**Data:** pandas · NumPy · PyArrow · Qdrant

**Auth & Security:** OAuth 2.0 · Google Identity · HMAC sessions · PII redaction · Prompt-injection
defense · Rate limiting

---

## 9. Ready-to-use resume bullets

### Three-bullet version (recommended, matches existing resume format)

> **Production RAG Support Agent : Evaluated LLM Triage System** (Gemini, Vertex AI, FastAPI, Cloud Run) — *[Live Demo] [GitHub]*
>
> • Built a retrieval-augmented agent over 40k real customer-support conversations that classifies intent, drafts a reply grounded in retrieved precedent, and decides auto-handle vs. human escalation; containerized and deployed on Cloud Run with 1.3s warm latency.
>
> • Hand-labelled a 200-message golden evaluation set and benchmarked against two baselines using paired bootstrap confidence intervals — +24.0pp intent accuracy over a TF-IDF baseline (95% CI excludes zero); dataset versioned with checksum verification enforced in CI.
>
> • Validated the LLM-as-a-judge against 60 blinded human ratings (Cohen's κ = 0.63) and shipped deterministic guardrails — prompt-injection screening, Luhn-validated PII redaction, unverifiable-claim blocking — covered by 25 adversarial red-team cases running in CI.

### Optional fourth bullet (if space allows)

> • Added Google OAuth with graduated access — 3 free messages, then sign-in — metering anonymous use by cookie and IP so clearing cookies cannot reset it; bounded LLM spend with per-instance call caps, rate limiting and budget alerts.

### Two-bullet version (tight space)

> • Built and deployed a retrieval-augmented support agent (Gemini on Vertex AI, FastAPI, Cloud Run) over 40k real conversations — classifies intent, drafts grounded replies, routes to humans; +24.0pp intent accuracy over a TF-IDF baseline with paired bootstrap CIs on a 200-message hand-labelled eval set.
>
> • Validated the LLM-as-a-judge against 60 blinded human ratings (κ = 0.63) and shipped deterministic guardrails — injection screening, Luhn-validated PII redaction, 25 red-team cases — all gated in CI alongside dataset checksums and a metric regression gate.

---

## 10. Interview talking points

| Question | Answer |
|---|---|
| Hardest problem? | The stand-in model used in development **overstated safety** — escalation recall 86.4% vs. a real 81.8%. Replicated on a second split. Caught it because the harness compares runs rather than trusting one. |
| How do you know the judge is right? | 60 blinded human ratings, κ = 0.63. Predicted self-preference, found the opposite. The judge is bad at groundedness (κ 0.18), so that number is not quoted. |
| Why no vector database? | Qdrant is implemented and measured — **450/450 identical results**. At 33,838 vectors a brute-force matmul *is* exact search. Adopting it buys incremental updates and cold start, not better answers. |
| Why aren't the guardrails LLM-based? | Safety is the part you least want to be probabilistic. Regex and Luhn are unit-testable, which is why red-team is 25/25 in CI rather than a claim. |
| What would you do next? | A knowledge-retrieval route for `how_to_usage` (29% recall — structurally unfixable by prompting), and a second human rater for inter-annotator κ. |

---

## 11. Honesty constraints — do not violate

The value of this project is that its claims are verifiable. An inflated bullet is worse than no
bullet, because a reviewer can open the repo.

**Do NOT write:**
- "99% accuracy" or any number not in this file
- "Processed millions of..." — it is 40k conversations, 33,838 indexed
- "Reduced support costs by X%" — no deployment to real customers, no cost data
- "Built a vector database" — Qdrant is behind a flag and not the default
- "Fine-tuned an LLM" — no fine-tuning; prompting + retrieval only
- "Eliminated hallucinations" — groundedness is the judge's *weakest* criterion
- "Real-time" — warm latency is 1.3s, cold start ~50s

**Phrases that are accurate and strong:** "hand-labelled", "paired bootstrap confidence intervals",
"validated against human ratings", "measured and reverted", "deterministic guardrails",
"gated in CI".
