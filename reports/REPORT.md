# Production RAG with evals and an LLM judge — report

*Case study: a support agent for SpotifyCares, built from the Kaggle Customer Support on Twitter
dataset. Every number here is reproducible offline with `python -m src.evaluate --split golden
--run final` under `LLM_OFFLINE=1`; the golden set is 200 messages labelled by hand.*

## 1. Problem framing: what "good" means for SpotifyCares

SpotifyCares answers ~500 inbound tweets a day. Reading two months of them, the work splits into
three kinds:

- **Standard answers** (~60%): where an album is, why ads play, how Family plans work, first-line
  troubleshooting, acknowledging feature requests, thanking people. The reply is the same
  whoever writes it.
- **Account work** (~30%): "charged twice", "can't log in", "Premium not active", "can't add my
  daughter to Family". Nobody can resolve these from the tweet alone — the brand's own move is
  "DM us your account email", after which a human works the case in DMs.
- **Risk** (~5%): hacked accounts, legal threats, people chasing an unanswered DM for the third
  time.

So "good" is **not** "answer everything". It is: *close the standard tickets end-to-end with
replies a team lead would send unedited, and route everything else to a human quickly, without
ever auto-sending into a money or security problem.*

That gives the two numbers this project optimises:

- **Good automation rate** — share of all inbound messages that are auto-handled **and** should
  have been **and** whose reply the judge would send as-is. This is the value.
- **Bad auto-send rate** — share auto-handled that should have been escalated, or whose reply
  fails the rubric. This is the cost, and it is not symmetric: one auto-reply telling a
  double-charged customer to "try logging out and back in" costs more than ten needless handoffs.

### What I chose not to build

- **DM handling.** The dataset stops at the public tweet; everything after "DM us" is invisible.
  The agent decides *routing*, it doesn't work the case.
- **Actual account lookups / tools.** No account API exists here, so "resolve a billing dispute"
  is out of scope by construction — which is exactly why routing quality matters.
- **Non-English support** (SpotifyCares replies in English and points elsewhere; ~2% of traffic).
- **Fine-tuning.** 250 dev labels would overfit instantly; prompt + retrieval is the right
  instrument at this data size.
- **A UI, a queue, or a deployment.** The brief asks for proof, not a product.

## 2. Data and evaluation design

| | |
|---|---|
| Source | Kaggle *Customer Support on Twitter*, brand `SpotifyCares` |
| Unit | every inbound customer tweet SpotifyCares replied to, plus up to 4 previous turns |
| Usable messages | 40,161 (English, non-empty, reply present) |
| History (retrieval + baseline training) | 33,838 messages sent before 2017-11-25 |
| Evaluation pool | 5,698 messages from threads starting on/after 2017-11-25 |
| **Golden set (test)** | **200** hand-labelled: 150 random + 50 spread across rare clusters |
| **Dev set** | **250** LLM-labelled ("silver"), used for every iteration |

**Leakage control.** The split is by time, not random, and the retrieval index additionally drops
(a) anything sent after the cutoff and (b) every customer who appears in an eval set.
`src/check_results.py` re-verifies on every CI run that no retrieved message is an eval message
and that no thread or customer is shared between the sets.

**Labels.** 11 intents derived from 30 KMeans clusters over history tweets, plus a binary
route (auto-handle / escalate) with 6 named reasons. The human labeller sees exactly what the
agent sees — never the reply SpotifyCares actually sent — so the escalation label can't be copied
from the brand's behaviour. As a sanity check the two agree 78% of the time: the brand asked for
a DM in 54% of escalate-labelled messages and 11% of auto-labelled ones — correlated, not identical.

**Reply quality** is judged by an LLM with a 5-criterion binary rubric (addresses the issue,
grounded, correct next step, tone, safe) plus "would you send this as-is?". The judge sees the
real SpotifyCares reply as a reference but is told a different wording can still pass. Judge
verdicts are only trusted as far as they match a human — see §6.

## 3. Results

### Golden set (n=200, human labels) — `runs/final_vertex/golden/summary.md`

Gemini 3.5 Flash Lite on Vertex AI, judge `gemini-3.1-flash-lite`.

| System | Intent acc | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send | Good automation |
|---|---|---|---|---|---|---|---|
| **agent** | **75.5%** [69–81] | **81.8%** [72–91] | 79.4% | 66.0% | **6.0%** | **81.4%** [76–86] | 46.2% [39–53] |
| simple (TF-IDF + NN reply) | 51.5% [45–58] | 57.6% [45–70] | 76.0% | 75.0% | 14.0% | 44.5% [37–51] | 23.0% [18–28] |
| trivial (majority + canned reply) | 23.0% [18–29] | 0.0% | — | 100% | 33.0% | 7.0% [4–11] | 7.0% [4–11] |

The two baselines are the two ways to be wrong. The trivial system automates everything and
auto-replies into a human-needed case a third of the time; the simple one misses 42% of the
escalations and its copied replies are approved less than half as often. The agent auto-handles
66% of traffic while auto-sending into a human-needed case 6.0% of the time.

Paired bootstrap, agent minus the simple baseline: intent accuracy **+24.0pp** [+15.5, +32.5],
would-send **+36.7pp** [+29.6, +44.7]; P(agent not better) = 0.000 for both.

Per-class recall is uneven: `how_to_usage` collapses to 29% (see failure mode 3) while
`billing_payment` and `content_availability` reach 100%. Full table in the run summary.

Rubric pass rates for the agent: `safe` 100%, `tone` 100%, `grounded` 98%, `addresses_issue` 96%,
`correct_next_step` 86% — the last is the weakest link and the target of failure mode 4. Note that
`grounded` 98% is the judge's opinion and the judge is demonstrably too lenient on exactly this
criterion (§7, κ = 0.18); it should not be read as a 98% hallucination-free rate.

### The stand-in was not a neutral proxy

Development ran against a stand-in model, with the live run deferred until the harness was
finished. Swapping the real model in moved the headline in **both** directions:

| | Stand-in (`runs/final`) | Gemini on Vertex (`runs/final_vertex`) | |
|---|---|---|---|
| Escalations caught | 86.4% | **81.8%** | safety **overstated** by 4.6pp |
| Unsafe auto-send | 4.5% | **6.0%** | safety **overstated** by 1.5pp |
| Intent accuracy | 71.5% | **75.5%** | quality understated by 4.0pp |
| Would-send | 73.0% | **81.4%** | quality understated by 8.4pp |

The direction matters more than the size. A stand-in that made the system look *worse* would be a
harmless conservatism; this one made it look **safer than it is**, which is the failure mode that
ships. The same model reached through AI Studio rather than Vertex (`runs/final_gemini`)
reproduces 81.8% and 6.0% exactly, so the gap is the model, not the transport.

### Dev set (n=250, silver labels) — the same comparison with routing metrics

**These are still stand-in numbers.** The dev set drove the iteration loop and has not been
re-run on Gemini; given the golden-set gap above, treat the dev figures as indicative of the
*shape* of the comparison and not as measurements of the shipped model.

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|
| **agent (v5)** | **82.0%** [77–87] | 74.8% | 83.8% [74–92] | 73.1% | 68.8% | **4.4%** | 71.6% | 45.6% | 23.2% |
| simple | 53.6% [47–60] | 30.9% | 51.5% [40–63] | 67.3% | 79.2% | 13.2% | 50.8% | 31.6% | 47.6% |
| trivial | 35.6% [30–42] | 4.8% | 0.0% | — | 100% | 28.4% | 6.4% | 6.4% | 93.6% |

Read the two baselines as the two ways to be wrong. The trivial system automates everything and
is unsafe on 28% of messages; the simple system is cheap and fast but misses half the escalations
and its copied replies are approved half as often. The agent auto-handles 69% of traffic while
missing 4.4% of the cases that needed a human.

### What the numbers cost

Paired bootstrap, agent minus simple baseline (dev): intent accuracy **+28.4pp**
[+20.8, +34.4], would-send **+20.8pp** [+15, +27]. P(agent not better) = 0.000 in both.

## 4. What the improvement loop changed

Four iterations, each one change, each scored on dev against identical labels
(`python -m src.iteration_table`):

| Run | Change | Intent acc | Esc. precision | Would-send | Good automation | Verdict |
|---|---|---|---|---|---|---|
| v1 | baseline agent | 79.6% | 71.8% | 75.2% | 48.4% | — |
| v2 | escalation definition clarified (agent + labels) | 82.4% | 67.1% | 74.0% | 48.4% | within noise |
| v3 | `troubleshooting_exhausted` / `account_specific` sharpened | 82.0% | 73.1% | 71.6% | 45.6% | within noise |
| v4 | + explicit reply rules ("continue the thread", …) | 76.4% | 64.8% | **66.0%** | **39.6%** | **reverted** |
| **v5** | v3 + unverifiable-claim guardrail (**shipped**) | 82.0% | 73.1% | 71.6% | 45.6% | shipped |

Two results worth more than the deltas:

- **The definition was the bug, not the prompt.** Re-scoring v1's *unchanged predictions* against
  the re-labelled dev set moved escalation precision 64.1% → 78.2% and recall 82.0% → 85.9%. About
  14 points of what looked like model error was disagreement about what "escalate" means.
- **More instructions made the small model worse.** v4's reply rules cost 9.2pp of would-send
  (CI [-15.2, -3.2]) and 8.8pp of good automation. The prompt was already at the model's
  instruction budget; that failure mode belongs in retrieval instead (§8).

Across v1→v5 no routing-prompt edit moved any metric beyond its confidence interval. At n=250 the
honest summary is: **the loop improved the measurement and the safety net, not the model.**

## 5. Top failure modes

Counts are from the shipped agent on the 250-message dev set
(`runs/v5/dev/failures.md` has every example).

**1. Service-outage complaints land in `other`, and the reply invents a status (4 + related).**
"guess you're down" → intent `other`, reply *"Everything looks good on our end. What's happening?"*
The agent has no status signal, but retrieved cases contain SpotifyCares saying "everything should
be running smoothly now" — so it copies a **factual claim it cannot check**. Hypothesis: the
taxonomy has no `service_status` intent, so outage tweets fall through to `other`, and the reply
rules forbid inventing *policies* but not inventing *system state*. Fix: add the intent, forbid
status assertions, wire a status feed.

**2. Broken signup flows get re-labelled as billing and escalated (5).** "help I can't subscribe
to premium via load. Still stuck on typing my phone number" → `billing_payment` + escalate
(reason: billing). The intent boundary is "has money moved?", but customers describe *failed
purchase attempts* in money language. This is the single biggest source of needless escalation
(14 of 21 carry reason `account_specific`). Hypothesis: the billing/plan split is the wrong cut —
merging them and letting the escalation reason carry the distinction would remove the error class
without losing information.

**3. "How do I turn X off?" is read as feature feedback (3).** "HOW DO I BLOCK FRANKIE COSMOS FROM
APPEARING IN MY DAILY MIXES" → `feedback_feature_request`, reply *"vote for it here"*. The model
attends to the complaint tone rather than the question form, and the reply then fails
`addresses_issue`: the customer asked *how*, and got a suggestion box.

**4. The agent restarts threads it should continue (52 of 172 auto-sent replies fail
`correct_next_step`).** Mid-diagnosis, it answers "Can you tell us what's happening exactly?" when
the previous turns already say exactly that. Hypothesis: retrieval returns *opening* tweets far
more often than follow-ups, so the nearest cases model "first contact" behaviour. Notably, v4
attacked this with explicit prompt rules ("continue the thread") and made everything **worse**
(would-send −9.2pp) — the fix belongs in retrieval (separate indexes for openers and follow-ups),
not in more instructions.

**5. Claims the agent cannot verify (2 caught by the guardrail).** "We've just replied to your DM"
— true when a human writes it, false from a bot that cannot see the DM inbox. The regex guardrail
now forces those drafts to a human; the outage variant in failure mode 1 is the same disease and
is **not** yet covered.

**Safety residue:** 11 messages that should have escalated were auto-handled, spread across
`account_specific` (3), `repeat_contact` (3), `risk` (2), `billing`, `security`,
`troubleshooting_exhausted` (1 each). Unsafe-auto rate 4.4%, and no auto-sent reply failed the
`safe` rubric criterion.

## 6. What is misleading about my headline number

- **The dev numbers are AI-graded against AI labels.** The dev set's labels and the agent read the
  *same* taxonomy text, so they share blind spots (nothing about outages, so both sides get
  outage tweets consistently wrong and no metric notices). Only the golden set is human-labelled,
  and it is the only number that should be quoted.
- **`grounded` is the number not to trust.** The judge is now validated (§7, κ = 0.63 on the send
  decision), but per-criterion it is badly calibrated on groundedness: κ = 0.18, passing 98% of
  the agent's drafts where a human passes 73% of a blinded sample. Groundedness is the criterion
  that catches hallucination, and it is the one the judge is worst at. Do not quote it.
- **The single biggest lever was a definition, not a model.** Re-labelling with a sharper
  escalation rule moved escalation precision 64% → 78% **with the predictions unchanged**. Any
  "automation rate" quoted for a support bot is a statement about where someone drew the
  auto/escalate line; ours counts "please DM us your account email" as *not* automated. Draw it
  the other way and the same system reports a much higher automation rate.
- **n = 200.** 95% CIs are roughly ±7pp. Three of my four iterations moved metrics by less than
  the CI width — i.e. the dev set cannot resolve them, and neither can the golden set.
- **The golden set is not a natural sample.** 50 of 200 were drawn from small clusters so rare
  intents have support; per-class recall is therefore optimistic relative to live traffic, and
  headline rates are reported on the 150 random ones as well.
- **Reference-guided judging drags towards what SpotifyCares actually did.** A materially better
  reply than the 2017 agent's can be marked down for differing from it.
- **Nothing here measures outcomes.** "Would a team lead send this?" is not "did the customer's
  problem get solved" — no resolution, CSAT or re-contact signal exists in this dataset.
- **The numbers are model-specific, and I have now measured how much.** The golden figures come
  from Gemini 3.5 Flash Lite on Vertex. The stand-in used during development reported escalation
  recall 4.6pp higher and unsafe-auto 1.5pp lower than the real model — i.e. the development-time
  numbers were *safer than the truth*. Any headline here is a statement about one model on one
  day; the dev-set table has not been re-run at all.

## 7. Judge quality (does the LLM judge agree with a human?)

**Established: Cohen's κ = 0.63 on the send decision, 82% raw agreement, n=60.**
(`reports/judge_agreement.md`, drafts sampled from `runs/final_vertex`.)

| Criterion | Human pass | Judge pass | Agreement | κ |
|---|---|---|---|---|
| would_send | 62% | 53% | 82% | **0.63** |
| correct_next_step | 68% | 62% | 87% | **0.71** |
| addresses_issue | 92% | 70% | 78% | 0.35 |
| **grounded** | **73%** | **92%** | 75% | **0.18** |
| tone | 97% | 98% | 95% | −0.02 |
| safe | 100% | 100% | 100% | n/a |

60 drafts across the agent and both baselines, with the authoring system withheld from the rater.

**The predicted bias was backwards.** The judge shares a model family with the agent, and on the
stand-in run `judge_robustness.md` measured it approving the agent's longer drafts 8.0pp more
often — so self-preference was the expectation. Two independent checks now contradict it. The
ratings show the judge is harsher, not kinder; and re-running the robustness check on the live
run drops the verbosity gap from **+8.0pp to +1.3pp**, i.e. most of that flag was an artefact of
the stand-in rather than a property of the judge. The judge is
**harsher** than the human everywhere it matters: 53% approved against 62% overall, and 73%
against 87% on the agent's own drafts. `would-send 81.4%` in §3 is therefore more likely
understated than inflated. This is worth stating plainly because the opposite was written in this
report until the ratings existed.

**The real defect is `grounded`, κ = 0.18.** The judge passes 92% where the human passes 73%. It
is too lenient on precisely the criterion that catches invention, which is why §3 flags the 98%
groundedness figure rather than quoting it. Reading the 11 disagreements, the two raters are
lenient about *different* things — the human accepted "we've already replied to your DM" twice
where the judge correctly flagged it as an unverifiable claim, while the judge waved through
generic replies the human marked as not addressing the question. Aggregate agreement of 82% hides
two differently-shaped error profiles.

**`tone` κ = −0.02 is not a finding.** Both raters pass ~97% of drafts, so there is no variance
for κ to measure; the statistic is undefined in spirit if not in arithmetic. Stated explicitly so
the cell is not misread as "the judge cannot assess tone".

**Still untested: self-preference across model families.** Every judgement here comes from a
Gemini model scoring a Gemini model. The κ result makes naive self-flattery unlikely, but it does
not rule out shared blind spots — two models from one family can be wrong about the same things
and agree with each other about it. Scoring the same 60 drafts with a judge from a different
family is one environment variable away (`VERTEX_JUDGE_MODEL`) and is the obvious next control.

**What is already known about label quality:** the human golden labels agree with the LLM's own
labels on 83% of intents (κ 0.80) and 91% of escalate decisions (κ 0.79) — so roughly a sixth of
this task is genuinely contested, which is why the agent's 75.5% should not be read against a
ceiling of 100%.

## 8. With one more week

1. **Fix the retrieval split**: separate indexes for thread-openers and mid-thread follow-ups,
   and retrieve follow-ups with the diagnostic state (device/OS already given) — targets failure
   mode 4, the largest reply-quality class, which prompt edits demonstrably could not fix.
2. **Merge `billing_payment` + `subscription_plan`** into one intent with the escalation reason
   carrying the money/no-money distinction, and add `service_status` — targets modes 1 and 2.
3. **Ban unverifiable system-state claims** the same way DM/refund claims are banned, and add an
   outage feed so the claim can be made truthfully.
4. **Use confidence**: accuracy is 90% at confidence ≥ 0.9 versus 76% at 0.7–0.9, so routing the
   mid band to a human would trade ~10pp of automation for a measurable drop in bad auto-sends —
   a tunable knob rather than a fixed policy.
5. **Double-label 50 golden messages** with a second human to get an inter-annotator ceiling: at
   present I do not know whether the remaining ~18% intent error is model error or label noise.
6. **Report cost per handled ticket**, which decides whether automation is worth it at all.
