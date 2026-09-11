# SpotifyCares support agent — report

*(Numbers marked TBD are filled from `runs/final/golden/summary.md` once the golden set is
hand-labelled; every number in this report is reproducible with
`python -m src.evaluate --split golden --run final` and `LLM_OFFLINE=1`.)*

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

TBD — golden set (n=200), agent vs. two baselines, with 95% bootstrap CIs.

## 4. What the improvement loop changed

TBD — iteration table.

## 5. Top failure modes

TBD.

## 6. What is misleading about my headline number

TBD.

## 7. With one more week

TBD.
